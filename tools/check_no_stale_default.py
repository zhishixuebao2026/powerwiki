#!/usr/bin/env python3
"""反馈回路：断言 29 个升格默认页永远是整页皮肤，绝不会退回会闪屏的旧标准页。

这是 diagnosing-bugs 的 tight red-capable loop：
  - 绿 = 全站重建后 29 页均为整页（无 fade-on-load、升格标记在）
  - 红 = 任何一页退回标准页（用户症状：进旧默认 / 闪屏）
跑法：python3 tools/check_no_stale_default.py
"""
import subprocess, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 第三批 17 个升格默认页（2026-11-29，与 build_site.py PROMOTED_PRODUCT_DEFAULTS 同源）
THIRD_BATCH = [
    ("xiayouzhe", "xiayouzhe-sujuan"), ("futan", "futan-abyss"),
    ("guchensha", "guchensha-molong"), ("luofeng", "luofeng-xingcha"),
    ("tongguan", "tongguan-yunchi"), ("zhangyan", "zhangyan-zifu"),
    ("jiangwuye", "jiangwuye-starvortex"), ("linfei", "linfei-crystal"),
    ("lufasi", "ruphas-crimson"), ("xuezhishaonv", "xuezhishaonv-sujian"),
    ("yog", "yog-teal-vortex"), ("baiguang", "baiguang-gufeng"),
    ("suzhou", "suzhou-zhoutian"), ("xingshen", "xingshen-heng"),
    ("mozhe", "mozhe-mijing"), ("tianren", "tianren-register"),
    ("divinity", "divinity-seal"),
]
# 升格默认页 → 期望的"整页识别标记"（出现任一即认为是升格皮肤）
GUARDS = {
    "character/yutu.html":          ["pw-moon-nav"],
    "character/xuqing.html":        ['data-pw-edition="xuqing-qingchuan"'],
    "character/shangdi.html":       ['data-pw-edition="shangdi-jinian"'],
    "character/sunwukong.html":     ['data-pw-edition="sunwukong-lingxiao"'],
    "character/zhigaowangzuo.html": ['data-pw-edition="zhigaowangzuo-yihuan"'],
    "materials.html":               ['data-pw-edition="material-shatter"'],
    "rules.html":                   ['data-pw-edition="observatory"'],
    # 第二批 5 个（2026-11-28，产物基底 + base）：
    "character/pangu.html":         ['data-pw-edition="pangu-hunyuan"'],
    "character/starkiller.html":    ['data-pw-edition="starkiller-chixiao"'],
    "character/nvwa.html":          ['data-pw-edition="nvwa-boshan"'],
    "character/shiva.html":         ['data-pw-edition="shiva-yeke"'],
    "character/juxingzhihui.html":  ['data-pw-edition="juxingzhihui-lingchun"'],
}
for _s, _e in THIRD_BATCH:
    GUARDS[f"character/{_s}.html"] = [f'data-pw-edition="{_e}"']
STALE_MARK = "fade-on-load"  # 旧标准页（会闪屏）的特征

def check() -> int:
    fails = []
    for rel, markers in GUARDS.items():
        p = ROOT / rel
        if not p.exists():
            fails.append(f"{rel}: 文件不存在"); continue
        html = p.read_text(encoding="utf-8")
        if STALE_MARK in html:
            fails.append(f"{rel}: 含旧标准页特征 '{STALE_MARK}'（会闪屏）")
        if not any(m in html for m in markers):
            fails.append(f"{rel}: 缺升格皮肤标记 {markers}")
        # 旧默认卡守卫：切换器里不得再有显示名「默认」的旧卡（2026-11-29）。
        if re.search(r'data-edition-id="default"[^>]*>.*?pw-edition-name">默认<', html, re.S):
            fails.append(f"{rel}: 切换器里仍有旧「默认 / 建筑感栅格」卡未清除")
    if fails:
        print("[RED] 检测到旧默认/闪屏标准页：")
        for f in fails: print("  -", f)
        return 1
    print(f"[GREEN] {len(GUARDS)} 个升格默认页均为整页皮肤，无旧默认残留")
    return 0

if __name__ == "__main__":
    sys.exit(check())
