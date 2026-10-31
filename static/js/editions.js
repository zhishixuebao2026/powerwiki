/* ==========================================================================
   衡天⊙ PowerWiki — 角落皮肤切换器交互
   只负责开合、键盘、外点关闭；跳转是普通的 <a>，不依赖 JS 才能用。
   ========================================================================== */
(function () {
  "use strict";

  function boot() {
    var dock = document.getElementById("pw-edition-dock");
    if (!dock || dock.dataset.bound === "1") return;
    var btn = document.getElementById("pw-edition-toggle");
    var panel = document.getElementById("pw-edition-panel");
    if (!btn || !panel) return;

    dock.dataset.bound = "1";

    function setOpen(open) {
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      dock.classList.toggle("is-open", open);
    }

    btn.addEventListener("click", function (e) {
      e.preventDefault();
      e.stopPropagation();
      setOpen(panel.hidden);
    });

    document.addEventListener("click", function (e) {
      if (panel.hidden) return;
      if (!dock.contains(e.target)) setOpen(false);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !panel.hidden) {
        setOpen(false);
        btn.focus({ preventScroll: true });
      }
    });

    /* 记住看到过哪些皮肤，下次命中同一个皮肤时给它"最近"标记 */
    try {
      var cards = panel.querySelectorAll("[data-edition-id]");
      var seen = null;
      try { seen = JSON.parse(localStorage.getItem("pw_edition_seen_v1") || "[]"); } catch (e) {}
      if (!Array.isArray(seen)) seen = [];
      var current = panel.getAttribute("data-current-edition");
      if (current && seen.indexOf(current) < 0) {
        seen.push(current);
        try { localStorage.setItem("pw_edition_seen_v1", JSON.stringify(seen.slice(-8))); } catch (e) {}
      }
      Array.prototype.forEach.call(cards, function (card) {
        if (card.classList.contains("is-current")) return;
        if (seen.indexOf(card.dataset.editionId) > -1) card.dataset.seen = "1";
      });
    } catch (e) {}
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
