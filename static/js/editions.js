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

    /* ── 定位：实测页面上所有贴底固定块，挑一个真正空着的位置 ───────────
       以前只按"底部横条高度"整体上推，会忽略左下角的阅读工具条，
       于是印章压在「A− A+ 宽屏」上面。现在逐块求交，印章永远落在空地。 */
    var GAP = 10;

    function visibleFixedBoxes() {
      var vw = window.innerWidth;
      var vh = window.innerHeight;
      var out = [];
      var nodes = document.querySelectorAll("body *");
      for (var i = 0; i < nodes.length; i++) {
        var el = nodes[i];
        if (el.closest && el.closest("#" + DOCK)) continue;
        var cs = getComputedStyle(el);
        if (cs.position !== "fixed" || cs.display === "none" || cs.visibility === "hidden") continue;
        if (parseFloat(cs.opacity) < 0.15) continue;
        var r = el.getBoundingClientRect();
        if (!r.width || !r.height || r.height < 16) continue;
        // 铺满视口的装饰层（纹理、渐晕、极光）不算障碍
        if (r.width > vw * 0.92 && r.height > vh * 0.6) continue;
        // 完全在视口外
        if (r.right <= 4 || r.left >= vw - 4 || r.bottom <= 4 || r.top >= vh - 4) continue;
        out.push({ top: r.top, bottom: r.bottom, left: r.left, right: r.right });
      }
      return out;
    }

    function placeDock() {
      var vw = window.innerWidth;
      var vh = window.innerHeight;
      var boxes = visibleFixedBoxes();
      var w = dock.offsetWidth || 63;
      var h = dock.offsetHeight || 28;
      var mSide = vw < 480 ? 12 : 16;
      var baseBottom = vw < 480 ? 14 : 18;

      // 贯通全高的左右侧栏（例如归档皮肤的 .rail）：把可用区推出来
      var leftInset = 0;
      var rightInset = 0;
      for (var k = 0; k < boxes.length; k++) {
        var sb = boxes[k];
        if (sb.bottom - sb.top < vh * 0.55) continue;
        if (sb.left <= 8) leftInset = Math.max(leftInset, sb.right);
        if (sb.right >= vw - 8) rightInset = Math.max(rightInset, vw - sb.left);
      }

      function clearance(left) {
        var bottom = baseBottom;
        for (var i = 0; i < boxes.length; i++) {
          var b = boxes[i];
          if (b.top < vh * 0.5) continue;            // 只看下半屏的常驻栏
          if (b.right <= left + 2 || b.left >= left + w - 2) continue;
          bottom = Math.max(bottom, Math.round(vh - b.top) + GAP);
        }
        return bottom;
      }

      var leftX = Math.round(mSide + leftInset);
      var rightX = Math.round(vw - mSide - w - rightInset);
      var leftSlot = clearance(leftX);
      var rightSlot = clearance(rightX);
      // 左侧有整条侧栏、或者手机屏（左边已经站着阅读工具条）时，
      // 一律贴右侧：和工具坞排成一列，左边整块留给正文。
      var useRight = leftInset > 0 || vw <= 560 || rightSlot + 0.5 < leftSlot;
      var bottom = useRight ? rightSlot : leftSlot;
      // 实在挤得太高，就退回另一侧
      if (bottom > vh * 0.42) {
        var other = useRight ? leftSlot : rightSlot;
        if (other < bottom) { useRight = !useRight; bottom = other; }
      }

      dock.classList.toggle("is-flipped", useRight);
      // 贴右边时用 right 锚定：展开标签只会往左长，不会顶出屏幕
      if (useRight) {
        dock.style.right = Math.max(mSide, vw - rightX - w) + "px";
        dock.style.left = "auto";
      } else {
        dock.style.left = Math.max(mSide, leftX) + "px";
        dock.style.right = "auto";
      }
      dock.style.bottom = bottom + "px";
      dock.style.top = "auto";

      // 面板向上弹：上方空间不足时压缩高度并改为向下弹
      var panel = document.getElementById("pw-edition-panel");
      if (panel) {
        var roomAbove = vh - h - bottom - 24;
        var roomBelow = vh - bottom - h - 24;
        var down = roomAbove < 240 && roomBelow > roomAbove;
        dock.classList.toggle("is-dropdown", down);
        panel.style.maxHeight = Math.max(160, Math.min(down ? roomBelow : roomAbove, Math.round(vh * 0.66))) + "px";
      }
    }

    var measureQueued = false;
    function queueMeasure() {
      if (measureQueued) return;
      measureQueued = true;
      requestAnimationFrame(function () {
        measureQueued = false;
        placeDock();
      });
    }
    window.__PW_PLACE_DOCK__ = queueMeasure;

    // React 产物是异步挂载的，分几个时间点各测一次
    [200, 700, 1500, 3000].forEach(function (t) { setTimeout(queueMeasure, t); });
    window.addEventListener("resize", queueMeasure);
    window.addEventListener("orientationchange", queueMeasure);
    // 面板开合会改变自身尺寸，重新量一次
    btn.addEventListener("click", function () { setTimeout(queueMeasure, 0); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
