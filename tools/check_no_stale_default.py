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

# 2026-11-29 用户："切到别的皮肤，默认的又回到切换器了" + "当前的应该自动置顶"。
# 第二批 5 + 第三批 17 的升格皮肤仍留在登记表，皮肤页会重新生成一张冗余「默认」卡。
# 这些角色的【所有页面】（默认页 + 皮肤页）切换器都必须：无 default 卡、当前卡居首、
# 返回角色档案入口在。第一批（御兔等）走 DEFAULT_ALIAS 改名，default 卡是有意保留的
# 唯一回默认入口，不在此断言内。
STRIP_SLUGS = ["pangu", "starkiller", "nvwa", "shiva", "juxingzhihui"] + [s for s, _ in THIRD_BATCH]

def _check_dock(rel: str, html: str, fails: list) -> None:
    """校验一个页面的切换器：无冗余 default 卡 + 当前卡置顶 + 返回入口在。"""
    cards = re.findall(r'<a class="(pw-edition-card[^"]*)"\s+data-edition-id="([^"]+)"', html)
    if any(cid == "default" for _cls, cid in cards):
        fails.append(f"{rel}: 切换器仍有冗余「默认」卡（data-edition-id=default）")
    if cards and "is-current" not in cards[0][0]:
        fails.append(f"{rel}: 当前皮肤卡未置顶（首位={cards[0][1]}，未标 is-current）")
    if "pw-edition-home-btn" not in html:
        fails.append(f"{rel}: 切换器缺「返回角色档案」入口")

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
    # 皮肤页切换器守卫：扫描所有升格角色的默认页 + 皮肤页，覆盖上次遗漏的生成路径。
    dock_pages = [f"character/{s}.html" for s in STRIP_SLUGS]
    for sp in sorted((ROOT / "skins").glob("*/character-*.html")):
        slug = sp.stem[len("character-"):]
        if slug in STRIP_SLUGS:
            dock_pages.append(str(sp.relative_to(ROOT)))
    for rel in dock_pages:
        p = ROOT / rel
        if p.exists():
            _check_dock(rel, p.read_text(encoding="utf-8"), fails)
    # base 锚点守卫（2026-11-29「点左侧目录报错」）：凡注入了 <base> 的升格默认页，
    # 必须同时带锚点修复脚本，否则页内 href="#s-xxx" 会被解析到皮肤目录根 →
    # Directory listing / 404。防有人在 base 页新增锚点或改动注入逻辑时复发。
    base_pages = 0
    for p in sorted((ROOT / "character").glob("*.html")):
        html = p.read_text(encoding="utf-8")
        if re.search(r"<base\b", html, re.I):
            base_pages += 1
            if "data-pw-base-anchor-fix" not in html:
                fails.append(f"{p.relative_to(ROOT)}: 含 <base> 但缺锚点修复脚本（点目录会跳皮肤目录根报错）")
    if fails:
        print("[RED] 检测到旧默认/闪屏标准页：")
        for f in fails: print("  -", f)
        return 1
    print(f"[GREEN] {len(GUARDS)} 个升格默认页均为整页皮肤，无旧默认残留")
    return 0

if __name__ == "__main__":
    sys.exit(check())
