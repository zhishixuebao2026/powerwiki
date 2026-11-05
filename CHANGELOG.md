# 更新记录

按天记录做了什么、为什么做。条目对应分支 `arena/7ea6b694-powerwiki` 上的提交，
`(abc1234)` 是提交短哈希，可以直接 `git show` 看细节。
皮肤的设计取舍写在 `README.md`，用户的硬性要求与验收方式写在 `docs/需求与约定.md`。

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
