# Başka sitelere giden bağlantılar yeni sekmede açılır:
#   <a href="https://arslan.io/">  →  <a href="https://arslan.io/" target="_blank" rel="noopener">
# Sitenin kendi sayfalarına giden bağlantılar (göreli ya da baydrogo.com) aynı sekmede kalır.

Jekyll::Hooks.register [:posts, :pages, :documents], :post_render do |belge|
  next unless belge.output_ext == ".html"

  belge.output = belge.output.gsub(/<a\b[^>]*>/) do |etiket|
    adres = etiket[/\bhref="(https?:\/\/[^"]*)"/, 1]
    next etiket if adres.nil? || etiket.include?("target=")
    next etiket if adres =~ %r{\Ahttps?://(www\.)?baydrogo\.com(/|\z)}i

    ek = etiket.include?(" rel=") ? ' target="_blank"' : ' target="_blank" rel="noopener"'
    etiket.sub(/\s*\/?>\z/) { |son| ek + son }
  end
end
