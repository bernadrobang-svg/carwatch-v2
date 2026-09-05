"""차종 표를 만든다 — 수집·표시·추천 탭·사이트별 가능 여부 (09-05 마스터 지시).

마스터 — 「차종 목록을 만들고, 그 테이블에 받는 목록과 안 받는 목록을 표시해라.
  수집 Y/N · 전체 목록 표시 · 추천 표시 · 추천 탭별 표시.
  그리고 각 차종과 수집 채널(사이트)별로 수집할 수 있는지 여부도 표시해라.
  앞으로 분류 관련된 부분은 다 그 테이블을 보게 프로그램을 고쳐라」

낸 것: config/vehicle_table.json — 이것이 분류의 정본이다.
       outputs/VEHICLE_TABLE.md — 사람이 읽는 표.
"""
import html
import json
import os
import re
import ssl
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(ROOT, "config", "vehicle_table.json")
DOC = os.path.join(ROOT, "outputs", "VEHICLE_TABLE.md")

SITES = ("encar", "kbchachacha", "reborncar", "hyundai_cert", "kia_cpo",
         "kcar", "bmw_bps", "heydealer", "bobaedream", "volvo_selekt",
         "lexus_certified", "revolt")


def _conn(base_url, name, secret):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                     urllib.request.HTTPCookieProcessor(CookieJar()))

    def get(p):
        with op.open(base_url + p, timeout=60) as r:
            return r.read().decode("utf-8", "replace")

    def csrf(t):
        m = re.search(r'name="csrf" value="([^"]+)"', t)
        return m.group(1) if m else ""

    op.open(base_url + "/login", timeout=60)
    op.open(urllib.request.Request(
        base_url + "/login",
        data=urllib.parse.urlencode({"name": name, "secret": secret,
                                     "csrf": csrf(get("/login"))}).encode()),
        timeout=60)

    def rows(sql):
        tok = csrf(get("/admin/query"))
        with op.open(urllib.request.Request(
                base_url + "/admin/query",
                data=urllib.parse.urlencode({"sql": sql, "csrf": tok}).encode()),
                timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
        t = html.unescape(re.sub(r"<[^>]+>", "\n", body))
        out = [x.strip() for x in t.split("\n") if x.strip()]
        if "탭 구분 — 표에 그대로 붙습니다" not in out:
            return []
        j = out.index("탭 구분 — 표에 그대로 붙습니다")
        got = []
        for ln in out[j + 1:]:
            if "\t" not in ln:
                break
            got.append(ln.split("\t"))
        return got[1:] if got else []

    return rows


def build(base_url: str, name: str = "admin", secret: str = "12345678") -> str:
    rows = _conn(base_url, name, secret)
    with open(os.path.join(ROOT, "config", "targets.json"), encoding="utf-8") as f:
        tg = json.load(f)

    # 우리가 켠 차종 — 사이트별 건수를 센다
    seen = {}
    for r in rows("SELECT target_key, site, COUNT(*) AS n FROM core_listing "
                  "WHERE target_key IS NOT NULL GROUP BY target_key, site"):
        if len(r) < 3:
            continue
        seen.setdefault(r[0], {})[r[1]] = int(r[2])

    # 안 켠 차종 — site_model_group 으로 묶는다
    off = {}
    for r in rows("SELECT site_model_group, site, COUNT(*) AS n FROM core_listing "
                  "WHERE status='out_of_scope' AND site_model_group IS NOT NULL "
                  "GROUP BY site_model_group, site"):
        if len(r) < 3:
            continue
        off.setdefault(r[0], {})[r[1]] = int(r[2])

    out = {
        "_뜻": ("차종 표 — 분류의 정본이다 (마스터 확정 09-05). "
                "분류와 관련된 코드는 모두 이 표를 읽는다. "
                "새 차종을 켜려면 여기서 collect 를 Y 로 바꾼다."),
        "_칸": {
            "collect": "수집한다 Y/N",
            "show_list": "전체 목록에 낸다 Y/N",
            "show_recommend": "추천에 낸다 Y/N",
            "tab1": "추천 탭1(내 기준에 가까운 차) Y/N",
            "tab2": "추천 탭2(값→등급→취향) Y/N",
            "tab3": "추천 탭3(분석) Y/N",
            "tab4": "추천 탭4(GV70·X3) Y/N",
            "sites": "사이트별 받은 건수. 0 이면 그 사이트에 없거나 못 받는다",
            "taste_rank": "마스터 취향 순위",
        },
        "차종": {},
    }
    for k, v in tg.items():
        if not isinstance(v, dict) or k.startswith("SPEC_"):
            continue
        on = bool(v.get("active"))
        rec = bool(v.get("recommend"))
        rank = v.get("taste_rank")
        out["차종"][k] = {
            "label": v.get("label"),
            "collect": "Y" if on else "N",
            "show_list": "Y" if on else "N",
            "show_recommend": "Y" if rec else "N",
            "tab1": "Y" if rec else "N",
            "tab2": "Y" if rec else "N",
            "tab3": "Y" if rec else "N",
            "tab4": "Y" if k in ("GV70_25T", "X3_IMPORT") else "N",
            "taste_rank": rank,
            "sites": seen.get(k, {}),
        }
    for g, sites in sorted(off.items(), key=lambda x: -sum(x[1].values())):
        key = "OFF:" + g
        out["차종"][key] = {
            "label": g,
            "collect": "N",
            "show_list": "N",
            "show_recommend": "N",
            "tab1": "N", "tab2": "N", "tab3": "N", "tab4": "N",
            "taste_rank": None,
            "sites": sites,
        }
    with open(TABLE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    on_n = sum(1 for v in out["차종"].values() if v["collect"] == "Y")
    lines = [
        "# 차종 표",
        "",
        "`python3 -c \"from tools.make_vehicle_table import build; build('배포주소')\"` 가 만든다.",
        "정본은 `config/vehicle_table.json` 이다. 분류 관련 코드는 모두 이 표를 읽는다.",
        "",
        f"차종 **{len(out['차종'])}** · 수집 **{on_n}** · 미수집 {len(out['차종']) - on_n}",
        "",
        "| 차종 | 수집 | 목록 | 추천 | 탭1 | 탭2 | 탭3 | 탭4 | 취향 | 받은 사이트 |",
        "|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|---|",
    ]
    def _n(v):
        return sum(v["sites"].values())
    for k, v in sorted(out["차종"].items(),
                       key=lambda x: (x[1]["collect"] != "Y", -_n(x[1]))):
        s = " · ".join(f"{a} {b:,}" for a, b in
                       sorted(v["sites"].items(), key=lambda x: -x[1])[:4]) or "—"
        lines.append(f"| {v['label'] or k} | {v['collect']} | {v['show_list']} | "
                     f"{v['show_recommend']} | {v['tab1']} | {v['tab2']} | "
                     f"{v['tab3']} | {v['tab4']} | {v['taste_rank'] or '—'} | {s} |")
    with open(DOC, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"차종 {len(out['차종'])} (수집 {on_n}) → {TABLE} · {DOC}")
    return TABLE
