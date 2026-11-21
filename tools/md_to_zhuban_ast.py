#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""md -> 朱版(zhuban)块结构 的转换器（先做回归验证，不改文件）。

朱版的正文是 JSON.parse('[...]')：块 = {k:p|h|ul|ol|tbl|q|hr}
  h: {k,lvl(1-3),id(c/s/ss + 序号),segs}
  p: {k,segs}
  ul/ol: {k,items:[{depth,segs}]}
  tbl: {k,head:[[segs],...],rows:[[[segs],...],...]}
  q: {k,children:[p|tbl]}
  hr: {k}
segs: {t:b|x, s:str}
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SEG_BOLD = re.compile(r"\*\*(.+?)\*\*")


def inline(text: str) -> list[dict]:
    """行内：**粗体** -> b 段，其余 x 段；清掉 markdown 反斜杠转义。"""
    # 朱版正文不含任何反斜杠：markdown 转义（F\* 等）一律还原为字面字符
    text = text.replace("\\", "")
    segs: list[dict] = []
    pos = 0
    for m in SEG_BOLD.finditer(text):
        if m.start() > pos:
            chunk = text[pos:m.start()]
            if chunk:
                segs.append({"t": "x", "s": chunk})
        segs.append({"t": "b", "s": m.group(1)})
        pos = m.end()
    if pos < len(text):
        segs.append({"t": "x", "s": text[pos:]})
    if not segs:
        segs.append({"t": "x", "s": ""})
    return segs


def join_lines(lines: list[str]) -> str:
    return "".join(x.strip() for x in lines)


def parse_table(lines: list[str], start: int) -> tuple[dict | None, int]:
    """从 start 行起的表格块。返回 (block, next_index)。"""
    rows: list[list[str]] = []
    i = start
    while i < len(lines) and lines[i].lstrip().startswith("|"):
        raw = lines[i].strip().strip("|")
        cells = [c.strip() for c in raw.split("|")]
        rows.append(cells)
        i += 1
    if len(rows) < 2:
        return None, start
    # 第二行是 |---|---| 分隔行
    sep = rows[1]
    if not all(re.fullmatch(r":?-{2,}:?", c) for c in sep if c != ""):
        return None, start
    head = [inline(c) for c in rows[0]]
    body = [[inline(c) for c in r] for r in rows[2:]]
    return {"k": "tbl", "head": head, "rows": body}, i


def parse_list(lines: list[str], start: int) -> tuple[dict | None, int]:
    i = start
    items: list[dict] = []
    ordered = bool(re.match(r"\s*\d+[.)]\s+", lines[i]))
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(\s*)(?:[-*+]|\d+[.)])\s+(.*)$", ln)
        if not m:
            # 续行（缩进的非列表行）并入上一项
            if items and ln.startswith("  ") and ln.strip():
                items[-1]["segs"][-1]["s"] += ln.strip()
                i += 1
                continue
            break
        indent = len(m.group(1).replace("\t", "  "))
        depth = 1 if indent >= 2 else 0
        items.append({"depth": depth, "segs": inline(m.group(2))})
        i += 1
    if not items:
        return None, start
    return {"k": "ol" if ordered else "ul", "items": items}, i


def parse_md(md: str) -> list[dict]:
    lines = md.split("\n")
    blocks: list[dict] = []
    counters = {1: 0, 2: 0, 3: 0}
    prefix = {1: "c", 2: "s", 3: "ss"}
    i = 0
    n = len(lines)
    while i < n:
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        # 分隔线
        if re.fullmatch(r"\s*(---+|\*\*\*+|___+)\s*", ln):
            blocks.append({"k": "hr"})
            i += 1
            continue
        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = min(len(m.group(1)), 3)
            counters[lvl] += 1
            blocks.append({
                "k": "h", "lvl": lvl,
                "id": f"{prefix[lvl]}{counters[lvl]}",
                "segs": inline(m.group(2).strip()),
            })
            i += 1
            continue
        # 引用
        if ln.lstrip().startswith(">"):
            inner: list[str] = []
            while i < n and lines[i].lstrip().startswith(">"):
                inner.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            children: list[dict] = []
            j = 0
            while j < len(inner):
                s = inner[j]
                if not s.strip():
                    j += 1
                    continue
                if s.lstrip().startswith("|"):
                    tbl, nxt = parse_table(inner, j)
                    if tbl:
                        children.append(tbl)
                        j = nxt
                        continue
                children.append({"k": "p", "segs": inline(s.strip())})
                j += 1
            blocks.append({"k": "q", "children": children})
            continue
        # 表格
        if ln.lstrip().startswith("|"):
            tbl, nxt = parse_table(lines, i)
            if tbl:
                blocks.append(tbl)
                i = nxt
                continue
        # 列表
        if re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", ln):
            lst, nxt = parse_list(lines, i)
            if lst:
                blocks.append(lst)
                i = nxt
                continue
        # 段落
        buf = [ln]
        i += 1
        while i < n:
            s = lines[i]
            if not s.strip():
                break
            if re.match(r"^(#{1,4})\s+", s) or s.lstrip().startswith(">") \
               or s.lstrip().startswith("|") \
               or re.match(r"^\s*(?:[-*+]|\d+[.)])\s+", s) \
               or re.fullmatch(r"\s*(---+|\*\*\*+|___+)\s*", s):
                break
            buf.append(s)
            i += 1
        blocks.append({"k": "p", "segs": inline(join_lines(buf))})
    return blocks


def text_of(block: dict) -> str:
    k = block["k"]
    if k in ("h", "p"):
        return "".join(g["s"] for g in block["segs"])
    if k in ("ul", "ol"):
        return "\n".join("".join(g["s"] for g in it["segs"]) for it in block["items"])
    if k == "tbl":
        def row_text(cells):
            return "|".join("".join(g["s"] for g in c) for c in cells)
        return "\n".join([row_text(block["head"])] + [row_text(r) for r in block["rows"]])
    if k == "q":
        return "\n".join(text_of(c) for c in block["children"])
    return ""


def main() -> int:
    old_md = Path("/tmp/skin_md.md").read_text(encoding="utf-8")
    old_blocks = json.loads(Path("/tmp/zhuban_blocks.json").read_text(encoding="utf-8"))
    new_blocks = parse_md(old_md)
    print(f"旧结构块数 {len(old_blocks)} / 新解析块数 {len(new_blocks)}")

    from collections import Counter
    print("旧 k 分布:", dict(Counter(b["k"] for b in old_blocks)))
    print("新 k 分布:", dict(Counter(b["k"] for b in new_blocks)))

    # 逐块文本比对
    lim = min(len(old_blocks), len(new_blocks))
    diffs = 0
    shown = 0
    for idx in range(lim):
        a, b = old_blocks[idx], new_blocks[idx]
        if a["k"] != b["k"] or text_of(a) != text_of(b):
            diffs += 1
            if shown < 8:
                ta, tb = text_of(a), text_of(b)
                print(f"--- #{idx} 旧[{a['k']}] vs 新[{b['k']}]  len {len(ta)}/{len(tb)}")
                k0 = next((x for x in range(min(len(ta), len(tb))) if ta[x] != tb[x]), min(len(ta), len(tb)))
                print(f"    旧: ...{ta[max(0,k0-30):k0+40]!r}")
                print(f"    新: ...{tb[max(0,k0-30):k0+40]!r}")
                shown += 1
    print(f"\n逐块不一致 {diffs}/{lim}")
    Path("/tmp/zhuban_new_blocks.json").write_text(
        json.dumps(new_blocks, ensure_ascii=False), encoding="utf-8")
    return 0 if diffs == 0 and len(old_blocks) == len(new_blocks) else 1


def locate_blob(html: str) -> tuple[int, int]:
    """定位 JSON.parse('…') 里的原始串区间 [start, end)。"""
    start = html.find("JSON.parse('") + len("JSON.parse('")
    if start < len("JSON.parse('"):
        raise SystemExit("未找到 JSON.parse(' 包裹的正文")
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
    raise SystemExit("正文串未闭合")


def apply_latest() -> int:
    """把最新 md 转成朱版块结构并写回 skins/_source/zhuban.html。"""
    latest = (Path(__file__).resolve().parent.parent
              / "data/docs/衡天量级体系【第六版·最新】.md").read_text(encoding="utf-8")
    blocks = parse_md(latest)
    from collections import Counter
    print("新结构块数:", len(blocks), dict(Counter(b["k"] for b in blocks)))
    print("11-13:", sum(1 for b in blocks for g in text_of(b).split("2026-11-13") if g) - 1,
          "（存在性）")
    body = json.dumps(blocks, ensure_ascii=False, separators=(",", ":"))
    body_esc = body.replace("\\", "\\\\").replace("'", "\\'")
    path = Path(__file__).resolve().parent.parent / "skins/_source/zhuban.html"
    html = path.read_text(encoding="utf-8")
    a, b = locate_blob(html)
    old_len = b - a
    html = html[:a] + body_esc + html[b:]
    path.write_text(html, encoding="utf-8")
    print(f"[ok] zhuban 正文 {old_len} → {len(body_esc)} 字符")
    return 0


if __name__ == "__main__":
    if "--apply" in sys.argv:
        sys.exit(apply_latest())
    sys.exit(main())
