#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Builder v6.2
Updated for 《衡天⊙ 多维战力量级体系（第四版）》 & Full-Text Character Dossiers
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

RULES_MD_PATH = DOCS_DIR / "衡天量级体系【第四版·最新】.md"
MATERIALS_MD_PATH = DOCS_DIR / "材质与破坏能量数据库（新）.md"

SVGS = {
    "search": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "menu": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="7" y2="7"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="17" y2="17"/></svg>',
    "sun": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "arrow_left": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>',
    "arrow_up": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
    "arrow_up_right": '<svg class="svg-icon sm card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>',
    "toc": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
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
    def __init__(self, image_map: Dict[str, str] | None = None) -> None:
        self.toc: List[Dict[str, Any]] = []
        self._slug_counts: Dict[str, int] = {}
        self.sections_for_index: List[Dict[str, str]] = []
        self.image_map: Dict[str, str] = dict(image_map or {})

    def _make_id(self, text: str) -> str:
        clean = re.sub(r"[`*_~]", "", text).strip()
        slug = re.sub(r"[^\w\u4e00-\u9fff\-]+", "-", clean).strip("-").lower()
        if not slug:
            slug = "sec"
        slug = f"sec-{slug}"
        count = self._slug_counts.get(slug, 0)
        self._slug_counts[slug] = count + 1
        return slug if count == 0 else f"{slug}-{count + 1}"

    def render_inline(self, text: str) -> str:
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

        def repl_img(m: re.Match[str]) -> str:
            alt_txt = html.escape(m.group(1), quote=True)
            raw_url = m.group(2).strip()
            resolved_url = html.escape(self.image_map.get(raw_url, raw_url), quote=True)
            return save_span(f'<img class="md-inline-img" src="{resolved_url}" alt="{alt_txt}" loading="lazy">')

        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl_img, text)

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

            m_img = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
            if m_img:
                alt_raw = m_img.group(1).strip()
                src_raw = m_img.group(2).strip()
                resolved_src = self.image_map.get(src_raw, src_raw)
                if record_toc and alt_raw:
                    cur_sec_buf.append(alt_raw)
                cap_html = (
                    f'<figcaption class="md-figcaption">{self.render_inline(alt_raw)}</figcaption>'
                    if alt_raw
                    else ""
                )
                out.append(
                    f'<figure class="md-figure">'
                    f'<div class="md-figure-frame">'
                    f'<a class="md-figure-link" href="{esc(resolved_src)}" target="_blank" rel="noopener" title="点击查看原尺寸图片">'
                    f'<img class="md-img" src="{esc(resolved_src)}" alt="{esc(alt_raw)}" loading="lazy">'
                    f"</a>"
                    f"</div>"
                    f"{cap_html}"
                    f"</figure>"
                )
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
                    or re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", s_p)
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
# Shared Layout Shell
# ==============================================================================
def render_shell(
    *,
    title: str,
    page_id: str,
    active_nav: str,
    body_html: str,
    root_prefix: str = "./",
    has_toc_button: bool = False,
) -> str:
    r = root_prefix

    def nav_link(key: str, href: str, label: str) -> str:
        cls = "nav-link active" if active_nav == key else "nav-link"
        return f'<a class="{cls}" href="{r}{href}">{label}</a>'

    toc_dock_html = (
        f'<button type="button" class="dock-btn dock-toc-trigger" id="dock-toc-btn" title="展开章节目录" aria-label="展开章节目录">'
        f'{SVGS["toc"]}</button>'
        if has_toc_button
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="dark" data-root="{r}" data-page-id="{esc(page_id)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} · 衡天⊙ PowerWiki</title>
  <meta name="description" content="衡天⊙ PowerWiki — 基于《衡天⊙ 多维战力量级体系（第四版）》与《材质与破坏能量数据库（第二版）》构建的多维战力与量级百科。">
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
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="{r}static/css/style.css">
</head>
<body>
  <header class="site-header">
    <div class="container header-inner">
      <div class="header-left">
        <button type="button" class="icon-btn mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单">
          {SVGS["menu"]}
        </button>
        <a class="brand-link" href="{r}index.html">
          <span class="brand-mark">⊙</span>
          <span class="brand-name">衡天 PowerWiki</span>
        </a>
      </div>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        {nav_link("home", "index.html", "首页")}
        {nav_link("tiers", "tiers.html", "量级")}
        {nav_link("characters", "characters.html", "角色")}
        {nav_link("rules", "rules.html", "体系全文")}
        {nav_link("materials", "materials.html", "材质库")}
        {nav_link("search", "search.html", "搜索")}
      </nav>

      <div class="header-right">
        <button type="button" class="search-btn" id="global-search-trigger" title="全站即时检索 (Ctrl+K 或 /)">
          {SVGS["search"]}
          <span class="search-btn-label">检索…</span>
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

  <div class="floating-dock" aria-label="快捷工具">
    {toc_dock_html}
    <button type="button" class="dock-btn is-hidden" id="dock-top-btn" title="回到页面顶部" aria-label="回到页面顶部">
      {SVGS["arrow_up"]}
    </button>
  </div>

  <div class="modal-backdrop" id="search-modal" role="dialog" aria-modal="true" aria-label="全站搜索">
    <div class="modal-panel">
      <div class="search-modal-head">
        <span class="search-modal-icon">{SVGS["search"]}</span>
        <input type="search" class="search-modal-input" id="search-modal-input" placeholder="输入量级代字（如 宇◆、恒○）、标注图、材质或规则关键词…" autocomplete="off">
        <button type="button" class="btn btn-ghost btn-sm" id="search-modal-close">ESC</button>
      </div>
      <div class="search-modal-tabs">
        <button type="button" class="chip-btn active" data-search-tab="all">全部结果</button>
        <button type="button" class="chip-btn" data-search-tab="tier">量级分类 (98)</button>
        <button type="button" class="chip-btn" data-search-tab="char">角色档案</button>
        <button type="button" class="chip-btn" data-search-tab="rules">衡天第四版全文</button>
        <button type="button" class="chip-btn" data-search-tab="materials">材质能量库全文</button>
      </div>
      <div class="search-modal-body" id="search-modal-results"></div>
      <div class="search-modal-foot">
        <span><kbd class="kbd-hint">↑</kbd> <kbd class="kbd-hint">↓</kbd> 选择 · <kbd class="kbd-hint">Enter</kbd> 打开</span>
        <a href="{r}search.html">进入独立搜索页 →</a>
      </div>
    </div>
  </div>

  <footer class="site-footer">
    <div class="container footer-inner">
      <div class="footer-brand">
        <span class="brand-mark">⊙</span>
        <span>衡天 PowerWiki · 多维战力与物理破坏参考百科（第四版基准）</span>
      </div>
      <div class="footer-links">
        <a href="{r}tiers.html">量级天梯</a>
        <a href="{r}characters.html">角色档案</a>
        <a href="{r}rules.html">衡天体系全文</a>
        <a href="{r}materials.html">材质能量库</a>
        <a href="{r}search.html">全站检索</a>
      </div>
    </div>
  </footer>

  <script src="{r}static/js/search-index.js"></script>
  <script src="{r}static/js/app.js"></script>
</body>
</html>
"""


def resolve_rel_asset(rel_path: str, prefix: str) -> str:
    if not rel_path:
        return ""
    if re.match(r"^(https?:)?//", rel_path) or rel_path.startswith("/"):
        return rel_path
    return f"{prefix}{rel_path.lstrip('./')}"


def render_char_card_html(c: Dict[str, Any], tier_by_slug: Dict[str, Dict[str, Any]], href_prefix: str) -> str:
    t = tier_by_slug.get(c.get("tier_slug", ""))
    t_code = t["code"] if t else "待定"
    t_name = t["name"] if t else "待定"
    t_order = f"#{t['order']:02d}" if t and not t.get("unranked") else "待定"
    initial = esc((c.get("initial") or "#").upper())
    mod_html = "".join(f'<span class="tag-pill">{esc(m)}</span>' for m in (c.get("modifiers") or []))
    img_src = resolve_rel_asset(c.get("image_url", ""), href_prefix)
    monogram_inner = (
        f'<img src="{esc(img_src)}" alt="{esc(c["name"])}" loading="lazy">'
        if img_src
        else esc(c["name"][:1])
    )
    origin_text = esc(c.get("series") or "未知出处") + (f" · {esc(c['realm'])}" if c.get("realm") else "")

    return f"""
    <a class="char-card" href="{href_prefix}character/{esc(c['slug'])}.html">
      <div class="char-head">
        <div class="char-identity">
          <div class="char-monogram">{monogram_inner}</div>
          <div class="char-meta">
            <h3 class="char-name">{esc(c['name'])}</h3>
            <div class="char-origin">{origin_text}</div>
          </div>
        </div>
        <span class="tier-badge gold mono">⊙ {esc(t_code)}</span>
      </div>
      <div class="char-tags">
        <span class="tag-pill accent">{esc(t_name)} · {t_order}</span>
        <span class="tag-pill mono">首字母 {initial}</span>
        {mod_html}
      </div>
      <p class="char-summary">{esc(c.get('summary') or '')}</p>
      <div class="char-foot">
        <span class="char-cred">{format_evidence_html(c.get('credibility') or '点击查阅七维证据链')}</span>
        <span class="card-link-hint">查看档案 {SVGS["arrow_up_right"]}</span>
      </div>
    </a>"""


# ==============================================================================
# Page Builders
# ==============================================================================
def build_home_page(
    tiers: List[Dict[str, Any]],
    all_chars: List[Dict[str, Any]],
    rules_lines: int,
    materials_lines: int,
    rules_toc_count: int,
) -> str:
    ranked_count = sum(1 for t in tiers if not t.get("unranked"))
    tier_by_slug = {t["slug"]: t for t in tiers}
    total_lines = rules_lines + materials_lines

    horizon_nodes = [
        ("虫 → 星☆", "个体与行星阶", "5×10⁻⁵ ～ 10³⁶ J", "var(--dom-terrestrial)", "tiers.html?seg=terrestrial"),
        ("巨▽ → 恒☆", "巨行星至恒星阶", "10³⁶ ～ 10⁴⁶ J", "var(--dom-stellar)", "tiers.html?seg=stellar"),
        ("渡A → 渡B", "星际过渡带", "恒星系至星团衔接", "var(--dom-transition)", "tiers.html?seg=transition"),
        ("系▽ → 维·∞", "恒星系至多元高维", "10⁴⁵ J ～ ∞-D", "var(--dom-cosmic)", "tiers.html?seg=cosmic"),
        ("f_ω → 天基", "广义无限层级", "快速增长层级 FGH", "var(--dom-fgh)", "tiers.html?seg=fgh"),
        ("外·门 → 天·最", "论外与论天大基数", "ℵ₀ ～ 莱因哈特/贝克莱", "var(--dom-beyond)", "tiers.html?seg=beyond"),
    ]
    horizon_html = "".join(
        f"""
        <a class="horizon-item" href="{h[4]}" style="--seg-color:{h[3]}">
          <span class="horizon-code mono">{esc(h[0])}</span>
          <span class="horizon-name">{esc(h[1])}</span>
          <span class="horizon-range mono">{esc(h[2])}</span>
        </a>"""
        for h in horizon_nodes
    )

    featured_section = ""
    if all_chars:
        featured_cards = [render_char_card_html(c, tier_by_slug, "") for c in all_chars[:6]]
        featured_section = f"""
      <section class="section-block">
        <div class="section-header">
          <div>
            <span class="section-kicker">Featured Dossiers</span>
            <h2 class="section-title">已收录角色档案</h2>
          </div>
          <a class="btn btn-secondary btn-sm" href="characters.html">全部 {len(all_chars)} 位角色 →</a>
        </div>
        <div class="char-grid">
          {"".join(featured_cards)}
        </div>
      </section>"""

    third_stat_val = f"{len(all_chars)} 份" if all_chars else "第四版"
    third_stat_label = (
        "独立角色档案页（首字母 / 量级双排序）"
        if all_chars
        else "2026-10-24 最新修订（含标注图与动图规范）"
    )

    body = f"""
    <div class="container home-stack">
      <section>
        <div class="hero-banner">
          <div class="hero-backdrop" aria-hidden="true">
            <img class="hero-backdrop-img" src="static/img/cosmos-eclipse.jpg" alt="">
          </div>
          <div class="hero-body">
            <div class="eyebrow">
              <span class="eyebrow-dot"></span>
              <span>衡天⊙ 多维战力量级体系 · 第四版最新基准</span>
            </div>
            <h1 class="hero-heading">多维战力刻度与物理破坏参考百科</h1>
            <p class="hero-desc">
              以《衡天⊙ 多维战力量级体系（第四版）》与《材质与破坏能量数据库（第二版）》为唯一标尺。每一量级锚定明确物理焦耳或集合论基数，支持全量级天梯检索、角色归档与双典籍全文查阅。
            </p>
            <div class="hero-cta-row">
              <a class="btn btn-primary" href="tiers.html">浏览量级天梯（从小到大）</a>
              <a class="btn btn-secondary" href="rules.html">阅读第四版体系全文</a>
              <button type="button" class="btn btn-ghost js-open-search">{SVGS["search"]} 全站检索</button>
            </div>
          </div>
        </div>

        <div class="stats-strip">
          <div class="stat-cell">
            <span class="stat-value mono">{ranked_count} + 1</span>
            <span class="stat-label">连续量级档位（#01 虫 → #97 天·最）</span>
          </div>
          <div class="stat-cell">
            <span class="stat-value mono">7 维 × 5 态</span>
            <span class="stat-label">破控域御速算性 · 证据等级分离</span>
          </div>
          <div class="stat-cell">
            <span class="stat-value mono">{third_stat_val}</span>
            <span class="stat-label">{third_stat_label}</span>
          </div>
          <div class="stat-cell">
            <span class="stat-value mono">{total_lines:,} 行</span>
            <span class="stat-label">两部基准典籍 100% 完整原文收录</span>
          </div>
        </div>
      </section>

      <section class="section-block">
        <div class="section-header">
          <div>
            <span class="section-kicker">Core Archives</span>
            <h2 class="section-title">四大核心板块</h2>
          </div>
        </div>

        <div class="portal-grid">
          <a class="portal-card" href="tiers.html">
            <div>
              <div class="portal-top">
                <span class="portal-num mono">01 / TIER TAXONOMY</span>
                <span class="portal-icon">{SVGS["arrow_up_right"]}</span>
              </div>
              <h3 class="portal-title">量级分类天梯</h3>
              <p class="portal-text">严格按能量与数学结构「从小到大」单向递增排列：由昆虫级（5×10⁻⁵ J）经行星、恒星、星系，直至莱因哈特与贝克莱基数。全 98 档均设独立规格页。</p>
            </div>
            <div class="portal-footer">
              <span class="tag-pill accent">↑ 严格从小到大</span>
              <span class="tag-pill">98 独立规格页</span>
              <span class="tag-pill">卡片 / 天梯 / 总表三视图</span>
            </div>
          </a>

          <a class="portal-card" href="characters.html">
            <div>
              <div class="portal-top">
                <span class="portal-num mono">02 / CHARACTER ARCHIVES</span>
                <span class="portal-icon">{SVGS["arrow_up_right"]}</span>
              </div>
              <h3 class="portal-title">角色战力档案</h3>
              <p class="portal-text">支持「按量级从小到大」与「按首字母 A–Z」双模式排序；录入角色后自动生成专属独立档案页面，展示完整书写结论与七维证据链。</p>
            </div>
            <div class="portal-footer">
              <span class="tag-pill accent">A–Z 首字母 / ↑ 从小到大</span>
              <span class="tag-pill">独立角色页面</span>
              <span class="tag-pill">自动记忆排序与位置</span>
            </div>
          </a>

          <a class="portal-card" href="rules.html">
            <div>
              <div class="portal-top">
                <span class="portal-num mono">03 / CANONICAL STANDARD V4</span>
                <span class="portal-icon">{SVGS["arrow_up_right"]}</span>
              </div>
              <h3 class="portal-title">衡天多维战力量级体系（第四版）</h3>
              <p class="portal-text">无删减全文展示：涵盖总则与违规审查、0.14.2 归因审查、1.5 完整书写规范、全量级定义、论外基数序数双轴、10.8 标注图与动图处理及超长篇通读流程。</p>
            </div>
            <div class="portal-footer">
              <span class="tag-pill accent">{rules_lines:,} 行完整原文</span>
              <span class="tag-pill">{rules_toc_count} 节目录实时联动</span>
            </div>
          </a>

          <a class="portal-card" href="materials.html">
            <div>
              <div class="portal-top">
                <span class="portal-num mono">04 / PHYSICS &amp; MATERIALS DB</span>
                <span class="portal-icon">{SVGS["arrow_up_right"]}</span>
              </div>
              <h3 class="portal-title">材质与破坏能量数据库（第二版）</h3>
              <p class="portal-text">完整收录常规岩石与金属力学强度、碎裂/粉碎/熔化/汽化至核子完全解离的全破坏方式比能（J/cm³），以及白矮星与中子星外壳极端物理锚点。</p>
            </div>
            <div class="portal-footer">
              <span class="tag-pill accent">{materials_lines:,} 行完整原文</span>
              <span class="tag-pill">破坏比能速查表</span>
            </div>
          </a>
        </div>
      </section>

      <section class="section-block">
        <div class="section-header">
          <div>
            <span class="section-kicker">Scale Spectrum</span>
            <h2 class="section-title">六大量级跨度速览</h2>
          </div>
          <a class="btn btn-secondary btn-sm" href="tiers.html">查看全部 98 档 →</a>
        </div>
        <div class="horizon-grid">
          {horizon_html}
        </div>
      </section>

      {featured_section}

      <section class="section-block">
        <div class="section-header">
          <div>
            <span class="section-kicker">Methodology</span>
            <h2 class="section-title">七维并列与五态证据规范</h2>
          </div>
          <a class="btn btn-secondary btn-sm" href="rules.html">阅读第四版总则 →</a>
        </div>
        <div class="principles-grid">
          <div class="principle-card">
            <h3 class="principle-title">七维独立计分（缺项不反推）</h3>
            <p class="principle-desc">
              除 0.11 条「整体掌控物质与结构可单向推出破坏」外，破坏、防御、速度、算力、场域与特性严格独立记录，原文未涉及之维度一律记为〔缺〕。
            </p>
            <div class="pill-cluster">
              <span class="tag-pill"><strong class="mono">破</strong> 破坏能量</span>
              <span class="tag-pill"><strong class="mono">控</strong> 整体掌控</span>
              <span class="tag-pill"><strong class="mono">域</strong> 作用范围</span>
              <span class="tag-pill"><strong class="mono">御</strong> 防御承受</span>
              <span class="tag-pill"><strong class="mono">速</strong> 机动速度</span>
              <span class="tag-pill"><strong class="mono">算</strong> 图灵演算</span>
              <span class="tag-pill"><strong class="mono">性</strong> 机制特性</span>
            </div>
          </div>

          <div class="principle-card">
            <h3 class="principle-title">五级证据状态标识</h3>
            <p class="principle-desc">
              所有定级须经 0.14.2「归因与知情度审查」（在场、知情、记忆可靠、表现一致、无后文推翻、归因准确）及 10.8「标注图与动图处理」核验，并显式标注证据等级。
            </p>
            <div class="pill-cluster">
              <span class="tag-pill"><span class="ev-badge ev-confirmed">〔实〕</span> 已确认表现</span>
              <span class="tag-pill"><span class="ev-badge ev-lower">〔下〕</span> 保守下限</span>
              <span class="tag-pill"><span class="ev-badge ev-inferred">〔推〕</span> 规则单向推定</span>
              <span class="tag-pill"><span class="ev-badge ev-hidden">〔隐〕</span> 隐含结构锚点</span>
              <span class="tag-pill"><span class="ev-badge ev-missing">〔缺〕</span> 原文未涉及</span>
            </div>
          </div>
        </div>
      </section>
    </div>
    """
    return render_shell(title="首页", page_id="home", active_nav="home", body_html=body, root_prefix="./")


def build_tiers_page(
    tiers: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    all_chars: List[Dict[str, Any]],
) -> str:
    group_map = {g["id"]: g for g in groups}
    char_count_by_tier: Dict[str, int] = {}
    for c in all_chars:
        ts = c.get("tier_slug")
        if ts:
            char_count_by_tier[ts] = char_count_by_tier.get(ts, 0) + 1

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
            c_cnt = char_count_by_tier.get(t["slug"], 0)
            char_pill = f'<span class="tag-pill accent">{c_cnt} 角色</span>' if c_cnt > 0 else ""
            cards_html.append(
                f"""
                <a class="tier-card" data-domain="{esc(t['domain'])}" href="tier/{esc(t['slug'])}.html">
                  <div class="tier-card-top">
                    <span class="tier-badge mono">⊙ {esc(t['code'])}</span>
                    <span class="tier-top-right">{char_pill}<span class="tier-seq mono">{order_str}</span></span>
                  </div>
                  <div class="tier-name-row">
                    <h3 class="tier-name">{esc(t['name'])}</h3>
                    <span class="tier-family">{esc(t['family'])}</span>
                  </div>
                  <div class="tier-energy mono">{esc(t['energy'])}</div>
                  <p class="tier-scale">{esc(t['scale'])}</p>
                  <div class="tier-foot">
                    <span>{esc(t['model'])}</span>
                    {SVGS["arrow_up_right"]}
                  </div>
                </a>"""
            )
        ssr_sections.append(
            f"""
            <section class="group-section" id="group-{esc(gid)}">
              <div class="group-header">
                <h2 class="group-title">{esc(g['title'])}</h2>
                <span class="group-sub">{esc(g['subtitle'])} · {len(g_items)} 档</span>
              </div>
              <div class="tier-grid">{''.join(cards_html)}</div>
            </section>"""
        )

    body = f"""
    <div class="container">
      <div class="page-header">
        <div class="page-header-art" aria-hidden="true">
          <img class="page-header-img" src="static/img/monolith-scale.jpg" alt="">
        </div>
        <div class="page-header-body">
          <div class="nav-crumb-row">
            <button type="button" class="back-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>量级分类</span>
            </nav>
          </div>
          <div class="page-title-row">
            <div>
              <h1 class="page-title">量级分类天梯（从小到大）</h1>
              <p class="page-desc">
                依据《衡天⊙ 多维战力量级体系（第四版）》严格按<strong>从小到大（#01 昆虫级 → #97 论天最上）</strong>单向递增排列。修饰符遵循 <code>▽ 弱</code> &lt; <code>○ 标准</code> &lt; <code>△ 强</code> &lt; <code>◆ 极</code> &lt; <code>☆ 超</code>。
              </p>
            </div>
            <span class="count-badge mono" id="tier-result-count">{len(tiers)} / {len(tiers)} 档</span>
          </div>
        </div>
      </div>

      <div class="control-panel">
        <div class="control-row">
          <div class="control-cluster">
            <span class="rule-indicator mono">↑ 排列基准：从小到大 (#01 → #97)</span>
            <div class="seg-group" role="group" aria-label="视图模式">
              <button type="button" class="seg-btn active" data-tier-view="card">分阶卡片</button>
              <button type="button" class="seg-btn" data-tier-view="flat">连续天梯</button>
              <button type="button" class="seg-btn" data-tier-view="table">紧凑总表</button>
            </div>
          </div>

          <div class="search-field">
            <input type="search" class="search-input" id="tier-filter-input" placeholder="筛选代字、名称、能量或参照物（如 宇◆、2.24×10³²）…" autocomplete="off">
            <button type="button" class="clear-input-btn" id="tier-filter-clear">清空</button>
          </div>
        </div>

        <div class="control-row divider-top">
          <div class="chip-rail" role="group" aria-label="量级区间筛选">
            <button type="button" class="chip-btn active" data-tier-seg="all">全量级 (98)</button>
            <button type="button" class="chip-btn" data-tier-seg="terrestrial">个体～行星阶 (41)</button>
            <button type="button" class="chip-btn" data-tier-seg="stellar">巨行星～恒星阶 (12)</button>
            <button type="button" class="chip-btn" data-tier-seg="transition">星际过渡带 (4)</button>
            <button type="button" class="chip-btn" data-tier-seg="cosmic">恒星系～多元高维 (25)</button>
            <button type="button" class="chip-btn" data-tier-seg="fgh">广义无限 FGH (7)</button>
            <button type="button" class="chip-btn" data-tier-seg="beyond">论外～论天 (8)</button>
            <button type="button" class="chip-btn" data-tier-seg="unranked">待定 (1)</button>
          </div>
        </div>
      </div>

      <div class="content-section" id="tiers-explorer-mount">
        {''.join(ssr_sections)}
      </div>
    </div>
    """
    return render_shell(title="量级分类（从小到大）", page_id="tiers", active_nav="tiers", body_html=body, root_prefix="./")


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
    tier_by_slug = {t["slug"]: t for t in tiers}
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
            neighbors = ranked[max(0, idx - 2) : min(len(ranked), idx + 3)]

        rule_sec_title = t.get("rule_section", "")
        rule_anchor = rules_title_to_id.get(rule_sec_title, "")
        rule_href = f"../rules.html#{rule_anchor}" if rule_anchor else "../rules.html"

        chars_in_tier = [c for c in all_chars if c.get("tier_slug") == t["slug"]]
        if chars_in_tier:
            char_list_html = (
                '<div class="char-grid">'
                + "".join(render_char_card_html(c, tier_by_slug, "../") for c in chars_in_tier)
                + "</div>"
            )
        else:
            char_list_html = f"""
            <div class="empty-notice">
              <span>当前档位暂无已收录角色档案。</span>
              <a class="btn btn-secondary btn-sm" href="../characters.html">前往角色分类 →</a>
            </div>
            """

        neighbor_section = ""
        if neighbors:
            rows = "".join(
                f'<a class="neighbor-row {"current" if nb["slug"] == t["slug"] else ""}" href="{esc(nb["slug"])}.html">'
                f'<span class="mono">#{nb["order"]:02d} · ⊙ {esc(nb["code"])}</span>'
                f'<span>{esc(nb["name"])}</span>'
                f'<span class="mono">{esc(nb["energy"])}</span>'
                f"</a>"
                for nb in neighbors
            )
            neighbor_section = f"""
            <section class="section-block">
              <div class="section-header">
                <h2 class="section-title">相邻天梯刻度（从小到大连续上下文）</h2>
              </div>
              <div class="neighbor-stack">{rows}</div>
            </section>
            """

        prev_html = (
            f"""<a class="pager-card" href="{esc(prev_t['slug'])}.html">
                  <span class="pager-dir">← 上一档（更低量级）</span>
                  <span class="pager-title">#{prev_t['order']:02d} · ⊙ {esc(prev_t['code'])} {esc(prev_t['name'])}</span>
                  <span class="pager-sub mono">{esc(prev_t['energy'])}</span>
                </a>"""
            if prev_t
            else """<div class="pager-card disabled">
                      <span class="pager-dir">← 起点档位</span>
                      <span class="pager-title">已是最低量级（#01 昆虫级）</span>
                    </div>"""
        )

        next_html = (
            f"""<a class="pager-card next" href="{esc(next_t['slug'])}.html">
                  <span class="pager-dir">下一档（更高量级） →</span>
                  <span class="pager-title">#{next_t['order']:02d} · ⊙ {esc(next_t['code'])} {esc(next_t['name'])}</span>
                  <span class="pager-sub mono">{esc(next_t['energy'])}</span>
                </a>"""
            if next_t
            else """<div class="pager-card next disabled">
                      <span class="pager-dir">顶点档位 →</span>
                      <span class="pager-title">已是最高量级（#97 论天最上）</span>
                    </div>"""
        )

        order_badge = "待定档" if is_unranked else f"序位 #{t['order']:02d} / 97"

        body = f"""
        <div class="container detail-stack">
          <div class="subpage-bar">
            <button type="button" class="back-btn js-smart-back" data-fallback="tiers.html" data-fallback-name="量级分类">
              {SVGS["arrow_left"]} <span class="js-back-label">返回量级分类</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="../index.html">首页</a>
              <span>/</span>
              <a href="../tiers.html">量级分类</a>
              <span>/</span>
              <span>⊙ {esc(t['code'])} {esc(t['name'])}</span>
            </nav>
          </div>

          <section class="dossier-header">
            <div class="page-header-art" aria-hidden="true">
              <img class="page-header-img" src="../static/img/monolith-scale.jpg" alt="">
            </div>
            <div class="dossier-body">
              <div class="dossier-top">
                <div>
                  <div class="char-tags">
                    <span class="tier-badge gold mono">⊙ {esc(t['code'])}</span>
                    <span class="count-badge mono">{order_badge}</span>
                    <span class="tag-pill">{esc(g['title'])}</span>
                  </div>
                  <h1 class="page-title">{esc(t['name'])} · {esc(t['family'])}系</h1>
                  <p class="page-desc">{esc(t.get('notes', ''))}</p>
                </div>
                <a class="btn btn-secondary btn-sm" href="{rule_href}">
                  查阅《衡天第四版》对应章节 {SVGS["arrow_up_right"]}
                </a>
              </div>

              <div class="full-writing-box">
                <div class="box-kicker">《衡天⊙ 第四版》1.5 完整书写推荐格式（首次出现须写全称与标准）</div>
                <div>综合量级：<span class="mono">⊙{esc(t['code'])}</span>——{esc(t['name'])}（{esc(t['scale'])}，能量/结构基准 <span class="mono">{esc(t['energy'])}</span>）</div>
              </div>
            </div>
          </section>

          <section class="spec-grid">
            <div class="spec-card">
              <div class="spec-label">能量阈值 / 数学定义</div>
              <div class="spec-val accent mono">{esc(t['energy'])}</div>
            </div>
            <div class="spec-card">
              <div class="spec-label">覆盖尺度与典型参照物</div>
              <div class="spec-val">{esc(t['scale'])}</div>
            </div>
            <div class="spec-card">
              <div class="spec-label">物理 / 数学计算模型</div>
              <div class="spec-val">{esc(t['model'])}</div>
            </div>
            <div class="spec-card">
              <div class="spec-label">检索拼音索引</div>
              <div class="spec-val mono">首字母 {(t.get('initial') or '#').upper()} · {esc(t.get('code_pinyin', ''))} / {esc(t.get('full_pinyin', ''))}</div>
            </div>
          </section>

          {neighbor_section}

          <section class="section-block">
            <div class="section-header">
              <h2 class="section-title">本档位已收录角色（{len(chars_in_tier)}）</h2>
            </div>
            {char_list_html}
          </section>

          <div class="pager-grid">
            {prev_html}
            {next_html}
          </div>
        </div>
        """

        page_html = render_shell(
            title=f"⊙{t['code']} {t['name']}",
            page_id=f"tier-{t['slug']}",
            active_nav="tiers",
            body_html=body,
            root_prefix="../",
        )
        (TIER_OUT_DIR / f"{t['slug']}.html").write_text(page_html, encoding="utf-8")


def build_characters_page(all_chars: List[Dict[str, Any]], tiers: List[Dict[str, Any]]) -> str:
    tier_by_slug = {t["slug"]: t for t in tiers}
    sorted_chars = sorted(
        all_chars,
        key=lambda c: (
            tier_by_slug.get(c.get("tier_slug", ""), {}).get("order", 999),
            c.get("pinyin") or c.get("name") or "",
        ),
    )

    all_series = sorted({c["series"] for c in all_chars if c.get("series")})
    series_options_html = f'<option value="all">全部作品（{len(all_series)}）</option>' + "".join(
        f'<option value="{esc(s)}">{esc(s)}</option>' for s in all_series
    )

    if sorted_chars:
        ssr_cards = [render_char_card_html(c, tier_by_slug, "") for c in sorted_chars]
        ssr_mount_inner = f"""
        <section class="group-section" id="char-scale-list">
          <div class="group-header">
            <h2 class="group-title">按主档量级从小到大排列（低量级 → 高量级）</h2>
            <span class="group-sub">{len(sorted_chars)} 位角色</span>
          </div>
          <div class="char-grid">{"".join(ssr_cards)}</div>
        </section>"""
    else:
        ssr_mount_inner = """
        <div class="empty-state-box">
          <h3 class="empty-state-title">当前暂未收录角色档案</h3>
          <p class="empty-state-sub">角色库已清空待录。后续在 data/characters.json 中录入角色后，将自动生成专属独立页面并支持按量级从小到大与按首字母 A–Z 排序。</p>
        </div>"""

    body = f"""
    <div class="container">
      <div class="page-header">
        <div class="page-header-art" aria-hidden="true">
          <img class="page-header-img" src="static/img/character-chronicle.jpg" alt="">
        </div>
        <div class="page-header-body">
          <div class="nav-crumb-row">
            <button type="button" class="back-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>角色分类</span>
            </nav>
          </div>
          <div class="page-title-row">
            <div>
              <h1 class="page-title">角色战力档案库</h1>
              <p class="page-desc">
                支持<strong>按主档量级从小到大</strong>与<strong>按拼音首字母（A–Z）</strong>双模式切换；点击角色卡片直接进入<strong>独立角色档案页面</strong>，返回时自动恢复当前排序与浏览位置。
              </p>
            </div>
            <span class="count-badge mono" id="char-result-count">{len(all_chars)} / {len(all_chars)} 位</span>
          </div>
        </div>
      </div>

      <div class="control-panel">
        <div class="control-row">
          <div class="control-cluster">
            <div class="seg-group" role="group" aria-label="角色排序方式">
              <button type="button" class="seg-btn active" data-char-sort="asc">↑ 按量级从小到大</button>
              <button type="button" class="seg-btn" data-char-sort="alpha">A–Z 按首字母排序</button>
            </div>
            <select class="select-control" id="char-series-select" aria-label="按作品筛选">
              {series_options_html}
            </select>
          </div>

          <div class="search-field">
            <input type="search" class="search-input" id="char-filter-input" placeholder="检索角色名、首字母、出处或量级代字…" autocomplete="off">
          </div>
        </div>

        <div class="control-row divider-top">
          <div class="chip-rail" role="group" aria-label="角色所属量级区间">
            <button type="button" class="chip-btn active" data-char-domain="all">全部区间</button>
            <button type="button" class="chip-btn" data-char-domain="terrestrial">个体～行星阶</button>
            <button type="button" class="chip-btn" data-char-domain="stellar">巨行星～恒星阶</button>
            <button type="button" class="chip-btn" data-char-domain="transition">星际过渡带</button>
            <button type="button" class="chip-btn" data-char-domain="cosmic">恒星系～多元高维</button>
            <button type="button" class="chip-btn" data-char-domain="fgh">广义无限 FGH</button>
            <button type="button" class="chip-btn" data-char-domain="beyond">论外～论天</button>
          </div>
        </div>
      </div>

      <div class="alpha-bar" id="char-alpha-bar" aria-label="首字母快速定位">
        <div class="alpha-letters" id="char-alpha-letters"></div>
      </div>

      <div class="content-section" id="chars-explorer-mount">
        {ssr_mount_inner}
      </div>
    </div>
    """
    return render_shell(
        title="角色分类（首字母 / 从小到大）",
        page_id="characters",
        active_nav="characters",
        body_html=body,
        root_prefix="./",
    )


def build_character_detail_pages(
    all_chars: List[Dict[str, Any]],
    tiers: List[Dict[str, Any]],
    groups: List[Dict[str, Any]],
    rules_title_to_id: Dict[str, str],
) -> List[Dict[str, str]]:
    if CHAR_OUT_DIR.exists():
        for old in CHAR_OUT_DIR.glob("*.html"):
            old.unlink()

    if not all_chars:
        if CHAR_OUT_DIR.exists() and not any(CHAR_OUT_DIR.iterdir()):
            CHAR_OUT_DIR.rmdir()
        return []

    CHAR_OUT_DIR.mkdir(parents=True, exist_ok=True)
    tier_by_slug = {t["slug"]: t for t in tiers}
    group_map = {g["id"]: g for g in groups}
    char_doc_index_entries: List[Dict[str, str]] = []

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

        mod_chips_html = "".join(f'<span class="tag-pill">{esc(m)}</span>' for m in (c.get("modifiers") or []))
        full_writing = c.get("full_writing") or (
            f"综合量级：⊙{t['code']}——{t['name']}（{t['scale']}，能量/结构基准 {t['energy']}）。"
        )

        avatar_src = resolve_rel_asset(c.get("image_url", ""), "../")
        monogram_inner = (
            f'<img src="{esc(avatar_src)}" alt="{esc(c["name"])}">'
            if avatar_src
            else esc(c["name"][:1])
        )

        submeta_parts = [f"出处：{esc(c.get('series') or '未标注')}", f"拼音首字母：{initial}"]
        if c.get("realm"):
            submeta_parts.append(f"形态：{esc(c['realm'])}")
        if c.get("alias"):
            submeta_parts.append(f"别称：{esc(c['alias'])}")
        if c.get("doc_date"):
            submeta_parts.append(f"定级版本：{esc(c['doc_date'])}")
        submeta_html = "<span>·</span>".join(f"<span>{p}</span>" for p in submeta_parts)

        portrait_src = resolve_rel_asset(c.get("portrait_url", ""), "../")
        if portrait_src:
            portrait_caption = esc(c.get("portrait_caption") or f"{c['name']} 官方角色图")
            dossier_body_html = f"""
            <div class="dossier-body has-portrait">
              <div class="dossier-main-col">
                <div class="dossier-top">
                  <div class="dossier-title-block">
                    <div class="char-monogram lg">{monogram_inner}</div>
                    <div>
                      <h1 class="page-title">{esc(c['name'])}</h1>
                      <div class="dossier-submeta">{submeta_html}</div>
                    </div>
                  </div>

                  <div class="dossier-seal-col">
                    <a class="tier-seal-link mono" href="../tier/{esc(t['slug'])}.html" title="查看所属主档规格页">
                      <span>⊙ {esc(t['code'])}</span>
                      <span>{esc(t['name'])}</span>
                      <span>{t_order_str}</span>
                      {SVGS["arrow_up_right"]}
                    </a>
                    <div class="char-tags">
                      <span class="tag-pill accent">{esc(g['title'])}</span>
                      {mod_chips_html}
                    </div>
                  </div>
                </div>

                <p class="page-desc">{esc(c.get('summary') or '')}</p>

                <div class="full-writing-box">
                  <div class="box-kicker">《衡天⊙ 第四版》1.5 正式完整书写摘要</div>
                  <div>{format_evidence_html(full_writing)}</div>
                  {f'<div class="box-subnote">证据链核验摘要：{format_evidence_html(c["credibility"])}</div>' if c.get("credibility") else ""}
                </div>

                <div class="dossier-actions-row">
                  <a class="btn btn-secondary btn-sm" href="../tier/{esc(t['slug'])}.html">
                    所属主档：⊙{esc(t['code'])} {esc(t['name'])}（{t_order_str}） {SVGS["arrow_up_right"]}
                  </a>
                  <a class="btn btn-ghost btn-sm" href="{rule_href}">
                    对照《衡天第四版》{esc(rule_sec_title or '基准条文')} →
                  </a>
                </div>
              </div>

              <aside class="char-portrait-stage" aria-label="角色官方立绘">
                <div class="char-portrait-canvas">
                  <img class="char-portrait-img" src="{esc(portrait_src)}" alt="{esc(c['name'])}（{esc(c.get('series') or '')}）官方立绘">
                </div>
                <div class="char-portrait-caption">{portrait_caption}</div>
              </aside>
            </div>"""
        else:
            dossier_body_html = f"""
            <div class="dossier-body">
              <div class="dossier-top">
                <div class="dossier-title-block">
                  <div class="char-monogram lg">{monogram_inner}</div>
                  <div>
                    <h1 class="page-title">{esc(c['name'])}</h1>
                    <div class="dossier-submeta">{submeta_html}</div>
                  </div>
                </div>

                <div class="dossier-seal-col">
                  <a class="tier-seal-link mono" href="../tier/{esc(t['slug'])}.html" title="查看所属主档规格页">
                    <span>⊙ {esc(t['code'])}</span>
                    <span>{esc(t['name'])}</span>
                    <span>{t_order_str}</span>
                    {SVGS["arrow_up_right"]}
                  </a>
                  <div class="char-tags">
                    <span class="tag-pill accent">{esc(g['title'])}</span>
                    {mod_chips_html}
                  </div>
                </div>
              </div>

              <p class="page-desc">{esc(c.get('summary') or '')}</p>

              <div class="full-writing-box">
                <div class="box-kicker">《衡天⊙ 第四版》1.5 正式完整书写（首次出现展开全称、标准与能量）</div>
                <div>{format_evidence_html(full_writing)}</div>
                {f'<div class="box-subnote">证据链核验摘要：{format_evidence_html(c["credibility"])}</div>' if c.get("credibility") else ""}
              </div>
            </div>"""

        has_full_doc = False
        center_content_html = ""
        doc_rel_path = c.get("doc_path")
        if doc_rel_path and (ROOT / doc_rel_path).exists():
            has_full_doc = True
            raw_doc_md = (ROOT / doc_rel_path).read_text(encoding="utf-8")
            doc_filename = Path(doc_rel_path).name
            doc_renderer = VerbatimMarkdownRenderer(image_map=c.get("image_map"))
            rendered_doc_html = doc_renderer.render(raw_doc_md)
            doc_lines = len(raw_doc_md.splitlines())
            doc_chars = len(raw_doc_md)
            toc_links_html = "".join(
                f'<a class="toc-item toc-lvl-{item["level"]}" href="#{esc(item["id"])}">{esc(item["title"])}</a>'
                for item in doc_renderer.toc
            )
            for sec in doc_renderer.sections_for_index:
                clean_txt = re.sub(r"\s+", " ", sec["text"]).strip()
                char_doc_index_entries.append(
                    {
                        "type": "char",
                        "code": f"{c.get('initial', '')} ⊙{t['code']}",
                        "title": f"{c['name']} · {sec['title']}",
                        "badge": f"角色原文 · ⊙{t['code']}",
                        "pinyin": c.get("pinyin", ""),
                        "text": clean_txt,
                        "url": f"character/{c['slug']}.html#{sec['id']}",
                    }
                )

            center_content_html = f"""
          <div class="doc-layout">
            <aside class="doc-sidebar" id="doc-sidebar" aria-label="定级档案目录">
              <div class="toc-head">
                <div class="toc-head-row">
                  <span>定级全文目录</span>
                  <span class="mono">{len(doc_renderer.toc)} 节</span>
                </div>
                <input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选条目章节…" autocomplete="off">
              </div>
              <nav class="toc-list" id="toc-nav">
                {toc_links_html}
              </nav>
            </aside>

            <article class="doc-panel">
              <div class="doc-toolbar">
                <div class="doc-source-info">
                  <span>源文件：<code class="mono">{esc(doc_filename)}</code></span>
                  <span>·</span>
                  <span class="mono">{doc_lines:,} 行 / {doc_chars:,} 字</span>
                  <span>·</span>
                  <span class="ev-badge ev-confirmed">100% 完整原文无删减</span>
                </div>
                <div class="doc-tools">
                  <div class="doc-find-box">
                    <input type="search" class="doc-find-input" id="doc-find-input" placeholder="页内定位词句…">
                    <button type="button" class="tool-btn" id="doc-find-next" title="跳转到下一处匹配">定位</button>
                    <span class="doc-find-count mono" id="doc-find-count"></span>
                  </div>
                  <button type="button" class="tool-btn" id="doc-font-dec" title="缩小正文字号">A-</button>
                  <button type="button" class="tool-btn" id="doc-font-inc" title="放大正文字号">A+</button>
                  <button type="button" class="tool-btn" id="doc-wide-toggle" title="切换宽屏表格阅读模式">宽屏</button>
                </div>
              </div>

              <div class="markdown-body">
                {rendered_doc_html}
              </div>
            </article>
          </div>"""
        else:
            dims = c.get("dims") or {}
            dim_cards_html: List[str] = []
            for dim_key, dim_title, dim_desc in DIM_META:
                raw_val = dims.get(dim_key, "〔缺〕")
                wide_cls = "wide" if dim_key == "性" else ""
                dim_cards_html.append(
                    f"""
                    <div class="dim-detail-card {wide_cls}">
                      <div class="dim-detail-head">
                        <span class="dim-symbol mono">{esc(dim_key)}</span>
                        <div>
                          <div class="dim-title">{esc(dim_title)}</div>
                          <div class="dim-desc">{esc(dim_desc)}</div>
                        </div>
                      </div>
                      <div class="dim-value">{format_evidence_html(raw_val)}</div>
                    </div>"""
                )
            center_content_html = f"""
          <section class="section-block">
            <div class="section-header">
              <div>
                <span class="section-kicker">Seven-Dimension Assessment</span>
                <h2 class="section-title">七维战力分项评定</h2>
              </div>
            </div>
            <div class="dim-matrix-grid">
              {"".join(dim_cards_html)}
            </div>
          </section>"""

        prev_html = (
            f"""<a class="pager-card" href="{esc(prev_c['slug'])}.html">
                  <span class="pager-dir">← 上一位角色（更低量级）</span>
                  <span class="pager-title">{esc(prev_c['name'])}</span>
                  <span class="pager-sub mono">⊙ {esc(tier_by_slug.get(prev_c.get('tier_slug',''), {}).get('code', '待定'))} · 首字母 {esc((prev_c.get('initial') or '#').upper())}</span>
                </a>"""
            if prev_c
            else """<div class="pager-card disabled">
                      <span class="pager-dir">← 序列起点</span>
                      <span class="pager-title">已是当前库内最低量级角色</span>
                    </div>"""
        )

        next_html = (
            f"""<a class="pager-card next" href="{esc(next_c['slug'])}.html">
                  <span class="pager-dir">下一位角色（更高量级） →</span>
                  <span class="pager-title">{esc(next_c['name'])}</span>
                  <span class="pager-sub mono">⊙ {esc(tier_by_slug.get(next_c.get('tier_slug',''), {}).get('code', '待定'))} · 首字母 {esc((next_c.get('initial') or '#').upper())}</span>
                </a>"""
            if next_c
            else """<div class="pager-card next disabled">
                      <span class="pager-dir">序列顶点 →</span>
                      <span class="pager-title">已是当前库内最高量级角色</span>
                    </div>"""
        )

        body = f"""
        <div class="container detail-stack">
          <div class="subpage-bar">
            <button type="button" class="back-btn js-smart-back" data-fallback="characters.html" data-fallback-name="角色档案库">
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

          <section class="dossier-header">
            <div class="page-header-art" aria-hidden="true">
              <img class="page-header-img" src="../static/img/character-chronicle.jpg" alt="">
            </div>
            {dossier_body_html}
          </section>

          {center_content_html}

          <section class="section-block">
            <div class="section-header">
              <div>
                <span class="section-kicker">Tier Anchor</span>
                <h2 class="section-title">所属主档物理 / 数学基准对照</h2>
              </div>
              <a class="btn btn-secondary btn-sm" href="../tier/{esc(t['slug'])}.html">
                进入 ⊙{esc(t['code'])} 量级页 {SVGS["arrow_up_right"]}
              </a>
            </div>
            <div class="spec-grid">
              <div class="spec-card">
                <div class="spec-label">主档代字与序位</div>
                <div class="spec-val accent mono">⊙ {esc(t['code'])} · {esc(t['name'])}（{t_order_str}）</div>
              </div>
              <div class="spec-card">
                <div class="spec-label">能量阈值 / 超限基数</div>
                <div class="spec-val mono">{esc(t['energy'])}</div>
              </div>
              <div class="spec-card">
                <div class="spec-label">覆盖尺度与典型参照</div>
                <div class="spec-val">{esc(t['scale'])}</div>
              </div>
              <div class="spec-card">
                <div class="spec-label">对应《衡天第四版》章节</div>
                <div class="spec-val">
                  <a class="table-primary-link" href="{rule_href}">{esc(rule_sec_title or '查阅第四版规范原文')} →</a>
                </div>
              </div>
            </div>
          </section>

          <div class="pager-grid">
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
            has_toc_button=has_full_doc,
        )
        (CHAR_OUT_DIR / f"{c['slug']}.html").write_text(page_html, encoding="utf-8")

    return char_doc_index_entries


def build_fulltext_doc_page(
    *,
    page_id: str,
    active_nav: str,
    title: str,
    subtitle: str,
    source_filename: str,
    masthead_img: str,
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
        toc_links.append(f'<a class="toc-item toc-lvl-{lvl}" href="#{esc(hid)}">{esc(htitle)}</a>')

    body = f"""
    <div class="container">
      <div class="page-header">
        <div class="page-header-art" aria-hidden="true">
          <img class="page-header-img" src="{esc(masthead_img)}" alt="">
        </div>
        <div class="page-header-body">
          <div class="nav-crumb-row">
            <button type="button" class="back-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>{esc(title)}</span>
            </nav>
          </div>
          <div class="page-title-row">
            <div>
              <h1 class="page-title">{esc(title)}</h1>
              <p class="page-desc">{esc(subtitle)}</p>
            </div>
            <div class="header-side-actions">
              <span class="count-badge mono">全文无删减 · {line_count:,} 行 · {char_count:,} 字</span>
              <a class="btn btn-secondary btn-sm" href="{esc(other_doc_link[0])}">{esc(other_doc_link[1])} →</a>
            </div>
          </div>
        </div>
      </div>

      <div class="doc-layout">
        <aside class="doc-sidebar" id="doc-sidebar" aria-label="全文目录">
          <div class="toc-head">
            <div class="toc-head-row">
              <span>章节目录索引</span>
              <span class="mono">{len(renderer.toc)} 节</span>
            </div>
            <input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选目录章节…" autocomplete="off">
          </div>
          <nav class="toc-list" id="toc-nav">
            {''.join(toc_links)}
          </nav>
        </aside>

        <article class="doc-panel">
          <div class="doc-toolbar">
            <div class="doc-source-info">
              <span>源文件：<code class="mono">{esc(source_filename)}</code></span>
              <span>·</span>
              <span class="ev-badge ev-confirmed">100% 完整原文展示</span>
            </div>
            <div class="doc-tools">
              <div class="doc-find-box">
                <input type="search" class="doc-find-input" id="doc-find-input" placeholder="页内定位词句…">
                <button type="button" class="tool-btn" id="doc-find-next" title="跳转到下一处匹配">定位</button>
                <span class="doc-find-count mono" id="doc-find-count"></span>
              </div>
              <button type="button" class="tool-btn" id="doc-font-dec" title="缩小正文字号">A-</button>
              <button type="button" class="tool-btn" id="doc-font-inc" title="放大正文字号">A+</button>
              <button type="button" class="tool-btn" id="doc-wide-toggle" title="切换宽屏表格阅读模式">宽屏</button>
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
    )
    return full_html, renderer.sections_for_index, title_to_id


def build_search_page() -> str:
    hot_queries = [
        "御兔",
        "城△",
        "宇◆",
        "标注图与动图",
        "完整书写",
        "归因与知情度",
        "超长篇",
        "外·门",
        "中子星外壳",
        "花岗岩",
        "莱因哈特",
    ]
    hot_chips = "".join(
        f'<button type="button" class="chip-btn" data-hot-query="{esc(q)}">{esc(q)}</button>'
        for q in hot_queries
    )

    body = f"""
    <div class="container">
      <div class="page-header">
        <div class="page-header-art" aria-hidden="true">
          <img class="page-header-img" src="static/img/cosmos-eclipse.jpg" alt="">
        </div>
        <div class="page-header-body">
          <div class="nav-crumb-row">
            <button type="button" class="back-btn js-smart-back" data-fallback="index.html" data-fallback-name="首页">
              {SVGS["arrow_left"]} <span class="js-back-label">返回首页</span>
            </button>
            <nav class="breadcrumbs" aria-label="面包屑">
              <a href="index.html">首页</a>
              <span>/</span>
              <span>全站搜索</span>
            </nav>
          </div>
          <div class="page-title-row">
            <div>
              <h1 class="page-title">全站即时检索引擎</h1>
              <p class="page-desc">
                跨<strong>98 个量级档位</strong>、<strong>角色档案</strong>、《衡天量级体系（第四版）》全文与《材质与破坏能量数据库（第二版）》全文毫秒级检索。
              </p>
            </div>
            <span class="count-badge mono" id="dedicated-search-count">准备就绪</span>
          </div>
        </div>
      </div>

      <div class="control-panel">
        <div class="search-field full">
          <input type="search" class="search-input lg" id="dedicated-search-input" placeholder="输入关键词（支持空格分词组合检索，如：星○ 2.24、标注图 帧号、归因 审查、花岗岩 粉碎）…" autofocus>
        </div>

        <div class="control-row">
          <div class="chip-rail">
            <span class="rail-label">范围：</span>
            <button type="button" class="chip-btn active" data-page-search-type="all">全部类别</button>
            <button type="button" class="chip-btn" data-page-search-type="tier">量级分类 (98)</button>
            <button type="button" class="chip-btn" data-page-search-type="char">角色档案</button>
            <button type="button" class="chip-btn" data-page-search-type="rules">衡天第四版全文</button>
            <button type="button" class="chip-btn" data-page-search-type="materials">材质能量库全文</button>
          </div>
        </div>

        <div class="control-row divider-top">
          <div class="chip-rail">
            <span class="rail-label">热词：</span>
            {hot_chips}
          </div>
        </div>
      </div>

      <div class="content-section" id="dedicated-search-results"></div>
    </div>
    """
    return render_shell(title="全站搜索", page_id="search", active_nav="search", body_html=body, root_prefix="./")


def build_search_index_bundle(
    *,
    tiers_payload: Dict[str, Any],
    all_chars: List[Dict[str, Any]],
    char_doc_sections: List[Dict[str, str]],
    rules_sections: List[Dict[str, str]],
    materials_sections: List[Dict[str, str]],
) -> str:
    index_entries: List[Dict[str, str]] = []
    tiers = tiers_payload["tiers"]
    tier_by_slug = {t["slug"]: t for t in tiers}

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

    for c in all_chars:
        t = tier_by_slug.get(c.get("tier_slug", ""))
        t_code = t["code"] if t else "待定"
        t_name = t["name"] if t else "待定"
        dims_str = " ".join(f"{k}:{v}" for k, v in (c.get("dims") or {}).items())
        index_entries.append(
            {
                "type": "char",
                "code": f"{c.get('initial', '')} ⊙{t_code} {c.get('alias', '')}",
                "title": f"{c['name']}（{c.get('series', '未知出处')}）",
                "badge": f"角色 · ⊙{t_code} {t_name}",
                "pinyin": c.get("pinyin", ""),
                "text": f"{c.get('summary', '')} ｜ {c.get('full_writing', '')} ｜ {dims_str}",
                "url": f"character/{c['slug']}.html",
            }
        )

    index_entries.extend(char_doc_sections)

    for sec in rules_sections:
        clean_txt = re.sub(r"\s+", " ", sec["text"]).strip()
        index_entries.append(
            {
                "type": "rules",
                "code": "",
                "title": f"衡天第四版 · {sec['title']}",
                "badge": "衡天第四版",
                "pinyin": "",
                "text": clean_txt,
                "url": f"rules.html#{sec['id']}",
            }
        )

    for sec in materials_sections:
        clean_txt = re.sub(r"\s+", " ", sec["text"]).strip()
        index_entries.append(
            {
                "type": "materials",
                "code": "",
                "title": f"材质库 · {sec['title']}",
                "badge": "材质能量库",
                "pinyin": "",
                "text": clean_txt,
                "url": f"materials.html#{sec['id']}",
            }
        )

    client_data = {
        "groups": tiers_payload["groups"],
        "tiers": tiers_payload["tiers"],
        "allCharacters": all_chars,
    }

    return (
        "/* Auto-generated by build_site.py v6.2 — DO NOT EDIT MANUALLY */\n"
        f"window.__POWERWIKI_DATA__ = {json.dumps(client_data, ensure_ascii=False, separators=(',', ':'))};\n"
        f"window.__POWERWIKI_INDEX__ = {json.dumps(index_entries, ensure_ascii=False, separators=(',', ':'))};\n"
    )


def main() -> None:
    tiers_payload = json.loads((DATA_DIR / "tiers.json").read_text(encoding="utf-8"))
    chars_payload = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8"))

    by_slug: Dict[str, Dict[str, Any]] = {}
    for entry in chars_payload.get("demo_archetypes", []):
        by_slug[entry["slug"]] = entry
    for entry in chars_payload.get("characters", []):
        by_slug[entry["slug"]] = entry
    all_chars = list(by_slug.values())

    rules_md = RULES_MD_PATH.read_text(encoding="utf-8")
    materials_md = MATERIALS_MD_PATH.read_text(encoding="utf-8")

    rules_html, rules_sections, rules_title_to_id = build_fulltext_doc_page(
        page_id="rules",
        active_nav="rules",
        title="衡天⊙ 多维战力量级体系（第四版·全文）",
        subtitle="完整收录总则、常见违规与归因审查、1.5 完整书写规范、全量级定义、论外基数序数双轴、10.8 标注图与动图处理及超长篇自行通读流程。",
        source_filename="衡天量级体系【第四版·最新】.md",
        masthead_img="static/img/cosmos-eclipse.jpg",
        md_text=rules_md,
        other_doc_link=("materials.html", "材质与破坏能量数据库"),
    )
    (ROOT / "rules.html").write_text(rules_html, encoding="utf-8")

    materials_html, materials_sections, _ = build_fulltext_doc_page(
        page_id="materials",
        active_nav="materials",
        title="材质与破坏能量数据库（第二版·全文）",
        subtitle="完整收录岩石/金属/生物力学强度、碎裂至核子解离破坏方式比能（J/cm³）、天体结合能与致密星物质锚点。",
        source_filename="材质与破坏能量数据库（新）.md",
        masthead_img="static/img/physics-lattice.jpg",
        md_text=materials_md,
        other_doc_link=("rules.html", "衡天量级体系（第四版）"),
    )
    (ROOT / "materials.html").write_text(materials_html, encoding="utf-8")

    tiers = tiers_payload["tiers"]
    groups = tiers_payload["groups"]

    (ROOT / "index.html").write_text(
        build_home_page(
            tiers,
            all_chars,
            rules_lines=len(rules_md.splitlines()),
            materials_lines=len(materials_md.splitlines()),
            rules_toc_count=len(rules_sections),
        ),
        encoding="utf-8",
    )
    (ROOT / "tiers.html").write_text(build_tiers_page(tiers, groups, all_chars), encoding="utf-8")
    build_tier_detail_pages(tiers, groups, all_chars, rules_title_to_id)

    (ROOT / "characters.html").write_text(build_characters_page(all_chars, tiers), encoding="utf-8")
    char_doc_sections = build_character_detail_pages(all_chars, tiers, groups, rules_title_to_id)

    (ROOT / "search.html").write_text(build_search_page(), encoding="utf-8")

    JS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    bundle_js = build_search_index_bundle(
        tiers_payload=tiers_payload,
        all_chars=all_chars,
        char_doc_sections=char_doc_sections,
        rules_sections=rules_sections,
        materials_sections=materials_sections,
    )
    (JS_OUT_DIR / "search-index.js").write_text(bundle_js, encoding="utf-8")

    print(
        f"[OK] PowerWiki v6.2 built successfully:\n"
        f"  - Core pages: index.html, tiers.html, characters.html, rules.html, materials.html, search.html\n"
        f"  - Standalone Tier pages: {len(tiers)} files in tier/*.html\n"
        f"  - Standalone Character pages: {len(all_chars)} files in character/*.html ({len(char_doc_sections)} full-text sections indexed)\n"
        f"  - Rules v4 TOC anchors: {len(rules_sections)} sections | Materials TOC anchors: {len(materials_sections)} sections"
    )


if __name__ == "__main__":
    main()
