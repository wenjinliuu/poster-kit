#!/usr/bin/env python3
"""在维基共享资源（Wikimedia Commons）找公司官方字标 SVG，给 spec 的 brand.image 用。

用法：
    python3 find_wordmark.py "SK hynix"
    python3 find_wordmark.py "Meta Platforms" --limit 8
    python3 find_wordmark.py --file "SK_Hynix.svg"     # 已知文件名时直接给出下载地址

列出文件名、尺寸和直接下载地址。挑一个正式的横版字标（文件名常含 logo / wordmark），
把地址写进 spec：  "brand": {"image": "https://upload.wikimedia.org/...svg", ...}
build_poster.py 会下载并内嵌。找不到合适的，就用 brand.wordmark 按品牌色重建文字字标（见 references/logos.md）。
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "poster-kit/1.0 (https://github.com/wenjinliuu/poster-kit)"}


def api(params):
    url = API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    for wait in (0, 3, 8):  # 维基共享资源偶尔限流（429），稍等再试
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
    raise SystemExit("维基共享资源暂时限流，稍后再试，或改用 brand.wordmark 文字重建")


def search(name, limit=6):
    hits = api({"action": "query", "list": "search", "srsearch": f"{name} logo filetype:svg", "srnamespace": 6, "srlimit": limit})
    titles = [h["title"] for h in hits.get("query", {}).get("search", [])]
    if not titles:
        return []
    info = api({"action": "query", "titles": "|".join(titles), "prop": "imageinfo", "iiprop": "url|size|mime"})
    out = []
    for page in info.get("query", {}).get("pages", {}).values():
        ii = (page.get("imageinfo") or [{}])[0]
        if ii.get("mime") == "image/svg+xml":
            out.append((page["title"], ii.get("width"), ii.get("height"), ii.get("url")))
    return out


def file_url(name):
    """已知文件名（如 SK_Hynix.svg）时直接算出下载地址，不经过搜索接口"""
    import hashlib
    name = name.replace(" ", "_").removeprefix("File:")
    h = hashlib.md5(name.encode()).hexdigest()
    return f"https://upload.wikimedia.org/wikipedia/commons/{h[0]}/{h[:2]}/{urllib.parse.quote(name)}"


if __name__ == "__main__":
    if "--file" in sys.argv:
        print(file_url(sys.argv[sys.argv.index("--file") + 1]))
        sys.exit(0)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else 6
    rows = search(args[0], limit)
    if not rows:
        print("没找到 SVG 字标，改用 brand.wordmark 文字重建")
    for title, w, h, url in rows:
        print(f"{title}  {w}×{h}\n  {url}")
