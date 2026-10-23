#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Generator (Zero External Dependencies)
Generates pure relative-path HTML5 pages compatible with:
  - raw.githack.com/<owner>/<repo>/<commit_or_branch>/index.html
  - GitHub Pages (/<repo>/)
  - Local HTTP preview servers & offline file://
"""

import html
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"

CN_NUM_MAP = {
    "零": 0,
    "一": 1,
    "二": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "十一": 11,
    "十二": 12,
}


def make_heading_id(text: str, seen: set, doc_prefix: str = "sec") -> str:
    clean = text.strip()
    # Match "第X部分"
    m_part = re.match(r"^第([零一二三四五六七八九十百]+)部分", clean)
    if m_part:
        cn = m_part.group(1)
        num = CN_NUM_MAP.get(cn, cn)
        base = f"part-{num}"
    else:
        # Match numeric section like "2.1 ..." or "4.1.2 ..."
        m_sec = re.match(r"^(\d+(?:\.\d+)+)", clean)
        if m_sec:
            nums = m_sec.group(1).replace(".", "-")
            base = f"sec-{nums}"
        elif clean.startswith("附：") or clean.startswith("附录"):
            base = "appendix"
        elif clean.startswith("参考来源"):
            base = "references"
        elif clean.startswith("待补充事项"):
            base = "todo-items"
        else:
            slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", clean).strip("-").lower()
            base = f"{doc_prefix}-{slug[:28]}" if slug else f"{doc_prefix}-h"

    candidate = base
    idx = 2
    while candidate in seen:
        candidate = f"{base}-{idx}"
        idx += 1
    seen.add(candidate)
    return candidate


def format_inline_md(raw_text: str, doc_kind: str = "") -> str:
    """
    Convert Markdown inline syntax to HTML while strictly preserving:
      - Mathematical underscores: f_ω, f_{ω+1}, ℶ_κ, K_IC, V_λ→V_λ (NO _italic_ mangling!)
      - Escaped asterisks: F\\* -> F*
      - Inline code spans: `...`
      - Bold spans: **...**
      - Evidence tags: 〔实〕 〔下〕 〔推〕 〔隐〕 〔缺〕
      - Cross-document book references
    """
    code_store = []

    def save_code(match):
        idx = len(code_store)
        inner = html.escape(match.group(1))
        code_store.append(f"<code>{inner}</code>")
        return f"\x00CODE{idx}\x00"

    # 1. Protect inline backtick code spans
    s = re.sub(r"`([^`]+)`", save_code, raw_text)

    # 2. Protect escaped characters (\* \| \\)
    s = s.replace(r"\*", "\x00AST\x00").replace(r"\|", "\x00PIPE\x00")

    # 3. HTML escape remaining text
    s = html.escape(s)

    # 4. Bold (**...**)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)

    # 5. Markdown links [label](url) if any exist
    s = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        s,
    )

    # 6. Highlight canonical evidence status tags
    s = (
        s.replace("〔实〕", '<span class="ev-badge ev-confirmed">〔实〕</span>')
        .replace("〔下〕", '<span class="ev-badge ev-lower">〔下〕</span>')
        .replace("〔推〕", '<span class="ev-badge ev-inferred">〔推〕</span>')
        .replace("〔隐〕", '<span class="ev-badge ev-hidden">〔隐〕</span>')
        .replace("〔缺〕", '<span class="ev-badge ev-missing">〔缺〕</span>')
    )

    # 7. Cross-document smart reference links
    if doc_kind == "rules":
        s = s.replace(
            "《材质与破坏能量数据库》",
            '<a class="xref-link" href="./materials.html" title="点击跳转至《材质与破坏能量数据库（第二版）》全文">《材质与破坏能量数据库》↗</a>',
        )
    elif doc_kind == "materials":
        s = s.replace(
            "《衡天⊙ 多维战力量级体系》",
            '<a class="xref-link" href="./rules.html" title="点击跳转至《衡天⊙ 多维战力量级体系（第二版）》全文">《衡天⊙ 多维战力量级体系》↗</a>',
        )

    # 8. Restore escaped literals & code spans
    s = s.replace("\x00AST\x00", "*").replace("\x00PIPE\x00", "|")
    for idx, code_html in enumerate(code_store):
        s = s.replace(f"\x00CODE{idx}\x00", code_html)

    return s


def split_md_table_row(line: str) -> list:
    """Split a Markdown table row on unescaped | outside inline `code`."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith(r"\|"):
        s = s[:-1]

    cells = []
    cur = []
    in_code = False
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "`":
            in_code = not in_code
            cur.append(ch)
        elif ch == "\\" and i + 1 < len(s) and s[i + 1] == "|":
            cur.append(r"\|")
            i += 1
        elif ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def is_table_separator(line: str) -> bool:
    s = line.strip()
    if not s.startswith("|"):
        return False
    cells = split_md_table_row(s)
    return len(cells) >= 1 and all(re.match(r"^:?-{2,}:?$", c.replace(" ", "")) for c in cells)


def parse_markdown_document(md_text: str, doc_kind: str, doc_url: str):
    """
    Full-fidelity block & inline parser for canonical Markdown documents.
    Returns:
      - html_str: Complete rendered HTML
      - toc: List of { id, level, text }
      - search_sections: List of { type, title, url, text, code, pinyin }
    """
    lines = md_text.splitlines()
    n = len(lines)
    i = 0

    out = []
    toc = []
    seen_ids = set()

    sections = []
    cur_section = {
        "id": "doc-top",
        "title": "总览",
        "lines": [],
    }

    def flush_section():
        plain = " ".join(cur_section["lines"]).strip()
        plain = re.sub(r"[#*`|>-]+", " ", plain)
        plain = re.sub(r"\s+", " ", plain).strip()
        if plain:
            anchor = f"#{cur_section['id']}" if cur_section["id"] != "doc-top" else ""
            sections.append(
                {
                    "type": doc_kind,
                    "title": cur_section["title"],
                    "url": f"{doc_url}{anchor}",
                    "text": plain,
                    "code": "",
                    "pinyin": "",
                }
            )

    doc_title_seen = False

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if re.match(r"^-{3,}\s*$", stripped):
            out.append("<hr>")
            i += 1
            continue

        # Headings (#, ##, ###)
        m_h = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m_h:
            hashes, raw_h_text = m_h.group(1), m_h.group(2).strip()
            level = len(hashes)

            # First H1 is the document's main title
            if level == 1 and not doc_title_seen:
                doc_title_seen = True
                h_id = "doc-top"
                seen_ids.add(h_id)
                cur_section["title"] = raw_h_text
                cur_section["id"] = h_id
                out.append(
                    f'<h1 id="{h_id}" class="doc-main-h1">{format_inline_md(raw_h_text, doc_kind)}'
                    f'<a class="heading-anchor" href="#{h_id}" data-target-id="{h_id}" title="复制章节链接">#</a></h1>'
                )
                i += 1
                continue

            flush_section()
            h_id = make_heading_id(raw_h_text, seen_ids, doc_kind)
            cur_section = {"id": h_id, "title": raw_h_text, "lines": []}

            plain_toc = raw_h_text.replace("**", "").replace(r"\*", "*")
            toc.append({"id": h_id, "level": level, "text": plain_toc})

            tag = f"h{min(level, 4)}"
            out.append(
                f'<{tag} id="{h_id}">{format_inline_md(raw_h_text, doc_kind)}'
                f'<a class="heading-anchor" href="#{h_id}" data-target-id="{h_id}" title="复制本节链接">#</a></{tag}>'
            )
            i += 1
            continue

        # Markdown Table
        if stripped.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]):
            headers = split_md_table_row(lines[i])
            cur_section["lines"].append(" ".join(headers))
            i += 2  # skip header + separator
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                row_cells = split_md_table_row(lines[i])
                cur_section["lines"].append(" ".join(row_cells))
                rows.append(row_cells)
                i += 1

            col_count = len(headers)
            th_html = "".join(f"<th>{format_inline_md(c, doc_kind)}</th>" for c in headers)
            tbody_rows = []
            for r in rows:
                padded = r + [""] * max(0, col_count - len(r))
                tds = "".join(f"<td>{format_inline_md(c, doc_kind)}</td>" for c in padded[:col_count])
                tbody_rows.append(f"<tr>{tds}</tr>")
            out.append(
                f'<div class="table-scroll"><table><thead><tr>{th_html}</tr></thead>'
                f'<tbody>{"".join(tbody_rows)}</tbody></table></div>'
            )
            continue

        # Blockquote (> ...)
        if stripped.startswith(">"):
            bq_paras = []
            cur_p = []
            while i < n and lines[i].strip().startswith(">"):
                content = re.sub(r"^>\s?", "", lines[i].strip())
                cur_section["lines"].append(content)
                if not content:
                    if cur_p:
                        bq_paras.append(" ".join(cur_p))
                        cur_p = []
                else:
                    cur_p.append(content)
                i += 1
            if cur_p:
                bq_paras.append(" ".join(cur_p))
            inner_html = "".join(f"<p>{format_inline_md(p, doc_kind)}</p>" for p in bq_paras)
            out.append(f"<blockquote>{inner_html}</blockquote>")
            continue

        # Unordered list (- ...)
        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                item_txt = re.sub(r"^-\s+", "", lines[i].strip())
                cur_section["lines"].append(item_txt)
                items.append(f"<li>{format_inline_md(item_txt, doc_kind)}</li>")
                i += 1
            out.append(f'<ul>{"".join(items)}</ul>')
            continue

        # Ordered list (1. ...)
        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                item_txt = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                cur_section["lines"].append(item_txt)
                items.append(f"<li>{format_inline_md(item_txt, doc_kind)}</li>")
                i += 1
            out.append(f'<ol>{"".join(items)}</ol>')
            continue

        # Regular paragraph (merge consecutive non-special lines)
        para_lines = []
        while i < n:
            ln = lines[i].strip()
            if (
                not ln
                or re.match(r"^(#{1,4})\s+", ln)
                or re.match(r"^-{3,}\s*$", ln)
                or ln.startswith(">")
                or re.match(r"^-\s+", ln)
                or re.match(r"^\d+\.\s+", ln)
                or (ln.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]))
            ):
                break
            cur_section["lines"].append(ln)
            para_lines.append(ln)
            i += 1

        para_joined = "<br>".join(format_inline_md(pl, doc_kind) for pl in para_lines)
        out.append(f"<p>{para_joined}</p>")

    flush_section()
    return "\n".join(out), toc, sections


def render_shell(
    *,
    title: str,
    page_id: str,
    page_type: str,
    active_nav: str,
    root_prefix: str,
    body_html: str,
    context_bar_html: str = "",
    has_toc_drawer: bool = False,
    tier_count: int = 97,
    char_count: int = 0,
) -> str:
    r = root_prefix  # "./" or "../"

    def nav_cls(key):
        return "nav-link active" if active_nav == key else "nav-link"

    toc_dock_btn = (
        '<button type="button" class="dock-btn dock-toc-btn" id="dock-toc-btn" title="展开/收起章节目录">☰</button>'
        if has_toc_drawer
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark" data-root="{r}" data-page-id="{html.escape(page_id)}" data-page-type="{html.escape(page_type)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} · 衡天⊙ PowerWiki</title>
  <meta name="description" content="衡天⊙ 多维战力量级体系（第二版）与材质破坏能量数据库官方百科站——支持角色与量级按首字母及从小到大排序、全文检索与阅读进度保存。">
  <script>
    (function() {{
      try {{
        var t = localStorage.getItem('pw_theme_v2');
        if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
      }} catch (e) {{}}
    }})();
  </script>
  <link rel="stylesheet" href="{r}static/css/style.css">
</head>
<body>
  <div class="reading-progress-track" aria-hidden="true">
    <div class="reading-progress-bar" id="reading-progress-bar"></div>
  </div>

  <header class="site-header">
    <div class="container header-inner">
      <a class="brand" href="{r}index.html">
        <span class="brand-mark mono" aria-hidden="true">⊙</span>
        <span class="brand-text">
          <span class="brand-title">衡天 PowerWiki <span class="brand-badge">v2.0</span></span>
          <span class="brand-sub">多维战力量级 · 材质破坏能量参考系</span>
        </span>
      </a>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        <a class="{nav_cls('home')}" href="{r}index.html">首页</a>
        <a class="{nav_cls('tiers')}" href="{r}tiers.html">量级分类 <span class="nav-count mono">{tier_count}</span></a>
        <a class="{nav_cls('chars')}" href="{r}characters.html">角色档案 <span class="nav-count mono">{char_count}</span></a>
        <a class="{nav_cls('rules')}" href="{r}rules.html">衡天体系全文</a>
        <a class="{nav_cls('materials')}" href="{r}materials.html">材质能量全文</a>
      </nav>

      <div class="header-actions">
        <button type="button" class="search-trigger" id="global-search-trigger" aria-label="打开全站搜索">
          <span class="search-trigger-left">
            <span>🔍</span>
            <span class="search-trigger-placeholder">搜索量级 / 角色 / 材质…</span>
          </span>
          <kbd class="kbd-hint">Ctrl K</kbd>
        </button>
        <button type="button" class="icon-btn" id="history-open-btn" title="阅读进度与浏览足迹">
          <span>📖</span>
          <span class="dot-indicator"></span>
        </button>
        <button type="button" class="icon-btn" id="theme-toggle-btn" title="切换深浅色主题">☀️</button>
        <button type="button" class="icon-btn mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单">☰</button>
      </div>
    </div>
  </header>

  {context_bar_html}

  <main style="flex:1">
    {body_html}
  </main>

  <div class="resume-toast" id="resume-toast" role="status" aria-live="polite">
    <span class="resume-toast-text" id="resume-toast-text">上次阅读进度</span>
    <button type="button" class="resume-toast-btn" id="resume-toast-btn">继续阅读</button>
    <button type="button" class="resume-toast-close" id="resume-toast-close" aria-label="关闭提示">×</button>
  </div>

  <div class="floating-dock">
    {toc_dock_btn}
    <button type="button" class="dock-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页" title="返回上一页">‹</button>
    <button type="button" class="dock-btn" id="dock-top-btn" title="回到顶部">
      <svg class="progress-ring-svg" viewBox="0 0 44 44" aria-hidden="true">
        <circle class="progress-ring-circle" id="dock-progress-circle" cx="22" cy="22" r="20"></circle>
      </svg>
      <span>↑</span>
    </button>
  </div>

  <!-- Global Search Modal -->
  <div class="modal-backdrop" id="search-modal" role="dialog" aria-modal="true" aria-label="全站即时检索">
    <div class="modal-dialog">
      <div class="search-modal-head">
        <span style="font-size:18px">🔍</span>
        <input type="search" class="search-modal-input" id="search-modal-input" placeholder="输入代字（宇◆、恒○）、角色、规则或材质（白矮星、花岗岩、0#）…" autocomplete="off">
        <a href="{r}search.html" class="chip-btn" style="white-space:nowrap">高级搜索页 ↗</a>
        <button type="button" class="resume-toast-close" id="search-modal-close" aria-label="关闭">✕</button>
      </div>
      <div class="search-modal-tabs">
        <button type="button" class="chip-btn active" data-search-tab="all">全部结果</button>
        <button type="button" class="chip-btn" data-search-tab="tier">量级档位</button>
        <button type="button" class="chip-btn" data-search-tab="char">角色档案</button>
        <button type="button" class="chip-btn" data-search-tab="rules">衡天体系标准</button>
        <button type="button" class="chip-btn" data-search-tab="materials">材质能量库</button>
      </div>
      <div class="search-modal-body" id="search-modal-results"></div>
    </div>
  </div>

  <!-- Reading Progress & Footprints Modal -->
  <div class="modal-backdrop" id="history-modal" role="dialog" aria-modal="true" aria-label="阅读进度与足迹">
    <div class="modal-dialog">
      <div class="search-modal-head" style="justify-content:space-between">
        <strong style="font-size:16px">📖 阅读进度与最近浏览记录</strong>
        <div style="display:flex;align-items:center;gap:8px">
          <button type="button" class="chip-btn" id="history-clear-btn">清空全部</button>
          <button type="button" class="resume-toast-close" id="history-close-btn" aria-label="关闭">✕</button>
        </div>
      </div>
      <div class="search-modal-body" id="history-modal-body"></div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <strong style="color:var(--text-primary)">衡天⊙ PowerWiki</strong> · 基于《衡天⊙ 多维战力量级体系（第二版）》与《材质与破坏能量数据库（第二版）》构建
      </div>
      <div class="footer-links">
        <a href="{r}index.html">首页</a>
        <a href="{r}tiers.html">量级分类</a>
        <a href="{r}characters.html">角色分类</a>
        <a href="{r}rules.html">衡天体系全文</a>
        <a href="{r}materials.html">材质数据库全文</a>
        <a href="{r}search.html">全站检索</a>
      </div>
    </div>
  </footer>

  <script src="{r}static/js/search-index.js"></script>
  <script src="{r}static/js/app.js"></script>
</body>
</html>
"""


def make_context_bar(root_prefix: str, fallback_rel: str, fallback_name: str, crumbs: list, right_note: str = "") -> str:
    crumb_parts = [f'<a href="{root_prefix}index.html">首页</a>']
    for label, href in crumbs:
        crumb_parts.append('<span class="sep">/</span>')
        if href:
            crumb_parts.append(f'<a href="{href}">{html.escape(label)}</a>')
        else:
            crumb_parts.append(f'<span class="current">{html.escape(label)}</span>')

    return f"""
  <div class="context-bar">
    <div class="container context-inner">
      <div class="context-left">
        <button type="button" class="back-btn js-smart-back" data-fallback="{html.escape(fallback_rel)}" data-fallback-name="{html.escape(fallback_name)}">
          <span>‹</span>
          <span class="js-back-label">返回{html.escape(fallback_name)}</span>
        </button>
        <nav class="breadcrumbs" aria-label="面包屑导航">
          {"".join(crumb_parts)}
        </nav>
      </div>
      <div class="context-right">{right_note}</div>
    </div>
  </div>
"""


def build_all():
    tiers_payload = json.loads((DATA_DIR / "tiers.json").read_text(encoding="utf-8"))
    chars_payload = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8"))

    groups = tiers_payload["groups"]
    tiers = tiers_payload["tiers"]
    ranked_tiers = [t for t in tiers if not t.get("unranked")]
    formal_chars = chars_payload.get("characters", [])
    demo_chars = chars_payload.get("demo_archetypes", [])

    tier_count = len(ranked_tiers)
    char_count = len(formal_chars)

    # Parse both canonical Markdown documents in full
    rules_md = (DOCS_DIR / "衡天量级体系（新）.md").read_text(encoding="utf-8")
    materials_md = (DOCS_DIR / "材质与破坏能量数据库（新）.md").read_text(encoding="utf-8")

    rules_html_body, rules_toc, rules_sections = parse_markdown_document(rules_md, "rules", "rules.html")
    mat_html_body, mat_toc, mat_sections = parse_markdown_document(materials_md, "materials", "materials.html")

    # Verify & resolve all rule_section anchors in tiers.json against rules_toc
    rules_ids = {item["id"] for item in rules_toc} | {"doc-top"}
    rules_title_to_id = {item["text"]: item["id"] for item in rules_toc}
    tier_anchor_map = {}
    for t in tiers:
        sec_ref = t.get("rule_section", "")
        if not sec_ref:
            tier_anchor_map[t["slug"]] = "doc-top"
        elif sec_ref in rules_ids:
            tier_anchor_map[t["slug"]] = sec_ref
        elif sec_ref in rules_title_to_id:
            tier_anchor_map[t["slug"]] = rules_title_to_id[sec_ref]
        else:
            raise AssertionError(f"Tier {t['slug']} points to missing rules anchor/heading: {sec_ref!r}")

    # 1. Build Search Index & Client Data Bundle (static/js/search-index.js)
    search_items = []
    for t in tiers:
        search_items.append(
            {
                "type": "tier",
                "title": f"⊙ {t['code']} · {t['name']}（{t['family']}）",
                "code": t["code"],
                "pinyin": f"{t['code_pinyin']} {t['full_pinyin']} {t['code_initial']} {t['full_initial']}",
                "url": f"tier/{t['slug']}.html",
                "text": f"能量/数学刻度：{t['energy']} ｜ 覆盖尺度：{t['scale']} ｜ 模型：{t['model']} ｜ 说明：{t['notes']}",
            }
        )

    for c in formal_chars:
        t_obj = next((x for x in tiers if x["slug"] == c["tier_slug"]), None)
        t_label = f"⊙{t_obj['code']} {t_obj['name']}" if t_obj else "待定"
        search_items.append(
            {
                "type": "char",
                "title": f"{c['name']}（{c.get('series', '')}）· {t_label}",
                "code": t_obj["code"] if t_obj else "",
                "pinyin": f"{c.get('pinyin', '')} {c.get('initial', '')}",
                "url": f"character/{c['slug']}.html",
                "text": f"{c.get('summary', '')} ｜ 七维：{json.dumps(c.get('dims', {}), ensure_ascii=False)}",
            }
        )

    search_items.extend(rules_sections)
    search_items.extend(mat_sections)

    client_data = {
        "groups": groups,
        "tiers": tiers,
        "characters": formal_chars,
        "demoArchetypes": demo_chars,
    }

    js_bundle = (
        "window.__POWERWIKI_DATA__ = "
        + json.dumps(client_data, ensure_ascii=False, separators=(",", ":"))
        + ";\nwindow.__POWERWIKI_INDEX__ = "
        + json.dumps(search_items, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )
    (ROOT / "static" / "js" / "search-index.js").write_text(js_bundle, encoding="utf-8")

    # 2. Generate index.html
    home_body = f"""
    <section class="hero-section">
      <div class="hero-bg" style="background-image:url('./static/img/hero-hengtian.jpg')"></div>
      <div class="hero-mask"></div>
      <div class="container hero-content">
        <div class="hero-eyebrow mono">⊙ HENGTIAN MULTIDIMENSIONAL SCALE · SECOND EDITION</div>
        <h1 class="hero-title">衡天<span class="sun-mark">⊙</span> 多维战力量级与破坏能量百科</h1>
        <p class="hero-desc">
          告别单维标签与叠盒跳档——以<strong>七维独立评定（破·控·域·御·速·算·性）</strong>、物理通量统一模型
          <span class="mono">F* = 1.64×10²³ J/m²</span>、快速增长层级（FGH）及大基数公理谱系，构建从<strong>昆虫级（10⁻⁴ J）</strong>直至<strong>论天最上（莱茵哈特—伯克利基数）</strong>的严谨标尺。
        </p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="./tiers.html">浏览 {tier_count} 档量级天梯 ›</a>
          <a class="btn btn-ghost" href="./characters.html">进入角色分类库</a>
          <a class="btn btn-ghost" href="./rules.html">阅读《衡天⊙》全文标准</a>
          <a class="btn btn-ghost" href="./materials.html">查阅材质破坏能量库</a>
        </div>
        <div class="hero-metrics">
          <div class="metric-chip">
            <div class="metric-val mono">{tier_count} <span style="font-size:13px;font-weight:500">+ 1</span></div>
            <div class="metric-label">规范量级档位 + 待定兜底</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">7 维</div>
            <div class="metric-label">破·控·域·御·速·算·性</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">A–Z / ↑↓</div>
            <div class="metric-label">首字母与量级双向排序</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">100%</div>
            <div class="metric-label">两部核心典籍全文无删减</div>
          </div>
        </div>
      </div>
    </section>

    <div class="container">
      <section class="scale-ribbon-section">
        <div class="section-head">
          <h2 class="section-title"><span class="dot"></span>衡天⊙ 全域刻度速览（由小到大）</h2>
          <a href="./tiers.html?sort=asc" style="font-size:13.5px">查看完整 97 档递增序列 →</a>
        </div>
        <div class="scale-track">
          <a class="scale-node" style="--node-color:var(--dom-terrestrial)" href="./tier/insect.html">
            <span class="scale-node-range mono">#01 · ⊙虫 → ⊙表☆</span>
            <span class="scale-node-title">地表与常规目标区</span>
            <span class="scale-node-energy mono">&lt; 10⁻⁴ J ～ 1.8×10²⁹ J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-stellar)" href="./tier/star-std.html">
            <span class="scale-node-range mono">#43 · ⊙星▽ → ⊙恒☆</span>
            <span class="scale-node-title">天体自引力束缚区</span>
            <span class="scale-node-energy mono">1.8×10²⁹ J ～ 1.8×10⁴² J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-cosmic)" href="./tier/system-std.html">
            <span class="scale-node-range mono">#57 · ⊙系▽ → ⊙构☆</span>
            <span class="scale-node-title">球面/盘面通量覆盖区</span>
            <span class="scale-node-energy mono">3.7×10⁴⁹ J ～ 1.4×10⁷⁵ J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--accent-gold)" href="./tier/universe-extreme.html">
            <span class="scale-node-range mono">#79 · ⊙宇▽ → ⊙宇☆</span>
            <span class="scale-node-title">宇宙五档（含极宇宙◆）</span>
            <span class="scale-node-energy mono">1.4×10⁷⁵ J ～ 10↑↑3 倍宇○</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-fgh)" href="./tier/fgh-tower.html">
            <span class="scale-node-range mono">#84 · ⊙广·塔 → ⊙广·顶</span>
            <span class="scale-node-title">广义无限区（FGH 7段）</span>
            <span class="scale-node-energy mono">f₃ 幂塔 → f_ω → 不可计算</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-beyond)" href="./tier/beyond-sky-top.html">
            <span class="scale-node-range mono">#90 · ⊙外·门 → ⊙天·最</span>
            <span class="scale-node-title">论外与论天大基数区</span>
            <span class="scale-node-energy mono">ℵ₀ → ℶ 不动点 → 莱茵哈特</span>
          </a>
        </div>
      </section>

      <section class="resume-hub" id="home-resume-hub" aria-label="阅读进度与足迹">
        <div class="section-head" style="margin-bottom:8px">
          <h2 class="section-title"><span class="dot"></span>阅读进度与浏览足迹</h2>
          <span class="section-sub">正在读取本地进度…</span>
        </div>
      </section>

      <section class="portal-section">
        <div class="section-head">
          <h2 class="section-title"><span class="dot"></span>四大核心板块</h2>
          <span class="section-sub">支持首字母索引、从小到大排序、全文锚点定位与进度记忆</span>
        </div>
        <div class="portal-grid">
          <a class="portal-card" href="./tiers.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-tiers.jpg')">
              <span class="portal-tag mono">CATEGORY 01 · TIERS</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>量级分类总览</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">完整收录衡天⊙第二版全部 {tier_count} 个正式量级与过渡带。支持<strong>按量级从小到大</strong>、<strong>从大到小</strong>及<strong>按拼音首字母 A–Z</strong>自由切换，点击任一档位可直达规则原文对应条款。</p>
              <div class="portal-features">
                <span class="mini-chip">从小到大排序</span>
                <span class="mini-chip">首字母 A–Z 索引</span>
                <span class="mini-chip">卡片 / 紧凑表双视图</span>
              </div>
            </div>
          </a>

          <a class="portal-card" href="./characters.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-characters.jpg')">
              <span class="portal-tag mono">CATEGORY 02 · CHARACTERS</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>角色档案分类</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">采用七维战力面板（破·控·域·御·速·算·性）与五级证据可信度标记展示角色评定。支持<strong>按角色首字母 A–Z</strong>与<strong>按主档量级从小到大</strong>排序，内置 6 组标准书写演示样例供随时预览。</p>
              <div class="portal-features">
                <span class="mini-chip">七维雷达结构</span>
                <span class="mini-chip">首字母 / 量级双排序</span>
                <span class="mini-chip">证据状态高亮</span>
              </div>
            </div>
          </a>

          <a class="portal-card" href="./rules.html">
            <div class="portal-banner" style="background-image:url('./static/img/hero-hengtian.jpg')">
              <span class="portal-tag mono">CANONICAL DOC 01 · FULL TEXT</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>《衡天⊙ 多维战力量级体系（第二版）》</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">一字不漏全文展示全部十一部分与未定稿附则：核心判定总则、多击不认、证伪五信号、覆盖通量推导、广义无限 FGH 分段、数量轴与层级跃迁、论外大基数及漫改量化细则。</p>
              <div class="portal-features">
                <span class="mini-chip">全文无删减展示</span>
                <span class="mini-chip">目录同步高亮</span>
                <span class="mini-chip">自动保存阅读位置</span>
              </div>
            </div>
          </a>

          <a class="portal-card" href="./materials.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-materials.jpg')">
              <span class="portal-tag mono">CANONICAL DOC 02 · FULL TEXT</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>《材质与破坏能量数据库（第二版）》</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">全文展示破坏动词双轴矩阵、常规物质粉碎能量密度、抗压/剪切/断裂韧性、熔化与汽化热力学上限、白矮星与中子星引力束缚能、撞击成坑与云层推算公式及文献出处。</p>
              <div class="portal-features">
                <span class="mini-chip">全文数据速查</span>
                <span class="mini-chip">移动端横向滚表</span>
                <span class="mini-chip">跨文档双向互链</span>
              </div>
            </div>
          </a>
        </div>
      </section>
    </div>
    """

    (ROOT / "index.html").write_text(
        render_shell(
            title="首页",
            page_id="index.html",
            page_type="home",
            active_nav="home",
            root_prefix="./",
            body_html=home_body,
            tier_count=tier_count,
            char_count=char_count,
        ),
        encoding="utf-8",
    )

    # 3. Generate tiers.html (with static server-rendered fallback inside #tiers-explorer-mount)
    group_map = {g["id"]: g for g in groups}
    ssr_tier_blocks = []
    for g in groups:
        g_tiers = [t for t in tiers if t["group_id"] == g["id"]]
        cards = []
        for t in g_tiers:
            ord_str = "兜底暂存" if t.get("unranked") else f"#{t['order']:02d}"
            cards.append(
                f"""
            <a class="tier-card" data-domain="{t['domain']}" href="./tier/{t['slug']}.html">
              <div class="tier-card-top">
                <span class="tier-code-badge mono">⊙ {html.escape(t['code'])}</span>
                <span class="tier-order-num mono">{ord_str} · 首字母 {t['code_initial']}</span>
              </div>
              <div class="tier-card-name">
                <span>{html.escape(t['name'])}</span>
                <span style="font-size:12px;font-weight:500;color:var(--text-muted)">{html.escape(t['family'])}</span>
              </div>
              <div class="tier-energy-line mono">{html.escape(t['energy'])}</div>
              <div class="tier-scale-line">{html.escape(t['scale'])}</div>
              <div class="tier-card-foot">
                <span>{html.escape(t['model'])}</span>
                <span style="color:var(--accent-blue)">详情 ›</span>
              </div>
            </a>"""
            )
        ssr_tier_blocks.append(
            f"""
        <section class="tier-group-block" id="group-{g['id']}">
          <div class="tier-group-header">
            <h2 class="tier-group-title">{html.escape(g['title'])}</h2>
            <span class="tier-group-sub">{html.escape(g['subtitle'])} · 共 {len(g_tiers)} 档</span>
          </div>
          <div class="tier-grid">{"".join(cards)}</div>
        </section>"""
        )

    tiers_body = f"""
    <section class="page-hero">
      <div class="page-hero-bg" style="background-image:url('./static/img/banner-tiers.jpg')"></div>
      <div class="page-hero-mask"></div>
      <div class="container page-hero-inner">
        <h1 class="page-hero-title"><span>量级分类总览</span><span class="brand-badge mono">⊙ {tier_count} 正式档位 + 待定</span></h1>
        <p class="page-hero-desc">完整映射《衡天⊙ 多维战力量级体系（第二版）》从昆虫级（#01）到论天最上（#97）的全部标尺。支持按量级从小到大、从大到小及按首字母 A–Z 排序检索。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:54px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span style="font-size:13px;color:var(--text-muted);font-weight:600">排序方式：</span>
            <div class="segmented-group" role="group" aria-label="量级排序切换">
              <button type="button" class="seg-btn active" data-tier-sort="asc">↑ 量级从小到大</button>
              <button type="button" class="seg-btn" data-tier-sort="desc">↓ 量级从大到小</button>
              <button type="button" class="seg-btn" data-tier-sort="alpha">A–Z 首字母排序</button>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1;justify-content:flex-end">
            <div class="filter-input-wrap">
              <span class="filter-input-icon">🔍</span>
              <input type="search" class="filter-input" id="tier-filter-input" placeholder="筛选代字、名称、能量阈值（如 宇◆、10⁴¹、阿克曼）…">
              <button type="button" class="filter-clear-btn" id="tier-filter-clear" aria-label="清空">✕</button>
            </div>
            <div class="segmented-group" role="group" aria-label="视图切换">
              <button type="button" class="seg-btn active" data-tier-view="card">卡片</button>
              <button type="button" class="seg-btn" data-tier-view="table">总表</button>
            </div>
          </div>
        </div>

        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-tier-seg="all">全部区间（{len(tiers)}）</button>
            <button type="button" class="chip-btn" data-tier-seg="inherited">继承区 · 目标式（虫→恒）</button>
            <button type="button" class="chip-btn" data-tier-seg="transition">跨体系过渡带</button>
            <button type="button" class="chip-btn" data-tier-seg="coverage">覆盖体系（系→宇）</button>
            <button type="button" class="chip-btn" data-tier-seg="fgh">广义无限区（FGH）</button>
            <button type="button" class="chip-btn" data-tier-seg="beyond">论外与论天大基数</button>
          </div>
          <span class="mono" id="tier-result-count" style="font-size:12.5px;color:var(--text-muted)">共显示 {len(tiers)} 个档位</span>
        </div>
      </div>

      <div class="alpha-bar" id="tier-alpha-bar">
        <div class="alpha-letters" id="tier-alpha-letters"></div>
        <div class="alpha-mode-switch">
          <span>首字母依据：</span>
          <button type="button" class="chip-btn active" data-alpha-key="code" title="按衡天核心代字拼音首字母（如 城△→C、宇◆→Y、阿克曼→A），分布最均匀">按核心代字</button>
          <button type="button" class="chip-btn" data-alpha-key="full" title="按完整中文名称首字拼音（如 强爆城→Q、极宇宙→J）">按完整名称</button>
        </div>
      </div>

      <div id="tiers-explorer-mount">
        {"".join(ssr_tier_blocks)}
      </div>
    </div>
    """

    (ROOT / "tiers.html").write_text(
        render_shell(
            title="量级分类",
            page_id="tiers.html",
            page_type="tiers",
            active_nav="tiers",
            root_prefix="./",
            context_bar_html=make_context_bar(
                "./",
                "index.html",
                "首页",
                [("量级分类总览", "")],
                '<a href="./rules.html#part-11">对照第十一部分速查表 ↗</a>',
            ),
            body_html=tiers_body,
            tier_count=tier_count,
            char_count=char_count,
        ),
        encoding="utf-8",
    )

    # 4. Generate Individual Tier Detail Pages: tier/<slug>.html
    tier_dir = ROOT / "tier"
    tier_dir.mkdir(exist_ok=True)
    for idx, t in enumerate(tiers):
        g = group_map.get(t["group_id"], {})
        prev_t = ranked_tiers[t["order"] - 2] if (not t.get("unranked") and t["order"] > 1) else None
        next_t = ranked_tiers[t["order"]] if (not t.get("unranked") and t["order"] < len(ranked_tiers)) else None

        chars_in_tier = [c for c in formal_chars if c.get("tier_slug") == t["slug"]]
        if chars_in_tier:
            char_section_html = (
                '<div class="char-grid" style="margin-top:12px">'
                + "".join(
                    f'<a class="char-card" href="../character/{c["slug"]}.html"><h4 style="margin:0">{html.escape(c["name"])}</h4><div style="font-size:13px;color:var(--text-muted)">{html.escape(c.get("series",""))}</div></a>'
                    for c in chars_in_tier
                )
                + "</div>"
            )
        else:
            char_section_html = f"""
            <div style="background:var(--bg-surface-2);border:1px dashed var(--border-subtle);border-radius:12px;padding:18px;color:var(--text-muted);font-size:13.5px;margin-top:10px">
              当前正式角色库暂无定级于 <strong>⊙ {html.escape(t['code'])}（{html.escape(t['name'])}）</strong> 的角色档案。
              可前往 <a href="../characters.html">角色档案库</a> 了解录入规范。
            </div>"""

        prev_html = (
            f'<a class="ladder-item prev" href="./{prev_t["slug"]}.html"><span class="ladder-dir">← 上一较低量级（#{prev_t["order"]:02d}）</span><span class="ladder-name">⊙ {html.escape(prev_t["code"])} · {html.escape(prev_t["name"])}</span><span class="mono" style="font-size:12px;color:var(--accent-gold)">{html.escape(prev_t["energy"])}</span></a>'
            if prev_t
            else '<div class="ladder-item prev" style="opacity:0.45"><span class="ladder-dir">← 已是最低起点</span><span class="ladder-name">无更低正式量级</span></div>'
        )
        next_html = (
            f'<a class="ladder-item next" href="./{next_t["slug"]}.html"><span class="ladder-dir">下一较高量级（#{next_t["order"]:02d}）→</span><span class="ladder-name">⊙ {html.escape(next_t["code"])} · {html.escape(next_t["name"])}</span><span class="mono" style="font-size:12px;color:var(--accent-gold)">{html.escape(next_t["energy"])}</span></a>'
            if next_t
            else '<div class="ladder-item next" style="opacity:0.45"><span class="ladder-dir">已是最高顶点 →</span><span class="ladder-name">无更高正式量级</span></div>'
        )

        rank_display = "不参与大小排序（信息不足暂存）" if t.get("unranked") else f"第 {t['order']} 档 / 共 {len(ranked_tiers)} 正式档"

        rule_anchor_id = tier_anchor_map[t["slug"]]
        rule_sec_label = t.get("rule_section") or "总则"
        detail_body = f"""
        <div class="container detail-wrap">
          <article class="detail-card">
            <div class="detail-header">
              <div>
                <div class="detail-code-pill mono">⊙ {html.escape(t['code'])}</div>
                <h1 class="detail-title">{html.escape(t['name'])} <span style="font-size:18px;font-weight:500;color:var(--text-muted)">· {html.escape(t['family'])}</span></h1>
              </div>
              <div style="display:flex;gap:10px;flex-wrap:wrap">
                <a class="btn btn-primary" href="../rules.html#{html.escape(rule_anchor_id)}" title="跳转至：{html.escape(rule_sec_label)}">📖 查阅原文章节：{html.escape(rule_sec_label[:18])}{'…' if len(rule_sec_label) > 18 else ''} ↗</a>
                <a class="btn btn-surface" href="../tiers.html">返回全部量级</a>
              </div>
            </div>

            <div class="spec-grid">
              <div class="spec-box">
                <div class="spec-label">全链条序位（从小到大）</div>
                <div class="spec-value mono">{rank_display}</div>
              </div>
              <div class="spec-box">
                <div class="spec-label">所属体系区间</div>
                <div class="spec-value">{html.escape(g.get('title', ''))}</div>
              </div>
              <div class="spec-box wide">
                <div class="spec-label">能量区间 / 数学刻度定义</div>
                <div class="spec-value mono" style="color:var(--accent-gold);font-size:17px">{html.escape(t['energy'])}</div>
              </div>
              <div class="spec-box">
                <div class="spec-label">典型破坏尺度与参照物</div>
                <div class="spec-value">{html.escape(t['scale'])}</div>
              </div>
              <div class="spec-box">
                <div class="spec-label">适用物理 / 数学模型</div>
                <div class="spec-value">{html.escape(t['model'])}</div>
              </div>
              <div class="spec-box wide">
                <div class="spec-label">判定细则与注意事项</div>
                <div class="spec-value" style="font-weight:400;color:var(--text-secondary);line-height:1.75">{html.escape(t['notes'])}</div>
              </div>
              <div class="spec-box">
                <div class="spec-label">拼音检索索引（代字 / 全称）</div>
                <div class="spec-value mono">{t['code_initial']} ({t['code_pinyin']}) / {t['full_initial']} ({t['full_pinyin']})</div>
              </div>
              <div class="spec-box">
                <div class="spec-label">配套材质与天体参数参考</div>
                <div class="spec-value"><a href="../materials.html">查阅《材质与破坏能量数据库》↗</a></div>
              </div>
            </div>

            <section style="margin-top:26px">
              <h2 style="font-size:17px;margin:0 0 6px">本量级收录角色（{len(chars_in_tier)}）</h2>
              {char_section_html}
            </section>
          </article>

          <nav class="ladder-nav" aria-label="相邻量级切换">
            {prev_html}
            {next_html}
          </nav>
        </div>
        """

        (tier_dir / f"{t['slug']}.html").write_text(
            render_shell(
                title=f"⊙{t['code']} {t['name']}",
                page_id=f"tier/{t['slug']}.html",
                page_type="tier-detail",
                active_nav="tiers",
                root_prefix="../",
                context_bar_html=make_context_bar(
                    "../",
                    "tiers.html",
                    "量级分类",
                    [("量级分类总览", "../tiers.html"), (f"⊙ {t['code']} · {t['name']}", "")],
                    f'<span class="mono">序位 #{t["order"]:02d}</span>' if not t.get("unranked") else "兜底标记",
                ),
                body_html=detail_body,
                tier_count=tier_count,
                char_count=char_count,
            ),
            encoding="utf-8",
        )

    # 5. Generate characters.html & character/<slug>.html (if formal_chars exist)
    chars_body = f"""
    <section class="page-hero">
      <div class="page-hero-bg" style="background-image:url('./static/img/banner-characters.jpg')"></div>
      <div class="page-hero-mask"></div>
      <div class="container page-hero-inner">
        <h1 class="page-hero-title"><span>角色档案分类</span><span class="brand-badge mono">七维战力 · 证据标记</span></h1>
        <p class="page-hero-desc">按《衡天⊙ 多维战力量级体系（第二版）》展示角色主档与破·控·域·御·速·算·性七维细分评定。支持按角色首字母 A–Z 及按主档量级从小到大排序。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:56px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span style="font-size:13px;color:var(--text-muted);font-weight:600">排序方式：</span>
            <div class="segmented-group" role="group" aria-label="角色排序切换">
              <button type="button" class="seg-btn active" data-char-sort="asc">↑ 量级从小到大</button>
              <button type="button" class="seg-btn" data-char-sort="desc">↓ 量级从大到小</button>
              <button type="button" class="seg-btn" data-char-sort="alpha">A–Z 首字母排序</button>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1;justify-content:flex-end">
            <select id="char-series-select" class="filter-input" style="max-width:200px;padding-left:12px" aria-label="按作品筛选">
              <option value="all">全部作品</option>
            </select>
            <div class="filter-input-wrap">
              <span class="filter-input-icon">🔍</span>
              <input type="search" class="filter-input" id="char-filter-input" placeholder="搜索角色名、拼音、出处、机制特性…">
            </div>
            <button type="button" class="chip-btn" id="char-demo-toggle">✦ 预览体系书写演示样例（6 组）</button>
          </div>
        </div>

        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-char-domain="all">全部量级域</button>
            <button type="button" class="chip-btn" data-char-domain="terrestrial">地表与常规区</button>
            <button type="button" class="chip-btn" data-char-domain="stellar">行星与恒星区</button>
            <button type="button" class="chip-btn" data-char-domain="cosmic">星系与宇宙区</button>
            <button type="button" class="chip-btn" data-char-domain="fgh">广义无限区</button>
            <button type="button" class="chip-btn" data-char-domain="beyond">论外与论天区</button>
          </div>
          <span class="mono" id="char-result-count" style="font-size:12.5px;color:var(--text-muted)">正式收录 {char_count} 位角色</span>
        </div>
      </div>

      <div class="alpha-bar" id="char-alpha-bar">
        <div class="alpha-letters" id="char-alpha-letters"></div>
        <span style="font-size:12px;color:var(--text-muted)">按角色中文姓名拼音首字母分组</span>
      </div>

      <div id="chars-explorer-mount"></div>
    </div>

    <!-- Demo Character 7D Inspection Modal -->
    <div class="modal-backdrop" id="demo-char-modal" role="dialog" aria-modal="true" aria-label="七维评定样例详情">
      <div class="modal-dialog">
        <div class="search-modal-head" style="justify-content:space-between">
          <strong>⊙ 衡天七维角色卡书写样例</strong>
          <button type="button" class="resume-toast-close" id="demo-char-close" aria-label="关闭">✕</button>
        </div>
        <div class="search-modal-body" id="demo-char-modal-body" style="padding:20px 22px"></div>
      </div>
    </div>
    """

    (ROOT / "characters.html").write_text(
        render_shell(
            title="角色档案分类",
            page_id="characters.html",
            page_type="chars",
            active_nav="chars",
            root_prefix="./",
            context_bar_html=make_context_bar(
                "./",
                "index.html",
                "首页",
                [("角色档案分类", "")],
                '<a href="./rules.html#sec-1-5">查看 1.5 节完整格式规范 ↗</a>',
            ),
            body_html=chars_body,
            tier_count=tier_count,
            char_count=char_count,
        ),
        encoding="utf-8",
    )

    # Also build character/<slug>.html for any formal characters
    char_dir = ROOT / "character"
    char_dir.mkdir(exist_ok=True)
    for c in formal_chars:
        t_obj = next((x for x in tiers if x["slug"] == c["tier_slug"]), tiers[-1])
        dims_rows = "".join(
            f'<tr><th style="width:95px">维度「{k}」</th><td>{format_inline_md(c.get("dims", {}).get(k, "〔缺〕"))}</td></tr>'
            for k in ["破", "控", "域", "御", "速", "算", "性"]
        )
        c_body = f"""
        <div class="container detail-wrap">
          <article class="detail-card">
            <div class="detail-header">
              <div>
                <div class="detail-code-pill mono">⊙ {html.escape(t_obj['code'])} · {html.escape(t_obj['name'])}</div>
                <h1 class="detail-title">{html.escape(c['name'])}</h1>
                <div style="color:var(--text-muted);margin-top:6px">{html.escape(c.get('series', ''))} · {html.escape(c.get('realm', ''))}</div>
              </div>
              <a class="btn btn-surface" href="../tier/{t_obj['slug']}.html">查看所属量级详情 ›</a>
            </div>
            <p style="font-size:15.5px;color:var(--text-secondary)">{html.escape(c.get('summary', ''))}</p>
            <div class="table-scroll"><table><tbody>{dims_rows}</tbody></table></div>
          </article>
        </div>
        """
        (char_dir / f"{c['slug']}.html").write_text(
            render_shell(
                title=c["name"],
                page_id=f"character/{c['slug']}.html",
                page_type="char-detail",
                active_nav="chars",
                root_prefix="../",
                context_bar_html=make_context_bar(
                    "../",
                    "characters.html",
                    "角色分类",
                    [("角色档案分类", "../characters.html"), (c["name"], "")],
                ),
                body_html=c_body,
                tier_count=tier_count,
                char_count=char_count,
            ),
            encoding="utf-8",
        )

    # 6. Generate Full-Text Canonical Document Pages: rules.html & materials.html
    def build_doc_page(
        *,
        filename: str,
        title: str,
        subtitle: str,
        banner_img: str,
        active_nav: str,
        rendered_md: str,
        toc_list: list,
        raw_md_len: int,
        companion_link: str,
        companion_label: str,
    ):
        toc_items_html = []
        for item in toc_list:
            lvl_cls = f"toc-lvl-{min(item['level'], 3)}"
            toc_items_html.append(
                f'<a class="toc-item {lvl_cls}" href="#{item["id"]}">{html.escape(item["text"])}</a>'
            )

        doc_body = f"""
        <section class="page-hero">
          <div class="page-hero-bg" style="background-image:url('./static/img/{banner_img}')"></div>
          <div class="page-hero-mask"></div>
          <div class="container page-hero-inner">
            <h1 class="page-hero-title"><span>{html.escape(title)}</span><span class="brand-badge">全文无删减版</span></h1>
            <p class="page-hero-desc">{html.escape(subtitle)}</p>
          </div>
        </section>

        <div class="container doc-layout">
          <aside class="doc-sidebar" id="doc-sidebar" aria-label="文档章节目录">
            <div class="toc-header">
              <div class="toc-title-row">
                <span>📑 章节导航（{len(toc_list)} 节）</span>
                <span class="toc-pct mono" id="toc-progress-pct">0%</span>
              </div>
              <input type="search" class="toc-filter" id="toc-filter-input" placeholder="过滤章节标题…">
            </div>
            <nav class="toc-nav" id="toc-nav">
              {"".join(toc_items_html)}
            </nav>
          </aside>

          <article class="doc-article-card">
            <div class="doc-meta-strip">
              <span>📌 原文全文直出（共 <strong>{raw_md_len:,}</strong> 字符 · <strong>{len(toc_list)}</strong> 个锚点小节 · 自动记录阅读位置）</span>
              <a class="xref-link" href="./{companion_link}">切换至姊妹篇：{html.escape(companion_label)} ↗</a>
            </div>
            <div class="markdown-body">
              {rendered_md}
            </div>
          </article>
        </div>
        """

        (ROOT / filename).write_text(
            render_shell(
                title=title,
                page_id=filename,
                page_type="doc",
                active_nav=active_nav,
                root_prefix="./",
                context_bar_html=make_context_bar(
                    "./",
                    "index.html",
                    "首页",
                    [(title, "")],
                    f'<a href="./{companion_link}">{html.escape(companion_label)} ↗</a>',
                ),
                body_html=doc_body,
                has_toc_drawer=True,
                tier_count=tier_count,
                char_count=char_count,
            ),
            encoding="utf-8",
        )

    build_doc_page(
        filename="rules.html",
        title="《衡天⊙ 多维战力量级体系（第二版）》",
        subtitle="完整收录第一至第十一部分及未定稿附则：核心判定原则、目标式继承区、覆盖通量统一模型、广义无限 FGH 分段、数量与层级轴、论外大基数及漫改量化方法。",
        banner_img="hero-hengtian.jpg",
        active_nav="rules",
        rendered_md=rules_html_body,
        toc_list=rules_toc,
        raw_md_len=len(rules_md),
        companion_link="materials.html",
        companion_label="《材质与破坏能量数据库（第二版）》",
    )

    build_doc_page(
        filename="materials.html",
        title="《材质与破坏能量数据库（第二版）》",
        subtitle="《衡天⊙》官方配套工程物理参数库：破坏动词双轴定性、物质粉碎能量密度、材料强度与断裂韧性、相变潜热、天体引力束缚能、撞击成坑与云层推算。",
        banner_img="banner-materials.jpg",
        active_nav="materials",
        rendered_md=mat_html_body,
        toc_list=mat_toc,
        raw_md_len=len(materials_md),
        companion_link="rules.html",
        companion_label="《衡天⊙ 多维战力量级体系（第二版）》",
    )

    # 7. Generate Dedicated Search Page: search.html
    search_body = f"""
    <section class="page-hero">
      <div class="page-hero-bg" style="background-image:url('./static/img/banner-tiers.jpg')"></div>
      <div class="page-hero-mask"></div>
      <div class="container page-hero-inner">
        <h1 class="page-hero-title"><span>全站即时检索中心</span><span class="brand-badge mono">{len(search_items)} 条索引块</span></h1>
        <p class="page-hero-desc">跨量级档位、角色档案、《衡天⊙ 多维战力量级体系》及《材质与破坏能量数据库》全章节毫秒级检索。</p>
      </div>
    </section>

    <div class="container" style="padding:24px 22px 60px;max-width:980px">
      <div class="toolbar-panel" style="margin-top:0">
        <div style="display:flex;gap:10px;align-items:center">
          <span style="font-size:20px">🔍</span>
          <input type="search" id="dedicated-search-input" class="filter-input" style="max-width:none;font-size:15.5px;padding:11px 16px" placeholder="输入多个关键词空格分隔，例如：白矮星 束缚能 / 宇◆ / 0# 拉姆齐 / 花岗岩 汽化 / 多击不认…" autofocus>
        </div>
        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-page-search-type="all">全部类别</button>
            <button type="button" class="chip-btn" data-page-search-type="tier">量级档位（{len(tiers)}）</button>
            <button type="button" class="chip-btn" data-page-search-type="char">角色档案（{char_count}）</button>
            <button type="button" class="chip-btn" data-page-search-type="rules">衡天体系标准（{len(rules_sections)} 节）</button>
            <button type="button" class="chip-btn" data-page-search-type="materials">材质能量数据库（{len(mat_sections)} 节）</button>
          </div>
          <span class="mono" id="dedicated-search-count" style="font-size:12.5px;color:var(--text-muted)"></span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12.5px;color:var(--text-muted)">
          <span>热门速查词：</span>
          <button type="button" class="chip-btn" data-hot-query="宇◆">宇◆（极宇宙）</button>
          <button type="button" class="chip-btn" data-hot-query="F*">通量常数 F*</button>
          <button type="button" class="chip-btn" data-hot-query="多击不认">多击不认</button>
          <button type="button" class="chip-btn" data-hot-query="证伪">证伪五信号</button>
          <button type="button" class="chip-btn" data-hot-query="0#">0#（零尖）</button>
          <button type="button" class="chip-btn" data-hot-query="图灵跃迁">图灵跃迁</button>
          <button type="button" class="chip-btn" data-hot-query="中子星">中子星外壳/束缚能</button>
          <button type="button" class="chip-btn" data-hot-query="花岗岩">花岗岩粉碎/汽化</button>
          <button type="button" class="chip-btn" data-hot-query="斩陨">斩陨规则</button>
        </div>
      </div>

      <div id="dedicated-search-results"></div>
    </div>
    """

    (ROOT / "search.html").write_text(
        render_shell(
            title="全站搜索",
            page_id="search.html",
            page_type="search",
            active_nav="",
            root_prefix="./",
            context_bar_html=make_context_bar("./", "index.html", "首页", [("全站搜索", "")]),
            body_html=search_body,
            tier_count=tier_count,
            char_count=char_count,
        ),
        encoding="utf-8",
    )

    print(
        f"Build complete: {len(tiers)} tier pages, {len(formal_chars)} character pages, "
        f"{len(rules_toc)} rules TOC anchors, {len(mat_toc)} materials TOC anchors, "
        f"{len(search_items)} search index entries."
    )


if __name__ == "__main__":
    build_all()
