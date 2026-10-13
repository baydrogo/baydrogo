/* Bağlantı önizlemesi: yazı içindeki site içi bağlantıların üzerine gelince
   hedefin başlığını ve ilk cümlelerini küçük bir kutuda gösterir. Yalnızca fareli cihazlarda. */
(function () {
  if (!window.matchMedia || !matchMedia("(hover: hover) and (pointer: fine)").matches) return;

  var KELIME = 55, BEKLE = 300, onbellek = {}, kutu = null, zamanlayici = null, kapat = null, etkin = null;

  var ALANLAR = [location.hostname, "baydrogo.com", "www.baydrogo.com"];

  function uygun(a) {
    if (ALANLAR.indexOf(a.hostname) < 0 || a.pathname === location.pathname) return false;
    return !/^\/(assets|etiketler|sayfa)\/|\.(xml|json|png|jpe?g|webp|svg|pdf)$/i.test(a.pathname);
  }

  function getir(url) {
    if (!onbellek[url]) {
      onbellek[url] = fetch(url).then(function (y) { return y.ok ? y.text() : Promise.reject(); }).then(function (html) {
        var d = new DOMParser().parseFromString(html, "text/html");
        var govde = d.querySelector(".tek .e-content, article.sayfa");
        if (!govde) return null;
        var baslik = d.querySelector(".tek h1.p-name, .sayfa h1");
        var kelimeler = [], parcalar = govde.querySelectorAll("p, li, blockquote");
        for (var i = 0; i < parcalar.length && kelimeler.length < KELIME; i++) {
          if (parcalar[i].closest("figure, .footnotes")) continue;
          var t = parcalar[i].cloneNode(true);
          t.querySelectorAll("sup").forEach(function (s) { s.remove(); });
          kelimeler = kelimeler.concat(t.textContent.trim().split(/\s+/).filter(Boolean));
        }
        var metin = kelimeler.slice(0, KELIME).join(" ") + (kelimeler.length > KELIME ? "…" : "");
        return { baslik: baslik ? baslik.textContent.trim() : "", metin: metin };
      }).catch(function () { return null; });
    }
    return onbellek[url];
  }

  function goster(a, veri) {
    if (!veri || etkin !== a) return;
    if (!kutu) {
      kutu = document.createElement("div");
      kutu.className = "onizleme";
      kutu.addEventListener("mouseenter", function () { clearTimeout(kapat); });
      kutu.addEventListener("mouseleave", gizle);
      document.body.appendChild(kutu);
    }
    kutu.innerHTML = "";
    if (veri.baslik) { var h = document.createElement("strong"); h.textContent = veri.baslik; kutu.appendChild(h); }
    var p = document.createElement("p"); p.textContent = veri.metin; kutu.appendChild(p);
    kutu.style.display = "block";
    var r = a.getBoundingClientRect(), g = kutu.offsetWidth, y = kutu.offsetHeight;
    var sol = Math.min(Math.max(8, r.left), document.documentElement.clientWidth - g - 8);
    var ust = r.bottom + 8 + y > innerHeight ? r.top - y - 8 : r.bottom + 8;
    kutu.style.left = sol + scrollX + "px";
    kutu.style.top = ust + scrollY + "px";
  }

  function gizle() {
    clearTimeout(zamanlayici);
    kapat = setTimeout(function () { etkin = null; if (kutu) kutu.style.display = "none"; }, 150);
  }

  document.querySelectorAll(".e-content a[href], .icerik a[href], .geri-baglantilar a[href]").forEach(function (a) {
    if (!uygun(a)) return;
    a.addEventListener("mouseenter", function () {
      clearTimeout(kapat); clearTimeout(zamanlayici); etkin = a;
      zamanlayici = setTimeout(function () { getir(a.pathname).then(function (v) { goster(a, v); }); }, BEKLE);
    });
    a.addEventListener("mouseleave", gizle);
    a.addEventListener("focus", function () { etkin = a; getir(a.pathname).then(function (v) { goster(a, v); }); });
    a.addEventListener("blur", gizle);
  });
})();
