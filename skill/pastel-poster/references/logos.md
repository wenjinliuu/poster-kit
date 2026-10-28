# logo 规则

## 取用顺序（`scripts/fetch_logos.py` 自动执行）

1. **手工修正版**：`assets/logo-overrides/{交易所}_{代码}.png|svg`（如 `SZSE_300308.png`、`HKEX_700.svg`），也可以用市场名命名（`japan_7203.svg`）。在仓库里运行时读本地目录，否则读 `wenjinliuu/poster-kit` 仓库里的同名目录。对某个 logo 不满意时放这里，优先级最高。
2. **logo 仓库**：[MrChartist/global-stock-logos](https://github.com/MrChartist/global-stock-logos)，覆盖 68 个市场、7.5 万家公司，每天更新。先走 jsDelivr CDN，再走 raw.githubusercontent。
3. **TradingView 源头**（可选）：加 `--tradingview` 或设 `POSTER_LOGO_TRADINGVIEW=1` 才启用。先用行情扫描接口按代码查 logoid，再取 SVG，用于 logo 仓库里还没有的新上市股票。这是 TradingView 网页内部接口，只按需少量调用，不要批量抓取。
4. **都没有**：不输出，模板自动画首字徽章（中文名取首字，否则取代码首字母）。

来源可以用环境变量改（逗号分隔，按顺序尝试）：

- `POSTER_LOGO_OVERRIDES`：修正版位置，本地目录或 URL 前缀。
- `POSTER_LOGO_REPOS`：logo 仓库，写成 `owner/repo@分支`。例如用自己的 fork 优先、上游兜底：`me/global-stock-logos@main,MrChartist/global-stock-logos@main`。

SVG 在装了 cairosvg 时统一转成 256px PNG，否则原样内嵌；全部以 base64 内嵌进页面。海报页面不允许加载外部图片，外链会导致导出空白。

## 代码写法

三种写法都可以，海报上显示的代码可以用 `code` 另写：

| 写法 | 例子 |
|---|---|
| `交易所:代码` | `SSE:600519` `SZSE:300308` `HKEX:700` `NASDAQ:NVDA` `NYSE:ANET` `TSE:7203` `KRX:005930` `TWSE:2330` `LSE:AZN` |
| Yahoo 后缀 | `600519.SS`（或 `.SH`）`300308.SZ` `0700.HK` `7203.T` `005930.KS` `2330.TW` `AZN.L` `SAP.DE` `MC.PA` `ASML.AS` |
| `市场:代码` | `japan:7203` `korea:005930`（市场名就是 logo 仓库 `logos/` 下的目录名） |

- 只写代码也能识别：6 位数字按首位判断沪/深（6、9 开头为上交所），1–5 位数字为港股，字母为美股。
- 港股不论写不写前导零都能取到；显示用的 `code` 建议写 5 位，如 `"00700"`。
- Yahoo 写法会原样显示后缀（`7203.T`），想只显示数字就写 `code`。

## 版权说明

logo 归各自公司所有。logo 仓库的数据主要来自 TradingView 公开 logo 服务和 Wikidata，仅适合识别用途（图表、研究、学习材料）；商用或大量使用前请自行确认相关条款。海报页脚必须保留“徽标仅用于识别，归各自所有者”。不要修改、重绘或仿画 logo。
