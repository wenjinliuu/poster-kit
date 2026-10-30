# 版块库与 spec.json 字段

编辑器里可以用 `spec.schema.json` 做字段补全和校验；`build_poster.py` 生成前也会自动检查。

海报 = （品牌头部）+ 标题区 + 若干版块 + 页脚。版块按 `sections` 数组顺序从上到下排列，可以自由组合；用 `group` 把几块放进一张卡片，用 `row` 让几块并排。先按 `recipes.md` 选骨架。

所有文字字段都可以用 `**重点**` 标出强调（显示为强调色），标题、小标题、说明、要点里都能用。

## 顶层字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `file` | 是 | 下载文件名前缀，如 `"AI光互连"` |
| `eyebrow` | 否 | 标题上方小字，如 `"产业链名单 · AI 光互连"` |
| `tag` | 否 | 眉题旁的描边小标签，如 `"示意数据"`、`"截至 10.17"` |
| `title` | 是 | 三段：`[黑色主句, 强调色大字, 灰色副句]`。主句、大字放不下一行会自动缩小字号，建议主句 ≤ 10 字、大字 ≤ 9 字、副句 ≤ 18 字。大字里写 `**数字**` 时变成“黑字 + 特大强调色数字”，如 `"已锁定 **375** 亿美元"` |
| `brand` | 否 | 品牌头部（个股、公司事件），右边是 `label`（代码）和 `sub`（海报类型）。左边按优先级：`image` 官方字标（URL 或本地 SVG/PNG，生成时内嵌）→ `wordmark` 文字重建字标 `[{"text":"SK","color":"#e31837"},{"text":"hynix","color":"#f58025"}]`（可配 `svg` 图形）→ 圆形 logo + `name`。`colors` 写品牌色（第一个作强调色），`height` 调字标高度。见 `logos.md` |
| `numbered` | 否 | `true` 时卡片标题前加 1、2、3 编号，适合深度速览 |
| `object` | 否 | 右上背景物件，见 `style.md`：`chip` `module` `rack` `coin` `globe` `battery` `building` `wafer` `db` `robot`，或 `{"parts": [...]}` 自己拼 |
| `updown` | 否 | `"cn"`（默认，红涨绿跌）或 `"us"`（绿涨红跌） |
| `versions` | 否 | 默认 `["clear"]`（雾彩·清透）。新增风格后，需要对比时写多个，如 `["clear","新风格id"]` |
| `accent` | 否 | 强调色，默认靛紫 `#5b4cff`；有 `brand.colors` 时取第一个品牌色。写任意颜色都会吸附到 8 个图表色（避开涨跌红绿）里最接近的一个，`"exact_color": true` 才保留原色 |
| `companies` | 是* | 公司表，键是 `交易所:代码`（或 Yahoo 后缀代码、`市场:代码`），值是 `{"name": "中文名", "code": "显示代码(可选)", "color": "#rrggbb(可选，logo 描边色)"}` |
| `badge_ring` | 否 | 圆形 logo 的描边：`auto`（默认，按 logo 底板配色：白底彩色取主色、彩色底取底色浅一档、黑底浅灰、黑白图形按代码固定色，见 `palette.md`）、`category`（跟所在分类色）、`brand`（logo 原色）、`accent`、`none` |
| `sections` | 是 | 版块数组 |
| `footer` | 是 | 页脚多行，最后一行是免责声明（小字） |
| `page_title` / `page_sub` | 否 | 网页标题和说明（不进海报） |
| `mark` / `mark_sub` | 否 | 页脚右侧署名，默认 `pastel-poster` |

*只要版块里引用了公司就必须写。常用交易所：`SSE` 上交所、`SZSE` 深交所、`HKEX` 港交所、`NASDAQ`、`NYSE`、`AMEX`、`TSE` 东京、`KRX` 韩国、`TWSE` 台湾、`LSE` 伦敦；也可以写 `7203.T`、`2330.TW` 这类 Yahoo 代码。完整写法见 `logos.md`。
港股 `code` 建议写 5 位，如 `"06869"`；A 股、美股可省略 `code`，自动取键里的代码。

## 版块类型

### `chain` 分组 + 公司网格
受益股一览、产业链各环节名单。每组一种颜色，组数 ≤ 8，每组公司 ≤ 8 家。
```json
{"type":"chain","cols":4,"groups":[
  {"name":"光模块","desc":"一句话说明这一环节的作用","icon":"module","companies":["SZSE:300308","NASDAQ:COHR"]}]}
```
`icon` 可选（同背景物件的取值），`cols` 每行公司数，默认 4。组名 ≤ 7 字，说明 ≤ 22 字。

### `kpis` 大数字摘要
2–4 个。`tone` 写 `up`/`down` 时数字用涨跌色，否则用分类色。
```json
{"type":"kpis","items":[{"label":"板块周涨幅","value":"+5.84","unit":"%","note":"跑赢沪深300","tone":"up"}]}
```

### `holdings` 环形图 + 权重卡片
持仓、构成、份额。前 6 项出卡片和彩色环段，第 7 项起合并成灰色环段并以小胶囊列出；`other` 为“其他”。≥10% 的环段直接标数字。
```json
{"type":"holdings","title":"持仓权重","note":"占基金净值比例","center_label":"前十大合计","center_value":"86.4%",
 "items":[["SZSE:300308",15.4],["SZSE:300502",14.6]],"other":13.6}
```

### `years` 时间柱状
3–8 根柱。默认最后一根用强调色（`"highlight_last": false` 可关闭），所有柱都标数值。
```json
{"type":"years","title":"历年资本开支","note":"单位：亿美元","items":[["2024",2310],["2025E",4060]]}
```

### `ranking` 排行条
按数值降序。`items` 的第一项可以是公司键，也可以是 `{"label":"成都","sub":"西南"}` 这种普通标签。`other` 写成 `["其他", 数值, "说明"]`。
```json
{"type":"ranking","title":"钱从哪来","unit":"亿美元","items":[["NASDAQ:GOOGL",2050]],"other":["其他",440,"二线云厂商等"]}
```

### `banner` 合计横幅
强调一个总数，放在排行和流向之间。
```json
{"type":"banner","label":"2027E 合计","value":"$8,600 亿","note":"较 2026E 增长 37%"}
```

### `flows` 占比条 + 去向卡片
2–4 项，每项可带 ≤ 4 家代表公司；`prefix`/`suffix` 给金额加单位。
```json
{"type":"flows","title":"流向哪里","prefix":"$","suffix":" 亿","items":[{"name":"芯片与服务器","value":3870,"companies":["NASDAQ:NVDA"]}],"other":1890}
```

### `table` 通用表格
板块行情、对比表。列类型：`company`（徽章+代码+名称）、`pct`（涨跌胶囊，带正负号）、不写为普通文本。行数 ≤ 10。
```json
{"type":"table","title":"领涨成分股","columns":[{"label":"股票","type":"company"},{"label":"收盘"},{"label":"周涨跌","type":"pct"}],
 "rows":[["SZSE:300308","186.40",12.6]]}
```

### `notes` 要点
2–4 条，每条 ≤ 30 字，两列排布。

### 通用字段

每个版块都可以写 `title`（卡片标题，可用 `**强调**`）、`note`（标题右侧灰字：单位、口径、来源）、`caption`（版块底部的灰色小字说明）。

### `group` 一张卡片里放几块
```json
{"type":"group","title":"超预期多少","note":"单位：万亿韩元","sections":[{"type":"beat",...},{"type":"waterfall","title":"为什么净利润少了？",...}]}
```
子版块的 `title` 显示为小标题，之间用细线分隔。一个问题配一张主图和一张解释图时用它。

### `row` 并排
```json
{"type":"row","sections":[{"type":"kpis","title":"股东回报","layout":"list",...},{"type":"bars","title":"需求从哪来","layout":"stack",...}]}
```
2–3 块并排，各自成卡片。并排时横条用 `layout:"stack"`（标签在条上方）。

### `kpis` 补充
- `rows`：卡片底部的对比行，如 `[["环比","+32%"],["同比","+328%"]]`；`+` 开头自动用涨色、`-` 开头用跌色，第三项写 `""` 关掉颜色。
- `tone`：`up` / `down` / `accent`（强调色）/ `ink`（黑色），不写按分类色。
- `layout:"list"`：竖排的大数字列表（左数字、右说明），适合放在 `row` 里。
- 单位很长（“万亿韩元”）时写进 `note`，`unit` 留空，数字会更醒目；数字太宽会自动缩小。

### `beat` 实际 vs 预期
```json
{"type":"beat","items":[{"label":"营收","actual":104.62,"estimates":[{"name":"LSEG","value":98.34},{"name":"韩媒汇总","value":98.23}]}]}
```
灰点是各家预期，虚线是一致预期（各家的中位数），彩点是实际；超预期用涨色，不及预期用跌色（成本类写 `"higher_better": false`）。
- 同一个 `beat` 里的各行共用一把刻度，按“偏离一致预期的百分比”画：超 0.2% 几乎贴着虚线，超 30% 才拉到远处，不同单位（营收、EPS）也能放在一起比。预期不是正数（如亏损的 EPS）的那行改用自己的刻度。
- 点旁写“实际 0.52 +30.0%”，下方逐家写出“超 6.4%”。标签里有“指引”的行自动写“指引”而不是“实际”；别的叫法用 `actual_label` 改。
- 偏离差几十倍的两组数（如营收超 0.1%、EPS 低 40%）也可以放在一起，小的那行本来就该看起来很小；想单独看清小幅偏离时拆成两个 `beat`。

### `waterfall` 瀑布（拆解、分层口径）
```json
{"type":"waterfall","items":[{"label":"营业利润","value":83.33,"total":true},{"label":"汇兑损失","value":-11.63},{"label":"净利润","total":true}]}
```
- `total:true` 的柱从 0 画起，不写 `value` 时取前面累计值；其余项在累计值上浮动。
- `state`：`solid` 确定（默认）/ `option` 可选（斜纹）/ `plan` 计划（虚线框）。用到多种时自动出图例，图例文字可用 `legend` 改。
- `stack:true` 的合计柱按前面各项分段上色；`g` 指定分类色序号；`text` 改柱顶文字（如 `"+约 56"`）；`sub` 是柱下小字。
- 默认增项用浅强调色、减项用灰色；`"colors":"updown"` 改用涨跌色。`brackets: [{"from":0,"to":1,"text":"已锁定 375"}]` 在柱下画括号标注。

### `mix` 构成条 + 分项卡
```json
{"type":"mix","items":[{"name":"DRAM","value":75,"rows":[["出货量","约 +10%","up"],["平均售价","+20% 高段","up"]]},{"name":"NAND","value":24}],"other":1}
```
100% 条显示各项占比；带 `rows` 的项在下面出一张量价卡片。

### `bars` 通用横条
```json
{"type":"bars","unit":"%","max":100,"items":[{"label":"美光","sub":"6–9 月 · GAAP","value":80.7,"extra":"542 亿美元"},{"label":"SK 海力士","value":79.7,"highlight":true}]}
```
- `value` 可以是 `[低, 高]` 区间；`text` 改右侧数值文字（如 `"+20% 中段"`）；`company` 用公司 logo 当标签；`extra` 是最右侧灰字。
- 每行默认一种分类色；有 `highlight` 时那一行用强调色，并加同色浅底和描边的“选中”样式（同业对比突出自己用）；`tone:"gray"` 单独把某行变灰；`colors:"accent"` 全部用强调色；`g` 指定分类色序号。
- `layout:"stack"` 标签在条上方（窄卡片、并排时用）；`label_width`、`value_width` 调列宽，`max` 定刻度上限。

### `line` 折线
系列写 `symbol`（股票代码）不写 `values` 时自动取行情，`x` 也自动生成；默认换算成相对起点的涨跌幅（`normalize:false` 保留原价），`range` 默认 1y。
```json
{"type":"line","unit":"%","x":["Q2'25","Q3'25","Q4'25"],"series":[{"name":"SK 海力士","values":[62,57,50],"highlight":true},{"name":"三星","values":[17,22,33]}]}
```
- 单条线自动加面积底色，默认标出首、尾、最高、最低点；`labels` 写序号数组指定标哪些点，或 `"all"`、`"end"`。
- 多条线在线尾标名字和末值；有 `highlight` 时其余线变灰，没有时各用分类色并出图例。超过 4 条线看不清。
- `ymin` / `ymax` 定纵轴，`est_from` 从该序号起画虚线（预测），`x_every` 隔几个标一次横轴，`height` 改图高，`axis:false` 去掉纵轴。

### `columns` 柱状（可分组、可区间）
```json
{"type":"columns","unit":"%","est_from":3,"x":["4Q25","1Q26","2Q26","3Q26E"],"series":[{"name":"DRAM","values":[[45,50],[93,98],[58,63],[13,18]]},{"name":"NAND","values":[33,85,55,18]}]}
```
值可以是数字或 `[低, 高]` 区间（柱高取上限，柱顶标“低–高”）；`est_from` 起的柱变淡表示预估；单系列时 `highlight` 写序号只把那根用强调色。

### `points` 标签 + 一句话
```json
{"type":"points","items":[{"tag":"HBM4","text":"Q4 出货量将超过 HBM3E"},{"tag":"担心","tone":2,"text":"现金流转负"}]}
```
电话会要点、市场观点、风险、“数字怎么来的”对账。默认标签用强调色；`tone` 可写 `up` `down` `gray` `dark` `accent` 或分类色序号；`colors:"cats"` 让同名标签同色。`company` 在句首加 logo 和公司名，`sub` 是第二行小字，`cols:2` 两列。

### `callout` 提示框
```json
{"type":"callout","tone":"down","title":"缺口 **21** 亿美元","text":"花的比赚的多 → 需要外部融资"}
```
澄清一个容易误读的事实、强调一个结论、标明“未披露”。`tone`：`accent`（默认）`up` `down` `gray`。

### `text` 段落
大号小标题 + 一段说明，不带卡片。用来在海报中途换话题（“芯片商投钱，也绑定 **Muse**”）。

### `cards` 小卡片
```json
{"type":"cards","items":[{"title":"Muse Spark","sub":"4 月 · 驱动 Muse"},{"title":"用户","value":"1,000万+","sub":"约 6 周"}]}
```
产品线、时间节点、并列的小概念。默认强调色，`colors:"cats"` 每张一色，`cols` 定列数。

### `heatmap` 热力表
```json
{"type":"heatmap","format":"pct","columns":["周一","周二"],"rows":[{"label":"SPY","values":[-6,4]}]}
```
格子颜色按值相对 `center`（默认 0）的方向用涨跌色、按幅度定深浅；想显示 A 值、按 B 值上色时写 `colors` 矩阵（如格内写量倍数、颜色表示偏离）。`format`：`pct`（带正负号百分比）、`x`（倍数）或不写。

### `deviation` 偏离条
```json
{"type":"deviation","columns":["成交量","Call/Put"],"bar_label":"偏离 20 日常态","range":30,"rows":[{"label":"SPY","sub":"标普 500","cols":["0.8×",["0.76","常态 0.90"]],"value":-16}]}
```
中线是常态 / 基准，向右高于、向左低于，刻度为 ±`range`。`cols` 里的项写成 `[值, 小字]` 时小字跟在后面。

### `chips` 分组名单
```json
{"type":"chips","groups":[{"label":"偏多","items":[["NASDAQ:CRWD","up"],"NASDAQ:NVDA"]}]}
```
观察名单、名单外异动。每家一个 logo 胶囊，第二项是圆点颜色（`up` `down` `gray`）；`show_name:true` 显示名称。

### `target` 目标价刻度
```json
{"type":"target","items":[{"company":"NASDAQ:SMCI","price":38.5,"unit":"美元","rating":"摩根大通 · 维持中性","targets":[{"org":"摩根大通","tp":42,"highlight":true},{"org":"瑞银","tp":30}]}]}
```
浅色条带是各家目标价范围，竖线是现价，实心点是高亮那家；右侧显示其目标价和相对现价的空间（没有高亮时取中位数）。

### `html` 自定义
现有版块放不下时才用，直接写 HTML，可复用 `.card` `.card-h` `.co` 等类。

## 更多图表与信息结构

选哪种先看 `charts.md`。下面只列字段。凡是写 `company` 的地方都会自动带上 logo；写 `icon` 的地方用 Lucide 图标名（https://lucide.dev/icons，如 `coffee`、`train-front`、`shield-check`）。任何版块写 `"card": false` 就不包卡片。

### 数据图表

| 版块 | 字段 |
|---|---|
| `donut` 环形 | `items:[{label, value, company?, tone?}]`，`other`，`center_value`，`center_label`，`show:"value"`（图例显示数值而不是占比），`unit` |
| `stackbar` 堆叠横条 | `series:[类别名]`，`rows:[{label, sub?, company?, values:[…]}]`，`percent`（默认 true 归一到 100%），`diverging:true`（态度色阶），`unit`、`max` |
| `columns` 堆叠柱 | 在原 `columns` 上加 `stack:true`，柱顶标合计，段内标数值 |
| `bars` 棒棒糖 | 在原 `bars` 上加 `style:"lollipop"` |
| `scatter` 散点 / 气泡 | `points:[{label, x, y, size?, group?, company?, highlight?}]`，`x_label`、`y_label`、`x_unit`、`y_unit`，`quadrants:true` 或 `{x, y, labels:[右上,左上,左下,右下]}`，`labels:"all"/"highlight"/"none"` |
| `slope` 坡度 | `left`、`right`（两个时间点名），`items:[{label, a, b, company?, highlight?}]`，`unit`，`right_names:true` 右侧也写名字 |
| `dumbbell` 哑铃 | `a_label`、`b_label`，`items:[{label, a, b, company?}]`，`unit`，`xmin`/`xmax`，`colors:"updown"` |
| `treemap` 矩形树 | `items:[{label, value, group?, company?}]`，`height`，`show:"value"`，`unit` |
| `funnel` 漏斗 | `items:[{label, value, sub?}]`，`unit`，`conv_label`（默认“转化”） |
| `radar` 雷达 | `axes:[维度]`，`series:[{name, values, highlight?}]`（≤3），`max`，`size` |
| `rings` 圆环 | `items:[{label, value, max?, text?, sub?, tone?}]`，`unit`（默认 %），`cols`，`size`，`colors:"cats"` |
| `waffle` 方格 / 象形 | `items:[{label, value, text?, tone?}]` 或单个 `value`+`label`，`total`（默认 100），`unit_value`（每格代表多少），`icon`（每格画图标），`cols` |
| `sankey` 桑基 | `links:[{source, target, value}]`，`unit`，`height`，`colors:{节点名: tone}`，`link_color:"target"` |
| `price` 股价走势 | `company` 或 `symbol`，`range`（1mo 3mo 6mo 1y 2y 5y ytd，默认 1y），`style:"candle"`（K 线，默认收盘折线），`ma:[20,60]`，`volume:false` 关成交量，`events:[{date, label}]`，`targets:[{org, tp, highlight?}]`（目标价喇叭口和上涨空间），`height`。行情由 `build_poster.py` 调 `fetch_prices.py` 自动取（雅虎财经，港股和 A 股取不到用腾讯行情），最新价、涨跌、最高最低、空间都由代码算 |
| `sparks` 小多图 | `items:[{label, sub?, company?, values, value_text?, change?}]`，`cols`，`unit`，`colors:"updown"`；项里写 `symbol` 不写 `values` 时自动取行情（`range` 默认 3mo） |

### 信息结构

| 版块 | 字段 |
|---|---|
| `timeline` 时间线 | `items:[{time, title, text?, icon?, company?, highlight?}]`，`layout:"horizontal"`（≤6 个） |
| `steps` 步骤 | `items:[{title, text?, icon?}]`，`layout:"row"/"list"`（默认 ≤5 步横排） |
| `compare` 对比 | `left`/`right`：`{title, sub?, company?, icon?, tone?, items?}`；有 `rows:[{label, left, right, winner?:"left"/"right"}]` 时逐项对比，否则两列列表；`vs` 改中间字 |
| `quadrant` 四象限 | `cells:[左上, 右上, 左下, 右下]`，每格 `{title, items?, text?, tone?, letter?}`；`x_title`、`y_title`；`swot:true` 自动标 S/W/O/T |
| `tree` 树 | `root:{label, sub?, children:[…]}`，最多 3 层；`row_height` |
| `pyramid` 金字塔 | `items:[{title, text?}]`，从上（窄）到下（宽） |
| `cycle` 循环 | `items:[{title, text?, icon?}]`（3–6 个），`center`（中间文字，`\n` 换行），`size` |
| `draw` 自定义 | `height`，`js`（见 `charts.md` 第五节） |

`cards` 和 `kpis` 也支持 `icon`、`company`；`cards` 有 `value` 时显示大数字。

## 常用组合

完整的骨架和信息收集清单见 `recipes.md`。

- **产业链名单**：`chain` → 页脚
- **持仓占比**：`holdings` → `notes`
- **数据统计 + 流向**：`kpis` → `years` → `ranking` → `banner` → `flows` → `notes`
- **板块行情**：`kpis` → `table` → `notes`
- **通用统计（非股票）**：`kpis` → `ranking`（普通标签）→ `years` → `notes`
