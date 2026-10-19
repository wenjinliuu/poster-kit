#!/usr/bin/env python3
"""把 spec.json 和 logos.json 填进海报模板，生成可发布的 HTML 页面。

用法：
    python3 build_poster.py spec.json logos.json out.html [--preview preview.png]

--preview 会用无头浏览器把第一个版本截成 PNG，方便发布前检查一次版式
（需要 playwright；没有就跳过，不影响生成）。
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = HERE.parent / "assets" / "poster-template.html"


def safe_json(obj):
    # 防止数据里的 </script> 提前结束脚本
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def build(spec_path, logos_path, out_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    logos = json.load(open(logos_path, encoding="utf-8")) if logos_path and pathlib.Path(logos_path).exists() else {}
    html = TEMPLATE.read_text(encoding="utf-8")
    title = spec.get("page_title") or " ".join(t for t in spec.get("title", []) if t) or "海报"
    title = title.replace("<", "").replace(">", "")[:40]
    html = html.replace("__PAGE_TITLE__", title)
    html = html.replace("/*__SPEC__*/null", safe_json(spec))
    html = html.replace("/*__LOGOS__*/{}", safe_json(logos))
    pathlib.Path(out_path).write_text(html, encoding="utf-8")
    print(f"已生成 {out_path}（{len(html) // 1024} KB，logo {len(logos)} 个）")


def preview(out_html, png):
    try:
        import asyncio
        from playwright.async_api import async_playwright
    except ImportError:
        print("未安装 playwright，跳过预览")
        return
    wrapped = pathlib.Path(out_html).with_suffix(".preview.html")
    wrapped.write_text('<!doctype html><html><head><meta charset="utf-8"></head><body>'
                       + pathlib.Path(out_html).read_text(encoding="utf-8") + "</body></html>", encoding="utf-8")

    async def run():
        async with async_playwright() as p:
            b = await p.chromium.launch()
            pg = await b.new_page(viewport={"width": 1200, "height": 900})
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            await pg.goto("file://" + str(wrapped.resolve()))
            await pg.wait_for_timeout(1200)
            el = await pg.query_selector(".poster")
            await pg.evaluate("e => e.style.transform = 'none'", el)
            await el.screenshot(path=png)
            await b.close()
            print(f"预览图 {png}" + (f"；页面报错：{errors}" if errors else ""))
    asyncio.run(run())
    wrapped.unlink(missing_ok=True)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        print(__doc__)
        sys.exit(1)
    build(*args[:3])
    if "--preview" in sys.argv:
        i = sys.argv.index("--preview")
        preview(args[2], sys.argv[i + 1] if i + 1 < len(sys.argv) else "preview.png")
