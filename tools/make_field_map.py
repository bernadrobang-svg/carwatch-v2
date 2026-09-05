"""★★★★★★ 09-05 — ★ **사이트별 매핑표를 가이드가 만든다** (마스터 지시).

★ 마스터 — 「★ **표는 너가 만들어야지.  ★ 너가 자료를 주고 ★ 개발팀이 업로드하게 해**」
★ ★ 원문(JSON)에서 ★ **모든 길을 펴고** ★ 우리 칸으로 이을 후보를 낸다.
★ ★ ★ 낸 것은 ★ `outputs/field_map_{site}.json` — ★ 개발측이 ★ `meta_field_usage` 에 넣는다.

★★ 실측 09-05 — ★ `meta_field_usage` 가 ★ **엔카 850줄 · 나머지 넷은 8줄**뿐이다.
  ★ ★ 그래서 ★ **옵션 0 이 열한 곳** · 트림 0 이 열 곳이다.
  ★ ★ ★ 파서도 ★ 표를 안 읽고 ★ `if`·정규식으로 박혀 있다 (KB if 24 · 리볼트 41).

돌리기  python3 -c "from tools.make_field_map import from_json as f; \\
                   f('revolt', '원문파일.json')"
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ★ 낱말 → 우리 칸.  ★ 앞에 있는 것이 먼저 맞는다 (좁은 것부터)
GUESS = (
    ("thumbnail_image", "photo_list_json"),
    ("image_url", "photo_list_json"),
    ("option_package", "options_name_json"),
    ("option_name", "options_name_json"),
    ("options", "options_name_json"),
    ("trim", "trim_grade_name"),
    ("grade", "trim_grade_name"),
    ("mileage", "mileage_km"),
    ("year", "year_month"),
    ("color", "color_ext_raw"),
    ("vin", "vin"),
    ("plate", "plate"),
    ("new_car_price", "price_origin_won"),
    ("price", "price_current_won"),
)
# ★ 이 낱말이 들어가면 ★ 값이 아니다 — ★ 크기·수·참거짓
SKIP = ("width", "height", "count", "is_", "_id", "url_type", "order")


def walk(o, pre=""):
    """★ JSON 을 펴서 ★ (길, 값) 을 모두 낸다."""
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            out += walk(v, f"{pre}.{k}" if pre else k)
    elif isinstance(o, list):
        if o:
            out += walk(o[0], pre + "[]")
    else:
        out.append((pre, o))
    return out


def from_json(site: str, path: str, endpoint: str = "detail") -> str:
    """★ 원문 파일 하나에서 ★ 매핑표 후보를 낸다."""
    with open(path, encoding="utf-8") as f:
        body = json.load(f)
    rows = []
    for p, v in walk(body):
        lp = p.lower()
        if any(s in lp for s in SKIP):
            continue
        for word, col in GUESS:
            if word in lp:
                rows.append({"site": site, "endpoint": endpoint,
                             "json_path": p, "core_column": col,
                             "본보기": str(v)[:40]})
                break
    out = os.path.join(ROOT, "outputs", f"field_map_{site}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"_어떻게": "가이드가 원문에서 캤다 (09-05) — "
                             "개발측이 meta_field_usage 에 넣는다",
                   "_사이트": site, "줄": len(rows), "표": rows},
                  f, ensure_ascii=False, indent=1)
    print(f"★ {site} — 길 {len(rows)}개 → {out}")
    return out
