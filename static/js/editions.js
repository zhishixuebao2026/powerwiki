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
          // 滚停下来再量一次：有的侧栏是滚动后才滑进视口的，位置会变。
          queueMeasure();
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
        // sticky 也算：整页产物的侧栏常是 position:sticky 的，只量 fixed 会漏掉，
        // 印章就贴回左下角压在目录上。
        if ((cs.position !== "fixed" && cs.position !== "sticky") || cs.display === "none" || cs.visibility === "hidden") continue;
        if (parseFloat(cs.opacity) < 0.15) continue;
        var r = el.getBoundingClientRect();
        if (!r.width || !r.height || r.height < 16) continue;
        // 铺满视口的装饰层（纹理、渐晕、极光）不算障碍
        if (r.width > vw * 0.92 && r.height > vh * 0.6) continue;
        // 屏幕外的底栏：不少皮肤把底栏停在视口下方、"滚动后滑进来"，
        // 量的时候看不见，滚起来就压住印章。按它的 bottom 值还原落脚位置。
        if (r.top >= vh - 4) {
          var parkedBar = r.width >= vw * 0.4 && r.height >= 24 && r.height <= 200 && r.top < vh + 260;
          if (!parkedBar) continue;
          var bottomPx = parseFloat(cs.bottom);
          if (!isFinite(bottomPx)) continue;
          out.push({ top: vh - bottomPx - r.height, bottom: vh - bottomPx, left: r.left, right: r.right });
          continue;
        }
        // 还没滚到跟前的 sticky 侧栏：横向范围是固定的，先按"整条从底部起"记一笔，
        // 否则刚进页面时它还在视口下方，印章会在左下角落地、等它出现就被压住。
        if (cs.position === "sticky" && r.top >= vh - 4) {
          if (r.width >= 120) out.push({ top: vh, bottom: vh + r.height, left: r.left, right: r.right });
          continue;
        }
        // 其余完全在视口外的
        if (r.right <= 4 || r.left >= vw - 4 || r.bottom <= 4) continue;
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
      // 侧栏不一定贴着屏幕边缘：皮肤自己有页边距时（比如 rail 从 43px 才开始），
      // 只要它够高、够宽又靠边，就按整条侧栏处理。
      var edge = Math.max(10, Math.round(vw * 0.08));
      for (var k = 0; k < boxes.length; k++) {
        var sb = boxes[k];
        if (sb.bottom - sb.top < vh * 0.55) continue;
        if (sb.left <= edge && sb.right - sb.left >= 120) leftInset = Math.max(leftInset, sb.right);
        if (sb.right >= vw - edge && sb.right - sb.left >= 120) rightInset = Math.max(rightInset, vw - sb.left);
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
