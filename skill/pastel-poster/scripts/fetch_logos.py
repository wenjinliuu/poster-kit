#!/usr/bin/env python3
"""按 spec.json 里的公司列表取 logo，输出可直接内嵌的 logos.json。

用法：
    python3 fetch_logos.py spec.json logos.json [--tradingview]

公司键支持三种写法（覆盖 global-stock-logos 的 68 个市场）：
    交易所:代码     SZSE:300308  HKEX:700  NASDAQ:NVDA  TSE:7203  KRX:005930  TWSE:2330  LSE:AZN
    Yahoo 后缀      300308.SZ  688008.SH  0700.HK  7203.T  005930.KS  2330.TW  AZN.L  SAP.DE
    市场:代码       japan:7203  korea:005930（市场名即 logo 仓库的目录名）
只写代码也可以：6 位数字按首位判断沪/深，1–5 位数字为港股，字母为美股。

取用顺序（找到即停）：
    1. 手工修正版   本地或仓库里的 assets/logo-overrides/{交易所或市场}_{代码}.png|svg
    2. logo 仓库    默认 MrChartist/global-stock-logos（先走 jsDelivr，再走 raw.githubusercontent）
    3. TradingView  只有加 --tradingview 或设 POSTER_LOGO_TRADINGVIEW=1 才用（网页内部接口，少量按需）
    4. 都没有       不输出，海报里用首字徽章兜底

可用环境变量改来源（逗号分隔，按顺序尝试）：
    POSTER_LOGO_OVERRIDES   修正版位置，本地目录或 URL 前缀
    POSTER_LOGO_REPOS       logo 仓库，写成 owner/repo@分支，如 "me/global-stock-logos@main,MrChartist/global-stock-logos@main"

输出：{"SZSE:300308": {"src": "data:image/png;base64,...", "from": "repo"}, ...}
SVG 在装了 cairosvg 时转成 256px PNG，否则原样内嵌；海报页面不加载外部图片，外链会导致导出空白。
"""
import base64
import io
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
LOCAL_OVERRIDES = HERE.parent.parent.parent / "assets" / "logo-overrides"  # 在仓库里直接运行时
DEFAULT_OVERRIDES = "https://raw.githubusercontent.com/wenjinliuu/poster-kit/main/assets/logo-overrides"
DEFAULT_REPOS = "MrChartist/global-stock-logos@main"
REPO_URLS = ("https://cdn.jsdelivr.net/gh/{repo}@{ref}/logos/{dir}/{code}.{ext}",
             "https://raw.githubusercontent.com/{repo}/{ref}/logos/{dir}/{code}.{ext}")
TV_SCAN = "https://scanner.tradingview.com/{market}/scan"
TV_LOGO = "https://s3-symbol-logo.tradingview.com/{logoid}.svg"

# 交易所代码（TradingView 写法）→ logo 仓库目录
EXCHANGES = {
    "SSE": "china", "SZSE": "china", "HKEX": "hongkong",
    "NASDAQ": "us", "NYSE": "us", "AMEX": "us", "NYSEARCA": "us", "ARCA": "us", "OTC": "us", "CBOE": "us",
    "TSE": "japan", "TYO": "japan", "KRX": "korea", "KOSDAQ": "korea", "TWSE": "taiwan", "TPEX": "taiwan",
    "LSE": "uk", "LSIN": "uk", "AQUIS": "uk", "XETR": "germany", "FWB": "germany", "GETTEX": "germany", "TRADEGATE": "germany",
    "SIX": "switzerland", "BX": "switzerland", "MIL": "italy", "BME": "spain", "VIE": "austria", "GPW": "poland",
    "OMXSTO": "sweden", "NGM": "sweden", "OSL": "norway", "OMXCOP": "denmark", "OMXHEX": "finland", "OMXICE": "iceland",
    "ATHEX": "greece", "BET": "hungary", "PSECZ": "czech", "BVB": "romania", "BIST": "turkey", "RUS": "russia", "MOEX": "russia",
    "ASX": "australia", "NZX": "newzealand", "TSX": "canada", "TSXV": "canada", "NEO": "canada", "CSE": "canada",
    "NSE": "in", "BSE": "in", "SGX": "singapore", "SET": "thailand", "IDX": "indonesia", "MYX": "malaysia",
    "PSE": "philippines", "HOSE": "vietnam", "HNX": "vietnam", "UPCOM": "vietnam", "PSX": "pakistan", "DSEBD": "bangladesh",
    "BMFBOVESPA": "brazil", "B3": "brazil", "BMV": "mexico", "BIVA": "mexico", "BCBA": "argentina", "BCS": "chile",
    "BVC": "colombia", "BVL": "peru", "TADAWUL": "ksa", "ADX": "uae", "DFM": "uae", "QSE": "qatar", "KSE": "kuwait",
    "TASE": "israel", "EGX": "egypt", "JSE": "southafrica", "NSENG": "nigeria", "NSEKE": "kenya",
}
# Yahoo 代码后缀 → (logo 仓库目录, 交易所)
SUFFIXES = {
    "SS": ("china", "SSE"), "SH": ("china", "SSE"), "SZ": ("china", "SZSE"), "HK": ("hongkong", "HKEX"),
    "T": ("japan", "TSE"), "KS": ("korea", "KRX"), "KQ": ("korea", "KRX"), "TW": ("taiwan", "TWSE"), "TWO": ("taiwan", "TPEX"),
    "L": ("uk", "LSE"), "DE": ("germany", "XETR"), "F": ("germany", "FWB"), "PA": ("france", "EURONEXT"),
    "AS": ("netherlands", "EURONEXT"), "BR": ("belgium", "EURONEXT"), "LS": ("portugal", "EURONEXT"), "IR": ("ireland", "EURONEXT"),
    "MI": ("italy", "MIL"), "MC": ("spain", "BME"), "SW": ("switzerland", "SIX"), "VI": ("austria", "VIE"),
    "ST": ("sweden", "OMXSTO"), "OL": ("norway", "OSL"), "CO": ("denmark", "OMXCOP"), "HE": ("finland", "OMXHEX"),
    "IC": ("iceland", "OMXICE"), "WA": ("poland", "GPW"), "AT": ("greece", "ATHEX"), "IS": ("turkey", "BIST"),
    "AX": ("australia", "ASX"), "NZ": ("newzealand", "NZX"), "TO": ("canada", "TSX"), "V": ("canada", "TSXV"),
    "NS": ("in", "NSE"), "BO": ("in", "BSE"), "SI": ("singapore", "SGX"), "BK": ("thailand", "SET"),
    "JK": ("indonesia", "IDX"), "KL": ("malaysia", "MYX"), "PS": ("philippines", "PSE"), "SA": ("brazil", "BMFBOVESPA"),
    "MX": ("mexico", "BMV"), "BA": ("argentina", "BCBA"), "SN": ("chile", "BCS"), "SR": ("ksa", "TADAWUL"),
    "TA": ("israel", "TASE"), "JO": ("southafrica", "JSE"), "QA": ("qatar", "QSE"), "KW": ("kuwait", "KSE"), "CA": ("egypt", "EGX"),
}
# logo 仓库目录 → TradingView 扫描市场（只列常用的；其余市场不走 TradingView）
TV_MARKETS = {"china": "china", "hongkong": "hongkong", "us": "america", "japan": "japan", "korea": "korea",
              "taiwan": "taiwan", "uk": "uk", "germany": "germany", "in": "india"}
UA = {"User-Agent": "Mozilla/5.0 (poster-kit logo fetcher)"}
SIZE = 256


def http(url, data=None, timeout=15, tries=2):
    headers = dict(UA)
    if data is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(data).encode()
    for _ in range(tries):
        req = urllib.request.Request(url, data=data, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                if r.status == 200:
                    return r.read()
        except urllib.error.HTTPError as e:
            if e.code in (403, 404):
                return None  # 文件不存在，不必重试
        except Exception:
            pass
        time.sleep(0.8)
    return None


def normalize_key(raw):
    """把各种写法统一成 (logo 仓库目录, 交易所, 代码)。交易所未知时为 None。"""
    raw = raw.strip()
    up = raw.upper()
    if ":" in raw:
        ex, code = raw.split(":", 1)
        code = code.strip().upper()
        if ex.lower() in set(EXCHANGES.values()) | {m for m, _ in SUFFIXES.values()}:
            market, ex = ex.lower(), None  # 市场:代码
        else:
            ex = ex.strip().upper()
            market = EXCHANGES.get(ex, "us")
    elif re.fullmatch(r"[0-9A-Z\-]+\.[A-Z]{1,3}", up) and up.rsplit(".", 1)[1] in SUFFIXES:
        code, suf = up.rsplit(".", 1)
        market, ex = SUFFIXES[suf]
    else:
        code = up
        if re.fullmatch(r"\d{6}", code):
            market, ex = "china", ("SSE" if code[0] in "69" else "SZSE")
        elif re.fullmatch(r"\d{1,5}", code):
            market, ex = "hongkong", "HKEX"
        else:
            market, ex = "us", None  # 美股：仓库目录不区分交易所；TradingView 查询时几个都试
    if market == "hongkong":
        code = code.lstrip("0") or "0"
    return market, ex, code


def sources(env, default):
    return [s.strip() for s in os.environ.get(env, default).split(",") if s.strip()]


def from_overrides(market, ex, code):
    bases = sources("POSTER_LOGO_OVERRIDES", "")
    if not bases:
        bases = ([str(LOCAL_OVERRIDES)] if LOCAL_OVERRIDES.is_dir() else []) + [DEFAULT_OVERRIDES]
    names = [f"{p}_{code}" for p in dict.fromkeys(x for x in (ex, market) if x)]
    for base in bases:
        for name in names:
            for ext in ("png", "svg"):
                if re.match(r"https?://", base):
                    b = http(f"{base.rstrip('/')}/{name}.{ext}")
                else:
                    f = pathlib.Path(base) / f"{name}.{ext}"
                    b = f.read_bytes() if f.is_file() else None
                if b:
                    return b, ext
    return None


def from_repos(market, code):
    for spec in sources("POSTER_LOGO_REPOS", DEFAULT_REPOS):
        repo, _, ref = spec.partition("@")
        for ext in ("svg", "png"):
            for tpl in REPO_URLS:
                b = http(tpl.format(repo=repo, ref=ref or "main", dir=market, code=code, ext=ext))
                if b:
                    return b, ext
    return None


def from_tradingview(market, ex, code):
    tv = TV_MARKETS.get(market)
    if not tv:
        return None
    tickers = [f"{e}:{code}" for e in ("NASDAQ", "NYSE", "AMEX")] if market == "us" else [f"{ex}:{code}"] if ex else []
    if not tickers:
        return None
    raw = http(TV_SCAN.format(market=tv), {"symbols": {"tickers": tickers}, "columns": ["logoid"]})
    try:
        logoid = next(row["d"][0] for row in json.loads(raw or "{}").get("data", []) if row["d"] and row["d"][0])
    except (StopIteration, ValueError, KeyError):
        return None
    b = http(TV_LOGO.format(logoid=logoid))
    return (b, "svg") if b else None


def to_data_uri(content, ext):
    if ext == "svg":
        try:
            import cairosvg
            png = cairosvg.svg2png(bytestring=content, output_width=SIZE, output_height=SIZE)
            return "data:image/png;base64," + base64.b64encode(png).decode()
        except Exception:  # 没装 cairosvg 或这张 SVG 转不了：原样内嵌，浏览器同样能画
            return "data:image/svg+xml;base64," + base64.b64encode(content).decode()
    try:  # PNG：统一缩放到 SIZE
        from PIL import Image
        im = Image.open(io.BytesIO(content)).convert("RGBA")
        im.thumbnail((SIZE, SIZE))
        buf = io.BytesIO()
        im.save(buf, "PNG", optimize=True)
        content = buf.getvalue()
    except Exception:
        pass
    return "data:image/png;base64," + base64.b64encode(content).decode()


def analyze_logo(src):
    """看 logo 属于哪种底板、主色是什么，给圆形徽章的描边配色用（模板再吸附到海报自己的色板）：
    kind = light（白底 / 透明底）、color（整块彩色底）、dark（黑底 / 深色底）；
    bg = 彩色底的底色；mark = 底板以外最主要的彩色（白底彩色图形时就是图形颜色）；color = mark 或 bg（兼容旧字段）"""
    import colorsys
    import math
    from collections import Counter
    head, data = src.split(",", 1)
    raw = base64.b64decode(data)
    hx = lambda t: "#%02x%02x%02x" % t if t else None
    if "svg" in head:  # 没有转成 PNG 的 SVG：只能数 fill 里出现最多的彩色，当成白底彩色图形
        cols = re.findall(r"#([0-9a-fA-F]{6})\b", raw.decode("utf-8", "ignore"))
        sat = [c for c in cols if colorsys.rgb_to_hsv(*(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4)))[1] > .25]
        mark = "#" + max(set(sat), key=sat.count).lower() if sat else None
        return {"kind": "light", "mark": mark, "color": mark}
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert("RGBA").resize((96, 96))
    except Exception:
        return {}
    px, n = im.load(), 96
    c, edge, inner = (n - 1) / 2, [], []
    for y in range(n):
        for x in range(n):
            r, g, b, a = px[x, y]
            rgb = (255, 255, 255) if a < 40 else (r, g, b)
            d = math.hypot(x - c, y - c) / n
            if .40 <= d <= .48:  # 徽章是圆形裁切：看圆周附近的一圈判断底板
                edge.append(rgb)
            elif d < .36:
                inner.append(rgb)

    def cls(rgb):
        h, sv, v = colorsys.rgb_to_hsv(*(t / 255 for t in rgb))
        return "dark" if v < .3 else "light" if sv < .18 else "color"
    kind = Counter(cls(p) for p in edge).most_common(1)[0][0]
    bg = None
    if kind == "color":
        cs = [p for p in edge if cls(p) == "color"]
        bg = tuple(sum(t[i] for t in cs) // len(cs) for i in range(3))
    marks = [p for p in inner if cls(p) == "color" and (bg is None or sum(abs(p[i] - bg[i]) for i in range(3)) > 90)]
    mark = None
    if len(marks) > len(inner) * .03:
        buckets = {}
        for p in marks:
            buckets.setdefault(int(colorsys.rgb_to_hsv(*(t / 255 for t in p))[0] * 24), []).append(p)
        best = max(buckets.values(), key=len)
        mark = tuple(sum(t[i] for t in best) // len(best) for i in range(3))
    return {"kind": kind, "bg": hx(bg), "mark": hx(mark), "color": hx(mark) or hx(bg)}


def fetch_one(key, tradingview=False):
    market, ex, code = normalize_key(key)
    steps = [("override", lambda: from_overrides(market, ex, code)), ("repo", lambda: from_repos(market, code))]
    if tradingview:
        steps.append(("tradingview", lambda: from_tradingview(market, ex, code)))
    for origin, step in steps:
        hit = step()
        if hit:
            return to_data_uri(*hit), origin
    return None, "missing"


def fetch_all(keys, tradingview=False):
    out, report = {}, {}
    for key in keys:
        src, origin = fetch_one(key, tradingview)
        report[key] = origin
        if src:
            out[key] = {"src": src, "from": origin, **{k: v for k, v in analyze_logo(src).items() if v}}
    return out, report


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    tv = "--tradingview" in sys.argv or os.environ.get("POSTER_LOGO_TRADINGVIEW") == "1"
    spec = json.load(open(args[0], encoding="utf-8"))
    keys = list((spec.get("companies") or {}).keys())
    out, report = fetch_all(keys, tv)
    json.dump(out, open(args[1], "w", encoding="utf-8"))
    print(f"logo：{len(out)}/{len(keys)} 命中")
    for k, v in report.items():
        if v != "repo":
            print(f"  {k:<16} {v}")
    if "missing" in report.values() and not tv:
        print("  没取到的会用首字徽章；新上市的股票可以加 --tradingview 再试一次")


if __name__ == "__main__":
    main()
