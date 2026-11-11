# 更新记录

按天记录做了什么、为什么做。条目对应分支 `arena/7ea6b694-powerwiki` 上的提交，
`(abc1234)` 是提交短哈希，可以直接 `git show` 看细节。
皮肤的设计取舍写在 `README.md`，用户的硬性要求与验收方式写在 `docs/需求与约定.md`。

## 2026-11-11（顶栏色块撤回）· 删掉我自己加的纯色遮挡条与顶栏重绘，只保留几何

用户实测反馈：皮肤顶部被加了一条与皮肤设计割裂的**纯色色块／黑条**。复现确认（standalone 截图 + 逐像素采样）：`检字` / `金策` / `同心符环` 顶部 y=10/40/60/90 全是完全相同的 `(242,238,229)` 纯色，纸纹、渐变、金箔质感全部被盖掉。根因是上一版（`pw-v37`）为了通过自造的「15 点全宽不透明覆盖」指标，加了两处本不该有的东西：

- `statusBar()` 创建了一条 `position:fixed; top:0; height:54px; z-index:40` 的**独立纯色遮挡条**，颜色取 `bgOf(body)` 全局背景色 —— 深色皮肤取到深色就是黑条，浅色皮肤就是米白色块；
- `bgOf()` 沿祖先链找不透明色，半透明顶栏会跳到 `body` 返回它的色，再用 `[data-pw-bar-bg]` + `background-color:...!important` **把顶栏重绘成纯色**，皮肤自己的毛玻璃／渐变／纹理被覆盖。

这两处都不是用户要的「顶栏贴最上」，是我多加的。本次**外科式删除，几何逻辑一行不动**：

- 删除 `statusBar()` 及 `[data-pw-statusbar]` CSS；删除 `alphaOf()` / `solid()` / `bgOf()` 及 `[data-pw-bar-bg]` CSS、顶栏重绘块、`refreshBars()`。生成器与 36 套产物的注入脚本里，`background-color` / `backgroundColor` / `--pw-bar-bg` / `--pw-status-bg` / `data-pw-statusbar` / `pw-safe-bar` 字样**全部为 0**，只剩 `top` / `padding-top` / `height` / `box-sizing` / `--pw-safe-top` 这些几何属性 —— 物理上不可能再产生色块。
- 保留：顶栏 `top:0 !important`、内容 `padding-top: calc(原值 + 54px)`、容器 `height: calc(原高 + 54px)` + `box-sizing:border-box`。皮肤**自己的**顶栏背景（含半透明／渐变／纹理／金箔）从 y=0 自然铺满状态栏区，是皮肤原设计。贴顶悬浮控件下移、全屏抽屉 padding、`hasStickyBar()` 区分 sticky/fixed、`padBody()` 可撤销让位、`[200,700,1500,3000]` 分批重扫与滚动节流，全部原样保留。
- **明确取舍**：不再有遮挡条后，无横贯顶栏的沉浸式皮肤滚动时，正文会进入顶部 54px 状态栏区 —— 这是「不带不透明顶栏的长页面」的固有行为（iOS Safari 亦然），不是新增缺陷，且打开时的首屏状态栏区 36/36 无任何文字。宁可保留这个皮肤原设计，**也不再加任何色块**。

**验证**：36 套产物页注入脚本静态扫描颜色字样全 0；standalone 全量 36/36 —— 无遮挡/重绘注入元素、顶栏 `top=0`、内容文字 ≥54px、状态栏区首屏 36/36 无文字、顶栏 computed 背景色与网页版逐字符一致（如 `检字 color(srgb …/0.78)`、`金策 …/0.95`、`同心符环 rgba(0,0,0,0)`）、0 横向溢出、0 JS 报错、0 个 4xx；网页版 36/36 零变化（`data-pw-standalone` 不出现、无注入元素）。像素采样：修复前顶部为恒定纯色，修复后为 `(240,234,224)→(241,236,226)→(238,234,223)` 的纸纹起伏。修复前后严格同条件对比图（同服务器、同为初始态、同样等待）仅本地留存、不入库。**定级原文与角色页正文零改动** —— 36 个改动 HTML 剥离注入后逐字一致，`character/` 与 `skins/_source/` 零改动。SW 升 `pw-v38`。

> 修正三处验证脚本自身的假阴性（不影响产物）：① 复用页面对象只等 500ms 取网页版基准，皮肤 JS 未初始化完选中了别的元素；② `scrollWidth−vw` 为负（页面比视口窄 10–15px）被当成横向溢出；③ `inlineBg=='-'` 把皮肤自己写在 inline style 的 `background:transparent` 当成我方写入、`/var\(--pw/` 正则误伤合法的 `var(--pw-safe-top)` 几何值。终版改为独立 context + 逐条列印可证事实。

## 2026-11-11（主屏顶栏复修）· 改回「顶栏贴最上」，缝隙与重叠一起清掉

上一版把顶栏整体下推 54px，方向错了：屏幕最顶 0–54px 露出页面背景，形成**通站都有的空白缝隙**；「金策」等套的顶栏内容没跟着下移，状态栏文字仍压在标题上。用户实测截图（衡天类 / 金策 / 滚动态）确认三处：① 顶栏被推到约 120px，上方一大条空白；② 状态栏 `19:10` 与「衡天 / 至高神性」重叠；③ 滚动后 `1993/1995` 等正文落在状态栏区。

- **方向改为顶栏紧贴屏幕最上**：`top:0 !important`，只把顶栏**内容**用 `padding-top: calc(原值 + var(--pw-safe-top))` 往下挪，并 `height: calc(原高 + var(--pw-safe-top))` + `box-sizing:border-box` 同步加高容器 —— 内容区高度不变，顶栏背景从 y=0 一路铺到状态栏，不再有空白带。这与主站 `app.css` 原生规则（`padding-top` + `height: calc(原高 + inset)`）同向，不再用 `!important` 打架。旧的下推类 `pw-safe-push` / `pw-safe-pad` / `data-pw-needs-pad` 全部移除。
- **body 让位按顶栏类型区分**：`sticky` 顶栏在文档流里，自身加高 54px 已经把内容推下去，再给 `body` 加 padding 会把顶栏起点推到 54px、重新制造缝隙 —— 所以有 sticky 顶栏时不动 body（且可撤销，防 React 异步挂载晚到）；只有 `fixed` 顶栏 / 无顶栏时才读 `body` 原 `padding-top` 做 `calc(原值 + 54px)` 叠加，不覆盖原值。
- **半透明顶栏补不透明底**：星烬/夜钤记 `rgba(...,0.78)`、金策 `color(srgb …/0.95)`、同心符环/御言干脆透明，滚动正文会透到状态栏区。`bgOf()` 沿祖先链优先取本来就不透明的 `rgb()` 纸色/深色（暗色皮肤取到 `rgb(7,8,11)` 一类，不产生白块），只补 `background-color`，`background-image` 渐变纹理保留。底色用「属性选择器 `[data-pw-bar-bg]` + CSS 变量 + 样式表 `!important`」承载 —— 皮肤 JS 滚动时 `className=` 整体覆盖或删 inline `background-color`（月牍的 `oklab(…/0.78)` 毛玻璃）都影响不到它。兼容 `rgb/rgba/color(srgb)/oklab` 的 alpha 读取与去 alpha。
- **状态栏区兜底遮挡条**：`fixed; top:0; height:var(--pw-safe-top); z-index:40; pointer-events:none`，颜色取页面自身背景（深浅自适应）。垫在正文之上、顶栏之下：有横贯顶栏时完全不可见、不改动设计；沉浸式无顶栏皮肤才露出来盖住滚到 y=0 的正文。用独立元素承载，不受皮肤 JS 重建 DOM / 改 class 影响。
- **贴顶浮动控件下移**：终焉金环、墨龙山水、弧界、素卷没有横贯顶栏，只有 `fixed`、`z-index:50~60`、不满屏宽的悬浮胶囊工具条（☼ A ▲ A 目），原本正好落在状态栏 54px 内。筛选收紧到「横贯全宽 ≥70% 视口」才当顶栏（不再把浮动控件误拉到 `top:0`），窄而浅且带文字的控件改为 `top: calc(原值 + var(--pw-safe-top))`，实测从约 10px 下移到 63–66px。切换器浮层与遮挡条自身显式排除。
- **抗覆写与异步**：`[200,700,1500,3000]` 分批重扫 + 滚动节流 120ms + resize/orientationchange 重跑，覆盖 React 异步挂载与皮肤 JS 滚动态重建。
- **验证**：全量 36 套皮肤页、初始 + 滚动各一次：顶栏贴顶 36/36、顶栏内容文字 ≥54px 36/36、状态栏区 15 点全宽被不透明层覆盖 36/36、0 正文透出、0 横向溢出、0 JS 报错、0 个 4xx、遮挡条高度均为 54px；网页版 36/36 零变化（`data-pw-standalone` 与遮挡条均不出现）。滚动时状态栏区内文字经「临时启用命中」验证 3/3、1/1、0/0、1/1 全被遮挡条盖住，此前报的「透字」是 `pointer-events:none` 造成的命中测试假阳性。**定级原文与角色页正文零改动** —— 36 个改动 HTML 剥离注入后逐字一致。SW 升 `pw-v37`。

## 2026-11-11（主屏顶栏 / 命名 / 切换器）· 三处一起收拾

- **主屏状态栏压住顶栏（严重，34/36 套）**：iPhone 保存到主屏后以 standalone 打开，状态栏覆盖页面顶部。实测 36 套皮肤里 34 套在顶部 54px 内有文字。根因有三：① 32 套 `minimal` 皮肤按设计不引入主站 `app.css`/`pwa.js`，拿不到 `--pw-top-inset`；② 历史注入的 `.topbar{padding-top:env(safe-area-inset-top,0px)!important}` 兜底是 0px，且 `!important` 会把 `app.css` 已有的避让覆盖掉；③ 2 套缺 `viewport-fit=cover`，iOS 上 `env()` 根本不赋值。
- **改法**：改 `build_site.py`，在 `<head>` 注入一段自包含脚本（不引外链样式、不污染 React 皮肤 DOM）：判定 standalone → 量 `env(safe-area-inset-top)`，小于 24px 兜底 54px → 写 `--pw-safe-top` / `--pw-top-inset` → 运行时按 computed style 找「贴顶的固定栏」并只下推**尚未避让**的那些。小顶栏用 `top` 下推，全屏抽屉用 `padding-top`（抽屉常带 `transform`，改 `top` 会被抵消）；已自带避让的自动跳过，避免叠加。React 异步挂载用 `[200,700,1500,3000]` 分批重扫。旧注入先移除，缺的 `viewport-fit=cover` 补齐。
- **验证**：standalone 模拟 36/36 套顶部 54px 内无文字；普通网页版 36 页 `data-pw-standalone` 零误触发、0 溢出、0 JS 报错、0 个 4xx；36 套模拟状态栏截图自查顶栏无错位/截断。**定级原文与角色页 HTML 零改动**——剥离注入后 50 个 HTML 逐字一致。
- **命名重做（36 套）**：旧名多为「颜色＋材质」「功能描述」「XX之X」公式（冷白星球弧、放射线战场、竖排版本牌、箔面羊皮…），看着像流水线产出。改为 2–4 字错落的专名（检字 / 裂宿图 / 候星 / 月牍 / 沉墨长卷 / 铜柩长夜 / 朱契 / 御言 / 霜阈 / 弧界 / 疾线…），字数分布 2字20 / 3字7 / 4字9，无重名、无 4 次以上撞字。清空清一色 `英文 · 中文` 副标（`tag`），生成器对空 tag 不再输出 span；36 条 `note` 也改成一句干净的视觉描述，去掉「亮暗双主题、字号、目录」「（暗色，图/字体内联）」「8 张插图原图已用包内优化版补齐」这类功能清单与开发备注。
- **切换器形态**：保留用户认可的淡化/滚动隐藏行为，只重做形态与大小。白底圆钮＋金色渐变立体球 → 42×42 薄纸方章＋单色细线 ⊙（圆角 12px、`::before` 把命中区扩到 46px）；回首页按钮同套语言。卡片名字 12.5→14px、当前态由整块黄底渐变换成一道左侧赭金细线、说明文字两行、空副标不占位。上一轮自检里「50 页切换器按钮宽度不足 40px」由 50 降到 0。
- **回归**：全站 216 次加载 0 个 4xx / 0 JS 报错 / 0 横向溢出 / 0 破图 / 0 字体方框；198 张卡片名一致、旧名残留 0；桌面 1440 与手机 390 选边锚定边恒定（左右横跳未复发）；35 项交互专项通过（另 2 项为测试脚本口径误报，用 `textContent` 与真实 `display-mode: standalone` 复验均通过）。
- **上线**：SW `pw-v35 → pw-v36`，保证主屏 App 拿到新样式与新的安全区注入。

## 2026-11-09（插图改为页内放大）· 点图不再跳出当前页

- **问题**：站内 18 处插图（至高王座 8、无限宝石 8、御兔 2）的 `<a class="md-figure-link" target="_blank">` 指向原图文件。主屏幕启动（standalone）时点一下会跳出当前视图、没有返回键只能侧滑回 App；网页版则直接开新标签页。
- **改法**：`static/js/app.js` 新增 `initFigureLightbox()`，用事件委托接管插图点击，在**当前页内**放大原图；`static/css/editorial.css` 补灯箱样式。普通左键点击 `preventDefault()` 不再跳页，Esc／点空白处／关闭按钮三种方式关闭，焦点回到原链接，正文滚动锁，Tab 焦点留在对话框内。
- **保留能力**：Ctrl／Cmd／Shift／Alt + 点击与中键不被拦截，需要新开标签看原图时仍可用；JS 未加载时链接原样工作（渐进增强）。
- **铁律守住**：**定级原文与角色页 HTML 零改动**——只改共用脚本／样式，`character/*.html`、`rules.html`、`data/docs/` diff 全为 0；`target="_blank"` 属性也保留不删。
- **主屏适配**：关闭按钮与图片区用 `env(safe-area-inset-*)` + `--pw-top-inset` 让出刘海／Home 条，实测 standalone 下按钮落到 68px、图片区留白 72px；层级 1600 高于版本切换器 1400，灯箱关闭后切换器照常可用；尊重 `prefers-reduced-motion`。
- **范围**：切换器缩略图卡片不在此次改动内——每套皮肤是独立整页，切换必然换页，且每页常驻切换器可一键切回。70 处外部文献链接的 `target="_blank"` 保持原样（本就是去站外）。
- **核验**：桌面 1440 / 移动 390 双端，18／18 个插图链接点击后 URL 不变、无 popup／新标签、原图 `naturalWidth > 0`、三种关闭方式与焦点回归全部通过；明／暗主题截图复核无遮挡、无横向溢出；0 个 JS 报错、0 个 4xx/5xx。SW 版本 `pw-v34` → `pw-v35`，确保主屏 App 拿到新脚本（代码类资源本就网络优先，升版本用于清掉旧缓存壳）。

## 2026-11-08（仓库整理）· 验收截图不再入库

- 将已跟踪的 10 张验收／自检截图（命名整理 2 张、补3212 3 张、全站自检 5 张，共 6.9 MB）从 git 索引移除，`git rm --cached` 保留本地文件，截图本身仍可查看。
- `.gitignore` 追加 `验收截图/`，以后本地生成的检查截图不会再被 `git add -A` 带进仓库。
- 这些图没有任何页面／CSS／JS 引用，站点内容与线上页面零变化，SW 版本保持 `pw-v34` 不升。

## 2026-11-08（全站自检）· 修掉新栏目切换器的失效链接，并补齐根 favicon 兜底

- **修复 20 张失效链接**：上一批新增的 4 套「至高王座」皮肤在 `editions.json` 里把 `pages[character-zhigaowangzuo]` 误写成 `character/character-zhigaowangzuo.html`（既有主站页是 `character/zhigaowangzuo.html`，皮肤产物在 `skins/<id>/`）。生成器 `edition_launcher_html()` 直接拿这个值拼卡片 href，导致主站 4 张 + 4 套皮肤页各 4 张共 **20 张卡片点进去必然 404**，且四套指向同一个错误地址。已全部改为 `skins/<id>/character-zhigaowangzuo.html`，重跑生成器后 198 张卡片链接全有效。之前的验收只查了卡片名与面板开合、没实际点跳转，这次补上点击回归。
- **补根 `favicon.ico`**：生成器只在 `inject == "minimal"` 时把 icon 声明补进 `<head>`；`archive`／`atlas`／`observatory`（未声明 inject，走完整注入、icon 落在 `</body>` 前）与 `futan-lamp`（打包 JS 里的 `</head>` 字面量干扰定位）共 4 套皮肤 head 里没有 icon，浏览器回退请求根 `/favicon.ico` 产生 404。按 Web 标准在站点根补一个多尺寸 `favicon.ico`（由 `static/img/icons/favicon-32.png` 生成），不改生成器、不重生成 36 套页面，全站兜底 404 清零。
- **全站自检**（五层）：静态层 37 套登记字段齐全、id 唯一、`source`／`thumb`／`pages` 目标齐备、名字无重名、副标撞字 0；156 个 HTML 页浏览器加载 **156/156 全绿**（HTTP 200、0 资源 404、0 JS 报错）；198 张 launcher 卡片链接 0 失效；点击跳转回归 8/8（主站→4 套、4 次点回默认、4 次皮肤互切）；移动端 390 共 23 页 23/23（名字无截断、面板不超屏、锚定边恒定）；桌面 1440 共 14 页横跳回归 0 失败；4 套历史皮肤截图确认各自版式完整、无主站样式叠加污染。
- **铁律守住**：改动仅 `data/editions.json` 4 行、5 个页面的 launcher 链接行、1 个新增 `favicon.ico`，共 6 改 + 1 增；`rules.html` 等主站页 diff 0 行，规则正文与角色定级原文零改动。
- **非故障项**：`archive`／`atlas`／`observatory`／`moonfile` 4 条早期登记未显式写 `inject`，生成器按默认「完整注入」分支处理，行为确定且实机正常，仅为写法不统一，不影响功能，本次不动以免改变渲染行为。

## 2026-11-08（补3212）· 新增四套「至高王座」整页皮肤（开新栏目），并补齐缺图套的 8 张插图

- **来源**：用户上传 `3212.zip`（176,999,579 B）。对话层附件因超限下载失败，改用附件里的对象存储签名链接直取。包内 4 个独立整页工程，均为「护国机神·至高王座（《斩！赤红之瞳》）」衡天定级页，各带 `dist/index.html` 成品与 `images/` / `generated/` 资源；其中一套目录自带「(缺图)」标注。
- **新栏目**：主站 `character/zhigaowangzuo.html` 与权威定级 md `data/docs/characters/至高王座（斩！赤红之瞳）衡天定级.md` 早已存在，`build_site.py` 的 `BOOT_BG_CHARACTERS` 也已预留 `character-zhigaowangzuo`，只是没登记进切换器。本次给 `default.pages` 补 `character-zhigaowangzuo` → `character/zhigaowangzuo.html`，4 套皮肤 `section` 统一挂该栏目；主站角色页切换器由 0 张变 5 张（默认＋4）。
- **命名（沿用上一版命名整理的自检）**：4 套按各自视觉物象起名，字数排成 **2／3／4／5 阶梯**，不堆两字古风词、不与现有 33 套撞套路，副标也不与名字撞字：

| id | 新名 | 字数 | 视觉依据 |
| --- | --- | --- | --- |
| `zhigaowangzuo-rilun` | **日轮** | 2 | 黑金铜版画、巨大日蚀光环、机神立绘、档案顶栏 |
| `zhigaowangzuo-junzhen` | **军阵图** | 3 | 铜版线描机神、军阵全景、珊瑚橙点缀 |
| `zhigaowangzuo-yihuan` | **猩红仪环** | 4 | 金线浑天仪环、猩红核心、观测台刻度、档案双栏 |
| `zhigaowangzuo-zhanchang` | **放射线战场** | 5 | 全屏机神巨像、放射速度线、战场废墟、红白巨字 |

- **★ 缺图套修复**：`kimi-k3.1-pro-max＆gemini3.8flash` 那套的 8 个插图位用的是**占位图**，图面明写「原插图缺失 · 占位图」「源码包未包含『至高王座_图3_*.png』」「补齐原图后重新构建，即可自动替换为真实证据图」；JS 数组 `D2` 也指向 8 个不存在的 `./images/至高王座_图N_*.png`。关键坑：包内 `images/optimized/plate-01~08.jpg` **本身就是这 8 张占位图**（首轮误当成正常图补了一遍，看图后推翻重做）。按用户「可以用其他正常的补上去」，从**另外 3 套的正常图**里按 8 个插图位的语义一一对应挑图：

| 插图位 | 补入的图 | 来源 |
| --- | --- | --- |
| 图1 炮击与弹坑 | `banner-dark-1-crater`（炮击火光弹坑俯瞰） | gemini＋opus 套 |
| 图2 弹坑宽度测量 | `banner-light-1-crater`（线描弹坑剖面） | gemini＋opus 套 |
| 图3 机体身高 | `hero-dark.png`（机神全身立绘） | gpt-6-astra 套 |
| 图4 腿部局部 | `banner-light-2-scale`（腿部与房屋比例尺） | gemini＋opus 套 |
| 图5 事后全景城墙 | `banner-light-3-capital`（帝都全景） | gemini＋opus 套 |
| 图6 肩炮齐射 | `hero-dark.jpg`（全屏机神带炮） | fable 套 |
| 图7 索敌迎击与装甲 | `hero-dark-emblem`（机神装甲半身） | gemini＋opus 套 |
| 图8 帝都面积设定 | `map-light.jpg`（帝都圆形规划图） | fable 套 |

  处理：8 张统一 cover 裁到 1600×1000、JPEG q88，替换 `_source` 里对应的 8 段内联 base64（**后 2 段 hero 原样不动**）；同步覆盖 `images/optimized/plate-0N.jpg` 与补齐的 8 张 `至高王座_图N_*.png`，页面与磁盘资源一致。8 张全部 HTTP 200、PIL 可解码；图版区实机截图已无「占位图／PLACEHOLDER」字样。
- **铁律守住**：**定级原文逐字保留**——把两侧 HTML 所有 `data:image/jpeg;base64,...` 抹成占位符、只去掉安全区注入后，正文长度差 **0**、逐字完全一致；「定级依据」「条目版本」「城▽」「弱爆城级」「第六版」计数原／现完全相同。4 套均按惯例只注入 `<style data-pw-safearea>`（`viewport-fit=cover` 原始文件本已带），无字体外链可修（4 套 `@font-face` 全为内联／系统栈，0 个失效 woff2）。主站 `rules.html` 与其余角色页 diff **0 行**，`character/zhigaowangzuo.html` 仅 launcher 1 行变化，规则正文零改动。
- **验收**：本地 8900 + 无头 Chromium，桌面 1440 / 移动 390 × 5 页 = 10 组：切换器 5 卡名字逐字命中、面板开合、0 破图、0 404、0 JS 报错；横跳回归按锚定边 8/8 恒定（桌面 `left=16`、移动 `right=370/378`）；最长 5 字名「放射线战场」在 390px 下完整显示。截图 `验收截图/3212_*.png`。
- **累计 37 套**；`service-worker.js` `pw-v32`→`pw-v33`。

## 2026-11-08（命名整理）· 皮肤名去掉「全是两字」的套路感

- **起因**：用户反馈「怎么全是两个字，别重复了」。核查 `data/editions.json` 共 33 套，**26 套是两字名**（79%），且用字严重撞车——「星」5 次、「墨」3 次、「金」3 次、「鎏」2 次，「渊／穹／卷／铜／青」成串；另有 12 处 `tag` 副标直接复述 `name`（最典型 `观象台` / `OBSERVATORY · 观象台`）。
- **做法**：**不搞统一加长**——把「全是两字」换成「全是四字」只是换个套路。保留最凝练贴切的两字名，只把撞车、雷同的 17 套按各自 `note` 里的**具体物象**重命名，让字数自然错落，且同一栏目内字数互不相同：

| 栏目 | 旧 → 新 |
| --- | --- |
| 材质 | 卷宗→**索引栏**、碎核→**赤陶裂核**（星图不变） |
| 规则 | 璇玑→**浑天金轨**、朱版→**竖排版本牌**（观象台／宣衡不变） |
| 露法斯 | 绛翼→**珊瑚印**、鎏星→**星轨**、霜门→**淡蓝之门** |
| 至高神性 | 鎏金→**箔面羊皮**、玄金→**玄夜描边**、星烬→**余烬**（金印神性／圣辉不变） |
| 弗坦 | 碧渊→**地海回响**（无光之渊／孤灯不变） |
| 犹格 | 青漩→**青绿涡旋**、铜晖→**辉光**（黄铜钥不变） |
| 林飞 | 晶穹→**晶球**（墨印长生不变） |
| 江无夜 | 星涡→**金榜孤崖**（蚀环不变） |
| 古尘沙 | 墨龙→**龙符山水** |
| 下游者 | 穹弧→**冷白星球弧**（素卷不变） |

- **字数分布**：`2字 26 / 3字 2 / 4字 4 / 5字 1` → `2字 13 / 3字 4 / 4字 13 / 5字 3`。**没有任何一个栏目仍全是两字**，规则栏目恰好形成 2／3／4／5 字各一。装饰性堆砌字已清掉：「鎏」「穹」降为 0 次，「墨」（仅墨印长生）「渊」（仅无光之渊）「卷」（仅素卷）「铜」（仅黄铜钥）各剩 1 次；「星」5→4、「金」3→3 保留——本站主题即恒星系／星团量级，天体类皮肤用这两个字是语义需要，不是无差别装饰。
- **副标去重**：10 处 `tag` 中与 `name` 复述／撞字的中文描述换成该皮肤 `note` 里另一处意象（如观象台 `OBSERVATORY · 观象台`→`· 二十八宿`、璇玑 `XUAN JI · 浑天星图`→`· 暗色观台`、下游者 `SU JUAN · 水墨长卷`→`· 淡红日`），复核后**剩余撞字 0 处**。拼音代号（XUAN HENG／XUAN JI／ZHU BAN 等）作为皮肤内部代号保留不变。
- **只动名字**：`id`、`source`、`pages`、`thumb`、`note` 一律不动；缩略图、页面源文件、皮肤内嵌文案均不碰。重跑 `python3.11 build_site.py` 后全站切换器卡片同步，git diff 44 个文件**全部只有 launcher 那一行文字变化**（70+/70-），规则正文与角色定级原文零改动，「定级原文逐字保留」「规则换版只更规则页」两条铁律守住。
- **验收**：本地 8900 服务 + 无头 Chromium，桌面 1440 / 移动 390 共 10 页 × 2 端 = 20 组，卡片名字逐字比对全部命中新名、旧名零残留、面板开合正常、0 JS 报错、0 资源 404；横跳回归按锚定边判定（桌面停左 `left=16`、移动停右 `right=370`，璇玑全屏背景页 `flip=true` 属正常），滚动／开合／关闭 10/10 恒定；最长 5 字名在 390px 下完整显示无截断（截图 `验收截图/names_*.png`）。`service-worker.js` `pw-v31`→`pw-v32` 让缓存失效。

## 2026-11-08（补12）· 新增五套整页皮肤：璇玑/朱版（规则·第六版）、墨龙（古尘沙）、穹弧/素卷（下游者）

- **来源**：用户上传的 `12.zip`（沙箱 `1794126165450599944-12.zip`）内含 5 个独立 Vite/React 单文件工程，各带 `dist/index.html` 成品、`public/` 图片与 `src/` 源码初始结构（用户明确指出包内成品、结构、图片齐全）。按设计语言命名（非模型名）：
  - `GLM5.3MAX＆gemini-4-argon-high衡天规则页面` → 规则栏目「璇玑」`xuanji`（深空浑天仪、金线星轨、朱金印、暗色观测台，图/字体内联）
  - `KIMIK3＆grok-4.7-xhigh衡天规则页面` → 规则栏目「朱版」`zhuban`（米纸朱印、大字衡天、竖排目录、版本牌，亮/暗双主题）
  - `OPUS5.5HIGH＆gemini-3.8-flash-medium龙符定级页面` → 古尘沙栏目「墨龙」`guchensha-molong`（青绿山水、水墨龙、朱印、毛笔大字，亮/暗双主题）
  - `fable-5.1-lowa＆GPT6LUNAMAX＆GEMINI3.8FLASHHIGH下游者定级页面` → 下游者栏目「穹弧」`xiayouzhe-qionghu`（深空巨大星球弧面、极简冷白，暗色）
  - `fable-5.1-low＆opus5.5low下游者定级页面` → 下游者栏目「素卷」`xiayouzhe-sujuan`（米纸水墨长卷、淡红日、克制版式，亮色）
- **★ 规则拉齐第六版（沿用补11 既定铁律）**：两套规则页工程自带的 `doc.md` / `hengtian.md` 均为**第五版**（129KB，h1 21 / h2 98，md5 `009cc126f3`，与补11 那套第五版逐字一致），而主站 `rules.html`、资料库权威源 `data/docs/衡天量级体系【第六版·最新】.md` 已是**第六版·最新**（145KB，h1 22 / h2 98，md5 `934cd7b86b`）。处理方式：权威第六版 md 覆盖两套的正文源；`index.html` 的 title/description 与 UI 版本标识（顶栏、封面大标题、`tb-ver` 徽标）由「第五版」改为「第六版」；分别跑 `node scripts/build-content.mjs` 重新生成结构化内容（GLM → `content.ts` 22 节 138 目录 552 块；KIMIK3 → `doc.json` 且**逐行保真校验 1110 行一致**），再 `npm ci` + `vite build` 出单文件成品。重建后两套均显示第六版全文、含「第六版修订要点」；第二~五版修订要点作为历史对照按惯例保留，UI 里「第五版修订要点」这类**章节名**与 `build-content.mjs` 的 `UI_TEXT` 不动。
- **铁律守住**：三套定级页内嵌的「定级依据：《…（第五版）》」「条目版本：2026-11-04」「终决条目」及主站 `character/guchensha.html` / `character/xiayouzhe.html` 的 `doc_basis` 均属**定级原文/条目元信息**，按「定级原文逐字保留」**一字未改**（该条目定级时第五版即当期有效版本）。「规则拉齐」只作用于规则栏目页面，不回溯改写历史定级结论。主站 `rules.html` / 两角色页及 `skins/observatory` / `skins/xuanheng` 的 diff 均仅 launcher 卡片数变化（rules 3→5、古尘沙 2、下游者 3），规则正文、定级原文零改动。
- **栏目**：主站已有「下游者」`character/xiayouzhe.html` 与「古尘沙」`character/guchensha.html` 角色页，`build_site.py` 配色字典亦已预留 `character-xiayouzhe` / `character-guchensha`。`data/editions.json` 追加 5 条（累计 33 套）并给 `default.pages` 补这两个栏目，使主站对应角色页出现切换器。全部 `inject: minimal`。
- **资源与字体**：5 套 `dist/` 下除 `index.html` 外的资源（璇玑 `img/` 10 图、朱版 `images/` 4 图 + `fonts/fonts.css` + `favicon.svg`、墨龙/穹弧/素卷各 `images/` 10 图）按原相对路径全量拷到 `skins/<id>/`，`./images/hero-${m}.jpg` 等动态路径实机抽查全 200。全包**无 woff2 文件**：璇玑/墨龙/穹弧的字体本就全 base64 内联（5/8/1 个 @font-face，0 404），一字未动；仅**朱版**（`fonts.css` 外链 5 个失效子集 woff2）与**素卷**（JS 模板字符串 `iv` 注入 5 个动态 `@font-face`，`Mu()` 拼 `fonts/*.woff2`）会各报 5 个 404 —— 已用最小侵入方式去掉这两处失效声明（朱版删该 stylesheet link、素卷删 5 行声明使 `iv` 变空串），页面自带系统字体栈（Songti SC / Noto Serif CJK SC / serif）回落，视觉与去除前一致、中文无方框。
- **验收**：无头 Chromium 桌面 1440 / 移动 390 双端，对 5 套新皮肤 + 主站 rules/古尘沙/下游者共 8 页做「收起/打开/多次滚动」三态：dock 锚定边与 `bottom` 全程恒定、翻面状态一致、面板开合与 `aria-expanded` 正常、卡片数（5/2/3）与当前标记准确；两套规则页确为第六版全文；三套定级页「依据第五版」原文保留；**0 个 JS 报错、0 个 404**。跨 560px 缩放：墨龙/素卷桌面左↔移动右正确切换；璇玑/朱版因页面自带 `position:fixed` 全屏背景层被 `decideSide` 判为贯通左栏而桌面即贴右（桌面/移动 flip 恒为 True、全程稳定），属既有选边规则的稳定结果、非乱跳，未改动已修复的 `editions.js`。5 套实机截图存 `验收截图/skin12_*.png`。

## 2026-11-08（补11）· 新增三套整页皮肤：「宣衡」（规则·第六版）与「星涡」「蚀环」（江无夜），并把规则拉齐到最新

- **来源**：用户上传的 `11.zip`（沙箱 `1794123658796248794-11.zip`）内含三个独立 Vite/React 整页工程，各带 `dist/index.html` 单文件构建产物：
  - `sonnet-5-5-xhigh＆fable5.1high＆muse-spark-1.3-max衡天规则页面` → 规则栏目皮肤「宣衡」（米纸水墨、朱印⊙日轮、暗/亮双主题、字阶可调）
  - `KIMIK3＆gemini-3.8-flash-high江无夜定级页面` → 江无夜栏目皮肤「星涡」（青蓝星系漩涡、金榜书、深空孤崖）
  - `OPUS5.5HIGH＆DS4.1FLASHMAX江无夜定级页面` → 江无夜栏目皮肤「蚀环」（近黑金环日蚀、极简留白、TERMINUS 终焉）
- **★ 规则拉齐到最新（用户明确要求）**：这套「衡天规则页面」工程自带的 `src/content/doc.md` 是**第五版**全文（标题、版本说明、修订要点均为第五版），而主站 `rules.html` 与资料库权威源 `data/docs/衡天量级体系【第六版·最新】.md` 已是**第六版·最新**（2026-11-05 发布 / 11-06 修订），二者 md5 一致（`934cd7b8…`）。若原样接入，站内会出现第五/六版两套规则并存。处理方式：把权威第六版 md 覆盖为该工程的 `doc.md`，同步把 `index.html` 的 `<title>`/description 从第五版改为第六版，`npm ci` + `vite build` 重新出单文件产物。第五版与第六版章节结构兼容（h1 21→22、h2 均 98，仅多「第六版修订要点」一章），解析器无需改动。重建后页面显示第六版全文、含「第六版修订要点」，第二~五版修订要点作为历史对照保留（与主站一致）。
- **铁律守住**：两套江无夜定级页内嵌的定级原文写「定级依据：《…第五版》」、主站 `character/jiangwuye.html` 的 `doc_basis` 亦为第五版——这些是**定级原文/条目元信息**，按「定级原文逐字保留」**不改动**（该条目 2026-11-04 定级时第五版即当期有效版本）。「规则拉齐」只作用于规则栏目页面，不回溯改写历史定级结论。
- **字体修复**：规则页原工程 15 个 `@font-face` 指向 `./fonts/*.woff2`（子集字体由 `tools/build-fonts.py` 生成，字体源未随包，直接接入会 12 处 404、中文退成方框）。已删除这些失效声明，把 `--f-serif/sans/kai/brush/disp` 改指站内自托管的思源宋/黑与 Space Grotesk（覆盖第六版全文字符集），并在 head 挂上站内字体表。江无夜两套的字体与图片本就全 base64 内联，无需处理。
- **接入**：三份产物落 `skins/_source/`，注入安全区（`viewport-fit=cover` + `.topbar` safe-area）；`./images/` 外链图（规则页、星涡）随包拷到 `skins/<id>/images/`；各生成 640×400 缩略图。`data/editions.json` 追加三条（累计 28 套），并给 `default.pages` 补 `character-jiangwuye`（主站已有该角色页），使新栏目切换器生效。全部 `inject: minimal`。
- **核验**：无头 Chromium 桌面 1440 / 移动 390 双端，对三套新皮肤 + 主站 rules + 主站江无夜页做「收起/打开/多次滚动」三态：dock 锚定边与 `bottom` 全程恒定、翻面状态一致、跨 560px 缩放正确左↔右切换；面板开合正常、卡片 3 张且当前标记准确；字体 `document.fonts.check` 全部 loaded；规则页确为第六版全文；**0 个 JS 报错、0 个 404**。三套实机截图存 `验收截图/skin11_*.png`。

## 2026-11-07（修复）· 皮肤切换器 dock 左右乱跳

- **现象**：皮肤页角落的「⊙ 皮肤」切换器在滚动、或点开面板时，会在左下角与右下角之间反复横跳；面板跟着跳。
- **根因**（`static/js/editions.js` 的 `placeDock`）：选边（`is-flipped` 左/右翻转）每次重测都重算，且依赖两处瞬时输入——
  1. 旧逻辑把"两侧瞬时净空的比较"（`rightSlot + 0.5 < leftSlot`）作为翻面条件，页面上 fixed/sticky 块几何一变就翻；
  2. 面板 `pw-edition-panel` 打开瞬间 dock 因标签展开变宽（30→~63px），`dock.offsetWidth` 被带进水平锚定，临界宽度下翻面；
  3. "太高就翻到另一侧"的兜底（`bottom > vh*0.42`）遇到滚动后滑入的底部栏也会翻面；
  4. 露法斯页（`ruphas-frostgate`）在"开面板+滚动"时会出现一个匿名 `position:fixed`、`left:-196 / right:348 / h:544` 的屏外元素，被误判成"贯通左栏"，直接触发翻面。
- **修法**：① 选边一次性决定后**冻结**——只在启动时（200/700/1500/3000ms 布局稳定期）与视口尺寸真正变化（resize/orientation）时重算，滚动与开合只调上下净空、横向永不翻；② 水平锚定改用 `inset` 直接定位，与 dock 实际宽度无关；③ 选边与 inset 计算排除"半截在屏外"的元素（`left < -4` 或 `right > vw+4`），真正贴边的侧栏左缘≈0，虚惊消除；④ `clearance` 跳过底部已探出视口的块（`b.bottom > vh+2`），不再被那个屏外元素顶高。
- **核验**：无头 Chromium 桌面/移动双端，对 8 套皮肤（含露法斯开/合、至高神性、弗坦、青漩、周天等）做"收起/打开/多次来回滚动"三态对比——dock 的锚定边与 `bottom` 全程恒定（横稳+纵稳），跨 560px 缩放仍正确左↔右切换；面板开合正常、卡片数与当前标记准确、0 个 JS 报错。

## 2026-11-07（补9）· 新增两套整页皮肤：「星烬」（我就是我·至高神性 第5套）与「霜门」（露法斯·玛法尔 第3套）

- **来源**：用户上传的 `8.zip`（沙箱 `1793992492063340232-8.zip`）内含两个独立构建的整页——`sonnet-5-5-high我就是我定级页面/index.html`、`qwen3.8-max-0902＆sonnet5.5high露法斯定级页面/index.html`。定级原文均**逐字零改动**。
- **命名**（按设计语言，非模型名）：`divinity-starember`「星烬」——近黑夜空（#05060D）与亮金星烬（#E8C577）、米纸衬线（#F3ECDC）的至高神性卷，`tag: STAR EMBER · 至高神性`，`section=character-divinity`（与「金印神性」「圣辉」「鎏金」「玄金」并列，至高神性第 5 套）；`ruphas-frostgate`「霜门」——近黑与金（#E0B158）、米（#F6EFE0）、淡蓝门意象（#86B6D6）的露法斯卷、衡天⊙外·门（ℵ₀）主题，`tag: FROST GATE · 外门档案`，`section=character-lufasi`（沿用 `ruphas-` 前缀，与「绛翼」「鎏星」并列，露法斯第 3 套）。均 `inject: minimal`。
- **全内联、零外部依赖**：两套图片（`data:image` webp×4 / svg×1 与 jpeg×7 / svg×2，全部 base64）、字体（`@font-face` 全部 base64，星烬 10 个、霜门 5 个）、favicon（构建器 minimal 分支自动补站内 `favicon-32.png`，消除 `/favicon.ico` 回退 404）。HTML 中 `./images/`、`./fonts/` 外链引用均为 0，故**无缺图、无缺字体、无 favicon 404**。
- **安全区**：两套均在 `</head>` 前注入 `<style data-pw-safearea>`：`.topbar{padding-top:env(safe-area-inset-top,0px)!important}`。
- **缩略图**：两套各从内联首图（webp / jpeg 解码）裁切 640×400，`static/img/editions/{divinity-starember,ruphas-frostgate}.jpg`；切换器 cards：至高神性页 `default / 金印神性 / 圣辉 / 鎏金 / 玄金 / 星烬`（共 6 套）、露法斯页 `default / 绛翼 / 鎏星 / 霜门`（共 4 套）。
- service-worker 升 `pw-v29` 强制刷新缓存。

## 2026-11-07（补8）· 新增四套整页皮肤：鎏金 / 玄金（我就是我·至高神性）+ 青漩 / 铜晖（犹格·索托斯）

- **来源**：用户上传的 `7.zip`（沙箱 `1793991206676768051-7.zip`）内含四个独立构建的整页——两套「我就是我·至高神性」（`dubi-mega＆…＆GEMINI4ARGON我就是我定级页面`、`dubi-mega＆…＆fable-5.1-max我就是我定级页面`）与两套「犹格·索托斯」（克苏鲁神话原作）（`qwen3.8-flash-next＆…＆DS4.1flashMAX＆GPT6LUNAMAX犹格…定级量级页面`、`qwen3.8-flash-next＆…＆sonnet-5-5-xhigh＆opus-5.5-max犹格…定级量级页面`）。定级原文均**逐字零改动**。
- **命名**（按设计语言，非模型名）：`divinity-gilt`「鎏金」——纯金箔面＋米白羊皮纸、衬线巨字「我就是我·至高神性」的金色神性卷，`tag: GILT · 至高神性`，`section=character-divinity`（与「金印神性」「圣辉」并列）；`divinity-xuanjin`「玄金」——近黑底＋暗金描边、暖金衬线巨字的暗黑神性卷，`tag: XUANJIN · 暗金神性`，同 `section=character-divinity`；`yog-teal-vortex`「青漩」——黄铜金＋青绿涡旋、近黑的外神卷宗（webp 动态主视觉），`tag: TEAL VORTEX · 外神档案`，`section=character-yog`（与「黄铜钥」并列）；`yog-bronze-glow`「铜晖」——黄铜金＋青绿辉光、近黑的外神卷宗（jpeg 主视觉），`tag: BRONZE GLOW · 外神档案`，同 `section=character-yog`。四套均 `inject: minimal`。
- **全内联、零外部依赖**：四套图片（data:image webp/jpeg/png/svg 全部 base64）、字体（`@font-face` 全部 base64，含鎏金 20 个、玄金 10 个、青漩/铜晖各 4 个）、favicon（鎏金/玄金/青漩为内联 `data:image/svg+xml`，铜晖原为本地 `favicon.svg`——已在 `_source` 层改为内联 base64 消除外部引用）。HTML 中 `./images/`、`./fonts/` 外链引用均为 0，故**无缺图、无缺字体、无 favicon 404**（补7 犹格曾误判外链缺图，本次先核验确认为纯内联）。
- **安全区**：四套均在 `</head>` 前注入 `<style data-pw-safearea>`：`.topbar{padding-top:env(safe-area-inset-top,0px)!important}`。
- **缩略图**：四套各从内联首图（jpeg/webp 解码）裁切 640×400，`static/img/editions/{divinity-gilt,divinity-xuanjin,yog-teal-vortex,yog-bronze-glow}.jpg`；切换器 cards：至高神性页 `default / 金印神性 / 圣辉 / 鎏金 / 玄金`（共 5 套）、犹格页 `default / 黄铜钥 / 青漩 / 铜晖`（共 4 套）。
- service-worker 升 `pw-v28` 强制刷新缓存。

## 2026-11-07（补7）· 新增三套整页皮肤：「碧渊」（弗坦 第3套）、「黄铜钥」（犹格·索托斯）、「周天」（天人大圣 第2套）

- **来源**：用户上传的 `6.zip`（沙箱 `1793989306026607734-6.zip`）内含三个独立构建的整页——`opus-5＆mimo-v2.6-flash＆glm-5.3-flash＆opus5.5low弗坦定级页面/dist/index.html`、`DS4.1FLASHMAX＆kalmia＆qwen3.7-max＆gemini4argon犹格索托斯定级页面/dist/index.html`、`gpt-6-sol-max＆GPT6SOL＆qwen3.8-max-0902天人大圣定级页面/dist/index.html`。定级原文均**逐字零改动**。
- **命名**（按设计语言，非模型名）：`futan-biyuan`「碧渊」——青绿回响（#5fe3d0）＋暖米底（#f2ece0）＋近黑深渊的诡秘地海卷，`tag: BIYUAN · 诡秘地海`，`section=character-futan`（与「无光之渊」「孤灯」并列，弗坦第 3 套）；`yog-bronze-key`「黄铜钥」——黄铜金（#c8a86c）＋米纸（#f3edde）＋近黑绿（#07100e）的外神卷宗、门之钥意向，`tag: BRONZE KEY · 外神档案`，`section=character-yog`（新栏目，对应站内 `character/yog.html`）；`tianren-zhoutian`「周天」——米白＋灰金（#cdc1a0）＋近黑的修仙宇宙卷、周天运行意象，`tag: ZHOUTIAN · 宇宙之阶`，`section=character-tianren`（与「衡天星册」并列，天人大圣第 2 套）。均 `inject: minimal`。
- **资源落位**：三套各 `./images/*.jpg` 按生成页目录原样落到 `skins/<id>/images/`，相对路径零改写；「周天」另含 `./fonts/`（仅 3 份 OFL 授权文本，无 woff2 二进制）与自带 `favicon.svg`，一并落到 `skins/tianren-zhoutian/fonts/`、`favicon.svg`。「碧渊」「黄铜钥」源 HTML 无 `<link rel=icon>`，按既有逻辑在 `_source` 手动补 `<link rel="icon" href="./favicon-32.png">` 并落位图标，规避 minimal 分支 favicon 注入误插 JS 字符串的风险。
- **字体**：「碧渊」「黄铜钥」字体全内联自包含（base64 / 运行时注入），无需 `font_rewrite`；「周天」的 3 条 `@font-face` 指向 `./fonts/Tianren-*.woff2`，但 ZIP 未随包发出字体二进制（仅 OFL 文本），实机会 404。已在 `_source` 层删除缺失 @font-face 块，并把 `font-family` 里的 `Tianren Display/Text/Symbols` 重映射为系统 `serif`/`sans-serif` 栈（其 font-family 列表本就带 `Noto Serif SC`/`serif` 回退，重映射后零残留、无 tofu）。
- **安全区**：三套都在 `</head>` 前注入 `<style data-pw-safearea>`：`.topbar{padding-top:env(safe-area-inset-top,0px)!important}`（三套 `.topbar` 均无显式 height，仅由内部内容撑高，补 padding 即可避开刘海）。
- **切换器**：`default.pages` 补 `character-yog: character/yog.html`——此前站内已有 `character/yog.html` 但栏目未登记，补键后「黄铜钥」与默认页在该栏目双向出现；「碧渊」「周天」的栏目键此前已存在。实机 cards：弗坦页 `default / 无光之渊 / 孤灯 / 碧渊`（共 4 套）、天人大圣页 `default / 衡天星册 / 周天`（共 3 套）、犹格页 `default / 黄铜钥`（共 2 套）。
- **缩略图**：三套各生成 640×400（取首屏代表图裁切），`static/img/editions/futan-biyuan.jpg`、`yog-bronze-key.jpg`、`tianren-zhoutian.jpg`。
- **图片加载方式（更正说明）**：犹格·索托斯皮肤图片**全部内联**——渲染取 `b0[o]`（`data:image/webp;base64`，14 张场景图全内联，含 `abyss-light`/`key-dark`/`observatory-dark`/`planes-dark`），`y0[o]` 仅作为 `relPath` 相对路径元信息，不参与真实 `src`。故**不存在缺图/404**（CDP 实机已验证 0 报错、0 坏响应）。源 ZIP 外发的 `./images/*.jpg` 实为冗余 relPath 文件，未用于实际加载。
- service-worker 升 `pw-v27` 强制刷新缓存。

## 2026-11-07（补6）· 新增两套整页皮肤：「圣辉」（我就是我·至高神性 第2套）与「碎核」（材质与破坏能量数据库）

- **来源**：用户上传的 `4.zip`（沙箱 `1793984073908146836-4.zip`）内含两个独立构建的整页——`sonnet-5-5-xhigh＆haiku-5.5-high＆gpt-5.6-terra-xhigh我就是我定级页面/dist/index.html`、`opus-5.5-low＆GLM5.2MAX＆mimo-v2.6-flash＆gemini3.7flash材质页面/dist/index.html`。
- **命名**（按设计语言，非模型名）：`divinity-radiance`「圣辉」——米白羊皮纸＋中心金色光晕、衬线巨字「我就是我·至高神性」、环形 `I AM THAT I AM`、虚空／万有双态切换，`tag: SACRED RADIANCE · 虚空万有`，`section=character-divinity`（与「金印神性」并列，至高神性第 2 套皮肤）；`material-shatter`「碎核」——赤陶与朱红、裂核＋轨道环＋漂浮碎石的破坏物理主题，`tag: SHATTERED CORE · 破坏能量数据库`，`section=materials`（挂在既有 `materials.html` 数据参考页，类比观象台挂 `rules`）。均 `inject: minimal`。
- **自包含、零字体修复**：两份 ZIP 的资源策略与上轮相反——「圣辉」把 14 个 woff2 字体（Noto Serif SC 等）与各图（portrait/texture/voice）**全部 base64 内联**，页面 54MB、零外部请求，无需 `font_rewrite`；「碎核」0 个 @font-face（系统字体），仅 8 张 `./images/*.jpg` 经 `hi()` 运行时解码引用，已原样落到 `skins/material-shatter/images/`，相对路径零改写。两套均无需扩展 `patch_skin_fonts`。
- **favicon / 安全区**：两套源 HTML 都无 `<link rel=icon>`，由构建器既有逻辑补站内 `favicon-32.png` 消除 `/favicon.ico` 回退 404。两套均有 `viewport-fit=cover` 但顶栏**无顶部 `env()`**，按 `</head>` 前注入 `<style data-pw-safearea>`：`.topbar{padding-top:env(safe-area-inset-top,0px)!important}`（两套 `.topbar` 均无显式 height，仅由内部 56/63px 内容撑高，补 padding 即可避开刘海而不破坏布局）。CDP 模拟刘海（top=47）实机：圣辉顶栏 `pt:47px / h:106`、碎核 `pt:47px / h:63`，状态栏无遮挡。
- **切换器**：`default.pages` 的 `character-divinity` 与 `materials` 键此前已存在，无需改动。实机 cards：至高神性页 `default / 金印神性 / 圣辉`（共 3 套）；材质页 `default / archive / atlas / 碎核`（共 4 套）。两套皮肤页零 JS 报错、零 404；碎核 8 图 curl 全 200。
- **缩略图**：两套各生成 640×400（清 localStorage 真实首屏），`static/img/editions/divinity-radiance.jpg`、`material-shatter.jpg`。

## 2026-11-06（补5）· 新增两套整页皮肤：「衡天星册」（天人大圣）与「金印神性」（我就是我·至高神性）

- **来源**：用户上传的 `3.zip`（沙箱 `1793979930868732710-3.zip`）内含两个独立构建的整页——`muse-wonder-max＆gpt-6.1-terra-max＆qwen3.8-max-0902天人大圣定级页面/dist/index.html`、`opus-5.5-high＆DS4.1FLASHMAX＆grok-4.6-xhigh我就是我定级页面/dist/index.html`。两份都是自包含的 React 阅读器，各带亮暗主题、字号调节与章节目录。定级原文均**逐字零改动**：天人大圣 `dist/source.md` 与站内 `data/docs/characters/天人大圣（走进修仙）衡天定级.md` md5 完全一致（`0a6e941b…`，第五版，按约定不回改第六版）；我就是我的原文内嵌在打包 JS 的 `O0` 常量里，站内 md 的 114 个非空行逐行命中、零缺失。
- **命名**（沿用「模型名不是样式名、皮肤按设计语言命名」的既定规则）：`tianren-register`「衡天星册」——`CELESTIAL REGISTER` 徽记、深空黑洞与初星星云、黄铜衬线巨字、天体登记册式导航，`tag: CELESTIAL REGISTER · 初星之志`，`section=character-tianren`；`divinity-seal`「金印神性」——淡金羊皮纸与同心符环、金色衬线巨字「至高神性」、环形 `I AM THAT I AM`、`tag: I AM THAT I AM · 神性卷宗`，`section=character-divinity`。均为 `inject: minimal`。
- **注册**：`data/editions.json` 新增两条，`default.pages` 补 `character-tianren: character/tianren.html`、`character-divinity: character/divinity.html`——凑够两套皮肤，切换器才在主站角色页与皮肤页双向出现（实机 cards：主站两页各 `["default","<新皮肤>"]`）。缩略图按最终皮肤页真实首屏、清 localStorage 后重截，640×400。
- **资源**：两套各 10 张 `./images/*.jpg` 按生成页目录原样落到 `skins/<id>/images/`，相对路径零改写；天人大圣的 `source.md` 同目录落下（页面「查看原文」用）、3 份 OFL 许可证文本与 `.tmp/` 审计脚本一律不进项目。天人大圣没自带 icon，由构建器既有逻辑补站内 `favicon-32.png` 消除回退 `/favicon.ico` 的 404；我就是我自带 data-URI icon，保留不覆盖。
- **缺字体修复（关键）**：两份 ZIP **都没有随包发出字体二进制**（全包无 `*.woff2`、无 base64 内嵌），但页面会注册指向缺失文件的 @font-face——天人大圣是静态 CSS 的 3 条 `url(./assets/fonts/heng-*.woff2)`，我就是我是运行时 `document.head.appendChild(style)` 注入的 10 条 `url("./fonts/*.woff2")`，原始页实机分别 3 / 10 个 404。按站内「观象台」的 `font_rewrite` 先例扩展 `build_site.py` 的 `patch_skin_fonts`：① 删掉静态坏 @font-face；② 把运行时注入的 `Ns.textContent=M0` 置空（**用 lambda 返回纯 `""`**，替换串里写 `\"` 会把反斜杠注入打包 JS 导致整包崩溃，已修正）；③ 把 `:root` 的 `--serif/--sans/--display/--garamond` 字体变量整体改指站内自托管的思源宋体／黑体；④ `inject: minimal` 分支补注入站内 3 份字体表（`font_tags` 仅在 `font_rewrite` 时非空，对其余 minimal 皮肤零影响）。族名 `Heng *` / `HT Display` / `HT Garamond` / `HT Symbols` 全部落到站内字体栈，中文实机无方框、无 tofu。
- **移动端安全区**：天人大圣源里完全没有 `env(safe-area-inset-*)`、viewport 也没有 `viewport-fit=cover`，按 `</head>` 前注入 `<style data-pw-safearea>`：补 `viewport-fit=cover`、`.site-header{padding-top:env(top)}`、`.back-to-top{bottom:calc(22px+env(bottom))}`（只让顶栏单层下移，不去叠加 `.header-inner` 高度，避免双重偏移）。我就是我作者已处理左右／底部，只补 `.topbar` 的 `calc(60px+env(top))` 与 `padding-top`，不重复叠加。CDP 模拟刘海（top=47／bottom=34）实机验证：天人大圣顶栏 112px／`padding-top:47px`、回顶按钮 752–798；我就是我顶栏 107px／`padding-top:47px`、fab 787–825，顶栏文字与目录弹层第一项均在状态栏下方、无挤压变形。
- **自检**：明暗双主题各截首屏复核（衡天星册 dark/light、金印神性 light/dark），无亮白块、无颜色突兀板块、文字清晰、hero 图完整；桌面 1440／移动 390 零 JS 报错、零 4xx/5xx、零横向溢出（CDP 偶发 `ERR_ABORTED` 指向站内字体分片的截图竞态，curl 逐资源全 200）；两套定级 md 非空行 279／108 行在生成页逐行命中、零缺失；坏字体 @font-face 在 DOM 层全清除（静态 0 处，运行时注入已置空）；切换器面板在主站角色页与皮肤页双向可开、卡片齐全。生成/检查图全在项目外，页面无图注、无 AI 说明、无水印杂碎文字。
- service-worker 升 `pw-v25` 强制刷新缓存。

## 2026-11-06（补4）· 新增角色「无限宝石」（漫威漫画）

- **新角色**：`【11.06】无限宝石（漫威漫画）衡天定级.zip` 内含 1 份定级 md（28754 B，md5 `cf495fe…`）＋ `img/` 下 8 张证据标注图。定级 md **逐字入库** `data/docs/characters/无限宝石（漫威漫画）衡天定级.md`（与用户文件 md5 一致），档位 `universe-std`（⊙宇○（掌控式）〔实〕，标准宇宙级 8.0×10⁷⁷ J；保底 ⊙系▽〔下〕），`doc_basis` 按新条目自身写明「第六版」，条目版本 2026-11-06。评的是宝石本身（8.3.2），电影宇宙／《What If》／平行世界不计入，持有者（灭霸、卡魔拉等）为操作者另行评级。
- **图片与位置**：沿用站内既有 `image_map` 机制——8 张 PNG 转 WebP（`quality=92`，16.7 MB → 3.4 MB，尺寸与画面零改动）落到 `static/img/characters/wuxianbaoshi/`，`characters.json` 的 `image_map` 把 md 里 `img/无限宝石_图N_….png` 逐条映射到站内文件；`VerbatimMarkdownRenderer` 按原文位置渲染 8 张 `<img class="md-img">`（带真实宽高、`loading="lazy"`），插图清单与每张图的插入位置完全照用户 md 的说明。md 里「**【插图位置 · 图N】文件名.png**」这 8 行是随包给的制作标注、不是条目正文：**存档 md 逐字不动，只在角色文档渲染时跳过这 8 行**，页面只显示图片。参考资料里的 AIPT／Comic Watch／Wikipedia／Screen Rant 等链接按既有渲染器输出为真正的 `<a target="_blank">` 超链接。
- **默认角色页视觉**：按既有 14 个角色页同一规格补齐卡片横幅 1536×865、立绘 1024×1536、头图 1536×1024 三张概念图（六宝石宇宙回路／神圣曼陀罗／星环星系，宇宙紫＋宝石金）；ImageGen 强制的右下角「AI生成 / WORKBUDDY」水印**不修补**，改在右下角小区域内检测浅灰文字包围盒、用邻近纯净背景填充并补少量暗星，三张最终图右下角放大复核零文字、零修复痕。`experience.css` 补该角色亮／暗两套完整变量块（暗色 `--dossier-surface: rgba(18,13,30,.84)` 等，宇宙紫＋宝石金，暗色 KPI 不亮白）、`.theme-wuxianbaoshi` 与共用 dossier 骨架选择器；`polish.css` 补卡片横幅标签对比色；`BOOT_BG_CHARACTERS` 补该 slug 防首帧闪屏。生成图与验证拼图全在项目外。
- **自检**：新角色页正文关键句去标签后逐字命中、8 张证据图零 404、超链接 13 处、无「【插图位置】」标记、无 AI 生成/图注/水印杂碎文字；亮暗双主题 CDP 首屏复核，暗色 KPI 为深紫黑底无亮白块、cosmos 头图正常；桌面 1440 零 JS 报错、零 4xx/5xx（CDP `--full` 偶发 `ERR_ABORTED` 为超出视口截图的请求中断假象，curl 逐资源核验全 200）、零横向溢出；列表页卡片横幅为正常宽幅、角色名清晰。项目内无检查图或预览图。全量重建同步刷新 `characters.html`／`index.html`／`tiers.html`／`tier/universe-std.html`／`search-index.js`，相邻角色（御兔↔无限宝石↔弗坦）分页上/下一位链接按新排序自动更新。
- service-worker 升 `pw-v24` 强制刷新缓存。

## 2026-11-06（补3）· 规则第六版 11-06 修订 ＋ 新增角色「至高王座」（斩！赤红之瞳）

- **规则修订（严格按约定 #18）**：用户上传 `【11.06】衡天量级体系（第六版·最新）.md`（149342 B，md5 `934cd7b…`），与站内第六版只差 3 处——版本行加「11-06 修订 10.8 一处」、修订记录新增第 11 条、10.8「他人的测量图」正文改写（报告只放自己的标注图，不转载/不点评他人测量图、不注明出处；素材截图上的他人标注先抹除或遮盖）。逐字替换 `data/docs/衡天量级体系【第六版·最新】.md`，`build_site.py` 重建 `rules.html`，并把观象台皮肤 `skins/_source/observatory.html` 的 `const Jx=\`…\`` 内嵌规则全文按同一转义规则整体替换（反转义后与规则原文逐字一致，复核 True），重建 `skins/observatory/rules.html`。**未动**首页／导航／搜索页结构／材质／98 档量级数据／全站版本标识／12 份既有角色定级 md／`characters.json` 既有条目的 `doc_basis`／任何角色类皮肤；`static/js/search-index.js` 的 2 行变化是规则全文检索索引随原文自动同步，非手动改搜索。此前定级的角色仍是第五版，未回改。
- **新角色**：`【11.06】至高王座（斩！赤红之瞳）衡天定级.zip` 内含 1 份定级 md（17459 B，md5 `b4c367d…`）＋ `img/` 下 8 张证据标注图。定级 md **逐字入库** `data/docs/characters/至高王座（斩！赤红之瞳）衡天定级.md`（与用户文件 md5 一致），档位 `city-weak`（⊙城▽〔实〕，中值 6.6×10¹⁵ J；保底 ⊙弱化弱爆城〔实〕），`doc_basis` 按新条目自身写明「第六版」，条目版本 2026-11-06。
- **图片与位置**：沿用站内既有的 `image_map` 机制（御兔先例）——8 张 PNG 转 WebP（`quality=92`，12.1 MB → 3.2 MB，尺寸与画面零改动）落到 `static/img/characters/zhigaowangzuo/`，`characters.json` 的 `image_map` 把 md 里 `img/至高王座_图N_….png` 逐条映射到站内文件；`VerbatimMarkdownRenderer` 按原文位置渲染 8 张 `<img class="md-img">`（带真实宽高、`loading="lazy"`），插图清单与每张图的插入位置完全照用户 md 的说明。md 里「**【插图位置 · 图N】文件名.png**」这 8 行是随包给的制作标注、不是条目正文：**存档 md 逐字不动，只在角色文档渲染时跳过这 8 行**，页面只显示图片，避免出现说明/杂碎文字；既有 `strip_character_doc_front_banner` 照常去掉开头引用块。参考资料里的 NDL／Wikipedia 链接按既有渲染器输出为真正的 `<a target="_blank">` 超链接。
- **默认角色页视觉**：按既有 12 个角色页同一规格补齐卡片横幅 1536×865、立绘 1024×1536、头图 1536×1024 三张概念图（帝都决战／巨型帝具机甲／弹坑，墨黑＋铜金＋暗红）；ImageGen 强制的右下角「AI生成 / WORKBUDDY」水印不用修补，**裁切时让水印区整体落在裁切框外**，三张最终图右下角放大复核零文字、零修复痕。`experience.css` 补该角色亮／暗两套完整变量块（暗色 `--dossier-surface: rgba(20,15,11,.84)` 等，暗色 KPI 不亮白）、`.theme-zhigaowangzuo` 与共用 dossier 骨架 25 处选择器；`polish.css` 补卡片横幅标签对比色；`BOOT_BG_CHARACTERS` 补该 slug 防首帧闪屏。生成图与验证拼图全在项目外。
- **自检**：规则三处修订在原文／`rules.html`／观象台源与产物四处逐字命中，观象台 `Jx` 与规则原文逐字一致；新角色页原文关键句去标签后逐字命中、8 张证据图零 404、超链接 10 处、无「【插图位置】」标记、无 AI 生成/图注/水印杂碎文字；亮暗双主题各截首屏与正文中段复核，暗色 KPI 为深棕黑底无亮白块；桌面 1440／移动 390 零 JS 报错、零 4xx/5xx、零横向溢出；列表页卡片横幅为正常宽幅、角色名清晰，移动端顶栏避开状态栏。项目内无检查图或预览图。
- service-worker 升 `pw-v23` 强制刷新缓存。

## 2026-11-06（补2）· 新增三套整页皮肤：「鎏星」「墨印长生」「晶穹」

- **来源**：用户上传的 `2.zip` 内含三个独立构建的整页——`glm-5.3 (max)＆kalmia路法斯定级页面/dist/index.html`、`fable-5.1-low＆OPUS5.5MAX＆fe-raichu＆kerria林飞定级量级页面/dist/index.html`、`opus-5-medium＆fe-raichu＆GPT5.6TERRAXHIGH＆sonnet-5-high林飞定级量级页面/dist/index.html`。三份都是自包含的 React 阅读器（字体与首屏图内联），各带亮暗主题、字号调节与章节目录；定级原文与项目内 `data/docs/characters/林飞…衡天定级.md` md5 完全一致（`a19ee6c…`，第五版，按约定不回改第六版），露法斯 `content.ts` 亦自述「全部文本转录自原条目（2026-10-29 版），未删改」。
- **注册**：`data/editions.json` 新增 `ruphas-gilded`「鎏星」（`GILDED STAR · 终局档案`，暗夜鎏金＋星轨＋金色衬线巨字，`section=character-lufasi`）、`linfei-inkseal`「墨印长生」（`INK SEAL · 超脱`，水墨宣纸＋朱印超脱＋竖排「长生万万年·不败天地间」，`section=character-linfei`）、`linfei-crystal`「晶穹」（`CRYSTAL DOME · 宣纸`，淡金宣纸＋宇宙晶体光球＋洪荒盘古场景图，`section=character-linfei`），均为 `inject: minimal`。`default.pages` 补 `character-linfei: character/linfei.html`。切换器项数：路法斯页 3 套（默认／绛翼／鎏星），林飞页 3 套（默认／墨印长生／晶穹）；新皮肤与旧皮肤并存，不删不改。
- **资源**：「鎏星」「墨印长生」全内联，无需搬运资源；「晶穹」引用 `./images/{crystal,honghuang,linfei,pangu}.jpg` 与 `./source.md`，按生成页所在目录原样落到 `skins/linfei-crystal/`，相对路径零改写。「晶穹」没自带 icon，由构建器既有逻辑自动补站内 `favicon-32.png`，避免浏览器回退请求站点根 `/favicon.ico` 的 404；另两份自带 data-URI icon，保留不覆盖。ASSETS / README / RESEARCH 等说明文件一律不进项目。
- **移动端安全区**：「墨印长生」作者已用 `--chrome-height`、`drawer-panel`、`mobile-dock`、`totop`、`footer` 完整处理 `env(safe-area-inset-*)`，不再注入以免双重叠加。「鎏星」（顶栏 65px）与「晶穹」（顶栏 62px）完全没做安全区，按各自语义类名注入 `calc(原高 + env(safe-area-inset-top))` 与 `padding-top`，并给固定底部工具条补 `calc(20px + env(safe-area-inset-bottom))`。CDP 模拟刘海（top=47／bottom=34）实机验证：三套顶栏分别落在 112／112／109px、`padding-top: 47px`，顶栏文字与目录弹层第一项均在状态栏下方、无挤压变形。
- **自检**：明暗双主题各截正文中段复核，无亮白块、无颜色突兀板块；桌面／移动端零 JS 报错、零 4xx/5xx、零横向溢出（CDP 偶发 `ERR_ABORTED` 指向 `editions.js/css` 的新建标签请求竞态，切换器面板实机可开、卡片齐全，非资源缺失）；切换器面板 3 项在 5 个页面实机打开确认；生成页去掉注入块后与源 HTML 逐字一致（三份全部 True），正文零改动；页面无图注、无 AI 说明、无水印杂碎文字，项目内无检查图或预览图，仅保留切换器必需的 3 张 640×400 缩略图（按最终皮肤页真实渲染、清 localStorage 后重截）。
- service-worker 升 `pw-v22` 强制刷新缓存。

## 2026-11-06（补）· 新增两套整页皮肤：「孤灯」（弗坦）与「绛翼」（露法斯）

- **来源**：用户上传的 `1.zip` 内含两个独立构建的整页——`gpt-6-luna-max弗坦定级页面/dist/index.html` 与 `GPT6astraMAX路法斯定级页面/dist/index.html`。两份都是自包含的 React 阅读器，正文内嵌，各带亮暗主题、字号调节、章节目录与阅读进度；定级原文与项目内 `data/docs/characters/` 对应文件 md5 完全一致（第五版，按约定不回改第六版）。
- **注册**：`data/editions.json` 新增 `futan-lamp`「孤灯」（`tag: LONE LAMP · 003`，海蚀洞巨幕＋孤舟微灯的墨黑绿长卷，`section=character-futan`）与 `ruphas-crimson`「绛翼」（`tag: CRIMSON WING · 黑翼档案`，黑底金发黑翼巨像＋珊瑚红印章的衬线卷宗，`section=character-lufasi`），均为 `inject: minimal`。`default.pages` 补 `character-lufasi`；弗坦页现有「无光之渊」，新增后切换器自动列出 3 套（默认／无光之渊／孤灯），路法斯页 2 套（默认／绛翼），双向切换无需改切换器代码。
- **资源**：弗坦只需 1 张封面图；路法斯补齐封面、favicon、`content/original.md`（noscript 与「查看原始 Markdown」用）与 3 套 Archive 子集字体。ZIP 的 `dist/fonts/` 只带 OFL 许可证、缺字体二进制（页面 `@font-face` 会 404），从同包 `.cache/portable-test/…/assets/styles.css` 里同源的 base64 子集解码补回，页面字体与排版原样保留，零 404。ASSETS.md / START-HERE.txt / RESEARCH 等说明文件一律不进项目。另给没自带 icon 的 minimal 皮肤在构建时补站内 `favicon-32.png`（认 head 真正的末尾），消除浏览器回退请求站点根 `/favicon.ico` 的 404；「绛翼」自带的 `favicon.svg` 保留不覆盖。
- **构建器修复**：这两份整页把 `</head><body>`、`</body></html>` 当作字符串写进打包后的 JS（DOMParser 代码）；`build_skin_editions()` 原来按**第一个** `</body>` 注入，切换器被塞进脚本里，React 直接崩、页面只剩源码文本。改为 `rpartition` 只认最后一个真实结束标签；源 HTML 注入安全区样式同样改为认最后一个 `</head>`。生成页去掉注入块后与源 HTML 逐字一致，正文零改动。
- **移动端安全区**：两份源页加 `viewport-fit=cover`，并按各自语义类名与断点注入 `header.site-header` 的 `calc(原高 + env(safe-area-inset-top))` 与 `padding-top`（弗坦 76px／≤720px 64px；路法斯 85px／≤800px 72px／≤520px 66px）；弗坦阅读进度条同步下移，路法斯目录弹层补 `padding-bottom: env(safe-area-inset-bottom)`。另发现 `editions.js` 用 inline `style.bottom` 覆盖了 `editions.css` 的底部安全区，新增 `safeBottomInset()` 实测 env 值计入 `baseBottom`（全站通用修复）。CDP 模拟刘海（top=47／bottom=34）实机验证：顶栏 111px／113px、`padding-top: 47px`，切换器印章 bottom=796（=844−34−14），目录弹层顶部落在状态栏下方、底部留出安全区。
- **自检**：明暗双主题各截正文中段复核，无亮白块、无颜色突兀板块、文字清晰；桌面／移动端零 JS 报错、零 404（字体补齐、favicon 补入后）、零横向溢出；切换器面板 3 项／2 项实机打开确认；页面无图注、无 AI 说明、无水印或杂碎文字，项目内无检查图或预览图，仅保留切换器必需的两张 640×400 缩略图（按最终皮肤页真实渲染重截）。线上 Pages 逐字节核验：皮肤页、默认角色页、缩略图、字体与本地完全一致。
- service-worker 升 `pw-v21` 强制刷新缓存。

## 2026-11-06 · 新增皮肤「茶白·长夜」（三世铜棺之主量级页面）· 含配色收敛

- **来源**：用户上传的 `opus-5.5-high＆DS4.1MAX三世铜棺之主量级页面.zip`，取其中已构建好的 `dist/index.html`。该文件完全自包含（7 张图、4 套字体全部内联，零外部资源引用），直接作为整页皮肤源，无需搬运图片目录或改写路径。页面自带的定级原文、13 个章节、长夜／茶白双主题、字号调节与目录交互一律原样保留。
- **注册**：`data/editions.json` 新增 `bronze-coffin`（`section=character-tongguan`、`inject=minimal`），并在 `default.pages` 补 `character-tongguan: character/tongguan.html`——凑够两套皮肤，切换器才在主站角色页与皮肤页双向出现。构建产物 `skins/bronze-coffin/character-tongguan.html`；切换器缩略图取页面真实首屏截图（640×400）。
- **minimal 注入**：只挂 `editions.css` + 切换器浮层 + `editions.js`，不注入主站 `app.css` / `chrome.js` / `pwa.js` / manifest，避免污染 React 应用的内联样式与 DOM（与「无光之渊」一致）。
- **移动端安全区**：按该应用自身的语义类名精确注入，未照抄弗坦的 Tailwind 选择器。`.topbar` 固定高度（桌面 60px / ≤430px 54px）原本没有顶部安全区，改为 `calc(60px + env(safe-area-inset-top))` 并加 `padding-top`；`.toc-rail` sticky 偏移同步下移。页面自带的 `.sheet-body`、`.backtop` 已处理底部安全区，保持不变。CDP 模拟刘海（top=47 / bottom=34）实机验证：顶栏 101px、按钮落在 y=58–90 完全避开状态栏，底部 52px / 58px 正常。
- **配色收敛（用户反馈后修正）**：该 zip 与「无光之渊」出自同一套模板，连 `--verdigris: #79bfb1` 亮青绿主色都一并带过来，混在赭铜／金／墨／茶白里；`.verdict` 综合定级卡更叠了「左下青绿＋右上朱砂」双色渐变，同层卡片又分纯白／米白／虚线框几种底，板块颜色杂乱。改用纯 CSS 变量覆盖收敛：青绿 → 铜锈墨绿（亮 `#3d6b5d` / 暗 `#82a89a`），朱砂 → 沉印泥红；`.verdict` 改单一赭金晕染 + 与同层一致的表面；`.kv` / `.ia-zone` / `.gl-k` 统一底色；亮色主题下 `.interlude` / `.toast-frame` 由死黑改墨绿黑 + 铜金描边。皮肤名与 tag 也从「长夜铜棺 / COFFIN · 长夜卷」改为取自页面自带主题名的「茶白·长夜 / BRONZE COFFIN」，去掉照抄「无光之渊 / ABYSS · 深海卷」的格式感。缩略图按改色后首屏重截。全程只加 `<style data-pw-palette>`，不动 React 结构、不动定级原文。
- **自检**：双向切换（主站角色页 ⇄ 皮肤页）往返成功；皮肤页自身主题切换、字号调节、目录抽屉与 Esc 关闭均正常；桌面/移动端零 JS 报错、零 404、零横向溢出；主站角色页 diff 仅 1 行（挂切换器），定级原文关键句逐字命中、零改动；项目内无检查图或预览图，仅保留切换器必需缩略图。亮/暗双主题各板块实机截图复核，配色收敛后无亮白块、无冷色突兀。

## 2026-11-05（夜·补6）· 新增五位角色：林飞 / 下游者 / 江无夜 / 古尘沙 / 雪之少女

- **原文逐字入库**：5 份定级文档从用户给的 GitHub 仓库拉取，md5 与源一致，正文零删改；文件名沿用站内惯例（去掉日期前缀）。按约定「之前定级的角色就是之前的版本」，5 份原文页眉「定级依据：《…第五版》」与 `doc_basis` 均保留第五版，不随规则第六版回改。
- **档位归属**：林飞 → `beyond-gate`（⊙外·门 ℵ₀〔实〕· 结构 φ(ω,0)）；下游者 → `universe-std`（⊙宇○ 弱化·需时·触发式〔下〕）；江无夜 → `beyond-gate`（⊙外·门 ℵ₀〔实〕· 叙事层阶梯 ω 层）；古尘沙 → `universe-strong`（⊙宇△ 掌控式〔实〕· 元·多）；雪之少女 → `beyond-gate`（⊙外·门 ℵ₀ 掌控式〔下〕）。
- **默认角色定级页面**：按用户确认，与现有 7 个角色完全一致的完整默认形态；未新增皮肤、未改任何布局结构，共 12 个角色页。
- **配图**：每角色 3 张共 15 张——卡片横幅 1536×865（页面卡片原生 16:9）、立绘 1024×1536、头图 1536×1024；build 依真实尺寸自动判 `is-landscape` 满铺，全站 12 张卡零 `is-square`。右下角强制水印用紧 ROI 精确去除并逐张放大复核，15 张无文字、无修复痕；压缩至合计 4.55 MB。生成图与验证拼图全在项目外，项目内仅 15 张必需图；无图注、无 AI 说明、无杂碎文字。
- **主题与对比色**：`experience.css` 补 5 套明暗变量块并把 5 个 slug 并入共用 dossier 骨架 25 处选择器；`.theme-*` 各自定义明暗 `--dossier-surface`，实机 5 页暗色 KPI 零亮白块。`BOOT_BG_CHARACTERS` 补 5 项防首帧闪屏；`polish.css` 补 5 条横幅标签对比色（同等特异性）。
- **自检**：5 页无 JS 报错、无 404、无坏图、无图注；定级原文关键句逐字命中；移动端无横向溢出、安全区 CSS 保留；卡片标签对比色各自生效。
- service-worker 升 `pw-v17` 强制刷新缓存。

## 2026-11-05（夜·补5）· 规则升级第六版，全站同步

- **规则原文整体替换**：从用户给的 GitHub 仓库拉取《【11.05】衡天量级体系（第六版·最新）.md》，与线上逐字节校验一致后落盘为 `data/docs/衡天量级体系【第六版·最新】.md`，替换第五版文件；`RULES_MD_PATH`、规则页标题、`source_filename` 同步。第六版目录 138 节（第五版 136 节）。
- **第六版新增内容全部上线**：第六版修订要点、8.5「门槛之上的结构证据」、1.7.1 保底量级、1.3 第 8 条未定级与不予定级、0.14.1 作者场外说明、0.14.2 后文推翻细化、1.4 触发式破坏 ⇒ 御、5.6 能量枯竭补充、7.6 互相包含（非良基）、8.1 世界观推定两步与「字面用法」反例、8.4 术语对象的错位、7.9「无法判定」措辞、附：未定稿事项第 9 项等，逐条在 `rules.html` 命中。
- **量级数据零改动**：第六版明确「不改动任何量级刻度和能量数值，也不新增档位」，98 档结构化数据与全部角色定级结论原样保留；`tiers.json` 只更新 `system_name` 与体系 `version` 5.0 → 6.0。
- **全站版本标识**：生成器 24 处、导航与抽屉、首页 eyebrow（第六版 · 2026.11.05 最新基准）、搜索页、搜索索引 138 条规则条目的 `衡天第六版` 标题与 badge、`static/js/app.js`、`README.md`、meta description、`version_label`（第六版 · 2026.11.05）、构建日志 v5 → v6 全部统一。
- **皮肤**：观象台内嵌的规则全文（压缩 JS 中的模板字符串 `Jx`）整体替换为第六版原文并做 JS 模板转义，重新提取反转义后与原文逐字一致；`Jx` 之外的 UI 版本标识同步。第六版原文自身的「在第五版基础上修订」「第五版修订要点」等历史引用按原文保留。
- **定级档案原文一字未改**：7 份角色定级文档、`characters.json` 的 `doc_basis`、月面／无光之渊皮肤内嵌的「定级依据：《…第五版》」按用户铁律保留——这些条目确实依据第五版定级，第六版不改量级数值，结论仍有效。
- 实机核验：规则页 138 节目录、首页／搜索页无「第五版」标识、观象台与另两套角色皮肤渲染正常、无 JS 报错；service-worker 升 `pw-v16` 强制刷新缓存。

## 2026-11-05（夜·补4）· 三世铜棺之主卡片图由正方形改横幅

- **根因**：`static/img/characters/tongguan/character-card.jpg` 是 720×720（1:1），`enrich_character_media_dimensions()` 按图片真实宽高比判成 `is-square`，所以列表卡一直是正方形；其余六个角色卡片图都是横幅（`is-landscape`）。
- **只换图、不动页面结构**：重新绘制三重青铜古棺横幅（青绿铜锈 / 灰烬白雾 / 深黑宇宙漩涡），按页面卡片媒体区原生 16:9（实机实测桌面 378×213、移动 348×196）裁成 **1536×865**。三口棺全部完整、几乎零二次裁切；`style.css` 等布局结构一行未动。
- **水印处理**：生成图右下角强制烤入的「AI生成 / WORKBUDDY」先做紧 ROI 精确修复，再落在被裁掉的底部纯暗区域，最终右下角亮像素 0、放大复核无字无修复痕。生成图、模拟裁切图、验证截图全部留在项目外临时目录，项目内只有这一张必需图。
- **标签对比色**：`polish.css` 补 `char-card-tongguan` 的横幅标签规则（`#f0c96b` + 深色描边），与其余角色一致，避免被 `style.css:3863` 的 4 类特异性 `is-landscape::after` 盖掉。
- **影响范围**：`characters.html`、`index.html`、`tier/universe-extreme.html` 三处铜棺卡片均变为 `is-landscape`；实机桌面 / 移动端核验通过，全站 7 张角色卡已无 `is-square`，页面无「AI生成 / WORKBUDDY / 形象参考」等说明文字。
- service-worker 升 `pw-v15` 强制刷新缓存。

## 2026-11-05（夜·补3）· 新增两位角色：露法斯·玛法尔 / 天人大圣

- **新增角色与档位归属**：
  - 露法斯·玛法尔（《野生的最终BOSS出现了》）→ `beyond-gate` 论外门槛（#90）；文档综合量级「⊙外·门（ℵ₀）〔下〕· 结构三层」，保底量级 ⊙宇☆〔下〕。
  - 天人大圣（《走进修仙》）→ `beyond-sky-low` 论天下（#94），按用户指定「论天那边，强不可达」；综合量级 ⊙宇○（掌控式）〔实〕，位格字面为论天下（强不可达基数）及以上、结构证据〔缺〕。
  - 两份定级文档从用户给的 GitHub 仓库逐字拷贝，md5 与源一致，正文零删改；页面 h2 数量与表格数、关键句逐字内联均已核验。
- **配图按「生成合适比例」而非改页面结构**：两角色各 3 张，卡片横幅 3:2（1536×1024）、立绘 2:3（1024×1536）、头图 3:2（1536×1024）；build 依图片真实尺寸自动判为 `is-landscape` 满铺，`style.css` 等布局结构一行未动。
- **去水印**：6 张生成图右下角强制烤入的「AI生成 / WORKBUDDY」精确修复去除；其中天人大圣头图因水印压在复杂晶格上，重新生成一张并将右下角留纯暗底后无痕去除。生成图、验证拼图全放项目外临时目录，项目内仅 6 张必需图。
- **无任何说明/AI/杂碎文字**：`portrait_caption` 为空、不渲染图注；收敛全站模板 `char-portrait-stage` 的 `aria-label` 与图片 `alt`，去掉「形象参考」措辞改纯角色名（隐藏无障碍文本，不动视觉与布局）。
- **主题配色（各角色独立）**：露法斯＝绯紫黑＋熔金（黑翼霸王 / 十二星天），天人大圣＝墨青＋冷银金（初代恒星 / 数学宇宙晶格），与已有靛蓝（犹格）、白金（至高神性）区分；`experience.css` 补两套明暗变量块并并入共用 dossier 骨架，`.theme-lufasi` / `.theme-tianren` 在 dossier 元素自身定义明暗 `--dossier-surface`，避免暗色 KPI 等 5 处变亮白块。
- **顺带修好历史遗留**：`style.css:3863` 的 `.char-card.media-top .char-card-media.is-landscape::after`（4 类特异性）会盖过 2 类的角色名对比色规则，导致上一轮 yog / divinity 的对比色在横幅卡片上失效；改用同等以上特异性的选择器，四个角色高亮色 + 深色描边现已全部生效。
- `BOOT_BG_CHARACTERS` 补两角色防首帧闪屏；service-worker 升 `pw-v14` 强制刷新缓存。
- 实机自检：7 个角色页暗色 KPI 全为深色无亮白块、浅色无回退、移动端安全区规则完好、列表卡横幅满铺、原文逐字内联、项目内无检查图。

## 2026-11-05（夜·补2）· 修复新角色暗色主题 KPI 等板块变亮白块

- **问题**：暗色下 yog / divinity 的「综合主档定级」「保底量级」两张 KPI 卡、
  右上 dossier 徽标、立绘容器、立绘角标共 5 处呈 `rgba(255,255,255,.58)` 亮白块，
  浅色文字近乎白底白字，与暗色版割裂；老角色 tongguan 暗色无此问题。
- **根因**：`.character-dossier` 自带白色兜底 `--dossier-surface`；按 CSS 变量
  「元素自身定义 > 继承」，挂在 `body` 上的 `character-yog/divinity` 暗色变量被它盖掉。
  老角色是把明暗表面色定义在 dossier 元素自身的 `.theme-tongguan` 类上。
- **修复**：`experience.css` 给 `.theme-yog` / `.theme-divinity` 补明暗两套
  `--dossier-surface`（暗色 yog `rgba(18,28,56,.82)` / divinity `rgba(22,19,12,.82)`，
  浅色各取对应浅色），与老角色写法一致。一行变量同时修好 5 个板块，未改页面结构。
- **全面自检**：playwright 实机 dump 明暗两套 computed background-color，逐项对比
  tongguan；暗色白块由 5 处降为 0（仅剩三角色共有的刻度金点，属设计元素），
  浅色无回退；滚动至量级信息面板与正文区复查，全页无残留亮块。
- service-worker 升 `pw-v13` 强制刷新样式缓存。

## 2026-11-05（夜·补）· 重新生成合适比例配图 + 去水印 / 去图注 / 角色名对比色

- **重新生成 6 张配图（核心）**：yog / divinity 各 3 张整套重做，比例按页面原生版式匹配——
  角色卡横幅 1536×1024（3:2）、立绘竖版 1024×1536（2:3）、头图横幅 1536×1024（3:2）。
  卡片图由方形改横幅后，`build_site.py` 的 `classify_image_shape()` 自动判为 `landscape`，
  列表卡自动走 `object-fit:cover` 满铺版式。**全程未改任何页面结构 / CSS**，靠图片比例本身适配。
- **去除配图 AI 水印**：图片工具强制在右下角烤入「AI生成 / WORKBUDDY」，已用 opencv 精确修复
  文字像素去除，画面无 readable 文字、亮部无误伤；生成预览/检查图全部放项目外临时目录，未入库。
- **删除配图下说明文字**：`data/characters.json` 五位角色 `portrait_caption` 清空；`build_site.py`
  改为 caption 空则不渲染 `char-portrait-caption`，消除「形象参考·艺术演绎」等说明。文档正文未改动。
- **左上角角色名对比色**：yog / divinity 卡片 `data-art-label` 改高亮色 + 深色描边
  （`#9fd8e6` / `#fdf3d0`），压在配图上也清晰显著。
- service-worker 升 `pw-v12` 强制刷新缓存（本轮图片整套重做）。

## 2026-11-05（夜）· 新增两位角色：犹格·索托斯 / 我就是我·至高神性

- **犹格·索托斯（克苏鲁神话原作）**：新增默认角色页 `character/yog.html`，归属 `beyond-gate`（论外门槛）档；定级结论综合主档未定级、位格存在规模为外·门（论外门槛，可数无限 ℵ₀）。原定级文档逐字拷入 `data/docs/characters/`（md5 校验未改动）。
- **我就是我·至高神性（《法师：飞升》）**：新增默认角色页 `character/divinity.html`，按需求归入**暂存**（`pending` / 待定／暂存档）；综合主档未定级，存在规模记"遍及全部造化（规模未定）"，创世文字作"若采信"存疑。原文档逐字拷入 `data/docs/characters/`。
- **角色图自生成**：两位各 3 张图（角色卡 1:1 / 立绘 2:3 / 题图 3:2 横幅），比例对齐现有角色图规范，置于 `static/img/characters/yog/`、`static/img/characters/divinity/`。
- **新角色主题**：`experience.css` 追加 yog（靛蓝虚空+古金）、divinity（白金辉光）两套完整变量块 + 共用 dossier 视觉段；`build_site.py` 的 `BOOT_BG_CHARACTERS` 补 `character-yog` / `character-divinity` 防首帧闪屏。
- service-worker 升 `pw-v10` 强制刷新缓存。

## 2026-11-05（晚）· 全站移动端安全区自检与底部留白优化

- **全站移动端安全区补齐（自检核心发现）**：`polish.css` 统一给 `.site-header` / `.reading-progress` /
  `.site-drawer` / `.floating-dock` / `.modal-backdrop` / `.doc-sidebar` 加 `env(safe-area-inset-*)`，
  顶栏、阅读进度条、移动抽屉、浮动工具、搜索模态、文档侧栏在真机上自动避让系统状态栏与
  Home Indicator。桌面端 `env` 为 0，布局完全不变；独立窗口（`[data-standalone="1"]`）仍由
  `app.css` 用实测 `--pw-top-inset` 接管，二者特异性分工不冲突。
- **5 个皮肤页顶栏安全区**：`archive` / `atlas` / `observatory` / `moonfile` 四个整页皮肤的源
  `head` 各注入针对性顶栏安全区样式（`futan-abyss` 此前已修）。之前这些皮肤顶栏均 `top:0` 直接
  贴状态栏，且源码只给底部 toast/dock 加了安全区、漏了顶栏——本次补齐（含固定高度顶栏的高度补偿）。
- **移动端底部留白**：`main` 加 `padding-bottom: 6rem`，避免滚动到底时正文被右下角浮动工具
  （目录 / 字号栏 / 回顶）遮挡。
- 验证：真机模拟 44px 状态栏后，主站与全部皮肤页顶栏内容均精确下移 44px 让出状态栏，抽屉头部与
  浮动工具同步避让；暗色模式顶栏安全区规则与主题无关、正常生效。`service-worker` 升 `pw-v9`
  强制刷新缓存。

## 2026-11-05（下午）

- **弗坦新增整页皮肤「无光之渊」（ABYSS · 深海卷）**：把用户提供的独立构建的弗坦定级
  React 应用（`dist/` 单文件 SPA + 10 张配图）做成弗坦角色页（`character-futan`）的整页皮肤
  edition，接入页面皮肤切换器。`editions.json` 里 `default` 与 `futan-abyss` 都登记了
  `character-futan`，弗坦页因此出现切换器（切换器规则：同栏目不足两套不挂）；`futan-abyss`
  的 `source` 指向 `skins/_source/futan-abyss.html`（图片引用由绝对 `/images/` 改为相对
  `./images/`），`inject` 设为 `minimal`，缩略图 `static/img/editions/futan-abyss.jpg`。
- **构建器新增 `minimal` 注入模式**：`build_site.py` 的 `build_skin_editions` 对 React /
  第三方整页应用皮肤只注入切换器浮层（`editions.css` + `editions.js` + launcher），不注入
  主站 `app.css` / `chrome.js` / `pwa.js` / `manifest`——否则会污染应用自身的内联样式与 DOM。
- 验证：弗坦默认页与「无光之渊」双向切换正常、React 应用完整渲染（弗坦定级条目 / 配图 /
  图表卡片）、切换器缩略图 URL 200、无 JS 报错；`service-worker.js` 升 `pw-v8`。

## 2026-11-05（中午）

- **新增角色：三世铜棺之主（《遮天三部曲》）**
  按用户上传的《【10.28】三世铜棺之主（遮天三部曲）衡天定级》建条目，归入
  `universe-extreme`（⊙宇◆ 极宇宙，#81，8.0×10⁸⁵–8.0×10⁹³ J）——与文档「点眉心一刹那
  亿万宇宙成灰、说话间全部复原」的主档结论一致。`characters.json` 写入完整字段：
  七维（破 / 控同档宇◆〔实〕，御 / 域 / 算〔缺〕，速远超光速〔下〕，性含自我抹除等）、
  位格「—」、证据链摘要、三个事实卡片与专属 `visual` 配置；定级 md 放入
  `data/docs/characters/`，全文自动渲染成 27 节档案（13 个 h2 / 10 张表 / 4 段引文）。
- **配图自行生成（3 张，合计约 580 KB）**：三重青铜古棺星海（页头 1400×933）、
  苍白病人小院立绘（900×1350）、铜棺方形卡片图（720×720）；逐张修复掉右下角
  「AI 生成」水印并压缩为 JPG，避免串用御兔的月球底图。
- **专属「灰烬青铜」皮肤**：`experience.css` 增加 `body.character-tongguan` 明暗两套
  完整配色（含 `--char-atmosphere` 指向新图、`--banner-art-opacity`，二者缺一即导致
  氛围层空白 / 浅色页头图不可见），档案盒用细金边＋双层内描边呼应「三重棺椁」，
  事实卡片编号用「壹 / 贰 / 叁」，配衬线巨题、灰烬浮尘与宽屏角标；`style.css`、
  `editorial.css` 同步补 `.theme-tongguan` 变量与排版；`build_site.py` 的
  `BOOT_BG_CHARACTERS` 登记首帧底色，杜绝冷启动白闪。
- **窄屏兼容**：`.tag-pill` 全局为 `nowrap`，320px 下长标签会被父级裁掉；精简
  `modifiers` 文案并在本角色档案盒内放开折行，标签与标题在 320 / 390 均完整无溢出。
- `service-worker.js` 版本升 `pw-v7`。
- **验收（真实 Chromium）**：1440 / 390 / 320 × 明暗两套共 6 组，零 JS 报错、
  零请求失败、零横向溢出，两张首屏图均加载、氛围层就绪；冷启动首帧底色浅
  `(227,223,211)` / 深 `(16,26,23)` 各 10 帧零跳变；量级页 `#81 极宇宙` 正确收录、
  角色库 `3 / 3 位`、首页统计 3、搜索索引新增 34 处分节、弗坦分页器自动指向新角色。

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
- **规则文档同步到 11.04 最新版**
  比对 testonly 仓库《【11.04】衡天⊙量级体系（第五版·最新）》与站内
  `data/docs/衡天量级体系【第五版·最新】.md`：1641 行中仅 2 处差异，且站内文件无
  powerwiki 自有改写，安全同步。改动即官方「2026-11-04 修正 8.3.1 措辞」：
  (1) 版本注记补 `2026-11-04 修正 8.3.1 措辞`；(2) `8.3.1 序数不能当作"攀爬式境界"`
  段把"构造 ω、ω²、ε₀ 乃至任意可数序数"收紧为"构造 ω·2、ω²、ε₀ 这类能明确写出的
  序数（不是任意可数序数：…例如邱奇–克莱尼序数 ω₁^CK 及以上，本条不涉及）"。
  `rules.html` / `search-index.js` 已随构建刷新。

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
