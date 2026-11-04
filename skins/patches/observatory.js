/* ==========================================================================
   观象台（原 KALMIA 整页产物）页面补丁
   1. 原产物的移动端底栏（.dock）只在滚动后滑出，且停在视口底部；
      印章（.pw-edition-dock）需要在底栏出现时让位，由 editions.js 实测处理，
      这里只保证底栏出现时正文末段不被压住。
   2. 原产物的字体文件没随包发出，构建阶段已把字体族改指站内自托管字体
      （build_site.py 的 patch_skin_fonts），这里只补两处观感细节。
   ========================================================================== */
(function () {
  "use strict";

  var STYLE_ID = "pw-kalmia-patch-style";


  /* ── 站内导航：这个皮肤是整页独立产物，原本没有任何回主站的入口。
        在侧栏（桌面）和抽屉（移动）底部补一组「站内其他栏目」，
        让它真正成为网站的一个页面，而不是一扇单向门。 ───────────────── */
  var SITE_LINKS = [
    ["量级分类", "tiers.html"],
    ["角色档案", "characters.html"],
    ["规则原文", "rules.html"],
    ["材质数据库", "materials.html"],
    ["站点首页", "index.html"],
  ];

  function siteNavHTML() {
    var base = new URL("../../", location.href).href;
    var items = SITE_LINKS.map(function (pair) {
      return (
        '<a class="pw-site-link" href="' + base + pair[1] + '">' +
        '<span class="pw-site-dot" aria-hidden="true"></span>' + pair[0] + "</a>"
      );
    }).join("");
    return (
      '<div class="pw-site-nav" data-pw-site-nav="1">' +
      '<p class="pw-site-cap">站内其他栏目</p>' + items +
      "</div>"
    );
  }

  // 侧栏的「目录 · CONTENTS」标题是 .rail-sticky 里排在滚动区前面的兄弟节点，
  // 所以要把导航插到标题之前，否则会读成「目录」的一部分。
  function railHost() {
    var sticky = document.querySelector(".rail-sticky");
    if (sticky) return sticky;
    return document.querySelector(".rail-scroll");
  }

  function insertSiteNav(host) {
    if (!host || host.querySelector("[data-pw-site-nav]")) return;
    var wrap = document.createElement("div");
    wrap.innerHTML = siteNavHTML();
    var cap = host.querySelector(":scope > .rail-cap, :scope > .toc-cap, :scope > .drawer-cap");
    // 放在最前面：侧栏目录一千多像素高，追加到末尾等于永远看不见。
    host.insertBefore(wrap.firstChild, cap || host.firstChild);
  }

  function mountSiteNav() {
    insertSiteNav(railHost());
    insertSiteNav(document.querySelector(".drawer-scroll"));
  }

  function watchSiteNav() {
    // 侧栏/抽屉是 React 在 DOMContentLoaded 之后才挂上去的，
    // 所以不能"第一次找不到就收工"，要留几个时间点反复补。
    mountSiteNav();
    [300, 900, 1800, 3200, 5000].forEach(function (t) { setTimeout(mountSiteNav, t); });
    if (!window.MutationObserver) return;
    var mo = new MutationObserver(function () { mountSiteNav(); });
    function observeHosts() {
      var hosts = [railHost(), document.querySelector(".drawer-scroll")];
      for (var i = 0; i < hosts.length; i++) {
        if (!hosts[i] || hosts[i].dataset.pwNavWatched === "1") continue;
        hosts[i].dataset.pwNavWatched = "1";
        mo.observe(hosts[i], { childList: true });
      }
    }
    [600, 1500, 3000].forEach(function (t) { setTimeout(observeHosts, t); });
  }

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      /* 底栏出现时给正文留出落脚空间 */
      "html[data-pw-edition='observatory'] main{padding-bottom:calc(96px + env(safe-area-inset-bottom,0px))}",
      "html[data-pw-edition='observatory'] .colophon{margin-bottom:120px}",
      /* 侧栏目录滚到底时给印章让出位置，别让最后一项目录被圆钮压住 */
      "html[data-pw-edition='observatory'] .rail-scroll{padding-bottom:64px}",
      /* 站内导航 */
      ".pw-site-nav{margin:0 0 16px;padding-bottom:12px;border-bottom:1px solid var(--line-soft,var(--line,#ffffff1a))}",
      /* 小标题跟着皮肤自己的排版语言走（中文标签不要拉字距，否则会被排成方块阵） */
      ".pw-site-cap{font-family:inherit;font-size:11.5px;letter-spacing:.04em;color:var(--ink-4,var(--ink-3,#8a8a86));margin:0 0 6px;opacity:.85}",
      ".pw-site-link{display:flex;align-items:center;gap:9px;padding:7px 9px;border-radius:9px;color:var(--ink-2,var(--ink-3,#8a8a86));text-decoration:none;font-size:12.5px;line-height:1.35;transition:background-color .16s ease,color .16s ease}",
      ".pw-site-link:hover,.pw-site-link:focus-visible{background:var(--surface2,rgba(255,255,255,.05));color:var(--brass,#c9a35a)}",
      ".pw-site-dot{width:5px;height:5px;border-radius:50%;background:currentColor;opacity:.45;flex:0 0 auto}",
      ".pw-site-link:hover .pw-site-dot{opacity:1}",
      /* 印章在深色顶栏上有一层发光底，和皮肤的圆角金属件对齐 */
      "html[data-pw-edition='observatory'] .pw-edition-toggle,",
      "html[data-pw-edition='observatory'] .pw-edition-home-btn{",
      "  border-color:color-mix(in srgb,var(--brass,#c9a35a) 34%,transparent);",
      "  box-shadow:0 6px 20px rgba(0,0,0,.34),0 0 0 1px color-mix(in srgb,var(--brass,#c9a35a) 12%,transparent) inset;",
      "}",
    ].join("\n");
    var tag = document.createElement("style");
    tag.id = STYLE_ID;
    tag.textContent = css;
    document.head.appendChild(tag);
  }

  function boot() {
    injectStyle();
    watchSiteNav();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
