/* ==========================================================================
   衡天⊙ PowerWiki — 角落皮肤切换器交互
   只负责开合、键盘、外点关闭、避让定位、滚动淡出；跳转是普通的 <a>。

   定位要点（2026-11-15 重写）：
   水平位置（选边 + 左右 inset）合为一个「锚点」，等 DOM 安静后算定一次
   并永久冻结；之后滚动、开合、定时重测只调上下净空，横向绝不再变。
   以前每次 placeDock() 都重算 leftInset / refreshSide()，React 侧栏异步
   挂载、滚动后 sticky 栏滑入、屏幕外底栏还原都会把印章「挤到旁边」或
   左右横跳（archive 皮肤桌面 16→1334px 即由此而来），注释写着冻结、
   代码却没冻住。现在锚点一旦锁定就谁也动不了。
   启动期印章先 visibility:hidden，锚点锁定、位置同步落好之后才
   .is-ready 显示，消除「CSS 默认左下 → JS 翻右下」的首屏跳变。
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
    // 锚点定稿前先隐藏，消除首屏位置跳变；lockAnchor() 会摘掉。
    // 若 CSS 是旧版（没有 .pw-dock-pending 规则），这个 class 无副作用，
    // 印章照常可见 —— 版本不同步也不会让入口消失。
    dock.classList.add("pw-dock-pending");

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
          // 滚停下来再量一次：有的底栏是滚动后才滑进视口的，只调上下净空。
          queueMeasure();
        }, 600);
      });
    }
    window.addEventListener("scroll", onScroll, { passive: true });

    var GAP = 10;

    /* 量出真实的底部安全区（env() 只能靠一个临时元素读到计算值）。
       同一视口下它是常量：缓存起来，避免每次定位都往 body 增删探测节点、
       把自己刚装的 DOM 安静监听器反复触发，拖到兜底才定稿。
       视口变化（resize / 横竖屏）时清空重算。 */
    var safeInsetCache = null;
    function safeBottomInset() {
      if (safeInsetCache !== null) return safeInsetCache;
      var probe = document.createElement("div");
      probe.style.cssText = "position:fixed;left:-9999px;top:0;width:0;height:0;padding-bottom:env(safe-area-inset-bottom, 0px);pointer-events:none;";
      document.body.appendChild(probe);
      var v = parseFloat(getComputedStyle(probe).paddingBottom) || 0;
      probe.parentNode.removeChild(probe);
      safeInsetCache = v;
      return v;
    }
    // 预热：在任何 DOM 监听器安装之前就把探测节点的增删做完，
    // 之后定位只读缓存，不会再触发监听、干扰安静计时。
    safeBottomInset();

    /* 采集所有贴底/贴边固定块，供上下净空与侧栏 inset 使用 */
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

    /* ── 水平锚点：算定一次，永久冻结 ───────────────────────────────── */
    var anchor = null;          // 锁定后不再变：{ side, leftInset, rightInset }
    var QUIET_MS = 280;         // DOM 安静多久算布局稳定
    var FORCE_LOCK_MS = 3000;   // 兜底：DOM 一直变动也必须在这个时间内定稿
    var quietTimer = null;
    var observer = null;

    function decideSide(vw, vh, boxes) {
      if (vw <= 560) return "right";                 // 手机屏：左边常站着阅读工具条，统一贴右
      var edge = Math.max(10, Math.round(vw * 0.08));
      for (var k = 0; k < boxes.length; k++) {
        var sb = boxes[k];
        if (sb.bottom - sb.top < vh * 0.55) continue;   // 只认贯通全高的侧栏
        // 排除半截在屏外的元素（如匿名 fixed 装饰层 left 为负）：它高却不在屏内，
        // 一旦被误判成"左栏"就会把印章翻到右，必须跳过。真正贴边的侧栏左缘≈0。
        if (sb.left < -4 || sb.right > vw + 4) continue;
        if (sb.left <= edge && sb.right - sb.left >= 120) return "right";
      }
      return "left";
    }

    function computeAnchor(vw, vh, boxes) {
      var side = decideSide(vw, vh, boxes);
      var leftInset = 0;
      var rightInset = 0;
      // 侧栏不一定贴着屏幕边缘：皮肤自己有页边距时（比如 rail 从 43px 才开始），
      // 只要它够高、够宽又靠边，就按整条侧栏处理。
      var edge = Math.max(10, Math.round(vw * 0.08));
      for (var k = 0; k < boxes.length; k++) {
        var sb = boxes[k];
        if (sb.bottom - sb.top < vh * 0.55) continue;
        if (sb.left < -4 || sb.right > vw + 4) continue;
        if (sb.left <= edge && sb.right - sb.left >= 120) leftInset = Math.max(leftInset, sb.right);
        if (sb.right >= vw - edge && sb.right - sb.left >= 120) rightInset = Math.max(rightInset, vw - sb.left);
      }
      return { side: side, leftInset: leftInset, rightInset: rightInset };
    }

    /* 定稿：算锚点 → 同步落位 → 才显示。位置先摆好再露面，不会闪一下。 */
    function lockAnchor() {
      var vw = window.innerWidth, vh = window.innerHeight;
      anchor = computeAnchor(vw, vh, visibleFixedBoxes());
      placeDock();                            // 先把位置摆到最终值
      dock.classList.remove("pw-dock-pending");
      dock.classList.add("is-ready");         // 再露面，用户看不到任何横向跳变
      if (observer) { observer.disconnect(); observer = null; }
      clearTimeout(quietTimer);
    }

    function placeDock() {
      var vw = window.innerWidth;
      var vh = window.innerHeight;
      var boxes = visibleFixedBoxes();
      var w = dock.offsetWidth || 63;
      var h = dock.offsetHeight || 28;
      var mSide = vw < 480 ? 12 : 16;
      // JS 会用 inline style 覆盖 CSS 的 bottom，所以安全区必须在这里算进去，
      // 否则印章会压在 iPhone 的 Home 指示条上。
      var baseBottom = (vw < 480 ? 14 : 18) + safeBottomInset();

      // 横向：锁定后只读冻结锚点；未锁定时用实时候选（此时印章仍隐藏，看不见）。
      var a = anchor || computeAnchor(vw, vh, boxes);
      var side = a.side;

      // 给定选边下的水平起点（紧贴可用区；与 dock 实际宽度无关）
      var leftX = mSide + a.leftInset;
      var rightX = mSide + a.rightInset;

      // 下半屏常驻栏的净空：只决定"抬多高"，不改变左右
      function clearance(spanLeft, spanRight) {
        var bottom = baseBottom;
        for (var i = 0; i < boxes.length; i++) {
          var b = boxes[i];
          if (b.top < vh * 0.5) continue;            // 只看下半屏的常驻栏
          if (b.bottom > vh + 2) continue;           // 底已探出视口的不是底栏，别拿来顶高印章
          if (b.right <= spanLeft + 2 || b.left >= spanRight - 2) continue;
          bottom = Math.max(bottom, Math.round(vh - b.top) + GAP);
        }
        return bottom;
      }

      var bottom;
      if (side === "right") {
        var rightSpanL = vw - rightX - w, rightSpanR = vw - rightX;
        bottom = clearance(rightSpanL, rightSpanR);
      } else {
        bottom = clearance(leftX, leftX + w);
      }
      bottom = Math.max(baseBottom, Math.min(bottom, Math.round(vh * 0.66)));

      dock.classList.toggle("is-flipped", side === "right");
      // 用 inset 直接锚定：展开标签只朝屏内长，绝不顶出屏幕、也不左右跳动
      if (side === "right") {
        dock.style.right = Math.max(mSide, rightX) + "px";
        dock.style.left = "auto";
      } else {
        dock.style.left = Math.max(mSide, leftX) + "px";
        dock.style.right = "auto";
      }
      dock.style.bottom = bottom + "px";
      dock.style.top = "auto";

      // 面板向上弹：上方空间不足时压缩高度并改为向下弹
      var pnl = document.getElementById("pw-edition-panel");
      if (pnl) {
        var roomAbove = vh - h - bottom - 24;
        var roomBelow = vh - bottom - h - 24;
        var down = roomAbove < 240 && roomBelow > roomAbove;
        dock.classList.toggle("is-dropdown", down);
        pnl.style.maxHeight = Math.max(160, Math.min(down ? roomBelow : roomAbove, Math.round(vh * 0.66))) + "px";
      }
    }

    var measureQueued = false;
    function queueMeasure() {
      if (measureQueued) return;
      measureQueued = true;
      requestAnimationFrame(function () {
        measureQueued = false;
        placeDock();      // 横向用冻结锚点，只有上下净空会随滚动变
      });
    }
    window.__PW_PLACE_DOCK__ = queueMeasure;

    /* ── DOM 安静检测：等 React 异步挂载完再定稿，避免过早锁定 ──────────
       静态页 body 无变化也要能锁定，所以 boot 末尾主动排一次 quietTimer。 */
    function onDomChange() {
      if (anchor) return;
      clearTimeout(quietTimer);
      quietTimer = setTimeout(function () {
        if (!anchor) { lockAnchor(); queueMeasure(); }
      }, QUIET_MS);
    }
    if (window.MutationObserver) {
      observer = new MutationObserver(onDomChange);
      observer.observe(document.body, { childList: true, subtree: true, attributes: false });
    }

    // 启动期多测点：覆盖底栏延迟滑入，只调上下净空（此时隐藏，横向随便算）
    [150, 450, 900, 1600].forEach(function (t) { setTimeout(queueMeasure, t); });
    // 兜底：DOM 一直变动也必须在 3s 内定稿显示
    setTimeout(function () { if (!anchor) { lockAnchor(); queueMeasure(); } }, FORCE_LOCK_MS);
    // 静态页没有 DOM 变化时，主动起一次安静计时
    onDomChange();

    // 仅视口尺寸真正变化才重算横向锚点（手机横竖屏、桌面缩放/拖拽窗口）。
    // 不隐藏、不闪烁：视口变了位置本来就该变。
    function onViewportChange() {
      anchor = null;
      safeInsetCache = null;   // 横竖屏 / 窗口变化后安全区可能变，重算
      clearTimeout(quietTimer);
      lockAnchor();
      queueMeasure();
    }
    window.addEventListener("resize", onViewportChange);
    window.addEventListener("orientationchange", onViewportChange);
    // 面板开合会改变自身尺寸，重新量一次（只重定位，不动横向锚点）
    btn.addEventListener("click", function () { setTimeout(queueMeasure, 0); });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
