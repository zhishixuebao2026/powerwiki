/* ==========================================================================
   衡天⊙ PowerWiki — 悬浮层管理器
   实测页面里所有"贴底固定"的元素，算出一条地板线 --pw-floor：
   阅读工具条、工具坞、皮肤印章都踩在这条线上，彼此不再重叠。
   只在主站页面运行；皮肤页（html[data-pw-edition]）由 editions.js 自己算。
   ========================================================================== */
(function () {
  "use strict";

  /* ── 横向筛选条：左右哪边还能滑，就给哪边加渐变遮罩 ─────────────────── */
  function initRails() {
    var rails = document.querySelectorAll(".chip-rail");
    for (var i = 0; i < rails.length; i++) {
      (function (rail) {
        function sync() {
          var max = rail.scrollWidth - rail.clientWidth;
          rail.classList.toggle("can-left", rail.scrollLeft > 4);
          rail.classList.toggle("can-right", max > 4 && rail.scrollLeft < max - 4);
        }
        rail.addEventListener("scroll", sync, { passive: true });
        window.addEventListener("resize", sync);
        sync();
        setTimeout(sync, 400);
      })(rails[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRails);
  } else {
    initRails();
  }
  window.addEventListener("load", initRails);


  /* ── 滚动进入：给首屏之外的卡片加一点上浮淡入 ─────────────────────────
     只用 IntersectionObserver 加类，CSS 决定动画；元素一旦显示就不再隐藏，
     所以打印、整页截图、关闭动效时都不会出现空白。 */
  function initRise() {
    if (!("IntersectionObserver" in window)) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    var scope = document.querySelector(".tier-grid") ? ".tier-grid > .tier-card" : null;
    if (!scope) return;
    var cards = document.querySelectorAll(scope);
    if (cards.length < 6) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.classList.add("pw-in");
          io.unobserve(e.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.05 });

    for (var i = 0; i < cards.length; i++) {
      if (i < 4) continue;
      cards[i].classList.add("pw-will-rise");
      io.observe(cards[i]);
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { setTimeout(initRise, 300); });
  } else {
    setTimeout(initRise, 300);
  }

  if (document.documentElement.hasAttribute("data-pw-edition")) return;

  var OUR_SELECTORS = [".reader-rail", ".floating-dock", "#pw-edition-dock", ".reading-progress"];
  var GAP = 12;

  function isOurs(el) {
    for (var i = 0; i < OUR_SELECTORS.length; i++) {
      if (el.matches && el.matches(OUR_SELECTORS[i])) return true;
      if (el.closest && el.closest(OUR_SELECTORS[i])) return true;
    }
    return false;
  }

  function measure() {
    // 没可能有整条底部栏的页面直接跳过，省掉一次全量遍历
    if (!document.querySelector(".mobile-dock, .mobile-bottom-nav, .bottom-bar, nav.mobile-dock")) {
      if (document.documentElement.style.getPropertyValue("--pw-floor") !== "0px") {
        document.documentElement.style.setProperty("--pw-floor", "0px");
      }
      return;
    }
    var vh = window.innerHeight;
    var vw = window.innerWidth;
    var floor = 0;
    var nodes = document.querySelectorAll("body *");

    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      if (isOurs(el)) continue;
      var cs = getComputedStyle(el);
      if (cs.position !== "fixed" || cs.display === "none" || cs.visibility === "hidden") continue;
      if (parseFloat(cs.opacity) === 0) continue;

      var r = el.getBoundingClientRect();
      if (!r.width || !r.height) continue;
      // 只认"贴底横条"：宽度够、贴住底部、不是全屏遮罩
      if (r.height > 200 || r.height < 24) continue;
      if (r.width < vw * 0.45) continue;
      if (r.bottom < vh - 30) continue;
      if (r.top < vh * 0.5) continue;
      floor = Math.max(floor, r.height);
    }

    var value = floor ? Math.round(floor + 6) + "px" : "0px";
    if (document.documentElement.style.getPropertyValue("--pw-floor") !== value) {
      document.documentElement.style.setProperty("--pw-floor", value);
    }
  }

  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      measure();
    });
  }

  function boot() {
    measure();
    [180, 700, 1600, 2800].forEach(function (t) { setTimeout(schedule, t); });
    window.addEventListener("resize", schedule);
    window.addEventListener("orientationchange", schedule);

    /* 抽屉/弹窗打开时，底部悬浮条会被盖住，不必重排 */
    document.addEventListener("pw:layout-change", schedule);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }

  window.__PW_MEASURE_FLOOR__ = schedule;
})();
