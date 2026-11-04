/* ==========================================================================
   衡天⊙ PowerWiki — 明暗主题切换
   与「页面皮肤」是两条独立的轴：皮肤换整页设计，这里只切明暗。
   <head> 里的内联脚本负责首帧（读 localStorage / 系统偏好并刷底色），
   本脚本负责之后的交互：点击、多标签同步、按钮状态。
   底色一律从 html 的 data-boot-bg-* 读，与首帧用的是同一组值，
   避免切主题时 html 的 inline 底色还停在旧色、又整屏换一次颜色。
   ========================================================================== */
(function () {
  "use strict";

  var KEY = "pw_theme_v2";
  var root = document.documentElement;
  var btn = document.getElementById("theme-toggle-btn");
  if (!btn) return;                          // 皮肤页没有主站顶栏
  if (root.hasAttribute("data-pw-edition")) return;

  function canvasFor(theme) {
    return root.getAttribute(theme === "dark" ? "data-boot-bg-dark" : "data-boot-bg-light")
      || (theme === "dark" ? "#080d11" : "#f1f2ed");
  }

  function apply(theme, persist) {
    if (theme !== "light" && theme !== "dark") theme = "light";
    root.setAttribute("data-theme", theme);
    var canvas = canvasFor(theme);
    // html 的 inline 底色必须跟着换：body 比视口短时露出来的就是它
    root.style.backgroundColor = canvas;
    var meta = document.getElementById("theme-color-meta");
    if (meta) meta.setAttribute("content", canvas);
    btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    btn.setAttribute("aria-label", theme === "dark" ? "切换到亮色主题" : "切换到暗色主题");
    if (persist) {
      try { localStorage.setItem(KEY, theme); } catch (e) {}
    }
  }

  var timer = null;
  function withTransition(fn) {
    // experience.css 里 html.theme-transitioning 给各块加了短过渡
    root.classList.add("theme-transitioning");
    fn();
    clearTimeout(timer);
    timer = setTimeout(function () {
      root.classList.remove("theme-transitioning");
    }, 380);
  }

  btn.addEventListener("click", function (e) {
    e.preventDefault();
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    withTransition(function () { apply(next, true); });
  });

  // 另一个标签切了主题：跟着切，但不重复写 localStorage
  window.addEventListener("storage", function (e) {
    if (e.key === KEY && (e.newValue === "light" || e.newValue === "dark")) {
      withTransition(function () { apply(e.newValue, false); });
    }
  });

  // 初始化：把 aria、meta、inline 底色对齐到 <head> 已经定好的主题。
  // 不写 localStorage —— 首次访问时系统偏好的落盘由 <head> 脚本负责。
  apply(root.getAttribute("data-theme"), false);
})();
