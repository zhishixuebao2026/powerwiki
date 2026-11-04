/* ==========================================================================
   衡天⊙ PowerWiki — 明暗主题切换
   与「页面皮肤」是两条独立的轴：皮肤换整页设计，这里只切明暗。
   <head> 里的内联脚本负责首帧（读 localStorage / 系统偏好并刷底色），
   本脚本负责之后的交互：点击、多标签同步、按钮状态。
   底色由 <head> 内联 <style> 按 html[data-theme] 属性选择器给出，用的是
   同一组 data-boot-bg-* 值；切主题只改 data-theme，不再写 inline 底色，
   杜绝 JS 与 CSS 两处颜色不同步造成的整屏换色。
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
    // 底色由 <head> 内联 <style> 的 [data-theme] 属性选择器接管，
    // 改 data-theme 即自动换色；这里不再写 inline 底色，避免两处不同步。
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
