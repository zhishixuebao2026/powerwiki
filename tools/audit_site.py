#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PowerWiki 全站体检（防「浏览时突然冒 bug」）。

把每次上线前该做的检查固化成一条可重复运行的命令，不靠人肉记忆：

    python3 tools/audit_site.py                 # 静态体检（默认，秒级）
    python3 tools/audit_site.py --render        # 额外渲染复判状态栏明暗（需本地服务 + playwright）
    python3 tools/audit_site.py --build         # 先重建再体检
    python3 tools/audit_site.py --url http://localhost:8137 --render

检查项：
  1. 36 套产物：dock JSX / data-dock-toggle 残留、JS 语法（node --check）、
     状态栏 meta、皮肤切换器、沉浸式避让、clearbar.css、文件完整闭合
  2. 切换器链路：148+ 卡片链接与缩略图目标是否存在（防 404 / 破图）
  3. 登记表：editions.json ↔ 产物目录 ↔ section 路径 ↔ source 一致性
  4. 双主题皮肤清单：列出跟随系统深色模式的皮肤（记录已知边界，不判失败）
  5. 首页 Hero 亮色版：双图资源 + 亮色主题样式分支齐全（防深色块复发）
  6. 角色配图：每个角色都有 16:9 卡片图 + 2:3 肖像图且文件存在（防漏图 /
     回退 monogram / 比例错乱）
  7. 已定级内容基线：角色定级字段、角色归档原文、data/tiers.json 量级数值
     与基线指纹比对（规则/皮肤同步时误改定级会直接判失败）
  8. 状态栏明暗：--render 时逐套量取状态栏正下方 (195,22) 真实底色亮度，
     与 SKIN_STATUS_BAR_MODE 比对（能抓出整页中位数采样抓不到的漏判）

规则更新的允许改动范围见 docs/需求与约定.md：只动规则文档、规则页、
版本标签与皮肤展示层；已定级的角色档位与量级数值一律不动。确需改档时
用 --update-baseline 显式重建基线并在 CHANGELOG 记录。

退出码：有问题 1，全通过 0。可直接接进 CI / 发布前钩子。
"""
import argparse
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

DOCK_CLASS = 'className:"fixed inset-x-0 bottom-0 z-40 lg:hidden"'
CARD_RE = re.compile(
    r'<a\s+class="pw-edition-card[^"]*"\s+data-edition-id="([^"]+)"\s+href="([^"]+)"',
    re.S,
)
IMG_RE = re.compile(r'<img\s+src="([^"]*static/img/editions/[^"]+)"', re.S)
SCRIPT_RE = re.compile(r"<script\b[^>]*>(.*?)</script>", re.S)


def products():
    return sorted(
        p for p in glob.glob("skins/*/*.html") if "/_source/" not in p
    )


def js_syntax_ok(html):
    """逐段提取内联 script 交给 node --check；返回 (ok, 错误信息)。"""
    if not _has_node():
        return None, "node 不可用，跳过语法校验"
    for idx, m in enumerate(SCRIPT_RE.finditer(html)):
        js = m.group(1)
        if not js.strip():
            continue
        with tempfile.NamedTemporaryFile(
            "w", suffix=".mjs", delete=False, encoding="utf-8"
        ) as f:
            f.write(js)
            tmp = f.name
        try:
            cp = subprocess.run(
                ["node", "--check", tmp], capture_output=True, text=True, timeout=90
            )
        finally:
            os.unlink(tmp)
        if cp.returncode != 0:
            last = (cp.stderr.strip().splitlines() or ["?"])[-1]
            return False, f"script#{idx}: {last[:140]}"
    return True, ""


def _has_node():
    try:
        return subprocess.run(["node", "--version"], capture_output=True, timeout=5).returncode == 0
    except Exception:
        return False


def check_products():
    issues = []
    rows = []
    for p in products():
        h = open(p, encoding="utf-8", errors="replace").read()
        r = {"file": p, "size": len(h)}
        r["dock_cls"] = h.count(DOCK_CLASS)
        r["dock_toggle"] = h.count("data-dock-toggle")
        r["statusbar"] = (
            re.findall(r'status-bar-style"\s+content="([a-z]+)', h) or ["MISSING"]
        )[0]
        r["edock"] = h.count("pw-edition-dock")
        r["editions_js"] = h.count("static/js/editions.js")
        r["viewport_cover"] = h.count("viewport-fit=cover")
        r["safearea"] = h.count("env(safe-area-inset-top")
        r["clearbar"] = h.count("static/css/clearbar.css")
        r["html_close"] = h.count("</html>")
        ok, err = js_syntax_ok(h)
        r["js_ok"], r["js_err"] = ok, err
        rows.append(r)

        if r["dock_cls"] or r["dock_toggle"]:
            issues.append(f"{p}: 重复目录 dock 残留 cls={r['dock_cls']} toggle={r['dock_toggle']}")
        if r["statusbar"] == "MISSING":
            issues.append(f"{p}: 状态栏 meta 缺失")
        if not r["edock"]:
            issues.append(f"{p}: 皮肤切换器缺失")
        if not r["editions_js"]:
            issues.append(f"{p}: editions.js 缺失")
        if not r["viewport_cover"]:
            issues.append(f"{p}: viewport-fit=cover 缺失")
        if not r["safearea"]:
            issues.append(f"{p}: env(safe-area-inset-top) 避让缺失")
        if not r["clearbar"]:
            issues.append(f"{p}: clearbar.css 引用缺失")
        if not r["html_close"]:
            issues.append(f"{p}: </html> 缺失（文件可能截断）")
        if ok is False:
            issues.append(f"{p}: JS 语法错误 {err}")
    return rows, issues


def check_links():
    """切换器卡片链接与缩略图目标存在性（防 404 / 破图）。"""
    missing = []
    total_cards = 0
    total_imgs = 0
    for p in products():
        h = open(p, encoding="utf-8", errors="replace").read()
        base = os.path.dirname(p)
        cards = CARD_RE.findall(h)
        if not cards:
            # 单皮肤角色（升格后仅剩 1 套）：切换器按设计收起，只保留 home-btn 返回入口，
            # 没有可切换卡片是合法的。但仍须有返回入口，否则才算真缺失。
            if 'pw-edition-home-btn' in h:
                continue
            missing.append(f"{p}: 找不到切换器卡片")
            continue
        for eid, href in cards:
            total_cards += 1
            if href.startswith(("http", "#", "javascript")):
                continue
            target = os.path.normpath(os.path.join(base, href.split("#")[0].split("?")[0]))
            if not os.path.exists(target):
                missing.append(f"{p}: 卡片 {eid} 指向不存在 {href}")
        for src in IMG_RE.findall(h):
            total_imgs += 1
            t = os.path.normpath(os.path.join(base, src))
            if not os.path.exists(t):
                missing.append(f"{p}: 缩略图缺失 {src}")
    return total_cards, total_imgs, missing


def check_manifest():
    """editions.json ↔ 产物目录 ↔ section 路径 ↔ source / patch 一致性。"""
    issues = []
    d = json.load(open("data/editions.json", encoding="utf-8"))
    eds = d["editions"] if isinstance(d, dict) else d
    ids = [e["id"] for e in eds]
    if len(ids) != len(set(ids)):
        issues.append("editions.json 存在重复 id")
    for e in eds:
        for key in ("source", "patch"):
            if e.get(key) and not os.path.exists(e[key]):
                issues.append(f"{e['id']}: {key} 不存在 {e[key]}")
        if e["id"] == "default":
            continue  # 主站默认皮肤没有独立产物目录，属正常
        sec = e.get("section") or "home"
        if not os.path.exists(f"skins/{e['id']}/{sec}.html"):
            issues.append(f"{e['id']}: 产物缺失 skins/{e['id']}/{sec}.html")
    dirs = {
        os.path.basename(os.path.dirname(p)) for p in products()
    }
    for x in sorted(dirs - set(ids)):
        issues.append(f"产物目录 {x} 未登记在 editions.json")
    return len(eds), issues


def dual_theme_skins():
    """列出自带 data-theme 双主题、跟随系统深色模式的皮肤（已知边界记录）。"""
    out = []
    for f in sorted(glob.glob("skins/_source/*.html")):
        h = open(f, encoding="utf-8", errors="replace").read()
        if "data-theme" in h and re.search(r'prefers-color-scheme', h):
            out.append(Path(f).stem)
    return out


def render_statusbar(base_url):
    """逐套渲染，量取状态栏正下方 (195,22) 真实底色亮度，与映射表比对。"""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return None, ["未安装 playwright，--render 跳过"]
    sys.path.insert(0, str(ROOT))
    import build_site as B

    JS = r"""()=>{
      function parse(c){
        if(!c) return null; c=c.trim();
        if(/^(transparent|none|initial|unset)$/i.test(c)) return null;
        if(c.startsWith('rgb')){const n=c.match(/[\d.]+/g); if(!n||n.length<3) return null;
          const a=n.length>3?parseFloat(n[3]):1; if(a<0.5) return null;
          return [parseFloat(n[0]),parseFloat(n[1]),parseFloat(n[2])];}
        if(c.startsWith('oklab')){const L=parseFloat((c.match(/[\d.]+%?/)||['0'])[0]);
          return [L*2.55,L*2.55,L*2.55];}
        if(c.startsWith('color(')){const n=c.match(/[\d.]+/g);
          return n&&n.length>=3?[n[0]*255,n[1]*255,n[2]*255]:null;}
        const h=c.match(/^#([0-9a-f]{3}|[0-9a-f]{6})$/i);
        if(h){let s=h[1]; if(s.length===3) s=s.split('').map(x=>x+x).join('');
          return [parseInt(s.slice(0,2),16),parseInt(s.slice(2,4),16),parseInt(s.slice(4,6),16)];}
        return null;}
      let el=document.elementFromPoint(195,22);
      while(el){
        const bg=parse(getComputedStyle(el).backgroundColor);
        if(bg) return {rgb:bg};
        el=el.parentElement;}
      return {rgb:null};
    }"""
    mismatches = []
    checked = 0
    skipped = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--no-sandbox"])
        for p in products():
            skin = Path(p).parent.name
            try:
                pg = browser.new_page(viewport={"width": 390, "height": 844})
                pg.goto(f"{base_url}/{p}", wait_until="domcontentloaded", timeout=30000)
                try:
                    pg.wait_for_function(
                        "document.body && document.body.innerText.length>300", timeout=20000
                    )
                except Exception:
                    pass
                pg.wait_for_timeout(400)
                r = pg.evaluate(JS)
                pg.close()
            except Exception as e:
                skipped.append(f"{skin}: {str(e)[:60]}")
                continue
            rgb = r.get("rgb")
            if rgb is None:
                skipped.append(f"{skin}: 取不到底色")
                continue
            lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
            expect = "default" if lum >= 128 else "black"
            current = B.SKIN_STATUS_BAR_MODE.get(skin, "default")
            checked += 1
            if expect != current:
                mismatches.append(
                    f"{skin}: 实测亮度 {round(lum)} 应为 {expect}，当前却是 {current}"
                )
        browser.close()
    return {"checked": checked, "mismatches": mismatches, "skipped": skipped}, mismatches


def check_hero_light():
    """首页 Hero 亮色版回归：双图资源 + 亮色主题样式分支必须同时存在。

    防止日后重构 CSS 时把 hero 又写死成深色（亮色页面里冒出深色块），
    也防止只改图片或只改样式导致明暗两版不同步。
    """
    issues = []
    idx = ROOT / "index.html"
    css = ROOT / "static/css/editorial.css"
    dark = ROOT / "static/img/cosmic-atlas-hero.jpg"
    light = ROOT / "static/img/cosmic-atlas-hero-light.jpg"

    if not idx.exists():
        return ["首页 index.html 缺失"], 0
    html = idx.read_text(encoding="utf-8")
    for cls in ("hero-art-dark", "hero-art-light"):
        if cls not in html:
            issues.append("首页 Hero 缺少 %s 底图层" % cls)
    for f in (dark, light):
        if not f.exists():
            issues.append("Hero 底图缺失：%s" % f.name)
    if not css.exists():
        issues.append("editorial.css 缺失")
    else:
        c = css.read_text(encoding="utf-8")
        for sel in ('html[data-theme="light"] .hero-banner',
                    'html[data-theme="light"] .hero-backdrop::after',
                    'html[data-theme="light"] .hero-heading'):
            if sel not in c:
                issues.append("editorial.css 缺少亮色 Hero 规则：%s" % sel)
        if not re.search(r'html\[data-theme="light"\][^{]*\.hero-art-light\s*\{', c):
            issues.append("editorial.css 缺少亮色 Hero 图层规则（light → hero-art-light）")
    return issues, light.stat().st_size if light.exists() else 0


# 采用「卡片图精确 16:9 + 肖像图精确 2:3」规范制作的角色。
# 分辨率不限（既有 1536x864/1024x1536，也有官方高清 2560x1440/1200x1800）。
# 历史角色（含 yog / divinity / lufasi / tianren 等）的配图比例本就多样，
# 由 CSS 的 contain / cover 正常兜底，属既有设计，不参与比例校验。
# 日后新增角色若沿用同一规范，把 slug 加进这里即可自动纳入。
STD_MEDIA_SLUGS = {"nvwa", "shiva", "sunwukong", "pangu", "starkiller", "luofeng", "xuqing", "zhangyan",
                   "juxingzhihui", "mozhe", "shangdi", "suzhou", "baiguang", "xingshen", "aladiya"}


def check_character_media():
    """角色配图回归：每个角色都要登记配图且文件真实可读，防止回退 monogram / 破图。

    STD_MEDIA_SLUGS 里的角色额外校验精确比例：卡片图 16:9、肖像图 2:3（±2%）。
    """
    issues = []
    data = ROOT / "data/characters.json"
    if not data.exists():
        return ["characters.json 缺失"], 0
    chars = json.loads(data.read_text(encoding="utf-8"))["characters"]
    with_img = 0
    ratio_checked = 0
    for c in chars:
        slug = c["slug"]
        for field in ("image_url", "portrait_url"):
            rel = c.get(field) or ""
            if not rel:
                issues.append("%s 缺 %s（会回退成 monogram）" % (slug, field))
                continue
            f = ROOT / rel.lstrip("./")
            if not f.is_file():
                issues.append("%s 的 %s 指向的文件不存在：%s" % (slug, field, rel))
                continue
            try:
                from PIL import Image
                w, h = Image.open(f).size
                if w <= 0 or h <= 0:
                    issues.append("%s 的 %s 尺寸无效：%dx%d" % (slug, field, w, h))
                    continue
                # 仅规范名单内的角色校验精确比例
                if slug in STD_MEDIA_SLUGS:
                    want = 16 / 9 if field == "image_url" else 2 / 3
                    ratio_checked += 1
                    if abs(w / h - want) > 0.02:
                        issues.append("%s 的 %s 比例错乱：%dx%d (%.4f)，期望 %.4f"
                                      % (slug, field, w, h, w / h, want))
            except Exception as exc:
                issues.append("%s 的 %s 无法读取尺寸：%s" % (slug, field, exc))
        if c.get("image_url") and c.get("portrait_url"):
            with_img += 1
    return issues, with_img, ratio_checked


# --- 7) 已定级内容基线 ---------------------------------------------------
# 规则/皮肤同步只允许改「规则文档、规则页、版本标签、皮肤展示层」；
# 已定级的角色档位、定级归档原文、量级数值表一律锁死。
BASELINE_PATH = ROOT / "tools" / "grading_baseline.json"
# 这些是展示/配图字段，允许随配图调整变动，不计入定级指纹
GRADING_MUTABLE_FIELDS = {
    "image_url", "portrait_url", "portrait_caption", "image_map", "visual",
}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _grading_snapshot():
    chars = json.loads(
        (ROOT / "data/characters.json").read_text(encoding="utf-8")
    )["characters"]
    char_fp = {}
    for c in chars:
        locked = {k: v for k, v in c.items() if k not in GRADING_MUTABLE_FIELDS}
        blob = json.dumps(locked, ensure_ascii=False, sort_keys=True,
                          separators=(",", ":"))
        char_fp[c["slug"]] = _sha(blob.encode("utf-8"))
    doc_fp = {}
    for p in sorted((ROOT / "data/docs/characters").glob("*.md")):
        doc_fp[p.relative_to(ROOT).as_posix()] = _sha(p.read_bytes())
    return {
        "characters": char_fp,
        "character_docs": doc_fp,
        "tiers_json": _sha((ROOT / "data/tiers.json").read_bytes()),
    }


def check_grading_baseline(update=False):
    """返回 (问题列表, 说明)。新增角色/归档不拦，已有内容被改一律判失败。"""
    snap = _grading_snapshot()
    if update or not BASELINE_PATH.exists():
        payload = {
            "note": "已定级内容指纹基线；规则/皮肤同步不得改动下列数据。"
                    "确需改档时显式运行 audit_site.py --update-baseline 并在 CHANGELOG 记录。",
            **snap,
        }
        BASELINE_PATH.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        action = "已更新" if update else "首次生成"
        return [], (f"{action}基线：{len(snap['characters'])} 角色 / "
                    f"{len(snap['character_docs'])} 归档 / tiers.json")

    base = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    issues = []
    old_chars = base.get("characters", {})
    for slug, fp in snap["characters"].items():
        if slug in old_chars and old_chars[slug] != fp:
            issues.append(
                f"角色 {slug} 的已定级字段被改动（规则同步不得触碰；"
                f"确需改档请 --update-baseline 并记 CHANGELOG）"
            )
    old_docs = base.get("character_docs", {})
    for path, fp in snap["character_docs"].items():
        if path in old_docs and old_docs[path] != fp:
            issues.append(f"角色定级归档被改动：{path}")
    for path in old_docs:
        if path not in snap["character_docs"]:
            issues.append(f"角色定级归档缺失：{path}")
    if base.get("tiers_json") != snap["tiers_json"]:
        issues.append("data/tiers.json 量级数值被改动（规则同步不得触碰）")
    summary = (f"{len(snap['characters'])} 角色 / "
               f"{len(snap['character_docs'])} 归档 / tiers.json")
    return issues, summary if issues else summary + " 全部与基线一致"


def main():
    ap = argparse.ArgumentParser(description="PowerWiki 全站体检")
    ap.add_argument("--build", action="store_true", help="先运行 build_site.py 再体检")
    ap.add_argument("--render", action="store_true", help="渲染复判状态栏明暗")
    ap.add_argument("--url", default="http://localhost:8137", help="--render 用的站点根 URL")
    ap.add_argument("--update-baseline", action="store_true",
                    help="显式重建已定级内容基线（仅在确实调整角色定级时使用）")
    args = ap.parse_args()

    if args.build:
        print("=== 重建 ===")
        cp = subprocess.run([sys.executable, "build_site.py"], capture_output=True, text=True)
        for line in cp.stdout.splitlines():
            if "[dock]" in line or "[WARN]" in line or "[OK]" in line:
                print("  " + line)
        if cp.returncode != 0:
            print("  构建失败：", cp.stderr[-500:])
            return 1

    all_issues = []
    print("=== 1) 36 套产物静态体检 ===")
    rows, issues = check_products()
    print(f"  产物 {len(rows)} 套；JS 语法校验 "
          f"{'node 可用' if _has_node() else 'node 不可用(跳过)'}")
    print(f"  状态栏分布: {dict(__import__('collections').Counter(r['statusbar'] for r in rows))}")
    print(f"  dock 残留: {sum(r['dock_cls'] + r['dock_toggle'] for r in rows)} 处")
    all_issues += issues

    print("=== 2) 切换器链路 ===")
    cards, imgs, link_issues = check_links()
    print(f"  卡片链接 {cards} 个、缩略图 {imgs} 个；目标缺失 {len(link_issues)} 个")
    all_issues += link_issues

    print("=== 3) 登记表一致性 ===")
    n_eds, man_issues = check_manifest()
    print(f"  editions.json {n_eds} 条；不一致 {len(man_issues)} 项")
    all_issues += man_issues

    themes = dual_theme_skins()
    print(f"=== 4) 双主题皮肤（跟随系统深色模式，已知边界）: {len(themes)} 套 ===")
    print("  " + ", ".join(themes[:8]) + (" …" if len(themes) > 8 else ""))

    print("=== 5) 首页 Hero 亮色版（明暗双版同源）===")
    hero_issues, hero_size = check_hero_light()
    print(f"  双图资源与亮色样式分支{'齐全' if not hero_issues else '缺失'}；亮色底图 {hero_size} B")
    all_issues += hero_issues

    print("=== 6) 角色配图（缺图 / 破图 / 新配图比例）===")
    media_issues, with_img, ratio_checked = check_character_media()
    total_chars = len(json.loads((ROOT/"data/characters.json").read_text(encoding="utf-8"))["characters"])
    print(f"  已配图角色 {with_img}/{total_chars}；规范化新配图校验 {ratio_checked} 张；"
          f"缺图或比例异常 {len(media_issues)} 项")
    all_issues += media_issues

    print("=== 7) 已定级内容基线（规则/皮肤同步不得改动定级）===")
    base_issues, base_msg = check_grading_baseline(update=args.update_baseline)
    print(f"  {base_msg}；异常 {len(base_issues)} 项")
    all_issues += base_issues

    print("=== 7b) 升格默认页不得退回旧标准页（闪屏/旧默认回归）===")
    stale_issues = []
    _guards = {
        "character/yutu.html": ["pw-moon-nav"],
        "character/xuqing.html": ['data-pw-edition="xuqing-qingchuan"'],
        "character/shangdi.html": ['data-pw-edition="shangdi-jinian"'],
        "character/sunwukong.html": ['data-pw-edition="sunwukong-lingxiao"'],
        "character/zhigaowangzuo.html": ['data-pw-edition="zhigaowangzuo-yihuan"'],
        "materials.html": ['data-pw-edition="material-shatter"'],
        "rules.html": ['data-pw-edition="observatory"'],
        # 第二批 5 个（2026-11-28，产物基底 + base）：
        "character/pangu.html": ['data-pw-edition="pangu-hunyuan"'],
        "character/starkiller.html": ['data-pw-edition="starkiller-chixiao"'],
        "character/nvwa.html": ['data-pw-edition="nvwa-boshan"'],
        "character/shiva.html": ['data-pw-edition="shiva-yeke"'],
        "character/juxingzhihui.html": ['data-pw-edition="juxingzhihui-lingchun"'],
    }
    # 第三批 17 个（2026-11-29，与 build_site.py PROMOTED_PRODUCT_DEFAULTS 同源）
    _third = [
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
    for _s, _e in _third:
        _guards[f"character/{_s}.html"] = [f'data-pw-edition="{_e}"']
    for _rel, _markers in _guards.items():
        _f = Path(__file__).resolve().parent.parent / _rel
        if not _f.exists():
            stale_issues.append(f"{_rel} 缺失")
            continue
        _html = _f.read_text(encoding="utf-8")
        if "fade-on-load" in _html:
            stale_issues.append(f"{_rel} 含旧标准页特征 fade-on-load（会闪屏）")
        if not any(m in _html for m in _markers):
            stale_issues.append(f"{_rel} 缺升格皮肤标记 {_markers}")
        if re.search(r'data-edition-id="default"[^>]*>.*?pw-edition-name">默认<', _html, re.S):
            stale_issues.append(f"{_rel} 切换器里仍有旧「默认 / 建筑感栅格」卡未清除")
    # 皮肤页切换器一致性（2026-11-29）：覆盖上次遗漏的 skins/*/ 生成路径。
    # 第二/三批升格角色的所有页面（默认页+皮肤页）切换器须：无 default 卡、当前卡置顶、
    # 返回入口在。第一批走 DEFAULT_ALIAS 改名、default 卡是有意保留的唯一回默认入口，跳过。
    _strip_slugs = ["pangu", "starkiller", "nvwa", "shiva", "juxingzhihui"] + [s for s, _ in _third]
    _dock_pages = [f"character/{s}.html" for s in _strip_slugs]
    for _sp in sorted((Path(__file__).resolve().parent.parent / "skins").glob("*/character-*.html")):
        if _sp.stem[len("character-"):] in _strip_slugs:
            _dock_pages.append(str(_sp.relative_to(Path(__file__).resolve().parent.parent)))
    for _rel in _dock_pages:
        _f = Path(__file__).resolve().parent.parent / _rel
        if not _f.exists():
            continue
        _html = _f.read_text(encoding="utf-8")
        _cards = re.findall(r'<a class="(pw-edition-card[^"]*)"\s+data-edition-id="([^"]+)"', _html)
        if any(cid == "default" for _c, cid in _cards):
            stale_issues.append(f"{_rel} 切换器仍有冗余「默认」卡")
        if _cards and "is-current" not in _cards[0][0]:
            stale_issues.append(f"{_rel} 当前皮肤卡未置顶（首位={_cards[0][1]}）")
        if "pw-edition-home-btn" not in _html:
            stale_issues.append(f"{_rel} 切换器缺「返回角色档案」入口")
    print(f"  检查 {len(_guards)} 页 + {len(_dock_pages)} 切换器；异常 {len(stale_issues)} 项")
    all_issues += stale_issues

    if args.render:
        print("=== 8) 状态栏明暗渲染复判 ===")
        result, mism = render_statusbar(args.url.rstrip("/"))
        if result is None:
            print("  " + mism[0])
        else:
            print(f"  复判 {result['checked']} 套；不一致 {len(result['mismatches'])} 套；跳过 {len(result['skipped'])} 套")
            for x in result["mismatches"]:
                print("    ★ " + x)
            for x in result["skipped"]:
                print("    - " + x)
            all_issues += ["状态栏渲染复判：" + x for x in result["mismatches"]]

    print("\n=== 结论 ===")
    if all_issues:
        for x in all_issues:
            print("  ✗ " + x)
        print(f"  共 {len(all_issues)} 项待修")
        return 1
    print("  ✓ 全部通过，无已知隐患")
    return 0


if __name__ == "__main__":
    sys.exit(main())
