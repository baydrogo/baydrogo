# Geri bağlantılar: bir yazıya/nota sitedeki hangi girdilerin bağlantı verdiğini bulur.
# Her hedefin `geri_baglantilar` alanına {url, baslik, baglam} listesi yazılır;
# _includes/geri-baglantilar.html bunu yazının altında gösterir.
module Baydrogo
  class GeriBaglantilar < Jekyll::Generator
    priority :low
    BAGLAM_KELIME = 36

    def generate(site)
      girdiler = site.posts.docs + site.pages.select { |p| p.data["layout"] == "sayfa" }
      adresler = {}
      girdiler.each { |g| adresler[normal(g.url)] = g }

      girdiler.each { |g| g.data["geri_baglantilar"] = [] }
      girdiler.each do |kaynak|
        gorulen = {}
        paragraflar(kaynak.content).each do |paragraf|
          paragraf.to_enum(:scan, desen(site)).map { Regexp.last_match }.each do |m|
            adres = m[1]
            hedef = adresler[normal(adres)]
            next if hedef.nil? || hedef.equal?(kaynak) || gorulen[hedef.url]
            gorulen[hedef.url] = true
            hedef.data["geri_baglantilar"] << {
              "url" => kaynak.url,
              "baslik" => baslik(kaynak),
              "tur" => kaynak.data["tur"],
              "tarih" => kaynak.data["date"],
              "baglam" => baglam(paragraf, m.begin(0))
            }
          end
        end
      end
      girdiler.each { |g| g.data["geri_baglantilar"].sort_by! { |b| b["tarih"] || Time.at(0) }.reverse! }
    end

    private

    # [metin](/adres/) ya da [metin](https://site/adres/) — görseller (![…]) hariç
    # Yerel `jekyll serve` site.url'yi localhost yapar; asıl alan adı CNAME'den de okunur.
    def desen(site)
      cname = File.join(site.source, "CNAME")
      alanlar = [site.config["url"].to_s, File.exist?(cname) ? File.read(cname) : ""]
                .map { |a| a.strip.sub(%r{\Ahttps?://(www\.)?}, "").chomp("/") }
                .reject(&:empty?).uniq.map { |a| Regexp.escape(a) }
      @desen ||= %r{(?<!!)\[[^\]]*\]\((?:https?://(?:www\.)?(?:#{alanlar.join("|")}))?(/[^)\s]*)}
    end

    def normal(adres)
      a = adres.split(/[#?]/).first.to_s
      a = a.sub(/index\.html\z/, "")
      a.end_with?("/") ? a : "#{a}/"
    end

    def paragraflar(metin)
      metin.to_s.gsub(/^---.*?^---/m, "").split(/\n\s*\n/)
    end

    def duz(metin)
      metin.gsub(/!\[[^\]]*\]\([^)]*\)/, "")
           .gsub(/\[([^\]]*)\]\([^)]*\)/, '\1')
           .gsub(/\[\^[^\]]+\]/, "")
           .gsub(/<[^>]+>/, "")
           .gsub(/^\s*(>|#+|[-*+]|\d+\.)\s*/, "")
           .gsub(/[*_`]/, "")
           .split.join(" ")
    end

    def baslik(g)
      return g.data["title"] if g.data["tur"] != "not" || g.data["baslikli"]
      kelimeler = duz(g.content).split
      kelimeler.first(8).join(" ") + (kelimeler.size > 8 ? "…" : "")
    end

    # Bağlantının geçtiği paragraftan, bağlantıyı ortalayan kısa bir kesit
    def baglam(paragraf, konum)
      on = duz(paragraf[0...konum]).split
      kelimeler = duz(paragraf).split
      return kelimeler.join(" ") if kelimeler.size <= BAGLAM_KELIME
      bas = [[on.size - BAGLAM_KELIME / 2, 0].max, kelimeler.size - BAGLAM_KELIME].min
      parca = kelimeler[bas, BAGLAM_KELIME].join(" ")
      (bas > 0 ? "…" : "") + parca + (bas + BAGLAM_KELIME < kelimeler.size ? "…" : "")
    end
  end
end
