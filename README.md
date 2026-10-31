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
├── editions.json          # 页面皮肤登记表（id / 名称 / 缩略图 / 各栏目页面路径）
└── docs/                  # 完整 Markdown 原文
static/
├── css/style.css          # 功能样式与基础设计系统
├── css/editorial.css      # 全站外壳与角色明暗设计
├── css/experience.css     # 阅读工具栏与档位配图等体验层样式
├── css/editions.css       # 左下角皮肤切换器的样式
├── fonts/                 # 本地可变字体与 SIL OFL 许可证
├── js/app.js              # 筛选、搜索、目录与阅读工具
└── img/                   # 本地图片与角色主题美术（`img/tiers/<slug>.jpg` 为每档独立配图，16:9；缺图时回落同名分组图）
```

修改数据或文档后，在仓库根目录执行：

```bash
python3 build_site.py
```

生成器仅使用 Python 3 标准库，会重新生成所有静态页面及 `static/js/search-index.js`。`pelican.html` 是独立的单文件动画，不参与主站构建。

## 页面皮肤（整页换设计）

一套皮肤 = 一份完整的整页设计。左下角的「⊙ 皮肤」印章可以在它们之间跳转，每张卡片带缩略图、名称和"当前"标记。

| id | 名称 | 来源 | 覆盖页面 |
| --- | --- | --- | --- |
| `default` | 默认 | 本仓库生成器（`build_site.py`） | 全站：首页 / 98 档量级 / 角色 / 规则 / 材质 |
| `vol` | 卷宗 | `skins/_source/vol.html`（Arena 产物，整页自包含） | 材质页 |
| `poster` | 图鉴 | `skins/_source/poster.html`（Arena 产物，整页自包含） | 材质页 |

明暗仍由右上角的太阳 / 月亮控制，与皮肤是两个独立的轴；皮肤内部若自带明暗，以皮肤为准。

### 新增一套皮肤

1. 把整页 HTML 放进 `skins/_source/`（自包含最好：字体、图片内联或相对路径）；
2. `data/editions.json` 的 `editions[]` 加一条：

```json
{
  "id": "poster",
  "name": "图鉴",
  "tag": "POSTER · ATLAS",
  "note": "巨字标题、球形主视觉、浮动卡片的海报排版",
  "source": "skins/_source/poster.html",
  "section": "materials",
  "thumb": "static/img/editions/poster.jpg",
  "pages": { "materials": "skins/poster/materials.html" }
}
```

3. `python3 build_site.py` —— 生成器会把 HTML 复制到 `skins/<id>/<section>.html`，并在 `</body>` 前注入切换器和它的 CSS/JS；主站所有页面也会自动挂上切换器；
4. 截一张缩略图存到 `static/img/editions/<id>.jpg`（16:10 裁切、宽 640）。

`pages` 里没有登记的栏目，切换器会退回到该皮肤的第一个页面，并标注「仅 xx 页」——目前两份 Arena 产物只有材质页，所以从首页点进去会落到材质页。

### 实现要点

- 注入是纯字符串替换，产物本身不被改写，只多一个 `<link>`、一段切换器 HTML 和一个 `<script>`；两边都不依赖框架。
- 跳转是普通 `<a href>`，JS 失效也能换皮肤；JS 只负责开合、Esc / 外点关闭。
- 相对链接按"页面在仓库里的层深"计算，所以同一条脚本能同时服务根目录页、`tier/`、`character/` 和 `skins/<id>/`。
