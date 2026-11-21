#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把规则皮肤的嵌入 Markdown 正文同步为 data/docs 最新版。

背景：候星(observatory)、宣衡典章(xuanheng) 两套整页皮肤把整份规则以
Markdown 原文存进 JS 模板字符串，运行时前端渲染。它们当初接入时底本是
11-06 版，落后于最新 md（11-13 推定规则 / 11-15 超越类描述等）。

同步方式：定位模板字符串内的 Markdown 段，整段替换为最新 md。
因为标题结构完全一致（138 标题、0 差异），目录与锚点由前端从标题派生，
替换后自动跟随，无需改其它代码。

注意：模板字符串会吃掉一层反斜杠，最新 md 里的 `F\\*`（markdown 转义）
写进模板串必须变成 `F\\\\*`，否则运行时退化成裸 `*` 触发斜体。
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEST_MD = ROOT / "data/docs/衡天量级体系【第六版·最新】.md"

# 只处理 Markdown 原文格式的皮肤；仪轨/朱版是 AST 结构，另做
TARGETS = ["observatory", "xuanheng"]


def norm_heading(t: str) -> str:
    return re.sub(r"[\s#*`·、（）()：:，,.。\-—；;\"“”‘’]+", "", t)


def heading_list(md: str) -> list[str]:
    return re.findall(r"^#{1,4}\s+(.+)$", md, re.M)


def main() -> int:
    latest = LATEST_MD.read_text(encoding="utf-8")
    if "`" in latest or "${" in latest:
        print("[ABORT] 最新 md 含反引号或 ${，无法安全写入模板字符串")
        return 1
    latest_heads = heading_list(latest)
    latest_set = {norm_heading(h) for h in latest_heads}
    escaped = latest.replace("\\", "\\\\")
    print(f"最新 md: {len(latest)} 字符 / {len(latest_heads)} 标题 / 反斜杠 {latest.count(chr(92))} 个")

    rc = 0
    for eid in TARGETS:
        path = ROOT / f"skins/_source/{eid}.html"
        if not path.exists():
            print(f"[skip] {eid}: 源文件不存在")
            continue
        src = path.read_text(encoding="utf-8")
        m = re.search(r"`# 衡天[^`]*", src)
        if not m:
            print(f"[skip] {eid}: 未找到以反引号包裹的 Markdown 段")
            rc = 1
            continue
        start = m.start() + 1
        end = src.find("`", start)
        old_md = src[start:end]

        old_heads = heading_list(old_md)
        old_set = {norm_heading(h) for h in old_heads}
        if old_set != latest_set:
            print(f"[ABORT] {eid}: 标题结构不一致（旧 {len(old_heads)} / 新 {len(latest_heads)}）")
            rc = 1
            continue

        new_src = src[:start] + escaped + src[end:]
        path.write_text(new_src, encoding="utf-8")
        print(
            f"[ok] {eid}: {len(old_md)} → {len(latest)} 字符 "
            f"(+{len(latest) - len(old_md)})，标题 {len(old_heads)} 一致，"
            f"11-13={latest.count('2026-11-13')} 11-15={latest.count('2026-11-15')}"
        )
    return rc


if __name__ == "__main__":
    sys.exit(main())
