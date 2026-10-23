#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Builder v5.0 — Obsidian Celestial Archive
Generates:
  - index.html             (Home: feathered celestial hero, 4 art-backed portals, spectrum, featured dossiers)
  - tiers.html             (98-tier taxonomy strictly ordered 从小到大 #01 -> #97)
  - tier/<slug>.html       (98 standalone tier detail pages)
  - characters.html        (Character archive: 首字母 A-Z & 量级从小到大 dual sort)
  - character/<slug>.html  (Standalone character dossier pages for all characters — zero modals)
  - rules.html             (Full-text verbatim: 衡天量级体系【第三版·最新】.md)
  - materials.html         (Full-text verbatim: 材质与破坏能量数据库（新）.md)
  - search.html            (Full-site instant search center)
  - static/js/search-index.js (Offline data & search index for RawGit / static hosting)
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
TIER_OUT_DIR = ROOT / "tier"
CHAR_OUT_DIR = ROOT / "character"
JS_OUT_DIR = ROOT / "static" / "js"

RULES_MD_PATH = DOCS_DIR / "衡天量级体系【第三版·最新】.md"
MATERIALS_MD_PATH = DOCS_DIR / "材质与破坏能量数据库（新）.md"

SVGS = {
    "search": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "menu": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="7" y2="7"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="17" y2="17"/></svg>',
    "sun": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "arrow_left": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>',
    "arrow_up": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
    "arrow_up_right": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>',
    "toc": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
}

DIM_META = [
    ("破", "破坏能量", "单次作用直接瓦解、打爆目标结构的实测或推定能量阈值"),
    ("控", "能量操控", "对物质、能量或时空结构进行整体掌控的尺度与上限"),
    ("御", "防御承受", "正面承受对应量级能量冲击而不丧失核心结构的耐久锚点"),
    ("速", "机动反应", "战斗机动、巡航跨越或无延迟响应的物理/超限速度标定"),
    ("域", "作用范围", "规则干涉、精神场域或概念覆写的空间/层级覆盖边界"),
    ("算", "演算感知", "有限算力至图灵跃迁（0′ / 0⁽ω⁾）级的信息处理与预判能力"),
    ("性", "机制特性", "独立于纯能量数值之外的存续形态、材质构成与特殊机制"),
]


def esc(val: Any) -> str:
    return html.escape(str(val if val is not None else ""), quote=True)


def format_evidence_html(val: str) -> str:
    s = esc(val)
    s = s.replace("〔实〕", '<span class="ev-badge ev-confirmed">〔实〕</span>')
    s = s.replace("〔下〕", '<span class="ev-badge ev-lower">〔下〕</span>')
    s = s.replace("〔推〕", '<span class="ev-badge ev-inferred">〔推〕</span>')
    s = s.replace("〔隐〕", '<span class="ev-badge ev-hidden">〔隐〕</span>')
    s = s.replace("〔缺〕", '<span class="ev-badge ev-missing">〔缺〕</span>')
    return s


# ==============================================================================
# Custom Zero-Dependency Verbatim Markdown Parser (Preserves Subscripts & Tables)
# ==============================================================================
class VerbatimMarkdownRenderer:
    def __init__(self) -> None:
        self.toc: List[Dict[str, Any]] = []
        self._slug_counts: Dict[str, int] = {}
        self.sections_for_index: List[Dict[str, str]] = []

    def _make_id(self, text: str) -> str:
        clean = re.sub(r"[`*_~]", "", text).strip()
        slug = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", clean).strip("-").lower()
        if not slug:
            slug = "sec"
        slug = f"sec-{slug}"
        count = self._slug_counts.get(slug, 0)
        self._slug_counts[slug] = count + 1
        return slug if count == 0 else f"{slug}-{count + 1}"

    @staticmethod
    def render_inline(text: str) -> str:
        placeholders: List[str] = []

        def save_span(html_fragment: str) -> str:
            idx = len(placeholders)
            placeholders.append(html_fragment)
            return f"\x00SPAN{idx}\x00"

        def repl_code(m: re.Match[str]) -> str:
            inner = html.escape(m.group(1), quote=False)
            return save_span(f"<code>{inner}</code>")

        text = re.sub(r"`([^`]+)`", repl_code, text)

        def repl_escape(m: re.Match[str]) -> str:
            ch = html.escape(m.group(1), quote=False)
            return save_span(ch)

        text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", repl_escape, text)

        def repl_link(m: re.Match[str]) -> str:
            label = html.escape(m.group(1), quote=False)
            url = html.escape(m.group(2), quote=True)
            return save_span(f'<a href="{url}" target="_blank" rel="noopener">{label}</a>')

        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl_link, text)

        escaped = html.escape(text, quote=False)
        escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
        escaped = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<em>\1</em>", escaped)

        for badge, cls in [
            ("〔实〕", "ev-confirmed"),
            ("〔下〕", "ev-lower"),
            ("〔推〕", "ev-inferred"),
            ("〔隐〕", "ev-hidden"),
            ("〔缺〕", "ev-missing"),
        ]:
            escaped = escaped.replace(badge, f'<span class="ev-badge {cls}">{badge}</span>')

        for idx, frag in enumerate(placeholders):
            escaped = escaped.replace(f"\x00SPAN{idx}\x00", frag)

        return escaped

    @staticmethod
    def _split_table_row(line: str) -> List[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|") and not s.endswith(r"\|"):
            s = s[:-1]
        cells = re.split(r"(?<!\\)\|", s)
        return [c.strip().replace(r"\|", "|") for c in cells]

    @staticmethod
    def _is_table_sep(line: str) -> bool:
        s = line.strip()
        if "|" not in s:
            return False
        cells = VerbatimMarkdownRenderer._split_table_row(s)
        if not cells:
            return False
        return all(bool(re.match(r"^:?-{2,}:?$", c.strip())) for c in cells if c.strip() != "")

    def _render_blocks(self, lines: List[str], record_toc: bool) -> str:
        n = len(lines)
        i = 0
        out: List[str] = []

        cur_sec_id = "sec-top"
        cur_sec_title = "正文导言"
        cur_sec_buf: List[str] = []

        def flush_section_index() -> None:
            nonlocal cur_sec_buf
            if not record_toc:
                return
            joined = " ".join(cur_sec_buf).strip()
            if joined:
                self.sections_for_index.append(
                    {"id": cur_sec_id, "title": cur_sec_title, "text": joined}
                )
            cur_sec_buf = []

        while i < n:
            line = lines[i]
            stripped = line.strip()

            if not stripped:
                i += 1
                continue

            if stripped.startswith("```"):
                lang = stripped[3:].strip()
                i += 1
                code_lines: List[str] = []
                while i < n and not lines[i].strip().startswith("```"):
                    code_lines.append(lines[i])
                    if record_toc:
                        cur_sec_buf.append(lines[i])
                    i += 1
                if i < n:
                    i += 1
                code_html = html.escape("\n".join(code_lines), quote=False)
                lang_attr = f' data-lang="{esc(lang)}"' if lang else ""
                out.append(f"<pre{lang_attr}><code>{code_html}</code></pre>")
                continue

            m_head = re.match(r"^(#{1,4})\s+(.+?)\s*$", stripped)
            if m_head:
                level = len(m_head.group(1))
                raw_title = m_head.group(2)
                plain_title = re.sub(r"[`*_]", "", raw_title).replace(r"\*", "*").strip()
                if record_toc:
                    flush_section_index()
                    hid = self._make_id(plain_title)
                    cur_sec_id = hid
                    cur_sec_title = plain_title
                    cur_sec_buf.append(plain_title)
                    if level in (1, 2, 3):
                        self.toc.append({"level": level, "id": hid, "title": plain_title})
                    inline_html = self.render_inline(raw_title)
                    out.append(
                        f'<h{level} id="{hid}">{inline_html}'
                        f'<a class="heading-anchor" href="#{hid}" data-target-id="{hid}" title="复制本节锚点链接">#</a>'
                        f"</h{level}>"
                    )
                else:
                    out.append(f"<h{level}>{self.render_inline(raw_title)}</h{level}>")
                i += 1
                continue

            if re.match(r"^-{3,}\s*$", stripped) or re.match(r"^\*{3,}\s*$", stripped):
                out.append("<hr>")
                i += 1
                continue

            if "|" in stripped and (i + 1 < n) and self._is_table_sep(lines[i + 1]):
                headers = self._split_table_row(lines[i])
                align_raw = self._split_table_row(lines[i + 1])
                aligns: List[str] = []
                for a in align_raw:
                    a = a.strip()
                    if a.startswith(":") and a.endswith(":"):
                        aligns.append("center")
                    elif a.endswith(":"):
                        aligns.append("right")
                    else:
                        aligns.append("left")
                i += 2
                rows: List[List[str]] = []
                while i < n and lines[i].strip() and "|" in lines[i]:
                    if re.match(r"^(#{1,4})\s+", lines[i].strip()):
                        break
                    rows.append(self._split_table_row(lines[i]))
                    if record_toc:
                        cur_sec_buf.append(lines[i])
                    i += 1

                th_html = "".join(
                    f'<th style="text-align:{aligns[idx] if idx < len(aligns) else "left"}">{self.render_inline(h)}</th>'
                    for idx, h in enumerate(headers)
                )
                if record_toc:
                    cur_sec_buf.append(" ".join(headers))
                tr_list: List[str] = []
                for r in rows:
                    if len(r) < len(headers):
                        r = r + [""] * (len(headers) - len(r))
                    elif len(r) > len(headers):
                        r = r[: len(headers) - 1] + [" | ".join(r[len(headers) - 1 :])]
                    tds = "".join(
                        f'<td style="text-align:{aligns[idx] if idx < len(aligns) else "left"}">{self.render_inline(cell)}</td>'
                        for idx, cell in enumerate(r)
                    )
                    tr_list.append(f"<tr>{tds}</tr>")
                out.append(
                    f'<div class="md-table-wrap"><table><thead><tr>{th_html}</tr></thead>'
                    f"<tbody>{''.join(tr_list)}</tbody></table></div>"
                )
                continue

            if stripped.startswith(">"):
                bq_inner_lines: List[str] = []
                while i < n and lines[i].strip().startswith(">"):
                    raw_bq = re.sub(r"^\s*>\s?", "", lines[i])
                    bq_inner_lines.append(raw_bq)
                    if record_toc:
                        cur_sec_buf.append(raw_bq)
                    i += 1
                inner_html = self._render_blocks(bq_inner_lines, record_toc=False)
                out.append(f"<blockquote>{inner_html}</blockquote>")
                continue

            m_ul = re.match(r"^(\s*)[-*+]\s+(.+)$", line)
            m_ol = re.match(r"^(\s*)(\d+)\.\s+(.+)$", line)
            if m_ul or m_ol:
                is_ordered = bool(m_ol)
                tag = "ol" if is_ordered else "ul"
                items_html: List[str] = []
                while i < n:
                    l_cur = lines[i]
                    if not l_cur.strip():
                        break
                    mu = re.match(r"^(\s*)[-*+]\s+(.+)$", l_cur)
                    mo = re.match(r"^(\s*)(\d+)\.\s+(.+)$", l_cur)
                    if is_ordered and mo and len(mo.group(1)) == 0:
                        item_chunks = [self.render_inline(mo.group(3))]
                        if record_toc:
                            cur_sec_buf.append(mo.group(3))
                        i += 1
                    elif (not is_ordered) and mu and len(mu.group(1)) == 0:
                        item_chunks = [self.render_inline(mu.group(2))]
                        if record_toc:
                            cur_sec_buf.append(mu.group(2))
                        i += 1
                    else:
                        break

                    sub_items: List[str] = []
                    while i < n and lines[i].strip():
                        l_sub = lines[i]
                        msu = re.match(r"^(\s{2,})[-*+]\s+(.+)$", l_sub)
                        mso = re.match(r"^(\s{2,})(\d+)\.\s+(.+)$", l_sub)
                        if msu:
                            sub_items.append(f"<li>{self.render_inline(msu.group(2))}</li>")
                            if record_toc:
                                cur_sec_buf.append(msu.group(2))
                            i += 1
                        elif mso:
                            sub_items.append(f"<li>{self.render_inline(mso.group(3))}</li>")
                            if record_toc:
                                cur_sec_buf.append(mso.group(3))
                            i += 1
                        elif l_sub.startswith("  ") and not re.match(r"^\s*[-*+\d]", l_sub):
                            item_chunks.append("<br>" + self.render_inline(l_sub.strip()))
                            if record_toc:
                                cur_sec_buf.append(l_sub.strip())
                            i += 1
                        else:
                            break
                    if sub_items:
                        item_chunks.append(f"<ul>{''.join(sub_items)}</ul>")
                    items_html.append(f"<li>{''.join(item_chunks)}</li>")

                out.append(f"<{tag}>{''.join(items_html)}</{tag}>")
                continue

            para_lines: List[str] = []
            while i < n:
                l_p = lines[i]
                s_p = l_p.strip()
                if not s_p:
                    break
                if (
                    s_p.startswith("```")
                    or s_p.startswith(">")
                    or re.match(r"^(#{1,4})\s+", s_p)
                    or re.match(r"^-{3,}\s*$", s_p)
                    or re.match(r"^(\s*)[-*+]\s+", l_p)
                    or re.match(r"^(\s*)(\d+)\.\s+", l_p)
                    or ("|" in s_p and (i + 1 < n) and self._is_table_sep(lines[i + 1]))
                ):
                    break
                para_lines.append(self.render_inline(s_p))
                if record_toc:
                    cur_sec_buf.append(s_p)
                i += 1
            if para_lines:
                out.append(f"<p>{'<br>'.join(para_lines)}</p>")

        if record_toc:
            flush_section_index()
        return "\n".join(out)

    def render(self, md_text: str) -> str:
        return self._render_blocks(md_text.splitlines(), record_toc=True)


# ==============================================================================
# Shared Layout Shell (Header + Search Modal + Floating Dock + Footer)
# ==============================================================================
def render_shell(
    *,
    title: str,
    page_id: str,
    active_nav: str,
    body_html: str,
    root_prefix: str = "./",
    has_toc_button: bool = False,
    back_fallback: Tuple[str, str] = ("index.html", "首页"),
) -> str:
    r = root_prefix

    def nav_link(key: str, href: str, label: str) -> str:
        cls = "nav-link active" if active_nav == key else "nav-link"
        return f'<a class="{cls}" href="{r}{href}">{label}</a>'

    toc_dock_html = (
        f'<button type="button" class="dock-btn dock-toc-trigger" id="dock-toc-btn" title="展开章节目录">'
        f'{SVGS["toc"]} <span>目录</span></button>'
        if has_toc_button
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark" data-root="{r}" data-page-id="{esc(page_id)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} · 衡天⊙ PowerWiki</title>
  <meta name="description" content="衡天⊙ PowerWiki — 基于《衡天⊙ 多维战力量级体系（第三版）》与《材质与破坏能量数据库（第二版）》构建的多维战力与量级百科。">
  <script>
    (function() {{
      try {{
        var t = localStorage.getItem('pw_theme_v2');
        if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
      }} catch (e) {{}}
    }})();
  </script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&family=Noto+Serif+SC:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{r}static/css/style.css">
</head>
<body>
  <header class="site-header">
    <div class="header-inner">
      <div class="brand-cluster">
        <button type="button" class="icon-btn mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单">
          {SVGS["menu"]}
        </button>
        <a class="brand-logo" href="{r}index.html">
          <span class="brand-emblem">⊙</span>
          <span class="brand-text">
            <span class="brand-title">衡天 PowerWiki</span>
            <span class="brand-sub">Celestial Scale Archive · V3</span>
          </span>
        </a>
      </div>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        {nav_link("home", "index.html", "首页")}
        {nav_link("tiers", "tiers.html", "量级")}
        {nav_link("characters", "characters.html", "角色")}
        {nav_link("rules", "rules.html", "衡天体系全文")}
        {nav_link("materials", "materials.html", "材质能量库")}
        {nav_link("search", "search.html", "搜索")}
      </nav>

      <div class="header-actions">
        <button type="button" class="search-trigger-btn" id="global-search-trigger" title="全站即时检索 (Ctrl+K 或 /)">
          {SVGS["search"]}
          <span>检索角色、量级、规则…</span>
          <kbd class="kbd-hint">Ctrl K</kbd>
        </button>
        <button type="button" class="icon-btn" id="theme-toggle-btn" aria-label="切换明暗主题">
          {SVGS["sun"]}
        </button>
      </div>
    </div>
  </header>

  <div class="drawer-backdrop" id="drawer-backdrop"></div>

  <main>
    {body_html}
  </main>

  <!-- Floating Navigation Dock (Smart Back + Back to Top) -->
  <div class="floating-dock" aria-label="快捷返回工具栏">
    {toc_dock_html}
    <button type="button" class="dock-btn js-smart-back" data-fallback="{esc(back_fallback[0])}" data-fallback-name="{esc(back_fallback[1])}" title="返回上一页并恢复浏览位置">
      {SVGS["arrow_left"]} <span class="js-back-label">返回</span>
    </button>
    <button type="button" class="dock-btn" id="dock-top-btn" title="回到页面顶部">
      {SVGS["arrow_up"]} <span>顶部</span>
    </button>
  </div>

  <!-- Global Search Command Palette Modal -->
  <div class="modal-backdrop" id="search-modal" role="dialog" aria-modal="true" aria-label="全站搜索">
    <div class="modal-panel">
      <div class="search-modal-head">
        <span style="color:var(--accent-gold);display:flex">{SVGS["search"]}</span>
        <input type="search" class="search-modal-input" id="search-modal-input" placeholder="输入量级代字（如 宇◆、恒○）、角色名、材质或规则关键词…" autocomplete="off">
        <button type="button" class="btn btn-surface" id="search-modal-close" style="padding:5px 11px;font-size:12px">ESC</button>
      </div>
      <div class="search-modal-tabs">
        <button type="button" class="chip-btn active" data-search-tab="all">全部结果</button>
        <button type="button" class="chip-btn" data-search-tab="char">角色档案</button>
        <button type="button" class="chip-btn" data-search-tab="tier">量级分类 (98)</button>
        <button type="button" class="chip-btn" data-search-tab="rules">衡天第三版全文</button>
        <button type="button" class="chip-btn" data-search-tab="materials">材质能量库全文</button>
      </div>
      <div class="search-modal-body" id="search-modal-results"></div>
      <div class="search-modal-foot">
        <span><kbd class="kbd-hint">↑</kbd> <kbd class="kbd-hint">↓</kbd> 选择条目 · <kbd class="kbd-hint">Enter</kbd> 进入页面</span>
        <a href="{r}search.html" style="font-weight:500">进入独立搜索页 →</a>
      </div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid">
        <div>
          <div class="brand-logo" style="margin-bottom:10px">
            <span class="brand-emblem" style="width:28px;height:28px;font-size:14px">⊙</span>
            <span class="brand-title" style="font-size:15px">衡天 PowerWiki</span>
          </div>
          <p class="footer-desc">
            以《衡天⊙ 多维战力量级体系（第三版）》与《材质与破坏能量数据库（第二版）》为唯一基准锚点，提供从昆虫级（5×10⁻⁵ J）至论天最上（莱因哈特 / 贝克莱基数）的全尺度量级检索与独立角色战力档案。
          </p>
        </div>
        <div class="footer-col">
          <h4>核心导览</h4>
          <a href="{r}tiers.html">量级分类（从小到大）</a>
          <a href="{r}characters.html">角色档案（首字母 / 从小到大）</a>
          <a href="{r}search.html">全站检索引擎</a>
        </div>
        <div class="footer-col">
          <h4>基准典籍全文</h4>
          <a href="{r}rules.html">衡天量级体系（第三版·全文）</a>
          <a href="{r}materials.html">材质与破坏能量数据库（第二版·全文）</a>
        </div>
      </div>
      <div class="footer-bottom">
        <span>衡天⊙ PowerWiki · Obsidian Celestial Edition</span>
        <span>全部角色与量级均采用独立静态档案页 · 自动记忆浏览状态与滚动位置</span>
      </div>
    </div>
  </footer>

  <script src="{r}static/js/search-index.js"></script>
  <script src="{r}static/js/app.js"></script>
</body>
</html>
"""


# ==============================================================================
# Page Builders
# ==============================================================================
def build_home_page(tiers: List[Dict[str, Any]], all_chars: List[Dict[str, Any]]) -> str:
    ranked_count = sum(1 for t in tiers if not t.get("unranked"))
    tier_by_slug = {t["slug"]: t for t in tiers}

    segments = [
        ("human", "个体与战术阶", "虫 → 城☆", "5×10⁻⁵ J ～ 4.2×10¹⁷ J", "var(--dom-human)", "tiers.html?seg=human"),
        ("continent", "地理与大陆阶", "国▽ → 陆☆", "4.2×10¹⁷ ～ 2×10²⁹ J", "var(--dom-continent)", "tiers.html?seg=continent"),
        ("planet", "行星与巨行星阶", "星▽ → 巨☆", "2×10²⁹ ～ 2.2×10³⁸ J", "var(--dom-planet)", "tiers.html?seg=planet"),
        ("star", "致密星与恒星系阶", "矮○ → 系☆", "10³⁹ ～ 10⁴⁹ J", "var(--dom-star)", "tiers.html?seg=star"),
        ("galaxy", "星团与星系阶", "团▽ → 河☆", "1.3×10⁵² ～ 10⁶⁹ J", "var(--dom-galaxy)", "tiers.html?seg=galaxy"),
        ("universe", "宇宙与单体顶点", "网▽ → 宇★", "10⁶⁹ J ～ 10^(10^100) J", "var(--dom-universe)", "tiers.html?seg=universe"),
        ("multiverse", "多元与无限高维", "多 → 维·∞", "N×8×10⁷⁷ J ～ ∞-D", "var(--dom-multiverse)", "tiers.html?seg=multiverse"),
        ("outer", "论外与论天大基数", "外·门 → 天·最", "ℵ₀ ～ 莱因哈特/贝克莱", "var(--dom-heaven)", "tiers.html?seg=outer"),
    ]
    seg_html = "".join(
        f"""
        <a class="spectrum-seg" href="{s[5]}" style="--seg-color:{s[4]}">
          <div class="spectrum-seg-range mono">{esc(s[2])}</div>
          <div class="spectrum-seg-label">{esc(s[1])}</div>
          <div class="spectrum-seg-energy mono">{esc(s[3])}</div>
        </a>"""
        for s in segments
    )

    # Pick 3 featured standalone character dossiers ordered weak -> strong
    featured_slugs = ["demo-alpha", "demo-cangqiong", "demo-yuanxu"]
    featured_cards = []
    for slug in featured_slugs:
        c = next((x for x in all_chars if x["slug"] == slug), None)
        if not c:
            continue
        t = tier_by_slug.get(c["tier_slug"])
        t_code = t["code"] if t else "待定"
        t_name = t["name"] if t else "待定"
        t_order = f"#{t['order']:02d}" if t and not t.get("unranked") else "—"
        initial = esc((c.get("initial") or "#").upper())
        featured_cards.append(
            f"""
            <a class="char-card" href="character/{esc(c['slug'])}.html">
              <span class="char-watermark-letter" aria-hidden="true">{initial}</span>
              <div class="char-card-head">
                <div style="display:flex;align-items:center;gap:13px;min-width:0">
                  <div class="char-avatar">{esc(c['name'][:1])}</div>
                  <div class="char-title-group">
                    <h3 class="char-name">{esc(c['name'])}</h3>
                    <div class="char-series">{esc(c.get('alias') or c.get('series') or '')}</div>
                  </div>
                </div>
                <span class="char-rating-pill mono">⊙ {esc(t_code)}</span>
              </div>
              <div class="char-modifiers">
                <span class="mod-chip" style="color:var(--accent-blue)">{esc(t_name)} · {t_order}</span>
                <span class="mod-chip mono">首字母 {initial}</span>
              </div>
              <div style="font-size:13px;color:var(--text-secondary);line-height:1.7">{esc(c.get('summary') or '')}</div>
              <div class="char-card-foot">
                <span class="mono" style="font-size:11.5px">{esc(c.get('credibility') or '')}</span>
                <span class="char-enter-link" style="white-space:nowrap;font-weight:500;display:inline-flex;align-items:center;gap:4px">独立档案页 {SVGS['arrow_up_right']}</span>
              </div>
            </a>"""
        )

    body = f"""
    <div class="container">
      <!-- Obsidian Celestial Hero Stage -->
      <section class="hero-stage">
        <div class="hero-art-layer" aria-hidden="true">
          <img src="static/img/cosmos-eclipse.jpg" alt="" style="--art-pos: 76% 48%;">
        </div>
        <div class="hero-content">
          <div class="hero-eyebrow">
            <span class="hero-eyebrow-line"></span>
            <span>OBSIDIAN CELESTIAL ARCHIVE · 衡天⊙ 第三版</span>
          </div>
          <h1 class="hero-title">
            多维战力刻度与<span class="gold-accent">实证角色典藏</span>
          </h1>
          <p class="hero-lead">
            以《衡天⊙ 多维战力量级体系（第三版）》与《材质与破坏能量数据库（第二版）》为唯一标尺。拒绝脱离物理与集合论的空洞标签——每一档位锚定明确焦耳阈值或超限基数，每一位角色拥有独立实证档案。
          </p>

          <div class="hero-actions">
            <a class="btn btn-gold" href="tiers.html">浏览量级天梯（从小到大） {SVGS["arrow_up_right"]}</a>
            <a class="btn btn-surface" href="characters.html">查阅角色档案库</a>
            <button type="button" class="btn btn-surface js-open-search">{SVGS["search"]} 全站检索</button>
          </div>

          <div class="hero-metrics">
            <div>
              <div class="metric-val mono">{ranked_count}<span style="font-size:14px;color:var(--text-muted);font-weight:400"> +1</span></div>
              <div class="metric-label">连续量级刻度（#01 虫 → #97 天·最）</div>
            </div>
            <div>
              <div class="metric-val mono">7 <span style="font-size:14px;color:var(--accent-gold)">维</span> × 5 <span style="font-size:14px;color:var(--accent-blue)">态</span></div>
              <div class="metric-label">破控域御速算性 · 实证状态分离</div>
            </div>
            <div>
              <div class="metric-val mono">{len(all_chars)} <span style="font-size:14px;color:var(--text-muted);font-weight:400">份</span></div>
              <div class="metric-label">独立角色档案页（首字母 / 量级双排序）</div>
            </div>
            <div>
              <div class="metric-val mono">1,861 <span style="font-size:14px;color:var(--text-muted);font-weight:400">行</span></div>
              <div class="metric-label">双基准典籍一字不漏全文收录</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Four Art-Backed Editorial Portals -->
      <section class="section-block">
        <div class="section-head">
          <div>
            <span class="section-kicker">Core Archives</span>
            <h2 class="section-title">四大核心典藏入口</h2>
          </div>
        </div>

        <div class="portal-grid">
          <a class="portal-card" href="tiers.html">
            <div class="portal-art" aria-hidden="true">
              <img src="static/img/monolith-scale.jpg" alt="" loading="lazy" style="--art-pos: 50% 48%;">
            </div>
            <div class="portal-body">
              <div class="portal-top">
                <span class="portal-index">01 / TIER TAXONOMY</span>
                <span class="portal-arrow">{SVGS["arrow_up_right"]}</span>
              </div>
              <div>
                <h3 class="portal-title">量级分类天梯</h3>
                <p class="portal-desc">严格按能量与数学结构「从小到大」单向递增排列：由昆虫级（5×10⁻⁵ J）经行星、恒星、宇宙网，直至莱因哈特与贝克莱基数。全 98 档均设独立规格页。</p>
                <div class="portal-meta">
                  <span class="portal-tag">↑ 严格从小到大</span>
                  <span class="portal-tag">98 独立规格页</span>
                  <span class="portal-tag">三视图切换</span>
                </div>
              </div>
            </div>
          </a>

          <a class="portal-card" href="characters.html">
            <div class="portal-art" aria-hidden="true">
              <img src="static/img/character-chronicle.jpg" alt="" loading="lazy" style="--art-pos: 78% 45%;">
            </div>
            <div class="portal-body">
              <div class="portal-top">
                <span class="portal-index">02 / CHARACTER ARCHIVES</span>
                <span class="portal-arrow">{SVGS["arrow_up_right"]}</span>
              </div>
              <div>
                <h3 class="portal-title">角色战力档案</h3>
                <p class="portal-desc">支持「按首字母 A–Z」与「按量级从小到大」双模式切换；点击任意角色直接进入专属独立档案界面，呈现第三版完整书写与七维证据链。</p>
                <div class="portal-meta">
                  <span class="portal-tag">A–Z 首字母索引</span>
                  <span class="portal-tag">↑ 量级从小到大</span>
                  <span class="portal-tag">独立角色页面</span>
                </div>
              </div>
            </div>
          </a>

          <a class="portal-card" href="rules.html">
            <div class="portal-art" aria-hidden="true">
              <img src="static/img/cosmos-eclipse.jpg" alt="" loading="lazy" style="--art-pos: 82% 46%;">
            </div>
            <div class="portal-body">
              <div class="portal-top">
                <span class="portal-index">03 / CANONICAL STANDARD V3</span>
                <span class="portal-arrow">{SVGS["arrow_up_right"]}</span>
              </div>
              <div>
                <h3 class="portal-title">衡天多维战力量级体系（第三版）</h3>
                <p class="portal-desc">100% 完整原文呈现：涵盖总则与常见违规审查、归因与知情度六问表、1.5 完整书写规范、七维并列记录、论外序数与基数双轴及超长篇通读流程。</p>
                <div class="portal-meta">
                  <span class="portal-tag">1,445 行全文展示</span>
                  <span class="portal-tag">126 节目录联动</span>
                </div>
              </div>
            </div>
          </a>

          <a class="portal-card" href="materials.html">
            <div class="portal-art" aria-hidden="true">
              <img src="static/img/physics-lattice.jpg" alt="" loading="lazy" style="--art-pos: 84% 50%;">
            </div>
            <div class="portal-body">
              <div class="portal-top">
                <span class="portal-index">04 / PHYSICS &amp; MATERIALS DB</span>
                <span class="portal-arrow">{SVGS["arrow_up_right"]}</span>
              </div>
              <div>
                <h3 class="portal-title">材质与破坏能量数据库（第二版）</h3>
                <p class="portal-desc">完整收录常规岩石金属抗压抗拉参数、碎裂/粉碎/熔化/汽化至核子完全解离的全破坏方式比能（J/cm³），以及白矮星与中子星外壳极端物理锚点。</p>
                <div class="portal-meta">
                  <span class="portal-tag">416 行全文展示</span>
                  <span class="portal-tag">物理比能速查表</span>
                </div>
              </div>
            </div>
          </a>
        </div>
      </section>

      <!-- Scale Spectrum -->
      <section class="section-block">
        <div class="spectrum-box">
          <div class="section-head" style="margin-bottom:4px">
            <div>
              <span class="section-kicker">Continuous Scale Spectrum</span>
              <h2 class="section-title" style="font-size:20px">八大量级跨度速览（点击直达对应区间）</h2>
            </div>
            <a class="btn btn-surface" href="tiers.html" style="padding:7px 14px;font-size:12.5px">展开全部 98 档 →</a>
          </div>
          <div class="spectrum-track">
            {seg_html}
          </div>
        </div>
      </section>

      <!-- Featured Standalone Character Dossiers -->
      <section class="section-block">
        <div class="section-head">
          <div>
            <span class="section-kicker">Standalone Character Dossiers</span>
            <h2 class="section-title">代表性角色独立档案预览</h2>
          </div>
          <a class="btn btn-surface" href="characters.html" style="padding:7px 14px;font-size:12.5px">全部 {len(all_chars)} 位角色档案 →</a>
        </div>
        <div class="char-grid">
          {"".join(featured_cards)}
        </div>
      </section>

      <!-- Seven Dimensions & Five Evidence Badges -->
      <section class="section-block">
        <div class="section-head">
          <div>
            <span class="section-kicker">Methodology</span>
            <h2 class="section-title">七维并列评定与五态证据规范</h2>
          </div>
          <a class="btn btn-surface" href="rules.html" style="padding:7px 14px;font-size:12.5px">查阅第三版总则 →</a>
        </div>
        <div class="arch-grid">
          <div class="arch-card">
            <h3 style="margin:0 0 8px;font-family:var(--font-serif);font-size:17px">七维不互推原则</h3>
            <p style="margin:0;color:var(--text-secondary);font-size:13.3px;line-height:1.7">
              除 0.11 条「整体掌控物质与结构可单向推出破坏」外，破坏、防御、速度、算力、场域与特性严格独立计分，缺项记为〔缺〕而不脑补补齐。
            </p>
            <div class="arch-pills">
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">破</strong> 破坏能量</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">控</strong> 整体掌控</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">域</strong> 作用范围</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">御</strong> 防御承受</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">速</strong> 机动速度</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">算</strong> 图灵演算</span>
              <span class="arch-pill"><strong class="mono" style="color:var(--accent-gold)">性</strong> 机制特性</span>
            </div>
          </div>

          <div class="arch-card">
            <h3 style="margin:0 0 8px;font-family:var(--font-serif);font-size:17px">五级证据可信度标识</h3>
            <p style="margin:0;color:var(--text-secondary);font-size:13.3px;line-height:1.7">
              所有定级必须通过 0.14.2「归因与知情度审查」（在场、知情、记忆可靠、表现一致、无后文推翻、归因准确），并显式标注证据等级。
            </p>
            <div class="arch-pills">
              <span class="arch-pill"><span class="ev-badge ev-confirmed">〔实〕</span> 已确认表现</span>
              <span class="arch-pill"><span class="ev-badge ev-lower">〔下〕</span> 保守下限</span>
              <span class="arch-pill"><span class="ev-badge ev-inferred">〔推〕</span> 规则单向推定</span>
              <span class="arch-pill"><span class="ev-badge ev-hidden">〔隐〕</span> 隐含结构锚点</span>
              <span class="arch-pill"><span class="ev-badge ev-missing">〔缺〕</span> 原文未涉及</span>
            </div>
          </div>
        </div>
      </section>
    </div>
    """
    return render_shell(
        title="首页",
        page_id="home",
        active_nav="home",
        body_html=body,
        root_prefix="./",
    )


def build_tiers_page(tiers: List[Dict[str, Any]], groups: List[Dict[str, Any]]) -> str:
    group_map = {g["id"]: g for g in groups}
    ranked = sorted([t for t in tiers if not t.get("unranked")], key=lambda x: x["order"])
    unranked = [t for t in tiers if t.get("unranked")]
    all_ordered = ranked + unranked

    ordered_gids: List[str] = []
    for t in all_ordered:
        if t["group_id"] not in ordered_gids:
            ordered_gids.append(t["group_id"])

    ssr_sections: List[str] = []
    for gid in ordered_gids:
        g = group_map.get(gid, {"title": gid, "subtitle": ""})
        g_items = [t for t in all_ordered if t["group_id"] == gid]
        cards_html = []
        for t in g_items:
            order_str = "待定" if t.get("unranked") else f"#{t['order']:02d}"
            cards_html.append(
                f"""
                <a class="tier-card" data-domain="{esc(t['domain'])}" href="tier/{esc(t['slug'])}.html">
                  <div class="tier-card-top">
                    <span class="tier-code-badge mono">⊙ {esc(t['code'])}</span>
                    <span class="tier-order-num mono">{order_str}</span>
                  </div>
                  <div class="tier-card-name">
                    <span>{esc(t['name'])}</span>
                    <span class="tier-family-tag">{esc(t['family'])}</span>
                  </div>
                  <div class="tier-energy-line mono">{esc(t['energy'])}</div>
                  <div class="tier-scale-line">{esc(t['scale'])}</div>
                  <div class="tier-card-foot">
                    <span>{esc(t['model'])}</span>
                    {SVGS["arrow_up_right"]}
                  </div>
                </a>"""
            )
        ssr_sections.append(
            f"""
            <section class="tier-group-block" id="group-{esc(gid)}">
              <div class="tier-group-header">
                <h2 class="tier-group-title">{esc(g['title'])}</h2>
                <span class="tier-group-sub">{esc(g['subtitle'])} · {len(g_items)} 档</span>
              </div>
              <div class="tier-grid">{''.join(cards_html)}</div>
            </section>"""
        )

    body = f"""
    <div class="container">
      <div class="page-masthead">
        <div class="masthead-art" aria-hidden="true">
          <img src="static/img/monolith-scale.jpg" alt="" style="--art-pos: 62% 48%;">
        </div>
        <div class="masthead-inner">
          <div class="masthead-top">
            <button type="button" class="back-pill js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>量级分类</span>
            </nav>
          </div>
          <div class="masthead-title-row">
            <div>
              <h1 class="masthead-title">量级分类天梯（从小到大）</h1>
              <p class="masthead-sub">
                依据《衡天⊙ 多维战力量级体系（第三版）》严格按<strong>从小到大（#01 昆虫级 → #97 论天最上）</strong>单向排列。修饰符遵循 <code>▽ 弱</code> &lt; <code>○ 标准</code> &lt; <code>△ 强</code> &lt; <code>◆ 极</code> &lt; <code>☆ 超</code>。
              </p>
            </div>
            <span class="count-pill mono" id="tier-result-count">{len(tiers)} / {len(tiers)} 档</span>
          </div>
        </div>
      </div>

      <!-- Controls Bar -->
      <div class="controls-bar">
        <div class="controls-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span class="seg-badge mono" style="color:var(--accent-gold);border-color:rgba(216,184,120,0.3);background:var(--accent-gold-soft)">
              ↑ 排列基准：严格按量级从小到大 (#01 → #97)
            </span>

            <div class="seg-control" role="group" aria-label="视图模式">
              <button type="button" class="seg-btn active" data-tier-view="card">分阶卡片</button>
              <button type="button" class="seg-btn" data-tier-view="flat">连续天梯</button>
              <button type="button" class="seg-btn" data-tier-view="table">紧凑总表</button>
            </div>
          </div>

          <div class="inline-search">
            <input type="search" id="tier-filter-input" placeholder="筛选代字、名称、焦耳能量或天体参照（如 宇◆、2.24×10³²、花岗岩）…" autocomplete="off">
            <button type="button" id="tier-filter-clear" style="display:none;position:absolute;right:8px;top:50%;transform:translateY(-50%);border:none;background:transparent;color:var(--text-muted);cursor:pointer;font-size:12px">清空</button>
          </div>
        </div>

        <div class="controls-row" style="border-top:1px solid var(--border-hairline);padding-top:10px">
          <div class="filter-Chips" role="group" aria-label="量级大类筛选">
            <button type="button" class="chip-btn active" data-tier-seg="all">全量级 (98)</button>
            <button type="button" class="chip-btn" data-tier-seg="human">个体～城市 (30)</button>
            <button type="button" class="chip-btn" data-tier-seg="continent">国家～大陆 (10)</button>
            <button type="button" class="chip-btn" data-tier-seg="planet">行星～巨行星 (10)</button>
            <button type="button" class="chip-btn" data-tier-seg="star">致密星～恒星系 (14)</button>
            <button type="button" class="chip-btn" data-tier-seg="galaxy">星团～星系 (10)</button>
            <button type="button" class="chip-btn" data-tier-seg="universe">宇宙网～宇宙顶点 (11)</button>
            <button type="button" class="chip-btn" data-tier-seg="multiverse">多元～无限维 (4)</button>
            <button type="button" class="chip-btn" data-tier-seg="outer">论外～论天 (8)</button>
            <button type="button" class="chip-btn" data-tier-seg="unranked">待定 (1)</button>
          </div>
        </div>
      </div>

      <div id="tiers-explorer-mount" style="padding-bottom:24px">
        {''.join(ssr_sections)}
      </div>
    </div>
    """
    return render_shell(
        title="量级分类（从小到大）",
        page_id="tiers",
        active_nav="tiers",
        body_html=body,
        root_prefix="./",
        back_fallback=("index.html", "首页"),
    )


def build_tier_detail_pages(
    tiers: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    all_chars: List[Dict[str, Any]],
    rules_title_to_id: Dict[str, str],
) -> None:
    TIER_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in TIER_OUT_DIR.glob("*.html"):
        old.unlink()

    group_map = {g["id"]: g for g in groups}
    ranked = sorted([t for t in tiers if not t.get("unranked")], key=lambda x: x["order"])

    for t in tiers:
        g = group_map.get(t["group_id"], {"title": t["group_id"], "subtitle": ""})
        is_unranked = bool(t.get("unranked"))

        prev_t = None
        next_t = None
        neighbors: List[Dict[str, Any]] = []
        if not is_unranked:
            idx = next(i for i, item in enumerate(ranked) if item["slug"] == t["slug"])
            if idx > 0:
                prev_t = ranked[idx - 1]
            if idx + 1 < len(ranked):
                next_t = ranked[idx + 1]
            lo = max(0, idx - 2)
            hi = min(len(ranked), idx + 3)
            neighbors = ranked[lo:hi]

        rule_sec_title = t.get("rule_section", "")
        rule_anchor = rules_title_to_id.get(rule_sec_title, "")
        rule_href = f"../rules.html#{rule_anchor}" if rule_anchor else "../rules.html"

        chars_in_tier = [c for c in all_chars if c.get("tier_slug") == t["slug"]]
        if chars_in_tier:
            char_list_html = (
                '<div class="char-grid" style="margin-top:14px">'
                + "".join(
                    f"""
                    <a class="char-card" href="../character/{esc(c['slug'])}.html">
                      <span class="char-watermark-letter" aria-hidden="true">{esc((c.get('initial') or '#').upper())}</span>
                      <div class="char-card-head">
                        <div style="display:flex;align-items:center;gap:12px">
                          <div class="char-avatar">{esc(c['name'][:1])}</div>
                          <div>
                            <div class="char-name">{esc(c['name'])}</div>
                            <div class="char-series">{esc(c.get('series', ''))}</div>
                          </div>
                        </div>
                        <span class="char-rating-pill mono">⊙ {esc(t['code'])}</span>
                      </div>
                      <div style="font-size:13px;color:var(--text-secondary)">{esc(c.get('summary', ''))}</div>
                      <div class="char-card-foot">
                        <span class="mono" style="font-size:11.5px">{esc(c.get('credibility') or '')}</span>
                        <span class="char-enter-link" style="display:inline-flex;align-items:center;gap:4px">进入独立角色页 {SVGS['arrow_up_right']}</span>
                      </div>
                    </a>"""
                    for c in chars_in_tier
                )
                + "</div>"
            )
        else:
            char_list_html = f"""
            <div style="margin-top:12px;padding:18px;border-radius:var(--radius-md);background:var(--bg-surface-2);border:1px dashed var(--border-subtle);color:var(--text-muted);font-size:13px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
              <span>当前档位暂无已收录角色档案。在 <code>data/characters.json</code> 中填入 <code>"tier_slug": "{esc(t['slug'])}"</code> 并构建即可自动生成独立角色页并关联至此。</span>
              <a class="btn btn-surface" href="../characters.html" style="padding:6px 12px;font-size:12px">前往角色库 →</a>
            </div>
            """

        ladder_strip_html = ""
        if neighbors:
            pills = []
            for nb in neighbors:
                is_cur = nb["slug"] == t["slug"]
                style = (
                    "border-color:var(--accent-gold);background:var(--accent-gold-soft);color:var(--accent-gold)"
                    if is_cur
                    else ""
                )
                pills.append(
                    f'<a class="btn btn-surface" style="justify-content:space-between;padding:10px 14px;{style}" href="{esc(nb["slug"])}.html">'
                    f'<span class="mono" style="font-weight:700">#{nb["order"]:02d} · ⊙ {esc(nb["code"])}</span>'
                    f'<span style="font-size:12.5px">{esc(nb["name"])}</span>'
                    f'<span class="mono" style="font-size:12px;color:var(--text-muted)">{esc(nb["energy"])}</span>'
                    f"</a>"
                )
            ladder_strip_html = f"""
            <div class="detail-meta-card" style="margin-top:18px">
              <div class="meta-kicker">相邻天梯序列（从小到大连续上下文）</div>
              <div style="display:grid;gap:8px;margin-top:10px">{''.join(pills)}</div>
            </div>
            """

        prev_html = (
            f"""<a class="adj-nav-card" href="{esc(prev_t['slug'])}.html">
                  <span class="adj-dir">← 上一档（更低量级）</span>
                  <span class="adj-name">#{prev_t['order']:02d} · ⊙ {esc(prev_t['code'])} {esc(prev_t['name'])}</span>
                  <span class="mono" style="font-size:12px;color:var(--accent-gold)">{esc(prev_t['energy'])}</span>
                </a>"""
            if prev_t
            else """<div class="adj-nav-card" style="opacity:0.45;pointer-events:none">
                      <span class="adj-dir">← 起点档位</span>
                      <span class="adj-name">已是最低量级（#01 昆虫级）</span>
                    </div>"""
        )

        next_html = (
            f"""<a class="adj-nav-card next" href="{esc(next_t['slug'])}.html">
                  <span class="adj-dir">下一档（更高量级） →</span>
                  <span class="adj-name">#{next_t['order']:02d} · ⊙ {esc(next_t['code'])} {esc(next_t['name'])}</span>
                  <span class="mono" style="font-size:12px;color:var(--accent-gold)">{esc(next_t['energy'])}</span>
                </a>"""
            if next_t
            else """<div class="adj-nav-card next" style="opacity:0.45;pointer-events:none">
                      <span class="adj-dir">顶点档位 →</span>
                      <span class="adj-name">已是最高量级（#97 论天最上）</span>
                    </div>"""
        )

        order_badge = "待定档" if is_unranked else f"天梯序位 #{t['order']:02d} / 97"

        body = f"""
        <div class="container" style="padding-bottom:32px">
          <div style="padding-top:24px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
            <button type="button" class="back-pill js-smart-back" data-fallback="tiers.html" data-fallback-name="量级总览">
              {SVGS["arrow_left"]} <span class="js-back-label">返回量级总览</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="../index.html">首页</a>
              <span>/</span>
              <a href="../tiers.html">量级分类</a>
              <span>/</span>
              <span>⊙ {esc(t['code'])} {esc(t['name'])}</span>
            </nav>
          </div>

          <article class="detail-hero" data-domain="{esc(t['domain'])}" style="margin-top:16px">
            <div style="display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
              <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">
                <span class="tier-code-badge mono" style="font-size:20px;padding:6px 16px;--dom-color:var(--dom-{esc(t['domain'])},var(--accent-gold))">⊙ {esc(t['code'])}</span>
                <span class="count-pill mono">{order_badge}</span>
                <span class="count-pill">{esc(g['title'])}</span>
              </div>
              <a class="btn btn-surface" href="{rule_href}" style="padding:7px 14px;font-size:12.5px">
                查阅《衡天第三版》对应章节 {SVGS["arrow_up_right"]}
              </a>
            </div>

            <h1 style="margin:18px 0 8px;font-family:var(--font-serif);font-size:clamp(26px,3.6vw,36px);font-weight:700;letter-spacing:-0.015em">
              {esc(t['name'])} <span style="font-family:var(--font-sans);font-size:16px;color:var(--text-muted);font-weight:500">· {esc(t['family'])}系</span>
            </h1>
            <p style="margin:0;color:var(--text-secondary);font-size:14.5px;line-height:1.75;max-width:820px">
              {esc(t.get('notes', ''))}
            </p>

            <div class="detail-grid">
              <div class="detail-meta-card">
                <div class="meta-kicker">能量阈值 / 数学定义</div>
                <div class="meta-val mono" style="color:var(--accent-gold);font-size:16.5px">{esc(t['energy'])}</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">覆盖尺度与典型参照物</div>
                <div class="meta-val">{esc(t['scale'])}</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">物理 / 数学计算模型</div>
                <div class="meta-val">{esc(t['model'])}</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">检索拼音索引</div>
                <div class="meta-val mono" style="font-size:13px;color:var(--text-secondary)">
                  首字母 {(t.get('initial') or '#').upper()} · {esc(t.get('code_pinyin', ''))} / {esc(t.get('full_pinyin', ''))}
                </div>
              </div>
            </div>

            <div class="detail-meta-card" style="margin-top:16px;background:var(--bg-surface-1)">
              <div class="meta-kicker">《衡天⊙ 第三版》1.5 完整书写示范格式（首次出现须写全称与标准）</div>
              <div class="meta-val" style="font-size:13.5px;line-height:1.75;color:var(--text-secondary)">
                综合量级：<span class="mono" style="color:var(--accent-gold)">⊙{esc(t['code'])}</span>——{esc(t['name'])}（{esc(t['scale'])}，能量/结构基准 <span class="mono">{esc(t['energy'])}</span>）
              </div>
            </div>

            {ladder_strip_html}

            <div style="margin-top:26px">
              <h2 style="margin:0;font-family:var(--font-serif);font-size:19px;font-weight:700">本档位已收录角色（{len(chars_in_tier)}）</h2>
              {char_list_html}
            </div>

            <div class="adjacent-nav">
              {prev_html}
              {next_html}
            </div>
          </article>
        </div>
        """

        page_html = render_shell(
            title=f"⊙{t['code']} {t['name']}",
            page_id=f"tier-{t['slug']}",
            active_nav="tiers",
            body_html=body,
            root_prefix="../",
            back_fallback=("tiers.html", "量级总览"),
        )
        (TIER_OUT_DIR / f"{t['slug']}.html").write_text(page_html, encoding="utf-8")


def build_characters_page(
    all_chars: List[Dict[str, Any]],
    tiers: List[Dict[str, Any]],
) -> str:
    tier_by_slug = {t["slug"]: t for t in tiers}

    # Pre-render initial SSR character cards (sorted weak -> strong) so page is complete even before JS
    sorted_chars = sorted(
        all_chars,
        key=lambda c: (
            tier_by_slug.get(c.get("tier_slug", ""), {}).get("order", 999),
            c.get("pinyin") or c.get("name") or "",
        ),
    )

    ssr_cards: List[str] = []
    for c in sorted_chars:
        t = tier_by_slug.get(c.get("tier_slug", ""))
        t_code = t["code"] if t else "待定"
        t_name = t["name"] if t else "待定"
        t_order = f"#{t['order']:02d}" if t and not t.get("unranked") else "—"
        initial = esc((c.get("initial") or "#").upper())
        mod_html = "".join(f'<span class="mod-chip">{esc(m)}</span>' for m in (c.get("modifiers") or []))
        dims = c.get("dims") or {}
        dims_html = "".join(
            f'<div class="dim-cell {"full-row" if k in ("域", "性") else ""}">'
            f'<span class="dim-key">{k}</span>'
            f'<span class="dim-val">{format_evidence_html(dims.get(k, "〔缺〕"))}</span></div>'
            for k in ["破", "控", "御", "速", "域", "算", "性"]
        )
        ssr_cards.append(
            f"""
            <a class="char-card" href="character/{esc(c['slug'])}.html">
              <span class="char-watermark-letter" aria-hidden="true">{initial}</span>
              <div class="char-card-head">
                <div style="display:flex;align-items:center;gap:13px;min-width:0">
                  <div class="char-avatar">{esc(c['name'][:1])}</div>
                  <div class="char-title-group">
                    <h3 class="char-name">{esc(c['name'])}</h3>
                    <div class="char-series">{esc(c.get('series') or '未知出处')}{' · ' + esc(c['realm']) if c.get('realm') else ''}</div>
                  </div>
                </div>
                <span class="char-rating-pill mono">⊙ {esc(t_code)}</span>
              </div>
              <div class="char-modifiers">
                <span class="mod-chip" style="color:var(--accent-blue)">{esc(t_name)} · {t_order}</span>
                <span class="mod-chip mono">首字母 {initial}</span>
                {mod_html}
              </div>
              <div class="dims-mini-grid">{dims_html}</div>
              <div class="char-card-foot">
                <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{esc(c.get('summary') or '')}</span>
                <span class="char-enter-link" style="white-space:nowrap;font-weight:500;display:inline-flex;align-items:center;gap:4px">进入档案 {SVGS['arrow_up_right']}</span>
              </div>
            </a>"""
        )

    body = f"""
    <div class="container">
      <div class="page-masthead">
        <div class="masthead-art" aria-hidden="true">
          <img src="static/img/character-chronicle.jpg" alt="" style="--art-pos: 78% 45%;">
        </div>
        <div class="masthead-inner">
          <div class="masthead-top">
            <button type="button" class="back-pill js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>角色分类</span>
            </nav>
          </div>
          <div class="masthead-title-row">
            <div>
              <h1 class="masthead-title">角色战力档案库</h1>
              <p class="masthead-sub">
                支持<strong>按主档量级从小到大</strong>与<strong>按拼音首字母（A–Z）</strong>双基准排序；点击任意角色卡片将<strong>直接进入专属独立角色档案界面</strong>，返回时自动恢复当前排序与滚动位置。
              </p>
            </div>
            <span class="count-pill mono" id="char-result-count">显示 {len(all_chars)} / {len(all_chars)} 位</span>
          </div>
        </div>
      </div>

      <!-- Controls Bar -->
      <div class="controls-bar">
        <div class="controls-row">
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <div class="seg-control" role="group" aria-label="角色排序方式">
              <button type="button" class="seg-btn active" data-char-sort="asc">↑ 按量级从小到大</button>
              <button type="button" class="seg-btn" data-char-sort="alpha">A–Z 按首字母排序</button>
            </div>

            <select id="char-series-select" aria-label="按作品筛选" style="padding:7px 12px;border-radius:var(--radius-sm);border:1px solid var(--border-subtle);background:var(--bg-surface-2);color:var(--text-primary);font-size:12.5px">
              <option value="all">全部作品</option>
            </select>
          </div>

          <div class="inline-search">
            <input type="search" id="char-filter-input" placeholder="检索角色名、拼音首字母、出处、量级代字或维度表现…" autocomplete="off">
          </div>
        </div>

        <div class="controls-row" style="border-top:1px solid var(--border-hairline);padding-top:10px">
          <div class="filter-Chips" role="group" aria-label="角色所属量级段筛选">
            <button type="button" class="chip-btn active" data-char-domain="all">全部量级区间</button>
            <button type="button" class="chip-btn" data-char-domain="human">个体～城市</button>
            <button type="button" class="chip-btn" data-char-domain="continent">国家～大陆</button>
            <button type="button" class="chip-btn" data-char-domain="planet">行星～巨行星</button>
            <button type="button" class="chip-btn" data-char-domain="star">致密星～恒星系</button>
            <button type="button" class="chip-btn" data-char-domain="galaxy">星团～星系</button>
            <button type="button" class="chip-btn" data-char-domain="universe">宇宙网～宇宙</button>
            <button type="button" class="chip-btn" data-char-domain="multiverse">多元～无限维</button>
            <button type="button" class="chip-btn" data-char-domain="outer">论外</button>
            <button type="button" class="chip-btn" data-char-domain="heaven">论天</button>
          </div>
        </div>
      </div>

      <!-- Sticky A-Z Jump Bar (Visible when A-Z Sort Active) -->
      <div class="alpha-bar" id="char-alpha-bar" aria-label="首字母快速定位栏">
        <div class="alpha-letters" id="char-alpha-letters"></div>
      </div>

      <div id="chars-explorer-mount" style="padding-bottom:28px">
        <section class="tier-group-block" id="char-scale-list">
          <div class="tier-group-header">
            <h2 class="tier-group-title">按主档量级从小到大排列（低量级 → 高量级）</h2>
            <span class="tier-group-sub">{len(sorted_chars)} 位角色</span>
          </div>
          <div class="char-grid">{"".join(ssr_cards)}</div>
        </section>
      </div>
    </div>
    """
    return render_shell(
        title="角色分类（首字母 / 从小到大）",
        page_id="characters",
        active_nav="characters",
        body_html=body,
        root_prefix="./",
        back_fallback=("index.html", "首页"),
    )


def build_character_detail_pages(
    all_chars: List[Dict[str, Any]],
    tiers: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    rules_title_to_id: Dict[str, str],
) -> None:
    CHAR_OUT_DIR.mkdir(parents=True, exist_ok=True)
    for old in CHAR_OUT_DIR.glob("*.html"):
        old.unlink()

    if not all_chars:
        return

    tier_by_slug = {t["slug"]: t for t in tiers}
    group_map = {g["id"]: g for g in groups}

    # Order characters weak -> strong for Prev / Next dossier navigation
    ordered_chars = sorted(
        all_chars,
        key=lambda c: (
            tier_by_slug.get(c.get("tier_slug", ""), {}).get("order", 999),
            c.get("pinyin") or c.get("name") or "",
        ),
    )

    for idx, c in enumerate(ordered_chars):
        t = tier_by_slug.get(c.get("tier_slug", ""), tier_by_slug.get("pending", tiers[-1]))
        g = group_map.get(t["group_id"], {"title": t["group_id"], "subtitle": ""})
        prev_c = ordered_chars[idx - 1] if idx > 0 else None
        next_c = ordered_chars[idx + 1] if idx + 1 < len(ordered_chars) else None

        initial = esc((c.get("initial") or "#").upper())
        t_order_str = "待定档" if t.get("unranked") else f"#{t['order']:02d}"

        rule_sec_title = t.get("rule_section", "")
        rule_anchor = rules_title_to_id.get(rule_sec_title, "")
        rule_href = f"../rules.html#{rule_anchor}" if rule_anchor else "../rules.html"

        dims = c.get("dims") or {}
        dim_cards_html: List[str] = []
        for dim_key, dim_title, dim_desc in DIM_META:
            raw_val = dims.get(dim_key, "〔缺〕")
            wide_cls = "wide" if dim_key == "性" else ""
            dim_cards_html.append(
                f"""
                <div class="dossier-dim-card {wide_cls}">
                  <div class="dossier-dim-head">
                    <span class="dossier-dim-symbol mono">{esc(dim_key)}</span>
                    <div>
                      <div class="dossier-dim-title">{esc(dim_title)}</div>
                      <div style="font-size:11.5px;color:var(--text-muted)">{esc(dim_desc)}</div>
                    </div>
                  </div>
                  <div class="dossier-dim-body">{format_evidence_html(raw_val)}</div>
                </div>"""
            )

        mod_chips_html = "".join(
            f'<span class="mod-chip" style="padding:4px 10px;font-size:12px">{esc(m)}</span>'
            for m in (c.get("modifiers") or [])
        )

        full_writing = c.get("full_writing") or (
            f"综合量级：⊙{t['code']}——{t['name']}（{t['scale']}，能量/结构基准 {t['energy']}）。"
        )

        # Optional feats list if provided in characters.json
        feats = c.get("feats") or []
        feats_section_html = ""
        if feats:
            feat_items = "".join(
                f'<li style="margin-bottom:8px;color:var(--text-secondary);line-height:1.75">{format_evidence_html(f)}</li>'
                for f in feats
            )
            feats_section_html = f"""
            <section class="dossier-section">
              <div class="dossier-section-head">
                <h2 class="dossier-section-title">关键战绩与原文引证</h2>
              </div>
              <div class="detail-meta-card">
                <ul style="margin:0;padding-left:20px">{feat_items}</ul>
              </div>
            </section>
            """

        prev_html = (
            f"""<a class="adj-nav-card" href="{esc(prev_c['slug'])}.html">
                  <span class="adj-dir">← 上一位角色（更低量级）</span>
                  <span class="adj-name">{esc(prev_c['name'])}</span>
                  <span class="mono" style="font-size:12px;color:var(--accent-gold)">⊙ {esc(tier_by_slug.get(prev_c.get('tier_slug',''), {}).get('code', '待定'))} · 首字母 {esc((prev_c.get('initial') or '#').upper())}</span>
                </a>"""
            if prev_c
            else """<div class="adj-nav-card" style="opacity:0.45;pointer-events:none">
                      <span class="adj-dir">← 序列起点</span>
                      <span class="adj-name">已是当前库内最低量级角色</span>
                    </div>"""
        )

        next_html = (
            f"""<a class="adj-nav-card next" href="{esc(next_c['slug'])}.html">
                  <span class="adj-dir">下一位角色（更高量级） →</span>
                  <span class="adj-name">{esc(next_c['name'])}</span>
                  <span class="mono" style="font-size:12px;color:var(--accent-gold)">⊙ {esc(tier_by_slug.get(next_c.get('tier_slug',''), {}).get('code', '待定'))} · 首字母 {esc((next_c.get('initial') or '#').upper())}</span>
                </a>"""
            if next_c
            else """<div class="adj-nav-card next" style="opacity:0.45;pointer-events:none">
                      <span class="adj-dir">序列顶点 →</span>
                      <span class="adj-name">已是当前库内最高量级角色</span>
                    </div>"""
        )

        monogram_inner = (
            f'<img src="{esc(c["image_url"])}" alt="{esc(c["name"])}">'
            if c.get("image_url")
            else esc(c["name"][:1])
        )

        body = f"""
        <div class="container" style="padding-bottom:36px">
          <div style="padding-top:24px;display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap">
            <button type="button" class="back-pill js-smart-back" data-fallback="characters.html" data-fallback-name="角色档案库">
              {SVGS["arrow_left"]} <span class="js-back-label">返回角色档案库</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="../index.html">首页</a>
              <span>/</span>
              <a href="../characters.html">角色分类</a>
              <span>/</span>
              <span>{esc(c['name'])}</span>
            </nav>
          </div>

          <!-- Standalone Character Dossier Hero -->
          <section class="dossier-hero">
            <div class="dossier-art" aria-hidden="true">
              <img src="../static/img/character-chronicle.jpg" alt="" style="--art-pos: 82% 42%;">
            </div>
            <div class="dossier-inner">
              <div class="dossier-top-bar">
                <div class="dossier-identity">
                  <div class="dossier-monogram">{monogram_inner}</div>
                  <div>
                    <div class="hero-eyebrow" style="margin-bottom:8px">
                      <span class="hero-eyebrow-line" style="width:18px"></span>
                      <span>CHARACTER DOSSIER · 首字母 {initial}</span>
                    </div>
                    <h1 class="dossier-name">{esc(c['name'])}</h1>
                    <div class="dossier-subtitle">
                      <span>出处：{esc(c.get('series') or '未标注')}</span>
                      {f'<span>·</span><span>境界/形态：{esc(c["realm"])}</span>' if c.get("realm") else ""}
                      {f'<span>·</span><span>称号：{esc(c["alias"])}</span>' if c.get("alias") else ""}
                    </div>
                  </div>
                </div>

                <div class="dossier-seal-box">
                  <a class="dossier-tier-seal mono" href="../tier/{esc(t['slug'])}.html" title="点击查看 ⊙{esc(t['code'])} 量级规格页">
                    <span>⊙ {esc(t['code'])}</span>
                    <span style="font-family:var(--font-serif);font-size:15px;font-weight:700;color:var(--text-primary)">{esc(t['name'])}</span>
                    <span style="font-size:12px;color:var(--text-muted)">{t_order_str}</span>
                    {SVGS["arrow_up_right"]}
                  </a>
                  <div style="display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end">
                    <span class="mod-chip" style="padding:4px 10px;font-size:12px;color:var(--accent-blue)">{esc(g['title'])}</span>
                    {mod_chips_html}
                  </div>
                </div>
              </div>

              <p style="margin:20px 0 0;color:var(--text-secondary);font-size:14.8px;line-height:1.8;max-width:860px">
                {esc(c.get('summary') or '')}
              </p>

              <div class="dossier-quote-box">
                <div class="meta-kicker" style="color:var(--accent-gold);margin-bottom:6px">
                  《衡天⊙ 第三版》1.5 正式完整书写（首次出现展开全称、标准与能量）
                </div>
                <div>{format_evidence_html(full_writing)}</div>
                {f'<div style="margin-top:8px;font-size:12.5px;color:var(--text-muted)">证据链核验摘要：{format_evidence_html(c["credibility"])}</div>' if c.get("credibility") else ""}
              </div>
            </div>
          </section>

          <!-- Seven Dimensions Breakdown -->
          <section class="dossier-section">
            <div class="dossier-section-head">
              <h2 class="dossier-section-title">七维战力分项评定</h2>
              <span class="dossier-section-sub">依据《衡天⊙ 第三版》七维并列与缺项不反推规范逐项标定</span>
            </div>
            <div class="dossier-dims-grid">
              {"".join(dim_cards_html)}
            </div>
          </section>

          {feats_section_html}

          <!-- Canonical Tier Anchor Comparison -->
          <section class="dossier-section">
            <div class="dossier-section-head">
              <h2 class="dossier-section-title">所属主档物理 / 数学基准锚点</h2>
              <a class="btn btn-surface" href="../tier/{esc(t['slug'])}.html" style="padding:6px 13px;font-size:12.5px">
                进入 ⊙{esc(t['code'])} 量级规格页 {SVGS["arrow_up_right"]}
              </a>
            </div>
            <div class="detail-grid" style="margin-top:0">
              <div class="detail-meta-card">
                <div class="meta-kicker">主档代字与序位</div>
                <div class="meta-val mono" style="color:var(--accent-gold)">⊙ {esc(t['code'])} · {esc(t['name'])}（{t_order_str}）</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">能量阈值 / 超限基数</div>
                <div class="meta-val mono">{esc(t['energy'])}</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">覆盖尺度与典型参照</div>
                <div class="meta-val">{esc(t['scale'])}</div>
              </div>
              <div class="detail-meta-card">
                <div class="meta-kicker">对应《衡天第三版》章节</div>
                <div class="meta-val">
                  <a href="{rule_href}" style="display:inline-flex;align-items:center;gap:5px">
                    {esc(rule_sec_title or '查阅第三版规范原文')} {SVGS["arrow_up_right"]}
                  </a>
                </div>
              </div>
            </div>
          </section>

          <!-- Prev / Next Character Navigation -->
          <div class="adjacent-nav" style="margin-top:30px">
            {prev_html}
            {next_html}
          </div>
        </div>
        """

        page_html = render_shell(
            title=f"{c['name']} · 角色战力档案",
            page_id=f"char-{c['slug']}",
            active_nav="characters",
            body_html=body,
            root_prefix="../",
            back_fallback=("characters.html", "角色档案库"),
        )
        (CHAR_OUT_DIR / f"{c['slug']}.html").write_text(page_html, encoding="utf-8")


def build_fulltext_doc_page(
    *,
    page_id: str,
    active_nav: str,
    title: str,
    subtitle: str,
    source_filename: str,
    masthead_img: str,
    masthead_pos: str,
    md_text: str,
    other_doc_link: Tuple[str, str],
) -> Tuple[str, List[Dict[str, str]], Dict[str, str]]:
    renderer = VerbatimMarkdownRenderer()
    rendered_html = renderer.render(md_text)
    line_count = len(md_text.splitlines())
    char_count = len(md_text)

    toc_links: List[str] = []
    title_to_id: Dict[str, str] = {}
    for item in renderer.toc:
        lvl = item["level"]
        hid = item["id"]
        htitle = item["title"]
        title_to_id[htitle] = hid
        toc_links.append(
            f'<a class="toc-item toc-lvl-{lvl}" href="#{esc(hid)}">{esc(htitle)}</a>'
        )

    body = f"""
    <div class="container">
      <div class="page-masthead">
        <div class="masthead-art" aria-hidden="true">
          <img src="{esc(masthead_img)}" alt="" style="--art-pos: {esc(masthead_pos)};">
        </div>
        <div class="masthead-inner">
          <div class="masthead-top">
            <button type="button" class="back-pill js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>{esc(title)}</span>
            </nav>
          </div>
          <div class="masthead-title-row">
            <div>
              <h1 class="masthead-title">{esc(title)}</h1>
              <p class="masthead-sub">{esc(subtitle)}</p>
            </div>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
              <span class="count-pill mono">全文无删减 · {line_count} 行 · {char_count:,} 字</span>
              <a class="btn btn-surface" href="{esc(other_doc_link[0])}" style="padding:6px 12px;font-size:12px">{esc(other_doc_link[1])} →</a>
            </div>
          </div>
        </div>
      </div>

      <div class="doc-layout">
        <!-- Left Sticky TOC Sidebar -->
        <aside class="doc-sidebar" id="doc-sidebar" aria-label="全文目录">
          <div class="toc-head">
            <div class="toc-head-title">
              <span>章节目录索引</span>
              <span class="mono" style="color:var(--text-muted)">{len(renderer.toc)} 节</span>
            </div>
            <input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选目录章节…" autocomplete="off">
          </div>
          <nav class="toc-list" id="toc-nav">
            {''.join(toc_links)}
          </nav>
        </aside>

        <!-- Full Verbatim Markdown Reader -->
        <article class="doc-article">
          <div class="doc-toolbar">
            <div class="doc-source-badge">
              <span>源文件：<code class="mono">{esc(source_filename)}</code></span>
              <span>·</span>
              <span style="color:var(--ev-confirmed)">100% 完整原文展示</span>
            </div>
            <div class="doc-tools">
              <div style="display:flex;align-items:center;gap:4px">
                <input type="search" id="doc-find-input" placeholder="页内定位词句…" style="width:142px;padding:4px 9px;border-radius:var(--radius-sm);border:1px solid var(--border-subtle);background:var(--bg-surface-2);color:var(--text-primary);font-size:12px">
                <button type="button" class="tool-mini-btn" id="doc-find-next" title="跳转到下一处匹配">定位</button>
                <span class="mono" id="doc-find-count" style="font-size:11px;color:var(--accent-gold);min-width:34px"></span>
              </div>
              <button type="button" class="tool-mini-btn" id="doc-font-dec" title="缩小正文字号">A-</button>
              <button type="button" class="tool-mini-btn" id="doc-font-inc" title="放大正文字号">A+</button>
              <button type="button" class="tool-mini-btn" id="doc-wide-toggle" title="切换宽屏表格阅读模式">宽屏</button>
            </div>
          </div>

          <div class="markdown-body">
            {rendered_html}
          </div>
        </article>
      </div>
    </div>
    """

    full_html = render_shell(
        title=title,
        page_id=page_id,
        active_nav=active_nav,
        body_html=body,
        root_prefix="./",
        has_toc_button=True,
        back_fallback=("index.html", "首页"),
    )
    return full_html, renderer.sections_for_index, title_to_id


def build_search_page() -> str:
    hot_queries = [
        "宇◆",
        "完整书写",
        "归因与知情度",
        "超长篇",
        "外·门",
        "中子星外壳",
        "花岗岩",
        "0′",
        "攻防双满",
        "莱因哈特",
    ]
    hot_chips = "".join(
        f'<button type="button" class="chip-btn" data-hot-query="{esc(q)}">{esc(q)}</button>'
        for q in hot_queries
    )

    body = f"""
    <div class="container" style="padding-bottom:36px">
      <div class="page-masthead">
        <div class="masthead-art" aria-hidden="true">
          <img src="static/img/cosmos-eclipse.jpg" alt="" style="--art-pos: 75% 46%;">
        </div>
        <div class="masthead-inner">
          <div class="masthead-top">
            <button type="button" class="back-pill js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>全站搜索</span>
            </nav>
          </div>
          <div class="masthead-title-row">
            <div>
              <h1 class="masthead-title">全站即时检索引擎</h1>
              <p class="masthead-sub">
                跨<strong>角色独立档案</strong>、<strong>98 个量级档位</strong>、《衡天量级体系（第三版）》全文与《材质与破坏能量数据库（第二版）》全文毫秒级检索。支持代字、拼音、焦耳数值、数学符号与正文词句。
              </p>
            </div>
            <span class="count-pill mono" id="dedicated-search-count">准备就绪</span>
          </div>
        </div>
      </div>

      <div class="controls-bar">
        <div style="position:relative">
          <input type="search" id="dedicated-search-input" placeholder="输入关键词（支持空格分词组合检索，如：星○ 2.24、归因 审查、花岗岩 粉碎、虚空观测者）…" autofocus style="width:100%;padding:13px 18px;border-radius:var(--radius-md);border:1px solid var(--border-strong);background:var(--bg-surface-2);color:var(--text-primary);font-size:15px;outline:none">
        </div>

        <div class="controls-row" style="justify-content:flex-start;gap:8px">
          <span style="font-size:12px;color:var(--text-muted)">范围：</span>
          <button type="button" class="chip-btn active" data-page-search-type="all">全部类别</button>
          <button type="button" class="chip-btn" data-page-search-type="char">角色独立档案</button>
          <button type="button" class="chip-btn" data-page-search-type="tier">量级分类 (98)</button>
          <button type="button" class="chip-btn" data-page-search-type="rules">衡天第三版全文</button>
          <button type="button" class="chip-btn" data-page-search-type="materials">材质能量库全文</button>
        </div>

        <div class="controls-row" style="justify-content:flex-start;gap:6px;border-top:1px solid var(--border-hairline);padding-top:10px">
          <span style="font-size:12px;color:var(--text-muted)">高频检索词：</span>
          {hot_chips}
        </div>
      </div>

      <div id="dedicated-search-results"></div>
    </div>
    """
    return render_shell(
        title="全站搜索",
        page_id="search",
        active_nav="search",
        body_html=body,
        root_prefix="./",
        back_fallback=("index.html", "首页"),
    )


def build_search_index_bundle(
    *,
    tiers_payload: Dict[str, Any],
    all_chars: List[Dict[str, Any]],
    rules_sections: List[Dict[str, str]],
    materials_sections: List[Dict[str, str]],
) -> str:
    index_entries: List[Dict[str, str]] = []
    tiers = tiers_payload["tiers"]
    tier_by_slug = {t["slug"]: t for t in tiers}

    # 1. Tiers -> standalone tier/<slug>.html
    for t in tiers:
        order_tag = "待定" if t.get("unranked") else f"#{t['order']:02d}"
        index_entries.append(
            {
                "type": "tier",
                "code": f"⊙{t['code']} {t['code']}",
                "title": f"⊙{t['code']} · {t['name']}（{order_tag}）",
                "badge": f"量级 {order_tag}",
                "pinyin": f"{t.get('code_pinyin', '')} {t.get('full_pinyin', '')}",
                "text": f"能量/数学刻度：{t['energy']} ｜ 覆盖尺度：{t['scale']} ｜ 模型：{t['model']} ｜ {t.get('notes', '')}",
                "url": f"tier/{t['slug']}.html",
            }
        )

    # 2. All Characters -> standalone character/<slug>.html
    for c in all_chars:
        t = tier_by_slug.get(c.get("tier_slug", ""))
        t_code = t["code"] if t else "待定"
        t_name = t["name"] if t else "待定"
        dims_str = " ".join(f"{k}:{v}" for k, v in (c.get("dims") or {}).items())
        index_entries.append(
            {
                "type": "char",
                "code": f"{c.get('initial', '')} ⊙{t_code}",
                "title": f"{c['name']}（{c.get('series', '未知出处')}）",
                "badge": f"角色 · ⊙{t_code} {t_name}",
                "pinyin": c.get("pinyin", ""),
                "text": f"{c.get('summary', '')} ｜ {c.get('full_writing', '')} ｜ {dims_str}",
                "url": f"character/{c['slug']}.html",
            }
        )

    # 3. Rules sections
    for sec in rules_sections:
        clean_txt = re.sub(r"\s+", " ", sec["text"]).strip()
        index_entries.append(
            {
                "type": "rules",
                "code": "",
                "title": f"衡天第三版 · {sec['title']}",
                "badge": "衡天第三版",
                "pinyin": "",
                "text": clean_txt[:900],
                "url": f"rules.html#{sec['id']}",
            }
        )

    # 4. Materials sections
    for sec in materials_sections:
        clean_txt = re.sub(r"\s+", " ", sec["text"]).strip()
        index_entries.append(
            {
                "type": "materials",
                "code": "",
                "title": f"材质库 · {sec['title']}",
                "badge": "材质能量库",
                "pinyin": "",
                "text": clean_txt[:900],
                "url": f"materials.html#{sec['id']}",
            }
        )

    client_data = {
        "groups": tiers_payload["groups"],
        "tiers": tiers_payload["tiers"],
        "allCharacters": all_chars,
    }

    js_content = (
        "/* Auto-generated by build_site.py v5.0 — DO NOT EDIT MANUALLY */\n"
        f"window.__POWERWIKI_DATA__ = {json.dumps(client_data, ensure_ascii=False, separators=(',', ':'))};\n"
        f"window.__POWERWIKI_INDEX__ = {json.dumps(index_entries, ensure_ascii=False, separators=(',', ':'))};\n"
    )
    return js_content


def main() -> None:
    tiers_payload = json.loads((DATA_DIR / "tiers.json").read_text(encoding="utf-8"))
    chars_payload = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8"))

    # Merge formal characters + Third Edition archetype dossiers (deduplicated by slug)
    by_slug: Dict[str, Dict[str, Any]] = {}
    for entry in chars_payload.get("demo_archetypes", []):
        by_slug[entry["slug"]] = entry
    for entry in chars_payload.get("characters", []):
        by_slug[entry["slug"]] = entry
    all_chars = list(by_slug.values())

    rules_md = RULES_MD_PATH.read_text(encoding="utf-8")
    materials_md = MATERIALS_MD_PATH.read_text(encoding="utf-8")

    # 1. Full-text Standard & Materials pages
    rules_html, rules_sections, rules_title_to_id = build_fulltext_doc_page(
        page_id="rules",
        active_nav="rules",
        title="衡天⊙ 多维战力量级体系（第三版·全文）",
        subtitle="完整收录总则、常见违规与归因审查、1.5 完整书写规范、全量级定义、论外基数序数双轴及超长篇自行通读流程。",
        source_filename="衡天量级体系【第三版·最新】.md",
        masthead_img="static/img/cosmos-eclipse.jpg",
        masthead_pos="80% 46%",
        md_text=rules_md,
        other_doc_link=("materials.html", "查阅《材质与破坏能量数据库》全文"),
    )
    (ROOT / "rules.html").write_text(rules_html, encoding="utf-8")

    materials_html, materials_sections, _ = build_fulltext_doc_page(
        page_id="materials",
        active_nav="materials",
        title="材质与破坏能量数据库（第二版·全文）",
        subtitle="完整收录岩石/金属/生物力学强度、碎裂至核子解离破坏方式比能（J/cm³）、天体结合能与致密星物质锚点。",
        source_filename="材质与破坏能量数据库（新）.md",
        masthead_img="static/img/physics-lattice.jpg",
        masthead_pos="84% 50%",
        md_text=materials_md,
        other_doc_link=("rules.html", "查阅《衡天量级体系（第三版）》全文"),
    )
    (ROOT / "materials.html").write_text(materials_html, encoding="utf-8")

    # 2. Home, Tiers, Tier Details, Characters, Character Details, Search
    tiers = tiers_payload["tiers"]
    groups = tiers_payload["groups"]

    (ROOT / "index.html").write_text(build_home_page(tiers, all_chars), encoding="utf-8")
    (ROOT / "tiers.html").write_text(build_tiers_page(tiers, groups), encoding="utf-8")
    build_tier_detail_pages(tiers, groups, all_chars, rules_title_to_id)

    (ROOT / "characters.html").write_text(build_characters_page(all_chars, tiers), encoding="utf-8")
    build_character_detail_pages(all_chars, tiers, groups, rules_title_to_id)

    (ROOT / "search.html").write_text(build_search_page(), encoding="utf-8")

    # 3. Search & Data JS Bundle
    JS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_js = build_search_index_bundle(
        tiers_payload=tiers_payload,
        all_chars=all_chars,
        rules_sections=rules_sections,
        materials_sections=materials_sections,
    )
    (JS_OUT_DIR / "search-index.js").write_text(bundle_js, encoding="utf-8")

    print(
        f"[OK] PowerWiki v5.0 built successfully:\n"
        f"  - Core pages: index.html, tiers.html, characters.html, rules.html, materials.html, search.html\n"
        f"  - Standalone Tier pages: {len(tiers)} files in tier/*.html\n"
        f"  - Standalone Character pages: {len(all_chars)} files in character/*.html\n"
        f"  - Rules TOC anchors: {len(rules_sections)} sections | Materials TOC anchors: {len(materials_sections)} sections\n"
        f"  - Search index entries: {len(tiers) + len(all_chars) + len(rules_sections) + len(materials_sections)}"
    )


if __name__ == "__main__":
    main()
