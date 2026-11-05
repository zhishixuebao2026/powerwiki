# 衡天⊙ PowerWiki（v9.1）

以《衡天⊙ 多维战力量级体系（第五版）》和《材质与破坏能量数据库（第二版）》为基准的静态战力量级百科。

## 文档

- `README.md`（本文件）：站点结构、构建流程、皮肤系统怎么实现。
- `CHANGELOG.md`：按日期的更新记录，条目对上提交哈希。
- `docs/需求与约定.md`：用户提出过的硬性要求、每条的落实方式与验收口径、已知取舍。

## 页面

- `index.html`：精简首页，集中提供量级、角色、规则三类入口。
- `tiers.html`：98 个连续量级，支持卡片、天梯、总表三种视图及区间筛选。
- `characters.html`：角色目录；少量角色使用轻量布局，角色增多后自动启用完整筛选。
- `rules.html`：第五版体系全文，含目录、页内查找、字号与宽屏设置。
- `materials.html`：材质与破坏能量全文。
- `search.html`：全站检索；其他页面可按 `Ctrl + K` 或 `/` 唤起搜索。
- `tier/*.html`、`character/*.html`：自动生成的独立详情页。
- 窄屏下章节抽屉从右下角工具坞打开，带独立关闭按钮、遮罩层与「全站导航」出口；按 `Esc` 或点遮罩即可关闭。

全站采用统一的档案式编辑设计，提供完整的亮色与暗色模式，适配桌面与手机。御兔使用月白／午夜两套页面级月面轨道主题，弗坦使用雾绿／黑金两套页面级深渊主题，三世铜棺之主使用灰烬米纸／墨铜暗金两套页面级「灰烬青铜」主题；背景、导航、目录、正文、表格、阅读工具、搜索与页脚均随角色模式协调变化。角色正文提供主题化阅读进度、章节编号与测量图版，搜索摘要经过可读性清理；各角色的形象原图、完整证据与阅读工具均保留。中文 Noto Sans SC、Noto Serif SC 和英文 Space Grotesk 可变字体随站本地提供，不依赖外部字体 CDN。生成页面使用相对路径，可直接部署到 GitHub Pages 等静态托管服务。

## 当前内容（2026-10-25）

- **规则**：`data/docs/衡天量级体系【第五版·最新】.md`。
- **御兔**：`data/docs/characters/御兔（非人学园）衡天定级.md`；官方立绘与两张测量图保持不变。
- **弗坦**：`data/docs/characters/弗坦（诡秘地海）衡天定级（新）.md`；使用横向克苏鲁风格形象参考壁纸。
- **三世铜棺之主**：`data/docs/characters/三世铜棺之主（遮天三部曲）衡天定级.md`；归入 `universe-extreme`（⊙宇◆ 极宇宙，#81），配图为生成的三重青铜古棺星海（页头 / 卡片）与苍白病人小院立绘，已去除水印并压缩至合计约 580 KB。
- **材质**：`data/docs/材质与破坏能量数据库（新）.md`。

第五版不改变既有量级刻度和能量数值，因此保留现有 98 档结构化数据，仅更新规则原文、证据规范与全站版本标识。

## 数据与构建

主要输入：

```text
data/
├── characters.json        # 角色元数据、视觉主题、图片映射与摘要
├── tier-art-tuning.json   # 98 张档位配图的取景重心与浓淡补偿（按图实测，缺失时回落 CSS 默认值）
├── tiers.json             # 量级和分组定义
├── editions.json          # 页面皮肤登记表（id / 名称 / 缩略图 / 各栏目页面路径）
└── docs/                  # 完整 Markdown 原文
static/
├── css/style.css          # 功能样式与基础设计系统
├── css/editorial.css      # 全站外壳与角色明暗设计
├── css/experience.css     # 阅读工具栏与档位配图等体验层样式
├── css/editions.css       # 皮肤切换器的样式
├── css/polish.css         # 打磨层：悬浮层地板线、排版、响应式细节（最后加载，只覆盖）
├── fonts/                 # 本地可变字体与 SIL OFL 许可证
├── js/theme.js            # 明暗主题切换（只改 data-theme / 状态栏 / 图标 / 多标签同步）
├── js/app.js              # 筛选、搜索、目录与阅读工具（交互引擎）
├── js/pwa.js              # 静默离线：注册 SW、预热页面、独立窗口适配
├── js/chrome.js           # 量底部固定栏写入 --pw-floor；筛选条的滑到头提示
└── img/                   # 本地图片与角色主题美术（`img/tiers/<slug>.jpg` 为每档独立配图，16:9；缺图时回落同名分组图）
```

修改数据或文档后，在仓库根目录执行：

```bash
python3 build_site.py
```

生成器仅使用 Python 3 标准库，会重新生成所有静态页面及 `static/js/search-index.js`。`pelican.html` 是独立的单文件动画，不参与主站构建。

## 离线可用（静默，无安装提示）

站点照常支持断网阅读，但**全站不提供任何「装成 App / 下载本地 / 添加到主屏幕」
的按钮、气泡或引导面板**——不需要也不希望看到这类提示，离线能力完全静默运行。

| 文件 | 作用 |
|---|---|
| `manifest.webmanifest` | 名称、`standalone` 显示模式、`scope`、4 个图标（含 maskable）、4 个快捷方式 |
| `service-worker.js` | 离线缓存：壳层预缓存 + 导航网络优先 + 静态资源分级策略（当前 `pw-v7`） |
| `offline.html` | 断网且没缓存时的兜底页（纯系统字体，不依赖任何网络资源） |
| `static/js/app.js` | 站内交互引擎：搜索 / 筛选 / 目录 / 阅读工具 / 回到顶部 |
| `static/js/pwa.js` | 静默注册 SW、预热常用页面、独立窗口安全区、左边缘返回手势 |
| `static/css/app.css` | 仅剩独立窗口的安全区与状态栏留白（已无任何安装按钮样式） |
| `static/img/icons/` | 192 / 512 / maskable 512 / apple-touch-icon 180 / favicon 32 |

**独立窗口适配**：`html[data-standalone]` 由 `pwa.js` 判断后写入，随后把实测的顶栏安全边距
写进 `--pw-top-inset`（`env(safe-area-inset-top)` 在很多机型上是 0，不能只靠它），
顶栏高度与底部留白据此调整；主屏幕启动时接管左边缘滑动返回。

**注意**：service worker 只在 https / localhost 下注册，`file://` 直接打开不受影响。
`docs/需求与约定.md` 的「一·五、装成 App 的验收」已按「不做安装提示」的决策更新：
保留 manifest / 独立窗口等能力给想自己加主屏的人用，但全站不出现任何安装引导入口。

## 页面皮肤（整页换设计）

一套皮肤 = 一份完整的整页设计。左下角的「⊙ 皮肤」印章可以在它们之间跳转，每张卡片带缩略图、名称和"当前"标记。

| id | 名称 | 来源 | 覆盖页面 | 说明 |
| --- | --- | --- | --- | --- |
| `default` | 默认 | 本仓库生成器（`build_site.py`） | 全站：首页 / 98 档量级 / 角色 / 规则 / 材质 | 建筑感栅格 |
| `archive` | 卷宗 | `skins/_source/archive.html`（整页自包含产物） | 材质页 | 米纸底、左侧索引栏的档案排版 |
| `atlas` | 星图 | `skins/_source/atlas.html`（整页自包含产物） | 材质页 | 大留白、描边巨字、裂星主视觉 |
| `observatory` | 观象台 | `skins/_source/observatory.html`（原 `KALMIA衡天量级体系.zip`） | 规则页 | 夜观 / 昼测双主题、二十八宿衡天仪、全链对数天梯 |
| `moonfile` | 月面 | `skins/_source/moonfile.html`（原 `opus-5.5-high御兔量级页面.zip`） | 御兔角色页 | 米纸底、墨笔巨字、月面插图与红色印章的卷宗排版 |

规则：**切换器只列出"当前这一页真有对应页面"的皮肤**。首页只有 `default` 有页面，所以首页不出现切换器；
材质页三套都有（默认 / 卷宗 / 星图），规则页两套（默认 / 观象台），御兔角色页两套（默认 / 月面）。
站在别的皮肤上时，左下角常驻一个回主站首页的按钮。

明暗仍由右上角的太阳 / 月亮控制（`static/js/theme.js`），与皮肤是两个独立的轴；皮肤内部若自带明暗，以皮肤为准。首帧底色按页面写在 `html` 的 `data-boot-bg-light/dark` 上，由 `<head>` 里一段 `:where()` 内联 CSS 直接画到 html/body（优先级 0，外链样式表到达后自动接管）；切主题只改 `data-theme`，属性选择器随之换色，JS 不再写 inline 底色，三层底色始终一致。

皮肤名按设计语言起，不沿用原产物里写着的名字（那些是模型名，不是样式名）：
`观象台` 来自 `KALMIA衡天量级体系.zip`（夜观 / 昼测 / 衡天仪），
`月面` 来自 `opus-5.5-high御兔量级页面.zip`（月面卷宗、兔子、印章）。

`观象台` 的原产物自带五个 `woff2` 子集字体，但 ZIP 里没有 `assets/fonts/` 目录，
缺字体时整页会退成方框。所以它在 `data/editions.json` 里标了 `"font_rewrite": true`：
构建时把 `HT Sans / HT Serif / HT Brush / HT Mono` 四个族改指站内自托管的
思源黑体 / 思源宋体 / Space Grotesk，并去掉指向缺失文件的 `@font-face`。
新增同类产物时记得加这个开关。

`月面` 的字体是**按正文用字裁过的子集**，打包在页面里、不缺字表里没有的字 ——
缺字时不是画方框而是直接留白。所以凡是我们自己往这页加的文字（站内导航、
皮肤切换器）都必须显式换成站内自托管字体，不能跟着 `--font-*` 变量走。

整页产物原本是「单向门」：进去以后没有任何回主站的入口。
`skins/patches/observatory.js` 因此往侧栏（`aside.rail` 的 `.rail-sticky`，插在
「目录 · CONTENTS」标题之前）和移动端抽屉（`.drawer-scroll` 顶部）各挂一组
「站内其他栏目」链接；`skins/patches/moonfile.js` 同样挂在它的 `nav.sticky`
（桌面目录）和汉堡抽屉里。把量级分类 / 角色档案 / 规则原文 / 材质数据库 / 首页连回去。
React 侧的壳在 `DOMContentLoaded` 之后才挂载，所以挂载用定时重试 + `MutationObserver`，
不是一次 `querySelector` 就完事。

### 只给单个页面挂皮肤

`pages` 里的键不一定是栏目名，也可以是单页（例如 `character-yutu`）。
构建器把它当 `skin_section` 传给 `render_shell()`，于是只在那一个页面上出现皮肤切换器：

```json
"pages": { "character-yutu": "skins/moonfile/character-yutu.html" }
```

默认皮肤也登记了同一个键（指回 `character/yutu.html`），两边互相跳得回去。
新增角色单页皮肤时，记得在默认皮肤那条里也补一个同名键。

### 新增一套皮肤

1. 把整页 HTML 放进 `skins/_source/`（自包含最好：字体、图片内联或相对路径）；
2. `data/editions.json` 的 `editions[]` 加一条：

```json
{
  "id": "archive",
  "name": "卷宗",
  "tag": "ARCHIVE",
  "note": "米纸底、左侧索引栏、细线分隔与衬线巨标题的档案排版",
  "source": "skins/_source/archive.html",
  "section": "materials",
  "thumb": "static/img/editions/archive.jpg",
  "patch": "skins/patches/archive.js",
  "pages": { "materials": "skins/archive/materials.html" }
}
```

3. `python3 build_site.py` —— 生成器会把 HTML 复制到 `skins/<id>/<section>.html`，并在 `</body>` 前注入切换器和它的 CSS/JS；主站所有页面也会自动挂上切换器；
4. 截一张缩略图存到 `static/img/editions/<id>.jpg`（16:10 裁切、宽 640）。

`pages` 里没有登记的栏目，这套皮肤就不会出现在那一栏的切换器里（不会把用户带去别的页面）。

### 产物补丁（`patch`）

产物是别人的整页设计，偶尔有"按单页生成、但按多页站点写的"部件。`patch` 指向一个小脚本，在注入时跟在切换器后面加载，只做结构调整，不改产物本体：

- `skins/patches/archive.js` —— 把 12 条「上一章 / 下一章」翻页条换成「章节分隔 + 01/12 进度 + 章节目录」；整页是连续滚动，翻页跳锚点没有意义。顺带把左下角切换器抬到该页固定工具栏之上。

### 实现要点

- 注入是纯字符串替换，产物本身不被改写，只多一个 `<link>`、一段切换器 HTML 和一个 `<script>`；两边都不依赖框架。
- 跳转是普通 `<a href>`，JS 失效也能换皮肤；JS 只负责开合、Esc / 外点关闭。
- 相对链接按"页面在仓库里的层深"计算，所以同一条脚本能同时服务根目录页、`tier/`、`character/` 和 `skins/<id>/`。

## 性能与资源（实测）

原则：只做"不减少任何效果"的优化，每一条都用同一脚本前后对比过；没有实测收益的不写进 CSS。

| 项目 | 之前 | 现在 | 做法 |
| --- | --- | --- | --- |
| 量级页首屏图片请求 | 4176 KB（33 张原图） | 415 KB（35 张卡片版） | 卡片配图改用 `static/img/tiers/card/*.webp`（560px 宽），并用 `<img loading="lazy">`；原图仍留给详情页页头 |
| 规则页首屏总流量 | 4363 KB | 3974 KB | 索引包（404 KB）改为按需加载 |
| 非检索页面 | 每页都拉 404 KB 索引 | 打开检索时才加载 | `<head>` 里只写 `window.__PW_INDEX_SRC__`，首次 Ctrl+K 时注入脚本 |
| 星图页滚动 | 每步 114ms | 每步 62ms | 极光层（2000×1300 位移动画）交给合成器：`will-change/translateZ/contain` |

试过但没有收益、**已回退**的方案（避免以后有人再踩）：

- `.tier-card { content-visibility: auto }` —— 本机软件渲染下帧时无变化，等于白加一层复杂度。
- 卷宗页整屏网格纹理加 `will-change/transform` —— 反而慢 30%，全屏层交给合成器要重栅格化。
- 侧栏渐变背景提升为合成层 —— 无收益。
- 去掉全局 blur/mix-blend 效果 —— 有收益但会改变外观，按"不减少效果"的要求放弃。

## 皮肤切换器（角落印章）

- 默认是 30px 的 ⊙ 圆点、62% 不透明度；hover / 聚焦才展开成「⊙ 皮肤」。
- 滚动时淡到 14%，停下 600ms 恢复，不遮挡正文。
- 点开是一整块面板：缩略图 + 名称 + 「当前」标记 + 「返回主站首页」。上方放不下时自动改为向下弹。
- **避让是逐块求交，不是估算**：`editions.js` 每次定位都枚举页面上所有可见的 `position: fixed` 块
  （阅读工具条 `.reader-rail`、工具坞 `.floating-dock`、皮肤自带的 `.mobile-dock`、卷宗页的 `.rail`…），
  逐个和印章的横向区间求交，把印章压到真正空着的那一格里；左侧有整条侧栏时整组翻到右侧。
  贴右边时用 `right` 锚定，展开标签只会往左长，不会顶出屏幕。
- 手机（≤560px）默认贴右下角，和工具坞排成一列，左下角整块留给阅读工具条。
- 深色主题下面板与按钮跟着变暗。
- 只在"这一栏目真有对应页面"的皮肤之间出现；不足两套就不挂。

验证脚本：`qa2/overlap.js`（在 390 / 768 / 1440 三档宽度下枚举固定元素并两两求交，必须打印 `TOTAL OVERLAPS: 0`）。

## 修掉的排版 bug（2026-11-02）

- **卷宗皮肤「空了一大块」**：`.hero-footnote` 在 ≤420px 变成 `14px minmax(0,1fr)` 两列网格，
  但脚注有 4 个 span，第 4 个（「全文逐字收录 · 未删改原文」）自动落进 14px 那一列，
  被挤成一字一行、撑出 220px 高的空白。现在第 4 段 `grid-column: 1 / -1` 横跨整行。
- **皮肤页顶栏发糊**：原始页面只写了 `-webkit-backdrop-filter`，Chrome 里标准属性缺失，
  顶栏只剩 68% 底色，正文从条里透出来。`polish.css` 给 `html[data-pw-edition] .topbar` 补回标准写法。
- **滚动进入会锁在透明态**：之前用 `animation-timeline: view()`，整页截图 / 打印时卡片停在 opacity 0。
  改成 `IntersectionObserver` 加 `.pw-in` 类（`chrome.js`），元素一旦出现就不再隐藏。
- 验证脚本：`qa2/vscan.js`（逐屏截图统计空白行占比，≥62% 视为异常屏）、`qa2/vert.js`（找被挤成竖排的文字）、
  `qa2/overlap.js`（固定元素两两求交，必须 `TOTAL OVERLAPS: 0`）。

## 修掉的排版 bug（2026-11-04）

- **印章压在侧栏目录上**：`editions.js` 的避让定位原来只量 `position: fixed` 的障碍，
  而整页产物的侧栏是 `position: sticky` 的，于是印章一路贴回左下角、盖住目录最后几行。
  现在 sticky 也算障碍，并且「尚未滚进视口的 sticky 侧栏」也记一笔，滚动停下后再量一次。
  侧栏的判定从「必须贴屏幕边缘」放宽到「靠边 8% 以内且够高够宽」，皮肤自带页边距时也认。
- **月面皮肤的导航缺字**：那套页面的字体是按正文用字裁的子集，缺字时留白不画框，
  站内导航直接少了几个字。导航与切换器一律改用站内自托管的思源黑体。

## 界面打磨（2026-11-02）

- **悬浮层地板线**：`chrome.js` 实测页面底部的整条固定栏，写进 `--pw-floor`；阅读工具条、工具坞、
  正文留白统一踩这条线，互不压边。
- **正文标题去重**：构建时把 Markdown 第一行的大标题收进页头（`id` 搬到 `codex-folio-title`），
  目录第一条照样能跳，正文不再重复一次同名大标题。
- **出处行瘦身**：`衡天档案` 这种只有一句的 `.doc-toolbar` 整条隐藏；角色页保留带依据说明的那行。
- **排版**：标题 `text-wrap: balance`、正文 `text-wrap: pretty` + 中文标点悬挂；小屏文档大标题降一档；
  分割线间距收紧。
- **筛选条**：横向滚动条隐藏，滑得动的一侧加渐隐（`chrome.js` 按 `scrollLeft` 切换 `can-left/right`），
  滑到头自动收掉。
- **细节**：标签压在详情页大图上时补一层磨砂底；浅色主题压深分组色；输入框不再叠两层焦点圈；
  统一 hover 抬升与按压反馈；键盘焦点环只在键盘操作时出现。
- **滚动进入**：`animation-timeline: view()` 驱动卡片淡入上浮（只动 `opacity`/`translate`，
  不影响 hover 的 `transform`；`prefers-reduced-motion` 下关闭）。
- **不做任何整屏入场动效**：既不做原生 cross-document 全屏交叉淡入（新旧快照淡化会露出白底，见需求 #6 与 `8507c08`），也**不再做 `main` 的 opacity 淡入**。后者每次加载都让整屏先暗一下再亮起来，其 transform 还会把 `position:fixed` 的悬浮控件锁进 `main` 的包含块——这是「御兔页反复闪屏」一直没修干净的根因。现在首帧即终态；主题切换的短过渡仍由 `html.theme-transitioning` 提供（用户主动触发）。
- **首屏加载**：两个中文可变字体 CSS（各约 99 KB，只含 `@font-face`、全带 `font-display: swap`）改为非阻塞加载，把阻塞首次绘制的样式表从 469 KB 降到约 271 KB；站点 CSS 仍保持阻塞，保证布局不闪。
