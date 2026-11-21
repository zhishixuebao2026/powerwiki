/* ==========================================================================
   衡天⊙ PowerWiki — 阅读进度记忆
   目的：换皮肤 / 从皮肤退回角色页时，接着刚才那一行往下读，而不是回到顶部
   再从头找。2026-11-25 用户提出：进皮肤之后退回首页，等于把「角色档案 →
   找到角色 → 点开 → 往下翻」重走一遍，设计本身有问题。

   做法：
   1. 进度按「内容」存，不按「网址」存 —— 同一个角色的 4 套皮肤版式和它的
      正式页共用一把钥匙（char:<slug>），换版式不掉位置。
      规则 / 材质同理（rules / materials）。首页、列表页不记忆。
   2. 同一个网址回来用**精确像素**；换到另一种版式（版式尺寸不同）用
      **百分比**，两边行数不同也能落在相近的段落。
   3. 只在站内跳转时恢复（没有 referrer 的直接打开、带 #锚点 的链接都不动），
      避免第一次打开就莫名落到页面中间。
   4. 字体、图片陆续到位会把文档撑高，所以按 0/120/300/700/1400/2400ms
      补几次；用户一旦自己滚动 / 触屏 / 按键就立刻停手，绝不抢滚动条。
   5. sessionStorage 作用域为单个标签页，关掉即忘；隐私模式下读写失败就静默退出。
   ========================================================================== */
(function () {
  "use strict";

  var KEY = "pw-progress:v1";
  var HAS_APP = !!document.querySelector('script[src*="app.js"]');
  var MIN_RESTORE = 240;   // 小于这个距离不值得"接续"，当新页面看
  var MIN_SAVE = 300;      // 页面本身不够高就不记

  /* ── 这把钥匙代表"同一份内容" ─────────────────────────────────── */
  function contentKey() {
    var p = location.pathname;
    var m;
    if ((m = p.match(/\/(?:skins\/[^/]+\/)?character-([a-z0-9_-]+)\.html$/i))) return "char:" + m[1].toLowerCase();
    if ((m = p.match(/\/(?:skins\/[^/]+\/)?character\/([a-z0-9_-]+)\.html$/i))) return "char:" + m[1].toLowerCase();
    if (/\/(?:skins\/[^/]+\/)?rules\.html$/i.test(p)) return "rules";
    if (/\/(?:skins\/[^/]+\/)?materials\.html$/i.test(p)) return "materials";
    return "";
  }

  function readAll() {
    try {
      var raw = sessionStorage.getItem(KEY);
      var o = raw ? JSON.parse(raw) : null;
      return o && typeof o === "object" ? o : {};
    } catch (e) {
      return {};
    }
  }

  function writeAll(o) {
    try {
      sessionStorage.setItem(KEY, JSON.stringify(o));
    } catch (e) {}
  }

  /* ── 找真正的滚动容器（多数页滚 window，少数整页应用滚自己的 div） ── */
  function docScroller() {
    return document.scrollingElement || document.documentElement;
  }

  function scroller() {
    var de = docScroller();
    if (de && de.scrollHeight - de.clientHeight > MIN_SAVE) return de;
    var best = null;
    var bestGap = MIN_SAVE;
    var nodes = document.querySelectorAll("main,div,section,article,body");
    for (var i = 0; i < nodes.length && i < 3000; i++) {
      var e = nodes[i];
      var gap = e.scrollHeight - e.clientHeight;
      if (gap <= bestGap) continue;
      var oy = getComputedStyle(e).overflowY;
      if (oy !== "auto" && oy !== "scroll" && oy !== "overlay") continue;
      best = e;
      bestGap = gap;
    }
    return best || de;
  }

  function getY(el) {
    if (el === docScroller()) return window.pageYOffset || el.scrollTop || 0;
    return el.scrollTop || 0;
  }

  function maxY(el) {
    return Math.max(0, el.scrollHeight - el.clientHeight);
  }

  /* ── 存 ─────────────────────────────────────────────────────────── */
  function save() {
    var k = contentKey();
    if (!k) return;
    var el = scroller();
    if (!el) return;
    var max = maxY(el);
    if (max < MIN_SAVE) return;
    var y = Math.round(getY(el));
    if (y <= 0) return;
    var all = readAll();
    all[k] = { p: location.pathname, y: y, r: max ? y / max : 0, at: Date.now() };
    writeAll(all);
  }

  /* ── 恢复 ───────────────────────────────────────────────────────── */
  function fromSite() {
    if (!document.referrer) return false;
    try {
      return new URL(document.referrer).origin === location.origin;
    } catch (e) {
      return false;
    }
  }

  function toast(text) {
    try {
      if (document.getElementById("pw-resume-note")) return;
      var d = document.createElement("div");
      d.id = "pw-resume-note";
      d.setAttribute("role", "status");
      d.textContent = text;
      var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      d.style.cssText =
        "position:fixed;left:50%;bottom:calc(76px + env(safe-area-inset-bottom,0px));transform:translateX(-50%);" +
        "z-index:2147483000;pointer-events:none;max-width:min(84vw,340px);" +
        "padding:7px 14px;border-radius:999px;background:rgba(23,24,26,.82);color:#fdfaf3;" +
        "font:500 12px/1.5 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif;" +
        "letter-spacing:.02em;box-shadow:0 6px 22px rgba(0,0,0,.26);" +
        (reduce ? "" : "opacity:0;transition:opacity .22s ease;");
      document.body.appendChild(d);
      if (!reduce) {
        requestAnimationFrame(function () {
          d.style.opacity = "1";
        });
      }
      setTimeout(function () {
        if (reduce) {
          if (d.parentNode) d.parentNode.removeChild(d);
          return;
        }
        d.style.opacity = "0";
        setTimeout(function () {
          if (d.parentNode) d.parentNode.removeChild(d);
        }, 260);
      }, 1600);
    } catch (e) {}
  }

  function restore() {
    var k = contentKey();
    if (!k) return;
    // 主站页面（index / 角色页 / 规则页…）自带 app.js 的「静默浏览缓存」，它按
    // data-page-id 记住本页 scrollY 并在回来时精确复位，比这里更准。两边都动手
    // 会互相盖（一个用像素、一个用比例，差几百像素会抖）。这类页面本脚本只负责
    // "存"，不负责"恢复"；皮肤整页与升格默认页没有 app.js，由本脚本接管。
    if (HAS_APP) return;
    if (location.hash) return;              // 带锚点的链接，锚点优先
    if (!fromSite()) return;                // 直接打开的新标签页不猜
    var rec = readAll()[k];
    if (!rec) return;

    var el = scroller();
    if (!el) return;
    var max = maxY(el);
    if (max < MIN_RESTORE) return;

    var samePath = rec.p === location.pathname;
    var y = samePath ? rec.y : Math.round((rec.r || 0) * max);
    y = Math.max(0, Math.min(y, max));
    if (y < MIN_RESTORE) return;

    var userMoved = false;
    function detach() {
      ["wheel", "touchstart", "keydown", "mousedown"].forEach(function (ev) {
        window.removeEventListener(ev, onUser);
      });
    }
    function onUser() {
      userMoved = true;
      detach();
    }
    ["wheel", "touchstart", "keydown", "mousedown"].forEach(function (ev) {
      window.addEventListener(ev, onUser, { passive: true });
    });

    function apply() {
      if (userMoved) return;
      var m = maxY(el);
      var target = Math.min(y, m);
      if (target <= 0) return;
      if (Math.abs(getY(el) - target) < 4) return;
      // 必须显式 behavior:"instant"：不少皮肤在 html 上开了 scroll-behavior:smooth，
      // 用 window.scrollTo(0,y) 会变成一段动画，补位重试再把动画重新拉一遍，
      // 用户会看到"慢慢滑过去"。这里要的是落位。
      if (el === docScroller()) window.scrollTo({ top: target, behavior: "instant" });
      else if (el.scrollTo) el.scrollTo({ top: target, behavior: "instant" });
      else el.scrollTop = target;
    }

    apply();
    [120, 300, 700, 1400, 2400].forEach(function (t) {
      setTimeout(apply, t);
    });
    setTimeout(function () {
      detach();
      if (!userMoved && y > 400) toast("已接续上次读到的位置");
    }, 2500);
  }

  if (document.readyState === "complete") {
    restore();
  } else {
    window.addEventListener("load", function () {
      setTimeout(restore, 0);
    });
  }

  window.addEventListener("pagehide", save);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") save();
  });
})();
