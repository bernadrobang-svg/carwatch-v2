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
# ★★★★★ 09-05 — ★ **한 낱말이 여러 칸을 뜻한다**.  ★ 엔카 실측:
#   ★ `options.choice[]` 는 ★ **값이 있는 코드**(10004) → `options_choice_json`
#   ★ `options.standard[]`·`etc[]`·`tuning[]` 은 ★ **이름 목록** → `options_name_json`
#   ★ `category.originPrice` 는 ★ **신차가**(4406) → `price_origin_won`
#   ★ ★ 그래서 ★ **좁은 길을 먼저** 둔다 — ★ 앞에 있는 것이 먼저 맞는다
GUESS = (
    ("options.choice", "options_choice_json"),
    ("options.standard", "options_name_json"),
    ("options.etc", "options_name_json"),
    ("options.tuning", "options_name_json"),
    ("originprice", "price_origin_won"),
    ("gradedetailname", "trim_grade_name"),
    ("gradename", "trim_grade_name"),
    ("colorname", "color_ext_raw"),
    ("yearmonth", "year_month"),
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
# ★ 09-05 — ★ 이 낱말이 들어가면 ★ 값이 아니다.
#   ★ `warranty.bodyMileage`(보증 주행) · `leaseRentInfo`(리스) · `EnglishName` ·
#   ★ `gradeCd`(코드) 를 ★ 잘못 이었다 — ★ 실측에서 잡아 뺐다
SKIP = ("width", "height", "count", "is_", "_id", "url_type", "order",
        "warranty", "leaserent", "englishname", "cd", "type", "custom")


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
    """★ 원문 파일 하나에서 ★ 매핑표 후보를 낸다.

    ★★★★★ 09-05 — ★ **여기서 크게 틀렸다**.  ★ `curl` 이 실패해도
      ★ ★ `/tmp/o.txt` 에 ★ **앞 응답이 그대로 남아** ★ 기아·렉서스 표에
      ★ ★ ★ **리볼트 자료가 들어갔다**(`prnd-car-purchase` 주소가 그대로).
      ★ ★ ★ ★ 셋이 ★ **똑같은 34줄**이었다 — ★ 그래서 잡았다.
    ★★ 그래서 ★ **본보기 값에 그 사이트 자취가 있는지** 본다 —
      ★ 없으면 ★ **표를 안 만든다**.  ★ 「남의 자료로 표를 만드는 것」이 ★ 가장 나쁘다
    """
    import hashlib as _h
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
    if not rows:
        print(f"★ {site} — 길 0개.  ★ 표를 안 만든다")
        return ""
    # ★ 09-05 — ★ 남의 자료가 섞이지 않았는지 ★ 자취로 본다
    mark = _h.md5(json.dumps(rows, ensure_ascii=False,
                             sort_keys=True).encode()).hexdigest()[:10]
    for old in os.listdir(os.path.join(ROOT, "outputs")):
        if not old.startswith("field_map_") or old == f"field_map_{site}.json":
            continue
        with open(os.path.join(ROOT, "outputs", old), encoding="utf-8") as f:
            prev = json.load(f)
        if _h.md5(json.dumps(prev.get("표", []), ensure_ascii=False,
                             sort_keys=True).encode()).hexdigest()[:10] == mark:
            print(f"★ {site} — ★ {old} 과 ★ **똑같다**.  "
                  "★ 원문이 안 바뀐 것이다 — ★ 표를 안 만든다")
            return ""
    out = os.path.join(ROOT, "outputs", f"field_map_{site}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"_어떻게": "가이드가 원문에서 캤다 (09-05) — "
                             "개발측이 meta_field_usage 에 넣는다",
                   "_사이트": site, "줄": len(rows), "표": rows},
                  f, ensure_ascii=False, indent=1)
    print(f"★ {site} — 길 {len(rows)}개 → {out}")
    return out


# ★★★★★★★ 09-05 — ★ **파서에서 뽑는다** (마스터 지시)
#
#   ★ 마스터 — 「★ **개발에게 왜 위임하지?  ★ 파서에 하드코딩으로 값이 있다면서**」
#   ★ ★ 맞다.  ★ **사이트를 두드릴 것 없이** ★ 파서 코드에 ★ 이미 짝이 들어 있다 —
#     ★ 실측 09-05 — ★ 우리 칸 이름이 ★ **열한 곳 파서에 다 나온다**
#       (KB 11가지 · 보배 10 · 볼보 9 · 리본카 10 · BMW 9 · 기아CPO 14 · K카 11 …)
#   ★ ★ ★ 그러니 ★ **코드에서 뽑아 표로 만들면** ★ 사이트가 막혀도 된다

# ★★★★★ 09-05 — ★ **개인정보 칸은 이름이 다르다**.
#   ★ 번호판은 ★ `core_listing.plate` 가 아니라 ★ **`_pii_plate_no`** 로 넘긴다 —
#   ★ ★ `save_listing_pii()` 가 ★ `core_pii` 표에 따로 넣기 때문이다.
#   ★ ★ ★ 그걸 몰라 ★ 「번호판이 열두 곳 다 없다」로 잘못 냈다 [09-05].
#   ★ 차대번호(`vin`)도 ★ 같은 자리일 수 있다 — ★ 둘 다 본다
COL_RE = (r"(_pii_plate_no|_pii_record_plate_no|"
          r"price_current_won|price_origin_won|mileage_km|year_month|"
          r"color_ext_raw|color_int_raw|trim_grade_name|options_choice_json|"
          r"options_name_json|photo_list_json|vin|plate|form_year|"
          r"displacement_cc|fuel_raw)")


def from_parser(site: str) -> str:
    """★ 파서 코드에서 ★ 「우리 칸 ← 원문 길」 짝을 뽑아 ★ 표로 낸다.

    ★ 세 꼴을 본다 —
      ① `"칸": _get(body, "a.b")`      ★ 길이 그대로 있다
      ② `out["칸"] = ...`              ★ 길을 옆에서 찾는다
      ③ `"칸": 변수`                    ★ 길을 못 캐면 ★ **「코드에 박혀 있다」로 적는다**
    ★ ★ 못 캔 것도 ★ **버리지 않는다** — ★ 개발측이 그 줄을 보고 옮긴다
    """
    import glob as _g
    import re as _re

    rows = []
    for f in sorted(_g.glob(os.path.join(ROOT, "parse", site, "*.py"))):
        body = open(f, encoding="utf-8").read()
        name = os.path.basename(f)
        # ★★ 09-05 (2차) — ★ **꼴이 셋이다**.  ★ 여섯 곳을 못 뽑아 찾아보니 —
        #   ① `"칸": _get(body, "a.b")`        ★ 엔카·기아·K카·현대·헤이딜러
        #   ② `out["칸"] = _int(price)`        ★ KB·볼보·리본카·BMW·보배
        #   ③ `("칸", RE_KM)` ★ 짝 목록         ★ KB 가 정규식과 짝지어 쓴다
        #   ★ ★ **셋 다 잡는다** — ★ 한 꼴만 보면 ★ 절반이 빈다
        pat = (r'"' + COL_RE + r'"\s*:\s*([^,\n]{0,90})'
               r'|\[\s*"' + COL_RE + r'"\s*\]\s*=\s*([^\n]{0,90})'
               r'|\(\s*"' + COL_RE + r'"\s*,\s*([^)\n]{0,60})')
        for m in _re.finditer(pat, body):
            col = m.group(1) or m.group(3) or m.group(5)
            expr = (m.group(2) or m.group(4) or m.group(6) or "").strip()
            path = ""
            g = _re.search(r'"([\w.\[\]]+)"', expr)
            if g:
                path = g.group(1)
            line = body[:m.start()].count("\n") + 1
            rows.append({"site": site, "core_column": col,
                         "json_path": path or "(코드에 박혀 있다)",
                         "코드": f"{name}:{line}", "식": expr[:60]})
    if not rows:
        print(f"★ {site} — 파서에서 못 뽑았다")
        return ""
    out = os.path.join(ROOT, "outputs", f"field_map_{site}.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"_어떻게": "가이드가 ★ 파서 코드에서 뽑았다 (09-05) — "
                             "★ 사이트를 안 두드렸다.  개발측이 meta_field_usage 에 넣는다",
                   "_사이트": site, "줄": len(rows), "표": rows},
                  f, ensure_ascii=False, indent=1)
    print(f"★ {site} — 파서에서 {len(rows)}줄 → {out}")
    return out
