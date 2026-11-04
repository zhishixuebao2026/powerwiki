/* ==========================================================================
   月面（御兔卷宗整页产物）页面补丁
   1. 原产物是一份自包含的单页，进去以后没有回主站的入口 ——
      这里在桌面目录栏顶部和移动端抽屉目录顶部各挂一组「站内其他栏目」。
   2. 产物的目录栏是 React 挂载后才有的，所以用定时重试 + MutationObserver。
   3. 产物自带的是按正文用字裁过的字体子集（YT Sans 里没有「站」「库」这些字），
      站内导航不能跟着它走，改用站内自托管的思源黑体。
   ========================================================================== */
(function () {
  "use strict";

  var STYLE_ID = "pw-moonfile-patch-style";

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
      '<button type="button" class="pw-site-app" data-pw-install hidden>' +
      '<span class="pw-site-dot" aria-hidden="true"></span>装成 App</button>' +
      "</div>"
    );
  }

  function insertNav(host, before) {
    if (!host || host.querySelector("[data-pw-site-nav]")) return;
    var wrap = document.createElement("div");
    wrap.innerHTML = siteNavHTML();
    host.insertBefore(wrap.firstChild, before || host.firstChild);
  }

  function mountSiteNav() {
    // 桌面：正文左侧的 sticky 目录，插在「Contents · 目录」小标题下面。
    var deskToc = document.querySelector("nav.sticky.top-24") || document.querySelector("nav[class*='sticky'][class*='top-24']");
    if (deskToc) {
      var kicker = deskToc.querySelector(".kicker");
      insertNav(deskToc, kicker ? kicker.nextSibling : deskToc.firstChild);
    }
    // 移动：右上角汉堡打开的抽屉目录，插在「Contents · 目录」标题下面。
    var drawerToc = document.querySelector("nav.absolute[class*='right-0']");
    if (drawerToc) {
      var head = drawerToc.querySelector(":scope > div");
      insertNav(drawerToc, head ? head.nextSibling : drawerToc.firstChild);
    }
  }

  function watchSiteNav() {
    mountSiteNav();
    [300, 900, 1800, 3200, 5000].forEach(function (t) { setTimeout(mountSiteNav, t); });
    if (!window.MutationObserver) return;
    var mo = new MutationObserver(function () { mountSiteNav(); });
    var body = document.body || document.documentElement;
    mo.observe(body, { childList: true, subtree: true });
  }

  var SITE_FONT_SHEET = "static/fonts/noto-sans-sc/index.css";
  var SITE_FONT_STACK = '"Noto Sans SC Variable", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif';

  function injectSiteFont() {
    // 子集字体缺字时不是画方框、而是留白，不换字体这行链接会缺字。
    if (document.getElementById("pw-moonfile-site-font")) return;
    var href = new URL("../../" + SITE_FONT_SHEET, location.href).href;
    if ([].some.call(document.querySelectorAll('link[rel="stylesheet"]'), function (l) { return l.href === href; })) return;
    var link = document.createElement("link");
    link.id = "pw-moonfile-site-font";
    link.rel = "stylesheet";
    link.href = href;
    document.head.appendChild(link);
  }

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      // 产物自带的主题变量：--ink / --line / --seal / --bg，深浅两套都在
      ".pw-site-nav{margin:10px 0 14px;padding-bottom:12px;border-bottom:1px solid var(--line,#3c2a1824)}",
      ".pw-site-nav{font-family:" + SITE_FONT_STACK + "}",
      ".pw-site-cap{font-family:inherit;font-size:11px;letter-spacing:.06em;color:var(--muted,var(--ink,#1c1915));opacity:.6;margin:0 0 4px;padding:0 10px}",
      ".pw-site-link{display:flex;align-items:center;gap:9px;padding:6px 10px;border-radius:6px;color:var(--ink,#1c1915);text-decoration:none;font-family:inherit;font-size:12.5px;line-height:1.35;opacity:.82;transition:background-color .16s ease,opacity .16s ease}",
      ".pw-site-link:hover,.pw-site-link:focus-visible{background:color-mix(in srgb,var(--seal,#b8302a) 9%,transparent);opacity:1}",
      ".pw-site-dot{width:5px;height:5px;border-radius:50%;background:var(--seal,#b8302a);opacity:.5;flex:0 0 auto}",
      ".pw-site-link:hover .pw-site-dot{opacity:1}",
      // 「装成 App」：外观跟着站内链接走，省得和皮肤自己的按钮打架
      ".pw-site-app{display:flex;align-items:center;gap:9px;width:100%;margin:2px 0 0;padding:6px 10px;border:0;border-radius:6px;background:transparent;color:var(--ink,#1c1915);font:inherit;font-size:12.5px;line-height:1.35;opacity:.82;text-align:left;cursor:pointer;appearance:none;-webkit-appearance:none;border:0;outline-offset:2px}",
      ".pw-site-app:hover,.pw-site-app:focus-visible{background:rgba(128,128,128,.12);opacity:1}",
      ".pw-site-app[hidden]{display:none!important}",
    ].join("\n");
    var tag = document.createElement("style");
    tag.id = STYLE_ID;
    tag.textContent = css;
    document.head.appendChild(tag);
  }

  function boot() {
    injectSiteFont();
    injectStyle();
    watchSiteNav();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
