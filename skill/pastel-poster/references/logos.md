# logo 规则

## 取用顺序（`scripts/fetch_logos.py` 自动执行）

1. **手工修正版**：`wenjinliuu/poster-kit` 仓库的 `assets/logo-overrides/{交易所}_{代码}.png|svg`，例如 `SZSE_300308.png`、`HKEX_700.svg`。对某个 logo 不满意时放这里，优先级最高。
2. **自己的 fork**：`wenjinliuu/global-stock-logos`，每天自动同步上游，覆盖 A 股、港股、美股等 68 个市场。日常主力来源。
3. **TradingView 源头**：先用行情扫描接口按代码查 logoid，再从 TradingView 的 logo 地址取 SVG。用于 fork 里还没有的新上市股票。这是 TradingView 网页内部接口，只按需少量调用，不要批量抓取。
4. **上游仓库**：`MrChartist/global-stock-logos`，fork 同步出问题时的备份。
5. **都没有**：不输出，模板自动画首字徽章（中文名取首字，否则取代码首字母）。

所有 logo 统一转成 256px PNG，以 base64 内嵌进页面。海报页面不允许加载外部图片，外链会导致导出空白。

## 代码写法

- 推荐 `交易所:代码`：`SSE:600519`、`SZSE:300308`、`HKEX:700`、`NASDAQ:NVDA`、`NYSE:ANET`。
- 只写代码也能识别：6 位数字按首位判断沪/深（6、9 开头为上交所），1–5 位数字为港股，字母为美股。
- 港股键里写不带前导零的代码（`HKEX:700`），显示用的 `code` 可以写 `00700`。

## 版权说明

logo 归各自公司所有。fork 与上游的数据来自 TradingView 公开 logo 服务和 Wikidata，仅适合识别用途（图表、研究、学习材料）。海报页脚必须保留“徽标仅用于识别，归各自所有者”。不要修改、重绘或仿画 logo。
