#!/usr/bin/env python3
"""检查 spec.json：字段缺失、版块类型拼错、引用了没登记的公司等错误，以及标题过长、分类过多等版式提醒。

用法：
    python3 validate_spec.py spec.json [...]

build_poster.py 生成前会自动调用；有错误时不生成。字段说明见 references/sections.md，
编辑器里可以用 references/spec.schema.json 做补全和校验。
"""
import json
import re
import sys

# 每种版块的必填字段
SECTIONS = {
    "chain": ["groups"], "kpis": ["items"], "holdings": ["items"], "years": ["items"], "ranking": ["items"],
    "banner": ["label", "value"], "flows": ["items"], "table": ["columns", "rows"], "notes": ["items"], "html": ["html"],
    "beat": ["items"], "waterfall": ["items"], "mix": ["items"], "bars": ["items"], "line": ["x", "series"],
    "columns": ["x", "series"], "points": ["items"], "callout": ["title"], "text": [], "cards": ["items"],
    "heatmap": ["columns", "rows"], "deviation": ["rows"], "chips": ["groups"], "target": ["items"],
    "group": ["sections"], "row": ["sections"],
    "donut": ["items"], "stackbar": ["series", "rows"], "scatter": ["points"], "slope": ["items"], "dumbbell": ["items"],
    "treemap": ["items"], "funnel": ["items"], "radar": ["axes", "series"], "rings": ["items"], "waffle": [],
    "sankey": ["links"], "sparks": ["items"], "timeline": ["items"], "steps": ["items"], "compare": ["left", "right"],
    "quadrant": ["cells"], "tree": ["root"], "pyramid": ["items"], "cycle": ["items"], "draw": ["js"],
}
OBJECTS = {"chip", "module", "rack", "coin", "globe", "battery", "building", "wafer", "db", "robot"}


def width(text):
    """按中文字宽估算：中文和全角算 1，数字、字母、空格约 0.55；**强调** 记号不算"""
    text = text.replace("**", "")
    return sum(1 if ord(c) > 0x2000 else 0.55 for c in text)


def validate(spec):
    errors, warnings = [], []
    if not isinstance(spec, dict):
        return ["spec 必须是一个 JSON 对象"], []
    title = spec.get("title")
    if not isinstance(title, list) or not title:
        errors.append("title 必须是 [黑色主句, 强调色大字, 灰色副句] 数组")
    else:
        # 主句、大字放不下一行会自动缩小字号；超过约 1.4 倍就缩得太小了
        for t, n, label in zip(title, (13, 12, 22), ("主句", "大字", "副句")):
            if isinstance(t, str) and width(t) > n:
                warnings.append(f"标题{label}“{t}”约 {width(t):.0f} 字宽，建议 ≤ {n}，太长会被缩得很小或换行")
    if not isinstance(spec.get("sections"), list) or not spec["sections"]:
        errors.append("sections 必须是非空数组")
    if not isinstance(spec.get("footer"), list) or not spec["footer"]:
        errors.append("footer 必须是数组，至少写来源和免责声明")
    elif spec.get("companies") and not any("不构成投资建议" in s or "仅用于识别" in s for s in spec["footer"] if isinstance(s, str)):
        warnings.append("页脚没有免责声明（“徽标仅用于识别，归各自所有者；不构成投资建议”）")
    obj = spec.get("object")
    if isinstance(obj, dict):
        if not isinstance(obj.get("parts"), list):
            errors.append("object 写成对象时要有 parts 数组，如 [[\"box\",0,0,0,100,100,40,\"body\"]]")
    elif obj is not None and obj not in OBJECTS:
        errors.append(f"object “{obj}” 不存在，可选 {sorted(OBJECTS)}，或用 parts 自己拼")
    if spec.get("updown", "cn") not in ("cn", "us"):
        errors.append("updown 只能是 cn 或 us")
    if spec.get("accent") and not re.fullmatch(r"#[0-9a-fA-F]{6}", spec["accent"]):
        errors.append("accent 要写成 #rrggbb")
    brand = spec.get("brand")

    companies = spec.get("companies") or {}

    def need(key, where):
        if isinstance(key, str) and key not in companies:
            errors.append(f"{where} 引用了 {key}，但 companies 里没有登记")

    if isinstance(brand, dict) and brand.get("company"):
        need(brand["company"], "brand")

    def check(sections, path, depth=0):
        for i, s in enumerate(sections):
            where = f"{path}[{i}]"
            t = s.get("type") if isinstance(s, dict) else None
            if t not in SECTIONS:
                errors.append(f"{where} 的 type “{t}” 不存在，可选 {sorted(SECTIONS)}")
                continue
            where += f"（{t}）"
            missing = [f for f in SECTIONS[t] if f not in s]
            if missing:
                errors.append(f"{where} 缺少字段 {missing}")
                continue
            if t in ("group", "row"):
                if depth >= 1 and t == "row":
                    warnings.append(f"{where} 嵌在别的 group/row 里，排版会很挤")
                if t == "row" and len(s["sections"]) > 3:
                    warnings.append(f"{where} 并排 {len(s['sections'])} 块，超过 3 块会很窄")
                check(s["sections"], where + ".sections", depth + 1)
                continue
            check_one(t, s, where)

    def check_one(t, s, where):
        if t == "chain":
            if len(s["groups"]) > 8:
                warnings.append(f"{where} 有 {len(s['groups'])} 组，超过 8 种分类色")
            for g in s["groups"]:
                for k in g.get("companies", []):
                    need(k, where)
                if len(g.get("name", "")) > 7:
                    warnings.append(f"{where} 组名“{g.get('name')}”超过 7 字")
        elif t == "holdings":
            for h in s["items"]:
                need(h[0], where)
            total = sum(h[1] for h in s["items"]) + (s.get("other") or 0)
            if not 95 <= total <= 105:
                warnings.append(f"{where} 各项加“其他”合计 {total:.1f}%，不接近 100%")
        elif t == "flows":
            for f in s["items"]:
                for k in f.get("companies", []):
                    need(k, where)
        elif t == "table":
            for j, c in enumerate(s["columns"]):
                if c.get("type") == "company":
                    for r in s["rows"]:
                        need(r[j], where)
            if len(s["rows"]) > 10:
                warnings.append(f"{where} 有 {len(s['rows'])} 行，超过 10 行海报会很长")
        elif t == "ranking":
            for r in s["items"]:
                if isinstance(r[0], str) and ":" in r[0]:
                    need(r[0], where)
        elif t == "kpis" and not 1 <= len(s["items"]) <= 4:
            warnings.append(f"{where} 建议 2–4 个大数字")
        elif t == "beat":
            for it in s["items"]:
                if "actual" not in it:
                    errors.append(f"{where} 每项要有 actual（实际值）")
        elif t == "waterfall":
            for it in s["items"]:
                if "value" not in it and not it.get("total"):
                    errors.append(f"{where} 的“{it.get('label')}”没有 value")
                if it.get("state", "solid") not in ("solid", "option", "plan"):
                    errors.append(f"{where} state 只能是 solid / option / plan")
        elif t in ("bars", "points", "cards", "donut", "slope", "dumbbell", "treemap", "funnel", "sparks", "timeline"):
            for it in s["items"]:
                need(it.get("company"), where)
            if t == "donut" and len(s["items"]) > 6:
                warnings.append(f"{where} 超过 6 块，小的并进 other（“其他”）")
            if t == "slope" and len(s["items"]) > 10:
                warnings.append(f"{where} 超过 10 条线会挤，只留重点并 highlight")
        elif t == "scatter":
            for it in s["points"]:
                need(it.get("company"), where)
                if "x" not in it or "y" not in it:
                    errors.append(f"{where} 每个点要有 x 和 y")
        elif t == "stackbar":
            for r in s["rows"]:
                need(r.get("company"), where)
                if len(r.get("values", [])) != len(s["series"]):
                    errors.append(f"{where} 行“{r.get('label')}”的值个数和 series 不一致")
        elif t == "radar":
            if len(s["series"]) > 3:
                warnings.append(f"{where} 超过 3 个系列会糊成一团")
            for q in s["series"]:
                if len(q.get("values", [])) != len(s["axes"]):
                    errors.append(f"{where} 系列“{q.get('name')}”的值个数和 axes 不一致")
        elif t == "waffle":
            if "items" not in s and "value" not in s:
                errors.append(f"{where} 要写 items 或 value")
        elif t == "sankey":
            for l in s["links"]:
                if not {"source", "target", "value"} <= set(l):
                    errors.append(f"{where} 每条 link 要有 source、target、value")
        elif t == "compare":
            for side in ("left", "right"):
                need(s[side].get("company"), where)
        elif t == "quadrant" and len(s["cells"]) != 4:
            errors.append(f"{where} cells 要正好 4 个（左上、右上、左下、右下）")
        elif t in ("line", "columns"):
            n = len(s["x"])
            for q in s["series"]:
                if len(q.get("values", [])) != n:
                    errors.append(f"{where} 系列“{q.get('name')}”有 {len(q.get('values', []))} 个值，x 有 {n} 个")
            if t == "line" and len(s["series"]) > 4:
                warnings.append(f"{where} 超过 4 条线会看不清，突出一条（highlight）其余变灰")
        elif t == "heatmap":
            for r in s["rows"]:
                need(r.get("company"), where)
                if len(r.get("values", [])) != len(s["columns"]):
                    errors.append(f"{where} 行“{r.get('label') or r.get('company')}”的格子数和 columns 不一致")
        elif t == "deviation":
            for r in s["rows"]:
                need(r.get("company"), where)
                if "value" not in r:
                    errors.append(f"{where} 每行要有 value（偏离值）")
        elif t == "chips":
            for g in s["groups"]:
                for it in g.get("items", []):
                    need(it[0] if isinstance(it, list) else it, where)
        elif t == "target":
            for it in s["items"]:
                need(it.get("company"), where)
                if not it.get("targets") or "price" not in it:
                    errors.append(f"{where} 每项要有 price 和 targets")

    check(spec.get("sections") or [], "sections")
    return errors, warnings


if __name__ == "__main__":
    ok = True
    for path in sys.argv[1:]:
        errs, warns = validate(json.load(open(path, encoding="utf-8")))
        print(("✓" if not errs else "✗"), path)
        for e in errs:
            print(f"  ✗ {e}")
        for w in warns:
            print(f"  提醒：{w}")
        ok &= not errs
    sys.exit(0 if ok else 1)
