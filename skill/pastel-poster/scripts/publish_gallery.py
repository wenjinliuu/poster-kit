#!/usr/bin/env python3
"""把海报发布到海报图库（poster-gallery）：用图库模式生成 HTML，带上卡片信息，POST 到图库。

用法：
    GALLERY_KEY=<密钥> python3 publish_gallery.py spec.json [logos.json] [--slug googl-q3-2026] [--replace] [--dry-run]

    logos.json   fetch_logos.py 的输出（只用它的品牌色和来源；不给就现取一次）
    --slug       图库网址名（小写字母、数字、连字符）；不写用 spec.gallery.slug，再不行由图库按日期和标题生成
    --replace    覆盖同名海报（更新时用）。不写时撞上已有的 slug 会被拒绝，并显示那张是谁发的
    --dry-run    只生成 gallery.html 并检查，不发布

卡片信息写在 spec 的 gallery 字段里（都可以省略）：
    "gallery": {"title": "谷歌三季报：盘后重挫 −10.7%", "subtitle": "……", "tags": ["财报", "美股", "AI"],
                "hero": "−10.7%", "hero_label": "GOOGL 盘后", "hero_tone": "down", "date": "2026-10-29", "time": "05:46"}
    title 默认用 page_title 或标题三段；date / time 默认北京时间现在；market 跟 spec.updown。

环境变量：GALLERY_KEY（必需，向用户要），GALLERY_URL（默认 https://poster-gallery.wenjinuu.workers.dev）。
图库的发布规范：$GALLERY_URL/api/guide
"""
import datetime
import json
import os
import pathlib
import re
import sys
import tempfile
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

GALLERY_URL = os.environ.get("GALLERY_URL", "https://poster-gallery.wenjinuu.workers.dev").rstrip("/")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else default


def local_check(html):
    """发布前在本地先查一遍图库最常退回的几条（以图库返回为准）"""
    problems = []
    if len(html.encode()) > 400000:
        problems.append(f"HTML {len(html.encode()) // 1024} KB，超过图库上限 400 KB")
    if re.search(r"data:(?:image|font)/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]{4000,}", html):
        problems.append("还有超过约 3KB 的 base64 内嵌图片或字体")
    if "不构成投资建议" not in html:
        problems.append("页脚缺免责声明（不构成投资建议）")
    return problems


def meta_of(spec):
    g = spec.get("gallery") or {}
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
    title = g.get("title") or spec.get("page_title") or "".join(t for t in spec.get("title", []) if t)
    meta = {"title": title[:60], "date": g.get("date") or now.strftime("%Y-%m-%d"), "time": g.get("time") or now.strftime("%H:%M"),
            "market": "us" if spec.get("updown") == "us" else "cn"}
    for k in ("subtitle", "tags", "hero", "hero_label", "hero_tone", "slug"):
        if g.get(k):
            meta[k] = g[k]
    return meta


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--") and a not in (arg("--slug"),)]
    if not args:
        print(__doc__)
        sys.exit(1)
    spec_path = args[0]
    spec = json.load(open(spec_path, encoding="utf-8"))
    tmp = pathlib.Path(tempfile.mkdtemp())
    logos_path = args[1] if len(args) > 1 else None
    if not logos_path:  # 现取一次 logo（只为品牌色和来源；图库按代码自己取图）
        from fetch_logos import fetch_all
        logos, _ = fetch_all(list((spec.get("companies") or {}).keys()) + ([spec["brand"]["company"]] if (spec.get("brand") or {}).get("company") else []))
        logos_path = tmp / "logos.json"
        json.dump(logos, open(logos_path, "w", encoding="utf-8"))
    from build_poster import build
    out = build(spec_path, str(logos_path), str(tmp / "gallery.html"), gallery=True)
    html = pathlib.Path(out).read_text(encoding="utf-8")
    problems = local_check(html)
    for p in problems:
        print(f"  ✗ {p}")
    if "--dry-run" in sys.argv:
        dest = pathlib.Path("gallery.html")
        dest.write_text(html, encoding="utf-8")
        print(f"已生成 {dest}（{len(html.encode()) // 1024} KB），未发布")
        return
    if problems:
        sys.exit(2)
    key = os.environ.get("GALLERY_KEY")
    if not key:
        print("没有 GALLERY_KEY：向用户要图库的发布密钥，设成环境变量后再运行")
        sys.exit(1)
    body = {**meta_of(spec), "html": html}
    if arg("--slug"):
        body["slug"] = arg("--slug")
    if "--replace" in sys.argv:
        body["replace"] = True
    req = urllib.request.Request(f"{GALLERY_URL}/api/posters", data=json.dumps(body, ensure_ascii=False).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                          "User-Agent": "poster-kit/publish_gallery"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.loads(r.read())
        print(f"已发布：{res['url']}（第 {res['version']} 版）\n下载高清图：{res['download']}")
    except urllib.error.HTTPError as e:
        res = json.loads(e.read() or b"{}")
        print(f"图库退回（HTTP {e.code}）：")
        for err in res.get("errors") or [res.get("error", "")]:
            print(f"  ✗ {err}")
        if e.code == 409:
            print("  同一张海报要更新就加 --replace；是另一张就换个 --slug")
        sys.exit(2)


if __name__ == "__main__":
    main()
