#!/usr/bin/env python3
"""验收“下载高清图”：手机窄屏下导出的 PNG 不能被截断。

用法：
    python3 test_export.py [spec.json ...] [--out 输出目录]

不给 spec 时用 examples/ 里的全部示例。每个示例生成一页 HTML，用无头浏览器以手机视口（390×844）打开，
执行和按钮完全相同的导出逻辑（模板里的 window.__renderPoster），检查：
  1. PNG 宽 = 1080 × 倍率，高 = 海报 scrollHeight × 倍率（误差 ≤ 2px），且不超过 1680 万像素（倍率默认 2，海报很长时自动降低）
  2. 页脚最底部 40px 的那一段在 PNG 里能看到文字（有深色像素）
两种场景各跑一遍：字体内嵌（默认生成方式）；不内嵌且拦截 Google Fonts（字体回退到更宽的系统字体，海报会更高）。
导出的 PNG 存到输出目录，方便人工看一眼。需要 playwright（pip install playwright）和 Pillow；可用 CHROMIUM_PATH 指定浏览器。
"""
import io
import base64
import json
import pathlib
import sys
import tempfile

from PIL import Image
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_poster import build  # noqa: E402
from render_png import launch  # noqa: E402

SCALE = 2
VIEWPORT = {"width": 390, "height": 844}

EXPORT_JS = """async () => {
  const p = document.querySelector('.frame > .poster');
  const foot = p.querySelector('.p-foot');
  // 和按钮一样的导出逻辑
  const { canvas, height, scale } = await window.__renderPoster(p, %d);
  // 对照：旧写法（在页面里被缩放、被外框裁剪的节点上直接截图），只用来展示修复前的问题
  const prev = p.style.transform; p.style.transform = 'none';
  let old; try { old = await html2canvas(p, { scale: %d, backgroundColor: '#ffffff', useCORS: true, windowWidth: 1200, logging: false }); }
  finally { p.style.transform = prev; }
  return { png: canvas.toDataURL('image/png'), w: canvas.width, h: canvas.height, scrollHeight: height, scale,
           footTop: foot.offsetTop, footBottom: foot.offsetTop + foot.offsetHeight, oldH: old.height, oldPng: old.toDataURL('image/png'),
           fonts: [...document.fonts].filter(f => f.status === 'loaded').map(f => f.family).slice(0, 5) };
}""" % (SCALE, SCALE)


def dark_pixels(img, top, bottom):
    """统计 [top, bottom) 行里的深色像素（文字），用来判断页脚有没有被画出来"""
    top, bottom = max(0, int(top)), min(img.height, int(bottom))
    if bottom <= top:
        return 0
    region = img.crop((0, top, img.width, bottom)).convert("L")
    data = region.get_flattened_data() if hasattr(region, "get_flattened_data") else region.getdata()
    return sum(1 for v in data if v < 150)


def run_case(browser, html, block_fonts, out_png):
    ctx = browser.new_context(viewport=VIEWPORT, is_mobile=True, has_touch=True, device_scale_factor=1)
    if block_fonts:
        ctx.route("**/fonts.googleapis.com/**", lambda r: r.abort())
        ctx.route("**/fonts.gstatic.com/**", lambda r: r.abort())
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(html.as_uri(), wait_until="domcontentloaded")
    page.wait_for_function("() => window.html2canvas && window.__renderPoster", timeout=30000)
    page.wait_for_timeout(1500)
    r = page.evaluate(EXPORT_JS)
    ctx.close()
    png = base64.b64decode(r["png"].split(",", 1)[1])
    out_png.write_bytes(png)
    img = Image.open(io.BytesIO(png))
    s = r["scale"]  # 海报很长时会自动降低倍率（iPhone 画布约 1670 万像素封顶）
    want_w, want_h = round(1080 * s), round(r["scrollHeight"] * s)
    foot_dark = dark_pixels(img, (r["footBottom"] - 40) * s, r["footBottom"] * s)
    old = Image.open(io.BytesIO(base64.b64decode(r["oldPng"].split(",", 1)[1])))
    old_dark = dark_pixels(old, (r["footBottom"] - 40) * SCALE, r["footBottom"] * SCALE)
    ok = abs(img.width - want_w) <= 2 and abs(img.height - want_h) <= 2 and img.width * img.height <= 16.8e6 and foot_dark > 50 and not errors
    return ok, {
        "场景": "字体加载失败" if block_fonts else "字体内嵌",
        "PNG": f"{img.width}×{img.height}", "海报高": r["scrollHeight"], "倍率": round(s, 3), "应为": f"{want_w}×{want_h}",
        "页脚底部40px深色像素": foot_dark, "修复前旧写法": f"高 {r['oldH']}，页脚深色像素 {old_dark}", "已加载字体": r["fonts"], "页面报错": errors,
        "文件": str(out_png),
    }


def main():
    args = sys.argv[1:]
    out_dir = pathlib.Path(args[args.index("--out") + 1]) if "--out" in args else pathlib.Path(tempfile.mkdtemp(prefix="export-test-"))
    specs = [pathlib.Path(a) for a in args if a.endswith(".json")] or sorted((HERE.parent / "examples").glob("*.json"))
    out_dir.mkdir(parents=True, exist_ok=True)
    all_ok = True
    with sync_playwright() as p:
        browser = launch(p)
        for spec in specs:
            for block in (False, True):
                # 模板是 artifact 页面片段，没有 <html> 外壳；standalone 包一层，和发布后的页面一致
                page = out_dir / f"{spec.stem}{'-nofont' if block else ''}.html"
                build(spec, None, page, standalone=True, embed=not block)
                ok, info = run_case(browser, page.resolve(), block, out_dir / f"{spec.stem}{'-nofont' if block else ''}.png")
                all_ok &= ok
                print(("✓" if ok else "✗"), spec.stem, json.dumps(info, ensure_ascii=False))
        browser.close()
    print(f"\n导出的图片在 {out_dir}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
