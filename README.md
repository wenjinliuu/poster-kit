# poster-kit

**pastel-poster**：一个把话题做成中文信息海报的 Claude 技能。写一份 spec.json，生成“雾彩·清透”风格的海报网页，再导出高清 PNG。自带 68 个市场的真实公司 logo、8 色分类配色、等距背景物件和版式检查。

*A Claude skill that turns a JSON spec into a clean Chinese infographic poster (HTML page + high-res PNG), with real company logos from 68 stock markets.*

<p>
<img src="docs/images/supply-chain.jpg" width="24%" alt="产业链名单">
<img src="docs/images/global-semis.jpg" width="24%" alt="跨市场名单">
<img src="docs/images/etf-holdings.jpg" width="24%" alt="持仓占比">
<img src="docs/images/capex-stats.jpg" width="24%" alt="数据统计">
</p>

## 能做什么

- **版块自由组合**：产业链名单、大数字、环形持仓、年度柱状、排行条、合计横幅、资金流向、涨跌表格、要点，见 [`sections.md`](skill/pastel-poster/references/sections.md)。
- **真实 logo**：A 股、港股、美股、日韩台、欧洲等 68 个市场，代码写 `SZSE:300308`、`7203.T`、`2330.TW` 都行；取不到自动用首字徽章。
- **先网页、后图片**：海报是一张 1080px 宽的网页，页面上能预览、点按钮下载 2 倍高清 PNG；命令行也能直接导出。
- **页面自包含**：字体按用到的字取子集内嵌，html2canvas 内置，不依赖外部资源，国内打开和导出也稳定。
- **有检查**：生成前检查 spec（字段、公司引用、标题字数、分类数），导出有手机窄屏和字体回退两种场景的自动验收。

## 快速开始

```bash
cd skill/pastel-poster
pip install -r requirements.txt && python3 -m playwright install chromium   # 只生成网页时可以不装

python3 scripts/fetch_logos.py examples/supply-chain.json logos.json
python3 scripts/build_poster.py examples/supply-chain.json logos.json poster.html --standalone --png poster.png
```

打开 `poster.html` 预览，或直接用 `poster.png`。不加 `--standalone` 输出的是 claude.ai Artifact 页面片段。

## 在 Claude 里使用

1. 到 [Releases](../../releases) 下载 `pastel-poster.zip`，在 Claude 的技能设置里上传。
2. 对 Claude 说“做一张 AI 光互连产业链的海报”之类的话，技能会按 [`SKILL.md`](skill/pastel-poster/SKILL.md) 的流程收集数据、写 spec、取 logo、生成并检查海报。

## 结构

```
poster-kit/
├─ skill/pastel-poster/        技能本体（打包上传的就是这个目录）
│  ├─ SKILL.md                 流程与要点
│  ├─ references/              版块、配色、风格、版式关卡、logo 规则、spec.schema.json
│  ├─ scripts/
│  │  ├─ fetch_logos.py        取 logo：手工修正版 → logo 仓库 → 可选 TradingView → 首字徽章
│  │  ├─ build_poster.py       spec.json + logos.json → 海报网页（--png 直接出图）
│  │  ├─ render_png.py         海报网页 → PNG
│  │  ├─ validate_spec.py      检查 spec
│  │  └─ test_export.py        导出验收
│  ├─ assets/                  海报模板、html2canvas
│  └─ examples/                完整示例 spec
├─ assets/logo-overrides/      手工修正的 logo（不打包，取 logo 时在线读取）
├─ docs/images/                README 效果图
└─ .github/workflows/          CI（示例验收）与发布（打 tag 生成技能 zip）
```

## 配置 logo 来源

默认来源是 [MrChartist/global-stock-logos](https://github.com/MrChartist/global-stock-logos)。可用环境变量换成自己的 fork 或修正图目录：

```bash
export POSTER_LOGO_REPOS="me/global-stock-logos@main,MrChartist/global-stock-logos@main"
export POSTER_LOGO_OVERRIDES="/path/to/my-overrides,https://raw.githubusercontent.com/me/poster-kit/main/assets/logo-overrides"
```

对某个 logo 不满意：把文件放进 `assets/logo-overrides/`，命名 `{交易所}_{代码}.png` 或 `.svg`（如 `SZSE_300308.png`、`HKEX_700.svg`），推送即可生效。

## 发布新版本

1. 修改 `skill/pastel-poster/` 并推送，CI 会跑示例验收。
2. 打 tag：`git tag v1.2 && git push origin v1.2`。
3. 工作流在 Releases 里生成 `pastel-poster.zip`。也可以在 Actions 页面手动运行 **Release skill**。

## 版权

代码以 [MIT](LICENSE) 协议提供。公司 logo 归各自所有者，仅用于识别；logo 仓库的数据来源和条款见其 [DATA-SOURCES](https://github.com/MrChartist/global-stock-logos/blob/main/DATA-SOURCES.md)。海报内容不构成投资建议。
