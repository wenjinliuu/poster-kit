#!/usr/bin/env python3
"""取股价日线（开高低收量），给走势图用。先雅虎财经，港股、A 股取不到再用腾讯行情。

用法：
    python3 fetch_prices.py NASDAQ:NVDA 300308.SZ HKEX:700 [--range 1y] [--interval 1d]

代码写法和 fetch_logos.py 一样（交易所:代码、Yahoo 后缀、市场:代码）。打印最新价、区间涨跌、最高最低。
build_poster.py 生成时会自动给 price 版块、带 symbol 的 sparks / line 取数，一般不用单独跑。
range：1mo 3mo 6mo 1y 2y 5y ytd max；interval：1d 1wk 1mo。只按需少量请求，不要批量抓取。
"""
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from fetch_logos import normalize_key  # noqa: E402

YAHOO = "https://query1.finance.yahoo.com/v8/finance/chart/{sym}?range={range}&interval={interval}"
TENCENT = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?param={sym},day,,,{n},qfq"
UA = {"User-Agent": "Mozilla/5.0"}
# logo 仓库目录 → Yahoo 后缀（交易所能区分时优先按交易所）
MARKET_SUFFIX = {
    "hongkong": "HK", "japan": "T", "korea": "KS", "taiwan": "TW", "uk": "L", "germany": "DE", "france": "PA",
    "netherlands": "AS", "belgium": "BR", "italy": "MI", "spain": "MC", "switzerland": "SW", "sweden": "ST",
    "norway": "OL", "denmark": "CO", "finland": "HE", "australia": "AX", "canada": "TO", "in": "NS",
    "singapore": "SI", "thailand": "BK", "indonesia": "JK", "malaysia": "KL", "brazil": "SA", "mexico": "MX",
    "austria": "VI", "portugal": "LS", "ireland": "IR", "poland": "WA", "greece": "AT", "turkey": "IS",
    "israel": "TA", "southafrica": "JO", "newzealand": "NZ", "ksa": "SR",
}
EXCHANGE_SUFFIX = {"SSE": "SS", "SZSE": "SZ", "TPEX": "TWO", "KOSDAQ": "KQ", "TSXV": "V", "BSE": "BO"}
DAYS = {"1mo": 23, "3mo": 66, "6mo": 130, "1y": 260, "2y": 520, "5y": 1300, "ytd": 260, "max": 2000}


def yahoo_symbol(key):
    market, ex, code = normalize_key(key)
    if market == "us":
        return code.replace(".", "-")
    if market == "hongkong":
        return code.zfill(4) + ".HK"
    suf = EXCHANGE_SUFFIX.get(ex) or MARKET_SUFFIX.get(market)
    return f"{code}.{suf}" if suf else code


def get_json(url):
    for wait in (0, 1.5):
        time.sleep(wait)
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
                return json.load(r)
        except Exception:
            pass
    return None


def from_yahoo(sym, rng, interval):
    d = get_json(YAHOO.format(sym=urllib.parse.quote(sym), range=rng, interval=interval))
    try:
        x = d["chart"]["result"][0]
        q = x["indicators"]["quote"][0]
        rows = []
        for i, t in enumerate(x.get("timestamp") or []):
            o, h, l, c, v = (q[k][i] for k in ("open", "high", "low", "close", "volume"))
            if c is None:
                continue
            day = datetime.fromtimestamp(t + (x["meta"].get("gmtoffset") or 0), timezone.utc).strftime("%Y-%m-%d")
            rows.append([day, *(round(z, 4) if z is not None else round(c, 4) for z in (o, h, l, c)), int(v or 0)])
        return {"symbol": sym, "currency": x["meta"].get("currency"), "name": x["meta"].get("shortName") or x["meta"].get("longName"), "rows": rows, "source": "Yahoo Finance"}
    except Exception:
        return None


def from_tencent(key, rng):
    market, ex, code = normalize_key(key)
    tsym = "hk" + code.zfill(5) if market == "hongkong" else ("sh" if ex == "SSE" else "sz") + code if market == "china" else None
    if not tsym:
        return None
    d = get_json(TENCENT.format(sym=tsym, n=DAYS.get(rng, 260)))
    try:
        x = d["data"][tsym]
        raw = x.get("qfqday") or x.get("day") or []
        rows = [[r[0], float(r[1]), float(r[3]), float(r[4]), float(r[2]), int(float(r[5]))] for r in raw]  # 腾讯顺序：日期 开 收 高 低 量
        return {"symbol": tsym, "currency": "HKD" if market == "hongkong" else "CNY", "rows": rows, "source": "腾讯行情"}
    except Exception:
        return None


def get_prices(key, rng="1y", interval="1d"):
    """返回 {symbol, currency, source, rows: [[日期, 开, 高, 低, 收, 量], ...]}，取不到返回 None"""
    sym = key if "." in key and ":" not in key else yahoo_symbol(key)
    r = from_yahoo(sym, rng, interval)
    if (not r or len(r["rows"]) < 5) and interval == "1d":
        r = from_tencent(key, rng) or r
    return r if r and r["rows"] else None


def fill_prices(spec):
    """build_poster 调用：给没有 data 的 price 版块、带 symbol 的 sparks 项和 line 系列取数，返回取不到的代码"""
    missing, cache = [], {}

    def load(sym, rng):
        if (sym, rng) not in cache:
            cache[sym, rng] = get_prices(sym, rng)
        return cache[sym, rng]

    def walk(sections):
        for s in sections:
            t = s.get("type")
            if t in ("group", "row"):
                walk(s.get("sections", []))
            elif t == "price" and not s.get("data"):
                sym = s.get("symbol") or s.get("company")
                r = load(sym, s.get("range", "1y"))
                if r:
                    s["data"] = r["rows"]
                    s.setdefault("currency", r["currency"])
                    s.setdefault("source", r["source"])
                else:
                    missing.append(sym)
            elif t == "sparks":
                for it in s["items"]:
                    if it.get("symbol") and not it.get("values"):
                        r = load(it["symbol"], s.get("range", "3mo"))
                        rows = r["rows"] if r else []
                        it["values"] = [round(x[4], 3) for x in rows[:: max(1, len(rows) // 40)] + rows[-1:]] if rows else [0, 0]
                        if not r:
                            missing.append(it["symbol"])
            elif t == "line" and any(q.get("symbol") for q in s.get("series", [])):
                rng = s.get("range", "1y")
                data = {q["symbol"]: (load(q["symbol"], rng) or {}).get("rows", []) for q in s["series"] if q.get("symbol")}
                missing.extend(k for k, v in data.items() if not v)
                days = sorted(set.intersection(*[{r[0] for r in v} for v in data.values() if v])) if any(data.values()) else []
                step = max(1, len(days) // 60)
                days = days[::step] + ([days[-1]] if days and days[::step][-1] != days[-1] else [])
                s["x"] = [d[2:7].replace("-", "/") if len(days) > 120 else d[5:].replace("-", "/") for d in days]
                for q in s["series"]:
                    rows = {r[0]: r[4] for r in data.get(q.get("symbol"), [])}
                    vals = [rows.get(d) for d in days]
                    if s.get("normalize", True) and vals and vals[0]:  # 默认换算成相对起点的涨跌幅，几只股票才能放一起比
                        vals = [round((v / vals[0] - 1) * 100, 2) if v else None for v in vals]
                    q["values"] = vals
                if s.get("normalize", True):
                    s.setdefault("unit", "%")
    walk(spec.get("sections", []))
    return missing


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(1)
    rng = sys.argv[sys.argv.index("--range") + 1] if "--range" in sys.argv else "1y"
    itv = sys.argv[sys.argv.index("--interval") + 1] if "--interval" in sys.argv else "1d"
    args = [a for a in args if a not in (rng, itv)]
    for key in args:
        r = get_prices(key, rng, itv)
        if not r:
            print(f"{key}：取不到")
            continue
        rows = r["rows"]
        hi, lo = max(rows, key=lambda x: x[2]), min(rows, key=lambda x: x[3])
        print(f"{key} → {r['symbol']}（{r['source']}，{r['currency']}）{rows[0][0]} ~ {rows[-1][0]} 共 {len(rows)} 根")
        print(f"  最新 {rows[-1][4]}  区间涨跌 {(rows[-1][4] / rows[0][4] - 1) * 100:+.2f}%  最高 {hi[2]}（{hi[0]}）  最低 {lo[3]}（{lo[0]}）")
