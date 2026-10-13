/* Notoloji yorum formu: yorumu Worker'a gönderir, yanıtlama bağlantılarını yönetir. */
(function () {
	var form = document.getElementById('yorum-formu');
	if (!form) return;

	var durum = form.querySelector('.yorum-durum'),
		bilgi = form.querySelector('.yorum-yanit-bilgi'),
		dugme = form.querySelector('button[type=submit]'),
		ust = null,
		yanitlanan = null;

	function yanitla(id, ad) {
		ust = id;
		yanitlanan = ad;
		bilgi.querySelector('span').textContent = ad + ' adlı kişiye yanıt yazıyorsun.';
		bilgi.hidden = false;
		form.scrollIntoView({ behavior: 'smooth' });
		form.elements.metin.focus();
	}

	document.querySelectorAll('.yorum-yanitla').forEach(function (a) {
		a.addEventListener('click', function (e) {
			e.preventDefault();
			yanitla(a.dataset.id, a.dataset.ad);
		});
	});

	bilgi.querySelector('.yorum-yanit-iptal').addEventListener('click', function (e) {
		e.preventDefault();
		ust = yanitlanan = null;
		bilgi.hidden = true;
	});

	form.addEventListener('submit', function (e) {
		e.preventDefault();
		var token = form.querySelector('[name="cf-turnstile-response"]');
		if (!token || !token.value) {
			durum.textContent = 'Robot doğrulamasının bitmesini bekle.';
			return;
		}

		dugme.disabled = true;
		durum.textContent = 'Gönderiliyor…';

		fetch(form.dataset.worker, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({
				ad: form.elements.ad.value,
				metin: form.elements.metin.value,
				website: form.elements.website.value,
				anahtar: form.dataset.anahtar,
				yol: form.dataset.yol,
				ust: ust,
				yanitlanan: yanitlanan,
				turnstile: token.value
			})
		})
			.then(function (r) { return r.json(); })
			.then(function (v) {
				if (!v.tamam) throw new Error(v.hata || 'Bir sorun oluştu.');
				form.reset();
				ust = yanitlanan = null;
				bilgi.hidden = true;
				durum.textContent = 'Teşekkürler! Yorumun alındı, onaylandıktan sonra burada görünecek.';
			})
			.catch(function (err) {
				durum.textContent = err.message || 'Gönderilemedi. Biraz sonra tekrar dene.';
			})
			.finally(function () {
				dugme.disabled = false;
				if (window.turnstile) window.turnstile.reset();
			});
	});
})();
