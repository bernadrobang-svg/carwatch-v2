# -*- coding: utf-8 -*-
"""규격 기준 통합 테스트 (통합테스트_시나리오_규격기준.md).

★ 소스에서 폼 필드를 뽑아 짜지 않는다.  그러면 「만든 대로 도는가」만 본다.
  지시서 STEP · 시안 · 검증 코드가 요구한 것을 화면에서 찾는다 —
  「만들어야 할 것이 만들어졌나」를 본다

판정
  합격    규격이 요구한 것이 화면에 있고, 눌러서 규격대로 동작한다
  불합격  ① 규격에 있는데 화면에 없다     ② 눌러도 규격대로 안 된다
         ③ 안내와 동작이 다르다          ④ 500 이 난다
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))

from test_integration import (  # noqa: E402
    Client, links, seed_admin, start_server, text,
)

FAIL: list = []
ROWS: list = []


def rec(code, spec, did, got, ok, why=""):
    ROWS.append((str(code), spec, did, str(got), "합" if ok else "불", why))
    if not ok:
        FAIL.append(f"{code} {spec}")
    print(f"  {'PASS' if ok else 'FAIL'}  {code:6} {spec:30} {did:26} {got}"
          + (f"  ← {why}" if why and not ok else ""))
    return ok


# ── A  표시 규격 (STEP 149f) ────────────────────────────────────────
def spec_a(ad: Client, lid: int) -> None:
    print("\n[A] 표시 규격 (STEP 149f)")
    st, lb, _h = ad.get("/listings")
    body = text(lb)

    # A-1 비율이 크게 · 원점수/분모가 작게
    ratio = re.search(r"\d+\.\d\s*%", body)
    raw = re.search(r"\d+(?:\.\d+)?\s*/\s*\d+", body)
    rec("A-1", "비율 % + 원점수/분모 함께", "목록을 본다",
        f"비율={bool(ratio)} · 분수={bool(raw)}",
        bool(ratio) and bool(raw),
        "분모가 다른 매물을 눈으로 갈라야 한다")

    # A-2  ★ 부록 G 로 확인율이 상세(/why)로 갔다 (개정 332).
    #   목록은 요약이다 — 계산식과 확인율은 상세에서 본다
    _st, _wb, _hh = ad.get(f"/why/{lid}")
    _conf = re.search(r"확인율 \d+(?:\.\d+)?%", text(_wb))
    rec("A-2", "확인율을 상세에 낸다 (개정 298 I · 부록 G)", "상세를 본다",
        _conf.group(0) if _conf else "표시 없음", bool(_conf),
        "분모로 막지 않는 대신 얼마나 봤는지를 낸다")

    # A-3 막대는 비율.  ★ 목록에서 뺐으므로 추천·상세에서 본다 (부록 G)
    _st, _rb, _hh = ad.get("/recommend")
    _bar = re.search(r'width:\s*\d+(?:\.\d+)?%', _rb + _wb)
    rec("A-3", "막대는 비율을 그린다 (추천·상세)", "style 폭을 본다",
        "% 폭" if _bar else "없음", bool(_bar))

    # A-4 축 3상태
    # ★ 기호를 시험에 박지 않는다.  config/labels.json 이 정본이다 —
    #   실측 08-16: 「없음」을 · 에서 - 로 바꾸자 시험만 옛 기호를 찾았다
    import json as _j
    with open(os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "config", "labels.json"),
            encoding="utf-8") as _f:
        _marks = _j.load(_f)["VALUE_MARKS"]
    # ★ 어느 10행이 걸리느냐에 따라 결과가 달라지면 안 된다.
    #   기호를 만드는 규칙 자체를 본다 — 셋이 서로 다른가
    from report.screens.build import chip as _chip
    _APP_CSS = open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "web", "static", "app.css"),
        encoding="utf-8").read()
    _lab = _j.load(open(os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "config", "labels.json"),
        encoding="utf-8"))
    _three = [_chip("state.accident", v, e, _lab)
              for v, e in ((70, False), (0, False), (None, True))]
    want = {_marks["1"], _marks["0"], _marks["unknown"]}
    got3 = ({c.mark for c in _three} >= want
            and len({c.tone for c in _three}) == 3
            and all(f"axis-{c.tone}" in _APP_CSS for c in _three))
    rec("A-4", "축 3상태 O · - · ?", "기호를 만드는 규칙을 본다",
        " · ".join(f"{c.mark}({c.tone})" for c in _three) if got3
        else "구분 없음", got3,
        "「없음」과 「모름」이 같으면 v1 사고")

    # A-5 등급 흰 글자
    rec("A-5", "등급 S~D 흰 글자", "gradecls 를 본다",
        "grade- 클래스" if "grade-" in lb else "없음", "grade-" in lb)

    # A-6 E 는 뒤로
    st2, eb, _h = ad.get("/listings?order=rank")
    grades = re.findall(r'grade-([A-Z]+)', eb)
    e_last = ("E" not in grades) or (grades.index("E") >= len(grades) - 2
                                     or all(g == "E" for g in
                                            grades[grades.index("E"):]))
    rec("A-6", "E 는 맨 뒤", "정렬 순서를 본다",
        f"등급 순서 {grades[:6]}…", e_last)

    # A-7 숫자 셀 mono
    # ★ 시안이 class="r num" 처럼 붙여 쓴다 — 낱말로 본다 (개정 275)
    has_num = re.search(r'class="[^"]*\bnum\b[^"]*"', lb) is not None
    rec("A-7", "숫자 셀에 mono", "class 를 본다",
        "num 있음" if has_num else "없음", has_num)


# ── B  필터가 다음 행동의 조건 (STEP 149g · 149d) ───────────────────
def spec_b(ad: Client) -> None:
    print("\n[B] 필터 (STEP 149g · 149d)")
    st, lb, _h = ad.get("/listings")

    # B-1 표의 값을 누르면 조건 추가
    kinds = {k for k in ("grade=", "target=", "axis=")
             if any(k in x for x in links(lb))}
    rec("B-1", "표의 값 → 조건 추가", "링크 종류를 센다",
        f"{sorted(kinds)}", len(kinds) >= 2)

    # B-2 칩마다 × 로 하나씩
    st, cb, _h = ad.get("/listings?grade=B&target=KOLEOS_HEV")
    chips = re.findall(r'<span class="chip">(.*?)</span>', cb, re.S)
    xs = [x for x in links(cb) if "listings?" in x]
    one_left = any("grade=B" in x and "target" not in x for x in xs) or \
        any("target=KOLEOS_HEV" in x and "grade" not in x for x in xs)
    rec("B-2", "칩마다 × 로 하나씩", "× 링크를 본다",
        f"칩 {len(chips)} · 하나만 남는 링크={one_left}",
        len(chips) >= 2 and one_left)

    # B-3 가격 상·하한은 칩 하나
    st, pb, _h = ad.get("/listings?price_min=1000&price_max=99000000")
    price_chips = len(re.findall(r'price_(?:min|max)\s*\d|최저가|최고가',
                                 text(pb)))
    rec("B-3", "가격 상·하한은 칩 하나", "칩 수를 센다",
        f"가격 칩 {price_chips}", price_chips <= 1,
        "× 하나로 둘 다 빠져야 한다")

    # B-4 전부 지우기
    rec("B-4", "「전부 지우기」", "링크를 본다",
        "있음" if "전부 지우기" in text(cb) else "없음",
        "전부 지우기" in text(cb))

    # B-5 조건 없으면 안내
    rec("B-5", "조건 없으면 안내 문구", "빈 필터 화면",
        "안내 있음" if "필터 없음" in text(lb) else "빈칸",
        "필터 없음" in text(lb))

    # B-6 빈 결과 안내
    st, zb, _h = ad.get("/listings?grade=Z")
    rec("B-6", "빈 결과에 「필터를 하나 지워」", "결과 0건 화면",
        "안내 있음" if "필터를 하나" in text(zb) else text(zb)[-30:],
        "필터를 하나" in text(zb))

    # B-7 조건이 다음 행동으로
    carried = ('name="target_key" value="KOLEOS_HEV"' in cb
               and 'name="min_grade" value="B"' in cb)
    rec("B-7", "조건이 다음 행동 파라미터", "알림 폼을 본다",
        "실려 있음" if carried else "다시 입력해야 함", carried,
        "이 도구의 설계 핵심 (STEP 149g)")

    # B-8 「지금 조건으로」 문장
    box = "지금 조건으로" in text(cb)
    # ★ 조건 · 정렬 · 건수가 한 문장에 있는가
    sentence = bool(re.search(r"·\s*\S+순\s*·\s*[\d,]+건", text(cb)))
    rec("B-8", "「지금 조건으로」 문장", "상자를 읽는다",
        f"상자={box} · 문장={sentence}", box and sentence,
        "조건·정렬·건수가 문장이어야 한다")


# ── C  /why 9절 (STEP 149a · 149c) ──────────────────────────────────
WHY_SECTIONS = (
    ("C-1", "매물 요약", ("등급", "주행")),
    ("C-2", "무엇을 조회했는가", ("무엇을 조회했는가",)),
    ("C-3", "축별 판정", ("축별 판정",)),
    ("C-4", "왜 N순위인가", ("순위",)),
    ("C-5", "주요 옵션", ("주요 옵션", "옵션")),
    ("C-6", "비용", ("비용",)),
    ("C-7", "자동차이력정보", ("자동차이력정보", "이력")),
    ("C-8", "참고 자료", ("참고 자료",)),
    ("C-9", "확인 못 한 것", ("확인 못 한 것",)),
)


def spec_c(ad: Client, lid: int) -> None:
    print("\n[C] /why 9절 (STEP 149a · 149c)")
    st, wb, _h = ad.get(f"/why/{lid}")
    body = text(wb)
    for code, name, marks in WHY_SECTIONS:
        got = any(m in body for m in marks)
        rec(code, f"/why {name}", "절을 찾는다",
            "있음" if got else "없음", got)

    # C-3 은 17 Component 전부
    n = wb.count("<tr")
    rec("C-3b", "/why 17 Component 전부", "축 표 행을 센다",
        f"{n}행", n >= 17, "excluded 포함 전부여야 한다")

    # C-2 는 엔드포인트별 「무엇을 결정하는가」
    got = "결정" in body or "무엇을 주는가" in body
    rec("C-2b", "/why 엔드포인트가 무엇을 결정", "설명을 찾는다",
        "있음" if got else "받음/못 받음만", got)

    # C-10  절 순서 (개정 256).  ★ 있는지만 보면 순서가 바뀌어도 통과한다.
    #   「무엇을 조회했나 → 어떻게 판정했나 → 무엇이 빠졌나」가 읽는 순서다
    order = [h.split("<")[0].split("—")[0].strip()
             for h in re.findall(r"<h2[^>]*>(.*?)</h2>", wb, re.S)]
    want = ["무엇을 조회했는가", "축별 판정", "엔카 진단", "확인 못 한 것",
            "왜", "비용", "주요 옵션", "참고 자료"]
    seen, at = [], 0
    for w in want:
        hit = next((i for i, h in enumerate(order[at:], start=at)
                    if w in h), None)
        if hit is None:
            continue
        seen.append(w)
        at = hit + 1
    rec("C-10", "/why 절 순서가 규격 순서다", "h2 를 차례로 읽는다",
        f"{len(seen)}/{len(want)} · {' → '.join(seen[:4])}",
        len(seen) == len(want),
        "순서가 뒤바뀌면 규격을 먼저 고쳐야 한다 (개정 256)")


# ── D  「확인 못 한 것」 (STEP 149h) ─────────────────────────────────
def spec_d(ad: Client, db: str) -> None:
    print("\n[D] 확인 못 한 것 (STEP 149h)")
    lid = sqlite3.connect(db).execute(
        "SELECT listing_id FROM result_axis WHERE excluded=1 LIMIT 1"
    ).fetchone()
    if lid:
        st, wb, _h = ad.get(f"/why/{lid[0]}")
        body = text(wb)
        seg = body.split("확인 못 한 것")[-1][:400] if "확인 못 한 것" in body \
            else ""
        rec("D-1", "excluded 를 점수·사유와 함께", "그 절을 읽는다",
            seg[:44] or "절 없음",
            bool(re.search(r"\d+\s*점", seg)) and bool(seg))
        rec("D-2", "채웠을 때 비율·등급", "그 절을 읽는다",
            "있음" if re.search(r"채우면|최대", seg) else "없음",
            bool(re.search(r"채우면|최대", seg)))

    full = sqlite3.connect(db).execute(
        "SELECT s.listing_id FROM result_score s WHERE NOT EXISTS "
        "(SELECT 1 FROM result_axis a WHERE a.listing_id=s.listing_id "
        " AND a.excluded=1) LIMIT 1").fetchone()
    if full:
        st, wb, _h = ad.get(f"/why/{full[0]}")
        body = text(wb)
        got = "없습니다" in body and "확인 못 한 것" in body
        rec("D-4", "없을 때도 「없습니다」", "전 축 판정된 매물",
            "냄" if got else "절이 사라짐", got,
            "빼면 불합격 — 「확실한 것」을 가르는 절")
    else:
        rec("D-4", "없을 때도 「없습니다」", "해당 매물 없음", "건너뜀", True)


# ── F  관리자 메뉴 3분류 (STEP 149j) ────────────────────────────────
def spec_f(ad: Client, db: str) -> None:
    print("\n[F] 관리자 메뉴 (STEP 149j)")
    st, ab, _h = ad.get("/admin")
    groups = {g for g in ("운영", "조정", "탐색") if g in text(ab)}
    rec("F-1", "메뉴 3분류", "머리말을 본다", f"{sorted(groups)}",
        len(groups) == 3)

    conn = sqlite3.connect(db)
    conn.execute("INSERT INTO recalc_job(job_id,account_id,trigger,reason,"
                 "from_step,scope,status,queued_at) VALUES "
                 "('lock1',1,'manual','시험','S9','all','running','t')")
    conn.commit()
    st, ab, _h = ad.get("/admin")
    locked = "잠" in text(ab)
    st2, _b, _h = ad.get("/admin/audit")
    rec("F-2", "실행 중 조정만 잠김", "메뉴·탐색을 본다",
        f"잠금 표시={locked} · 탐색 {st2}", locked and st2 == 200)
    rec("F-3", "잠기는 이유를 화면에", "문구를 찾는다",
        "이유 있음" if re.search(r"도는 중|규칙이 바뀌", text(ab))
        else "이유 없음",
        bool(re.search(r"도는 중|규칙이 바뀌", text(ab))))
    conn.execute("DELETE FROM recalc_job WHERE job_id='lock1'")
    conn.commit()


# ── G  변경 화면 5단계 (STEP 149k) ──────────────────────────────────
def spec_g(ad: Client, root: str, db: str) -> None:
    print("\n[G] 변경 5단계 (STEP 149k)")
    st, sb, _h = ad.get("/admin/scoring")
    body = text(sb)

    rec("G-1", "① 현재 값 표시", "배점 화면", 
        "현재 점수 있음" if re.search(r"\d+\s*/\s*\d+|점수", body) else "없음",
        bool(re.search(r"점수", body)))
    rec("G-3", "③ 미리보기 (배점 필수)", "단추를 찾는다",
        "있음" if "미리보기" in body else "없음", "미리보기" in body)
    rec("G-4", "④ 사유 필수", "폼을 본다",
        "required" if 'name="reason"' in sb and "required" in sb else "없음",
        'name="reason"' in sb and "required" in sb)
    rec("G-7", "저장 못 하는 이유를 미리", "화면 안내",
        "미리 안내" if re.search(r"미리보기.{0,40}저장|사유.{0,20}필수",
                               body) else "누르면 알려줌",
        bool(re.search(r"미리보기.{0,40}저장|사유.{0,20}필수", body)),
        "눌러야 아는 것은 불합격")

    # ★ 실제로 바꾼 뒤 눌러 본다.  「이력이 없어 안 보이는 것」과
    #   「기능이 없는 것」은 다르다
    token = ad.csrf("/admin/config")
    ad.post("/admin/config",
            {"csrf": token, "previewed": "1", "file": "web.json",
             "key_path": "rows_per_page", "value": "160", "reason": "G-5"})
    st, hb, _h = ad.get("/admin")
    has = "되돌리기" in text(hb)
    rec("G-5", "⑤ 되돌리기가 화면에", "설정을 바꾼 뒤 본다",
        "단추 있음" if has else "없음", has)
    if has:
        cid = sqlite3.connect(db).execute(
            "SELECT change_id FROM config_change ORDER BY rowid DESC LIMIT 1"
        ).fetchone()[0]
        token = ad.csrf("/admin")
        st, _b, _l = ad.post("/admin/config",
                             {"csrf": token, "action": "revert",
                              "change_id": str(cid), "reason": "되돌린다"})
        with open(os.path.join(root, "config", "web.json"),
                  encoding="utf-8") as f:
            got = json.load(f)["rows_per_page"]
        n = sqlite3.connect(db).execute(
            "SELECT COUNT(*) FROM config_change").fetchone()[0]
        rec("G-8", "되돌리기는 이력에 2행", "눌러 본다",
            f"{st} · 값 {got} · 이력 {n}행",
            st in (302, 303) and got != 160 and n >= 2)


# ── H  위험한 행동 4단 (STEP 149l) ──────────────────────────────────
def spec_h(ad: Client) -> None:
    print("\n[H] 위험 4단 (STEP 149l)")
    st, ub, _h = ad.get("/admin/users")
    rec("H-2", "보통 — 사유 입력", "중지 폼",
        "사유 required" if 'name="reason"' in ub else "없음",
        'name="reason"' in ub)

    st, rb, _h = ad.get("/admin/run")
    got = bool(re.search(r"예상|시간|건", text(rb)))
    rec("H-3", "높음 — 영향 명시", "전 차종 수집",
        "영향 안내" if got else "없음", got)

    # H-4 최고 위험은 웹에 없어야 한다
    danger = []
    for path in ("/admin", "/admin/run", "/admin/tools", "/admin/users"):
        _s, b, _h2 = ad.get(path)
        for mark in ("db reset", "DB 초기화", "전면 재수집", "--full"):
            if mark in b and "없습니다" not in text(b)[:9999]:
                if f'value="{mark}"' in b or f">{mark}<" in b:
                    danger.append(f"{path}: {mark}")
    rec("H-4", "최고 위험은 웹에 없다", "단추를 찾는다",
        danger or "없음", not danger)

    rec("H-5", "무엇이 사라지는지 수치로", "중지 폼 안내",
        "수치 안내" if re.search(r"관심.{0,10}\d+건|남습니다", text(ub))
        else "없음",
        bool(re.search(r"관심.{0,10}\d+건|남습니다", text(ub))))
    rec("H-6", "덜 위험한 대안", "안내를 읽는다",
        "대안 있음" if re.search(r"중지|대신", text(ub)) else "없음",
        bool(re.search(r"중지|대신", text(ub))))


# ── J  판정 결과가 없을 때 (STEP 149) ───────────────────────────────
def spec_j(port: int) -> None:
    print("\n[J] 판정 없음 (STEP 149 · V11-11)")
    import shutil
    import tempfile
    import threading
    from http.server import HTTPServer

    from store.raw import open_db
    from web.app import make_app
    from web.server import make_handler

    root = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"),
                    os.path.join(root, "config"))
    for d in ("secrets", "web"):
        src = os.path.join(ROOT, d)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(root, d))
    db = os.path.join(root, "empty.db")
    open_db(db, os.path.join(ROOT, "sql", "ddl")).close()
    srv = HTTPServer(("127.0.0.1", 0),
                     make_handler(make_app(db, root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    c = Client(srv.server_address[1], "empty")
    try:
        for code, path in (("J-1", "/"), ("J-1b", "/listings")):
            st, b, _h = c.get(path)
            body = text(b)
            guided = "아직" in body or "수집하지" in body
            rec(code, f"{path} 빈 표가 아니라 안내", "빈 DB 로 연다",
                f"{st} · {'안내' if guided else '빈 표'}",
                st == 200 and guided, "빈 표·0건만이면 불합격")
        st, nb, _h = c.get("/notready")
        body = text(nb)
        for code, mark in (("J-2", "왜 멈추나"), ("J-3", "무엇을 하면 되나"),
                           ("J-4", "지금도 볼 수 있는 것")):
            rec(code, f"/notready {mark}", "절을 찾는다",
                "있음" if mark in body else "없음", mark in body)
    finally:
        srv.shutdown()


# ── M  관리 화면별 규격 (13장) ──────────────────────────────────────
def spec_m(ad: Client, db: str, root: str) -> None:
    print("\n[M] 관리 화면별 (13장)")
    st, rb, _h = ad.get("/admin/run")
    body = text(rb)
    rec("M-1", "사유 → 범위·예상시간 자동", "화면을 본다",
        "예상 표시" if re.search(r"예상|시간", body) else "없음",
        bool(re.search(r"예상|시간", body)))
    rec("M-2", "전 차종은 all 입력 확인", "폼을 본다",
        "확인 있음" if re.search(r"all", rb) else "없음", "all" in rb)
    rec("M-3", "진행 표시", "절을 찾는다",
        "있음" if "진행" in body else "없음", "진행" in body)
    rec("M-4", "중단 → 재개점", "단추를 찾는다",
        "있음" if "중단" in body else "없음", "중단" in body)

    st, sb, _h = ad.get("/admin/scoring")
    sbody = text(sb)
    rec("M-5", "합계≠total → 미리보기 불가", "안내를 찾는다",
        "안내 있음" if re.search(r"합계|저장할 수 없", sbody) else "없음",
        bool(re.search(r"합계", sbody)))
    rec("M-7", "미리보기에 등급 분포 변화", "미리보기 절",
        "있음" if re.search(r"등급 분포|바뀌는", sbody) else "없음",
        bool(re.search(r"등급 분포|바뀌는", sbody)))
    rec("M-8", "0점 거부 — 스킵을 쓴다", "안내를 찾는다",
        "있음" if "스킵" in sbody else "없음", "스킵" in sbody)

    st, qb, _h = ad.get("/admin/query")
    rec("M-9", "SELECT·WITH 만", "안내를 찾는다",
        "있음" if re.search(r"SELECT|읽기", text(qb)) else "없음",
        bool(re.search(r"SELECT|읽기", text(qb))))

    st, gb, _h = ad.get("/admin/registry")
    from store.admin import USAGE_VALUES

    shown = set(re.findall(r'<option value="(\w+)"', gb))
    rec("M-12", "분류 선택지 = 실제 허용값", "선택지를 본다",
        f"{len(shown)}종", bool(shown) and shown <= set(USAGE_VALUES))

    st, tb, _h = ad.get("/admin/targets")
    tbody = text(tb)
    rec("M-13", "국산 CarType.Y · 수입 .N", "화면을 본다",
        "구분 있음" if re.search(r"국산|수입|CarType", tbody) else "없음",
        bool(re.search(r"국산|수입|CarType", tbody)))
    rec("M-14", "추가는 확정 전 상태로", "안내를 본다",
        "있음" if re.search(r"확인 대기|pending", tbody) else "없음",
        bool(re.search(r"확인 대기|pending", tbody)))

    st, ob, _h = ad.get("/admin/tools")
    obody = text(ob)
    rec("M-16", "결과는 제안 — 자동 적용 안 함", "안내를 읽는다",
        "있음" if "제안" in obody else "없음", "제안" in obody)
    rec("M-17", "표본 미달이면 제안 안 함", "안내를 읽는다",
        "있음" if re.search(r"표본|미만", obody) else "없음",
        bool(re.search(r"표본|미만", obody)))

    st, qb2, _h = ad.get("/admin/requests")
    # ★ 「삭제하지 않습니다」 안내는 있어야 한다.  없어야 할 것은 단추다
    buttons = re.findall(r"<button[^>]*>([^<]*)</button>", qb2)
    has_delete = any("삭제" in b or "지우" in b for b in buttons) or \
        'value="delete"' in qb2
    rec("M-18", "삭제 기능이 없다", "단추를 찾는다",
        f"단추 {buttons}", not has_delete)

    st, db2, _h = ad.get("/admin/docs")
    rec("M-21", "문서를 화면에서 읽는다", "본문을 본다",
        f"{len(text(db2))}자", len(text(db2)) > 1000)


# ── E  관심 등록 (STEP 149i · 11장 111 · 117a) ──────────────────────
def spec_e(port: int, ad: Client, db: str, lid: int) -> None:
    print("\n[E] 관심 등록 (STEP 149i · 111 · 117a)")
    anon = Client(port, "e-anon")

    token = anon.csrf("/listings")
    st, ib, _l = anon.post("/watch/add", {"csrf": token,
                                          "listing_id": str(lid)})
    rec("E-1", "비로그인 관심 → 유도 화면", "＋ 관심을 누른다",
        f"{st}", st == 200, "403 이면 누른 것이 사라진다")

    body = text(ib)
    marks = [m for m in ("만", "등급", "km") if m in body]
    rec("E-2", "담으려던 대상을 보여 준다", "유도 화면을 읽는다",
        f"{marks}", len(marks) >= 2, "차종·가격·등급·연식·주행")

    # E-3 로그인 후 자동으로 담긴다
    nexts = re.findall(r'href="(/login\?next=[^"]+)"', ib)
    rec("E-3", "로그인 후 그 매물이 담긴다", "유도 링크를 본다",
        "next 있음" if nexts else "없음", bool(nexts),
        "다시 안 눌러도 돼야 한다")

    for code, path in (("E-4", "/listings"), ("E-4b", f"/why/{lid}"),
                       ("E-4c", "/market")):
        st, _b, _h = anon.get(path)
        rec(code, f"{path} 계정 없이 본다", "비로그인으로 연다", str(st),
            st == 200)

    # E-5 관심은 차량 단위
    from store.watch import watch_add  # noqa: F401

    cols = [r[1] for r in sqlite3.connect(db).execute(
        "PRAGMA table_info(watch_item)")]
    rec("E-5", "관심은 차량 단위", "표 컬럼을 본다",
        "vehicle_id" if "vehicle_id" in cols else "listing_id 단위",
        "vehicle_id" in cols, "매물이 내려가도 추적 유지")

    st, wb, _h = ad.get("/watch")
    rec("E-7", "조건 알림 — 매물이 아니라 조건", "절을 찾는다",
        "있음" if "조건 알림" in text(wb) else "없음",
        "조건 알림" in text(wb))


# ── I  계정 (STEP 149m · 149n · 13장 126) ───────────────────────────
def spec_i(port: int, ad: Client, db: str, root: str, lid: int) -> None:
    print("\n[I] 계정 (STEP 126 · 149m · 149n)")
    path = os.path.join(root, "config", "web.json")

    def policy(name: str) -> None:
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        blob["signup_policy"] = name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(blob, f, ensure_ascii=False, indent=2)

    seen = {}
    for name in ("open", "approval", "closed"):
        policy(name)
        st, jb, _h = Client(port, f"i-{name}").get("/join")
        seen[name] = text(jb)
    rec("I-1", "가입 정책 3종에 화면이 바뀐다", "세 정책을 본다",
        f"서로 다름={len(set(seen.values())) == 3}",
        len(set(seen.values())) == 3)
    rec("I-4", "closed — 가입 화면이 닫힌다", "closed 로 연다",
        "닫힘 안내" if "받지 않습니다" in seen["closed"] else "폼이 열림",
        "받지 않습니다" in seen["closed"])

    # I-2 · I-3  승인제
    policy("approval")
    u = Client(port, "i-pending")
    token = u.csrf("/join")
    st, b, _l = u.post("/join", {"csrf": token, "name": "규격대기",
                                 "secret": "pending12345",
                                 "secret2": "pending12345"})
    role = sqlite3.connect(db).execute(
        "SELECT role FROM account WHERE login_name='규격대기'").fetchone()
    rec("I-2", "approval — 승인 대기 상태가 있다", "신청한다",
        f"{st} · role={role and role[0]}",
        st in (302, 303) and role is not None and role[0] == "pending")

    st2 = u.login("규격대기", "pending12345")[0]
    token = u.csrf("/listings")
    st3, b3, _l = u.post("/watch/add", {"csrf": token,
                                        "listing_id": str(lid)})
    st4, _b, _h = u.get("/listings")
    rec("I-3", "승인 전 조회는 되고 등록만 막힘", "로그인 후 담아 본다",
        f"로그인 {st2} · 담기 {st3} · 조회 {st4}",
        st2 in (302, 303) and st3 == 403 and st4 == 200)

    st, ub, _h = ad.get("/admin/users")
    rec("I-2b", "「승인 대기」 절 · 승인 단추", "관리 화면을 본다",
        "있음" if "승인 대기" in text(ub) and "승인" in ub else "없음",
        "승인 대기" in text(ub))
    policy("open")

    # I-6 마지막 관리자
    me = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role='admin' "
        "AND disabled_at IS NULL LIMIT 1").fetchone()[0]
    token = ad.csrf("/admin/users")
    st, b, _l = ad.post("/admin/users",
                        {"csrf": token, "account_id": str(me),
                         "action": "disable", "reason": "규격 시험"})
    left = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM account WHERE role='admin' "
        "AND disabled_at IS NULL").fetchone()[0]
    rec("I-6", "마지막 관리자를 못 내린다", "자신을 중지",
        f"{st} · 남은 관리자 {left} · 대안={'있음' if '중지' in text(b) or st == 400 else '없음'}",
        left >= 1 and st in (400, 403, 409))

    # I-7 · I-8  임시 비밀번호
    token = ad.csrf("/admin/users")
    st, b, loc = ad.post("/admin/users",
                         {"csrf": token, "action": "create",
                          "name": "임시비번자", "role": "user",
                          "reason": "규격 시험"})
    st2, hb, _h = ad.get("/admin/users")
    temp = re.search(r"임시 비밀번호\s+(\S+)", text(hb))
    rec("I-7", "임시 비번은 한 번만 화면에", "계정을 만든다",
        "화면에 냄" if temp else "안 냄", bool(temp))

    if temp:
        tu = Client(port, "i-temp")
        tu.login("임시비번자", temp.group(1))
        st3, ob, _h = tu.get("/listings")
        st4, pb, _h = tu.get("/password")
        rec("I-8", "임시 비번 → 변경 강제", "다른 화면을 연다",
            f"/listings {st3} · /password {st4}",
            st3 in (302, 303) and st4 == 200)
        rec("I-9", "/password 는 강제 상태에서도 열림", "열어 본다",
            str(st4), st4 == 200)

    # I-11 · I-12
    lock = Client(port, "i-lock")
    last = ""
    for _i in range(12):
        _s, last, _l = lock.login("마스터", "틀린비번")
        if "시도가 많습니다" in last:
            break
    rec("I-11", "로그인 시도 상한", "11회 실패",
        "잠김" if "시도가 많습니다" in last else "안 잠김",
        "시도가 많습니다" in last)
    fresh = Client(port, "i-msg")
    _s, msg, _l = fresh.login("없는사람", "아무비번")
    rec("I-12", "실패 사유를 말하지 않는다", "없는 계정으로",
        "이름이나 비밀번호" if "이름이나 비밀번호" in msg else text(msg)[:24],
        "이름이나 비밀번호" in msg)


# ── K  오류 · 안전 (STEP 147 · 148 · 150) ───────────────────────────
def spec_k(port: int, ad: Client, lid: int) -> None:
    print("\n[K] 오류 · 안전 (STEP 147 · 148 · 150)")
    anon = Client(port, "k-anon")

    st, b, _h = anon.get("/why/99999999")
    stacky = "Traceback" in b or "File \"" in b
    rec("K-1", "오류 화면에 스택이 없다", "없는 매물",
        f"{st} · 스택={'있음' if stacky else '없음'}",
        not stacky and st == 404)
    # ★ 400 을 실제로 내는 요청으로 본다.  404 본문에서 찾으면 헛돈다
    st4, b4, _h4 = anon.get("/listings?page=abc")
    tail = text(b4).split("(/notready)")[-1]
    has_reason = bool(re.search(r"page|숫자|1 이상", tail))
    has_action = bool(re.search(r"확인|다시|돌아간다|시도", tail))
    rec("K-2", "도메인 예외 → 400 · 사유 + 조치", "잘못된 파라미터",
        f"{st4} · 사유={has_reason} · 조치={has_action}",
        st4 == 400 and has_reason and has_action)

    st, _b, _h = anon.get("/admin")
    rec("K-3", "권한 부족 → 403", "관리 화면", str(st), st == 403)

    for code, path, want in (
        ("K-4", "/listings?page=abc", 400),
        ("K-4b", "/listings?page=-1", 400),
        ("K-4c", "/why/abc", 404),
        ("K-7", "/static/../../secrets/plate_hmac.key", (400, 403, 404)),
    ):
        st, b, _h = anon.get(path)
        ok = st == want if isinstance(want, int) else st in want
        rec(code, f"{path[:28]}", "난입력", str(st), ok)

    st, b, _l = anon.post("/watch/add", {"listing_id": str(lid)})
    rec("K-6", "CSRF 없는 POST 거부", "토큰 없이", str(st),
        st in (400, 403))
    st, b, _l = anon.post("/watch/add", {"csrf": "한글토큰",
                                         "listing_id": str(lid)})
    rec("K-6b", "한글 CSRF 도 500 이 아니다", "위조 토큰", str(st),
        st in (400, 403))

    # K-8 쿠키에 role 문자열 없음
    got = ad.cookie
    rec("K-8", "쿠키에 role 문자열이 없다", "쿠키를 본다",
        got[:28], "admin" not in got and "role" not in got)

    # K-5 상태 변경이 GET 에 없다
    from web.routes import GET, POST, ROUTES

    bad = [r.path for r in ROUTES
           if GET in r.methods and POST not in r.methods
           and any(k in r.path for k in ("/add", "/delete", "/revert"))]
    rec("K-5", "상태 변경이 GET 에 없다", "라우팅 표", bad or "없음",
        not bad)


# ── L  성능 · 구조 (STEP 145b · 152) ────────────────────────────────
def spec_csrf(ad: Client, lid: int) -> None:
    """개정 308 — 같은 화면에서 여러 번 POST 가 되는가 (V11-99).

    ★ 마스터 실측 08-17 — 전 차종 수집에서 첫 묶음만 성공하고
      나머지 7개가 403 이었다.  토큰이 서버 메모리에 있어
      서비스를 재시작하면 열려 있던 화면의 토큰이 전부 무효가 된다
    ★ 시험이 한 번만 POST 했다.  연속으로 안 해 봤다 —
      시험은 실제 사용 패턴대로 한다.  전 차종은 16묶음이니 여러 번 보낸다
    """
    print("\n[CSRF] 한 화면에서 여러 번 POST (개정 308)")
    token = ad.csrf("/listings")
    codes = []
    for _i in range(5):
        st, _b, _l = ad.post("/watch/add",
                             {"csrf": token, "listing_id": str(lid)})
        codes.append(st)
    rec("V11-99", "같은 토큰으로 5번 연속 POST", "한 번 받은 토큰을 5번 쓴다",
        " · ".join(str(c) for c in codes), all(c != 403 for c in codes),
        "1회용이면 두 번째부터 403 이다")

    # ★ 토큰이 세션에서 만들어지므로 다시 열어도 같아야 한다
    again = ad.csrf("/listings")
    rec("V11-99b", "화면을 다시 열어도 같은 토큰", "두 번 읽어 견준다",
        "같다" if again == token else "바뀐다", again == token,
        "화면마다 토큰이 바뀌면 여러 탭이 서로를 무효로 만든다")


def spec_l(ad: Client) -> None:
    print("\n[L] 성능 · 구조 (STEP 145b · 152)")
    st, b, _h = ad.get("/listings")
    scripts = re.findall(r"<script[^>]*>", b)
    css = re.findall(r'href="([^"]*\.css)"', b)
    # ★ JS 자체가 금지가 아니다.  빌드 산출물과 바깥 주소가 금지다
    #   (STEP 145b · 개정 248 「바닐라·한 파일」 · 개정 277 data-peek)
    outside = [t for t in scripts if "src=" in t]
    rec("L-2", "빌드 산출물에 의존 안 함", "정적 자원을 센다",
        f"CSS {len(set(css))}장 · script {len(scripts)} (바깥 {len(outside)})",
        len(set(css)) <= 1 and not outside)

    st, cb, _h = ad.get("/static/app.css")
    literals = re.findall(r"#[0-9a-fA-F]{3,6}\b", cb)
    tokens = re.findall(r"--[\w-]+:\s*(#[0-9a-fA-F]{3,6})", cb)
    # ★ 시안이 쓴 색은 「늘린 색」이 아니다 — 시안이 정본이다 (개정 275).
    #   토큰 밖이면서 시안에도 없는 것만 결함이다
    sian = set()
    _sd = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "ref", "screens")
    if os.path.isdir(_sd):
        for _f in os.listdir(_sd):
            if _f.endswith(".html"):
                sian |= {c.lower() for c in re.findall(
                    r"#[0-9a-fA-F]{3,6}\b",
                    open(os.path.join(_sd, _f), encoding="utf-8").read())}
    outside = [x for x in literals
               if x not in tokens and x.lower() not in sian]
    rec("L-3", "토큰 밖 색값 없음", "CSS 를 훑는다",
        f"리터럴 {len(literals)} · 토큰 밖 {len(outside)}",
        not outside)

    st, hb, _h = ad.get("/")
    rec("L-4", "헤더 상태 표시", "꼬리를 본다",
        "버전 표시" if re.search(r"calc|dict|parse", text(hb)) else "없음",
        bool(re.search(r"calc", text(hb))))


# ── 몽키 — 규격에 없는 짓 (3절) ─────────────────────────────────────
def spec_monkey(port: int, ad: Client, db: str, lid: int) -> None:
    print("\n[몽키] 규격에 없는 짓")
    anon = Client(port, "m-anon")
    bad = []

    for path in ("/admin/없는화면", "/why/99999999", "/watch/99999",
                 "/listings?page=abc", "/listings?page=-1",
                 "/listings?order=이상값", "/listings?grade=Z",
                 "/static/../../secrets/plate_hmac.key",
                 "/listings?price_min=abc", "/why/-1"):
        st, b, _h = anon.get(path)
        if st == 500 or (st == 200 and not text(b)):
            bad.append(f"GET {path} → {st}")
    rec("몽키-①", "주소창 난입력", "10종을 넣는다",
        bad or "500·빈 화면 없음", not bad)

    bad = []
    token = ad.csrf("/admin/requests")
    for name, form in (
        ("빈 값", {"csrf": token, "action": "create", "title": "",
                  "body": "", "origin": "screen"}),
        ("공백만", {"csrf": token, "action": "create", "title": "   ",
                  "body": "  ", "origin": "screen"}),
        ("SQL 조각", {"csrf": token, "action": "create",
                    "title": "'; DROP TABLE account; --",
                    "body": "x", "origin": "screen"}),
        ("없는 출처", {"csrf": token, "action": "create", "title": "t",
                    "body": "x", "origin": "없는것"}),
    ):
        st, b, _l = ad.post("/admin/requests", form)
        if st == 500:
            bad.append(f"{name} → 500")
    alive = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM account").fetchone()[0]
    rec("몽키-②", "폼 난입력", "빈 값 · SQL 조각 등",
        bad or f"500 없음 · account {alive}행 살아 있음",
        not bad and alive > 0)

    bad = []
    for name, path, form in (
        ("사유 없이 저장", "/admin/config",
         {"previewed": "1", "file": "web.json",
          "key_path": "rows_per_page", "value": "111"}),
        ("미리보기 없이", "/admin/scoring",
         {"action": "component", "target": "taste.hud", "value": "22",
          "reason": "순서 어김"}),
    ):
        token = ad.csrf(path)
        st, b, _l = ad.post(path, {**form, "csrf": token})
        if st not in (400, 403, 409):
            bad.append(f"{name} → {st}")
    rec("몽키-③", "순서를 어겨서", "미리보기·사유 건너뜀",
        bad or "전부 400·403·409", not bad)

    # ④ 상태를 어겨서 — 중지된 계정으로 로그인
    from store.admin import create_account

    conn = sqlite3.connect(db)
    aid, _pw = create_account(conn, "중지될사람", "user",
                              "2026-08-15T00:00:00+00:00",
                              secret="disabled1234")
    conn.execute("UPDATE account SET disabled_at=? WHERE account_id=?",
                 ("2026-08-15T00:00:00+00:00", aid))
    conn.commit()
    off = Client(port, "m-off")
    st, b, _l = off.login("중지될사람", "disabled1234")
    st2, _b, _h = off.get("/watch")
    rec("몽키-④", "중지된 계정으로 로그인", "로그인해 본다",
        f"로그인 {st} · /watch {st2}", st2 in (302, 303, 403))


# ── S  역할별 흐름 — 「하려던 일을 끝까지 할 수 있나」 ────────────────
def flow_s1(port: int) -> None:
    """S-1 비로그인 — 「살 만한 차인지 알아본다」 12걸음."""
    print("\n[S-1] 비로그인 — 살 만한 차인지 알아본다")
    c = Client(port, "s1")
    st, home, _h = c.get("/")
    rec("S1-1", "/ 를 연다", "1걸음", str(st), st == 200)

    # 2  등급 분포에서 값이 있는 등급을 누른다
    page, picked = "", ""
    for cand in [x for x in links(home) if "grade=" in x]:
        _s, got, _h2 = c.get(cand)
        if re.search(r"/why/(\d+)", got):
            page, picked = got, cand
            break
    rec("S1-2", "등급 막대 → 목록", "2걸음",
        f"{picked} · 매물 {page.count('/why/')}건", bool(page))

    lid = re.search(r"/why/(\d+)", page)
    st, why, _h = c.get(f"/why/{lid.group(1)}") if lid else (0, "", {})
    body = text(why)
    rec("S1-3", "첫 매물의 「근거」", "3걸음", str(st), st == 200)

    # 4 · 5 · 7 은 「절만 있는 게 아니라 내용을 내는가」
    seg = body.split("무엇을 조회했는가")[-1][:300]
    rec("S1-4", "「무엇을 조회했는가」가 내용을 낸다", "4걸음",
        seg[:40] or "빈 절",
        bool(re.search(r"받음|미조회|못 받", seg)))

    seg5 = body.split("확인 못 한 것")[-1][:300]
    rec("S1-5", "「확인 못 한 것」이 내용을 낸다", "5걸음",
        seg5[:40] or "빈 절",
        bool(re.search(r"\d+\s*점|없습니다", seg5)))

    rec("S1-6", "「비용」에서 신차와 견준다", "6걸음",
        "있음" if "비용" in body else "없음", "비용" in body)

    seg7 = body.split("참고 자료")[-1][:200]
    rec("S1-7", "「참고 자료」가 내용을 낸다", "7걸음",
        seg7[:40] or "빈 절", bool(seg7.strip()))

    st, mk, _h = c.get("/market")
    rec("S1-8", "/market 시세 어디쯤", "8걸음", str(st), st == 200)

    bars = [x.replace("&amp;", "&") for x in links(mk) if "price_min=" in x]
    total = c.get("/listings")[1].count("/why/")
    got = c.get(bars[0])[1].count("/why/") if bars else total
    rec("S1-9", "막대를 눌러 그 구간 매물", "9걸음",
        f"전체 {total}행 → {got}행", bool(bars) and got < total)

    token = c.csrf("/listings")
    st, invite, _l = c.post("/watch/add",
                            {"csrf": token,
                             "listing_id": lid.group(1) if lid else "1"})
    rec("S1-10", "「＋ 관심」 → 유도 화면", "10걸음", str(st), st == 200)
    ibody = text(invite)
    rec("S1-11", "유도 화면에 차종 · 가격 · 등급", "11걸음",
        ibody[:44],
        sum(1 for m in ("만", "등급", "km") if m in ibody) >= 2)
    rec("S1-12", "「계정 만들기」", "12걸음",
        "있음" if "/join" in invite else "없음", "/join" in invite)


def flow_s2(port: int, ad: Client, db: str) -> None:
    """S-2 user1 — 「후보를 3대로 좁힌다」."""
    print("\n[S-2] user1 — 후보를 3대로 좁힌다")
    token = ad.csrf("/admin/users")
    ad.post("/admin/users", {"csrf": token, "action": "create",
                             "name": "규격사용자", "role": "user",
                             "secret": "usersecret1", "reason": "흐름 시험"})
    u = Client(port, "s2")
    st, _b, _l = u.login("규격사용자", "usersecret1")
    rec("S2-1", "로그인", "1걸음", str(st), st in (302, 303))

    # 2 · 3  칩 2개
    st, two, _h = u.get("/listings?grade=B&target=KOLEOS_HEV")
    chips = re.findall(r'<span class="chip">(.*?)</span>', two, re.S)
    rec("S2-2", "값을 눌러 칩 2개", "2·3걸음", f"칩 {len(chips)}",
        len(chips) >= 2)

    # 4  첫 칩의 × → 하나만 빠진다
    xs = re.findall(r'href="(/listings\?[^"]*)"[^>]*title="이 조건만', two)
    xs = xs or [x for x in links(two)
                if x.startswith("/listings?") and "=" in x]
    one = next((x for x in xs
                if ("grade=B" in x) != ("target=KOLEOS_HEV" in x)), "")
    rec("S2-4", "× 하나로 조건 하나만 빠진다", "4걸음",
        one or "없음", bool(one))

    st, sorted_, _h = u.get(
        "/listings?grade=B&target=KOLEOS_HEV&order=monthly")
    m = re.search(r"<p><strong>([^<]+)</strong></p>", sorted_)
    rec("S2-7", "조건·정렬·건수가 문장", "6·7걸음",
        m.group(1) if m else "없음",
        bool(m) and "월납입" in m.group(1))

    carried = ('name="target_key" value="KOLEOS_HEV"' in sorted_
               and 'name="min_grade" value="B"' in sorted_)
    rec("S2-8", "조건을 다시 입력하지 않는다", "8걸음",
        "폼에 실림" if carried else "다시 입력", carried,
        "STEP 149g — 이 도구의 설계 핵심")

    ids = [r[0] for r in sqlite3.connect(db).execute(
        "SELECT listing_id FROM result_score LIMIT 3")]
    for i in ids:
        token = u.csrf("/listings")
        u.post("/watch/add", {"csrf": token, "listing_id": str(i)})
    st, wb, _h = u.get("/watch")
    rec("S2-9", "3대를 관심 등록", "9걸음",
        f"{wb.count('/why/')}건", wb.count("/why/") >= 1)

    # ★ 화면에 실제로 보이는 행의 watch_id 를 쓴다.
    #   DB 에서 아무거나 고르면 다른 행을 눌러 놓고 「안 보인다」고 한다
    _s, wpage, _h = u.get("/watch")
    m = re.search(r'action="/watch/(\d+)"', wpage)
    wid = (int(m.group(1)),) if m else None
    if wid:
        token = u.csrf("/watch")
        u.post(f"/watch/{wid[0]}", {"csrf": token,
                                    "target_price_won": "32000000"})
        st2, again, _h = u.get("/watch")
        saved = sqlite3.connect(db).execute(
            "SELECT target_price_won FROM watch_item WHERE watch_id=?",
            (wid[0],)).fetchone()[0]
        # ★ 화면 표기는 만원 단위다.  DB 값과 화면을 함께 본다
        shown = "3,200만" in again
        rec("S2-10", "목표가가 저장되고 다시 열어도 있다", "10걸음",
            f"DB {saved} · 화면 {'보임' if shown else '없음'}",
            saved == 32000000 and shown)

    st, cmp_, _h = u.get("/compare?ids=" + ",".join(str(i) for i in ids))
    pct = len(re.findall(r"\d+\.\d\s*%", text(cmp_)))
    rec("S2-12", "분모가 달라도 비율로 견준다", "11·12걸음",
        f"비율 표시 {pct}곳", pct >= 1, "절대점수로 비교하면 불합격")

    other = Client(port, "s2-other")
    other.login("규격사용자", "usersecret1")
    token = u.csrf("/password")
    u.post("/password", {"csrf": token, "current": "usersecret1",
                         "secret": "newsecret12345",
                         "secret2": "newsecret12345"})
    st, _b, _h = other.get("/watch")
    rec("S2-15", "다른 창의 세션이 끊긴다", "14·15걸음", str(st),
        st in (302, 303, 403))


def flow_s5(port: int, ad: Client, db: str, root: str) -> None:
    """S-5 admin — 「하루를 운영한다」 중 ★ 12개."""
    print("\n[S-5] admin — 하루를 운영한다 (★ 12개)")
    st, home, _h = ad.get("/admin")
    body = text(home)
    todo = re.search(r"조치가 필요한 것(.{0,160})", body)
    rec("S5-2", "「조치가 필요한 것」이 무엇을 하라는지", "2걸음",
        (todo.group(1)[:44] if todo else "없음"),
        bool(todo) and bool(re.search(r"확인|실행|분류|정한다",
                                      todo.group(1) if todo else "")))

    st, rb, _h = ad.get("/admin/run")
    rec("S5-5", "범위·예상시간이 자동으로", "5걸음",
        "있음" if re.search(r"예상|시간", text(rb)) else "없음",
        bool(re.search(r"예상|시간", text(rb))))
    rec("S5-7", "진행 표시가 단계별로", "7걸음",
        "있음" if "진행" in text(rb) else "없음", "진행" in text(rb))

    # ★ 씨앗에 미실행 검사가 없으면 이 화면이 그것을 낼 줄 아는지 알 수 없다.
    #   실제로 한 줄 넣고 화면이 「미실행」으로 내는지 본다 (A-7 · S5-8)
    _c = sqlite3.connect(db)
    _c.execute(
        "INSERT INTO audit_validation(run_id, phase, code, expected, actual,"
        " passed, severity, checked_at, applicable)"
        " VALUES ('spec-ui','V0','V0-00','-','미실행',0,'warn',"
        "'2026-08-17T09:00:00+00:00',0)")
    _c.commit()
    _c.close()
    st, ab, _h = ad.get("/admin/audit")
    rec("S5-11", "안 돈 단계가 「미실행」", "11걸음",
        "미실행 표기" if "미실행" in ab else "없음", "미실행" in ab)

    from store.admin import USAGE_VALUES

    st, gb, _h = ad.get("/admin/registry")
    shown = set(re.findall(r'<option value="(\w+)"', gb))
    rec("S5-14", "선택지가 실제 허용값과 같다", "14걸음",
        f"{len(shown)}종", bool(shown) and shown <= set(USAGE_VALUES))

    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "action": "component",
                         "target": "taste.hud", "value": "26",
                         "reason": "미리 막히나"})
    rec("S5-16", "미리보기 없이 저장 → 미리 막힌다", "16걸음",
        f"{st} · {text(b)[:20]}", st in (400, 409))

    st, sb, _h = ad.get("/admin/scoring")
    rec("S5-17", "미리보기에 등급 분포 변화", "17걸음",
        "있음" if re.search(r"등급 분포|바뀌는", text(sb)) else "없음",
        bool(re.search(r"등급 분포|바뀌는", text(sb))))

    token = ad.csrf("/admin/config")
    ad.post("/admin/config",
            {"csrf": token, "previewed": "1", "file": "web.json",
             "key_path": "rows_per_page", "value": "165", "reason": "S5"})
    cid = sqlite3.connect(db).execute(
        "SELECT change_id FROM config_change ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]
    token = ad.csrf("/admin")
    st, b, _l = ad.post("/admin/config",
                        {"csrf": token, "action": "revert",
                         "change_id": str(cid), "reason": "되돌린다"})
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        got = json.load(f)["rows_per_page"]
    n = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    rec("S5-20", "값이 복원되고 이력이 2행", "19·20걸음",
        f"{st} · 값 {got} · 이력 {n}행",
        st in (302, 303) and got != 165 and n >= 2)

    token = ad.csrf("/admin/api")
    ad.post("/admin/api",
            {"csrf": token, "previewed": "1", "reason": "S5",
             "url": "https://api.encar.com/v1/s5"})
    sid = sqlite3.connect(db).execute(
        "SELECT snapshot_id FROM admin_api_snapshot "
        "ORDER BY rowid DESC LIMIT 1").fetchone()
    st, ob, _h = ad.get(f"/admin/api?snapshot={sid[0]}") if sid else (0, "",
                                                                     {})
    rec("S5-22", "저장 목록에서 다시 연다", "22걸음",
        f"{st} · {'열림' if 'originPrice' in ob else '안 열림'}",
        "originPrice" in ob)

    st, tb, _h = ad.get("/admin/tools")
    rec("S5-24", "결과가 「제안」 · 자동 적용 안 함", "24걸음",
        "있음" if "제안" in text(tb) else "없음", "제안" in text(tb))

    st, ub, _h = ad.get("/admin/users")
    rec("S5-26", "중지 시 영향 안내", "26걸음",
        "있음" if re.search(r"관심|남습니다", text(ub)) else "없음",
        bool(re.search(r"관심|남습니다", text(ub))))

    me = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role='admin' "
        "AND disabled_at IS NULL LIMIT 1").fetchone()[0]
    token = ad.csrf("/admin/users")
    st, b, _l = ad.post("/admin/users",
                        {"csrf": token, "account_id": str(me),
                         "action": "disable", "reason": "S5-29"})
    rec("S5-29", "마지막 관리자 중지 → 거부 · 대안", "28·29걸음",
        f"{st} · {text(b)[:24]}", st in (400, 403, 409))

    st, qb, _h = ad.get("/admin/requests")
    buttons = re.findall(r"<button[^>]*>([^<]*)</button>", qb)
    rec("S5-31", "삭제 단추가 없다", "31걸음", f"{buttons}",
        not any("삭제" in b or "지우" in b for b in buttons))

    st, db2, _h = ad.get("/admin/docs")
    rec("S5-32", "규격을 화면에서 읽는다", "32걸음",
        f"{len(text(db2))}자", len(text(db2)) > 1000)


def flow_s3(port: int, ad: Client, db: str) -> None:
    """S-3 user2 — 「남의 것을 건드릴 수 있나」 8걸음."""
    print("\n[S-3] user2 — 남의 것을 건드릴 수 있나")
    # 1  정책을 open 으로 (admin 이 화면에서)
    st, ub, _h = ad.get("/admin/users")
    rec("S3-1", "admin 이 정책을 open 으로", "1걸음",
        "정책 화면 있음" if "가입 정책" in text(ub) else "없음",
        "가입 정책" in text(ub))

    # 2 · 3  가입 → 로그인 → /watch
    u2 = Client(port, "s3-u2")
    token = u2.csrf("/join")
    st, b, _l = u2.post("/join", {"csrf": token, "name": "규격을",
                                  "secret": "usersecret2",
                                  "secret2": "usersecret2"})
    rec("S3-2", "/join 에서 가입", "2걸음", str(st), st in (302, 303))
    st2, _b, _l = u2.login("규격을", "usersecret2")
    st3, wb, _h = u2.get("/watch")
    rec("S3-3", "로그인 → /watch", "3걸음", f"{st2} · {st3}",
        st2 in (302, 303) and st3 == 200)

    # 4  남의 관심이 안 보인다
    mine = wb.count("/why/")
    others = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM watch_item WHERE closed_at IS NULL "
        "AND account_id <> (SELECT account_id FROM account "
        "                   WHERE login_name='규격을')").fetchone()[0]
    rec("S3-4", "남의 관심이 안 보인다", "4걸음",
        f"내 것 {mine}건 · 남의 것 {others}건", mine == 0 and others > 0)

    # 5  남의 watch_id 로 POST
    theirs = sqlite3.connect(db).execute(
        "SELECT watch_id, target_price_won FROM watch_item "
        "WHERE closed_at IS NULL ORDER BY rowid LIMIT 1").fetchone()
    if theirs:
        token = u2.csrf("/watch")
        st, b, _l = u2.post(f"/watch/{theirs[0]}",
                            {"csrf": token, "target_price_won": "1"})
        after = sqlite3.connect(db).execute(
            "SELECT target_price_won FROM watch_item WHERE watch_id=?",
            (theirs[0],)).fetchone()[0]
        rec("S3-5", "남의 watch_id 로 POST", "5걸음",
            f"{st} · 값 {theirs[1]} → {after}",
            st in (400, 403, 404) and after == theirs[1])

    # 6  같은 매물을 자기도 담는다 → 각자 보유
    lid = sqlite3.connect(db).execute(
        "SELECT l.listing_id FROM core_listing l JOIN watch_item w "
        "ON w.vehicle_id = l.vehicle_id LIMIT 1").fetchone()
    if lid:
        token = u2.csrf("/listings")
        st, b, _l = u2.post("/watch/add", {"csrf": token,
                                           "listing_id": str(lid[0])})
        n = sqlite3.connect(db).execute(
            "SELECT COUNT(DISTINCT account_id) FROM watch_item "
            "WHERE closed_at IS NULL").fetchone()[0]
        rec("S3-6", "같은 매물을 각자 보유", "6걸음",
            f"{st} · {n}명이 담고 있음", st in (302, 303) and n >= 2)

        # 7  같은 매물을 또 담는다 → 500 이 나면 안 된다
        token = u2.csrf("/listings")
        st, b, _l = u2.post("/watch/add", {"csrf": token,
                                           "listing_id": str(lid[0])})
        st2, wb2, _h = u2.get("/watch")
        guided = "이미" in text(wb2)
        rec("S3-7", "같은 매물을 또 담기", "7걸음",
            f"{st} · 안내={'있음' if guided else '없음'}",
            st in (302, 303) and st != 500,
            "500 이 나면 안 된다")

    # 8  /admin 직접 입력
    st, _b, _h = u2.get("/admin")
    rec("S3-8", "/admin 직접 입력", "8걸음", str(st), st == 403)


def flow_s4(port: int, ad: Client, db: str, root: str, lid: int) -> None:
    """S-4 user3 — 「승인제로 들어온다」 7걸음."""
    print("\n[S-4] user3 — 승인제로 들어온다")
    path = os.path.join(root, "config", "web.json")

    def policy(name: str) -> None:
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        blob["signup_policy"] = name
        with open(path, "w", encoding="utf-8") as f:
            json.dump(blob, f, ensure_ascii=False, indent=2)

    policy("approval")
    rec("S4-1", "admin 이 정책을 approval 로", "1걸음", "approval", True)

    u3 = Client(port, "s4-u3")
    st, jb, _h = u3.get("/join")
    body = text(jb)
    rec("S4-2", "/join 이 「승인제입니다」로 바뀐다", "2걸음",
        body[:44], "승인" in body)

    token = u3.csrf("/join")
    st, b, _l = u3.post("/join", {"csrf": token, "name": "규격병",
                                  "secret": "pending12345",
                                  "secret2": "pending12345"})
    row = sqlite3.connect(db).execute(
        "SELECT account_id, role FROM account "
        "WHERE login_name='규격병'").fetchone()
    rec("S4-3", "신청 → 계정이 만들어진다", "3걸음",
        f"{st} · role={row and row[1]}",
        st in (302, 303) and row is not None and row[1] == "pending")

    st2, _b, _l = u3.login("규격병", "pending12345")
    token = u3.csrf("/listings")
    st3, _b, _l = u3.post("/watch/add", {"csrf": token,
                                         "listing_id": str(lid)})
    st4, _b, _h = u3.get("/listings")
    rec("S4-4", "로그인은 되나 관심 등록은 안 된다", "4걸음",
        f"로그인 {st2} · 담기 {st3} · 조회 {st4}",
        st2 in (302, 303) and st3 == 403 and st4 == 200)

    st, ub, _h = ad.get("/admin/users")
    shown = "규격병" in ub and "승인 대기" in text(ub)
    rec("S4-5", "admin 이 「승인 대기」 절에서 본다", "5걸음",
        "보임" if shown else "안 보임", shown)

    if row:
        token = ad.csrf("/admin/users")
        st, b, _l = ad.post("/admin/users",
                            {"csrf": token, "account_id": str(row[0]),
                             "action": "approve", "reason": "승인"})
        got = sqlite3.connect(db).execute(
            "SELECT role FROM account WHERE account_id=?",
            (row[0],)).fetchone()[0]
        rec("S4-6", "승인 → 역할이 user 로", "6걸음", f"{st} · {got}",
            got == "user")

        # 7  관심을 담는다 → 된다
        u3b = Client(port, "s4-u3b")
        u3b.login("규격병", "pending12345")
        token = u3b.csrf("/listings")
        st, b, _l = u3b.post("/watch/add", {"csrf": token,
                                            "listing_id": str(lid)})
        n = sqlite3.connect(db).execute(
            "SELECT COUNT(*) FROM watch_item WHERE account_id=?",
            (row[0],)).fetchone()[0]
        rec("S4-7", "승인 뒤 관심을 담는다", "7걸음", f"{st} · {n}건",
            st in (302, 303) and n >= 1)
    policy("open")


def flow_s6(port: int) -> None:
    """S-6 판정 없는 상태 — 「처음 켰을 때」 5걸음."""
    print("\n[S-6] 판정 없는 상태 — 처음 켰을 때")
    import shutil
    import tempfile
    import threading
    from http.server import HTTPServer

    from store.raw import open_db
    from web.app import make_app
    from web.server import make_handler

    root = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"),
                    os.path.join(root, "config"))
    for d in ("secrets", "web"):
        src = os.path.join(ROOT, d)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(root, d))
    db = os.path.join(root, "s6.db")
    open_db(db, os.path.join(ROOT, "sql", "ddl")).close()
    srv = HTTPServer(("127.0.0.1", 0), make_handler(make_app(db, root)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    c = Client(srv.server_address[1], "s6")
    try:
        rec("S6-1", "DB 를 비우고 서버를 켠다", "1걸음", "기동", True)

        for code, path, step in (("S6-2", "/", "2걸음"),
                                 ("S6-3", "/listings", "3걸음")):
            st, b, _h = c.get(path)
            body = text(b)
            guided = bool(re.search(r"아직|수집하지|판정하지", body))
            zero_only = ("0건" in body and not guided)
            rec(code, f"{path} 빈 화면이 아니라 안내", step,
                f"{st} · {'안내' if guided else ('0건만' if zero_only else '빈 표')}",
                st == 200 and guided, "빈 표·0건만이면 불합격")

        st, nb, _h = c.get("/notready")
        body = text(nb)
        steps = re.findall(r"<li>", nb)
        rec("S6-4", "/notready 에서 무엇을 하면 되는지", "4걸음",
            f"{st} · 조치 {len(steps)}개",
            st == 200 and "무엇을 하면 되나" in body and len(steps) >= 2)

        # 5  그 순서대로 하면 판정이 나온다 — 첫 조치가 실행 가능한가
        first = re.search(r"무엇을 하면 되나(.{0,120})", body)
        runnable = bool(first and re.search(r"run\.py|수집|collect",
                                            first.group(1)))
        rec("S6-5", "그 순서대로 하면 판정이 나온다", "5걸음",
            (first.group(1)[:44] if first else "없음"), runnable,
            "무엇을 치면 되는지 적혀 있어야 한다")
    finally:
        srv.shutdown()


# ── 가이드 v132 검사 4건 — 재현 방지 ────────────────────────────────
def guide_v132(port: int, ad: Client, db: str, root: str, lid: int) -> None:
    print("\n[가이드 v132] 4건 재현 방지")

    # ① 전 차종 수집에 확인 절차 (M-2 · H-3 · STEP 149l)
    st, rb, _h = ad.get("/admin/run")
    body = text(rb)
    rec("가이드-2a", "전 차종이 기본 선택이 아니다", "라디오를 본다",
        "기본 아님" if 'value="all" checked' not in rb else "기본 선택",
        'value="all" checked' not in rb,
        "잘못 누르면 몇 시간이 그냥 돈다")
    rec("가이드-2b", "영향을 수치로 명시", "안내를 읽는다",
        "시간 표시" if re.search(r"약\s*[\d.]+\s*시간", body) else "없음",
        bool(re.search(r"약\s*[\d.]+\s*시간", body)))

    picks = re.findall(r'<option value="([^"]+)"', rb)
    reason = picks[0] if picks else "dictionary"
    token = ad.csrf("/admin/run")
    st, b, _l = ad.post("/admin/run",
                        {"csrf": token, "previewed": "1", "scope": "all",
                         "reason": reason})
    rec("가이드-2c", "확인 문구 없이 전 차종 → 거부", "confirm 없이",
        f"{st} · {text(b).split('(/notready)')[-1][:26]}", st == 400)

    token = ad.csrf("/admin/run")
    st, b, _l = ad.post("/admin/run",
                        {"csrf": token, "previewed": "1", "scope": "all",
                         "confirm": "all", "reason": reason})
    rec("가이드-2d", "all 을 입력하면 시작한다", "confirm=all",
        str(st), st in (302, 303))
    conn = sqlite3.connect(db)
    conn.execute("UPDATE recalc_job SET status='done'")
    conn.commit()

    # ② 「지금 조건으로」가 축·구간을 넘긴다 (B-7 · STEP 149g)
    token = ad.csrf("/admin/users")
    ad.post("/admin/users", {"csrf": token, "action": "create",
                             "name": "축조건자", "role": "user",
                             "secret": "usersecret9", "reason": "B-7"})
    u = Client(port, "g-b7")
    u.login("축조건자", "usersecret9")
    st, lb, _h = u.get("/listings?axis=taste.hud&bucket=1&target=KOLEOS_HEV")
    fields = dict(re.findall(
        r'name="(axis|bucket|target_key|min_grade)" value="([^"]*)"', lb))
    rec("가이드-3a", "축·구간이 폼에 실린다", "목록에서 축을 걸고 본다",
        f"{fields}",
        fields.get("axis") == "taste.hud" and fields.get("bucket") == "1",
        "문장에 적고 폼에 안 실으면 어긋난다")

    # ★ 차종·축을 시험에 박지 않는다.  씨앗에 실제로 갈리는 축을 골라 건다 —
    #   개정 292 로 축이 통째로 바뀌자 「없는 차종」을 걸고 있었다
    conn = sqlite3.connect(db)
    ver = conn.execute(
        "SELECT MAX(calc_version) FROM result_score").fetchone()[0]
    pick = conn.execute(
        "SELECT l.target_key, a.axis FROM result_axis a"
        " JOIN core_listing l USING(listing_id)"
        " WHERE a.calc_version=? AND a.excluded=0"
        " GROUP BY l.target_key, a.axis"
        " HAVING COUNT(DISTINCT CASE WHEN a.value>0 THEN 1 ELSE 0 END)=2"
        " LIMIT 1", (ver,)).fetchone() or ("G80_25T", "taste.hud")
    token = u.csrf("/watch")
    st, b, _l = u.post("/watch/add",
                       {"csrf": token, "kind": "query",
                        "name": "조건 있는 차", "target_key": pick[0],
                        "axis": pick[1], "bucket": "1"})
    from store.watch import run_watch_queries

    hits = run_watch_queries(conn, ver, "2026-08-15T00:00:00+00:00")
    total = conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE calc_version=?",
        (ver,)).fetchone()[0]
    got = sum(hits.values())
    rec("가이드-3b", f"「{pick[1]} 있는 차」 조건이 실제로 걸린다", "알림을 돌린다",
        f"{got}건 / 전체 {total}건", 0 < got < total,
        "전건이면 조건이 안 걸린 것이다")

    # ③ 마지막 관리자 거부에 대안 (I-6b · STEP 149m)
    me = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role='admin' "
        "AND disabled_at IS NULL LIMIT 1").fetchone()[0]
    token = ad.csrf("/admin/users")
    st, b, _l = ad.post("/admin/users",
                        {"csrf": token, "account_id": str(me),
                         "action": "disable", "reason": "대안 확인"})
    tail = text(b).split("(/notready)")[-1]
    has_alt = bool(re.search(r"다른 계정|관리자로 올린|비밀번호를 바꾸", tail))
    rec("가이드-4", "마지막 관리자 거부에 대안", "자신을 중지",
        tail[:60], st in (400, 403, 409) and has_alt,
        "「절차를 마친 뒤」는 마칠 절차가 없으면 갇힌다")
    _ = (root, lid)


def main() -> int:
    srv, port, root, db = start_server()
    try:
        name, pw = seed_admin(db)
        ad = Client(port, "admin")
        ad.login(name, pw)
        lid = sqlite3.connect(db).execute(
            "SELECT listing_id FROM result_score LIMIT 1").fetchone()[0]

        print("규격 기준 통합 테스트 — 지시서가 요구한 것을 화면에서 찾는다")
        spec_a(ad, lid)
        spec_b(ad)
        spec_c(ad, lid)
        spec_d(ad, db)
        spec_f(ad, db)
        spec_g(ad, root, db)
        spec_h(ad)
        spec_m(ad, db, root)
        spec_csrf(ad, lid)
        spec_e(port, ad, db, lid)
        spec_i(port, ad, db, root, lid)
        spec_k(port, ad, lid)
        spec_l(ad)
        spec_monkey(port, ad, db, lid)
        spec_j(port)
        flow_s1(port)
        flow_s2(port, ad, db)
        flow_s3(port, ad, db)
        flow_s4(port, ad, db, root, lid)
        flow_s5(port, ad, db, root)
        flow_s6(port)
        guide_v132(port, ad, db, root, lid)
    finally:
        srv.shutdown()

    print()
    print(f"항목 {len(ROWS)} · 합격 {len(ROWS) - len(FAIL)} · "
          f"불합격 {len(FAIL)}")
    for f in FAIL:
        print("  ✗", f)
    _write()
    return 1 if FAIL else 0


def _write() -> None:
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "규격기준_결과표.md"), "w",
              encoding="utf-8") as f:
        f.write("| # | 규격 조항 | 무엇을 했나 | 무엇이 나왔나 | 합/불 |\n")
        f.write("|:--:|---|---|---|:--:|\n")
        for code, spec, did, got, mark, _why in ROWS:
            f.write(f"| {code} | {spec} | {did} | {got} | **{mark}** |\n")
        f.write(f"\n**항목 {len(ROWS)} · 합격 {len(ROWS) - len(FAIL)} · "
                f"불합격 {len(FAIL)}**\n")


if __name__ == "__main__":
    sys.exit(main())








