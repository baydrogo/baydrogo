require "cgi"

# Akış için otomatik kesit: işlenmiş HTML'den dipnot numaralarını, görsel altyazılarını,
# başlıkları ve dipnot listesini atar, ilk N kelimeyi döndürür.
#   {{ girdi.content | kesit: 45 }}

module Baydrogo
  module KesitFiltresi
    def kesit(html, kelime = 45)
      metin = html.to_s.dup
      metin.gsub!(%r{<sup\b[^>]*>.*?</sup>}m, "")
      metin.gsub!(%r{<figcaption\b[^>]*>.*?</figcaption>}m, "")
      metin.gsub!(%r{<h[1-6]\b[^>]*>.*?</h[1-6]>}m, " ")
      metin.gsub!(%r{<div class="footnotes".*}m, "")
      metin.gsub!(%r{</?(p|br|li|ul|ol|div|blockquote|figure|tr|td|th)\b[^>]*>}i, " ")  # blok etiketleri boşluk olur
      metin.gsub!(/<[^>]+>/, "")                                                        # satır içi etiketler (a, em…) silinir
      metin = CGI.unescapeHTML(metin).split
      return metin.join(" ") if metin.size <= kelime

      metin.first(kelime).join(" ").sub(/[[:punct:]]+\z/, "") + "…"
    end

    # site.tags → en çok kullanılandan aza etiket adları
    def sik_etiketler(etiketler, adet = 12)
      etiketler.to_a.sort_by { |ad, girdiler| [-girdiler.size, ad] }.first(adet).map(&:first)
    end

    def kelime_sayisi(html)
      html.to_s.gsub(/<[^>]+>/, " ").split.size
    end
  end
end

Liquid::Template.register_filter(Baydrogo::KesitFiltresi)
