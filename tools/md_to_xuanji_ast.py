#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md -> 仪轨(xuanji) {sections,toc} 结构转换器。

仪轨正文是 JSON.parse(y4) 的 {sections:[...], toc:[...]}：
  section = {title:{t:h,l:1,in}, blocks:[...], id}
  block   = {t:p|h|tbl|ol|ul|q, ...}
    p   : {t,in}
    h   : {t,l:2|3,id,in}
    tbl : {t,head:[[inline],...],rows:[[[inline],...],...]}
    ol/ul:{t,items:[{in,children:[]}]}
    q   : {t,blocks:[p]}          # 多个 > 行在同一 p 内用 {t:br} 分隔
  inline = {t:x,v} | {t:b,c:[inline]} | {t:br}

标题 id：原文件里是手工 slug（"10.8" 保留点，"11.2" 变 "11-2"），无法推导。
因此**按标题原文复用现有 toc 的 id**；标题 138 条与 md 完全一致，全部可复用。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "skins/_source/xuanji.html"
LATEST_MD = ROOT / "data/docs/衡天量级体系【第六版·最新】.md"

SEG_BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str, br: bool = False) -> list[dict]:
    """行内解析：**粗体** → b，其余 x；反斜杠转义一律去掉（与现有正文一致）。"""
    text = text.replace("\\", "")
    out: list[dict] = []
    pos = 0
    for m in SEG_BOLD.finditer(text):
        if m.start() > pos:
            chunk = text[pos:m.start()]
            if chunk:
                out.append({"t": "x", "v": chunk})
        out.append({"t": "b", "c": [{"t": "x", "v": m.group(1)}]})
        pos = m.end()
    if pos < len(text):
        out.append({"t": "x", "v": text[pos:]})
    return out or [{"t": "x", "v": ""}]


def _join_br(lines: list[str]) -> list[dict]:
    """多行文本在单个 p 内用 {t:br} 连接；空串表示换行分隔。"""
    out: list[dict] = []
    for k, s in enumerate(lines):
        if k:
            out.append({"t": "br"})
        out.extend(inline(s))
    return out


def join_plain(lines: list[str]) -> str:
    return "".join(x.strip() for x in lines)


def parse_table(lines: list[str], start: int):
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
        i += 1
    if len(rows) < 2 or not all(re.fullmatch(r":?-{2,}:?", c) for c in rows[1] if c):
        return None, start
    head = [inline(c) for c in rows[0]]
    body = [[inline(c) for c in r] for r in rows[2:]]
    return {"t": "tbl", "head": head, "rows": body}, i


def parse_list(lines: list[str], start: int):
    ordered = bool(re.match(r"\s*\d+[.)]\s+", lines[start]))
    base = len(re.match(r"^(\s*)", lines[start]).group(1).replace("\t", "  "))
    items: list[dict] = []
    i = start
    while i < len(lines):
        m = re.match(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$", lines[i])
        if not m:
            if items and lines[i].startswith("  ") and lines[i].strip():
                items[-1]["in"][-1]["v"] += lines[i].strip()
                i += 1
                continue
            break
        indent = len(m.group(1).replace("\t", "  "))
        if indent < base:
            break
        if indent > base:
            sub, nxt = parse_list(lines, i)
            if sub and items:
                items[-1]["children"].append(sub)
                i = nxt
                continue
            break
        items.append({"in": inline(m.group(2)), "children": []})
        i += 1
    if not items:
        return None, start
    return {"t": "ol" if ordered else "ul", "items": items}, i


def parse_blocks(lines: list[str], start: int, end: int, ids: dict[str, str]) -> list[dict]:
    blocks: list[dict] = []
    i = start
    while i < end:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        if re.fullmatch(r"\s*(---+|\*\*\*+|___+)\s*", ln):
            i += 1           # 仪轨不渲染分隔线
            continue
        m = re.match(r"^(#{2,4})\s+(.*)$", ln)
        if m:
            raw = m.group(2).strip()
            blocks.append({
                "t": "h", "l": len(m.group(1)),
                "id": ids.get(raw, slug(raw)),
                "in": inline(raw),
            })
            i += 1
            continue
        if ln.lstrip().startswith(">"):
            qlines: list[str] = []
            while i < end and lines[i].lstrip().startswith(">"):
                qlines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner: list[dict] = []
            buf: list[str] = []
            for raw in qlines:
                if raw.strip().startswith("|"):
                    if buf:
                        inner.append({"t": "p", "in": _join_br(buf)})
                        buf = []
                    tbl, nxt = parse_table(qlines, qlines.index(raw))
                    if tbl:
                        inner.append(tbl)
                    continue
                if raw.strip():
                    buf.append(raw.strip())
            if buf:
                inner.append({"t": "p", "in": _join_br([x for x in buf])})
            blocks.append({"t": "q", "blocks": inner or [{"t": "p", "in": [{"t": "x", "v": ""}]}]})
            continue
        if ln.lstrip().startswith("|"):
            tbl, nxt = parse_table(lines, i)
            if tbl:
                blocks.append(tbl)
                i = nxt
                continue
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", ln):
            lst, nxt = parse_list(lines, i)
            if lst:
                blocks.append(lst)
                i = nxt
                continue
        buf = [ln]
        i += 1
        while i < end:
            s = lines[i]
            if not s.strip():
                break
            if re.match(r"^#{1,4}\s+", s) or s.lstrip().startswith(">") \
               or s.lstrip().startswith("|") \
               or re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", s) \
               or re.fullmatch(r"\s*(---+|\*\*\*+|___+)\s*", s):
                break
            buf.append(s)
            i += 1
        blocks.append({"t": "p", "in": inline(join_plain(buf))})
    return blocks


def slug(t: str) -> str:
    s = re.sub(r"[⊙⊙（）()「」『』“”\"'：:，,。.．、\s　]+", "-", t)
    return re.sub(r"-{2,}", "-", s).strip("-")


def parse_md(md: str, ids: dict[str, str]) -> dict:
    lines = md.split("\n")
    # 切 H1
    h1_idx = [i for i, l in enumerate(lines) if re.match(r"^#\s+", l)]
    sections = []
    for n, i in enumerate(h1_idx):
        end = h1_idx[n + 1] if n + 1 < len(h1_idx) else len(lines)
        title = re.sub(r"^#\s+", "", lines[i]).strip()
        sections.append({
            "title": {"t": "h", "l": 1, "in": inline(title)},
            "blocks": parse_blocks(lines, i + 1, end, ids),
            "id": ids.get(title, slug(title)),
        })
    toc = []
    chapter = -1
    for sec in sections:
        chapter += 1
        level1 = "".join(g.get("v", "") for g in sec["title"]["in"] if g["t"] == "x") or title_of(sec["title"])
        toc.append({"id": sec["id"], "title": level1, "level": 1, "idx": chapter})
        for b in sec["blocks"]:
            if b["t"] == "h":
                txt = "".join(g.get("v", "") for g in b["in"] if g["t"] == "x") or title_of(b["in"])
                toc.append({"id": b["id"], "title": txt, "level": b["l"], "idx": chapter})
    return {"sections": sections, "toc": toc}


def title_of(inl: list[dict]) -> str:
    out = []
    for g in inl:
        if g["t"] == "x":
            out.append(g["v"])
        elif g["t"] == "b":
            out.append(title_of(g["c"]))
    return "".join(out)


def text_of_block(b: dict) -> str:
    t = b["t"]
    if t in ("p", "h"):
        return inline_text(b["in"])
    if t == "q":
        return "\n".join(text_of_block(x) for x in b["blocks"])
    if t in ("ol", "ul"):
        out = []
        for it in b["items"]:
            out.append(inline_text(it["in"]))
            for ch in it.get("children", []):
                out.append(text_of_block(ch))
        return "\n".join(x for x in out if x)
    if t == "tbl":
        def row(cells):
            return "|".join(inline_text(c) for c in cells)
        return "\n".join([row(b["head"])] + [row(r) for r in b["rows"]])
    return ""


def inline_text(inl: list[dict]) -> str:
    out = []
    for g in inl:
        if g["t"] == "x":
            out.append(g["v"])
        elif g["t"] == "b":
            out.append(inline_text(g["c"]))
        elif g["t"] == "br":
            out.append("\n")
    return "".join(out)


def extract_y4(html: str) -> tuple[int, int]:
    start = html.find("y4='") + len("y4='")
    if start < len("y4='"):
        raise SystemExit("未找到 y4='")
    i, esc = start, False
    while i < len(html):
        c = html[i]
        if esc:
            esc = False
        elif c == "\\":
            esc = True
        elif c == "'":
            return start, i
        i += 1
    raise SystemExit("y4 未闭合")


def load_existing() -> tuple[dict, str]:
    html = SRC.read_text(encoding="utf-8")
    a, b = extract_y4(html)
    raw = html[a:b]
    data = json.loads(raw.replace("\\'", "'").replace("\\\\", "\\"))
    return data, html


def id_map(data: dict) -> dict[str, str]:
    m: dict[str, str] = {}
    for t in data["toc"]:
        m[t["title"]] = t["id"]
    return m


def main() -> int:
    data, _ = load_existing()
    old_blocks = []
    for sec in data["sections"]:
        old_blocks.extend(sec["blocks"])
    old_md = Path("/tmp/skin_md.md").read_text(encoding="utf-8")
    new = parse_md(old_md, id_map(data))
    new_blocks = []
    for sec in new["sections"]:
        new_blocks.extend(sec["blocks"])
    print(f"sections 旧 {len(data['sections'])} / 新 {len(new['sections'])}；toc 旧 {len(data['toc'])} / 新 {len(new['toc'])}")
    print(f"块数 旧 {len(old_blocks)} / 新 {len(new_blocks)}")
    from collections import Counter
    print("旧块类型:", dict(Counter(b['t'] for b in old_blocks)))
    print("新块类型:", dict(Counter(b['t'] for b in new_blocks)))
    diffs = 0
    shown = 0
    for idx in range(min(len(old_blocks), len(new_blocks))):
        a, b = old_blocks[idx], new_blocks[idx]
        if a["t"] != b["t"] or text_of_block(a) != text_of_block(b):
            diffs += 1
            if shown < 6:
                ta, tb = text_of_block(a), text_of_block(b)
                k = next((x for x in range(min(len(ta), len(tb))) if ta[x] != tb[x]), min(len(ta), len(tb)))
                print(f"--- #{idx} 旧[{a['t']}] vs 新[{b['t']}] len {len(ta)}/{len(tb)}")
                print(f"    旧: {ta[max(0,k-25):k+45]!r}")
                print(f"    新: {tb[max(0,k-25):k+45]!r}")
                shown += 1
    print(f"\n逐块不一致 {diffs}/{min(len(old_blocks), len(new_blocks))}")
    # toc 标题序列比对
    old_titles = [t["title"] for t in data["toc"]]
    new_titles = [t["title"] for t in new["toc"]]
    print("toc 标题序列一致:", old_titles == new_titles)
    if old_titles != new_titles:
        for a, b in zip(old_titles, new_titles):
            if a != b:
                print("  首个差异:", repr(a), "vs", repr(b))
                break
    return 0 if diffs == 0 else 1


def apply_latest() -> int:
    data, html = load_existing()
    ids = id_map(data)
    md = LATEST_MD.read_text(encoding="utf-8")
    new = parse_md(md, ids)
    from collections import Counter
    print("新 sections:", len(new["sections"]), " toc:", len(new["toc"]),
          dict(Counter(b["t"] for s_ in new["sections"] for b in s_["blocks"])))
    missing = [t["title"] for t in new["toc"] if t["id"] == slug(t["title"]) and t["title"] not in ids]
    if missing:
        print("[ABORT] 有标题找不到原 id：", missing[:5])
        return 1
    body = json.dumps(new, ensure_ascii=False, separators=(",", ":"))
    body_esc = body.replace("\\", "\\\\").replace("'", "\\'")
    a, b = extract_y4(html)
    old_len = b - a
    html = html[:a] + body_esc + html[b:]
    SRC.write_text(html, encoding="utf-8")
    print(f"[ok] xuanji 正文 {old_len} → {len(body_esc)} 字符")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        sys.exit(apply_latest())
    sys.exit(main())
