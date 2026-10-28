#!/usr/bin/env python3
"""把海报网页导出成 PNG：用无头浏览器打开页面，执行和“下载高清图”按钮完全相同的导出逻辑。

用法：
    python3 render_png.py poster.html out.png [--scale 2]

需要 playwright（pip install playwright && playwright install chromium）。
如果系统里已经有 Chromium，可以设 CHROMIUM_PATH 指向它，省去下载浏览器。
页面可以是 build_poster.py 输出的 Artifact 片段，也可以是 --standalone 的完整文档。
"""
import base64
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def launch(p):
    path = os.environ.get("CHROMIUM_PATH")
    return p.chromium.launch(executable_path=path) if path else p.chromium.launch()


def render(html_path, png_path, scale=2.0, viewport=None):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("未安装 playwright，无法导出 PNG：pip install playwright && playwright install chromium")
        return None
    from build_poster import wrap
    html = pathlib.Path(html_path).read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        page_file = pathlib.Path(tmp) / "page.html"
        page_file.write_text(wrap(html), encoding="utf-8")
        with sync_playwright() as p:
            browser = launch(p)
            page = browser.new_page(viewport=viewport or {"width": 1200, "height": 900})
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            page.goto(page_file.as_uri(), wait_until="domcontentloaded")
            page.wait_for_function("() => window.html2canvas && window.__renderPoster", timeout=30000)
            r = page.evaluate("""async (scale) => {
              const p = document.querySelector('.frame > .poster');
              const { canvas, height, scale: s } = await window.__renderPoster(p, scale);
              return { png: canvas.toDataURL('image/png'), w: canvas.width, h: canvas.height, height, scale: s };
            }""", scale)
            browser.close()
    pathlib.Path(png_path).write_bytes(base64.b64decode(r["png"].split(",", 1)[1]))
    print(f"已导出 {png_path}（{r['w']}×{r['h']}，倍率 {r['scale']:.2f}）" + (f"；页面报错：{errors}" if errors else ""))
    return r


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    s = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 2.0
    render(args[0], args[1], scale=s)
