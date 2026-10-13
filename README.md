# Baydrogo

[baydrogo.com](https://baydrogo.com) — Jekyll + GitHub Pages. `main` dalına her gönderimde GitHub Actions siteyi derleyip yayınlar.

## İçerik türleri

| Tür | Klasör | Başlık | Adres |
|---|---|---|---|
| Yazı | `_posts/` | var | `/yazinin-adi/` |
| Not | `_posts/notlar/` | isteğe bağlı | `/2026/10/13/ilk-bes-kelime/` |

Nota `title:` verilirse başlıklı not olur, başlığı akışta ve sayfasında görünür. Notların adresi başlıktan, başlık yoksa metnin ilk beş kelimesinden üretilir (`_plugins/not_adresi.rb`); ön bilgide `slug:` varsa o kullanılır. Notlar ana sayfa listesinde tam metinle, `/notlar/` sayfasında ve RSS/JSON akışında başlıksız görünür.

## Obsidian'dan yayın

Kasadaki `Baydrogo/` klasörüne yaz, özelliklere `tür: not` ya da `tür: yazı` ekle (nota `başlık` da verebilirsin) (şablonlar: `T_Baydrogo Not`, `T_Baydrogo Yazı`). Obsidian'daki **Baydrogo Yayın** eklentisi (kâğıt uçak simgesi) şunu çalıştırır:

```bash
python3 scripts/yayinla.py
```

Betik klasörü siteyle eşitler: yeni ve değişen girdileri `_posts/` altına yazar, kasadan silineni ya da `tür`ü kaldırılanı siteden kaldırır, `[[bağlantıları]]` ve `![[görselleri]]` dönüştürür, commit edip yükler. İlk yayında nota `yayın` ve `adres` özelliklerini ekler; adres ve tarih bundan sonra sabit kalır. `özet` özelliği yazının `description` alanı olur. `--kuru` yalnızca ne olacağını gösterir.

Sitedeki bütün yazılar, notlar ve Hakkında sayfası Obsidian'dan üretilir (`kaynak:` alanı bunu gösterir); düzeltmek için kasadaki notu düzenleyip yeniden yayımla. `tür: sayfa` sabit sayfalar içindir (`sayfalar/`). `adres: /tam/yol/` bir girdinin adresini olduğu gibi sabitler; eski adresler bu yolla korunur. `yazar` özelliği yazının yazarını belirler.

Elle eklenen ve `kaynak:` alanı olmayan dosyalara betik dokunmaz.

## Yorumlar

`yorum-worker/` bir Cloudflare Worker'dır: formdan gelen yorumu Turnstile ile doğrular ve `_data/yorumlar/<sayfa>/<id>.json` dosyası olarak pull request açar; birleştirilince yorum yayımlanır. `_config.yml` içindeki `yorum.worker_url` ve `yorum.turnstile_site_key` doldurulana kadar sitede yorum bölümü görünmez.
