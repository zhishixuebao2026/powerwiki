# AGENTS.md — PowerWiki 维护速查

> 给 agent 看的。动手前先读 `docs/需求与约定.md`（18 条硬性要求）和 `CHANGELOG.md` 最近几条。
> 本文件只放"每次都会用到、又容易忘"的操作要点与踩过的坑。

## 站点与在线

- 项目根目录：`/workspace/powerwiki`。静态站，`python3 build_site.py` 构建。
- **两个在线入口都可用**（实测均 200）：
  - GitHub Pages（公开、免 sharecode，推荐）：`https://zhishixuebao2026.github.io/powerwiki/`，
    子路径直接拼域名后（如 `/skins/<id>/character-<x>.html`）。Pages 由 `main` 分支 `/` 自动构建，
    状态可在 GitHub API `GET /repos/zhishixuebao2026/powerwiki/pages` 查（`status: built`）。
  - WorkBuddy 固定链接：`https://afecd13252576622f.app.workbuddy.host/?sharecode=ATAMOUH2UX`，
    子路径拼在域名后并带 `?sharecode=ATAMOUH2UX`。
  早期 Pages 未部署完曾 404，现已正常；验收时两个都测，别再当成"非当前入口"。
- 推送：`TOKEN=$(curl -s "http://github.agent-gateway.auth-proxy.local/_internal/accesstoken?refresh=1" | python3 -c "import sys,json;print(json.load(sys.stdin)['data']['access_token'])")`
  然后 `git push "https://x-access-token:${TOKEN}@github.com/zhishixuebao2026/powerwiki.git" main`。
  **网关发的 token 会轮换**：普通 `accesstoken`（不带 `?refresh=1`）常返回已失效的旧值，导致
  `Invalid username or token`。推送失败先加 `?refresh=1` 换新 token，不要怀疑连接器没连、也不要让用户去重连。

## 皮肤接入 SOP（整页整页接，不是换色）

1. **先找真正的构建产物**，别急着自己 build：
   - 常见入口 `dist/index.html`；**也可能叫别的名字**（如许青那套是 `dist/打开文库.html`）。
   - 判断成品的特征：单文件几百 KB~几 MB、含 `data:image` base64 图 / 内联 JS bundle。
   - **只有当 dist 里确实没有成品、根目录 `index.html` 又引用 `/src/main.tsx` 等源码路径时**，
     才需要 `npm install && npm run build`。构建前先看 `package.json` 的 `scripts.build`。
   - 教训：许青那套 dist 里是「打开文库.html」不是 index.html，我曾误判为未构建、白跑一次 npm build
     （产物 md5 一致、结果没错，但绕了远路）。**先看全 dist 目录再判断**。
2. **核验定级一致性**：从成品页提取综合量级文本，和 `tools/grading_baseline.json` / `data/characters.json`
   的 `tier_slug` 对照。定级正文一律不动，只接皮肤。
3. **三处联动**：
   - `skins/_source/<id>.html` ← 成品单页原样放（缺 `env(safe-area-inset-top)` 才补标准安全区样式）；
   - `data/editions.json` 登记一条：`id/name/tag/note/source/section/inject/thumb/pages`；
     `inject` 用 `minimal`（整页 React 应用，只注入切换器浮层）；
   - 产物目录 `skins/<id>/` 由 `build_site.py` 自动生成，dist 的资源目录（fonts/images/document/source）随附过去。
   - `build_site.py` 的 `SKIN_STATUS_BAR_MODE` 加一项：暗色首页 `black`，亮色 `default`。
4. **缩略图**：`static/img/editions/<id>.jpg`，640×400，从首屏截图按 `crop_ratio(im, 640/400, cx=.5, cy=.42)` 裁切。
5. **命名**（用户反复强调，见下）：走意象、古雅、贴合皮肤视觉；**不要堆"颜色+名词"**（如"深蓝补天""黑金浑天仪"被骂土）；
   也不要清一色两字古风词（"全是两个字，别重复了"）。长短错落、有典故出处最佳。
6. **收尾**：递增 `service-worker.js` 的 `pw-vNN`；`python3 build_site.py`；
   `python3 tools/audit_site.py` 必须全过（切换器卡片/缩略图 0 缺、定级基线 0 异常）；
   浏览器实测所有相关页（皮肤页+默认页）切换器/破图/JS 错误；更新 CHANGELOG；提交推送。

## 切换器怎么切皮肤

- 切换器显示名**只读 `data/editions.json` 的 `name` 字段**（`build_site.py` 的 `edition_launcher_html` 写入卡片）。
  改显示名只需改 `name` 再重建；皮肤 HTML 内部的"玄穹"之类是主题词，不是标签，别误改。
- 切换器按 `pages` 登记的 section 出现：`pages: {"character-zhangyan": "skins/.../character-zhangyan.html"}`。
  同一 section 登记 ≥2 套才显示切换器。默认页由构建自动注入 dock。
- 新增套数 = editions.json 条数 - 1（default）。产物套数 = 皮肤数。
