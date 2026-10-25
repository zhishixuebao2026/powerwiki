# 衡天⊙ PowerWiki（v7.0）

以《衡天⊙ 多维战力量级体系（第五版）》和《材质与破坏能量数据库（第二版）》为基准的静态战力量级百科。

## 页面

- `index.html`：精简首页，集中提供量级、角色、规则三类入口。
- `tiers.html`：98 个连续量级，支持卡片、天梯、总表三种视图及区间筛选。
- `characters.html`：角色目录；少量角色使用轻量布局，角色增多后自动启用完整筛选。
- `rules.html`：第五版体系全文，含目录、页内查找、字号与宽屏设置。
- `materials.html`：材质与破坏能量全文。
- `search.html`：全站检索；其他页面可按 `Ctrl + K` 或 `/` 唤起搜索。
- `tier/*.html`、`character/*.html`：自动生成的独立详情页。

全站采用浅色阅读界面，保留暗色模式，适配桌面与手机。生成页面使用相对路径，可直接部署到 GitHub Pages 等静态托管服务。

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
├── characters.json        # 角色元数据、图片映射与摘要
├── tiers.json             # 量级和分组定义
└── docs/                  # 完整 Markdown 原文
static/
├── css/style.css          # 全站样式与 v7 阅读界面
├── js/app.js              # 筛选、搜索、目录与阅读工具
└── img/                   # 本地图片
```

修改数据或文档后，在仓库根目录执行：

```bash
python3 build_site.py
```

生成器仅使用 Python 3 标准库，会重新生成所有静态页面及 `static/js/search-index.js`。`pelican.html` 是独立的单文件动画，不参与主站构建。
