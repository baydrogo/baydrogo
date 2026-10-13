/*
	Baydrogo yorum Worker'ı.

	Sitedeki formdan gelen yorumu doğrular (Turnstile, bal küpü, uzunluk sınırları, sayfanın
	gerçekten var olması) ve GitHub reposunda bir pull request açar:
		_data/yorumlar/<anahtar>/<id>.json
	Pull request birleştirilince Jekyll siteyi yeniden derler ve yorum yazının altında görünür.

	Gizli değerler (wrangler secret put ile):
		GITHUB_TOKEN      — yalnızca bu repoya Contents + Pull requests yazma izni olan token
		TURNSTILE_SECRET  — Cloudflare Turnstile gizli anahtarı
*/

const SINIR = { ad: 60, metin: 4000 };

export default {
	async fetch(request, env) {
		const izinliler = env.ALLOWED_ORIGINS.split(',').map(s => s.trim());
		const origin = request.headers.get('Origin') || '';
		const cors = {
			'Access-Control-Allow-Origin': izinliler.includes(origin) ? origin : izinliler[0],
			'Access-Control-Allow-Methods': 'POST, OPTIONS',
			'Access-Control-Allow-Headers': 'Content-Type',
			'Vary': 'Origin',
		};
		const yanit = (veri, durum = 200) =>
			new Response(JSON.stringify(veri), { status: durum, headers: { ...cors, 'Content-Type': 'application/json; charset=utf-8' } });

		if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors });
		if (request.method !== 'POST') return yanit({ hata: 'Yalnızca POST.' }, 405);
		if (!izinliler.includes(origin)) return yanit({ hata: 'İzin verilmeyen kaynak.' }, 403);

		let v;
		try {
			v = await request.json();
		} catch {
			return yanit({ hata: 'Geçersiz istek.' }, 400);
		}

		// Bal küpü: insanlar bu alanı görmez; doluysa bot. Başarılı görünüp sessizce yok say.
		if (v.website) return yanit({ tamam: true });

		const ad = String(v.ad || '').trim();
		const metin = String(v.metin || '').trim();
		const anahtar = String(v.anahtar || '');
		const yol = String(v.yol || '');
		const ust = v.ust ? String(v.ust) : null;
		const yanitlanan = v.yanitlanan ? String(v.yanitlanan).trim().slice(0, SINIR.ad) : null;

		if (!ad || ad.length > SINIR.ad) return yanit({ hata: `İsim 1–${SINIR.ad} karakter olmalı.` }, 400);
		if (!metin || metin.length > SINIR.metin) return yanit({ hata: `Yorum 1–${SINIR.metin} karakter olmalı.` }, 400);
		if (!/^[\p{L}\p{N}-]{1,120}$/u.test(anahtar)) return yanit({ hata: 'Geçersiz sayfa.' }, 400);
		if (!/^\/[\p{L}\p{N}\/._%-]{0,200}$/u.test(yol)) return yanit({ hata: 'Geçersiz sayfa.' }, 400);
		if (ust && !/^[a-z0-9-]{1,40}$/.test(ust)) return yanit({ hata: 'Geçersiz yanıt.' }, 400);

		// Turnstile doğrulaması.
		const ts = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', {
			method: 'POST',
			body: new URLSearchParams({
				secret: env.TURNSTILE_SECRET,
				response: String(v.turnstile || ''),
				remoteip: request.headers.get('CF-Connecting-IP') || '',
			}),
		}).then(r => r.json());
		if (!ts.success) return yanit({ hata: 'Robot doğrulaması başarısız. Sayfayı yenileyip tekrar dene.' }, 400);

		// Yorum yalnızca sitede gerçekten var olan bir sayfaya yapılabilir.
		const sayfa = await fetch(env.SITE_URL + yol, { method: 'HEAD' });
		if (!sayfa.ok) return yanit({ hata: 'Sayfa bulunamadı.' }, 400);

		const simdi = new Date();
		const id = simdi.toISOString().replace(/[-:TZ.]/g, '').slice(0, 14) + '-' + crypto.randomUUID().slice(0, 6);
		const yorum = { id, ad, metin, tarih: simdi.toISOString() };
		if (ust) yorum.ust = ust;
		if (yanitlanan) yorum.yanitlanan = yanitlanan;

		try {
			await pullRequestAc(env, anahtar, yol, yorum);
		} catch (e) {
			console.error(e);
			return yanit({ hata: 'Yorum şu an kaydedilemedi. Biraz sonra tekrar dene.' }, 502);
		}

		return yanit({ tamam: true });
	},
};

async function pullRequestAc(env, anahtar, yol, yorum) {
	const gh = (yolu, secenek = {}) =>
		fetch(`https://api.github.com/repos/${env.GITHUB_REPO}${yolu}`, {
			...secenek,
			headers: {
				'Authorization': `Bearer ${env.GITHUB_TOKEN}`,
				'Accept': 'application/vnd.github+json',
				'User-Agent': 'baydrogo-yorum',
				'Content-Type': 'application/json',
			},
		}).then(async r => {
			if (!r.ok) throw new Error(`GitHub ${r.status} ${yolu}: ${await r.text()}`);
			return r.json();
		});

	const dal = `yorum/${yorum.id}`;
	const ana = await gh(`/git/ref/heads/${env.GITHUB_BRANCH}`);
	await gh('/git/refs', { method: 'POST', body: JSON.stringify({ ref: `refs/heads/${dal}`, sha: ana.object.sha }) });

	await gh(`/contents/_data/yorumlar/${encodeURIComponent(anahtar)}/${yorum.id}.json`, {
		method: 'PUT',
		body: JSON.stringify({
			message: `Yorum: ${yorum.ad} → ${yol}`,
			content: base64(JSON.stringify(yorum, null, 2) + '\n'),
			branch: dal,
		}),
	});

	const alinti = yorum.metin.split('\n').map(s => '> ' + s).join('\n');
	await gh('/pulls', {
		method: 'POST',
		body: JSON.stringify({
			title: `Yorum: ${yorum.ad} → ${yol}`,
			head: dal,
			base: env.GITHUB_BRANCH,
			body: `**${yorum.ad}**${yorum.yanitlanan ? ` (${yorum.yanitlanan} adlı kişiye yanıt)` : ''}, ${env.SITE_URL}${yol}\n\n${alinti}\n\nYayımlamak için birleştir (merge), reddetmek için kapat.`,
		}),
	});
}

function base64(metin) {
	const baytlar = new TextEncoder().encode(metin);
	let ikili = '';
	for (const b of baytlar) ikili += String.fromCharCode(b);
	return btoa(ikili);
}
