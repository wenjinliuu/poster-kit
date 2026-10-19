#!/usr/bin/env python3
"""按 spec.json 里的公司列表取 logo，输出可直接内嵌的 logos.json。

用法：
    python3 fetch_logos.py spec.json logos.json

公司键写成 "交易所:代码"，例如 "SZSE:300308"、"HKEX:700"、"NASDAQ:NVDA"。
只写代码也可以（"300308"、"00700"、"NVDA"），脚本会自动推断交易所。

取用顺序（找到即停）：
    1. poster-kit 仓库里的手工修正版   assets/logo-overrides/{交易所}_{代码}.svg|png
    2. 自己的 fork（每日同步上游）       wenjinliuu/global-stock-logos
    3. TradingView 源头                  行情扫描接口查 logoid → 官方 logo 地址
    4. 上游仓库                          MrChartist/global-stock-logos
    5. 都没有 → 不输出，海报里用首字徽章兜底

输出：{"SZSE:300308": {"src": "data:image/png;base64,...", "from": "fork"}, ...}
所有图片都转成 256px PNG 内嵌，因为海报页面不允许加载外部图片。
"""
import base64
import io
import json
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request

OVERRIDES = "https://raw.githubusercontent.com/wenjinliuu/poster-kit/main/assets/logo-overrides/{name}"
FORK = "https://raw.githubusercontent.com/wenjinliuu/global-stock-logos/main/logos/{dir}/{code}.{ext}"
UPSTREAM = "https://raw.githubusercontent.com/MrChartist/global-stock-logos/main/logos/{dir}/{code}.{ext}"
TV_SCAN = "https://scanner.tradingview.com/{market}/scan"
TV_LOGO = "https://s3-symbol-logo.tradingview.com/{logoid}.svg"

# 交易所 → (logo 仓库目录, TradingView 扫描市场)
EXCHANGES = {
    "SSE": ("china", "china"), "SZSE": ("china", "china"),
    "HKEX": ("hongkong", "hongkong"),
    "NASDAQ": ("us", "america"), "NYSE": ("us", "america"), "AMEX": ("us", "america"),
}
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
            if e.code == 404:
                return None  # 文件不存在，不必重试
        except Exception:
            pass
        time.sleep(0.8)
    return None


def normalize_key(raw):
    """把用户写法统一成 (交易所, 代码)。"""
    raw = raw.strip().upper()
    if ":" in raw:
        ex, code = raw.split(":", 1)
    else:
        code = raw
        if re.fullmatch(r"\d{6}", code):
            ex = "SSE" if code[0] in "69" else "SZSE"
        elif re.fullmatch(r"\d{1,5}", code):
            ex = "HKEX"
        else:
            ex = "NASDAQ"  # 美股：仓库目录不区分交易所；TV 查询时两个都试
    if ex == "HKEX":
        code = code.lstrip("0") or "0"
    return ex, code


def tv_logoid(ex, code):
    market = EXCHANGES.get(ex, (None, None))[1]
    if not market:
        return None
    tickers = [f"{ex}:{code}"]
    if market == "america":
        tickers = [f"{e}:{code}" for e in ("NASDAQ", "NYSE", "AMEX")]
    body = {"symbols": {"tickers": tickers}, "columns": ["logoid"]}
    raw = http(TV_SCAN.format(market=market), body)
    if not raw:
        return None
    try:
        for row in json.loads(raw).get("data", []):
            if row["d"] and row["d"][0]:
                return row["d"][0]
    except Exception:
        return None
    return None


_cairo = None


def svg_to_png(svg_bytes):
    global _cairo
    if _cairo is None:
        try:
            import cairosvg  # noqa
            _cairo = cairosvg
        except ImportError:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", "cairosvg"],
                           capture_output=True)
            try:
                import cairosvg  # noqa
                _cairo = cairosvg
            except ImportError:
                _cairo = False
    if not _cairo:
        return None
    try:
        return _cairo.svg2png(bytestring=svg_bytes, output_width=SIZE, output_height=SIZE)
    except Exception:
        return None


def to_data_uri(content, ext):
    if ext == "svg":
        png = svg_to_png(content)
        if png:
            return "data:image/png;base64," + base64.b64encode(png).decode()
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


def fetch_one(ex, code):
    repo_dir = EXCHANGES.get(ex, ("us", None))[0]
    for ext in ("png", "svg"):
        b = http(OVERRIDES.format(name=f"{ex}_{code}.{ext}"))
        if b:
            return to_data_uri(b, ext), "override"
    for ext in ("svg", "png"):
        b = http(FORK.format(dir=repo_dir, code=code, ext=ext))
        if b:
            return to_data_uri(b, ext), "fork"
    logoid = tv_logoid(ex, code)
    if logoid:
        b = http(TV_LOGO.format(logoid=logoid))
        if b:
            return to_data_uri(b, "svg"), "tradingview"
    for ext in ("svg", "png"):
        b = http(UPSTREAM.format(dir=repo_dir, code=code, ext=ext))
        if b:
            return to_data_uri(b, ext), "upstream"
    return None, "missing"


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    keys = list((spec.get("companies") or {}).keys())
    out, report = {}, {}
    for key in keys:
        ex, code = normalize_key(key)
        src, origin = fetch_one(ex, code)
        report[key] = origin
        if src:
            out[key] = {"src": src, "from": origin}
    json.dump(out, open(sys.argv[2], "w", encoding="utf-8"))
    hit = sum(1 for v in report.values() if v != "missing")
    print(f"logo：{hit}/{len(keys)} 命中")
    for k, v in report.items():
        if v != "fork":
            print(f"  {k:<16} {v}")


if __name__ == "__main__":
    main()
