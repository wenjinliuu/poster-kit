# poster-kit

wenjin 的海报技能仓库：技能本体、海报模板和 logo 修正素材都在这里，是唯一的源头。

## 结构

```
poster-kit/
├─ skill/pastel-poster/        打包上传为 Claude 技能
│  ├─ SKILL.md                 流程与要点（入口，保持精简）
│  ├─ references/              按需读取的规范：版块、配色、风格、版式关卡、logo
│  ├─ scripts/
│  │  ├─ fetch_logos.py        取 logo：修正版 → fork → TradingView → 上游 → 首字兜底
│  │  └─ build_poster.py       spec.json + logos.json → 海报页面（可选预览图）
│  ├─ assets/poster-template.html   海报模板
│  └─ examples/                完整示例 spec
├─ assets/logo-overrides/      手工修正的 logo（不打包，生成时在线读取）
└─ .github/workflows/
   └─ release-skill.yml        打 tag 自动生成技能 zip
```

logo 主力来源是 [wenjinliuu/global-stock-logos](https://github.com/wenjinliuu/global-stock-logos)，它 fork 自 [MrChartist/global-stock-logos](https://github.com/MrChartist/global-stock-logos)，每天自动同步。

## 更新技能

1. 修改 `skill/pastel-poster/` 里的文件并推送。
2. 打一个 tag，例如 `git tag v1.1 && git push origin v1.1`。
3. 工作流会在 Releases 里生成 `pastel-poster.zip`，下载后到 Claude 的技能设置里上传替换。

也可以在 Actions 页面手动运行 **Release skill**。

## 本地试用

```bash
cd skill/pastel-poster
python3 scripts/fetch_logos.py examples/supply-chain.json /tmp/logos.json
python3 scripts/build_poster.py examples/supply-chain.json /tmp/logos.json /tmp/poster.html --preview /tmp/preview.png
```

## 加一个修正 logo

把文件放进 `assets/logo-overrides/`，命名 `{交易所}_{代码}.png` 或 `.svg`（如 `SZSE_300308.png`、`HKEX_700.svg`），推送即可生效，不需要重新上传技能。

## 版权

logo 归各自公司所有，仅用于识别。代码以 MIT 协议提供。
