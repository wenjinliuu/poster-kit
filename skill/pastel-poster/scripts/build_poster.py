#!/usr/bin/env python3
"""把 spec.json 和 logos.json 填进海报模板，生成海报网页，可选直接导出 PNG。

用法：
    python3 build_poster.py spec.json logos.json out.html [--png out.png] [--scale 2] [--standalone] [--no-embed-fonts] [--hosted]

    --png         生成网页后用无头浏览器按“下载高清图”同一套逻辑导出 PNG（需要 playwright）
    --scale       导出倍率，默认 2（1080 宽 → 2160 宽）
    --standalone  输出完整 HTML 文档（本地打开、自己部署用）；默认输出 Artifact 页面片段
    --no-embed-fonts  不内嵌字体，改为链接 Google Fonts
    --hosted      托管模式：给自己部署的海报站点（图库）用的完整 HTML —— 字体、logo 引用站点上的地址，不内嵌；
                  不内嵌 html2canvas、隐藏模板自带的标题栏和下载按钮（由站点提供下载）。地址可用环境变量改：
                  POSTER_HOSTED_FONTS（默认 /fonts.css，站点要提供 Noto Sans SC 和 Plus Jakarta Sans）、
                  POSTER_HOSTED_LOGO（默认 /logo/{key}，{key} 是 交易所:代码）

logos.json 不存在时所有公司用首字徽章。生成前会检查 spec，有错误时列出并退出。
页面完全自包含：html2canvas 内置，字体按海报实际用到的字从 Google Fonts 取子集内嵌（取不到就回退为链接）。
"""
import base64
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from validate_spec import validate  # noqa: E402

ASSETS = HERE.parent / "assets"
TEMPLATE = ASSETS / "poster-template.html"
HTML2CANVAS = ASSETS / "vendor" / "html2canvas.min.js"
FONT_CJK = "family=Noto+Sans+SC:wght@400;500;700;900"
FONT_NUM = "family=Plus+Jakarta+Sans:wght@500;700;800"  # 只有拉丁字符，数字和代码用
FONT_LINK = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{FONT_CJK}&{FONT_NUM}&display=swap">'
# 托管模式（--hosted）：字体和 logo 由站点提供，地址可配置
HOSTED_FONTS = os.environ.get("POSTER_HOSTED_FONTS", "/fonts.css")
HOSTED_LOGO = os.environ.get("POSTER_HOSTED_LOGO", "/logo/{key}")
# 请求 Google Fonts 时用现代浏览器的 UA，才会拿到 woff2
FONT_UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
BASE_CHARS = "".join(chr(c) for c in range(0x20, 0x7F)) + "，。：；、！？“”‘’（）《》【】·—…％×→↑↓±≈≤≥°￥€£"


def safe_json(obj):
    # 防止数据里的 </script> 提前结束脚本
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)
    elif isinstance(obj, (int, float)):
        yield str(obj)


def used_chars(spec, template):
    chars = set(BASE_CHARS)
    for s in strings(spec):
        chars.update(s)
    chars.update(re.findall(r"[⺀-鿿＀-￯]", template))  # 模板里写死的中文（“其他”“合计”等）
    return sorted(c for c in chars if c.isprintable())


def embed_fonts(chars):
    """按用到的字从 Google Fonts 取子集，转成 base64 内嵌的 @font-face。失败返回 None。"""
    latin = [c for c in chars if ord(c) < 0x2000]
    # 两个字体分开请求（text 里有某个字体完全没有的字时 Google Fonts 会返回 400）；中文分批，避免 URL 太长
    batches = [(FONT_NUM, latin)] + [(FONT_CJK, chars[i:i + 400]) for i in range(0, len(chars), 400)]
    faces = {}  # (字体, 文件) → 字重列表。子集是可变字体，几个字重共用一个文件，合并成一条 @font-face 只内嵌一次
    try:
        for family, part in batches:
            text = urllib.parse.quote("".join(part))
            url = f"https://fonts.googleapis.com/css2?{family}&text={text}&display=swap"
            with urllib.request.urlopen(urllib.request.Request(url, headers=FONT_UA), timeout=20) as r:
                css = r.read().decode()
            for block in re.findall(r"@font-face\s*{([^}]+)}", css):
                name = re.search(r"font-family:\s*'([^']+)'", block).group(1)
                weight = int(re.search(r"font-weight:\s*(\d+)", block).group(1))
                src = re.search(r"url\((https://[^)]+)\)", block).group(1)
                faces.setdefault((name, src), []).append(weight)
        rules = []
        for (name, src), weights in faces.items():
            with urllib.request.urlopen(urllib.request.Request(src, headers=FONT_UA), timeout=30) as r:
                data = base64.b64encode(r.read()).decode()
            rules.append(f"@font-face{{font-family:'{name}';font-style:normal;font-weight:{min(weights)} {max(weights)};"
                         f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2')}}")
    except Exception as e:
        print(f"字体内嵌失败（{e.__class__.__name__}），改为链接 Google Fonts")
        return None
    return "<style>/* 字体子集，由 build_poster.py 内嵌 */\n" + "\n".join(rules) + "</style>"


LUCIDE = "https://cdn.jsdelivr.net/npm/lucide-static@0.460.0/icons/{name}.svg"
ISO_OBJECTS = {"chip", "module", "rack", "coin", "globe", "battery", "building", "wafer", "db", "robot", "custom"}
UA = {"User-Agent": "poster-kit/1.0 (https://github.com/wenjinliuu/poster-kit)"}


def fetch(url, timeout=20, tries=3):
    import time
    for k in range(tries):  # 维基等站点偶尔超时或限流，稍等重试
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))


def icon_names(obj):
    """spec 里所有 icon 字段（不含等距物件名）"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "icon" and isinstance(v, str) and v not in ISO_OBJECTS:
                yield v
            else:
                yield from icon_names(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from icon_names(v)


def embed_icons(spec):
    """按名称从 Lucide 图标库取 SVG（https://lucide.dev/icons），原样交给模板上色"""
    icons = {}
    for name in sorted(set(icon_names(spec))):
        try:
            svg = fetch(LUCIDE.format(name=urllib.parse.quote(name))).decode()
            icons[name] = re.sub(r"<!--.*?-->", "", svg, flags=re.S).strip()
        except Exception:
            print(f"  提醒：图标“{name}”取不到（名称见 https://lucide.dev/icons），这处不显示图标")
    return icons


def clean_svg(svg):
    """去掉 SVG 里的脚本和事件属性，只保留图形"""
    svg = re.sub(r"<script.*?</script>", "", svg, flags=re.S | re.I)
    return re.sub(r"\son\w+\s*=\s*(\"[^\"]*\"|'[^']*')", "", svg)


HOSTED_EMBED_MAX = 2800  # 托管模式不内嵌超过约 3KB 的 base64 图片（站点通常不收大内嵌；SVG 改成文本形式内嵌）
HOSTED_LOGO_FROM = {"override", "repo"}  # 站点的 logo 代理一般只能从这两处取；TradingView 来的去掉，显示首字


def hosted_data_uri(uri):
    """托管模式：SVG 的 data URI 改成文本形式（不是 base64）；大于约 3KB 的位图放弃"""
    if not uri or not uri.startswith("data:"):
        return uri
    head, data = uri.split(",", 1)
    if "svg" in head:
        raw = base64.b64decode(data).decode("utf-8", "ignore") if ";base64" in head else urllib.parse.unquote(data)
        return "data:image/svg+xml;utf8," + urllib.parse.quote(clean_svg(raw), safe="=:/;,.-_()")  # 引号、#、空格都转义（放在 src="..." 里）
    return uri if len(data) <= HOSTED_EMBED_MAX else None


def hosted_logos(logos):
    """托管模式：logo 改成站点的地址（POSTER_HOSTED_LOGO），保留品牌色；站点取不到的去掉，显示首字"""
    out, dropped = {}, []
    for key, v in logos.items():
        if v.get("from") in HOSTED_LOGO_FROM:
            out[key] = {"src": HOSTED_LOGO.format(key=urllib.parse.quote(key, safe=":")), "from": v["from"],
                        **{k: v[k] for k in ("kind", "bg", "mark", "color") if v.get(k)}}  # 底板类型和颜色留给描边配色
        else:
            dropped.append(key)
    if dropped:
        print(f"  提醒：这些 logo 来自 TradingView，托管模式下取不到，海报上显示首字：{'、'.join(dropped)}")
    return out


def to_data_uri(src, base):
    """brand.image / brand.svg：URL、本地文件或 SVG 文本 → data URI（海报不加载外部图片）"""
    if not src or src.startswith("data:"):
        return src
    if src.lstrip().startswith("<svg"):
        raw, mime = clean_svg(src).encode(), "image/svg+xml"
    else:
        raw = fetch(src) if re.match(r"https?://", src) else (base / src).read_bytes()
        mime = "image/svg+xml" if raw.lstrip()[:200].lower().find(b"<svg") >= 0 else "image/png"
        if mime == "image/svg+xml":
            raw = clean_svg(raw.decode("utf-8", "ignore")).encode()
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def build(spec_path, logos_path, out_path, standalone=False, embed=True, hosted=False):
    spec = json.load(open(spec_path, encoding="utf-8"))
    from fetch_prices import fill_prices
    for sym in fill_prices(spec):  # price 版块、带 symbol 的 sparks / line：按代码取行情
        print(f"  提醒：{sym} 的行情取不到")
    errors, warnings = validate(spec)
    for w in warnings:
        print(f"  提醒：{w}")
    if errors:
        print("spec 有错误，未生成：")
        for e in errors:
            print(f"  ✗ {e}")
        sys.exit(2)
    logos = json.load(open(logos_path, encoding="utf-8")) if logos_path and pathlib.Path(logos_path).exists() else {}
    brand = spec.get("brand") or {}
    for key in ("image", "svg"):
        try:
            brand[key] = to_data_uri(brand.get(key), pathlib.Path(spec_path).resolve().parent)
            if hosted and brand.get(key):
                brand[key] = hosted_data_uri(brand[key])
                if not brand[key]:
                    print(f"  提醒：brand.{key} 是较大的位图，托管模式不内嵌大图，改用文字字标或圆形 logo")
                    brand.pop(key)
        except Exception as e:
            print(f"  提醒：brand.{key} 取不到（{e.__class__.__name__}），改用文字字标或圆形 logo")
            brand.pop(key, None)
    icons = embed_icons(spec)
    html = TEMPLATE.read_text(encoding="utf-8")
    title = spec.get("page_title") or " ".join(t for t in spec.get("title", []) if t) or "海报"
    title = title.replace("<", "").replace(">", "")[:40]
    if hosted:
        # 托管模式：字体、logo 用站点的，html2canvas 由站点的下载按钮按需加载，模板自带的标题栏和下载按钮隐藏
        logos = hosted_logos(logos)
        fonts = f'<link rel="stylesheet" href="{HOSTED_FONTS}">'
        html = html.replace("<!--__FONTS__-->", fonts + "<style>.page-h,.ver-h{display:none!important}</style>")
        html = html.replace("<!--__HTML2CANVAS__-->", "")
        standalone = True
    else:
        fonts = (embed and embed_fonts(used_chars(spec, html))) or FONT_LINK
        html = html.replace("<!--__FONTS__-->", fonts)
        html = html.replace("<!--__HTML2CANVAS__-->", "<script>" + HTML2CANVAS.read_text(encoding="utf-8") + "</script>")
    html = html.replace("__PAGE_TITLE__", title)
    html = html.replace("/*__SPEC__*/null", safe_json(spec))
    html = html.replace("/*__LOGOS__*/{}", safe_json(logos))
    html = html.replace("/*__ICONS__*/{}", safe_json(icons))
    if standalone:
        html = wrap(html)
    pathlib.Path(out_path).write_text(html, encoding="utf-8")
    print(f"已生成 {out_path}（{len(html) // 1024} KB，logo {len(logos)} 个，图标 {len(icons)} 个，"
          f"字体{'用站点的' if hosted else '内嵌' if fonts != FONT_LINK else '外链'}{'，托管模式' if hosted else ''}）")
    return out_path


def wrap(fragment):
    """Artifact 页面片段 → 完整 HTML 文档"""
    if fragment.lstrip().lower().startswith("<!doctype"):
        return fragment
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1"></head><body>'
            + fragment + "</body></html>")


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv and sys.argv.index(name) + 1 < len(sys.argv) else default


if __name__ == "__main__":
    opts_with_value = {"--png", "--preview", "--scale"}
    args, skip = [], False
    for a in sys.argv[1:]:
        if skip:
            skip = False
        elif a in opts_with_value:
            skip = True
        elif not a.startswith("--"):
            args.append(a)
    if len(args) < 3:
        print(__doc__)
        sys.exit(1)
    out = build(*args[:3], standalone="--standalone" in sys.argv, embed="--no-embed-fonts" not in sys.argv, hosted="--hosted" in sys.argv)
    png = arg("--png") or arg("--preview")  # --preview 是旧写法
    if png:
        from render_png import render
        render(out, png, scale=float(arg("--scale", 2)))
