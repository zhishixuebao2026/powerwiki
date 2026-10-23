#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Generator v4.0 (Celestial Monograph UI)
- Canonical Standard 1: data/docs/衡天量级体系【第三版·最新】.md (100% Verbatim Full Text)
- Canonical Standard 2: data/docs/材质与破坏能量数据库（新）.md (100% Verbatim Full Text)
- Tiers Category: Strictly ordered 从小到大 (#01 -> #97)
- Characters Category: Dual sorting (按量级从小到大 & 按首字母 A–Z)
- UI v4.0: Zero Emojis · Bespoke Vector Astrolabe · 120fps Scroll Architecture
"""

import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"

# Crisp 1.65px-stroke monochrome SVG icons (Zero raw system emojis)
SVG = {
    "search": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "search_sm": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "history": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/></svg>',
    "sun": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "menu": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="4" x2="20" y1="7" y2="7"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="17" y2="17"/></svg>',
    "close": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    "back": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg>',
    "up": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m18 15-6-6-6 6"/></svg>',
    "arrow_ur": '<svg class="svg-icon sm tier-card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>',
    "toc": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
    "bookmark": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>',
    "book": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"/></svg>',
    "layers": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/></svg>',
    "asc": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m3 8 4-4 4 4"/><path d="M7 4v16"/><path d="M11 12h4"/><path d="M11 16h7"/><path d="M11 20h10"/></svg>',
}

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


def build_hero_astrolabe_svg() -> str:
    """Generate a razor-sharp architectural SVG Celestial Astrolabe for the Home Hero."""
    cx, cy = 200, 200
    ticks = []
    for deg in range(0, 360, 6):
        rad = math.radians(deg)
        r_outer = 166
        r_inner = 156 if deg % 30 == 0 else (160 if deg % 15 == 0 else 163)
        stroke_op = "0.42" if deg % 30 == 0 else "0.18"
        x1 = cx + r_inner * math.cos(rad)
        y1 = cy + r_inner * math.sin(rad)
        x2 = cx + r_outer * math.cos(rad)
        y2 = cy + r_outer * math.sin(rad)
        ticks.append(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="currentColor" stroke-opacity="{stroke_op}" stroke-width="1"/>'
        )

    dims = ["破", "控", "域", "御", "速", "算", "性"]
    hept_pts = []
    star_pts = []
    dim_nodes = []
    r_hept = 96
    for i, label in enumerate(dims):
        ang = -math.pi / 2 + (i * 2 * math.pi) / 7
        px = cx + r_hept * math.cos(ang)
        py = cy + r_hept * math.sin(ang)
        hept_pts.append(f"{px:.1f},{py:.1f}")
        lx = cx + (r_hept + 22) * math.cos(ang)
        ly = cy + (r_hept + 22) * math.sin(ang) + 4
        dim_nodes.append(
            f'<line x1="{cx}" y1="{cy}" x2="{px:.1f}" y2="{py:.1f}" stroke="currentColor" stroke-opacity="0.12" stroke-width="1"/>'
            f'<circle cx="{px:.1f}" cy="{py:.1f}" r="3.2" fill="var(--accent-gold)"/>'
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="middle" fill="var(--text-secondary)" font-size="11.5" font-weight="600">{label}</text>'
        )

    # {7/2} heptagram star polygon
    for k in range(8):
        idx = (k * 2) % 7
        star_pts.append(hept_pts[idx])

    return f"""
    <svg class="astrolabe-svg" viewBox="0 0 400 400" aria-hidden="true" style="color:var(--accent-gold)">
      <defs>
        <radialGradient id="coreGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="var(--accent-gold)" stop-opacity="0.24"/>
          <stop offset="65%" stop-color="var(--accent-gold)" stop-opacity="0.04"/>
          <stop offset="100%" stop-color="var(--accent-gold)" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <circle cx="200" cy="200" r="145" fill="url(#coreGlow)"/>
      <line x1="20" y1="200" x2="380" y2="200" stroke="currentColor" stroke-opacity="0.11" stroke-width="1"/>
      <line x1="200" y1="20" x2="200" y2="380" stroke="currentColor" stroke-opacity="0.11" stroke-width="1"/>

      <g class="orbit-slow">
        <circle cx="200" cy="200" r="166" fill="none" stroke="currentColor" stroke-opacity="0.22" stroke-width="1"/>
        <circle cx="200" cy="200" r="148" fill="none" stroke="currentColor" stroke-opacity="0.14" stroke-dasharray="3 5" stroke-width="1"/>
        {"".join(ticks)}
      </g>

      <g class="orbit-reverse">
        <ellipse cx="200" cy="200" rx="134" ry="52" transform="rotate(-24 200 200)" fill="none" stroke="var(--accent-blue)" stroke-opacity="0.22" stroke-width="1"/>
        <ellipse cx="200" cy="200" rx="134" ry="52" transform="rotate(36 200 200)" fill="none" stroke="currentColor" stroke-opacity="0.18" stroke-width="1"/>
      </g>

      <polygon points="{' '.join(hept_pts)}" fill="var(--accent-gold-soft)" stroke="currentColor" stroke-opacity="0.38" stroke-width="1.2"/>
      <polyline points="{' '.join(star_pts)}" fill="none" stroke="currentColor" stroke-opacity="0.22" stroke-width="1"/>
      {"".join(dim_nodes)}

      <circle cx="200" cy="200" r="26" fill="var(--bg-surface-1)" stroke="currentColor" stroke-opacity="0.55" stroke-width="1.4"/>
      <circle cx="200" cy="200" r="4.5" fill="var(--accent-gold)"/>
    </svg>"""


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
        f'<button type="button" class="dock-btn dock-toc-btn" id="dock-toc-btn" title="展开/收起章节目录">{SVG["toc"]}</button>'
        if has_toc_drawer
        else ""
    )

    char_badge_label = str(char_count) if char_count > 0 else "6"

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
          <span class="brand-title">衡天 PowerWiki</span>
          <span class="brand-badge mono">v3.0</span>
        </span>
      </a>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        <a class="{nav_cls('home')}" href="{r}index.html">首页</a>
        <a class="{nav_cls('chars')}" href="{r}characters.html">角色 <span class="nav-count mono">{char_badge_label}</span></a>
        <a class="{nav_cls('tiers')}" href="{r}tiers.html">量级 <span class="nav-count mono">{tier_count}</span></a>
        <a class="{nav_cls('rules')}" href="{r}rules.html">衡天体系</a>
        <a class="{nav_cls('materials')}" href="{r}materials.html">材质数据库</a>
      </nav>

      <div class="header-actions">
        <button type="button" class="search-trigger" id="global-search-trigger" aria-label="打开全站搜索">
          <span class="search-trigger-left">
            {SVG['search_sm']}
            <span class="search-trigger-placeholder">搜索全站…</span>
          </span>
          <kbd class="kbd-hint">Ctrl K</kbd>
        </button>
        <button type="button" class="icon-btn" id="history-open-btn" title="浏览进度与最近足迹">
          {SVG['history']}
          <span class="dot-indicator"></span>
        </button>
        <button type="button" class="icon-btn" id="theme-toggle-btn" title="切换深浅色主题">
          {SVG['sun']}
        </button>
        <button type="button" class="icon-btn mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单">
          {SVG['menu']}
        </button>
      </div>
    </div>
  </header>

  <div class="drawer-backdrop" id="drawer-backdrop" aria-hidden="true"></div>

  {context_bar_html}

  <main style="flex:1">
    {body_html}
  </main>

  <div class="resume-toast" id="resume-toast" role="status" aria-live="polite">
    <span class="resume-toast-text" id="resume-toast-text">上次浏览位置</span>
    <button type="button" class="resume-toast-btn" id="resume-toast-btn">继续浏览</button>
    <button type="button" class="resume-toast-close" id="resume-toast-close" aria-label="关闭提示">{SVG['close']}</button>
  </div>

  <div class="floating-dock">
    {toc_dock_btn}
    <button type="button" class="dock-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页" title="返回上一页">{SVG['back']}</button>
    <button type="button" class="dock-btn" id="dock-top-btn" title="回到顶部">
      <svg class="progress-ring-svg" viewBox="0 0 40 40" aria-hidden="true">
        <circle class="progress-ring-circle" id="dock-progress-circle" cx="20" cy="20" r="18"></circle>
      </svg>
      {SVG['up']}
    </button>
  </div>

  <!-- Global Search Command Palette -->
  <div class="modal-backdrop" id="search-modal" role="dialog" aria-modal="true" aria-label="全站即时检索">
    <div class="modal-dialog">
      <div class="search-modal-head">
        <span style="color:var(--text-muted);display:inline-flex">{SVG['search']}</span>
        <input type="search" class="search-modal-input" id="search-modal-input" placeholder="搜索角色、量级代字（宇◆、恒○）、第三版规则或材质（归因、白矮星、花岗岩）…" autocomplete="off">
        <a href="{r}search.html" class="chip-btn">检索页 {SVG['arrow_ur']}</a>
        <button type="button" class="resume-toast-close" id="search-modal-close" aria-label="关闭">{SVG['close']}</button>
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
        <strong style="font-size:14.5px;display:inline-flex;align-items:center;gap:8px">{SVG['history']}<span>浏览进度与最近足迹</span></strong>
        <div style="display:flex;align-items:center;gap:8px">
          <button type="button" class="chip-btn" id="history-clear-btn">清空记录</button>
          <button type="button" class="resume-toast-close" id="history-close-btn" aria-label="关闭">{SVG['close']}</button>
        </div>
      </div>
      <div class="search-modal-body" id="history-modal-body"></div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div>
        <strong style="color:var(--text-primary);font-weight:600">衡天⊙ PowerWiki</strong>
        <span style="margin:0 6px;opacity:0.4">·</span>
        <span>《衡天⊙ 多维战力量级体系（第三版）》与《材质与破坏能量数据库（第二版）》</span>
      </div>
      <div class="footer-links">
        <a href="{r}index.html">首页</a>
        <a href="{r}characters.html">角色分类</a>
        <a href="{r}tiers.html">量级分类</a>
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
        f'<span class="save-status-pill mono" id="live-save-status">进度 0%</span>'
        f'<button type="button" class="chip-btn" id="save-bookmark-btn" title="保存当前阅读位置">{SVG["bookmark"]}<span>记录位置</span></button>'
        if show_bookmark
        else ""
    )

    return f"""
  <div class="context-bar">
    <div class="container context-inner">
      <div class="context-left">
        <button type="button" class="back-btn js-smart-back" data-fallback="{html.escape(fallback_rel)}" data-fallback-name="{html.escape(fallback_name)}">
          {SVG['back']}
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

    # 1. Build Search Index & Client Data Bundle
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

    # 2. Generate index.html (Sculptural Editorial Hero + Precision Bento Grid)
    astrolabe_svg = build_hero_astrolabe_svg()
    home_body = f"""
    <section class="hero-section">
      <div class="container hero-grid">
        <div>
          <div class="hero-eyebrow mono">
            <span class="hero-eyebrow-dot"></span>
            <span>HENGTIAN CODEX · EDITION III · 2026.10.23</span>
          </div>
          <h1 class="hero-title">衡天<span class="sun-mark serif-display">⊙</span> 多维战力量级与材质能量百科</h1>
          <p class="hero-desc">
            围绕<strong>角色档案</strong>（支持<strong>首字母 A–Z</strong> 与<strong>量级从小到大</strong>双排序）与<strong>量级标尺</strong>（严格按<strong>从小到大</strong>递增排布）构建；全文无删减收录最新<strong>《衡天⊙ 多维战力量级体系（第三版）》</strong>与<strong>《材质与破坏能量数据库（第二版）》</strong>。
          </p>

          <button type="button" class="hero-command-bar js-open-search" aria-label="打开全站快速检索">
            <span style="display:inline-flex;align-items:center;gap:10px">
              {SVG['search']}
              <span>检索角色、量级代字（宇◆、恒○）、第三版通则或材质参数…</span>
            </span>
            <kbd class="kbd-hint">Ctrl K</kbd>
          </button>

          <div class="hero-actions">
            <a class="btn btn-primary" href="./tiers.html">浏览 {tier_count} 档量级标尺 {SVG['arrow_ur']}</a>
            <a class="btn btn-gold" href="./characters.html">进入角色分类 {SVG['arrow_ur']}</a>
            <a class="btn btn-ghost" href="./rules.html">《衡天⊙ 第三版》全文</a>
            <a class="btn btn-ghost" href="./materials.html">《材质能量库》全文</a>
          </div>
        </div>

        <div class="astrolabe-stage">
          <div class="astrolabe-card">
            <span class="astrolabe-corner tl mono">F* = 3.04×10²⁰ J/m²</span>
            <span class="astrolabe-corner tr mono">⊙ SCALE 01 → 97</span>
            {astrolabe_svg}
            <span class="astrolabe-corner bl mono">5×10⁻⁵ J → 8×10¹⁰¹ J</span>
            <span class="astrolabe-corner br mono">f_ω · ℶ_κ = κ</span>
          </div>
        </div>
      </div>
    </section>

    <div class="container home-main">
      <div id="home-footprints-mount"></div>

      <section>
        <div class="section-head">
          <div>
            <span class="section-kicker mono">CORE ARCHIVES</span>
            <h2 class="section-title">核心分类目录</h2>
          </div>
          <span class="section-sub">角色支持「首字母 A–Z &amp; 量级从小到大」 ｜ 量级严格按「从小到大」递增</span>
        </div>

        <div class="bento-grid">
          <a class="bento-card" href="./characters.html">
            <div>
              <div class="bento-top" style="margin-bottom:14px">
                <span class="bento-index mono">01 / CHARACTER ARCHIVE</span>
                <span class="bento-arrow">{SVG['arrow_ur']}</span>
              </div>
              <h3 class="bento-title">角色档案分类</h3>
              <p class="bento-desc">依据第三版<strong>完整书写规范</strong>与<strong>破·控·域·御·速·算·性</strong>七维战力浑仪呈现角色定级，支持按主档<strong>量级从小到大</strong>与<strong>拼音首字母 A–Z</strong>自由切换。</p>
              <div class="bento-heptad-strip" aria-hidden="true">
                <span class="bento-heptad-pill">破</span>
                <span class="bento-heptad-pill">控</span>
                <span class="bento-heptad-pill">域</span>
                <span class="bento-heptad-pill">御</span>
                <span class="bento-heptad-pill">速</span>
                <span class="bento-heptad-pill">算</span>
                <span class="bento-heptad-pill">性</span>
              </div>
            </div>
            <div class="bento-meta-strip">
              <div class="tag-row">
                <span class="mini-chip">↑ 按量级从小到大</span>
                <span class="mini-chip">A–Z 按首字母排序</span>
                <span class="mini-chip">七维浑仪与证据标签</span>
              </div>
            </div>
          </a>

          <a class="bento-card" href="./tiers.html">
            <div>
              <div class="bento-top" style="margin-bottom:14px">
                <span class="bento-index mono">02 / 97-TIER SCALE</span>
                <span class="bento-arrow">{SVG['arrow_ur']}</span>
              </div>
              <h3 class="bento-title">量级标尺分类（{tier_count} 档）</h3>
              <p class="bento-desc">严格按<strong>量级从小到大（#01 昆虫级 → #97 论天最上）</strong>递增排布，完整覆盖常规破坏、天体束缚能、通量覆盖、FGH 函数层级与大基数公理。</p>
              <div class="bento-spectrum" aria-hidden="true">
                <span style="background:var(--dom-terrestrial)"></span>
                <span style="background:var(--dom-stellar)"></span>
                <span style="background:var(--dom-cosmic)"></span>
                <span style="background:var(--accent-gold)"></span>
                <span style="background:var(--dom-fgh)"></span>
                <span style="background:var(--dom-beyond)"></span>
              </div>
            </div>
            <div class="bento-meta-strip">
              <div class="tag-row">
                <span class="mini-chip">↑ 严格从小到大排列</span>
                <span class="mini-chip">分区 / 连续天梯 / 总表</span>
                <span class="mini-chip">直链第三版条文</span>
              </div>
            </div>
          </a>
        </div>
      </section>

      <section>
        <div class="section-head">
          <div>
            <span class="section-kicker mono">CANONICAL MONOGRAPHS · UNABRIDGED</span>
            <h2 class="section-title">标准与规则典籍（100% 全文展示）</h2>
          </div>
          <span class="section-sub">自动保存阅读进度与章节位置 · 点击卡片可断点续读</span>
        </div>

        <div class="bento-grid">
          <a class="bento-card" href="./rules.html">
            <div>
              <div class="bento-top" style="margin-bottom:14px">
                <span class="bento-index mono">STANDARD I · 1,445 LINES · {len(rules_toc)} SECTIONS</span>
                <span class="bento-arrow">{SVG['arrow_ur']}</span>
              </div>
              <h3 class="bento-title">《衡天⊙ 多维战力量级体系（第三版）》</h3>
              <p class="bento-desc">2026-10-23 最新第三版原文无删减直出：含新增<strong>完整书写原则</strong>、<strong>0.14.2 归因与知情度审查</strong>、<strong>超长篇自行通读流程</strong>、<strong>7.9 层级轴必检</strong>及全部十一部分标准。</p>
            </div>
            <div class="bento-progress-box" data-bento-progress="rules.html">
              <div class="bento-progress-head">
                <span data-prog-label>点击阅读完整无删减原文</span>
                <span class="mono" style="color:var(--accent-gold)" data-prog-pct>0%</span>
              </div>
              <div class="resume-bar-wrap"><div class="resume-bar-fill" data-prog-fill style="width:0%"></div></div>
            </div>
          </a>

          <a class="bento-card" href="./materials.html">
            <div>
              <div class="bento-top" style="margin-bottom:14px">
                <span class="bento-index mono">STANDARD II · 416 LINES · {len(mat_toc)} SECTIONS</span>
                <span class="bento-arrow">{SVG['arrow_ur']}</span>
              </div>
              <h3 class="bento-title">《材质与破坏能量数据库（第二版）》</h3>
              <p class="bento-desc">配套工程物理参数全文：破坏动词双轴定性、斩陨规则、物质粉碎能量密度、抗压/剪切/断裂韧性、相变潜热、白矮星/中子星引力束缚能与撞击成坑推算。</p>
            </div>
            <div class="bento-progress-box" data-bento-progress="materials.html">
              <div class="bento-progress-head">
                <span data-prog-label>点击阅读完整无删减原文</span>
                <span class="mono" style="color:var(--accent-gold)" data-prog-pct>0%</span>
              </div>
              <div class="resume-bar-wrap"><div class="resume-bar-fill" data-prog-fill style="width:0%"></div></div>
            </div>
          </a>
        </div>
      </section>

      <section>
        <div class="section-head">
          <div>
            <span class="section-kicker mono">LOGARITHMIC SPECTRUM</span>
            <h2 class="section-title">全域量级谱系速览（从小到大）</h2>
          </div>
          <a href="./tiers.html" style="font-size:13px;color:var(--accent-gold);display:inline-flex;align-items:center;gap:4px">查看全部 97 档标尺 {SVG['arrow_ur']}</a>
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
            <span class="scale-node-title">球面/盘面通量覆盖</span>
            <span class="scale-node-energy mono">3.7×10⁴⁹ J ～ 3.7×10⁷⁶ J</span>
          </a>
          <a class="scale-node" style="--node-color:var(--accent-gold)" href="./tier/universe-extreme.html">
            <span class="scale-node-range mono">#79 · ⊙宇▽ → ⊙宇☆</span>
            <span class="scale-node-title">宇宙五档（含宇◆）</span>
            <span class="scale-node-energy mono">3.7×10⁷⁶ J ～ 10↑↑3 倍宇○</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-fgh)" href="./tier/fgh-tower.html">
            <span class="scale-node-range mono">#84 · ⊙广·塔 → ⊙广·顶</span>
            <span class="scale-node-title">广义无限区（FGH）</span>
            <span class="scale-node-energy mono">f₃ 幂塔 → f_ω → 不可计算</span>
          </a>
          <a class="scale-node" style="--node-color:var(--dom-beyond)" href="./tier/beyond-sky-top.html">
            <span class="scale-node-range mono">#90 · ⊙外·门 → ⊙天·最</span>
            <span class="scale-node-title">论外与论天大基数</span>
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
            ord_str = "待定" if t.get("unranked") else f"#{t['order']:02d}"
            cards.append(
                f"""
            <a class="tier-card" data-domain="{t['domain']}" href="./tier/{t['slug']}.html">
              <div class="tier-card-top">
                <span class="tier-code-badge mono">⊙ {html.escape(t['code'])}</span>
                <span class="tier-order-num mono">{ord_str}</span>
              </div>
              <div class="tier-card-name">
                <span>{html.escape(t['name'])}</span>
                <span class="tier-family-tag">{html.escape(t['family'])}</span>
              </div>
              <div class="tier-energy-line mono">{html.escape(t['energy'])}</div>
              <div class="tier-scale-line">{html.escape(t['scale'])}</div>
              <div class="tier-card-foot">
                <span>{html.escape(t['model'])}</span>
                {SVG['arrow_ur']}
              </div>
            </a>"""
            )
        ssr_tier_blocks.append(
            f"""
        <section class="tier-group-block" id="group-{g['id']}">
          <div class="tier-group-header">
            <h2 class="tier-group-title">{html.escape(g['title'])}</h2>
            <span class="tier-group-sub">{html.escape(g['subtitle'])} · {len(g_tiers)} 档</span>
          </div>
          <div class="tier-grid">{"".join(cards)}</div>
        </section>"""
        )

    tiers_body = f"""
    <section class="page-hero">
      <div class="container page-hero-inner">
        <span class="page-kicker mono">CATEGORY 02 · TIER SCALE ARCHIVE</span>
        <h1 class="page-hero-title"><span>量级分类总览</span><span class="brand-badge mono">⊙ {tier_count} 档 + 待定 · 从小到大</span></h1>
        <p class="page-hero-desc">依据最新《衡天⊙ 多维战力量级体系（第三版）》，将全部量级标尺严格按<strong>从小到大（#01 昆虫级 → #97 论天最上）</strong>递增排列，点击任意档位可查阅完整书写展开格式与规则原文。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:60px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <span class="order-indicator mono">{SVG['asc']}<span>量级从小到大排列（#01 虫 → #97 天·最）</span></span>

          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;flex:1;justify-content:flex-end">
            <div class="filter-input-wrap">
              <span class="filter-input-icon">{SVG['search_sm']}</span>
              <input type="search" class="filter-input" id="tier-filter-input" placeholder="筛选代字、名称或能量（如 宇◆、10⁴¹、阿克曼）…">
              <button type="button" class="filter-clear-btn" id="tier-filter-clear" aria-label="清空">{SVG['close']}</button>
            </div>
            <div class="segmented-group" role="group" aria-label="视图切换">
              <button type="button" class="seg-btn active" data-tier-view="card">分区视图</button>
              <button type="button" class="seg-btn" data-tier-view="flat">连续天梯</button>
              <button type="button" class="seg-btn" data-tier-view="table">总表视图</button>
            </div>
          </div>
        </div>

        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-tier-seg="all">全部区间（{len(tiers)}）</button>
            <button type="button" class="chip-btn" data-tier-seg="inherited">目标式（虫→恒）</button>
            <button type="button" class="chip-btn" data-tier-seg="transition">跨体系过渡带</button>
            <button type="button" class="chip-btn" data-tier-seg="coverage">覆盖体系（系→宇）</button>
            <button type="button" class="chip-btn" data-tier-seg="fgh">广义无限（FGH）</button>
            <button type="button" class="chip-btn" data-tier-seg="beyond">论外与论天大基数</button>
          </div>
          <span class="mono" id="tier-result-count" style="font-size:12px;color:var(--text-muted);flex-shrink:0">{len(tiers)} / {len(tiers)} 档</span>
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
                [("量级分类（从小到大）", "")],
                f'<a href="./rules.html#part-11">对照第十一部分总表 {SVG["arrow_ur"]}</a>',
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
                    f'<a class="char-card" href="../character/{c["slug"]}.html"><h4 style="margin:0">{html.escape(c["name"])}</h4><div style="font-size:12.5px;color:var(--text-muted)">{html.escape(c.get("series",""))}</div></a>'
                    for c in chars_in_tier
                )
                + "</div>"
            )
        else:
            char_section_html = f"""
            <div style="background:var(--bg-subtle);border:1px solid var(--border-hairline);border-radius:10px;padding:16px 18px;color:var(--text-muted);font-size:13px;margin-top:10px">
              当前正式角色库暂无定级于 <strong style="color:var(--text-primary)">⊙ {html.escape(t['code'])}（{html.escape(t['name'])}）</strong> 的角色档案。
              可前往 <a href="../characters.html" style="color:var(--accent-gold)">角色分类页</a> 浏览第三版示例卡或录入新角色。
            </div>"""

        prev_html = (
            f'<a class="ladder-item prev" href="./{prev_t["slug"]}.html"><span class="ladder-dir">← 上一较低量级（#{prev_t["order"]:02d}）</span><span class="ladder-name">⊙ {html.escape(prev_t["code"])} · {html.escape(prev_t["name"])}</span><span class="mono" style="font-size:12px;color:var(--accent-gold)">{html.escape(prev_t["energy"])}</span></a>'
            if prev_t
            else '<div class="ladder-item prev" style="opacity:0.4"><span class="ladder-dir">← 已是最低起点</span><span class="ladder-name">无更低正式量级</span></div>'
        )
        next_html = (
            f'<a class="ladder-item next" href="./{next_t["slug"]}.html"><span class="ladder-dir">下一较高量级（#{next_t["order"]:02d}）→</span><span class="ladder-name">⊙ {html.escape(next_t["code"])} · {html.escape(next_t["name"])}</span><span class="mono" style="font-size:12px;color:var(--accent-gold)">{html.escape(next_t["energy"])}</span></a>'
            if next_t
            else '<div class="ladder-item next" style="opacity:0.4"><span class="ladder-dir">已是最高顶点 →</span><span class="ladder-name">无更高正式量级</span></div>'
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
                <h1 class="detail-title">{html.escape(t['name'])} <span style="font-size:17px;font-weight:400;color:var(--text-muted)">· {html.escape(t['family'])}</span></h1>
              </div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <a class="btn btn-primary" href="../rules.html#{html.escape(rule_anchor_id)}" title="跳转至：{html.escape(rule_sec_label)}">{SVG['book']}<span>第三版原文：{html.escape(rule_sec_label[:16])}{'…' if len(rule_sec_label) > 16 else ''}</span>{SVG['arrow_ur']}</a>
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
                <div class="spec-value mono" style="color:var(--accent-gold);font-size:16px">{html.escape(t['energy'])}</div>
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
                <div class="spec-value mono" style="font-size:13.5px;color:var(--accent-cyan)">{html.escape(full_write_example)}</div>
              </div>
              <div class="spec-box wide">
                <div class="spec-label">判定细则与注意事项</div>
                <div class="spec-value" style="font-weight:400;color:var(--text-secondary);line-height:1.75;font-size:14px">{html.escape(t['notes'])}</div>
              </div>
            </div>

            <section style="margin-top:24px">
              <h2 style="font-size:15.5px;margin:0 0 6px;font-weight:650">本量级收录角色（{len(chars_in_tier)}）</h2>
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
                    [("量级分类", "../tiers.html"), (f"⊙ {t['code']} · {t['name']}", "")],
                    f'<span class="mono">#{t["order"]:02d}</span>' if not t.get("unranked") else "待定",
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
      <div class="container page-hero-inner">
        <span class="page-kicker mono">CATEGORY 01 · CHARACTER DOSSIERS</span>
        <h1 class="page-hero-title"><span>角色档案分类</span><span class="brand-badge mono">首字母 A–Z &amp; 量级从小到大</span></h1>
        <p class="page-hero-desc">按《衡天⊙ 多维战力量级体系（第三版）》呈现角色主档、完整书写结论及破·控·域·御·速·算·性七维细分评定。支持<strong>按量级从小到大</strong>与<strong>按角色首字母 A–Z</strong>双模式排序。</p>
      </div>
    </section>

    <div class="container" style="padding-bottom:60px">
      <div class="toolbar-panel">
        <div class="toolbar-row">
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <span style="font-size:12px;color:var(--text-muted);font-weight:500">排序方式</span>
            <div class="segmented-group" role="group" aria-label="角色排序切换">
              <button type="button" class="seg-btn active" data-char-sort="asc">↑ 按量级从小到大</button>
              <button type="button" class="seg-btn" data-char-sort="alpha">A–Z 按首字母排序</button>
            </div>
          </div>

          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;flex:1;justify-content:flex-end">
            <select id="char-series-select" class="filter-input" style="max-width:190px" aria-label="按作品筛选">
              <option value="all">全部作品</option>
            </select>
            <div class="filter-input-wrap">
              <span class="filter-input-icon">{SVG['search_sm']}</span>
              <input type="search" class="filter-input" id="char-filter-input" placeholder="搜索角色名、拼音、出处、机制特性…">
            </div>
            <button type="button" class="chip-btn" id="char-demo-toggle">隐藏示例卡</button>
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
          <span class="mono" id="char-result-count" style="font-size:12px;color:var(--text-muted);flex-shrink:0">收录 {char_count} 位</span>
        </div>
      </div>

      <div id="char-demo-banner-slot"></div>

      <div class="alpha-bar" id="char-alpha-bar">
        <span class="mono" style="font-size:11px;color:var(--accent-gold);font-weight:600;flex-shrink:0">A–Z</span>
        <div class="alpha-letters" id="char-alpha-letters"></div>
      </div>

      <div id="chars-explorer-mount"></div>
    </div>

    <!-- Demo Character 7D Inspection Modal -->
    <div class="modal-backdrop" id="demo-char-modal" role="dialog" aria-modal="true" aria-label="七维评定面板详情">
      <div class="modal-dialog">
        <div class="search-modal-head" style="justify-content:space-between">
          <strong style="font-size:14.5px">⊙ 衡天第三版 · 七维角色战力档案</strong>
          <button type="button" class="resume-toast-close" id="demo-char-close" aria-label="关闭">{SVG['close']}</button>
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
                f'<a href="./rules.html#sec-1-5">1.5 节完整书写规范 {SVG["arrow_ur"]}</a>',
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
                f'<tr><th style="width:92px">维度「{k}」</th><td>{format_inline_md(c.get("dims", {}).get(k, "〔缺〕"))}</td></tr>'
                for k in ["破", "控", "域", "御", "速", "算", "性"]
            )
            c_body = f"""
            <div class="container detail-wrap">
              <article class="detail-card">
                <div class="detail-header">
                  <div>
                    <div class="detail-code-pill mono">⊙ {html.escape(t_obj['code'])} · {html.escape(t_obj['name'])}</div>
                    <h1 class="detail-title">{html.escape(c['name'])}</h1>
                    <div style="color:var(--text-muted);margin-top:6px;font-size:13px">{html.escape(c.get('series', ''))} · {html.escape(c.get('realm', ''))}</div>
                  </div>
                  <a class="btn btn-surface" href="../tier/{t_obj['slug']}.html">所属量级详情 {SVG['arrow_ur']}</a>
                </div>
                <p style="font-size:14.5px;color:var(--text-secondary)">{html.escape(c.get('summary', ''))}</p>
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
                        [("角色分类", "../characters.html"), (c["name"], "")],
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
        kicker: str,
        title: str,
        subtitle: str,
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
          <div class="container page-hero-inner">
            <span class="page-kicker mono">{html.escape(kicker)}</span>
            <h1 class="page-hero-title"><span>{html.escape(title)}</span><span class="brand-badge">全文无删减</span></h1>
            <p class="page-hero-desc">{html.escape(subtitle)}</p>
            <div class="doc-switcher-bar" role="tablist" aria-label="标准与规则文档切换">
              <a class="{rules_tab_cls}" href="./rules.html">{SVG['book']}<span>《衡天⊙ 多维战力量级体系（第三版）》全文</span></a>
              <a class="{mat_tab_cls}" href="./materials.html">{SVG['layers']}<span>《材质与破坏能量数据库（第二版）》全文</span></a>
            </div>
          </div>
        </section>

        <div class="container doc-layout">
          <aside class="doc-sidebar" id="doc-sidebar" aria-label="文档章节目录">
            <div class="toc-header">
              <div class="toc-title-row">
                <span style="display:inline-flex;align-items:center;gap:6px">{SVG['toc']}<span>章节目录（{len(toc_list)}）</span></span>
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
              <span>原文完整直出 · <strong style="color:var(--text-primary)">{raw_md_len:,}</strong> 字符 · <strong style="color:var(--text-primary)">{len(toc_list)}</strong> 节锚点 · 自动记录进度</span>
              <div class="doc-reader-tools">
                <div class="doc-find-wrap" title="在当前全文内查找并跳转段落/表格行">
                  <span style="color:var(--text-muted);display:inline-flex">{SVG['search_sm']}</span>
                  <input type="search" class="doc-find-input" id="doc-find-input" placeholder="文内查找定位…">
                  <span class="mono" id="doc-find-count" style="font-size:11px;color:var(--accent-gold)"></span>
                  <button type="button" class="chip-btn" id="doc-find-next" style="height:22px;padding:0 7px;font-size:11px">下一处</button>
                </div>
                <button type="button" class="chip-btn" id="doc-font-dec" title="缩小正文字号">A-</button>
                <button type="button" class="chip-btn" id="doc-font-inc" title="放大正文字号">A+</button>
                <button type="button" class="chip-btn" id="doc-wide-toggle" title="切换宽屏阅读模式">宽屏</button>
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
                    f'<a href="./{companion_link}">切换：{html.escape(companion_label)} {SVG["arrow_ur"]}</a>',
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
        kicker="STANDARD MONOGRAPH I · EDITION III (2026-10-23)",
        title="《衡天⊙ 多维战力量级体系（第三版）》",
        subtitle="最新第三版原文无删减展示：新增完整书写原则、0.14.2 归因与知情度审查、超长篇自行通读流程、0.6 体量不等于破坏、6.3 一次作用计数认定、7.9 层级轴必检及全部十一部分标准。",
        active_nav="rules",
        rendered_md=rules_html_body,
        toc_list=rules_toc,
        raw_md_len=len(rules_md),
        companion_link="materials.html",
        companion_label="《材质与破坏能量数据库（第二版）》",
    )

    build_doc_page(
        filename="materials.html",
        kicker="STANDARD MONOGRAPH II · PHYSICS & MATERIALS DB",
        title="《材质与破坏能量数据库（第二版）》",
        subtitle="《衡天⊙》配套工程物理参数库全文：破坏动词双轴定性、物质粉碎能量密度、材料强度与断裂韧性、相变潜热、天体引力束缚能、撞击成坑与云层推算。",
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
      <div class="container page-hero-inner">
        <span class="page-kicker mono">GLOBAL INDEX · {len(search_items)} ENTRIES</span>
        <h1 class="page-hero-title"><span>全站即时检索</span><span class="brand-badge mono">{len(search_items)} 条索引</span></h1>
        <p class="page-hero-desc">跨角色分类、量级分类、《衡天⊙ 多维战力量级体系（第三版）》及《材质与破坏能量数据库》全章节毫秒级检索。</p>
      </div>
    </section>

    <div class="container" style="padding:22px 24px 64px;max-width:960px">
      <div class="toolbar-panel" style="margin-top:0">
        <div class="filter-input-wrap" style="max-width:none">
          <span class="filter-input-icon">{SVG['search_sm']}</span>
          <input type="search" id="dedicated-search-input" class="filter-input" style="height:42px;font-size:14.5px;padding-left:36px" placeholder="输入关键词（支持空格组合检索），例如：归因 知情度 / 完整书写 / 白矮星 束缚能 / 宇◆…" autofocus>
        </div>
        <div class="toolbar-row">
          <div class="filter-Chips">
            <button type="button" class="chip-btn active" data-page-search-type="all">全部类别</button>
            <button type="button" class="chip-btn" data-page-search-type="char">角色分类（{len(chars_for_index)}）</button>
            <button type="button" class="chip-btn" data-page-search-type="tier">量级分类（{len(tiers)}）</button>
            <button type="button" class="chip-btn" data-page-search-type="rules">衡天第三版（{len(rules_sections)} 节）</button>
            <button type="button" class="chip-btn" data-page-search-type="materials">材质能量库（{len(mat_sections)} 节）</button>
          </div>
          <span class="mono" id="dedicated-search-count" style="font-size:12px;color:var(--text-muted);flex-shrink:0"></span>
        </div>
        <div class="filter-Chips">
          <span style="font-size:12px;color:var(--text-muted);flex-shrink:0">速查词：</span>
          <button type="button" class="chip-btn" data-hot-query="完整书写">完整书写原则</button>
          <button type="button" class="chip-btn" data-hot-query="归因与知情度">0.14.2 归因审查</button>
          <button type="button" class="chip-btn" data-hot-query="超长篇自行通读">超长篇通读流程</button>
          <button type="button" class="chip-btn" data-hot-query="层级轴必检">7.9 层级轴必检</button>
          <button type="button" class="chip-btn" data-hot-query="宇◆">宇◆（极宇宙）</button>
          <button type="button" class="chip-btn" data-hot-query="F*">通量常数 F*</button>
          <button type="button" class="chip-btn" data-hot-query="0#">0#（零尖）</button>
          <button type="button" class="chip-btn" data-hot-query="中子星">中子星束缚能</button>
          <button type="button" class="chip-btn" data-hot-query="花岗岩">花岗岩粉碎</button>
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
        f"Build v4.0 complete: {len(tiers)} tier pages, {len(formal_chars)} character pages, "
        f"{len(rules_toc)} rules TOC anchors, {len(mat_toc)} materials TOC anchors, "
        f"{len(search_items)} search index entries."
    )


if __name__ == "__main__":
    build_all()
