#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Generator v3.0 (Zero External Dependencies)
- Canonical Standard 1: data/docs/衡天量级体系【第三版·最新】.md (Full Text)
- Canonical Standard 2: data/docs/材质与破坏能量数据库（新）.md (Full Text)
- Tiers Category: Strictly ordered 从小到大 (#01 -> #97)
- Characters Category: Dual sorting (按量级从小到大 & 按首字母 A–Z)
"""

import html
import json
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
    m_part = re.match(r"^第([零一二三四五六七八九十百]+)部分", clean)
    if m_part:
        cn = m_part.group(1)
        num = CN_NUM_MAP.get(cn, cn)
        base = f"part-{num}"
    else:
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

    s = re.sub(r"`([^`]+)`", save_code, raw_text)
    s = s.replace(r"\*", "\x00AST\x00").replace(r"\|", "\x00PIPE\x00")
    s = html.escape(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        s,
    )
    s = (
        s.replace("〔实〕", '<span class="ev-badge ev-confirmed">〔实〕</span>')
        .replace("〔下〕", '<span class="ev-badge ev-lower">〔下〕</span>')
        .replace("〔推〕", '<span class="ev-badge ev-inferred">〔推〕</span>')
        .replace("〔隐〕", '<span class="ev-badge ev-hidden">〔隐〕</span>')
        .replace("〔缺〕", '<span class="ev-badge ev-missing">〔缺〕</span>')
    )

    if doc_kind == "rules":
        s = s.replace(
            "《材质与破坏能量数据库》",
            '<a class="xref-link" href="./materials.html" title="点击跳转至《材质与破坏能量数据库（第二版）》全文">《材质与破坏能量数据库》↗</a>',
        )
    elif doc_kind == "materials":
        s = s.replace(
            "《衡天⊙ 多维战力量级体系》",
            '<a class="xref-link" href="./rules.html" title="点击跳转至《衡天⊙ 多维战力量级体系（第三版）》全文">《衡天⊙ 多维战力量级体系》↗</a>',
        )

    s = s.replace("\x00AST\x00", "*").replace("\x00PIPE\x00", "|")
    for idx, code_html in enumerate(code_store):
        s = s.replace(f"\x00CODE{idx}\x00", code_html)

    return s


def split_md_table_row(line: str) -> list:
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


def render_inner_blocks(lines: list, doc_kind: str, line_sink: list) -> str:
    """Render inner block lines (used inside blockquotes so nested tables/lists render properly)."""
    out = []
    n = len(lines)
    i = 0
    while i < n:
        stripped = lines[i].strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]):
            headers = split_md_table_row(lines[i])
            line_sink.append(" ".join(headers))
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                row_cells = split_md_table_row(lines[i])
                line_sink.append(" ".join(row_cells))
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
        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                item_txt = re.sub(r"^-\s+", "", lines[i].strip())
                line_sink.append(item_txt)
                items.append(f"<li>{format_inline_md(item_txt, doc_kind)}</li>")
                i += 1
            out.append(f'<ul>{"".join(items)}</ul>')
            continue
        para_lines = []
        while i < n:
            ln = lines[i].strip()
            if (
                not ln
                or re.match(r"^-\s+", ln)
                or (ln.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]))
            ):
                break
            line_sink.append(ln)
            para_lines.append(ln)
            i += 1
        out.append("<p>" + "<br>".join(format_inline_md(pl, doc_kind) for pl in para_lines) + "</p>")
    return "\n".join(out)


def parse_markdown_document(md_text: str, doc_kind: str, doc_url: str):
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

        if not stripped:
            i += 1
            continue

        if re.match(r"^-{3,}\s*$", stripped):
            out.append("<hr>")
            i += 1
            continue

        m_h = re.match(r"^(#{1,4})\s+(.+)$", stripped)
        if m_h:
            hashes, raw_h_text = m_h.group(1), m_h.group(2).strip()
            level = len(hashes)

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

        if stripped.startswith("|") and i + 1 < n and is_table_separator(lines[i + 1]):
            headers = split_md_table_row(lines[i])
            cur_section["lines"].append(" ".join(headers))
            i += 2
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

        if stripped.startswith(">"):
            bq_raw_lines = []
            while i < n and lines[i].strip().startswith(">"):
                content = re.sub(r"^>\s?", "", lines[i].strip())
                bq_raw_lines.append(content)
                i += 1
            inner_html = render_inner_blocks(bq_raw_lines, doc_kind, cur_section["lines"])
            out.append(f"<blockquote>{inner_html}</blockquote>")
            continue

        if re.match(r"^-\s+", stripped):
            items = []
            while i < n and re.match(r"^-\s+", lines[i].strip()):
                item_txt = re.sub(r"^-\s+", "", lines[i].strip())
                cur_section["lines"].append(item_txt)
                items.append(f"<li>{format_inline_md(item_txt, doc_kind)}</li>")
                i += 1
            out.append(f'<ul>{"".join(items)}</ul>')
            continue

        if re.match(r"^\d+\.\s+", stripped):
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                item_txt = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                cur_section["lines"].append(item_txt)
                items.append(f"<li>{format_inline_md(item_txt, doc_kind)}</li>")
                i += 1
            out.append(f'<ol>{"".join(items)}</ol>')
            continue

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
    r = root_prefix

    def nav_cls(key):
        return "nav-link active" if active_nav == key else "nav-link"

    toc_dock_btn = (
        '<button type="button" class="dock-btn dock-toc-btn" id="dock-toc-btn" title="展开/收起章节目录">📑</button>'
        if has_toc_drawer
        else ""
    )

    char_badge_label = str(char_count) if char_count > 0 else "示例"

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark" data-root="{r}" data-page-id="{html.escape(page_id)}" data-page-type="{html.escape(page_type)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(title)} · 衡天⊙ PowerWiki</title>
  <meta name="description" content="衡天⊙ 多维战力量级体系（第三版·最新）与材质破坏能量数据库官方百科站——角色分类（首字母与量级从小到大排序）、量级分类（从小到大排列）、全文检索与浏览进度保存。">
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
          <span class="brand-title">衡天 PowerWiki <span class="brand-badge">第三版</span></span>
          <span class="brand-sub">角色 · 量级 · 标准与规则全文</span>
        </span>
      </a>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        <a class="{nav_cls('home')}" href="{r}index.html">首页</a>
        <a class="{nav_cls('chars')}" href="{r}characters.html">角色分类 <span class="nav-count mono">{char_badge_label}</span></a>
        <a class="{nav_cls('tiers')}" href="{r}tiers.html">量级分类 <span class="nav-count mono">{tier_count}</span></a>
        <span class="nav-divider" aria-hidden="true"></span>
        <a class="{nav_cls('rules')}" href="{r}rules.html">标准·衡天体系(第三版)</a>
        <a class="{nav_cls('materials')}" href="{r}materials.html">标准·材质能量库</a>
      </nav>

      <div class="header-actions">
        <button type="button" class="search-trigger" id="global-search-trigger" aria-label="打开全站搜索">
          <span class="search-trigger-left">
            <span>🔍</span>
            <span class="search-trigger-placeholder">搜索角色 / 量级 / 标准…</span>
          </span>
          <kbd class="kbd-hint">Ctrl K</kbd>
        </button>
        <button type="button" class="icon-btn" id="history-open-btn" title="已保存的浏览进度与足迹">
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
    <span class="resume-toast-text" id="resume-toast-text">上次浏览位置</span>
    <button type="button" class="resume-toast-btn" id="resume-toast-btn">继续浏览</button>
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
        <input type="search" class="search-modal-input" id="search-modal-input" placeholder="搜索角色、量级代字（宇◆、恒○）、第三版规则或材质（归因、白矮星、花岗岩）…" autocomplete="off">
        <a href="{r}search.html" class="chip-btn" style="white-space:nowrap">独立搜索页 ↗</a>
        <button type="button" class="resume-toast-close" id="search-modal-close" aria-label="关闭">✕</button>
      </div>
      <div class="search-modal-tabs">
        <button type="button" class="chip-btn active" data-search-tab="all">全部结果</button>
        <button type="button" class="chip-btn" data-search-tab="char">角色分类</button>
        <button type="button" class="chip-btn" data-search-tab="tier">量级分类</button>
        <button type="button" class="chip-btn" data-search-tab="rules">衡天体系(第三版)</button>
        <button type="button" class="chip-btn" data-search-tab="materials">材质破坏能量库</button>
      </div>
      <div class="search-modal-body" id="search-modal-results"></div>
    </div>
  </div>

  <!-- Reading Progress & Footprints Modal -->
  <div class="modal-backdrop" id="history-modal" role="dialog" aria-modal="true" aria-label="浏览进度与足迹">
    <div class="modal-dialog">
      <div class="search-modal-head" style="justify-content:space-between">
        <strong style="font-size:16px">📖 浏览进度保存与最近足迹</strong>
        <div style="display:flex;align-items:center;gap:8px">
          <button type="button" class="chip-btn" id="history-clear-btn">清空全部记录</button>
          <button type="button" class="resume-toast-close" id="history-close-btn" aria-label="关闭">✕</button>
        </div>
      </div>
      <div class="search-modal-body" id="history-modal-body"></div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <strong style="color:var(--text-primary)">衡天⊙ PowerWiki</strong> · 依据《衡天⊙ 多维战力量级体系（第三版）》与《材质与破坏能量数据库（第二版）》构建
      </div>
      <div class="footer-links">
        <a href="{r}index.html">首页</a>
        <a href="{r}characters.html">角色分类</a>
        <a href="{r}tiers.html">量级分类</a>
        <a href="{r}rules.html">衡天体系(第三版)全文</a>
        <a href="{r}materials.html">材质数据库全文</a>
        <a href="{r}search.html">全站搜索</a>
      </div>
    </div>
  </footer>

  <script src="{r}static/js/search-index.js"></script>
  <script src="{r}static/js/app.js"></script>
</body>
</html>
"""


def make_context_bar(
    root_prefix: str,
    fallback_rel: str,
    fallback_name: str,
    crumbs: list,
    right_note: str = "",
    show_bookmark: bool = True,
) -> str:
    crumb_parts = [f'<a href="{root_prefix}index.html">首页</a>']
    for label, href in crumbs:
        crumb_parts.append('<span class="sep">/</span>')
        if href:
            crumb_parts.append(f'<a href="{href}">{html.escape(label)}</a>')
        else:
            crumb_parts.append(f'<span class="current">{html.escape(label)}</span>')

    bkm_html = (
        '<span class="save-status-pill mono" id="live-save-status">进度 0%</span>'
        '<button type="button" class="chip-btn" id="save-bookmark-btn" style="padding:3px 10px;font-size:12px" title="手动保存当前浏览位置书签">🔖 保存位置</button>'
        if show_bookmark
        else ""
    )

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
      <div class="context-right">
        {bkm_html}
        {right_note}
      </div>
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

    rules_md = (DOCS_DIR / "衡天量级体系【第三版·最新】.md").read_text(encoding="utf-8")
    materials_md = (DOCS_DIR / "材质与破坏能量数据库（新）.md").read_text(encoding="utf-8")

    rules_html_body, rules_toc, rules_sections = parse_markdown_document(rules_md, "rules", "rules.html")
    mat_html_body, mat_toc, mat_sections = parse_markdown_document(materials_md, "materials", "materials.html")

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
                "badge": "量级分类",
                "title": f"⊙ {t['code']} · {t['name']}（{t['family']}）",
                "code": t["code"],
                "pinyin": f"{t['code_pinyin']} {t['full_pinyin']}",
                "url": f"tier/{t['slug']}.html",
                "text": f"能量/数学刻度：{t['energy']} ｜ 覆盖尺度：{t['scale']} ｜ 模型：{t['model']} ｜ 说明：{t['notes']}",
            }
        )

    chars_for_index = formal_chars if formal_chars else demo_chars
    is_demo_idx = len(formal_chars) == 0
    for c in chars_for_index:
        t_obj = next((x for x in tiers if x["slug"] == c["tier_slug"]), None)
        t_label = f"⊙{t_obj['code']} {t_obj['name']}" if t_obj else "待定"
        url_target = f"characters.html#demo-{c['slug']}" if is_demo_idx else f"character/{c['slug']}.html"
        search_items.append(
            {
                "type": "char",
                "badge": "角色示例" if is_demo_idx else "角色分类",
                "title": f"{c['name']}（{c.get('series', '')}）· {t_label}",
                "code": t_obj["code"] if t_obj else "",
                "pinyin": f"{c.get('pinyin', '')} {c.get('initial', '')}",
                "url": url_target,
                "text": f"{c.get('full_writing', '')} {c.get('summary', '')} ｜ 七维：{json.dumps(c.get('dims', {}), ensure_ascii=False)}",
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
        <div class="hero-eyebrow mono">⊙ HENGTIAN MULTIDIMENSIONAL SCALE · THIRD EDITION (LATEST)</div>
        <h1 class="hero-title">衡天<span class="sun-mark">⊙</span> 多维战力量级与破坏能量百科</h1>
        <p class="hero-desc">
          围绕<strong>角色</strong>（支持<strong>首字母 A–Z</strong> 与<strong>量级从小到大</strong>双排序）与<strong>量级</strong>（按<strong>从小到大</strong>完整排布）两大分类构建；一字不漏全文展示最新<strong>《衡天⊙ 多维战力量级体系（第三版）》</strong>与<strong>《材质与破坏能量数据库（第二版）》</strong>，内置全站搜索、浏览进度自动记忆与智能返回。
        </p>
        <div class="hero-actions">
          <a class="btn btn-primary" href="./characters.html">进入角色分类 ›</a>
          <a class="btn btn-primary" href="./tiers.html">浏览 {tier_count} 档量级天梯 ›</a>
          <a class="btn btn-ghost" href="./rules.html">《衡天⊙ 第三版》全文</a>
          <a class="btn btn-ghost" href="./materials.html">《材质能量库》全文</a>
        </div>
        <div class="hero-metrics">
          <div class="metric-chip">
            <div class="metric-val mono">角色分类</div>
            <div class="metric-label">首字母 A–Z &amp; 量级从小到大</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">量级分类</div>
            <div class="metric-label">97+1 档按从小到大排列</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">第三版·最新</div>
            <div class="metric-label">新增完整书写与归因审查等通则</div>
          </div>
          <div class="metric-chip">
            <div class="metric-val mono">100% 全文</div>
            <div class="metric-label">两部核心标准无删减直出</div>
          </div>
        </div>
      </div>
    </section>

    <div class="container" style="padding-bottom:42px">
      <section class="portal-section">
        <div class="section-head">
          <h2 class="section-title"><span class="dot"></span>两大核心分类（角色 · 量级）</h2>
          <span class="section-sub">角色支持「首字母 A–Z + 量级从小到大」双排序 ｜ 量级按「从小到大」递增排布</span>
        </div>
        <div class="portal-grid">
          <a class="portal-card" href="./characters.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-characters.jpg')">
              <span class="portal-tag mono">CATEGORY 01 · 角色分类</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>角色档案分类</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">采用第三版<strong>完整书写规范</strong>、<strong>七维战力面板（破·控·域·御·速·算·性）</strong>与浑仪星盘图呈现角色实力。支持<strong>按量级从小到大</strong>与<strong>按拼音首字母 A–Z</strong>自由切换。</p>
              <div class="portal-features">
                <span class="mini-chip">↑ 按量级从小到大</span>
                <span class="mini-chip">A–Z 按首字母排序</span>
                <span class="mini-chip">七维星盘与完整书写</span>
              </div>
            </div>
          </a>

          <a class="portal-card" href="./tiers.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-tiers.jpg')">
              <span class="portal-tag mono">CATEGORY 02 · 量级分类</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>量级标尺分类（{tier_count} 档）</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">严格按<strong>量级从小到大</strong>递增排列，完整涵盖昆虫级（5×10⁻⁵ J）至论天最上（莱茵哈特—伯克利基数）。支持分区卡片、连续天梯与紧凑总表三种视图，一键直达对应规则章节。</p>
              <div class="portal-features">
                <span class="mini-chip">↑ 从小到大递增（#01→#97）</span>
                <span class="mini-chip">分区 / 连续天梯 / 总表</span>
                <span class="mini-chip">直链第三版条文</span>
              </div>
            </div>
          </a>
        </div>
      </section>

      <section class="portal-section" style="padding-top:14px">
        <div class="section-head">
          <h2 class="section-title"><span class="dot"></span>网站标准与规则（全文无删减展示）</h2>
          <span class="section-sub">左侧章节导航同步高亮 · 支持文内查找定位、字号缩放、宽屏表格与自动断点续读</span>
        </div>
        <div class="portal-grid">
          <a class="portal-card" href="./rules.html">
            <div class="portal-banner" style="background-image:url('./static/img/hero-hengtian.jpg')">
              <span class="portal-tag mono">STANDARD 01 · 最新第三版全文</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>《衡天⊙ 多维战力量级体系（第三版）》</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">1,445 行最新原文无删减展示：涵盖第三版新增<strong>完整书写原则</strong>、<strong>0.14.2 归因与知情度审查</strong>、<strong>超长篇自行通读流程</strong>、<strong>7.9 层级轴必检</strong>及全部十一部分量级与大基数标准。</p>
              <div class="portal-features">
                <span class="mini-chip">第三版·最新全文</span>
                <span class="mini-chip">{len(rules_toc)} 个章节锚点</span>
                <span class="mini-chip">阅读进度自动保存</span>
              </div>
            </div>
          </a>

          <a class="portal-card" href="./materials.html">
            <div class="portal-banner" style="background-image:url('./static/img/banner-materials.jpg')">
              <span class="portal-tag mono">STANDARD 02 · 物理数据库全文</span>
            </div>
            <div class="portal-body">
              <h3 class="portal-title"><span>《材质与破坏能量数据库（第二版）》</span><span style="color:var(--accent-gold)">→</span></h3>
              <p class="portal-desc">416 行原文无删减展示：破坏动词双轴定性、斩陨规则、常规物质粉碎能量密度、抗压/剪切/断裂韧性、相变潜热、行星/白矮星/中子星引力束缚能、撞击成坑与云层推算。</p>
              <div class="portal-features">
                <span class="mini-chip">416 行原文无删减</span>
                <span class="mini-chip">宽屏/横向滚表适配</span>
                <span class="mini-chip">与主体系双向互链</span>
              </div>
            </div>
          </a>
        </div>
      </section>

      <section class="resume-hub" id="home-resume-hub" aria-label="浏览进度保存与断点续读">
        <div class="section-head" style="margin-bottom:8px">
          <h2 class="section-title"><span class="dot"></span>浏览进度保存与断点续读</h2>
          <span class="section-sub">正在读取本地进度…</span>
        </div>
      </section>

      <section class="scale-ribbon-section">
        <div class="section-head">
          <h2 class="section-title"><span class="dot"></span>衡天⊙ 全域刻度速览带（由小到大）</h2>
          <a href="./tiers.html" style="font-size:13.5px">查看完整 97 档递增天梯 →</a>
        </div>
        <div class="scale-track">
          <a class="scale-node" style="--node-color:var(--dom-terrestrial)" href="./tier/insect.html">
            <span class="scale-node-range mono">#01 · ⊙虫 → ⊙表☆</span>
            <span class="scale-node-title">地表与常规目标区</span>
            <span class="scale-node-energy mono">5×10⁻⁵ J ～ 1.63×10³⁰ J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-stellar)" href="./tier/star-std.html">
            <span class="scale-node-range mono">#43 · ⊙星▽ → ⊙恒☆</span>
            <span class="scale-node-title">天体自引力束缚区</span>
            <span class="scale-node-energy mono">4.87×10³⁰ J ～ 2.28×10⁴² J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-cosmic)" href="./tier/system-std.html">
            <span class="scale-node-range mono">#57 · ⊙系▽ → ⊙构☆</span>
            <span class="scale-node-title">球面/盘面通量覆盖区</span>
            <span class="scale-node-energy mono">3.7×10⁴⁹ J ～ 3.7×10⁷⁶ J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--accent-gold)" href="./tier/universe-extreme.html">
            <span class="scale-node-range mono">#79 · ⊙宇▽ → ⊙宇☆</span>
            <span class="scale-node-title">宇宙五档（含极宇宙◆）</span>
            <span class="scale-node-energy mono">3.7×10⁷⁶ J ～ 10↑↑3 倍宇○</span>
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

    # 3. Generate tiers.html — Strictly 从小到大!
    group_map = {g["id"]: g for g in groups}
    ssr_tier_blocks = []
    for g in groups:
        g_tiers = [t for t in tiers if t["group_id"] == g["id"]]
        cards = []
        for t in g_tiers:
            ord_str = "兜底暂存" if t.get("unranked") else f"#{t['order']:02d} / 97"
            bar_pct = 0 if t.get("unranked") else max(3, round((t["order"] / 97) * 100))
            cards.append(
                f"""
            <a class="tier-card" data-domain="{t['domain']}" href="./tier/{t['slug']}.html">
              <div class="tier-card-top">
                <span class="tier-code-badge mono">⊙ {html.escape(t['code'])}</span>
                <span class="tier-order-num mono">{ord_str}</span>
              </div>
              <div class="tier-card-name">
                <span>{html.escape(t['name'])}</span>
                <span style="font-size:12px;font-weight:500;color:var(--text-muted)">{html.escape(t['family'])}</span>
              </div>
              <div class="tier-energy-line mono">{html.escape(t['energy'])}</div>
              <div class="tier-scale-line">{html.escape(t['scale'])}</div>
              <div class="tier-scale-meter"><span style="width:{bar_pct}%"></span></div>
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
        <h1 class="page-hero-title"><span>量级分类总览</span><span class="brand-badge mono">⊙ {tier_count} 正式档位 + 待定 · 从小到大</span></h1>
        <p class="page-hero-desc">依据最新《衡天⊙ 多维战力量级体系（第三版）》，将全部量级标尺按<strong>从小到大（#01 昆虫级 → #97 论天最上）</strong>清晰排列，点击任意档位可查阅完整书写格式与对应规则原文。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:54px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span class="char-rating-pill mono" style="font-size:13px;padding:6px 13px">↑ 排列顺序：量级从小到大（#01 虫 → #97 天·最）</span>
          </div>

          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1;justify-content:flex-end">
            <div class="filter-input-wrap">
              <span class="filter-input-icon">🔍</span>
              <input type="search" class="filter-input" id="tier-filter-input" placeholder="筛选代字、名称、能量阈值（如 宇◆、10⁴¹、阿克曼）…">
              <button type="button" class="filter-clear-btn" id="tier-filter-clear" aria-label="清空">✕</button>
            </div>
            <div class="segmented-group" role="group" aria-label="视图切换">
              <button type="button" class="seg-btn active" data-tier-view="card">分区卡片</button>
              <button type="button" class="seg-btn" data-tier-view="flat">连续天梯</button>
              <button type="button" class="seg-btn" data-tier-view="table">紧凑总表</button>
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
          <span class="mono" id="tier-result-count" style="font-size:12.5px;color:var(--text-muted)">按量级从小到大显示 {len(tiers)} 个档位</span>
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
                [("量级分类总览（从小到大）", "")],
                '<a href="./rules.html#part-11">对照第十一部分全链条总览 ↗</a>',
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
    for t in tiers:
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
              可前往 <a href="../characters.html">角色分类页</a> 浏览第三版示例卡或录入新角色。
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
        full_write_example = f"⊙{t['code']}（{t['name']}：{t['scale']}，{t['energy']}）"

        detail_body = f"""
        <div class="container detail-wrap">
          <article class="detail-card">
            <div class="detail-header">
              <div>
                <div class="detail-code-pill mono">⊙ {html.escape(t['code'])}</div>
                <h1 class="detail-title">{html.escape(t['name'])} <span style="font-size:18px;font-weight:500;color:var(--text-muted)">· {html.escape(t['family'])}</span></h1>
              </div>
              <div style="display:flex;gap:10px;flex-wrap:wrap">
                <a class="btn btn-primary" href="../rules.html#{html.escape(rule_anchor_id)}" title="跳转至：{html.escape(rule_sec_label)}">📖 查阅第三版原文：{html.escape(rule_sec_label[:18])}{'…' if len(rule_sec_label) > 18 else ''} ↗</a>
                <a class="btn btn-surface" href="../tiers.html">返回量级分类</a>
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
                <div class="spec-label">第三版「完整书写」推荐展开格式（1.5 节规范）</div>
                <div class="spec-value mono" style="font-size:14px;color:var(--accent-cyan)">{html.escape(full_write_example)}</div>
              </div>
              <div class="spec-box wide">
                <div class="spec-label">判定细则与注意事项</div>
                <div class="spec-value" style="font-weight:400;color:var(--text-secondary);line-height:1.75">{html.escape(t['notes'])}</div>
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

    # 5. Generate characters.html — 首字母 A–Z & 量级从小到大
    chars_body = f"""
    <section class="page-hero">
      <div class="page-hero-bg" style="background-image:url('./static/img/banner-characters.jpg')"></div>
      <div class="page-hero-mask"></div>
      <div class="container page-hero-inner">
        <h1 class="page-hero-title"><span>角色档案分类</span><span class="brand-badge mono">首字母 A–Z &amp; 量级从小到大</span></h1>
        <p class="page-hero-desc">按《衡天⊙ 多维战力量级体系（第三版）》展示角色主档、完整书写结论及破·控·域·御·速·算·性七维细分评定。支持<strong>按量级从小到大</strong>与<strong>按角色首字母 A–Z</strong>两种排序方式。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:56px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span style="font-size:13px;color:var(--text-muted);font-weight:600">角色排序：</span>
            <div class="segmented-group" role="group" aria-label="角色排序切换">
              <button type="button" class="seg-btn active" data-char-sort="asc">↑ 按量级从小到大</button>
              <button type="button" class="seg-btn" data-char-sort="alpha">A–Z 按首字母排序</button>
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
            <button type="button" class="chip-btn" id="char-demo-toggle">✦ 切换示例卡显示</button>
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

      <div id="char-demo-banner-slot"></div>

      <div class="alpha-bar" id="char-alpha-bar">
        <div class="alpha-letters" id="char-alpha-letters"></div>
        <span style="font-size:12px;color:var(--text-muted)">点击字母快速定位对应角色分组</span>
      </div>

      <div id="chars-explorer-mount"></div>
    </div>

    <!-- Demo Character 7D Inspection Modal -->
    <div class="modal-backdrop" id="demo-char-modal" role="dialog" aria-modal="true" aria-label="七维评定面板详情">
      <div class="modal-dialog">
        <div class="search-modal-head" style="justify-content:space-between">
          <strong>⊙ 衡天第三版 · 七维角色战力面板</strong>
          <button type="button" class="resume-toast-close" id="demo-char-close" aria-label="关闭">✕</button>
        </div>
        <div class="search-modal-body" id="demo-char-modal-body" style="padding:20px 22px"></div>
      </div>
    </div>
    """

    (ROOT / "characters.html").write_text(
        render_shell(
            title="角色分类",
            page_id="characters.html",
            page_type="chars",
            active_nav="chars",
            root_prefix="./",
            context_bar_html=make_context_bar(
                "./",
                "index.html",
                "首页",
                [("角色档案分类", "")],
                '<a href="./rules.html#sec-1-5">查看 1.5 节第三版完整书写规范 ↗</a>',
            ),
            body_html=chars_body,
            tier_count=tier_count,
            char_count=char_count,
        ),
        encoding="utf-8",
    )

    if formal_chars:
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

        rules_tab_cls = "doc-switch-tab active" if filename == "rules.html" else "doc-switch-tab"
        mat_tab_cls = "doc-switch-tab active" if filename == "materials.html" else "doc-switch-tab"

        doc_body = f"""
        <section class="page-hero">
          <div class="page-hero-bg" style="background-image:url('./static/img/{banner_img}')"></div>
          <div class="page-hero-mask"></div>
          <div class="container page-hero-inner">
            <h1 class="page-hero-title"><span>{html.escape(title)}</span><span class="brand-badge">网站标准与规则 · 全文展示</span></h1>
            <p class="page-hero-desc">{html.escape(subtitle)}</p>
            <div class="doc-switcher-bar" role="tablist" aria-label="标准与规则文档切换">
              <a class="{rules_tab_cls}" href="./rules.html">📜 《衡天⊙ 多维战力量级体系（第三版·最新）》全文</a>
              <a class="{mat_tab_cls}" href="./materials.html">⚗️ 《材质与破坏能量数据库（第二版）》全文</a>
            </div>
          </div>
        </section>

        <div class="container doc-layout">
          <aside class="doc-sidebar" id="doc-sidebar" aria-label="文档章节目录">
            <div class="toc-header">
              <div class="toc-title-row">
                <span>📑 章节目录（{len(toc_list)} 节）</span>
                <span class="toc-pct mono" id="toc-progress-pct">0%</span>
              </div>
              <input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选章节标题…">
            </div>
            <nav class="toc-nav" id="toc-nav">
              {"".join(toc_items_html)}
            </nav>
          </aside>

          <article class="doc-article-card">
            <div class="doc-reader-toolbar">
              <span>📌 原文 100% 无删减直出（<strong>{raw_md_len:,}</strong> 字符 · <strong>{len(toc_list)}</strong> 个小节锚点 · 自动保存阅读位置）</span>
              <div class="doc-reader-tools">
                <div class="doc-find-wrap" title="在当前全文内查找并跳转段落/表格行">
                  <span>🔎</span>
                  <input type="search" class="doc-find-input" id="doc-find-input" placeholder="本文内查找并定位…">
                  <span class="mono" id="doc-find-count" style="font-size:11.5px;color:var(--accent-gold)"></span>
                  <button type="button" class="chip-btn" id="doc-find-next" style="padding:2px 8px;font-size:11.5px">下一处 ↓</button>
                </div>
                <button type="button" class="chip-btn" id="doc-font-dec" style="padding:3px 9px" title="缩小正文字号">A-</button>
                <button type="button" class="chip-btn" id="doc-font-inc" style="padding:3px 9px" title="放大正文字号">A+</button>
                <button type="button" class="chip-btn" id="doc-wide-toggle" style="padding:3px 10px" title="展开宽屏表格阅读模式">↔ 宽屏表格</button>
              </div>
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
                    [("标准与规则全文", ""), (title, "")],
                    f'<a href="./{companion_link}">切换：{html.escape(companion_label)} ↗</a>',
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
        title="《衡天⊙ 多维战力量级体系（第三版）》",
        subtitle="2026-10-23 最新第三版全文：新增完整书写原则、0.14.2 归因与知情度审查、超长篇自行通读流程、0.6 体量不等于破坏、6.3 一次作用计数认定、7.9 层级轴必检，完整收录全部十一部分及附则。",
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
        companion_label="《衡天⊙ 多维战力量级体系（第三版）》",
    )

    # 7. Generate Dedicated Search Page: search.html
    search_body = f"""
    <section class="page-hero">
      <div class="page-hero-bg" style="background-image:url('./static/img/banner-tiers.jpg')"></div>
      <div class="page-hero-mask"></div>
      <div class="container page-hero-inner">
        <h1 class="page-hero-title"><span>全站即时检索中心</span><span class="brand-badge mono">{len(search_items)} 条索引块</span></h1>
        <p class="page-hero-desc">跨角色分类、量级分类、《衡天⊙ 多维战力量级体系（第三版）》及《材质与破坏能量数据库》全章节毫秒级检索。</p>
      </div>
    </section>

    <div class="container" style="padding:24px 22px 60px;max-width:980px">
      <div class="toolbar-panel" style="margin-top:0">
        <div style="display:flex;gap:10px;align-items:center">
          <span style="font-size:20px">🔍</span>
          <input type="search" id="dedicated-search-input" class="filter-input" style="max-width:none;font-size:15.5px;padding:11px 16px" placeholder="输入多个关键词空格分隔，例如：归因 知情度 / 完整书写 / 白矮星 束缚能 / 宇◆ / 0#…" autofocus>
        </div>
        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-page-search-type="all">全部类别</button>
            <button type="button" class="chip-btn" data-page-search-type="char">角色分类（{len(chars_for_index)}）</button>
            <button type="button" class="chip-btn" data-page-search-type="tier">量级分类（{len(tiers)}）</button>
            <button type="button" class="chip-btn" data-page-search-type="rules">衡天体系第三版（{len(rules_sections)} 节）</button>
            <button type="button" class="chip-btn" data-page-search-type="materials">材质破坏能量库（{len(mat_sections)} 节）</button>
          </div>
          <span class="mono" id="dedicated-search-count" style="font-size:12.5px;color:var(--text-muted)"></span>
        </div>
        <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;font-size:12.5px;color:var(--text-muted)">
          <span>热门速查词：</span>
          <button type="button" class="chip-btn" data-hot-query="完整书写">完整书写原则(v3)</button>
          <button type="button" class="chip-btn" data-hot-query="归因与知情度">0.14.2 归因审查(v3)</button>
          <button type="button" class="chip-btn" data-hot-query="超长篇自行通读">超长篇通读流程(v3)</button>
          <button type="button" class="chip-btn" data-hot-query="层级轴必检">7.9 层级轴必检(v3)</button>
          <button type="button" class="chip-btn" data-hot-query="宇◆">宇◆（极宇宙）</button>
          <button type="button" class="chip-btn" data-hot-query="F*">通量常数 F*</button>
          <button type="button" class="chip-btn" data-hot-query="0#">0#（零尖）</button>
          <button type="button" class="chip-btn" data-hot-query="中子星">中子星外壳/束缚能</button>
          <button type="button" class="chip-btn" data-hot-query="花岗岩">花岗岩粉碎/汽化</button>
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
            context_bar_html=make_context_bar(
                "./", "index.html", "首页", [("全站搜索", "")], show_bookmark=False
            ),
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
