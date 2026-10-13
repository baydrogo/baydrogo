#!/usr/bin/env python3
"""
Obsidian → Baydrogo yayın betiği.

Kasadaki `Baydrogo/` klasörünü siteyle eşitler, commit edip GitHub'a yükler.

Kasada:
  tür: not            → not                (_posts/notlar/); `başlık` verilirse başlıklı not
  tür: yazı           → başlıklı yazı      (_posts/yazilar/), başlık = dosya adı ya da `başlık`
  tür: sayfa          → sabit sayfa        (sayfalar/), örn. Hakkında
  tür yoksa           → yayımlanmaz (taslak)
  tags: [kalem, ...]  → etiketler
  özet: "..."         → yazının özeti, sitede `description` olur (isteğe bağlı)
  yazar: "..."        → yazar adı (boşsa site yazarı)
  adres: /tam/yol/    → adresi olduğu gibi sabitler (eski adresleri korumak için)

İlk yayında betik nota iki özellik ekler, böylece adres ve tarih bir daha değişmez:
  yayın: 2026-10-13T14:30
  adres: kalemle-okumak-bir-konusmaya-donusur

Kasadan silinen ya da `tür`ü kaldırılan not sitede de kaldırılır.

Kullanım:
  python3 scripts/yayinla.py            # dönüştür, commit et, yükle
  python3 scripts/yayinla.py --kuru     # yalnızca ne olacağını göster
  python3 scripts/yayinla.py --yerel    # dönüştür ama commit/yükleme yapma
"""

import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

KASA = Path(os.environ.get("NOTOLOJI_KASA", "/Users/eduman/Desktop/eduman/OBSIDIAN"))
KLASOR = os.environ.get("NOTOLOJI_KLASOR", "Baydrogo")
REPO = Path(__file__).resolve().parent.parent
GORSEL_DIZIN = REPO / "assets" / "img" / "obsidian"
GORSEL_URL = "/assets/img/obsidian/"
SITE = "https://baydrogo.com"
SAAT_DILIMI = "+0300"
KELIME = 5

HARF = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u",
                      "â": "a", "î": "i", "û": "u", "é": "e", "è": "e", "à": "a"})
GORSEL_UZANTI = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}


# ---------- yardımcılar ----------

def sluglastir(metin, kelime=None):
    metin = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", metin)
    metin = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", metin)
    metin = re.sub(r"!?\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]",
                   lambda m: m.group(2) or m.group(1), metin)
    metin = re.sub(r"https?://\S+", " ", metin)
    metin = re.sub(r"<[^>]+>", " ", metin)
    metin = metin.replace("İ", "i").replace("I", "ı").lower().translate(HARF)
    parcalar = re.findall(r"[a-z0-9]+", metin)
    if kelime:
        parcalar = parcalar[:kelime]
    return "-".join(parcalar)[:60].strip("-")


def yaml_deger(ham):
    ham = ham.strip()
    if ham.startswith("[") and ham.endswith("]"):
        return [yaml_deger(p) for p in ham[1:-1].split(",") if p.strip()]
    if len(ham) >= 2 and ham[0] == ham[-1] and ham[0] in "\"'":
        return ham[1:-1]
    return ham


def on_bilgi_ayir(metin):
    """(özellikler sözlüğü, ön bilgi satırları, gövde) döndürür. Basit Obsidian özellikleri için."""
    if not metin.startswith("---"):
        return {}, None, metin
    satirlar = metin.split("\n")
    try:
        son = next(i for i in range(1, len(satirlar)) if satirlar[i].strip() == "---")
    except StopIteration:
        return {}, None, metin
    ozellik, anahtar = {}, None
    for satir in satirlar[1:son]:
        liste = re.match(r"^\s+-\s*(.*)$", satir)
        if liste and anahtar:
            if not isinstance(ozellik.get(anahtar), list):
                ozellik[anahtar] = []
            deger = yaml_deger(liste.group(1))
            if deger != "":
                ozellik[anahtar].append(deger)
            continue
        m = re.match(r"^([^:#][^:]*):\s*(.*)$", satir)
        if m:
            anahtar = m.group(1).strip()
            ozellik[anahtar] = yaml_deger(m.group(2)) if m.group(2).strip() else None
    return ozellik, satirlar[1:son], "\n".join(satirlar[son + 1:]).lstrip("\n")


def al(ozellik, *adlar):
    for ad in adlar:
        if ozellik.get(ad) not in (None, "", []):
            return ozellik[ad]
    return None


def liste(deger):
    if deger is None:
        return []
    if isinstance(deger, list):
        return [str(d).strip() for d in deger if str(d).strip()]
    return [p.strip() for p in str(deger).split(",") if p.strip()]


def yaml_metin(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


def tarih_coz(deger):
    if not deger:
        return None
    for bicim in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(deger).strip(), bicim)
        except ValueError:
            pass
    return None


# ---------- kasa ----------

class Girdi:
    def __init__(self, yol, ozellik, on_bilgi, govde):
        self.yol = yol
        self.ozellik = ozellik
        self.on_bilgi = on_bilgi
        self.govde = govde
        tur = liste(al(ozellik, "tür", "tur"))
        tur = (tur[0] if tur else "").lower().translate(HARF)
        self.tur = tur if tur in ("not", "yazi", "sayfa") else None
        self.not_basligi = al(ozellik, "başlık", "baslik") if self.tur == "not" else None
        self.baslik = al(ozellik, "başlık", "baslik") or yol.stem
        self.eklenecek = {}

        tarih = tarih_coz(al(ozellik, "yayın", "yayin"))
        if not tarih:
            tarih = datetime.now().replace(second=0, microsecond=0)
            if self.tur != "sayfa":  # sayfaların tarihi yok
                self.eklenecek["yayın"] = tarih.strftime("%Y-%m-%dT%H:%M")
        self.tarih = tarih

        adres = al(ozellik, "adres")
        if not adres:
            if self.tur == "not":
                adres = sluglastir(self.not_basligi) if self.not_basligi else sluglastir(govde, KELIME)
            else:
                adres = sluglastir(self.baslik)
            adres = adres or tarih.strftime("%H%M")
            self.eklenecek["adres"] = adres
        self.adres = str(adres)
        # `adres: /tam/yol/` biçimi, girdinin adresini olduğu gibi sabitler (eski adresleri korumak için)
        self.ozel_adres = self.adres if self.adres.startswith("/") else None
        if self.ozel_adres and not self.ozel_adres.endswith("/"):
            self.ozel_adres += "/"
        self.dosya_adi = sluglastir(self.adres) or tarih.strftime("%H%M")

    @property
    def url(self):
        if self.ozel_adres:
            return self.ozel_adres
        if self.tur == "not":
            return self.tarih.strftime("/%Y/%m/%d/") + self.adres + "/"
        return "/" + self.adres + "/"

    @property
    def hedef(self):
        gun = self.tarih.strftime("%Y-%m-%d")
        if self.tur == "sayfa":
            return REPO / "sayfalar" / f"{self.dosya_adi}.md"
        if self.tur == "not":
            return REPO / "_posts" / "notlar" / f"{gun}-{self.tarih.strftime('%H%M')}-{self.dosya_adi[:20].strip('-')}.md"
        return REPO / "_posts" / "yazilar" / f"{gun}-{self.dosya_adi}.md"


def kasayi_oku():
    kok = KASA / KLASOR
    if not kok.is_dir():
        sys.exit(f"Kasada '{KLASOR}' klasörü bulunamadı: {kok}")
    girdiler = []
    for yol in sorted(kok.rglob("*.md")):
        if any(p.startswith(".") for p in yol.relative_to(KASA).parts):
            continue
        ozellik, on_bilgi, govde = on_bilgi_ayir(yol.read_text(encoding="utf-8"))
        g = Girdi(yol, ozellik, on_bilgi, govde)
        if g.tur:
            girdiler.append(g)
    return girdiler


def kasa_dosyalari():
    """Kasadaki tüm dosyalar: ad → yol (görsel ve not bağlantıları için)."""
    harita = {}
    for yol in KASA.rglob("*"):
        if yol.is_file() and not any(p.startswith(".") for p in yol.relative_to(KASA).parts):
            harita.setdefault(yol.name.lower(), yol)
            if yol.suffix == ".md":
                harita.setdefault(yol.stem.lower(), yol)
    return harita


# ---------- dönüştürme ----------

def donustur(g, yayimlananlar, dosyalar, gorseller):
    metin = re.sub(r"%%.*?%%", "", g.govde, flags=re.S)  # Obsidian yorumları

    def gomulu(m):
        hedef, ayar = m.group(1).strip(), (m.group(2) or "").strip()
        yol = dosyalar.get(Path(hedef).name.lower())
        if yol and yol.suffix.lower() in GORSEL_UZANTI:
            ad = gorsel_adi(yol)
            gorseller[ad] = yol
            alt = "" if re.fullmatch(r"\d+(x\d+)?", ayar) else ayar
            # ![[foto.jpg|Altyazı]] → sitede altyazılı figür
            return f'![{alt}]({GORSEL_URL}{ad} "{alt}")' if alt else f"![]({GORSEL_URL}{ad})"
        return bag(hedef.split("#")[0], None)

    def bag(hedef, gorunen):
        hedef_g = yayimlananlar.get(Path(hedef).stem.lower())
        yazi = gorunen or hedef
        return f"[{yazi}]({hedef_g.url})" if hedef_g else yazi

    metin = re.sub(r"!\[\[([^\]|]+)(?:\|([^\]]*))?\]\]", gomulu, metin)
    metin = re.sub(r"\[\[([^\]|#]+)(?:#[^\]|]*)?(?:\|([^\]]*))?\]\]",
                   lambda m: bag(m.group(1).strip(), (m.group(2) or "").strip() or None), metin)

    def md_gorsel(m):
        hedef = m.group(2).split(" ")[0]
        if re.match(r"https?://|/", hedef):
            return m.group(0)
        yol = dosyalar.get(Path(hedef.replace("%20", " ")).name.lower())
        if yol and yol.suffix.lower() in GORSEL_UZANTI:
            ad = gorsel_adi(yol)
            gorseller[ad] = yol
            return f"![{m.group(1)}]({GORSEL_URL}{ad})"
        return m.group(0)

    metin = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", md_gorsel, metin)
    metin = re.sub(r"==(.+?)==", r"<mark>\1</mark>", metin)
    metin = re.sub(r"^(\s*>\s*)\[![\w-]+\][+-]?\s*", r"\1", metin, flags=re.M)  # callout işareti

    kaynak = f"kaynak: {yaml_metin(g.yol.relative_to(KASA))}"
    ozet = al(g.ozellik, "özet", "ozet")

    if g.tur == "sayfa":
        on = ["---", "layout: sayfa", f"title: {yaml_metin(g.baslik)}", f"permalink: {g.url}"]
        if ozet:
            on.append(f"description: {yaml_metin(ozet)}")
        on += [kaynak, "---"]
        return "\n".join(on) + "\n" + metin.strip() + "\n"

    on = ["---", f"date: {g.tarih.strftime('%Y-%m-%d %H:%M:00')} {SAAT_DILIMI}"]
    if g.tur == "not" and g.not_basligi:
        on.append(f"title: {yaml_metin(g.not_basligi)}")
    if g.tur == "yazi":
        on.append(f"title: {yaml_metin(g.baslik)}")
    if ozet:
        on.append(f"description: {yaml_metin(ozet)}")
    yazar = al(g.ozellik, "yazar")
    if yazar:
        on.append(f"author: {yaml_metin(liste(yazar)[0])}")
    on.append(f"permalink: {g.ozel_adres}" if g.ozel_adres else f"slug: {g.adres}")
    etiketler = [e.lstrip("#") for e in liste(al(g.ozellik, "tags", "etiketler"))]
    on.append("tags: [" + ", ".join(yaml_metin(e) for e in etiketler) + "]")
    on.append(kaynak)
    on.append("---")
    return "\n".join(on) + "\n" + metin.strip() + "\n"


def gorsel_adi(yol):
    return sluglastir(yol.stem) + yol.suffix.lower()


def kasaya_yaz(g):
    """İlk yayında `yayın` ve `adres` özelliklerini nota ekler."""
    if not g.eklenecek:
        return
    metin = g.yol.read_text(encoding="utf-8")
    yeni = [f"{k}: {v}" for k, v in g.eklenecek.items()]
    if g.on_bilgi is None:
        metin = "---\n" + "\n".join(yeni) + "\n---\n" + metin
    else:
        satirlar = metin.split("\n")
        son = next(i for i in range(1, len(satirlar)) if satirlar[i].strip() == "---")
        satirlar[son:son] = yeni
        metin = "\n".join(satirlar)
    g.yol.write_text(metin, encoding="utf-8")


# ---------- ana akış ----------

def mevcut_uretilenler():
    sonuc = {}
    for yol in [*(REPO / "_posts").rglob("*.md"), *(REPO / "sayfalar").glob("*.md")]:
        m = re.search(r'^kaynak:\s*"?(.+?)"?\s*$', yol.read_text(encoding="utf-8"), re.M)
        if m:
            sonuc[yol] = m.group(1)
    return sonuc


def git(*arg, yakala=False):
    return subprocess.run(["git", "-C", str(REPO), *arg], check=True, text=True,
                          capture_output=yakala)


def main():
    kuru = "--kuru" in sys.argv
    yerel = "--yerel" in sys.argv
    os.environ["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:" + os.environ.get("PATH", "")

    if not kuru and not yerel:
        git("pull", "--rebase", "--autostash", "-q")

    girdiler = kasayi_oku()
    adresler = {}
    for g in girdiler:
        if g.url in adresler:
            sys.exit(f"Aynı adres iki notta: {g.url}\n  {adresler[g.url].yol}\n  {g.yol}\n"
                     f"Birine farklı bir `adres` özelliği ver.")
        adresler[g.url] = g
    yayimlananlar = {g.yol.stem.lower(): g for g in girdiler}
    dosyalar = kasa_dosyalari()
    gorseller = {}

    ciktilar = {g.hedef: donustur(g, yayimlananlar, dosyalar, gorseller) for g in girdiler}
    eski = mevcut_uretilenler()
    silinecek = [y for y in eski if y not in ciktilar]
    degisen = [y for y, m in ciktilar.items() if not y.exists() or y.read_text(encoding="utf-8") != m]

    hedefler = {g.hedef: g for g in girdiler}
    for y in degisen:
        g = hedefler[y]
        ad = g.baslik if g.tur == "yazi" else g.yol.stem
        print(("Güncel: " if y.exists() else "Yeni: ") + f"{ad}\n  {SITE}{g.url}")
    for y in silinecek:
        print(f"Kaldırıldı: {eski[y]}")

    if kuru:
        print(f"\n{len(girdiler)} girdi bulundu. (kuru çalıştırma, hiçbir şey yazılmadı)")
        return

    for g in girdiler:
        kasaya_yaz(g)
    for y in degisen:
        y.parent.mkdir(parents=True, exist_ok=True)
        y.write_text(ciktilar[y], encoding="utf-8")
    for y in silinecek:
        y.unlink()

    if GORSEL_DIZIN.exists():
        shutil.rmtree(GORSEL_DIZIN)
    if gorseller:
        GORSEL_DIZIN.mkdir(parents=True)
        for ad, kaynak in gorseller.items():
            shutil.copy2(kaynak, GORSEL_DIZIN / ad)

    if yerel:
        print("Dosyalar yazıldı (yerel mod, yüklenmedi).")
        return

    git("add", "-A", "_posts", "sayfalar", "assets/img")
    if subprocess.run(["git", "-C", str(REPO), "diff", "--cached", "--quiet"]).returncode == 0:
        print("Değişiklik yok, site zaten güncel.")
        return
    ozet = f"{len(degisen)} yeni/güncel, {len(silinecek)} kaldırılan"
    git("commit", "-q", "-m", f"Obsidian'dan yayın: {ozet}")
    git("push", "-q")
    print(f"\nYüklendi ({ozet}). Site yaklaşık bir dakika içinde güncellenir.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        sys.exit(f"Git hatası: {' '.join(e.cmd)}\n{e.stderr or ''}")
