#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
衡天⊙ PowerWiki Static Site Builder v9.1
Updated for 《衡天⊙ 多维战力量级体系（第五版）》 & Full-Text Character Dossiers
"""

from __future__ import annotations

import html
import json
import re
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DOCS_DIR = DATA_DIR / "docs"
TIER_OUT_DIR = ROOT / "tier"
CHAR_OUT_DIR = ROOT / "character"
JS_OUT_DIR = ROOT / "static" / "js"

RULES_MD_PATH = DOCS_DIR / "衡天量级体系【第五版·最新】.md"
MATERIALS_MD_PATH = DOCS_DIR / "材质与破坏能量数据库（新）.md"

SVGS = {
    "search": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>',
    "menu": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" x2="20" y1="7" y2="7"/><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="17" y2="17"/></svg>',
    "close": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>',
    "sun": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "arrow_left": '<svg class="svg-icon sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>',
    "arrow_up": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m18 15-6-6-6 6"/></svg>',
    "arrow_up_right": '<svg class="svg-icon sm card-arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M7 17L17 7"/><path d="M7 7h10v10"/></svg>',
    "toc": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="8" x2="21" y1="6" y2="6"/><line x1="8" x2="21" y1="12" y2="12"/><line x1="8" x2="21" y1="18" y2="18"/><line x1="3" x2="3.01" y1="6" y2="6"/><line x1="3" x2="3.01" y1="12" y2="12"/><line x1="3" x2="3.01" y1="18" y2="18"/></svg>',
    "home": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round"><path d="m4 11.5 8-7.5 8 7.5"/><path d="M6.5 10v9h11v-9M10 19v-5h4v5"/></svg>',
    "materials": '<svg class="svg-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.55" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3 8 4.5-8 4.5-8-4.5Z"/><path d="m4 12 8 4.5 8-4.5M4 16.5 12 21l8-4.5"/></svg>',
    "atlas": '<svg class="svg-icon portal-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.2"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(-32 12 12)"/><path d="M5 5.8 18.8 18.4"/></svg>',
    "dossier": '<svg class="svg-icon portal-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="3.2"/><path d="M5.5 20c.7-4.1 3-6.2 6.5-6.2s5.8 2.1 6.5 6.2M4 4h3M17 4h3"/></svg>',
    "library": '<svg class="svg-icon portal-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round"><path d="M3.5 5.5A3.5 3.5 0 0 1 7 2h5v17H7a3.5 3.5 0 0 0-3.5 3.5ZM20.5 5.5A3.5 3.5 0 0 0 17 2h-5v17h5a3.5 3.5 0 0 1 3.5 3.5Z"/></svg>',
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


def tier_art_stem(slug: str, group_id: str) -> str:
    """Use a tier-specific image when available, with the group art as a safe fallback."""
    unique_art = ROOT / "static" / "img" / "tiers" / f"{slug}.jpg"
    return slug if unique_art.is_file() else group_id


# Reading controls live in a right-hand rail so they never float over the article text.
READER_RAIL_HTML = """
            <aside class="reader-rail" role="group" aria-label="阅读显示设置">
              <span class="reader-rail-label mono" aria-hidden="true">字号</span>
              <div class="reader-rail-btns">
                <button type="button" class="tool-btn" id="doc-font-dec" aria-label="缩小正文字号" title="缩小正文字号">A−</button>
                <button type="button" class="tool-btn" id="doc-font-inc" aria-label="放大正文字号" title="放大正文字号">A+</button>
                <button type="button" class="tool-btn" id="doc-wide-toggle" aria-label="切换宽屏表格阅读模式" aria-pressed="false" title="切换宽屏表格阅读模式">宽屏</button>
              </div>
              <span class="reader-rail-readout mono" id="doc-font-readout">15.5px</span>
            </aside>"""


TIER_ART_TUNING_PATH = DATA_DIR / "tier-art-tuning.json"


def tier_art_tuning(slug: str) -> str:
    """Per-image crop focus + ink compensation for the 98 tier backgrounds.

    Deep-space renders are nearly black while the street-level renders are pale,
    so a single opacity makes half of them invisible and the other half noisy.
    Missing data degrades silently to the CSS defaults.
    """
    if not TIER_ART_TUNING_PATH.is_file():
        return ""
    cache = getattr(tier_art_tuning, "_cache", None)
    if cache is None:
        try:
            cache = json.loads(TIER_ART_TUNING_PATH.read_text()).get("images", {})
        except (ValueError, OSError):
            cache = {}
        setattr(tier_art_tuning, "_cache", cache)
    cfg = cache.get(slug)
    if not isinstance(cfg, dict):
        return ""
    parts = []
    x, y = cfg.get("x"), cfg.get("y")
    if isinstance(x, (int, float)) and isinstance(y, (int, float)):
        parts.append("--tier-art-position:%d%% %d%%" % (int(x), int(y)))
    for key, name in (("light", "--tier-art-alpha-light"), ("dark", "--tier-art-alpha-dark")):
        val = cfg.get(key)
        if isinstance(val, (int, float)):
            parts.append("%s:%.3f" % (name, float(val)))
    light, dark = cfg.get("light"), cfg.get("dark")
    if isinstance(light, (int, float)):
        parts.append("--tier-art-ink:%.3f" % min(max(float(light) * 2.9, 0.20), 0.42))
    if isinstance(dark, (int, float)):
        parts.append("--tier-art-ink-dark:%.3f" % min(max(float(dark) * 0.9 + 0.05, 0.18), 0.34))
    return ";".join(parts) if parts else ""


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
def get_image_dimensions(img_path: Path) -> Optional[Tuple[int, int]]:
    if not img_path.is_file():
        return None
    try:
        data = img_path.read_bytes()
    except OSError:
        return None
    # PNG
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
        w, h = struct.unpack(">II", data[16:24])
        return (int(w), int(h)) if w > 0 and h > 0 else None
    # WebP
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        chunk = data[12:16]
        if chunk == b"VP8 " and len(data) >= 30:
            w, h = struct.unpack("<HH", data[26:30])
            return (w & 0x3FFF, h & 0x3FFF)
        if chunk == b"VP8L" and len(data) >= 25:
            bits = struct.unpack("<I", data[21:25])[0]
            w = (bits & 0x3FFF) + 1
            h = ((bits >> 14) & 0x3FFF) + 1
            return (int(w), int(h))
        if chunk == b"VP8X" and len(data) >= 30:
            w = int.from_bytes(data[24:27], "little") + 1
            h = int.from_bytes(data[27:30], "little") + 1
            return (int(w), int(h))
    # JPEG
    if len(data) >= 4 and data[:2] == b"\xff\xd8":
        idx = 2
        n = len(data)
        sof_markers = {
            0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
        }
        while idx + 4 < n:
            if data[idx] != 0xFF:
                idx += 1
                continue
            while idx < n and data[idx] == 0xFF:
                idx += 1
            if idx >= n:
                break
            marker = data[idx]
            idx += 1
            if marker in (0xD8, 0xD9) or (0xD0 <= marker <= 0xD7):
                continue
            if idx + 2 > n:
                break
            seg_len = struct.unpack(">H", data[idx : idx + 2])[0]
            if seg_len < 2 or idx + seg_len > n:
                break
            if marker in sof_markers and idx + 7 <= n:
                h, w = struct.unpack(">HH", data[idx + 3 : idx + 7])
                return (int(w), int(h)) if w > 0 and h > 0 else None
            idx += seg_len
    return None


def classify_image_shape(w: int, h: int) -> str:
    if w <= 0 or h <= 0:
        return "portrait"
    ratio = w / float(h)
    if ratio > 1.22:
        return "landscape"
    if ratio < 0.85:
        return "portrait"
    return "square"


def strip_character_doc_front_banner(md_text: str) -> str:
    lines = md_text.splitlines()
    idx = 0
    n = len(lines)
    while idx < n and not lines[idx].strip():
        idx += 1
    if idx < n and re.match(r"^#\s+.+$", lines[idx].strip()):
        idx += 1
        while idx < n and not lines[idx].strip():
            idx += 1
        if idx < n and lines[idx].strip().startswith(">") and "定级" in lines[idx]:
            while idx < n and lines[idx].strip().startswith(">"):
                idx += 1
            while idx < n and not lines[idx].strip():
                idx += 1
        return "\n".join(lines[idx:])
    return md_text


def clean_index_text(text: str) -> str:
    """Turn raw Markdown collected by the renderer into readable search copy."""
    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"__(.+?)__", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"\1", text)
    text = re.sub(r"\\([\\`*_{}\[\]()#+\-.!|])", r"\1", text)
    text = text.replace("|", " · ")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(?:·\s*){2,}", "· ", text)
    return text.strip(" ·\t\n")


class VerbatimMarkdownRenderer:
    def __init__(
        self,
        image_map: Dict[str, str] | None = None,
        base_dir: Path | None = None,
    ) -> None:
        self.toc: List[Dict[str, Any]] = []
        self._slug_counts: Dict[str, int] = {}
        self.sections_for_index: List[Dict[str, str]] = []
        self.image_map: Dict[str, str] = dict(image_map or {})
        self.base_dir: Path = base_dir or ROOT

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
            joined = clean_index_text(" ".join(cur_sec_buf))
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
                dim_attr = ""
                if not re.match(r"^(https?:)?//", resolved_src):
                    local_img = (self.base_dir / resolved_src).resolve()
                    dims = get_image_dimensions(local_img)
                    if dims:
                        dim_attr = f' width="{dims[0]}" height="{dims[1]}"'
                cap_html = (
                    f'<figcaption class="md-figcaption">{self.render_inline(alt_raw)}</figcaption>'
                    if alt_raw
                    else ""
                )
                out.append(
                    f'<figure class="md-figure">'
                    f'<div class="md-figure-frame">'
                    f'<a class="md-figure-link" href="{esc(resolved_src)}" target="_blank" rel="noopener" title="点击查看原尺寸图片">'
                    f'<img class="md-img" src="{esc(resolved_src)}" alt="{esc(alt_raw)}"{dim_attr} loading="lazy">'
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
    body_class: str = "",
) -> str:
    r = root_prefix

    def nav_link(key: str, href: str, label: str, extra_cls: str = "", icon: str = "") -> str:
        base = f"nav-link {extra_cls}".strip()
        cls = f"{base} active" if active_nav == key else base
        icon_html = f'<span class="nav-icon">{SVGS[icon]}</span>' if icon else ""
        return f'<a class="{cls}" href="{r}{href}">{icon_html}<span>{label}</span></a>'

    def drawer_card(key: str, href: str, label: str, sub: str) -> str:
        cls = "drawer-card-link active" if active_nav == key else "drawer-card-link"
        return (
            f'<a class="{cls}" href="{r}{href}">'
            f'<span class="drawer-card-title"><span>{label}</span>{SVGS["arrow_up_right"]}</span>'
            f'<span class="drawer-card-sub">{sub}</span>'
            f"</a>"
        )

    def drawer_doc(key: str, href: str, label: str) -> str:
        cls = "drawer-doc-link active" if active_nav == key else "drawer-doc-link"
        return f'<a class="{cls}" href="{r}{href}"><span>{label}</span><span>→</span></a>'

    toc_dock_html = (
        f'<button type="button" class="dock-btn dock-toc-trigger" id="dock-toc-btn" title="展开章节目录" aria-label="展开章节目录">'
        f'{SVGS["toc"]}</button>'
        if has_toc_button
        else ""
    )

    shell_body_class = f"site-{active_nav} {body_class}".strip()
    reading_progress_html = (
        '\n  <div class="reading-progress" aria-hidden="true"><span id="reading-progress-bar"></span></div>'
        if has_toc_button
        else ""
    )

    page = f"""<!DOCTYPE html>
<html lang="zh-CN" data-theme="light" data-root="{r}" data-page-id="{esc(page_id)}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
  <meta name="theme-color" id="theme-color-meta" content="#f6f7f4">
  <meta name="color-scheme" content="light dark">
  <title>{esc(title)} · 衡天⊙ PowerWiki</title>
  <meta name="description" content="衡天⊙ PowerWiki — 基于《衡天⊙ 多维战力量级体系（第五版）》与《材质与破坏能量数据库（第二版）》构建的多维战力与量级百科。">
  <script>
    (function() {{
      var t = null;
      try {{ t = localStorage.getItem('pw_theme_v2'); }} catch (e) {{}}
      if (t !== 'light' && t !== 'dark') {{
        try {{
          var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
          t = dark ? 'dark' : 'light';
          localStorage.setItem('pw_theme_v2', t);
        }} catch (e) {{ t = 'light'; }}
      }}
      document.documentElement.setAttribute('data-theme', t);
      var mc = document.getElementById('theme-color-meta');
      if (mc) mc.setAttribute('content', t === 'dark' ? '#090b10' : '#f6f7f4');
    }})();
  </script>
  <link rel="preload" href="{r}static/fonts/space-grotesk/files/space-grotesk-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="{r}static/fonts/noto-sans-sc/index.css">
  <link rel="stylesheet" href="{r}static/fonts/space-grotesk/index.css">
  <link rel="stylesheet" href="{r}static/fonts/noto-serif-sc/index.css">
  <link rel="stylesheet" href="{r}static/css/style.css">
  <link rel="stylesheet" href="{r}static/css/editorial.css">
  <link rel="stylesheet" href="{r}static/css/experience.css">
</head>
<body class="{esc(shell_body_class)}">
  <header class="site-header">
    <div class="container header-inner">
      <div class="header-left">
        <button type="button" class="icon-btn mobile-menu-btn" id="mobile-menu-btn" aria-label="打开导航菜单" aria-expanded="false" aria-controls="site-drawer">
          {SVGS["menu"]}
        </button>
        <a class="brand-link" href="{r}index.html">
          <span class="brand-mark">⊙</span>
          <span class="brand-copy"><span class="brand-name">衡天 PowerWiki</span><span class="brand-subtitle">MULTIDIMENSIONAL ARCHIVE</span></span>
        </a>
      </div>

      <nav class="main-nav" id="main-nav" aria-label="主导航">
        {nav_link("home", "index.html", "首页", icon="home")}
        {nav_link("tiers", "tiers.html", "量级", "nav-cat", "atlas")}
        {nav_link("characters", "characters.html", "角色", "nav-cat", "dossier")}
        {nav_link("rules", "rules.html", "规则", "nav-doc", "library")}
        {nav_link("materials", "materials.html", "材质", "nav-doc", "materials")}
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
  </header>{reading_progress_html}

  <div class="drawer-backdrop" id="drawer-backdrop"></div>
  <aside class="site-drawer" id="site-drawer" aria-label="全站导航抽屉" aria-hidden="true">
    <div class="site-drawer-head">
      <a class="brand-link" href="{r}index.html">
        <span class="brand-mark">⊙</span>
        <span class="brand-copy"><span class="brand-name">衡天 PowerWiki</span><span class="brand-subtitle">MULTIDIMENSIONAL ARCHIVE</span></span>
      </a>
      <button type="button" class="icon-btn" id="site-drawer-close" aria-label="关闭导航菜单">
        {SVGS["close"]}
      </button>
    </div>
    <div class="site-drawer-body">
      <div class="drawer-group">
        <div class="drawer-group-label">查阅</div>
        {drawer_card("tiers", "tiers.html", "量级天梯", "98 档 · 从昆虫到论天")}
        {drawer_card("characters", "characters.html", "角色档案", "定级结论与完整证据原文")}
      </div>
      <div class="drawer-group">
        <div class="drawer-group-label">规则与资料</div>
        {drawer_doc("rules", "rules.html", "衡天体系 · 第五版")}
        {drawer_doc("materials", "materials.html", "材质与能量 · 第二版")}
      </div>
      <div class="drawer-group">
        <div class="drawer-group-label">快捷导航</div>
        {drawer_doc("home", "index.html", "返回首页总览")}
        {drawer_doc("search", "search.html", "全站即时检索")}
      </div>
    </div>
  </aside>
  <script>
    (function() {{
      var btn = document.getElementById('mobile-menu-btn');
      var drawer = document.getElementById('site-drawer');
      var closeBtn = document.getElementById('site-drawer-close');
      var backdrop = document.getElementById('drawer-backdrop');
      if (!btn || !drawer) return;
      function sync() {{
        if (window.__PW_SYNC_LOCK__) {{ window.__PW_SYNC_LOCK__(); return; }}
        var open = drawer.classList.contains('open');
        drawer.setAttribute('aria-hidden', open ? 'false' : 'true');
        btn.setAttribute('aria-expanded', open ? 'true' : 'false');
        if (backdrop) backdrop.classList.toggle('open', open);
        document.body.classList.toggle('is-scroll-locked', open);
      }}
      function closeAll() {{
        if (window.__PW_CLOSE_ALL__) {{ window.__PW_CLOSE_ALL__(); return; }}
        drawer.classList.remove('open');
        sync();
      }}
      btn.dataset.navBound = '1';
      btn.addEventListener('click', function(e) {{
        e.preventDefault();
        var modals = document.querySelectorAll('.modal-backdrop.open');
        for (var i = 0; i < modals.length; i++) modals[i].classList.remove('open');
        var sb = document.getElementById('doc-sidebar');
        if (sb) sb.classList.remove('drawer-open');
        drawer.classList.toggle('open');
        sync();
      }});
      if (closeBtn) {{ closeBtn.dataset.bound = '1'; closeBtn.addEventListener('click', closeAll); }}
      if (backdrop) {{ backdrop.dataset.bound = '1'; backdrop.addEventListener('click', closeAll); }}
      drawer.dataset.linksBound = '1';
      var links = drawer.querySelectorAll('a');
      for (var j = 0; j < links.length; j++) {{
        links[j].addEventListener('click', function() {{ drawer.classList.remove('open'); sync(); }});
      }}
      window.addEventListener('pageshow', function() {{ drawer.classList.remove('open'); sync(); }});
    }})();
  </script>

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
        <button type="button" class="chip-btn" data-search-tab="rules">衡天第五版全文</button>
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
        <span>衡天 PowerWiki · 第五版基准</span>
      </div>
      <div class="footer-links">
        <a href="{r}tiers.html">量级天梯</a>
        <a href="{r}characters.html">角色档案</a>
        <a href="{r}rules.html">衡天体系全文</a>
        <a href="{r}materials.html">材质能量库</a>
      </div>
    </div>
  </footer>

  <script src="{r}static/js/search-index.js"></script>
  <script src="{r}static/js/app.js"></script>
</body>
</html>
"""
    return "\n".join(line.rstrip() for line in page.splitlines()) + "\n"


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
    img_src = resolve_rel_asset(c.get("image_url", ""), href_prefix)
    origin_text = esc(c.get("series") or "未知出处")
    updated = esc(c.get("doc_date") or "已归档")
    tier_line = f'<div class="char-tier-line"><span>{esc(t_name)}</span><span class="mono">{t_order}</span></div>'
    summary = f'<p class="char-summary">{esc(c.get("card_summary") or c.get("summary") or "")}</p>'
    foot = f'<div class="char-foot"><span>{updated} 更新</span><span class="card-link-hint">阅读档案 {SVGS["arrow_up_right"]}</span></div>'

    if img_src:
        shape = c.get("image_shape") or "portrait"
        if shape not in {"landscape", "square", "portrait"}:
            shape = "portrait"
        size_attrs = f' width="{int(c["image_w"])}" height="{int(c["image_h"])}"' if c.get("image_w") and c.get("image_h") else ""
        return f"""
    <a class="char-card has-media media-top char-card-{esc(c['slug'])}" data-character="{esc(c['slug'])}" href="{href_prefix}character/{esc(c['slug'])}.html">
      <div class="char-card-media is-{shape}" data-art-label="{esc(c.get('pinyin') or c['slug']).upper()}">
        <span class="char-card-ambience" aria-hidden="true" style="background-image:url('{esc(img_src)}')"></span>
        <img class="char-card-img" src="{esc(img_src)}" alt="{esc(c['name'])}"{size_attrs} loading="lazy">
      </div>
      <div class="char-card-body">
        <div class="char-head">
          <div class="char-meta"><h3 class="char-name">{esc(c['name'])}</h3><div class="char-origin">{origin_text}</div></div>
          <span class="tier-badge gold mono">⊙ {esc(t_code)}</span>
        </div>
        {tier_line}{summary}{foot}
      </div>
    </a>"""

    return f"""
    <a class="char-card char-card-{esc(c['slug'])}" data-character="{esc(c['slug'])}" href="{href_prefix}character/{esc(c['slug'])}.html">
      <div class="char-head">
        <div class="char-identity"><div class="char-monogram">{esc(c["name"][:1])}</div><div class="char-meta"><h3 class="char-name">{esc(c['name'])}</h3><div class="char-origin">{origin_text}</div></div></div>
        <span class="tier-badge gold mono">⊙ {esc(t_code)}</span>
      </div>
      {tier_line}{summary}{foot}
    </a>"""

def build_home_page(
    tiers: List[Dict[str, Any]],
    all_chars: List[Dict[str, Any]],
    rules_lines: int,
    materials_lines: int,
    rules_toc_count: int,
) -> str:
    tier_by_slug = {t["slug"]: t for t in tiers}
    featured_section = ""
    if all_chars:
        featured_cards = [render_char_card_html(c, tier_by_slug, "") for c in all_chars[:4]]
        featured_section = f"""
      <section class="section-block home-dossiers">
        <div class="section-header">
          <div>
            <span class="section-kicker">Character dossiers</span>
            <h2 class="section-title">角色档案</h2>
          </div>
          <a class="text-link" href="characters.html">查看全部 {len(all_chars)} 位 →</a>
        </div>
        <div class="char-grid">{"".join(featured_cards)}</div>
      </section>"""

    body = f"""
    <div class="container home-stack">
      <section class="hero-banner" aria-labelledby="home-title">
        <div class="hero-backdrop" aria-hidden="true">
          <img class="hero-backdrop-img" src="static/img/cosmic-atlas-hero.jpg" width="1584" height="672" alt="">
        </div>
        <div class="hero-body">
          <div class="eyebrow"><span class="eyebrow-dot"></span>第五版 · 2026.10.28 最新基准（含 1.7 位格栏）</div>
          <h1 class="hero-heading" id="home-title">从昆虫到无限，<br><span>查清每一个量级。</span></h1>
          <p class="hero-desc">从物理能量到无限基数，用同一套标尺查阅量级、角色证据与规则原文。</p>
          <div class="hero-cta-row">
            <a class="btn btn-primary" href="tiers.html">浏览量级天梯 {SVGS["arrow_up_right"]}</a>
            <a class="btn btn-secondary" href="rules.html">阅读第五版规则</a>
          </div>
        </div>
      </section>

      <div class="home-stats" aria-label="站点概览">
        <a class="home-stat" href="tiers.html"><strong class="mono">{len(tiers)}</strong><span>量级档位</span></a>
        <a class="home-stat" href="characters.html"><strong class="mono">{len(all_chars)}</strong><span>角色档案</span></a>
        <a class="home-stat" href="rules.html"><strong class="mono">V5</strong><span>当前规则版本</span></a>
      </div>

      <section class="section-block" aria-labelledby="start-title">
        <div class="section-header">
          <div>
            <span class="section-kicker">Start here</span>
            <h2 class="section-title" id="start-title">从这里开始</h2>
          </div>
        </div>
        <div class="portal-grid">
          <a class="portal-card" href="tiers.html">
            <div class="portal-top"><span class="portal-heading"><span class="portal-glyph">{SVGS["atlas"]}</span><span class="portal-num mono">01 / ATLAS</span></span><span class="portal-icon">{SVGS["arrow_up_right"]}</span></div>
            <div><h3 class="portal-title">量级天梯</h3><p class="portal-text">按序位、跨度或能量检索，从昆虫级连续查阅至论天最上。</p></div>
            <span class="portal-link">进入 {len(tiers)} 个档位 →</span>
          </a>
          <a class="portal-card" href="characters.html">
            <div class="portal-top"><span class="portal-heading"><span class="portal-glyph">{SVGS["dossier"]}</span><span class="portal-num mono">02 / DOSSIERS</span></span><span class="portal-icon">{SVGS["arrow_up_right"]}</span></div>
            <div><h3 class="portal-title">角色档案</h3><p class="portal-text">先看定级结论，再按章节核对完整证据、计算与存疑说明。</p></div>
            <span class="portal-link">查阅 {len(all_chars)} 份档案 →</span>
          </a>
          <div class="portal-card portal-library">
            <div class="portal-top"><span class="portal-heading"><span class="portal-glyph">{SVGS["library"]}</span><span class="portal-num mono">03 / LIBRARY</span></span></div>
            <div><h3 class="portal-title">规则与资料</h3><p class="portal-text">保留完整原文与章节目录，方便逐条核对。</p></div>
            <div class="library-links">
              <a href="rules.html"><span>衡天量级体系</span><span class="mono">第五版 →</span></a>
              <a href="materials.html"><span>材质与破坏能量</span><span class="mono">第二版 →</span></a>
            </div>
          </div>
        </div>
      </section>

      {featured_section}
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
        slug = c.get("tier_slug")
        if slug:
            char_count_by_tier[slug] = char_count_by_tier.get(slug, 0) + 1

    ranked = sorted((t for t in tiers if not t.get("unranked")), key=lambda t: t["order"])
    all_ordered = ranked + [t for t in tiers if t.get("unranked")]
    tier_art_urls = {
        t["slug"]: f"static/img/tiers/{tier_art_stem(t['slug'], t['group_id'])}.jpg"
        for t in all_ordered
    }
    tier_art_manifest = json.dumps(tier_art_urls, ensure_ascii=False).replace("</", "<\\/")
    tier_tuning_manifest = json.dumps(
        {t["slug"]: tier_art_tuning(t["slug"]) for t in all_ordered}, ensure_ascii=False
    ).replace("</", "<\\/")
    ordered_gids: List[str] = []
    for t in all_ordered:
        if t["group_id"] not in ordered_gids:
            ordered_gids.append(t["group_id"])

    ssr_sections: List[str] = []
    for gid in ordered_gids:
        group = group_map.get(gid, {"title": gid})
        items = [t for t in all_ordered if t["group_id"] == gid]
        cards: List[str] = []
        for t in items:
            order = "待定" if t.get("unranked") else f"#{t['order']:02d}"
            count = char_count_by_tier.get(t["slug"], 0)
            art_url = tier_art_urls[t["slug"]]
            art_tuning = tier_art_tuning(t["slug"])
            char_pill = f'<span class="tier-char-count">{count} 角色</span>' if count else ""
            cards.append(f"""
                <a class="tier-card" data-domain="{esc(t['domain'])}" href="tier/{esc(t['slug'])}.html">
                  <span class="tier-card-art" aria-hidden="true" style="background-image:url('{esc(art_url)}');{art_tuning}"></span>
                  <div class="tier-card-top">
                    <span class="tier-badge mono">⊙ {esc(t['code'])}</span>
                    <span class="tier-top-right">{char_pill}<span class="tier-seq mono">{order}</span></span>
                  </div>
                  <div class="tier-name-row"><h3 class="tier-name">{esc(t['name'])}</h3></div>
                  <div class="tier-energy mono">{esc(t['energy'])}</div>
                  <p class="tier-scale">{esc(t['scale'])}</p>
                </a>""")
        ssr_sections.append(f"""
            <section class="group-section" id="group-{esc(gid)}">
              <div class="group-header"><h2 class="group-title">{esc(group['title'])}</h2><span class="group-sub">{len(items)} 档</span></div>
              <div class="tier-grid">{''.join(cards)}</div>
            </section>""")

    counts: Dict[str, int] = {}
    for t in tiers:
        domain = t.get("domain", "unranked")
        counts[domain] = counts.get(domain, 0) + 1

    body = f"""
    <div class="container">
      <section class="category-hub" aria-labelledby="tiers-title">
        <div class="category-hub-body">
          <div class="hub-kicker-row">
            <span class="hub-kicker-badge mono">TIER ATLAS · 第五版</span>
            <span class="count-badge mono" id="tier-result-count">{len(tiers)} / {len(tiers)} 档</span>
          </div>
          <div><h1 class="page-title" id="tiers-title">量级天梯</h1><p class="page-desc">从 #01 昆虫级到 #97 论天最上，按能量与数学结构递增。</p></div>
        </div>
      </section>

      <div class="control-panel">
        <div class="control-row">
          <div class="seg-group" role="group" aria-label="视图模式">
            <button type="button" class="seg-btn active" data-tier-view="card">卡片</button>
            <button type="button" class="seg-btn" data-tier-view="flat">天梯</button>
            <button type="button" class="seg-btn" data-tier-view="table">总表</button>
          </div>
          <div class="search-field">
            <input type="search" class="search-input" id="tier-filter-input" placeholder="搜索代字、名称、能量或参照物…" autocomplete="off">
            <button type="button" class="clear-input-btn" id="tier-filter-clear">清空</button>
          </div>
        </div>
        <div class="control-row divider-top">
          <div class="chip-rail" role="group" aria-label="量级区间筛选">
            <button type="button" class="chip-btn active" data-tier-seg="all">全部 {len(tiers)}</button>
            <button type="button" class="chip-btn" data-tier-seg="terrestrial">个体—地表 {counts.get('terrestrial', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="stellar">行星—恒星 {counts.get('stellar', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="transition">过渡 {counts.get('transition', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="cosmic">恒星系—宇宙 {counts.get('cosmic', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="fgh">广义无限 {counts.get('fgh', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="beyond">论外—论天 {counts.get('beyond', 0)}</button>
            <button type="button" class="chip-btn" data-tier-seg="unranked">待定 {counts.get('unranked', 0)}</button>
          </div>
        </div>
      </div>
      <div class="content-section" id="tiers-explorer-mount">{''.join(ssr_sections)}</div>
      <script>window.PW_TIER_ART_URLS = {tier_art_manifest};window.PW_TIER_ART_TUNING = {tier_tuning_manifest};</script>
    </div>
    """
    return render_shell(title="量级天梯", page_id="tiers", active_nav="tiers", body_html=body, root_prefix="./")

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
        tier_art_src = f"../static/img/tiers/{esc(tier_art_stem(t['slug'], t['group_id']))}.jpg"
        tier_tuning = tier_art_tuning(t["slug"])
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
        <div class="container detail-stack tier-detail-stack" id="group-{esc(t['group_id'])}" style="{tier_tuning}">
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

          <section class="dossier-header tier-dossier">
            <div class="page-header-art" aria-hidden="true">
              <img class="page-header-img" src="{tier_art_src}" alt="">
            </div>
            <div class="dossier-body">
              <div class="dossier-top">
                <div>
                  <div class="char-tags">
                    <span class="tier-badge gold mono">⊙ {esc(t['code'])}</span>
                    <span class="count-badge mono">{order_badge}</span>
                    <span class="tag-pill tier-group-pill"><span class="tier-group-mark" aria-hidden="true"></span>{esc(g.get('short_title') or g['title'])}</span>
                  </div>
                  <h1 class="page-title">{esc(t['name'])} · {esc(t['family'])}系</h1>
                  <p class="page-desc">{esc(t.get('notes', ''))}</p>
                </div>
                <a class="btn btn-secondary btn-sm" href="{rule_href}">
                  查阅《衡天第五版》对应章节 {SVGS["arrow_up_right"]}
                </a>
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
          </section>

          <section class="section-block">
            <div class="section-header">
              <h2 class="section-title">本档位角色（{len(chars_in_tier)}）</h2>
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
    sorted_chars = sorted(all_chars, key=lambda c: (tier_by_slug.get(c.get("tier_slug", ""), {}).get("order", 999), c.get("pinyin") or c.get("name") or ""))
    compact = len(all_chars) <= 8
    cards = "".join(render_char_card_html(c, tier_by_slug, "") for c in sorted_chars)

    if sorted_chars:
        ssr_mount_inner = f'<div class="char-grid compact-roster-grid">{cards}</div>' if compact else f"""
        <section class="group-section" id="char-scale-list">
          <div class="group-header"><h2 class="group-title">按量级递增</h2><span class="group-sub">{len(sorted_chars)} 位角色</span></div>
          <div class="char-grid">{cards}</div>
        </section>"""
    else:
        ssr_mount_inner = """
        <div class="empty-state-box"><h3 class="empty-state-title">暂无角色档案</h3><p class="empty-state-sub">新档案收录后会显示在这里。</p></div>"""

    series_options = ""
    if not compact:
        all_series = sorted({c["series"] for c in all_chars if c.get("series")})
        series_options = f'<select class="select-control" id="char-series-select" aria-label="按作品筛选"><option value="all">全部作品（{len(all_series)}）</option>' + "".join(f'<option value="{esc(s)}">{esc(s)}</option>' for s in all_series) + "</select>"

    domain_controls = "" if compact else """
        <div class="control-row divider-top"><div class="chip-rail" role="group" aria-label="角色所属量级区间">
          <button type="button" class="chip-btn active" data-char-domain="all">全部区间</button>
          <button type="button" class="chip-btn" data-char-domain="terrestrial">个体—地表</button>
          <button type="button" class="chip-btn" data-char-domain="stellar">行星—恒星</button>
          <button type="button" class="chip-btn" data-char-domain="transition">过渡</button>
          <button type="button" class="chip-btn" data-char-domain="cosmic">恒星系—宇宙</button>
          <button type="button" class="chip-btn" data-char-domain="fgh">广义无限</button>
          <button type="button" class="chip-btn" data-char-domain="beyond">论外—论天</button>
        </div></div>"""
    alpha_bar = "" if compact else '<div class="alpha-bar" id="char-alpha-bar" aria-label="首字母快速定位"><div class="alpha-letters" id="char-alpha-letters"></div></div>'

    body = f"""
    <div class="container">
      <section class="category-hub" aria-labelledby="characters-title">
        <div class="category-hub-body">
          <div class="hub-kicker-row"><span class="hub-kicker-badge mono">CHARACTER DOSSIERS</span><span class="count-badge mono" id="char-result-count">{len(all_chars)} / {len(all_chars)} 位</span></div>
          <div><h1 class="page-title" id="characters-title">角色档案</h1><p class="page-desc">先看结论，再进入完整档案核对证据、计算与存疑说明。</p></div>
        </div>
      </section>
      <div class="control-panel">
        <div class="control-row">
          <div class="control-cluster">
            <div class="seg-group" role="group" aria-label="角色排序方式"><button type="button" class="seg-btn active" data-char-sort="asc">量级 ↑</button><button type="button" class="seg-btn" data-char-sort="alpha">A–Z</button></div>
            {series_options}
          </div>
          <div class="search-field"><input type="search" class="search-input" id="char-filter-input" placeholder="搜索角色、作品或量级…" autocomplete="off"></div>
        </div>
        {domain_controls}
      </div>
      {alpha_bar}
      <div class="content-section" id="chars-explorer-mount">{ssr_mount_inner}</div>
    </div>
    """
    return render_shell(title="角色档案", page_id="characters", active_nav="characters", body_html=body, root_prefix="./")

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
        group_badge_label = g.get("short_title") or g["title"]

        submeta_parts: List[str] = []
        if c.get("realm"):
            submeta_parts.append(f"形态：{esc(c['realm'])}")
        if c.get("alias"):
            submeta_parts.append(f"别称：{esc(c['alias'])}")
        if c.get("doc_date"):
            submeta_parts.append(f"定级日期：{esc(c['doc_date'])}")
        if not submeta_parts:
            submeta_parts.append(f"出处：{esc(c.get('series') or '未标注')}")
        submeta_html = "<span>·</span>".join(f"<span>{p}</span>" for p in submeta_parts)

        floor_val_html = format_evidence_html(c.get("floor_tier") or t["energy"])
        ceiling_val_html = format_evidence_html(c.get("ceiling_note") or t["scale"])
        basis_val_html = format_evidence_html(
            c.get("core_basis") or c.get("credibility") or f"依据《衡天⊙ 第五版》{t['name']}标准评定"
        )
        floor_label = "保底量级" if c.get("floor_tier") else "主档能量带"
        ceiling_label = "上限边界与反证" if c.get("ceiling_note") else "主档覆盖尺度"

        visual = c.get("visual") or {}
        detail_lede = c.get("detail_lede") or c.get("summary") or ""
        header_art_src = resolve_rel_asset(visual.get("art_url") or "static/img/character-chronicle.jpg", "../")
        header_class = f"dossier-header character-dossier theme-{esc(c['slug'])}" if visual else "dossier-header"
        dossier_masthead_html = ""
        if visual:
            dossier_masthead_html = f"""
            <div class="dossier-masthead">
              <span class="dossier-kicker mono">{esc(visual.get('kicker') or 'CHARACTER OBSERVATION')}</span>
              <span class="dossier-register mono">{esc(visual.get('register') or c['slug'].upper())}</span>
            </div>"""
        fact_items_html = "".join(
            f"""<div class="dossier-fact"><span class="fact-label">{esc(item.get('label') or '')}</span><strong class="fact-value">{esc(item.get('value') or '')}</strong><span class="fact-note">{format_evidence_html(item.get('note') or '')}</span></div>"""
            for item in (visual.get("facts") or [])
        )
        dossier_fact_rail_html = f'<div class="dossier-fact-rail">{fact_items_html}</div>' if fact_items_html else ""
        portrait_index_html = f'<span class="portrait-index mono">{esc(visual.get("art_badge"))}</span>' if visual.get("art_badge") else ""

        portrait_src = resolve_rel_asset(c.get("portrait_url") or c.get("image_url") or "", "../")
        if portrait_src:
            portrait_caption = esc(c.get("portrait_caption") or f"{c['name']} 角色立绘")
            p_shape = c.get("portrait_shape") or c.get("image_shape") or "portrait"
            body_layout_cls = "has-landscape" if p_shape == "landscape" else "has-portrait"
            pw = c.get("portrait_w") or c.get("image_w")
            ph = c.get("portrait_h") or c.get("image_h")
            p_dim_attrs = f' width="{int(pw)}" height="{int(ph)}"' if pw and ph else ""
            dossier_body_html = f"""
            <div class="dossier-body {body_layout_cls}">
              <div class="dossier-main-col">
                <div class="char-tags">
                  <span class="tag-pill accent">{esc(group_badge_label)}</span>
                  <span class="tag-pill">{esc(c.get('series') or '未标注出处')}</span>
                  {mod_chips_html}
                </div>

                <div>
                  <h1 class="page-title">{esc(c['name'])}</h1>
                  <div class="dossier-submeta">{submeta_html}</div>
                </div>

                <p class="page-desc">{esc(detail_lede)}</p>

                <div class="dossier-kpi-grid">
                  <div class="dossier-kpi-card">
                    <div class="kpi-label">综合主档定级</div>
                    <div class="kpi-value">
                      <a class="kpi-tier-link mono" href="../tier/{esc(t['slug'])}.html" title="查看所属主档规格页">
                        <span>⊙ {esc(t['code'])} · {esc(t['name'])}（{t_order_str}）</span>
                        {SVGS["arrow_up_right"]}
                      </a>
                    </div>
                  </div>
                  <div class="dossier-kpi-card">
                    <div class="kpi-label">{floor_label}</div>
                    <div class="kpi-value">{floor_val_html}</div>
                  </div>
                </div>

                <div class="dossier-actions-row"><a class="text-link" href="{rule_href}">对照衡天规则原文 →</a></div>

                <div class="full-writing-box">
                  <div class="box-kicker">正式完整书写摘要</div>
                  <div>{format_evidence_html(full_writing)}</div>
                  {f'<div class="box-rankline"><span class="box-rank-kicker mono">位格</span><span>{format_evidence_html(c["rank_writing"])}</span></div>' if c.get("rank_writing") else ""}
                  {f'<div class="box-subnote">证据链核验摘要：{format_evidence_html(c["credibility"])}</div>' if c.get("credibility") else ""}
                </div>
              </div>

              <aside class="char-portrait-stage" aria-label="角色形象参考">
                <div class="char-portrait-canvas">
                  {portrait_index_html}
                  <img class="char-portrait-img" src="{esc(portrait_src)}" alt="{esc(c['name'])}（{esc(c.get('series') or '')}）形象参考"{p_dim_attrs}>
                </div>
                <div class="char-portrait-caption">{portrait_caption}</div>
              </aside>
            </div>"""
        else:
            dossier_body_html = f"""
            <div class="dossier-body">
              <div class="dossier-top">
                <div class="dossier-title-block">
                  <div class="char-monogram lg">{esc(c["name"][:1])}</div>
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
                    <span class="tag-pill accent">{esc(group_badge_label)}</span>
                    {mod_chips_html}
                  </div>
                </div>
              </div>

              <p class="page-desc">{esc(detail_lede)}</p>

              <div class="full-writing-box">
                <div class="box-kicker">正式完整书写摘要</div>
                <div>{format_evidence_html(full_writing)}</div>
                {f'<div class="box-rankline"><span class="box-rank-kicker mono">位格</span><span>{format_evidence_html(c["rank_writing"])}</span></div>' if c.get("rank_writing") else ""}
                {f'<div class="box-subnote">证据链核验摘要：{format_evidence_html(c["credibility"])}</div>' if c.get("credibility") else ""}
              </div>
            </div>"""

        has_full_doc = False
        center_content_html = ""
        doc_rel_path = c.get("doc_path")
        if doc_rel_path and (ROOT / doc_rel_path).exists():
            has_full_doc = True
            raw_doc_md = (ROOT / doc_rel_path).read_text(encoding="utf-8")
            body_doc_md = strip_character_doc_front_banner(raw_doc_md)
            doc_renderer = VerbatimMarkdownRenderer(image_map=c.get("image_map"), base_dir=CHAR_OUT_DIR)
            rendered_doc_html = doc_renderer.render(body_doc_md)
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
                        "badge": f"角色档案 · ⊙{t['code']}",
                        "pinyin": c.get("pinyin", ""),
                        "text": clean_txt,
                        "url": f"character/{c['slug']}.html#{sec['id']}",
                    }
                )

            doc_basis_label = esc(c.get("doc_basis") or "依据《衡天⊙ 多维战力量级体系（第五版）》")
            center_content_html = f"""
          <div class="doc-layout">
            <aside class="doc-sidebar" id="doc-sidebar" aria-label="定级档案目录">
              <div class="toc-head">
                <div class="toc-head-row">
                  <span>档案章节目录</span>
                  <span class="mono">{len(doc_renderer.toc)} 节</span>
                </div>
                <input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选章节…" autocomplete="off">
              </div>
              <nav class="toc-list" id="toc-nav">
                {toc_links_html}
              </nav>
            </aside>

            <article class="doc-panel">
              <div class="doc-toolbar">
                <div class="doc-source-info">
                  <span>定级档案全文</span>
                  <span>·</span>
                  <span>{doc_basis_label}</span>
                </div>
              </div>

              <div class="markdown-body">
                {rendered_doc_html}
              </div>
            </article>
            {READER_RAIL_HTML}
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

        tier_anchor_section = (
            ""
            if has_full_doc
            else f"""
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
                <div class="spec-label">对应《衡天第五版》章节</div>
                <div class="spec-val">
                  <a class="table-primary-link" href="{rule_href}">{esc(rule_sec_title or '查阅第五版规范原文')} →</a>
                </div>
              </div>
            </div>
          </section>"""
        )

        char_fx_html = char_identity_fx_html(c["slug"])
        infographic_html = render_character_infographic(c)

        body = f"""
        <div class="container detail-stack character-detail character-{esc(c['slug'])}">
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

          <section class="{header_class}">
            <div class="page-header-art" aria-hidden="true">
              <img class="page-header-img" src="{esc(header_art_src)}" alt="">
            </div>
            {dossier_masthead_html}
            {dossier_body_html}
            {dossier_fact_rail_html}
          </section>

          {char_fx_html}
          {infographic_html}
          {center_content_html}
          {tier_anchor_section}

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
            body_class=f"character-site character-{c['slug']}",
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

    toc_links: List[str] = []
    title_to_id: Dict[str, str] = {}
    for item in renderer.toc:
        title_to_id[item["title"]] = item["id"]
        toc_links.append(f'<a class="toc-item toc-lvl-{item["level"]}" href="#{esc(item["id"])}">{esc(item["title"])}</a>')

    rules_tab_cls = "codex-tab active" if active_nav == "rules" else "codex-tab"
    mat_tab_cls = "codex-tab active" if active_nav == "materials" else "codex-tab"
    version_label = "第五版 · 2026.10.28（1.7 位格栏）" if active_nav == "rules" else "第二版 · 物理参考"

    body = f"""
    <div class="container">
      <header class="codex-header">
        <nav class="codex-tabs" aria-label="规则与资料切换">
          <a class="{rules_tab_cls}" href="rules.html">衡天体系 · 第五版</a>
          <a class="{mat_tab_cls}" href="materials.html">材质与能量 · 第二版</a>
        </nav>
        <div class="codex-folio">
          <div class="codex-folio-kicker"><span class="codex-folio-badge mono">{version_label}</span><span>完整原文 · {len(renderer.toc)} 节</span></div>
          <h1 class="codex-folio-title">{esc(title)}</h1>
          <p class="codex-folio-desc">{esc(subtitle)}</p>
        </div>
      </header>

      <div class="doc-layout">
        <aside class="doc-sidebar" id="doc-sidebar" aria-label="全文目录">
          <div class="toc-head"><div class="toc-head-row"><span>本文目录</span><span class="mono">{len(renderer.toc)}</span></div><input type="search" class="toc-filter" id="toc-filter-input" placeholder="筛选章节…" autocomplete="off"></div>
          <nav class="toc-list" id="toc-nav">{''.join(toc_links)}</nav>
        </aside>
        <article class="doc-panel">
          <div class="doc-toolbar">
            <div class="doc-source-info"><span>衡天档案</span></div>
          </div>
          <div class="markdown-body">{rendered_html}</div>
        </article>
        {READER_RAIL_HTML}
      </div>
    </div>
    """
    full_html = render_shell(title=title, page_id=page_id, active_nav=active_nav, body_html=body, root_prefix="./", has_toc_button=True)
    return full_html, renderer.sections_for_index, title_to_id

# ---------------------------------------------------------------------------
# 角色信息图（移动端免滚动阅读）与角色专属氛围层
# ---------------------------------------------------------------------------
_TIERS_CACHE: Optional[List[Dict[str, Any]]] = None


def _tiers_list() -> List[Dict[str, Any]]:
    """惰性加载量级表，供信息图计算刻度位置。"""
    global _TIERS_CACHE
    if _TIERS_CACHE is None:
        with open(ROOT / "data" / "tiers.json", encoding="utf-8") as fh:
            _TIERS_CACHE = (json.load(fh).get("tiers") or [])
    return _TIERS_CACHE


def _dim_chip_label(text: str) -> str:
    """从维度说明里提取一个紧凑标签：量级代字〔置信度〕 / 数值〔置信度〕 / 〔置信度〕。"""
    s = (text or "").strip()
    m = re.search(r"(?:[⊙◎◯○◇△☆★]\s*)?([\u4e00-\u9fff]{1,2})\s*([△☆○◇★])\s*〔([^〕]*)〕", s)
    if m:
        return f"{m.group(1)}{m.group(2)}〔{m.group(3)}〕"
    m3 = re.search(r"([0-9.]+～[0-9.]+)\s*(?:倍?光速|\bc)?\s*〔([^〕]*)〕", s)
    if m3:
        return f"{m3.group(1)}〔{m3.group(2)}〕"
    m2 = re.search(r"〔([^〕]*)〕", s)
    if m2:
        return f"〔{m2.group(1)}〕"
    return s[:8]


def _pct(order: int, max_order: int) -> int:
    if max_order <= 0:
        return 50
    return max(3, min(97, round(order / max_order * 100)))


def char_identity_fx_html(slug: str) -> str:
    """角色专属氛围层：御兔为漂浮液态光斑，弗坦由 CSS ::after 渲染。"""
    if slug == "yutu":
        return '<div class="char-identity-fx" aria-hidden="true"><span></span><span></span><span></span></div>'
    return '<div class="char-identity-fx" aria-hidden="true"></div>'


def render_character_infographic(entry: Dict[str, Any]) -> str:
    """把长文档里的关键结论压成一张免滚动的信息图：刻度 + 维度 + 关键数字。"""
    tiers = _tiers_list()
    tier = next((t for t in tiers if t.get("slug") == entry.get("tier_slug")), None)
    main_code = (tier or {}).get("code") or entry.get("floor_tier") or "—"
    max_order = max((t.get("order") or 0) for t in tiers) or 1
    order = (tier or {}).get("order") or 0
    pos = _pct(order, max_order)

    landmarks = ["城", "国", "恒", "宇", "超", "无", "论外"]
    labels_html = ""
    for lm in landmarks:
        hit = next((x for x in tiers if (x.get("code") or "").startswith(lm)), None)
        if hit and hit.get("order"):
            labels_html += f'<span style="left:{_pct(hit["order"], max_order)}%">{lm}</span>'

    dims = entry.get("dims") or {}
    dim_html = []
    for key in ("破", "控", "域", "御", "速", "算", "性"):
        label = _dim_chip_label(dims.get(key, "")) if dims.get(key) else "〔缺〕"
        miss = "is-missing" if label == "〔缺〕" else ""
        dim_html.append(f'<div class="char-dim {miss}"><b>{key}</b><span>{esc(label)}</span></div>')
    dims_html = "".join(dim_html)

    facts = (entry.get("visual") or {}).get("facts") or []
    facts_html = "".join(
        f'<div class="char-fact"><span class="char-fact-k">{esc(str(f.get("label", "")))}</span>'
        f'<span class="char-fact-v">{esc(str(f.get("value", "")))}</span></div>'
        for f in facts[:3]
    )

    modifiers = entry.get("modifiers") or []
    mod_html = f'<span class="char-info-note">{esc(" · ".join(modifiers[:4]))}</span>' if modifiers else ""

    return f"""
        <section class="char-info-panel" aria-label="量级信息图">
          <div class="char-info-kicker">量级刻度 / TIER SCALE</div>
          <div class="char-info-head">
            <span class="char-info-main">⊙ {esc(main_code)}<span class="char-info-code">〔主档〕</span></span>
            {mod_html}
          </div>
          <div class="char-scale">
            <div class="char-scale-track">
              <span class="char-scale-fill" style="--pos:{pos}%"></span>
              <i class="char-scale-mark" style="--pos:{pos}%"></i>
            </div>
            <div class="char-scale-labels">{labels_html}</div>
          </div>
          <div class="char-dims">{dims_html}</div>
          {f'<div class="char-facts">{facts_html}</div>' if facts_html else ""}
        </section>"""


def build_search_page() -> str:
    body = f"""
    <div class="container">
      <header class="page-header search-page-header">
        <div class="page-header-body">
          <div class="page-title-row">
            <div><span class="section-kicker">Search PowerWiki</span><h1 class="page-title">搜索全站</h1><p class="page-desc">检索量级、角色证据、第五版规则与材质数据。</p></div>
            <span class="count-badge mono" id="dedicated-search-count">准备就绪</span>
          </div>
        </div>
      </header>
      <div class="control-panel">
        <div class="search-field full"><input type="search" class="search-input lg" id="dedicated-search-input" placeholder="输入关键词；用空格组合多个条件…" autofocus></div>
        <div class="control-row"><div class="chip-rail" aria-label="搜索范围">
          <button type="button" class="chip-btn active" data-page-search-type="all">全部</button>
          <button type="button" class="chip-btn" data-page-search-type="tier">量级</button>
          <button type="button" class="chip-btn" data-page-search-type="char">角色</button>
          <button type="button" class="chip-btn" data-page-search-type="rules">第五版规则</button>
          <button type="button" class="chip-btn" data-page-search-type="materials">材质数据</button>
        </div></div>
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
                "title": f"衡天第五版 · {sec['title']}",
                "badge": "衡天第五版",
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
        "/* Auto-generated by build_site.py v9.1 — DO NOT EDIT MANUALLY */\n"
        f"window.__POWERWIKI_DATA__ = {json.dumps(client_data, ensure_ascii=False, separators=(',', ':'))};\n"
        f"window.__POWERWIKI_INDEX__ = {json.dumps(index_entries, ensure_ascii=False, separators=(',', ':'))};\n"
    )


def enrich_character_media_dimensions(all_chars: List[Dict[str, Any]]) -> None:
    for c in all_chars:
        img_rel = c.get("image_url") or ""
        if img_rel and not re.match(r"^(https?:)?//", img_rel):
            dims = get_image_dimensions((ROOT / img_rel.lstrip("./")).resolve())
            if dims:
                c["image_w"], c["image_h"] = dims[0], dims[1]
                c["image_shape"] = classify_image_shape(dims[0], dims[1])
        port_rel = c.get("portrait_url") or img_rel
        if port_rel and not re.match(r"^(https?:)?//", port_rel):
            p_dims = get_image_dimensions((ROOT / port_rel.lstrip("./")).resolve())
            if p_dims:
                c["portrait_w"], c["portrait_h"] = p_dims[0], p_dims[1]
                c["portrait_shape"] = classify_image_shape(p_dims[0], p_dims[1])


def main() -> None:
    tiers_payload = json.loads((DATA_DIR / "tiers.json").read_text(encoding="utf-8"))
    chars_payload = json.loads((DATA_DIR / "characters.json").read_text(encoding="utf-8"))

    by_slug: Dict[str, Dict[str, Any]] = {}
    for entry in chars_payload.get("demo_archetypes", []):
        by_slug[entry["slug"]] = entry
    for entry in chars_payload.get("characters", []):
        by_slug[entry["slug"]] = entry
    all_chars = list(by_slug.values())
    enrich_character_media_dimensions(all_chars)

    rules_md = RULES_MD_PATH.read_text(encoding="utf-8")
    materials_md = MATERIALS_MD_PATH.read_text(encoding="utf-8")

    rules_html, rules_sections, rules_title_to_id = build_fulltext_doc_page(
        page_id="rules",
        active_nav="rules",
        title="衡天⊙ 多维战力量级体系（第五版·全文）",
        subtitle="核对判定通则、量级定义、无限类证据与图像测量规范。",
        source_filename="衡天量级体系【第五版·最新】.md",
        masthead_img="static/img/cosmos-eclipse.jpg",
        md_text=rules_md,
        other_doc_link=("materials.html", "材质与破坏能量数据库"),
    )
    (ROOT / "rules.html").write_text(rules_html, encoding="utf-8")

    materials_html, materials_sections, _ = build_fulltext_doc_page(
        page_id="materials",
        active_nav="materials",
        title="材质与破坏能量数据库（第二版·全文）",
        subtitle="岩石、金属、生物与天体材质的破坏能量参考。",
        source_filename="材质与破坏能量数据库（新）.md",
        masthead_img="static/img/physics-lattice.jpg",
        md_text=materials_md,
        other_doc_link=("rules.html", "衡天量级体系（第五版）"),
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
        f"[OK] PowerWiki v9.1 built successfully:\n"
        f"  - Core pages: index.html, tiers.html, characters.html, rules.html, materials.html, search.html\n"
        f"  - Standalone Tier pages: {len(tiers)} files in tier/*.html\n"
        f"  - Standalone Character pages: {len(all_chars)} files in character/*.html ({len(char_doc_sections)} full-text sections indexed)\n"
        f"  - Rules v5 TOC anchors: {len(rules_sections)} sections | Materials TOC anchors: {len(materials_sections)} sections"
    )


if __name__ == "__main__":
    main()
