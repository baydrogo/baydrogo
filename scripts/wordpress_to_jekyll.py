#!/usr/bin/env python3
"""
WordPress XML → Jekyll Dönüştürücü
=====================================
WordPress'ten dışa aktardığınız XML dosyasını Jekyll _posts/ formatına çevirir.

Kullanım:
  1. WordPress Admin → Araçlar → Dışa Aktar → Tüm İçerik → İndir
  2. python3 wordpress_to_jekyll.py --xml wordpress.xml --hedef ../_posts

Gereksinimler:
  pip install html2text python-slugify python-frontmatter
"""

import os
import re
import argparse
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    import html2text
    from slugify import slugify
    import frontmatter
except ImportError:
    print("Eksik paketler! Şunu çalıştırın:")
    print("  pip install html2text python-slugify python-frontmatter")
    exit(1)


# WordPress XML namespace'leri
NS = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'wp':      'http://wordpress.org/export/1.2/',
    'dc':      'http://purl.org/dc/elements/1.1/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
}


def html_to_markdown(html_icerik):
    """HTML içeriği Markdown'a çevirir."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = False
    converter.body_width = 0  # Satır kesmeme
    converter.unicode_snob = True
    return converter.handle(html_icerik).strip()


def wordpress_donustur(xml_dosyasi, hedef_klasor):
    """WordPress XML dosyasını parse ederek Jekyll postları oluşturur."""
    tree = ET.parse(xml_dosyasi)
    root = tree.getroot()
    channel = root.find('channel')

    hedef = Path(hedef_klasor)
    hedef.mkdir(parents=True, exist_ok=True)

    items = channel.findall('item')
    yayinlananlar = [i for i in items if i.find('wp:status', NS) is not None
                     and i.find('wp:status', NS).text == 'publish'
                     and i.find('wp:post_type', NS) is not None
                     and i.find('wp:post_type', NS).text == 'post']

    print(f"🔍 {len(yayinlananlar)} yayınlanmış yazı bulundu...\n")
    basarili = 0

    for item in yayinlananlar:
        try:
            baslik = item.findtext('title', '').strip()
            html_icerik = item.findtext('content:encoded', '', NS)
            tarih_str = item.findtext('wp:post_date', '', NS)
            slug = item.findtext('wp:post_name', '', NS)
            ozet_html = item.findtext('excerpt:encoded', '', NS)

            # Kategori ve etiketler
            kategoriler = []
            etiketler = []
            for cat_elem in item.findall('category'):
                domain = cat_elem.get('domain', '')
                nicename = cat_elem.get('nicename', '')
                metin = cat_elem.text or ''
                if domain == 'category':
                    kategoriler.append(metin)
                elif domain == 'post_tag':
                    etiketler.append(metin)

            if not kategoriler:
                kategoriler = ['genel']

            # Tarih
            try:
                tarih_obj = datetime.strptime(tarih_str, "%Y-%m-%d %H:%M:%S")
            except:
                tarih_obj = datetime.now()
            jekyll_tarihi = tarih_obj.strftime("%Y-%m-%d %H:%M:%S +0300")

            # Slug
            if not slug:
                slug = slugify(baslik, allow_unicode=False)

            # Markdown içerik
            markdown_icerik = html_to_markdown(html_icerik)

            # Özet
            ozet = html_to_markdown(ozet_html).strip()[:200] if ozet_html.strip() else ''

            # Dosya adı
            hedef_dosya = hedef / f"{tarih_obj.strftime('%Y-%m-%d')}-{slug}.md"

            # Jekyll front matter
            meta = {
                'layout': 'post',
                'title': baslik,
                'date': jekyll_tarihi,
                'categories': kategoriler,
                'tags': etiketler,
            }
            if ozet:
                meta['excerpt'] = ozet[:200]

            post = frontmatter.Post(markdown_icerik, **meta)
            with open(hedef_dosya, 'w', encoding='utf-8') as f:
                f.write(frontmatter.dumps(post))

            print(f"  ✅ {baslik[:60]}")
            basarili += 1

        except Exception as e:
            print(f"  ❌ HATA: {e}")

    print(f"\n✨ {basarili} yazı dönüştürüldü!")
    print(f"📁 Çıktı klasörü: {hedef_klasor}")


def main():
    parser = argparse.ArgumentParser(description='WordPress XML → Jekyll dönüştürücü')
    parser.add_argument('--xml', required=True, help='WordPress export XML dosyası')
    parser.add_argument('--hedef', required=True, help='Jekyll _posts/ klasörü')
    args = parser.parse_args()

    wordpress_donustur(args.xml, args.hedef)


if __name__ == '__main__':
    main()
