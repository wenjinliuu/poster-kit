# 版块库与 spec.json 字段

编辑器里可以用 `spec.schema.json` 做字段补全和校验；`build_poster.py` 生成前也会自动检查。

海报 = 标题区 + 若干版块 + 页脚。版块按 `sections` 数组顺序从上到下排列，可以自由组合。

## 顶层字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `file` | 是 | 下载文件名前缀，如 `"AI光互连"` |
| `eyebrow` | 否 | 标题上方小字，如 `"产业链名单 · AI 光互连"` |
| `tag` | 否 | 眉题旁的描边小标签，如 `"示意数据"`、`"截至 10.17"` |
| `title` | 是 | 三段：`[黑色主句, 强调色大字, 灰色副句]`。主句 ≤ 10 字，大字 ≤ 9 字，副句 ≤ 14 字 |
| `object` | 否 | 右上背景物件：`chip` `module` `rack` `coin` `globe`，或不写 |
| `updown` | 否 | `"cn"`（默认，红涨绿跌）或 `"us"`（绿涨红跌） |
| `versions` | 否 | 默认 `["clear"]`（雾彩·清透）。新增风格后，需要对比时写多个，如 `["clear","新风格id"]` |
| `accent` | 否 | 强调色，默认靛紫 `#5b4cff`；系列海报想区分时换成 8 色里的另一色 |
| `companies` | 是* | 公司表，键是 `交易所:代码`（或 Yahoo 后缀代码、`市场:代码`），值是 `{"name": "中文名", "code": "显示代码(可选)"}` |
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

### `html` 自定义
现有版块放不下时才用，直接写 HTML，可复用 `.card` `.card-h` `.co` 等类。

## 常用组合

- **产业链名单**：`chain` → 页脚
- **持仓占比**：`holdings` → `notes`
- **数据统计 + 流向**：`kpis` → `years` → `ranking` → `banner` → `flows` → `notes`
- **板块行情**：`kpis` → `table` → `notes`
- **通用统计（非股票）**：`kpis` → `ranking`（普通标签）→ `years` → `notes`
