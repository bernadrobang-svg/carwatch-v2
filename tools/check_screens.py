# -*- coding: utf-8 -*-
"""화면 ↔ 시안 대조 (10장 · 14장).

지시서   ref/screens/README.md — 「시안이 화면 규격의 정본이다」
근거     ★ 구현이 시안과 다르면 시안을 먼저 고친다.
         코드가 시안보다 먼저 가면 안 된다
금지     시안을 안 보고 화면을 만드는 것 — 실제로 그렇게 만들어 다시 했다
사용     python3 tools/check_screens.py [carwatch.db]
"""
from __future__ import annotations

import io
import os
import re
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENS = os.path.join(ROOT, "ref", "screens")
TEMPLATES = os.path.join(ROOT, "web", "templates")

# 시안 파일 ↔ 우리 템플릿
def _pairs() -> tuple:
    """시안 ↔ 템플릿 짝을 디렉터리에서 만든다.

    ★ 손으로 나열하지 않는다 (D-2).  실측: 15쌍만 적혀 있어 시안 8개가
      검사 밖에 있었다 — admin_api · admin_config · admin_query ·
      admin_registry · admin_requests · admin_scoring · admin_targets ·
      admin_tools 가 대조된 적이 없다
    규칙   v2_{이름}_시안.html → {이름}.html
           없으면 admin_ 접두를 뗀 이름으로 한 번 더 본다 (admin_run → run)
    """
    out = []
    # ★★★ 08-26 — ★ 마스터께서 ★ v4m 을 확정하셨다 (「★ 그래 관심 이걸로 가자」).
    #   ★ ★ **같은 이름의 옛 판(v3)은 안 본다.**  ★ 새 판이 정본이다
    #   ★ ★ 안 그러면 ★ 새 시안대로 고칠 때마다 ★ 옛 시안이 ★ 빨간불을 낸다 —
    #     ★ 실측 08-26 — ★ `admin` · `dashboard` · `notready` 아홉 곳이 그랬다
    newest: dict = {}
    for f in sorted(os.listdir(SCREENS)):
        if not (f.endswith("_시안.html") and "_" in f):
            continue
        nm = f[f.index("_") + 1:-len("_시안.html")]
        ver = f[:f.index("_")]
        # ★ 판 이름은 ★ 글자로 견준다 — ★ v4m > v3 > v2
        if nm not in newest or ver > newest[nm][0]:
            newest[nm] = (ver, f)
    for f in sorted(x[1] for x in newest.values()):
        name = f[f.index("_") + 1:-len("_시안.html")]
        for cand in (f"{name}.html", f"{name.removeprefix('admin_')}.html"):
            if os.path.isfile(os.path.join(TEMPLATES, cand)):
                out.append((f, cand))
                break
        else:
            out.append((f, f"{name}.html"))   # 없는 것도 낸다 — 실패로 잡힌다
    return tuple(out)


PAIRS: tuple[tuple[str, str], ...] = _pairs()

# 시안에만 있고 우리 화면에 없으면 안 되는 문구.  ★ 「무엇을 하면 되나」다
KEY_PHRASES: dict[str, tuple[str, ...]] = {
    # ★ 개정 303·304 로 바뀌었다 — 「강점 태그 나열이 아니라 문장 하나」이고
    #   축 설명은 상세(/why)로 보낸다.  시안(개정 278)은 그 앞의 판이다.
    #   docs 가 정본이므로 시안을 따르지 않는다 (규칙 1)
    # ★★★★★ 09-01 — ★ **화면이 통째로 바뀌었다** (`docs/RECOMMEND_SCREEN.md`).
    #   ★ 마스터 확정 — 「★ 추천은 여러 탭으로 · ★ 1번 탭은 ★ **등급 무시하고**
    #     ★ 예산·주행·연식·색 ★ **네 축의 합(297)으로 세운다**」
    #   ★★ 그러므로 ★ 옛 문구 ★ 「**점수순이 아닙니다**」는 ★ **이제 거꾸로다** —
    #     ★ ★ 탭 1 은 ★ 점수순이 맞다.  ★ 그것이 마스터께서 시키신 것이다.
    #   ★★ ★ 「왜 이 순위인가」의 뜻은 ★ 살린다 — ★ 규격이 「★ 화면에 네 축의 점수를
    #     ★ ★ 따로 보인다 — ★ 그래야 **왜 위에 있는지** 마스터께서 아신다」라 한다.
    #   ★ 옛 화면은 ★ 안 지웠다 (`web/views.py:_recommend_old` · 개정 427)
    "recommend.html": ("네 축의 합", "등급을 보지 않습니다"),
    "listings.html": ("조건에 맞는 매물이 없습니다", "분모"),
    "why.html": ("확인 못 한 것", "분모"),
    "dealers.html": ("차량 판정에 들어가지 않습니다", "표본 부족"),
    "compare.html": ("분모",),
    "notready.html": ("무엇을 하면", "조치"),
    "watch.html": ("목표가", "가격"),
    "market.html": ("연식", "중앙"),
    "join.html": ("계정 없이도", "로그인"),
    "admin_users.html": ("0명으로 만들 수 없습니다", "삭제가 아닙니다"),
    "login.html": ("CLI 에서만", "누구나 관리자"),
}

FAIL: list[str] = []


def say(name: str, ok: int, bad: list) -> None:
    print(f"{name:30} {'통과' if not bad else '실패'}  "
          f"통과 {ok} · 실패 {len(bad)}")
    for b in bad[:40]:
        print(f"      ✗ {b}")
    if bad:
        FAIL.append(f"{name}({len(bad)})")


def _text(path: str) -> str:
    body = io.open(path, encoding="utf-8").read()
    body = re.sub(r"<style.*?</style>|<script.*?</script>", "", body,
                  flags=re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body))


def check_pairs() -> None:
    """시안이 있는데 템플릿이 없는가."""
    ok, bad = 0, []
    for sketch, tpl in PAIRS:
        if not os.path.isfile(os.path.join(SCREENS, sketch)):
            bad.append(f"시안 없음: {sketch}")
        elif not os.path.isfile(os.path.join(TEMPLATES, tpl)):
            bad.append(f"템플릿 없음: {tpl}  (시안은 있다)")
        else:
            ok += 1
    say("시안 ↔ 템플릿 짝", ok, bad)


def check_phrases() -> None:
    """★ 시안의 「무엇을 하면 되나」가 화면에 있는가."""
    ok, bad = 0, []
    for tpl, phrases in KEY_PHRASES.items():
        path = os.path.join(TEMPLATES, tpl)
        if not os.path.isfile(path):
            bad.append(f"{tpl}: 없음")
            continue
        body = io.open(path, encoding="utf-8").read()
        for p in phrases:
            if p in body:
                ok += 1
            else:
                bad.append(f"{tpl}: 「{p}」가 없다")
    say("시안 핵심 문구", ok, bad)


RE_HEAD = re.compile(r"<h[23][^>]*>(.*?)</h[23]>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
RE_VAR = re.compile(r"\{\{.*?\}\}|\{%.*?%\}", re.S)
RE_NUM = re.compile(r"[\d,]+")
# 제목 대조에 쓰는 앞자리.  ★ 짧은 제목(「응답」·「예제」)도 있어 4 자다
HEAD_PREFIX = 4


# ★ v3 시안은 ★ 절을 `<div class="v3-lbl">1 판정</div>` 으로 적는다 (개정 631).
#   ★ 마스터 ㉮ (r672) — ★ 시안 쪽에만 `.v3-` 을 붙였다.  ★ 옛 `lbl` 도 받는다
#   ★ `<h2>` 는 ★ 화면 이름과 ★ 「지켜야 하는 것」 메모다 — ★ 절이 아니다
RE_LBL = re.compile(r'<div class="(?:v3-|v4-|v4m-)?lbl">([^<]+)</div>')
SIAN_NOTE = ("지켜야 하는 것",)


def _sian_heads(html: str, v3: bool = False) -> list:
    """시안의 절.  ★ v3 는 `.v3-lbl` · ★ 옛 판은 `h2`·`h3` 다.

    ★★ v3 시안에서 ★ `h2`·`h3` 로 물러서지 않는다 — ★ 위 주석대로
      ★ v3 의 `h2` 는 ★ 화면 이름·틀 설명이지 ★ 절이 아니다.
      ★ 실측 08-24 — ★ 물러선 탓에 ★ `compare.html` 에 ★ 「상세 — 와이드」
      절이 없다고 ★ 헛잡았다.  ★ 그것은 ★ 시안이 곁에 그려 둔 ★ 상세 화면의
      ★ 이름표다.  ★ v3 시안이 `.v3-lbl` 을 안 쓰면 ★ 절을 안 밝힌 것이다
    ★ 옛 판 시안은 ★ 전부 지워졌다 (요구 73 — v2 24개) — ★ 물러섬은 남겨 둔다
    """
    got = [" ".join(RE_NUM.sub(" ", x).split()) for x in RE_LBL.findall(html)]
    got = [x for x in got if x]
    if got or v3:
        return got
    return [x for x in _heads(html)
            if not any(x.startswith(n) for n in SIAN_NOTE)]


def _heads(html: str, strip_vars: bool = False) -> list:
    """h2 · h3 의 글자만 뽑는다.

    ★ 태그와 값 자리를 지운다.  시안은 「등급 분포 203건」처럼 실측 수를
      품는데, 그 수를 템플릿에 적으면 안 된다 — 수는 DB 가 정본이다
    """
    out = []
    for raw in RE_HEAD.findall(html):
        s = raw
        if strip_vars:
            s = RE_VAR.sub(" ", s)
        s = RE_TAG.sub(" ", s)
        s = RE_NUM.sub(" ", s)
        s = " ".join(s.split())
        if s:
            out.append(s)
    return out


def check_sections() -> None:
    """★ 시안의 절이 화면에 다 있는가 (D-2 · G-1).

    짝만 맞추면 파일이 있다는 것밖에 모른다.  실측 08-15: 짝 검사는
    전건 통과인데 절은 54개가 비어 있었다 — 「무엇을 조회했는가」처럼
    사람이 판단에 쓰는 절이 통째로 없었다
    """
    ok, bad = 0, []
    for sketch, tpl in PAIRS:
        sp, tp = os.path.join(SCREENS, sketch), os.path.join(TEMPLATES, tpl)
        if not (os.path.isfile(sp) and os.path.isfile(tp)):
            continue
        mine = _heads(io.open(tp, encoding="utf-8").read(), strip_vars=True)
        for head in _sian_heads(io.open(sp, encoding="utf-8").read(),
                                v3=sketch.startswith(("v3_", "v4"))):
            # ★★ v4m 시안이 ★ 가운데 절을 ★ 「… 4~10절 (…)」로 ★ 줄여 적는다.
            #   ★ ★ 그것은 ★ 절 이름이 아니라 ★ 「여기 적기를 줄였다」는 표시다
            if head.startswith(("…", "...")):
                continue
            key = head[:HEAD_PREFIX]
            if any(key in m for m in mine):
                ok += 1
            else:
                bad.append(f"{tpl}: 「{head[:24]}」 절이 없다")
    say("시안 절 대조", ok, bad)


def check_nav() -> None:
    """시안의 상단 메뉴 9개가 라우팅 표에 다 있는가."""
    sys.path.insert(0, ROOT)
    from web.routes import ROUTES

    # ★★ `v2_dashboard_시안.html` 을 박아 두었다가 ★ 그 파일이 지워지자 터졌다
    #   (개정 634 — 가이드가 v2 24개를 지웠다).  ★ 있는 시안을 다 읽는다
    txt = " ".join(_text(os.path.join(SCREENS, f))
                   for f in sorted(os.listdir(SCREENS))
                   if f.endswith("_시안.html"))
    labels = ("현황", "후보", "매물", "관심", "비교", "시세", "딜러", "관리")
    from web.app import LABELS

    have = set(LABELS.values()) | {"현황", "관리"}
    bad = [f"메뉴 「{n}」가 라우팅 표에 없다" for n in labels
           if n in txt and n not in have]
    say("상단 메뉴", len(labels) - len(bad), bad)
    _ = ROUTES


def check_render(db: str) -> None:
    """★ 실제로 도는가.  시안대로 만들어도 안 돌면 소용없다."""
    sys.path.insert(0, ROOT)
    from contracts import ANONYMOUS, Account
    from web.routes import NON_SCREEN_VIEWS, ROLE_ADMIN, ROLE_USER, ROUTES
    from web.views import HANDLERS

    conn = sqlite3.connect(db)
    ok, bad = 0, []
    for route in ROUTES:
        fn = HANDLERS.get(route.view)
        # ★ 화면이 아닌 것은 건너뛴다 — 파일을 준다.  <h1> 이 없는 것이 맞다
        if (fn is None or "GET" not in route.methods
                or route.view in NON_SCREEN_VIEWS):
            continue
        who = {ROLE_ADMIN: Account(1, ROLE_ADMIN, "마스터"),
               ROLE_USER: Account(2, ROLE_USER, "사용자")}.get(route.role,
                                                            ANONYMOUS)
        try:
            status, _h, body = fn(conn, who, {"query": {}}, path_vars={
                "listing_id": "1"})
        except Exception as e:                              # noqa: BLE001
            bad.append(f"{route.path}: {type(e).__name__}: {e}"[:70])
            continue
        html = body.decode("utf-8")
        if status != 200:
            bad.append(f"{route.path}: {status}")
        elif "<h1>" not in html:
            bad.append(f"{route.path}: 제목이 없다")
        else:
            ok += 1
    say("전 화면 렌더", ok, bad)


def main() -> int:
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT,
                                                            "carwatch.db")
    check_pairs()
    check_phrases()
    check_sections()
    check_nav()
    if os.path.isfile(db):
        check_render(db)
    else:
        print(f"{'전 화면 렌더':30} 건너뜀  ({db} 없음)")
    print()
    print("결과:", "통과" if not FAIL else "실패 — " + " / ".join(FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
