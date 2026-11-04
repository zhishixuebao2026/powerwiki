/* ==========================================================================
   衡天⊙ PowerWiki — 装成 App（PWA）
   1. 注册 service worker（离线可用；只在 https / localhost 下注册）
   2. 接到 Chrome / Edge / Android 的 beforeinstallprompt 后，把「安装」入口做成
      页面内的按钮，不再依赖浏览器地址栏里那个藏起来的菜单
   3. iOS Safari 没有安装 API，退化成「分享 → 添加到主屏幕」的图文引导
   4. 独立窗口（standalone）下：隐藏引导、给顶栏和底部让出刘海 / 小白条、
      接管左边缘滑动返回（主屏幕启动时浏览器不提供返回手势）
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
    root.setAttribute("data-standalone", "1");
    // 主屏幕启动时没有地址栏，状态栏会压住顶栏：量一条安全边距写进 CSS 变量。
    // 这里不能只靠 env(safe-area-inset-top)：桌面/安卓模拟和部分机型上它是 0。
    var probe = document.createElement("div");
    probe.style.cssText =
      "position:fixed;top:0;left:0;width:0;height:env(safe-area-inset-top,0px);pointer-events:none;visibility:hidden";
    document.documentElement.appendChild(probe);
    var inset = probe.getBoundingClientRect().height || 0;
    probe.remove();
    if (inset < 24) inset = 54; // iPhone 刘海 / 灵动岛量级的兜底值
    root.style.setProperty("--pw-top-inset", inset + "px");
  }
  if (iOS) root.setAttribute("data-ios", "1");
  if (FROM_APP) root.setAttribute("data-app-launch", "1");

  /* ── 1. service worker ─────────────────────────────────────────────── */
  if ("serviceWorker" in navigator && location.protocol !== "file:") {
    window.addEventListener("load", function () {
      // static/js/app.js → 站点根目录的 service-worker.js
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
  // 安装时那一次可能因为并发请求失败，这里每次启动再补一次，已有就跳过。
  function warmShell(worker) {
    if (!worker || !worker.postMessage) return;
    // 每次都发；service worker 那边会跳过已经缓存过的文件，开销可以忽略。
    worker.postMessage({ type: "pw-warm-shell" });
    root.setAttribute("data-pw-warm", "1");
  }

  function precacheCurrentPage(worker) {
    var urls = [location.href.split("#")[0]];
    if (worker && worker.postMessage) worker.postMessage({ type: "pw-precache", urls: urls });
  }

  /* ── 2. 安装入口 ──────────────────────────────────────────────────── */
  var deferredPrompt = null;
  var buttons = [];

  function collectButtons() {
    buttons = [].slice.call(document.querySelectorAll("[data-pw-install]"));
  }

  var lastVisible = null;
  function setButtons(visible) {
    buttons.forEach(function (b) {
      b.hidden = !visible;
      b.classList.toggle("is-visible", visible);
    });
    // 印章那一组宽度变了，叫 editions.js 重新量一次落点，免得和皮肤自己的浮层压边
    if (lastVisible !== visible) {
      lastVisible = visible;
      window.dispatchEvent(new Event("resize"));
    }
  }

  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    collectButtons();
    setButtons(true);
  });

  window.addEventListener("appinstalled", function () {
    deferredPrompt = null;
    setButtons(false);
    hideSheet();
  });

  function install() {
    if (deferredPrompt) {
      deferredPrompt.prompt();
      deferredPrompt.userChoice.then(function () {
        deferredPrompt = null;
        setButtons(false);
      });
      return;
    }
    openSheet(); // iOS / 已经装过 / 浏览器不给 API：走手动引导
  }

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t.closest && t.closest("[data-pw-install]")) {
      e.preventDefault();
      install();
      return;
    }
    if (t.closest && t.closest("[data-pw-sheet-close]")) hideSheet();
  });

  var canHint = !STANDALONE && location.protocol !== "file:";
  if (canHint) {
    window.addEventListener("load", function () {
      collectButtons();
      setButtons(true);
    });
    // 抽屉 / 顶栏里的按钮可能晚于本脚本插入
    setTimeout(function () {
      collectButtons();
      setButtons(true);
    }, 600);
  }

  /* ── 3. 安装引导面板 ──────────────────────────────────────────────── */
  function openSheet() {
    var sheet = document.getElementById("pw-install-sheet");
    if (!sheet) return;
    sheet.hidden = false;
    requestAnimationFrame(function () {
      sheet.classList.add("is-open");
    });
    document.body.classList.add("pw-sheet-lock");
  }

  function hideSheet() {
    var sheet = document.getElementById("pw-install-sheet");
    if (!sheet || sheet.hidden) return;
    sheet.classList.remove("is-open");
    document.body.classList.remove("pw-sheet-lock");
    setTimeout(function () {
      sheet.hidden = true;
    }, 220);
  }

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") hideSheet();
  });

  /* ── 4. 左边缘滑动返回 ────────────────────────────────────────────── */
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
