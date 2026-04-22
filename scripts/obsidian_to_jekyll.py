#!/usr/bin/env python3
"""
Obsidian → Jekyll Dönüştürücü
==============================
Obsidian klasörünüzdeki .md dosyalarını Jekyll _posts/ formatına dönüştürür.

Kullanım:
  python3 obsidian_to_jekyll.py --kaynak ~/Obsidian/Blog --hedef ~/baydrogo/_posts

Gereksinimler:
  pip install python-frontmatter python-slugify
"""

import os
import re
import shutil
import argparse
from datetime import datetime
from pathlib import Path

try:
    import frontmatter
    from slugify import slugify
except ImportError:
    print("Eksik paket! Şunu çalıştırın:")
    print("  pip install python-frontmatter python-slugify")
    exit(1)


def obsidian_to_jekyll_date(tarih_str):
    """Çeşitli tarih formatlarını Jekyll formatına çevirir."""
    formatlar = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d.%m.%Y",
    ]
    for fmt in formatlar:
        try:
            dt = datetime.strptime(tarih_str.strip(), fmt)
            return dt.strftime("%Y-%m-%d %H:%M:%S +0300")
        except:
            continue
    return None


def obsidian_etiketlerini_temizle(icerik):
    """Obsidian #etiket formatını Jekyll tags'e çevirir."""
    # Obsidian wiki linklerini markdown'a çevir: [[Başlık]] → Başlık
    icerik = re.sub(r'\[\[([^\]|]+)\|([^\]]+)\]\]', r'\2', icerik)
    icerik = re.sub(r'\[\[([^\]]+)\]\]', r'\1', icerik)
    return icerik


def dosyayi_donustur(kaynak_dosya, hedef_klasor, varsayilan_kategori="genel"):
    """Tek bir Obsidian dosyasını Jekyll post'una dönüştürür."""
    with open(kaynak_dosya, 'r', encoding='utf-8') as f:
        post = frontmatter.load(f)

    # Tarih belirle
    if 'date' in post.metadata:
        tarih_str = str(post.metadata['date'])
        jekyll_tarihi = obsidian_to_jekyll_date(tarih_str)
        if not jekyll_tarihi:
            jekyll_tarihi = datetime.now().strftime("%Y-%m-%d %H:%M:%S +0300")
        tarih_obj = datetime.strptime(jekyll_tarihi[:10], "%Y-%m-%d")
    else:
        tarih_obj = datetime.fromtimestamp(os.path.getmtime(kaynak_dosya))
        jekyll_tarihi = tarih_obj.strftime("%Y-%m-%d %H:%M:%S +0300")

    # Başlık belirle
    baslik = post.metadata.get('title', Path(kaynak_dosya).stem)

    # Slug (URL uyumlu dosya adı)
    slug = slugify(baslik, allow_unicode=False, separator='-')

    # Hedef dosya adı: YYYY-MM-DD-baslik.md
    hedef_dosya_adi = f"{tarih_obj.strftime('%Y-%m-%d')}-{slug}.md"
    hedef_yolu = os.path.join(hedef_klasor, hedef_dosya_adi)

    # Kategoriler
    kategoriler = post.metadata.get('categories', post.metadata.get('category', [varsayilan_kategori]))
    if isinstance(kategoriler, str):
        kategoriler = [kategoriler]

    # Etiketler
    etiketler = post.metadata.get('tags', [])
    if isinstance(etiketler, str):
        etiketler = [e.strip().lstrip('#') for e in etiketler.split(',')]
    else:
        etiketler = [str(e).lstrip('#') for e in etiketler]

    # İçeriği dönüştür
    icerik = obsidian_etiketlerini_temizle(post.content)

    # Jekyll front matter yaz
    jekyll_metadata = {
        'layout': 'post',
        'title': baslik,
        'date': jekyll_tarihi,
        'categories': kategoriler,
        'tags': etiketler,
    }
    if 'excerpt' in post.metadata:
        jekyll_metadata['excerpt'] = post.metadata['excerpt']

    # Dosyayı oluştur
    jekyll_post = frontmatter.Post(icerik, **jekyll_metadata)
    with open(hedef_yolu, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dumps(jekyll_post))

    return hedef_dosya_adi


def main():
    parser = argparse.ArgumentParser(description='Obsidian notlarını Jekyll postlarına dönüştür')
    parser.add_argument('--kaynak', required=True, help='Obsidian blog klasörü')
    parser.add_argument('--hedef', required=True, help='Jekyll _posts/ klasörü')
    parser.add_argument('--kategori', default='genel', help='Varsayılan kategori')
    args = parser.parse_args()

    kaynak = Path(args.kaynak)
    hedef = Path(args.hedef)
    hedef.mkdir(parents=True, exist_ok=True)

    md_dosyalari = list(kaynak.glob('**/*.md'))
    if not md_dosyalari:
        print(f"⚠️  '{kaynak}' klasöründe .md dosyası bulunamadı.")
        return

    print(f"🔍 {len(md_dosyalari)} dosya bulundu...\n")
    basarili = 0
    hatali = 0

    for dosya in md_dosyalari:
        try:
            hedef_adi = dosyayi_donustur(dosya, hedef, args.kategori)
            print(f"  ✅ {dosya.name} → {hedef_adi}")
            basarili += 1
        except Exception as e:
            print(f"  ❌ {dosya.name} → HATA: {e}")
            hatali += 1

    print(f"\n✨ Tamamlandı! {basarili} başarılı, {hatali} hatalı.")


if __name__ == '__main__':
    main()
