/* ==========================================================================
   KALMIA（观象台）页面补丁
   1. 原产物的移动端底栏（.dock）只在滚动后滑出，且停在视口底部；
      印章（.pw-edition-dock）需要在底栏出现时让位，由 editions.js 实测处理，
      这里只保证底栏出现时正文末段不被压住。
   2. 原产物的字体文件没随包发出，构建阶段已把字体族改指站内自托管字体
      （build_site.py 的 patch_skin_fonts），这里只补两处观感细节。
   ========================================================================== */
(function () {
  "use strict";

  var STYLE_ID = "pw-kalmia-patch-style";

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    var css = [
      /* 底栏出现时给正文留出落脚空间 */
      "html[data-pw-edition='kalmia'] main{padding-bottom:calc(96px + env(safe-area-inset-bottom,0px))}",
      "html[data-pw-edition='kalmia'] .colophon{margin-bottom:120px}",
      /* 印章在深色顶栏上有一层发光底，和皮肤的圆角金属件对齐 */
      "html[data-pw-edition='kalmia'] .pw-edition-toggle,",
      "html[data-pw-edition='kalmia'] .pw-edition-home-btn{",
      "  border-color:color-mix(in srgb,var(--brass,#c9a35a) 34%,transparent);",
      "  box-shadow:0 6px 20px rgba(0,0,0,.34),0 0 0 1px color-mix(in srgb,var(--brass,#c9a35a) 12%,transparent) inset;",
      "}",
    ].join("\n");
    var tag = document.createElement("style");
    tag.id = STYLE_ID;
    tag.textContent = css;
    document.head.appendChild(tag);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", injectStyle);
  } else {
    injectStyle();
  }
})();
