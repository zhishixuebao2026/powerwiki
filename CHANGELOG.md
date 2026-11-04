# 更新记录

按天记录做了什么、为什么做。条目对应分支 `arena/7ea6b694-powerwiki` 上的提交，
`(abc1234)` 是提交短哈希，可以直接 `git show` 看细节。
皮肤的设计取舍写在 `README.md`，用户的硬性要求与验收方式写在 `docs/需求与约定.md`。

## 2026-11-05（上午）

- **修：御兔默认页反复闪屏（第三次回归，这次连根删除）**
  复盘「一直修不好」的原因：前两轮各修掉一个来源，却每次都把
  `body > main { animation: pw-page-arrive ... both }` 当成无害的入场动效
  特意保留下来。该动效每次加载都让 `main` 从 `opacity: .72` 淡入到 1
  （实测持续 400–750ms）、并伴随 `translateY(0→8px)`，逐帧录屏显示
  御兔浅色冷启动 `t+0ms` 纯白 → `t+409ms` 整屏跳变（色差 39/46），
  `transform` 还会把 `position:fixed` 的顶栏 / 悬浮坞锁进 main 的包含块。
  此外 `@keyframes pw-page-arrive-fade`（≤1080px 的第二套纯淡入）与
  `.motion-reveal` 死代码（全站 0 个元素、无 JS 会加 `has-motion-reveal`）一起清除。
  现在首帧即终态：`main` 全程 `opacity:1 / transform:none`，零淡入、零位移。
- **首帧底色改由 `<head>` 内联 CSS 负责**：生成器按页面把两组颜色写进
  `:where(html) / :where(html) > :where(body)` 规则（优先级 0，外链 CSS 到达后
  无缝接管）；内联脚本与 `theme.js` 不再写 `root.style.backgroundColor`，
  只同步 `theme-color` meta，切主题仅改 `data-theme`。三层底色（html / body /
  meta）在 7 个页面 × 明暗两套下逐项一致。`theme-color` 静态值也按页面写入，
  不再是全站写死的 `#f6f7f4`。
- **首屏阻塞减负**：两个中文可变字体 CSS（各约 99 KB、205 个 `@font-face`
  全部 `font-display: swap`、不含任何布局规则）改为 `media=print` + `onload`
  非阻塞加载并加 `<noscript>` 兜底；阻塞样式表 469 KB → 271 KB，冷启动白屏
  等待从约 450ms 降到 250–300ms，且不会引入布局闪现。
- `service-worker.js` 版本升 `pw-v5`，确保已缓存旧 CSS 的用户拿到新样式。
- **验收（真实 Chromium）**：御兔浅色冷启动 6 次中 4 次零白帧零跳变，
  深色冷启动、跨页导航（角色列表→御兔、月面皮肤→主站）全部零白帧；
  上一轮完整功能验收 0 失败（搜索 17 条、量级筛选 13 张、主题 / 目录 /
  字号 / 宽屏 / 回到顶部均正常）；1440/768/390/320 × 深浅截图零 JS 报错、
  零横向溢出、固定元素零越界；  离线缓存命中 `pw-v5`。

## 2026-11-05（下午）

- **修：御兔页局部闪屏（左手光团背景 / 右手月亮立绘）**
  整屏换色修掉后，慢网下仍看到两处局部「啪」地亮起：左手光团 = 页头大气图
  `lunar-observatory.jpg`、右手月亮 = 角色立绘 `official-portrait.png`。根因是两张
  首屏大图（215 KB / 88 KB）无预取、容器透明，慢网下图片晚到时整块瞬间覆盖占位底色。
  修复：生成器在 `<head>` 为页头图与立绘加 `<link rel=preload as=image>`，图片加
  `fade-on-load` 类先 `opacity:0`、就绪后 0.2s 淡入；`body.character-site::before`
  大气层同样先透明、页头图 load 后加 `atmosphere-ready` 淡入，容器铺与图同色调占位底色。
  无 JS 时这些规则不生效，图片照常立即显示，不损坏。
- **修：脚本里错误的二次预取导致 404**
  `pwFadeImages()` 原先从 `--char-atmosphere` 解析出 `../img/...` 当文档相对路径去
  `new Image().src`，从 `/character/yutu.html` 解析成 `/img/...`（缺 `static/`）凭空 404；
  CSS 里 `url("../img/...")` 本就相对 CSS 文件解析、指向正确。改为复用页头图的 `load`
  事件点亮 `atmosphere-ready`，不再重复预取。
- `service-worker.js` 版本升 `pw-v6`；构建重跑确认御兔页含 2 个 preload + 2 个
  `fade-on-load`。
- **验收（真实 Chromium）**：正常网络下左右首屏图均 `is-loaded`、控制台零报错零 404；
  Slow 4G 节流逐帧采样左 1/3 / 右 1/3 中心色，**0 次明显跳变**（阈值 15）——图片平滑
  淡入，不再突发覆盖。

## 2026-11-05（凌晨）

- **修：右下角工具坞、目录按钮、字号按钮全都点不开**
  比上一轮的主题问题更严重：`d00f844` 的 PWA 改造把 60 KB / 1514 行的
  `static/js/app.js` 交互引擎**整份替换**成 7.6 KB 的安装脚本，于是搜索、量级筛选、
  角色筛选、章节目录、字号 / 宽屏、回到顶部、滚动进度的事件绑定一起消失；
  右下角那个带横杠的 ☰ 按钮点了完全没有反应。从 `9c7a550` 恢复历史交互引擎，
  去掉会和现有实现打架的 `initTheme`（由 `theme.js` 负责）与 `initMotionReveal`
  （由 `chrome.js` 的 `pw-will-rise` 负责），其余初始化全部还原。
  实测：☰ 打开目录 / ESC 关闭、`--doc-font-scale 1.0000→1.0968`、`wide-doc-mode`、
  回到顶部 scrollY 归零、首页搜索 17 条结果、量级筛选 13 张卡片，逐一通过。
- **拆出 `static/js/pwa.js`**：只保留静默的 SW 注册、预热、独立窗口安全区与
  左边缘返回手势；PWA 能力不丢，但不再承担任何站内交互。
- **全站下线「装成 App / 下载本地」提示**（按用户要求）：删掉顶栏、抽屉、
  皮肤印章组、皮肤侧栏补丁里注入的全部 `[data-pw-install]` 按钮，删掉 iOS 三步
  引导面板与 `app.css` 里整套安装按钮样式；生成器不再产出 `INSTALL_ICON`。
  10 个代表页面复查：`install=0`、无引导面板、正文无相关文案。
- **修：左下角字号条太大、皮肤与主页小圆钮大小不一**
  `experience.css` 的阅读工具栏整体缩小：桌面竖条 64×163 → 54×141，
  390 横条 142×48 → 118×36，768 起把 `15.5px` 读数也收起（164 → 126 宽）。
  `editions.css` 把印章一组的 home / toggle 统一成 **30×30 正圆**，并撤掉
  ≤720px 的尺寸覆盖——主页、皮肤页、桌面、手机四处现在完全一致。
- `service-worker.js` 的 `SHELL` 加 `pwa.js`，`VERSION` 升 `pw-v4`；
  实测缓存命中 `pwa.js` / `app.js`，controller 接管。
- 验收：真实 Chromium，1440 / 768 / 390 / 320 × 深浅两套主题，
  7 张截图，零 JS 报错、零请求失败、零横向溢出、固定元素零重叠。
- **规则文档已同步**：`docs/需求与约定.md` 的「#16」与「一·五、装成 App 的验收」已按
  「添加到主屏幕只是方便自己、全站不做安装提示」更新——保留 manifest / 独立窗口等能力，
  但删除全站安装引导入口要求；README 对应「待确认」标注一并清除。

## 2026-11-04（晚）

- **修：默认皮肤全站换不了明暗主题**
  顶栏的太阳按钮一直在，但点了没反应：`static/js/app.js` 在 PWA 改造时被重写成只管
  安装 / 离线，主题切换的事件绑定整段丢了（CSS 里 `html.theme-transitioning` 还留着，
  却没人再加这个类）。现在拆出独立的 `static/js/theme.js`：点击切 `data-theme`、写
  `pw_theme_v2`、同步 `theme-color` meta 与 html 首帧底色、切太阳 / 月亮图标和 aria 状态，
  多标签通过 `storage` 事件跟随；`theme-transitioning` 的短过渡这下真正生效。
  首页 / 量级 / 角色 / 规则 / 材质 / 检索 / 档位详情页逐个点过，全部能切。
- **修：御兔默认页又闪屏**
  两个叠加原因：`<head>` 内联脚本把首帧底色写死成 `#f6f7f4 / #090b10`，而页面最终生效的
  `--bg-canvas` 是 `#f1f2ed / #080d11`，御兔页更被 `experience.css` 覆盖成
  `#edf3f6 / #071320`，样式表一到达就整屏换一次色；11-02 加的
  `@view-transition { navigation: auto }` 又把跨页切换做成全屏交叉淡入，
  正好把这次换色放大（需求 #6、`8507c08` 修过的老问题回归）。现在生成器按页面把两组
  底色写进 `data-boot-bg-light/dark`，首帧脚本与 `theme.js` 共用；
  `experience.css` / `polish.css` 的跨文档过渡一律关掉，只保留 `main` 的
  `pw-page-arrive` 入场动效。实测 9 个页面 × 明暗两套首帧底色与最终底色完全一致，
  32 张截图 × 四档宽度无白闪、无 JS 报错、无横向溢出。
- **离线壳层补上主题脚本**：`service-worker.js` 的 `SHELL` 加 `theme.js`，`VERSION`
  升到 `pw-v3`，装到主屏后断网也能换主题（实测缓存命中、controller 接管）。

## 2026-11-04（下午）

- **可以装到 iPhone 主屏幕，打开是全屏 App 而不是浏览器**
  之前「添加到主屏幕」只是存了个书签，点开还是跳 Safari，因为没有 manifest、
  没有 `apple-mobile-web-app-capable`，也不是独立窗口。
  现在补齐：`manifest.webmanifest`（standalone、scope、4 个图标、4 个快捷方式）、
  `apple-touch-icon` 180×180、`apple-mobile-web-app-*` 三件套、站点图标，
  独立窗口下顶栏让出状态栏（`--pw-top-inset` 实测写入）、底部让出 Home 指示条，
  并在主屏幕启动时接管左边缘滑动返回。
- **页面内多了「装成 App」入口**
  顶栏、移动端抽屉、皮肤页的印章那一组、两套整页产物的站内导航里都有了。
  Chrome / Edge / Android 走 `beforeinstallprompt` 弹原生安装框；
  iOS Safari 没有安装 API，点了给「分享 → 添加到主屏幕」的三步图文引导。
- **离线可用**
  新增 `service-worker.js`：首屏壳层（首页 / 规则 / 量级 / 角色 / 材质 / 样式 / 脚本 / 图标）
  装好后进缓存，页面导航网络优先、断网回缓存、再断网回 `offline.html`；
  样式与脚本走网络优先（改完立刻生效），字体图片缓存优先。
  实测：拔掉服务器后首页照常打开，没缓存过的页面落到离线提示页。
- **修：离线兜底页方框字**
  第一版兜底页引用了站内字体表，服务器一停字体也拿不到，整页中文变方框。
  改成纯系统字体栈，并且不加载任何外部资源。

## 2026-11-04

- **新增皮肤「月面」** (4df8395)
  把 `TH页面/opus-5.5-high御兔量级页面.zip` 里的 `dist/index.html` 整页纳入，
  挂到**御兔角色页**（`/character/yutu.html`）而不是整个角色栏目：
  `data/editions.json` 的 `pages` 支持单页键 `character-yutu`，构建器把它当
  `skin_section` 传给 `render_shell()`，因此只有那一页出现「默认 / 月面」。
  默认皮肤同时登记同名键指回 `character/yutu.html`，两边互跳。
- **修：印章压住侧栏目录** (4df8395)
  切换器的避让定位只量 `position: fixed`，而整页产物的侧栏是 `sticky` 的，
  于是印章贴回左下角盖住目录最后几行。现在 sticky 也算障碍；尚未滚进视口的
  sticky 侧栏预先记账、滚动停下后复测；侧栏判定放宽为「靠边 8% 以内且够高够宽」。
- **修：月面皮肤导航缺字** (4df8395)
  那份产物的字体是按正文用字裁的子集，缺字时**留白**（不是画方框），
  「站内其他栏目」「材质数据库」少了「站」「库」。导航与切换器改用站内自托管的思源黑体。
- **皮肤改名** (4df8395)
  `kalmia` → `observatory`「观象台」。kalmia 是模型名不是样式名，皮肤按设计语言命名。
  id / source / patch / thumb / 目录一条龙对齐，旧目录删除。

## 2026-11-03

- **皮肤「观象台」接入站内导航** (29f5fa0)
  整页产物原本是单向门：进去后没有任何回主站的入口。现在桌面侧栏
  （`.rail-sticky` 里、插在「目录 · CONTENTS」之前）和移动抽屉（`.drawer-scroll` 顶部）
  各挂一组「站内其他栏目」。React 壳晚于 `DOMContentLoaded` 挂载，
  所以用定时重试 + `MutationObserver`，不是一次 `querySelector` 就完事。
- **新增皮肤「观象台」** (1747cf5)
  `TH页面/KALMIA衡天量级体系.zip` 整页产物接入规则页，夜观 / 昼测双主题。
  ZIP 里缺 `assets/fonts/`，构建时用 `font_rewrite` 把四个字体族改指站内自托管字体。

## 2026-11-02

- **README 记录本轮 bug 与验证脚本** (ea64efe)
- **修：皮肤页顶栏发糊** (a7fef6a)
  原页面只写了 `-webkit-backdrop-filter`，Chrome 里标准属性缺失，正文从顶栏透出来。
- **修：卷宗脚注被挤成竖排、滚动进入锁在透明态** (d2b3203)
  ≤420px 时第 4 段落进 14px 窄列；`animation-timeline: view()` 换成 `IntersectionObserver`。

## 2026-11-01

- **焦点环不再改动元素圆角** (051065f)
- **悬浮层逐块避让 + 全面打磨** (2ce3430)
  标题去重、筛选条渐隐、深色印章、排版与动效统一。

## 2026-10-31

- **切换器缩成可折叠圆点并自动避让；首屏图片 4.2MB → 0.4MB** (9c7a550)
  性能优化只删冗余请求，不削减视觉效果。
- **切换器只在有对应页面的皮肤间切换 + 撤掉卷宗页的假翻页** (6bea10a)
- **页面皮肤（整页换设计）+ 左下角皮肤切换器** (9d6cab2)

## 2026-10-30

- **消灭首帧白闪与切皮肤时的全屏交叉淡入** (8507c08)
- **`data-skin` 外观皮肤轴（已废弃）** (ad7f88d)
  只换调色板不算皮肤，被「整页换设计」方案取代；提交保留以备查。
- **同步 10.30 版《弗坦定级》与《衡天体系第五版》** (0146e25)
- **修复移动端章节抽屉、重做弗坦页明暗** (35cadb1)

## 素材来源

| 皮肤 | 来源 ZIP（仓库 `zhishixuebao2026/testonly`，目录 `TH页面/`） |
|---|---|
| 卷宗 | `DS4.1MAX＆OPUS5.5MAX材质量级页面.zip` |
| 星图 | `opus-5.5-low＆GLM5.2MAX＆mimo-v2.6-flash＆gemini3.7flash材质页面.zip` |
| 观象台 | `KALMIA衡天量级体系.zip` |
| 月面 | `opus-5.5-high御兔量级页面.zip` |

产物一律只当输入：整页 HTML 放 `skins/_source/`，构建期打补丁，
**不手改生成出来的 HTML**。
