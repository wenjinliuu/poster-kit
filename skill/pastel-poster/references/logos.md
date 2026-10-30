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

## 头部大字标（brand）

个股、公司事件海报的头部放公司字标，比圆形小 logo 更醒目。按顺序选：

1. **官方字标**：维基共享资源（Wikimedia Commons）上大多数上市公司都有 SVG 字标。
   ```bash
   python3 scripts/find_wordmark.py "SK hynix"          # 搜索，列出候选和下载地址
   python3 scripts/find_wordmark.py --file "SK_Hynix.svg"   # 已知文件名时直接给地址（搜索接口限流时用）
   ```
   也可以用公司官网新闻中心 / 品牌资源页的 SVG。地址写进 `brand.image`，生成时下载并内嵌（脚本和事件属性会被去掉）。选横版、完整、现行的字标，不选旧版和子品牌。
2. **文字重建**：找不到官方文件时用 `brand.wordmark`，按官方字标的写法和颜色拼文字，例如 `[{"text":"SK","color":"#e31837","weight":900},{"text":"hynix","color":"#f58025"}]`。需要图形部分时，自己画一个简洁的 SVG 放 `brand.svg`（只用几何形状，忠实于原标志的形状和颜色，不做变形、加特效）。页脚加一句“字标为文字重建，仅用于识别”。
3. **都没有**：不写 `image`/`wordmark`，显示 logo 库的圆形 logo + 公司名。

品牌色从官方字标里取（SVG 里的 `fill` 颜色），写进 `brand.colors`。模板会把第一个品牌色吸附到 6 个冷色图表色里最接近的颜色作强调色（见 `style.md`），字标本身保持原色。

## 版权说明

logo 归各自公司所有。logo 仓库的数据主要来自 TradingView 公开 logo 服务和 Wikidata，仅适合识别用途（图表、研究、学习材料）；商用或大量使用前请自行确认相关条款。海报页脚必须保留“徽标仅用于识别，归各自所有者”。官方 logo 和字标不要修改、变形、改色；只在讲这家公司本身的海报里使用。
