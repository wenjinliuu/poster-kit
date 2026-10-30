---
name: pastel-poster
description: Use when the user asks for a poster, infographic, or visual summary of any topic (海报/信息图/长图/数据图/科普图/财报速览/事件速览/日报/产业链图/对比图), from user-provided material or web research — finance (stocks, earnings, financing, sectors, market reports) and everyday topics alike. Builds a light "雾彩·清透" Chinese poster page with 40+ chart and layout blocks (bars, line, donut, waterfall, scatter, sankey, treemap, radar, timeline, steps, compare, tree...), icons, official company wordmarks and logos (68 markets), and high-res PNG download.
---

# pastel-poster · 雾彩·清透海报

把一个话题做成可下载的中文海报：先生成海报网页，再从网页导出高清 PNG。风格、配色、logo 来源都已定好，不要每次再问风格。

下文的 `scripts/`、`assets/`、`references/`、`examples/` 都指本技能目录下的文件。

## 第 0 步：取最新版（每次使用先做）

技能的源头是 GitHub 仓库 `wenjinliuu/poster-kit` 的 main 分支，已安装的这份可能不是最新的。先拉取最新版：

```bash
rm -rf /tmp/poster-kit-main /tmp/poster-kit.tgz
curl -sfL --max-time 30 -o /tmp/poster-kit.tgz https://codeload.github.com/wenjinliuu/poster-kit/tar.gz/refs/heads/main \
  && tar xzf /tmp/poster-kit.tgz -C /tmp && test -f /tmp/poster-kit-main/skill/pastel-poster/SKILL.md \
  || { rm -rf /tmp/poster-kit-main && git clone -q --depth 1 https://github.com/wenjinliuu/poster-kit /tmp/poster-kit-main; } \
  && test -f /tmp/poster-kit-main/skill/pastel-poster/SKILL.md && echo OK || echo FAIL
```

- 输出 `OK`：读 `/tmp/poster-kit-main/skill/pastel-poster/SKILL.md`，按**那一份**的流程做，之后所有 `scripts/`、`assets/`、`references/`、`examples/` 都用 `/tmp/poster-kit-main/skill/pastel-poster/` 下的文件。
- 输出 `FAIL`（常见原因：会话的网络只放行已接入的仓库，代理把请求挡了）：
  1. 有接入 GitHub 仓库的工具（如 `add_repo`）就先把 `wenjinliuu/poster-kit` 接入本会话，再重跑上面的命令一次。
  2. 还是失败，才用本技能目录里的文件，并**在开始做之前告诉用户一句**：“没能拉到海报技能最新版，这次用的是已安装版本，可能缺最近的修复。”
- 如果你正在读的就是 `/tmp/poster-kit-main/` 下的这份，跳过本步。
- fork 了本仓库的人：把上面两处 `wenjinliuu/poster-kit` 换成自己的仓库。

## 流程

1. **判断类型**：读 `references/recipes.md`，判断属于哪一类（财报速览、公司事件、产业链名单、持仓构成、数据统计、行情日报、研报观点、知识科普、通用数据报告、事件始末、对比评测），看这一类“常问的问题”和信息收集清单。不限于财经：用户给了资料或让你上网搜一个话题，都可以做。**这一步不定版块。**
2. **查资料 → 资料卡 → 分析 → 大纲**：按 `references/story.md` 做。
   - **资料卡**（`research.md`）是记账本，不是筛子：查到的事实、数字、观点、传闻、线索都记下，每条写口径、来源、日期；几家数字不一致就都记并写清口径，传闻标“传闻”，查不到写“未披露”。清单只提醒别漏，不限制去哪查、查什么。
   - **分析**：找出这次最重要的变化（大标题），列读者会问的 3～5 个问题，用比较（预期、指引、上季、去年、同行）和拆分（业务、量价、利润各层、一次性）找原因，写出反方和不确定的地方。
   - **大纲**（`outline.md`）：每个版块写“问题 → 结论小标题 → 用哪几条资料 → 用什么图”（按 `references/charts.md` 选，字段见 `references/sections.md`）。没资料支撑的版块删掉；没用上的资料列在“未用”里，不删。按 `story.md` 第 4 节过一遍内容关卡。深度海报能和用户对话时，先给用户看大纲。
   - 另有专门的资料技能时，按它补充来源和问题。
3. **写 spec.json**：按大纲写标题、背景物件、公司表（键写 `交易所:代码`、Yahoo 后缀代码如 `7203.T`，或 `市场:代码`）、版块、页脚。字段见 `references/sections.md`，可从 `examples/` 里最接近的示例复制改写。
   - 个股和公司事件加 `brand`：头部放公司字标（`scripts/find_wordmark.py` 找官方 SVG，找不到就按品牌色文字重建），`brand.colors` 写品牌色作强调色，见 `references/logos.md`。
   - 海报里提到其他公司时，在条、线、点、卡片上写 `company` 带出 logo。
   - 要点、步骤、时间线可以写 `icon`（Lucide 图标名），让海报更形象。
   - 需要股价走势时用 `price` 版块只写公司代码，行情生成时自动取，不要手抄价格。
   - 深度速览加 `numbered`。
   - 页脚右下角署名写 `mark`（制作者或用户指定的名字，如机器人名称），不写默认显示 `pastel-poster`。
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
   - 发到自己部署的海报站点（图库）：加 `--hosted` 生成托管模式的网页（字体、logo 引用站点地址，不内嵌；由站点提供下载），再按站点自己的发布方式提交。
   默认只出“雾彩·清透”一个版本。以后新增风格时，用户要求对比才在 spec 里写多个 `versions`。

## 风格要点（详细见 `references/style.md`、`references/palette.md`）

- 底色接近纯白，右上角放淡化的等距主题物件（芯片、光模块、服务器、晶圆、数据库、硬币堆、柱群、电池、楼群、机器人，都不合适就用 `parts` 拼一个，比如床、汽车、杯子），彩色只用在分类、数字和图表上。
- 讲某家公司时按它的品牌色系选强调色（自动吸附到 6 个冷色，红橙黄品牌用默认靛紫，不用品牌原色）；强调色只用在标题、编号、主图和高亮项，并列的类别、卡片、步骤、标签默认多彩。
- 分类颜色按 8 个图表色顺序分配（避开涨跌红绿），颜色跟着分类走；一张海报不超过 8 个分类。另有 4 个接近涨跌色的颜色只给 logo 描边用，见 `references/palette.md`。
- 标题三层：黑色主句、强调色大字、灰色副句。
- 渐变只用同色深浅（浅 → 深），只用在排行条、重点柱和合计横幅上；不跨色相，不用在文字和分类胶囊上。
- 涨跌色默认 A 股习惯（红涨绿跌），美股题材可在 spec 里写 `"updown": "us"`。
- 图表只画真实数据，不画示意图；需要突出一项时只高亮它，其余变灰。

## 内容原则

- 用户要求精简时，优先合并同类项、减少行数，海报不要太长（普通 ≤ 2200px，深度速览 ≤ 5000px）。
- 测算口径要保守：一次性的按一次性算，不拿极端情形拉高数字；用户指定的口径贯穿整张海报。
- 页脚必须写：数据来源或筛选口径、制图或截至日期；用了公司 logo 时写“徽标仅用于识别，归各自所有者”，财经内容加“不构成投资建议”，健康类加“不构成医疗建议”。
- 示意或估算数据要在 `tag` 或页脚里明说。

## 完成后

回复里用一两句话说明做了什么和关键数字，以及有几家公司用了首字徽章（如有）。不要贴链接，不要描述配色代码。

## 文件

- `scripts/fetch_logos.py`：取 logo（手工修正版 → logo 仓库 → 可选 TradingView → 首字徽章兜底），支持 68 个市场
- `scripts/build_poster.py`：检查 spec，把 spec 填进模板生成网页（字体子集和 html2canvas 都内嵌，页面不依赖外部资源），`--png` 直接导出图片；`--hosted` 生成托管模式（字体、logo 引用站点地址）
- `scripts/render_png.py`：把已有的海报网页导出成 PNG，和“下载高清图”按钮同一套逻辑
- `scripts/validate_spec.py`：单独检查 spec
- `scripts/find_wordmark.py`：在维基共享资源找公司官方字标 SVG
- `scripts/fetch_prices.py`：取股价日线（雅虎财经，港股、A 股可回退腾讯行情），生成时自动给 `price`、带 `symbol` 的 `sparks` / `line` 取数，也可单独运行看最新价和区间涨跌
- `scripts/test_export.py`：验收导出，以手机视口和字体回退两种场景检查 PNG 尺寸和页脚（改模板或导出逻辑后跑一次）
- `assets/poster-template.html`：海报模板（样式、版块渲染、背景物件、下载）
- `assets/vendor/html2canvas.min.js`：导出用的 html2canvas 1.4.1
- `examples/`：财报速览、融资事件、行情日报、城市生活报告、睡眠科普、产业链名单、跨市场名单、持仓占比、资本开支统计九个完整示例（财报、融资、日报、城市为示例或虚构数据，只演示版式）
- `references/`：资料卡、分析与大纲 `story.md`，海报类型配方 `recipes.md`（常问的问题、收集清单、常见排法），图表选型 `charts.md`，版块、配色、风格、版式关卡、logo 规则、`spec.schema.json`
- `requirements.txt`：可选依赖（cairosvg、Pillow、playwright）
