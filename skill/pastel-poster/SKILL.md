---
name: pastel-poster
description: Use when the user asks for a poster, infographic, or table-style visual summary (海报/信息图/表格海报/产业链图/持仓占比/数据统计图/财报速览/事件速览/日报), especially for stocks, earnings, financing events, sectors, supply chains or market reports. Builds a light "雾彩·清透" Chinese poster page with charts (waterfall, beat-vs-estimate, line, columns, heatmap, target price), real company logos (68 markets), and high-res PNG download.
---

# pastel-poster · 雾彩·清透海报

把一个话题做成可下载的中文海报：先生成海报网页，再从网页导出高清 PNG。风格、配色、logo 来源都已定好，不要每次再问风格。

下文的 `scripts/`、`assets/`、`references/`、`examples/` 都指本技能目录下的文件。

## 流程

1. **判断类型、定骨架**：读 `references/recipes.md`，判断属于哪一类（财报速览、公司事件、产业链名单、持仓构成、数据统计、行情日报、研报观点），按配方的骨架选版块（字段见 `references/sections.md`）。
2. **按清单收集并核实数据**：照配方里的信息收集清单逐项上网查，数字和公司名单都要核实，写清口径、来源和日期。几家媒体数字不一致时对上口径；没公布的写“未披露”；拿不准的不放。先想清楚每个版块回答什么问题，小标题写成结论。
3. **写 spec.json**：标题、背景物件、公司表（键写 `交易所:代码`、Yahoo 后缀代码如 `7203.T`，或 `市场:代码`）、版块、页脚。个股和公司事件加 `brand`，深度速览加 `numbered`。字段见 `references/sections.md`，可从 `examples/` 里最接近的示例复制改写。
4. **取 logo**：
   ```bash
   python3 scripts/fetch_logos.py spec.json logos.json
   ```
   命中情况会打印出来；没取到的公司自动用首字徽章，不要手画 logo。新上市股票没取到时可加 `--tradingview` 再试一次。规则见 `references/logos.md`。
5. **生成网页和预览图**：
   ```bash
   python3 scripts/build_poster.py spec.json logos.json poster.html --png preview.png
   ```
   生成前会自动检查 spec：有错误会列出并停止，有提醒（标题过长、分类过多等）照着改。看一眼预览图，按 `references/gates.md` 的版式关卡检查，有问题改 spec 后重新生成。只检查一轮。
   没有 playwright 时去掉 `--png`，网页照样生成。
6. **验收导出**：发布前跑一次，确认手机窄屏下载的 PNG 尺寸和页脚完整（出现 ✗ 就先修再发）：
   ```bash
   python3 scripts/test_export.py spec.json --out export-check
   ```
7. **交付**：
   - 在 claude.ai 里：用 Artifact 发布 `poster.html`，声明 `capabilities: {downloads: true}`，icon 用 `chart`。页面带“下载高清图”按钮，导出约 2160px 宽 PNG。
   - 不在 claude.ai 里：加 `--standalone` 生成完整网页，直接把网页和 `--png` 导出的 PNG 交给用户；网页里的下载按钮走浏览器普通下载。
   默认只出“雾彩·清透”一个版本。以后新增风格时，用户要求对比才在 spec 里写多个 `versions`。

## 风格要点（详细见 `references/style.md`、`references/palette.md`）

- 底色接近纯白，右上角放淡化的等距主题物件（芯片、光模块、服务器、晶圆、数据库、硬币堆、柱群、电池、楼群、机器人，都不合适就用 `parts` 拼一个），彩色只用在分类、数字和图表上。
- 分类颜色按 8 色顺序分配，颜色跟着分类走；一张海报不超过 8 个分类。
- 标题三层：黑色主句、强调色大字、灰色副句。
- 渐变只用同色深浅（浅 → 深），只用在排行条、重点柱和合计横幅上；不跨色相，不用在文字和分类胶囊上。
- 涨跌色默认 A 股习惯（红涨绿跌），美股题材可在 spec 里写 `"updown": "us"`。
- 图表只画真实数据，不画示意图；需要突出一项时只高亮它，其余变灰。

## 内容原则

- 用户要求精简时，优先合并同类项、减少行数，海报不要太长（普通 ≤ 2200px，深度速览 ≤ 5000px）。
- 测算口径要保守：一次性的按一次性算，不拿极端情形拉高数字；用户指定的口径贯穿整张海报。
- 页脚必须写：筛选口径或数据来源、制图或截至日期、“徽标仅用于识别，归各自所有者；不构成投资建议”。
- 示意或估算数据要在 `tag` 或页脚里明说。

## 完成后

回复里用一两句话说明做了什么和关键数字，以及有几家公司用了首字徽章（如有）。不要贴链接，不要描述配色代码。

## 文件

- `scripts/fetch_logos.py`：取 logo（手工修正版 → logo 仓库 → 可选 TradingView → 首字徽章兜底），支持 68 个市场
- `scripts/build_poster.py`：检查 spec，把 spec 填进模板生成网页（字体子集和 html2canvas 都内嵌，页面不依赖外部资源），`--png` 直接导出图片
- `scripts/render_png.py`：把已有的海报网页导出成 PNG，和“下载高清图”按钮同一套逻辑
- `scripts/validate_spec.py`：单独检查 spec
- `scripts/test_export.py`：验收导出，以手机视口和字体回退两种场景检查 PNG 尺寸和页脚（改模板或导出逻辑后跑一次）
- `assets/poster-template.html`：海报模板（样式、版块渲染、背景物件、下载）
- `assets/vendor/html2canvas.min.js`：导出用的 html2canvas 1.4.1
- `examples/`：财报速览、融资事件、行情日报、产业链名单、跨市场名单、持仓占比、资本开支统计七个完整示例（前三个为示例数据，只演示版式）
- `references/`：海报类型配方 `recipes.md`、版块、配色、风格、版式关卡、logo 规则、`spec.schema.json`
- `requirements.txt`：可选依赖（cairosvg、Pillow、playwright）
