/* Açık/koyu tema düğmesi: seçim tarayıcıda hatırlanır; seçilmediyse cihaz ayarı geçerli. */
(function () {
  var kok = document.documentElement;
  var karanlik = window.matchMedia && matchMedia("(prefers-color-scheme: dark)");
  function simdiki() { return kok.getAttribute("data-tema") || (karanlik && karanlik.matches ? "koyu" : "acik"); }
  document.querySelectorAll(".tema-dugme").forEach(function (d) {
    d.addEventListener("click", function () {
      var yeni = simdiki() === "koyu" ? "acik" : "koyu";
      kok.setAttribute("data-tema", yeni);
      try { localStorage.setItem("tema", yeni); } catch (e) {}
    });
  });
})();
