/* ==========================================================================
   卷宗（ARCHIVE）页面补丁
   原始产物把长文切成 12 个「章」，每章末尾带「上一章 / 下一章」翻页条。
   但这其实是一整页连续滚动，翻页是个假动作：它只会跳到同一页里的锚点，
   而且每章都重复一次，读起来像被切碎。

   这里把翻页条换成「章节分隔 + 进度 + 回目录」，保留分章节奏，去掉翻页语义。
   ========================================================================== */
(function () {
  "use strict";

  var STYLE_ID = "pw-archive-patch-style";
  var SEEN = "data-pw-pager-done";

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      ".chapter-pager{display:none!important}",
      ".pw-chapter-end{",
      "  display:flex;align-items:center;gap:14px;",
      "  margin:34px 0 8px;padding:0;",
      "  font-family:var(--font-mono,ui-monospace,monospace);",
      "  font-size:10.5px;letter-spacing:.16em;text-transform:uppercase;",
      "  color:var(--ink-4,#989b90);",
      "  border:0;background:none;",
      "}",
      ".pw-chapter-end::before{",
      "  content:'';flex:0 0 26px;height:1px;background:var(--line-strong,#222a2442);",
      "}",
      ".pw-chapter-end-label{white-space:nowrap}",
      ".pw-chapter-end-rule{flex:1 1 auto;height:1px;background:var(--line-soft,#222a2412)}",
      ".pw-chapter-end-toc{",
      "  display:inline-flex;align-items:center;gap:6px;",
      "  padding:4px 10px;border-radius:999px;",
      "  border:1px solid var(--line,#222a241f);",
      "  color:var(--ink-2,#49504a);",
      "  font-size:10px;letter-spacing:.08em;",
      "  cursor:pointer;background:transparent;",
      "  transition:border-color .16s ease,color .16s ease,background-color .16s ease;",
      "}",
      ".pw-chapter-end-toc:hover{",
      "  border-color:var(--accent,#a64d20);",
      "  color:var(--accent,#a64d20);",
      "  background:var(--accent-soft,#a64d201a);",
      "}",
      ".pw-chapter-end.is-final .pw-chapter-end-label{color:var(--accent,#a64d20)}",
      "@media (max-width:720px){",
      "  .pw-chapter-end{font-size:9.5px;gap:10px;margin:26px 0 6px}",
      "  .pw-chapter-end::before{flex-basis:14px}",
      "}",
    ].join("\n");
    var tag = document.createElement("style");
    tag.id = STYLE_ID;
    tag.textContent = css;
    document.head.appendChild(tag);
  }

  function openChapterIndex() {
    /* 复用原页面的「章节目录」入口，不另造一套 */
    var btn =
      document.querySelector(".icon-button.topbar-menu") ||
      document.querySelector('[aria-label="打开章节目录"]') ||
      document.querySelector(".rail-action");
    if (btn) btn.click();
    else window.scrollTo({ top: 0, behavior: "smooth" });
    document.dispatchEvent(new CustomEvent("pw:archive-toc"));
  }

  function relabel() {
    injectStyle();
    var pagers = document.querySelectorAll(".chapter-pager:not([" + SEEN + "])");
    if (!pagers.length) return;

    var total = document.querySelectorAll(".chapter-pager").length;
    var i = 0;
    Array.prototype.forEach.call(pagers, function (pager) {
      i += 1;
      var isFinal = pager.querySelector(".pager-link--next") &&
        !pager.querySelector(".pager-link--next").getAttribute("href").match(/^#sec-/);

      var wrap = document.createElement("div");
      wrap.className = "pw-chapter-end" + (isFinal ? " is-final" : "");

      var label = document.createElement("span");
      label.className = "pw-chapter-end-label";
      label.textContent = isFinal
        ? "全文完 · " + String(i).padStart(2, "0") + " / " + String(total).padStart(2, "0")
        : "章节结束 · " + String(i).padStart(2, "0") + " / " + String(total).padStart(2, "0");

      var rule = document.createElement("span");
      rule.className = "pw-chapter-end-rule";

      var toc = document.createElement("button");
      toc.type = "button";
      toc.className = "pw-chapter-end-toc";
      toc.textContent = isFinal ? "回到卷首 ↑" : "章节目录";
      toc.addEventListener("click", function () {
        if (isFinal) window.scrollTo({ top: 0, behavior: "smooth" });
        else openChapterIndex();
      });

      wrap.appendChild(label);
      wrap.appendChild(rule);
      wrap.appendChild(toc);
      pager.parentNode.replaceChild(wrap, pager);
    });
  }

  function boot() {
    relabel();
    /* React 是异步渲染的，章节是分块挂上来的 */
    var pending = null;
    var observer = new MutationObserver(function () {
      if (pending) return;
      pending = requestAnimationFrame(function () {
        pending = null;
        relabel();
      });
    });
    observer.observe(document.body, { childList: true, subtree: true });
    setTimeout(function () { observer.disconnect(); }, 8000);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();

/* 这个页面底部自带一条固定工具栏（nav.mobile-dock），把角落切换器抬上去，别叠在一起 */
(function () {
  "use strict";
  function detectBar() {
    var vh = window.innerHeight;
    var best = 0;
    var all = document.querySelectorAll("body *");
    for (var i = 0; i < all.length; i++) {
      var el = all[i];
      var cs = getComputedStyle(el);
      if (cs.position !== "fixed" || cs.visibility === "hidden") continue;
      if (el.classList.contains("pw-edition-dock") || el.closest(".pw-edition-dock")) continue;
      var r = el.getBoundingClientRect();
      if (r.height < 36 || r.height > 180) continue;
      if (r.width < window.innerWidth * 0.5) continue;
      if (r.bottom < vh - 26) continue;
      if (r.top > vh) continue;
      best = Math.max(best, r.height);
    }
    return best;
  }
  function lift() {
    var bar = detectBar();
    document.documentElement.style.setProperty(
      "--pw-edition-dock-offset",
      (bar ? Math.round(bar + 10) : 0) + "px"
    );
  }
  function boot() {
    [600, 1400, 2800].forEach(function (t) { setTimeout(lift, t); });
    window.addEventListener("resize", lift);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
