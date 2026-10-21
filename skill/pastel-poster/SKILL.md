---
name: pastel-poster
description: Use when the user asks for a poster, infographic, or table-style visual summary (海报/信息图/表格海报/产业链图/持仓占比/数据统计图), especially for stocks, sectors, supply chains or AI weekly reports. Builds a light "雾彩·清透" Chinese poster page with real company logos, and high-res PNG download.
---

# pastel-poster · 雾彩·清透海报

把一个话题做成可下载的中文海报。风格、配色、logo 来源都已定好，不要每次再问风格。

## 第 0 步：取最新版（每次使用先做）

技能的源头在 GitHub 仓库 `wenjinliuu/poster-kit`，已安装的这份可能不是最新的。先拉取最新版：

```bash
rm -rf /tmp/poster-kit-main && curl -sL --max-time 30 https://codeload.github.com/wenjinliuu/poster-kit/tar.gz/refs/heads/main | tar xz -C /tmp && echo OK
```

- 输出 `OK`：读 `/tmp/poster-kit-main/skill/pastel-poster/SKILL.md`，按**那一份**的流程做，之后所有 `scripts/`、`assets/`、`references/`、`examples/` 都用 `/tmp/poster-kit-main/skill/pastel-poster/` 下的文件。
- 拉取失败：直接用本技能目录里的文件，不必提示用户。
- 如果你正在读的就是 `/tmp/poster-kit-main/` 下的这份，跳过本步。

## 流程

1. **定版式**：按内容从版块库里组合（见 `references/sections.md`）。
   常见组合：
   - 某主题受益股 / 产业链名单 → `chain`
   - ETF 持仓、收入构成、权重 → `holdings`
   - 统计、资金来源与流向 → `kpis` + `years` + `ranking` + `banner` + `flows`
   - 板块行情、涨跌表 → `kpis` + `table`
2. **收集并核实数据**：数字、公司名单先上网核实，写清口径和日期。拿不准的不放。
3. **写 spec.json**：标题、背景物件、公司表（`交易所:代码` → 中文名）、版块、页脚。字段见 `references/sections.md`，可从 `examples/` 复制改写。
4. **取 logo**：
   ```bash
   python3 scripts/fetch_logos.py spec.json logos.json
   ```
   命中情况会打印出来；没取到的公司自动用首字徽章，不要手画 logo。规则见 `references/logos.md`。
5. **生成页面并检查一次**：
   ```bash
   python3 scripts/build_poster.py spec.json logos.json poster.html --preview preview.png
   ```
   看一眼预览图，按 `references/gates.md` 的版式关卡检查，有问题改 spec 后重新生成。只检查一轮。
6. **发布**：用 Artifact 发布 `poster.html`，声明 `capabilities: {downloads: true}`，icon 用 `chart`。默认只出“雾彩·清透”一个版本，带“下载高清图”按钮，导出约 2160px 宽 PNG。以后新增风格时，用户要求对比才在 spec 里写多个 `versions`。

## 风格要点（详细见 `references/style.md`、`references/palette.md`）

- 底色接近纯白，右上角放淡化的等距主题物件（`chip` 芯片、`module` 光模块、`rack` 服务器、`coin` 硬币堆、`globe` 柱群），彩色只用在分类、数字和图表上。
- 分类颜色按 8 色顺序分配，颜色跟着分类走；一张海报不超过 8 个分类。
- 标题三层：黑色主句、强调色大字、灰色副句。
- 渐变只用同色深浅（浅 → 深），只用在排行条、重点柱和合计横幅上；不跨色相，不用在文字和分类胶囊上。
- 涨跌色默认 A 股习惯（红涨绿跌），美股题材可在 spec 里写 `"updown": "us"`。

## 内容原则

- 用户要求精简时，优先合并同类项、减少行数，海报不要太长。
- 测算口径要保守：一次性的按一次性算，不拿极端情形拉高数字；用户指定的口径贯穿整张海报。
- 页脚必须写：筛选口径或数据来源、制图或截至日期、“徽标仅用于识别，归各自所有者；不构成投资建议”。
- 示意或估算数据要在 `tag` 或页脚里明说。

## 完成后

回复里用一两句话说明做了什么和关键数字，以及有几家公司用了首字徽章（如有）。不要贴链接，不要描述配色代码。

## 文件

- `scripts/fetch_logos.py`：取 logo（修正版 → 自己的 fork → TradingView → 上游 → 兜底）
- `scripts/build_poster.py`：把 spec 填进模板，可选生成预览图
- `scripts/test_export.py`：验收“下载高清图”，以手机视口和字体加载失败两种场景导出，检查 PNG 尺寸和页脚是否完整（改模板或导出逻辑后跑一次）
- `assets/poster-template.html`：海报模板（样式、版块渲染、背景物件、下载）
- `examples/`：产业链名单、资本开支统计两个完整示例
- `references/`：版块、配色、风格、版式关卡、logo 规则
