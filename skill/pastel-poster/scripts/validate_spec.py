#!/usr/bin/env python3
"""检查 spec.json：字段缺失、版块类型拼错、引用了没登记的公司等错误，以及标题过长、分类过多等版式提醒。

用法：
    python3 validate_spec.py spec.json [...]

build_poster.py 生成前会自动调用；有错误时不生成。字段说明见 references/sections.md，
编辑器里可以用 references/spec.schema.json 做补全和校验。
"""
import json
import sys

# 每种版块的必填字段
SECTIONS = {
    "chain": ["groups"], "kpis": ["items"], "holdings": ["items"], "years": ["items"], "ranking": ["items"],
    "banner": ["label", "value"], "flows": ["items"], "table": ["columns", "rows"], "notes": ["items"], "html": ["html"],
}
OBJECTS = {"chip", "module", "rack", "coin", "globe"}


def width(text):
    """按中文字宽估算：中文和全角算 1，数字、字母、空格约 0.55"""
    return sum(1 if ord(c) > 0x2000 else 0.55 for c in text)


def validate(spec):
    errors, warnings = [], []
    if not isinstance(spec, dict):
        return ["spec 必须是一个 JSON 对象"], []
    title = spec.get("title")
    if not isinstance(title, list) or not title:
        errors.append("title 必须是 [黑色主句, 强调色大字, 灰色副句] 数组")
    else:
        for t, n, label in zip(title, (10, 9, 14), ("主句", "大字", "副句")):
            if isinstance(t, str) and width(t) > n:
                warnings.append(f"标题{label}“{t}”约 {width(t):.0f} 字宽，超过 {n} 字可能挤成两行")
    if not isinstance(spec.get("sections"), list) or not spec["sections"]:
        errors.append("sections 必须是非空数组")
    if not isinstance(spec.get("footer"), list) or not spec["footer"]:
        errors.append("footer 必须是数组，至少写来源和免责声明")
    elif not any("不构成投资建议" in s or "仅用于识别" in s for s in spec["footer"] if isinstance(s, str)):
        warnings.append("页脚没有免责声明（“徽标仅用于识别，归各自所有者；不构成投资建议”）")
    obj = spec.get("object")
    if obj is not None and not isinstance(obj, dict) and obj not in OBJECTS:
        errors.append(f"object “{obj}” 不存在，可选 {sorted(OBJECTS)}")
    if spec.get("updown", "cn") not in ("cn", "us"):
        errors.append("updown 只能是 cn 或 us")

    companies = spec.get("companies") or {}

    def need(key, where):
        if isinstance(key, str) and key not in companies:
            errors.append(f"{where} 引用了 {key}，但 companies 里没有登记")

    for i, s in enumerate(spec.get("sections") or []):
        where = f"sections[{i}]"
        t = s.get("type") if isinstance(s, dict) else None
        if t not in SECTIONS:
            errors.append(f"{where} 的 type “{t}” 不存在，可选 {sorted(SECTIONS)}")
            continue
        where += f"（{t}）"
        missing = [f for f in SECTIONS[t] if f not in s]
        if missing:
            errors.append(f"{where} 缺少字段 {missing}")
            continue
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
