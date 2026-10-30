# 衡天⊙ PowerWiki（v9.1）

以《衡天⊙ 多维战力量级体系（第五版）》和《材质与破坏能量数据库（第二版）》为基准的静态战力量级百科。

## 页面

- `index.html`：精简首页，集中提供量级、角色、规则三类入口。
- `tiers.html`：98 个连续量级，支持卡片、天梯、总表三种视图及区间筛选。
- `characters.html`：角色目录；少量角色使用轻量布局，角色增多后自动启用完整筛选。
- `rules.html`：第五版体系全文，含目录、页内查找、字号与宽屏设置。
- `materials.html`：材质与破坏能量全文。
- `search.html`：全站检索；其他页面可按 `Ctrl + K` 或 `/` 唤起搜索。
- `tier/*.html`、`character/*.html`：自动生成的独立详情页。
- 窄屏下章节抽屉从右下角工具坞打开，带独立关闭按钮、遮罩层与「全站导航」出口；按 `Esc` 或点遮罩即可关闭。

全站采用统一的档案式编辑设计，提供完整的亮色与暗色模式，适配桌面与手机。御兔使用月白／午夜两套页面级月面轨道主题，弗坦使用雾绿／黑金两套页面级深渊主题；背景、导航、目录、正文、表格、阅读工具、搜索与页脚均随角色模式协调变化。角色正文提供主题化阅读进度、章节编号与测量图版，搜索摘要经过可读性清理；两者的形象原图、完整证据与阅读工具均保留。中文 Noto Sans SC、Noto Serif SC 和英文 Space Grotesk 可变字体随站本地提供，不依赖外部字体 CDN。生成页面使用相对路径，可直接部署到 GitHub Pages 等静态托管服务。

## 当前内容（2026-10-25）

- **规则**：`data/docs/衡天量级体系【第五版·最新】.md`。
- **御兔**：`data/docs/characters/御兔（非人学园）衡天定级.md`；官方立绘与两张测量图保持不变。
- **弗坦**：`data/docs/characters/弗坦（诡秘地海）衡天定级（新）.md`；使用横向克苏鲁风格形象参考壁纸。
- **材质**：`data/docs/材质与破坏能量数据库（新）.md`。

第五版不改变既有量级刻度和能量数值，因此保留现有 98 档结构化数据，仅更新规则原文、证据规范与全站版本标识。

## 数据与构建

主要输入：

```text
data/
├── characters.json        # 角色元数据、视觉主题、图片映射与摘要
├── tier-art-tuning.json   # 98 张档位配图的取景重心与浓淡补偿（按图实测，缺失时回落 CSS 默认值）
├── tiers.json             # 量级和分组定义
├── skins.json             # 外观皮肤登记表（id / 名称 / 色卡 / theme-color）
└── docs/                  # 完整 Markdown 原文
static/
├── css/style.css          # 功能样式与基础设计系统
├── css/editorial.css      # 全站外壳与角色明暗设计
├── css/experience.css     # 阅读工具栏与档位配图等体验层样式
├── css/skins.css          # 外观皮肤：每套皮肤一组变量覆盖（含落地清单）
├── fonts/                 # 本地可变字体与 SIL OFL 许可证
├── js/app.js              # 筛选、搜索、目录与阅读工具
└── img/                   # 本地图片与角色主题美术（`img/tiers/<slug>.jpg` 为每档独立配图，16:9；缺图时回落同名分组图）
```

修改数据或文档后，在仓库根目录执行：

```bash
python3 build_site.py
```

生成器仅使用 Python 3 标准库，会重新生成所有静态页面及 `static/js/search-index.js`。`pelican.html` 是独立的单文件动画，不参与主站构建。

## 外观皮肤（`data-skin` 轴）

明暗与皮肤是两个正交的轴，互不干扰：

| 轴 | 属性 | 入口 | 持久化 |
| --- | --- | --- | --- |
| 明暗 | `html[data-theme="light\|dark"]` | 右上角太阳 / 月亮 | `pw_theme_v2` |
| 皮肤 | `html[data-skin="<id>"]` | 右上角调色板（明暗按钮左侧） | `pw_skin_v1` |

- 首屏脚本在 `<head>` 内按 `?skin=` → `localStorage` → 默认值 的顺序定皮肤，先于样式生效，不会闪。
- 皮肤全部写在 `static/css/skins.css`，按 `html[data-skin="<id>"]` 与 `html[data-skin="<id>"][data-theme="dark"]` 两组变量覆盖；选择器优先级高于 `[data-theme]`，且文件排在 `style/editorial/experience` 之后。
- 现有三套：`default`（v6.0 原设计，不覆盖任何变量）、`paper`（纸本）、`blueprint`（蓝图）。后两套是验证机制的样例，可随时替换。

新增一套皮肤：

1. `data/skins.json` 的 `skins[]` 加一条 `{id, name, note, swatch, theme_color}`；
2. `static/css/skins.css` 末尾按"落地清单"补 light / dark 两组变量（清单见该文件顶部注释，重点是 `--hero-fade-*` 这类烘焙了底色的派生变量）；
3. `python3 build_site.py` —— 按钮列表、`theme-color` 映射、首屏脚本全部自动生成；
4. 回归：首页 / 量级 / 角色档案 / 角色页 / 规则 / 材质 / 390 宽各截一张。

已知边界：弗坦、御兔的角色页带有各自专属的配色层（`body.character-*`），皮肤只接管外壳（导航、面包屑、按钮、页脚），正文区保留角色自己的明暗语言。
