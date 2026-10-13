# Notların adresini, micro.blog'daki gibi, metnin (başlıklı notta başlığın) ilk kelimelerinden üretir:
#   _posts/notlar/2026-10-12-0915.md  →  /2026/10/12/kalemle-okumak-bir-konusmaya-donusur/
# Ön bilgide `slug:` yazılıysa o kullanılır. Not yayımlandıktan sonra ilk kelimeleri
# değiştirirsen adres de değişir; eski adresi korumak için `slug:` ekle.

module Notoloji
  class NotAdresi < Jekyll::Generator
    priority :highest

    KELIME = 5
    HARF = { "ç" => "c", "ğ" => "g", "ı" => "i", "ö" => "o", "ş" => "s", "ü" => "u",
             "â" => "a", "î" => "i", "û" => "u", "é" => "e", "è" => "e", "à" => "a" }.freeze

    def generate(site)
      site.posts.docs.each do |not_|
        next unless not_.data["tur"] == "not"
        # Jekyll, dosya adındaki tarihten sonraki kısmı (ör. "0915") zaten slug yapar;
        # ancak ön bilgide elle farklı bir slug verilmişse ona dokunma.
        dosya_slug = not_.basename_without_ext.sub(/\A\d{4}-\d{2}-\d{2}-/, "")

        # Jekyll her yazıya dosya adından bir başlık uydurur; ön bilgide gerçek bir
        # başlık yazılmışsa not "başlıklı" sayılır ve başlığı sitede görünür.
        baslikli = not_.data["title"] && not_.data["title"] != Jekyll::Utils.titleize_slug(dosya_slug)
        not_.data["baslikli"] = baslikli ? true : false

        next if not_.data["slug"] && not_.data["slug"] != dosya_slug

        slug = uret(baslikli ? not_.data["title"] : not_.content)
        next if slug.empty?

        not_.data["slug"] = slug
        not_.instance_variable_set(:@url, nil)
        not_.instance_variable_set(:@url_placeholders, nil)
      end
    end

    private

    def uret(metin)
      metin = metin.dup
      metin.gsub!(/!\[[^\]]*\]\([^)]*\)/, " ")          # görseller
      metin.gsub!(/\[([^\]]*)\]\([^)]*\)/, '\1')         # bağlantılar → metin
      metin.gsub!(%r{https?://\S+}, " ")                 # çıplak adresler
      metin.gsub!(/<[^>]+>/, " ")                        # HTML
      metin = metin.tr("İI", "iı").downcase
      metin = metin.gsub(/[#{HARF.keys.join}]/o, HARF)
      kelimeler = metin.scan(/[a-z0-9]+/)
      kelimeler.first(KELIME).join("-")[0, 60].sub(/-+\z/, "")
    end
  end
end
