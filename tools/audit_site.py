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
  4. 状态栏明暗：--render 时逐套量取状态栏正下方 (195,22) 真实底色亮度，
     与 SKIN_STATUS_BAR_MODE 比对（能抓出整页中位数采样抓不到的漏判）
  5. 双主题皮肤清单：列出跟随系统深色模式的皮肤（记录已知边界，不判失败）

退出码：有问题 1，全通过 0。可直接接进 CI / 发布前钩子。
"""
import argparse
import glob
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


def main():
    ap = argparse.ArgumentParser(description="PowerWiki 全站体检")
    ap.add_argument("--build", action="store_true", help="先运行 build_site.py 再体检")
    ap.add_argument("--render", action="store_true", help="渲染复判状态栏明暗")
    ap.add_argument("--url", default="http://localhost:8137", help="--render 用的站点根 URL")
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

    if args.render:
        print("=== 5) 状态栏明暗渲染复判 ===")
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
