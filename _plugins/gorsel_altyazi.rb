# Başlıklı görselleri altyazılı figüre çevirir:
#   ![Amasya kalesi](/assets/images/amasya_1.jpg "Kaleden Yeşilırmak")
#   → <figure><img …><figcaption>Kaleden Yeşilırmak</figcaption></figure>

Jekyll::Hooks.register [:posts, :pages], :post_render do |belge|
  next unless belge.output_ext == ".html"

  belge.output = belge.output.gsub(%r{<p>\s*(<img\b[^>]*\btitle="([^"]+)"[^>]*/?>)\s*</p>}) do
    "<figure>#{Regexp.last_match(1)}<figcaption>#{Regexp.last_match(2)}</figcaption></figure>"
  end
end
