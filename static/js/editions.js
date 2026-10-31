/* ==========================================================================
   衡天⊙ PowerWiki — 角落皮肤切换器交互
   只负责开合、键盘、外点关闭、避让定位、滚动淡出；跳转是普通的 <a>。
   ========================================================================== */
(function () {
  "use strict";

  var DOCK = "pw-edition-dock";

  function boot() {
    var dock = document.getElementById(DOCK);
    if (!dock || dock.dataset.bound === "1") return;
    var btn = document.getElementById("pw-edition-toggle");
    var panel = document.getElementById("pw-edition-panel");
    if (!btn || !panel) return;

    dock.dataset.bound = "1";
    var root = document.documentElement;

    function setOpen(open) {
      panel.hidden = !open;
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      dock.classList.toggle("is-open", open);
      if (open) dock.classList.remove("is-dim");
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

    /* ── 滚动时淡出，停下再出现 ───────────────────────────────────── */
    var idleTimer = null;
    var ticking = false;
    function onScroll() {
      if (ticking || !panel.hidden) return;
      ticking = true;
      requestAnimationFrame(function () {
        ticking = false;
        dock.classList.add("is-dim");
        clearTimeout(idleTimer);
        idleTimer = setTimeout(function () {
          dock.classList.remove("is-dim");
        }, 600);
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });

    /* ── 避让：实测页面自带的固定栏，把印章推出去 ─────────────────── */
    function measureInsets() {
      var vw = window.innerWidth;
      var vh = window.innerHeight;
      var bottom = 0;
      var leftRail = 0;
      var rightRail = 0;
      var nodes = document.querySelectorAll("body *");
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.closest && el.closest("#" + DOCK)) continue;
        var cs = getComputedStyle(el);
        if (cs.position !== "fixed" || cs.display === "none" || cs.visibility === "hidden") continue;
        var r = el.getBoundingClientRect();
        if (!r.width || !r.height || r.bottom < 0 || r.top > vh) continue;
        // 底部横条
        if (r.height >= 36 && r.height <= 190 && r.width >= vw * 0.5 && r.bottom > vh - 26) {
          bottom = Math.max(bottom, r.height);
        }
        // 左侧固定侧栏
        if (r.width >= 180 && r.width <= vw * 0.6 && r.height > vh * 0.55 && r.left <= 24) {
          leftRail = Math.max(leftRail, r.right);
        }
        // 右侧固定侧栏
        if (r.width >= 180 && r.width <= vw * 0.6 && r.height > vh * 0.55 && r.right >= vw - 24) {
          rightRail = Math.max(rightRail, vw - r.left);
        }
      }

      root.style.setProperty("--pw-edition-safe-bottom", (bottom ? Math.round(bottom + 8) : 0) + "px");

      // 左侧被固定栏占住时：右侧也空着就翻到右下角，否则贴着侧栏右侧
      var flip = leftRail > 0 && rightRail === 0 && vw > 760;
      dock.classList.toggle("is-flipped", flip);
      if (!flip && leftRail > 0) {
        root.style.setProperty("--pw-edition-safe-left", Math.round(leftRail + 10) + "px");
        dock.style.left = Math.round(leftRail + 10) + "px";
      } else {
        dock.style.left = "";
        if (flip) dock.style.right = Math.max(16, rightRail + 12) + "px";
        else dock.style.right = "";
      }
    }

    var measureQueued = false;
    function queueMeasure() {
      if (measureQueued) return;
      measureQueued = true;
      requestAnimationFrame(function () {
        measureQueued = false;
        measureInsets();
      });
    }

    // React 产物是异步挂载的，分几个时间点各测一次
    [300, 900, 1800, 3200].forEach(function (t) { setTimeout(queueMeasure, t); });
    window.addEventListener("resize", queueMeasure);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
