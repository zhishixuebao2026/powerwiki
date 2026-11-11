/* ==========================================================================
   衡天⊙ PowerWiki — 静默离线层（PWA）
   只做三件事：注册 service worker、预热常用页面、
   主屏幕启动时接管左边缘返回手势。

   独立窗口（主屏 App）的状态栏由 iOS 系统绘制，视口天然落在状态栏下方，
   网页不做任何顶部安全区适配，也不量 inset、不兜底 54px。

   按项目要求，全站不提供任何「装成 App / 下载本地 / 添加到主屏幕」的
   按钮、气泡或引导面板。离线能力照常工作，但完全静默、不打扰阅读。
   ========================================================================== */
(function () {
  "use strict";

  var SELF_SRC = (document.currentScript && document.currentScript.src) || location.href;
  var root = document.documentElement;
  var STANDALONE =
    (window.matchMedia && window.matchMedia("(display-mode: standalone)").matches) ||
    window.navigator.standalone === true;
  var FROM_APP = /[?&]src=app\b/.test(location.search);
  var iOS =
    /iPad|iPhone|iPod/.test(navigator.userAgent) ||
    (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);

  if (STANDALONE) {
    // 状态栏由 iOS 系统绘制，网页视口天然在其下方，无需量 inset、无需 54px 兜底。
    root.setAttribute("data-standalone", "1");
  }
  if (iOS) root.setAttribute("data-ios", "1");
  if (FROM_APP) root.setAttribute("data-app-launch", "1");

  /* ── 1. service worker（静默注册，失败也不影响阅读） ───────────────── */
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", function () {
      // static/js/pwa.js → 站点根目录的 service-worker.js
      var swUrl = new URL("../../service-worker.js", SELF_SRC);
      navigator.serviceWorker
        .register(swUrl.href, { scope: new URL("./", swUrl).href })
        .then(function (reg) {
          if (reg.active) {
            precacheCurrentPage(reg.active);
            warmShell(reg.active);
          } else if (reg.installing || reg.waiting) {
            var w = reg.installing || reg.waiting;
            w.addEventListener("statechange", function () {
              if (w.state === "activated") {
                precacheCurrentPage(w);
                warmShell(w);
              }
            });
          }
        })
        .catch(function () {
          /* 注册失败不影响阅读，静默 */
        });
    });
  }

  // 让 SW 把常用页面（首页 / 规则 / 量级 / 角色 / 材质）补进离线缓存。
  function warmShell(worker) {
    if (!worker || !worker.postMessage) return;
    worker.postMessage({ type: "pw-warm-shell" });
    root.setAttribute("data-pw-warm", "1");
  }

  function precacheCurrentPage(worker) {
    var urls = [location.href.split("#")[0]];
    if (worker && worker.postMessage) worker.postMessage({ type: "pw-precache", urls: urls });
  }

  /* ── 2. 左边缘滑动返回（独立窗口里没有浏览器返回手势） ─────────────── */
  if (STANDALONE) {
    var startX = null;
    var startY = null;
    document.addEventListener(
      "touchstart",
      function (e) {
        if (e.touches.length !== 1) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
      },
      { passive: true }
    );
    document.addEventListener(
      "touchend",
      function (e) {
        if (startX === null) return;
        var t = e.changedTouches[0];
        var dx = t.clientX - startX;
        var dy = Math.abs(t.clientY - startY);
        var fromEdge = startX < 28;
        startX = null;
        startY = null;
        if (fromEdge && dx > 84 && dy < 60 && window.history.length > 1) {
          window.history.back();
        }
      },
      { passive: true }
    );
  }
})();
