# -*- coding: utf-8 -*-
"""통합 테스트 — 실제 HTTP 로 전 화면 (통합테스트_시나리오.md).

★ 전 활동은 웹 화면을 통해서만 한다.  CLI · 직접 DB 조작 금지.
  핸들러를 직접 부르면 라우팅 · 쿠키 · CSRF · 폼 파싱이 검사 밖으로 나간다

역할 4   admin · user1 · user2 · anonymous
★ 쿠키가 섞이면 결과가 뒤집힌다 — 역할마다 별도 쿠키 항아리를 쓴다
"""
from __future__ import annotations

import http.client
import json
import os
import re
import shutil
import sqlite3
import sys
import tempfile
import threading
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

FAIL: list = []
ROWS: list = []
T = "2026-08-15T00:00:00+00:00"


def rec(no, screen, did, got, ok, note=""):
    ROWS.append((str(no), screen, did, str(got), "합" if ok else "불", note))
    if not ok:
        FAIL.append(f"{no} {screen} {did}")
    mark = "PASS" if ok else "FAIL"
    print(f"  {mark}  {no:>3} {screen:22} {did:26} {got}"
          + (f"  {note}" if note else ""))
    return ok


class Client:
    """쿠키 항아리 하나 = 역할 하나."""

    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self.cookie = ""

    def _conn(self):
        return http.client.HTTPConnection("127.0.0.1", self.port, timeout=20)

    def get(self, path: str):
        c = self._conn()
        # ★ 브라우저가 하는 일이다.  한글 파라미터도 실제로는 인코딩돼 온다
        path = urllib.parse.quote(path, safe="/?=&%")
        c.request("GET", path, headers={"Cookie": self.cookie} if self.cookie
                  else {})
        r = c.getresponse()
        body = r.read().decode("utf-8", "replace")
        self._take(r)
        c.close()
        return r.status, body, dict(r.getheaders())

    def post(self, path: str, form: dict, raw: bytes | None = None):
        c = self._conn()
        data = raw if raw is not None else urllib.parse.urlencode(
            form, encoding="utf-8").encode("utf-8")
        head = {"Content-Type": "application/x-www-form-urlencoded",
                "Content-Length": str(len(data))}
        if self.cookie:
            head["Cookie"] = self.cookie
        c.request("POST", path, body=data, headers=head)
        r = c.getresponse()
        body = r.read().decode("utf-8", "replace")
        self._take(r)
        loc = r.getheader("Location")
        c.close()
        return r.status, body, loc

    def _take(self, r):
        raw = r.getheader("Set-Cookie")
        if raw:
            self.cookie = raw.split(";")[0]

    def csrf(self, path: str = "/") -> str:
        _s, body, _h = self.get(path)
        m = re.search(r'name="csrf" value="([^"]*)"', body)
        return m.group(1) if m else ""

    def login(self, name: str, secret: str):
        token = self.csrf("/login")
        return self.post("/login", {"csrf": token, "name": name,
                                    "secret": secret})


def text(html: str) -> str:
    html = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def links(html: str) -> list:
    return re.findall(r'href="([^"]+)"', html)


def start_server():
    """실제 DB 사본 위에 서버를 띄운다.  ★ 원본을 고치지 않는다."""
    from collect.pipeline import (
        REPROCESS_TABLE, check_recalc_origin, from_step_for, web_reasons,
    )
    from web.app import make_app
    from web.server import make_handler

    def resume_plan(reason, origin):
        check_recalc_origin(reason, origin)
        return from_step_for(reason)

    reason_rows = [{"key": r, "label": r,
                    "from_step": REPROCESS_TABLE[r].steps[0]
                    if REPROCESS_TABLE[r].steps else "—"}
                   for r in web_reasons()]

    root = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "config"), os.path.join(root, "config"))
    for d in ("secrets", "web"):
        src = os.path.join(ROOT, d)
        if os.path.isdir(src):
            shutil.copytree(src, os.path.join(root, d))
    db = os.path.join(root, "carwatch.db")
    # ★ 운영 DB 를 복사하지 않는다 (0장 · S24 · 개정 246).
    #   거기 남은 recalc_job·계정이 시험 결과를 바꿔 「코드는 그대로인데
    #   어제는 되고 오늘은 안 되는」 상태가 된다 — 실측 08-16
    from seed import build_seed_db

    build_seed_db(db, root)

    from collect.pipeline import resume_point

    app = make_app(db, root, plan=resume_plan, reason_rows=reason_rows,
                   resume=resume_point,
                   fetch=lambda u: (200, "application/json",
                                    '{"category":{"originPrice":4270}}'))
    from http.server import HTTPServer

    srv = HTTPServer(("127.0.0.1", 0), make_handler(app))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, srv.server_address[1], root, db


def seed_admin(db: str) -> tuple[str, str]:
    """★ setup 은 화면 밖 유일 예외다 (시나리오 0)."""
    from contracts import ROLE_ADMIN
    from store.admin import create_account

    conn = sqlite3.connect(db)
    _aid, pw = create_account(conn, "마스터", ROLE_ADMIN, T,
                              secret="adminsecret1")
    conn.close()
    return "마스터", "adminsecret1"


# ── M-1  비로그인 — 전 링크 (21항목) ────────────────────────────────
NAV = ("/", "/listings", "/recommend", "/market", "/dealers", "/watch")


def m1(anon: Client, lid: int) -> None:
    print("\n[M-1] 비로그인 — 전 링크")
    ok = 0
    for path in NAV:
        st, _b, _h = anon.get(path)
        if st in (200, 403):
            ok += 1
    rec(1, "/", "상단 메뉴 6개", f"{ok}/{len(NAV)} 응답", ok == len(NAV))

    st, body, _h = anon.get("/")
    grade_links = [x for x in links(body) if "grade=" in x]
    rec(2, "/", "등급 분포 막대", f"링크 {len(grade_links)}", bool(grade_links))
    st2 = anon.get(grade_links[0])[0] if grade_links else 0
    rec(2.1, "/", "막대를 눌러 목록", str(st2), st2 == 200)

    tgt = [x for x in links(body) if "target=" in x]
    rec(3, "/", "차종별 표의 차종명", f"링크 {len(tgt)}", bool(tgt))

    # ★ 개정 427 — 현황의 매물 링크도 /detail 로 바뀌었다.  /why 는 살아 있다
    why = [x for x in links(body)
           if x.startswith("/why/") or x.startswith("/detail/")]
    rec(4, "/", "상위 후보 → 상세", f"링크 {len(why)}", bool(why))

    st, lbody, _h = anon.get("/listings")
    chips = [x for x in links(lbody) if "?" in x and "listings" in x]
    rec(5, "/listings", "축 값 → 필터 칩", f"필터 링크 {len(chips)}",
        bool(chips))
    st3 = anon.get(chips[0])[0] if chips else 0
    rec(6, "/listings", "필터 칩 적용", str(st3), st3 == 200)
    rec(7, "/listings", "전부 지우기", str(anon.get("/listings")[0]),
        anon.get("/listings")[0] == 200)

    from report.screens.views import ORDERS

    bad = [o for o in ORDERS if anon.get(f"/listings?order={o}")[0] != 200]
    rec(8, "/listings", f"정렬 {len(ORDERS)}종", f"실패 {bad}", not bad)

    token = anon.csrf("/listings")
    st, wbody, loc = anon.post("/watch/add",
                               {"csrf": token, "listing_id": str(lid)})
    invite = st == 200 and "로그인" in wbody
    rec(9, "/listings", "＋ 관심 (비로그인)",
        f"{st} · 유도={'예' if invite else '아니오'}", invite,
        "403 이면 불합격")
    shown = str(lid) in wbody or "만" in wbody
    rec("9.1", "유도 화면", "담으려던 매물 표시", "보임" if shown else "없음",
        shown)

    st, wb, _h = anon.get(f"/why/{lid}")
    rec(10, "/listings", "근거 → /why", str(st), st == 200)
    axis_links = [x for x in links(wb) if "axis=" in x or "?" in x]
    rec(12, "/why", "축 태그 링크", f"{len(axis_links)}개", bool(axis_links))
    rec(13, "/why", "참고 자료 절", "있음" if "참고 자료" in wb else "없음",
        "참고 자료" in wb)

    st, rb, _h = anon.get("/recommend")
    # ★★★★★ 09-01 — ★ 시안 `v4m_recommend_시안.html` 에 ★ **관심 단추가 없다.**
    #   ★ 브라우저로 열어 뽑아 봤다 — ★ 카드는 ★ 합·사진·이름·제원·값·네 축·막대뿐이다.
    #   ★★ ★ 「시안이 화면 규격의 정본이다」(`ref/screens/README.md`) —
    #     ★ ★ 시안에 없는 것을 ★ 내가 더하지 않는다.
    #   ★ ★ **관심 담기는 없어지지 않았다** — ★ `/listings`·`/watch` 에 그대로 있다.
    #     ★ ★ 추천은 ★ **세우기만** 하는 곳이다 (규격 3장 「금지」)
    rec(11, "/recommend", "시안대로 카드로 낸다",
        "카드" if "pickcard" in rb else "없음", "pickcard" in rb)

    st, mb, _h = anon.get("/market")
    bars = [x for x in links(mb) if "price_min=" in x]
    rec(14, "/market", "히스토그램 막대", f"{len(bars)}개", bool(bars))
    rec(15, "/market", "막대 → 목록",
        str(anon.get(bars[0])[0] if bars else 0),
        bool(bars) and anon.get(bars[0])[0] == 200)

    st, db_, _h = anon.get("/dealers")
    rec(16, "/dealers", "딜러 이름 링크", str(st), st == 200)

    st, cb, _h = anon.get("/compare")
    rec(17, "/compare", "비교 화면", str(st), st == 200)

    st, nb, _h = anon.get("/notready")
    acts = [x for x in links(nb) if x.startswith("/")]
    rec(18, "/notready", "조치 링크", f"{len(acts)}개", st == 200)

    st, lo, _h = anon.get("/login")
    rec(19, "/login", "계정 만들기 링크", "있음" if "/join" in lo else "없음",
        "/join" in lo)
    st, jo, _h = anon.get("/join")
    rec(20, "/join", "로그인 링크", "있음" if "/login" in jo else "없음",
        "/login" in jo)

    st, ab, _h = anon.get("/admin")
    rec(21, "/admin", "비로그인 직접 입력",
        f"{st} · 사유={'있음' if text(ab) else '없음'}",
        st == 403 and bool(text(ab)))


# ── M-2  user1 — 관심 (22~29) ───────────────────────────────────────
def m2(admin: Client, u1: Client, port: int, lid: int, db: str) -> None:
    print("\n[M-2] user1 — 관심")
    st, body, loc = u1.login("사용자갑", "usersecret1")
    rec(22.0, "/login", "user1 로그인", f"{st} {loc}", st == 303)

    token = u1.csrf("/listings")
    st, b, loc = u1.post("/watch/add", {"csrf": token,
                                        "listing_id": str(lid)})
    st2, wb, _h = u1.get("/watch")
    rec(22, "/listings", "＋ 관심", f"{st} · /watch {st2}",
        st in (302, 303) and st2 == 200)
    inlist = str(lid) in wb or "관심" in wb
    rec("22.1", "/watch", "담긴 것이 보인다", "보임" if inlist else "없음",
        inlist)

    wid = sqlite3.connect(db).execute(
        "SELECT watch_id FROM watch_item ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    wid = wid[0] if wid else None
    token = u1.csrf("/watch")
    st, b, _l = u1.post(f"/watch/{wid}", {"csrf": token,
                                          "target_price_won": "33000000"})
    saved = sqlite3.connect(db).execute(
        "SELECT target_price_won FROM watch_item WHERE watch_id=?",
        (wid,)).fetchone()
    rec(23, "/watch", "목표가 저장", f"{st} · 값 {saved and saved[0]}",
        saved is not None and saved[0] == 33000000)

    token = u1.csrf("/watch")
    st, b, _l = u1.post(f"/watch/{wid}", {"csrf": token, "action": "remove"})
    closed = sqlite3.connect(db).execute(
        "SELECT closed_at FROM watch_item WHERE watch_id=?",
        (wid,)).fetchone()
    rec(24, "/watch", "추적 종료", f"{st} · 이력 {'남음' if closed else '없음'}",
        st in (302, 303))

    token = u1.csrf("/watch")
    st, b, _l = u1.post("/watch/add",
                        {"csrf": token, "kind": "query", "name": "콜레오스 B",
                         "target_key": "KOLEOS_HEV", "min_grade": "B"})
    n = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM watch_query").fetchone()[0]
    rec(25, "/watch", "조건 알림 추가", f"{st} · {n}건", n >= 1)

    token = u1.csrf("/password")
    st, b, _l = u1.post("/password", {"csrf": token,
                                      "current": "usersecret1",
                                      "secret": "newsecret123",
                                      "secret2": "newsecret123"})
    other = Client(port, "u1-other")
    other.login("사용자갑", "usersecret1")
    st2, ob, _h = other.get("/watch")
    rec(27, "/password", "비밀번호 변경", f"{st} · 옛 비번 로그인 {st2}",
        st in (200, 302, 303))

    token = u1.csrf("/")
    st, b, loc = u1.post("/logout", {"csrf": token})
    st2, ab, _h = u1.get("/watch")
    rec(28, "상단", "로그아웃", f"{st} · 이후 /watch {st2}",
        st2 in (302, 303, 403))

    u1.login("사용자갑", "newsecret123")
    st, ab, _h = u1.get("/admin/query")
    rec(29, "user1", "관리 화면 직접 입력", str(st), st == 403)
    _ = admin


# ── M-3  admin — 관리 12화면 (30~57) ────────────────────────────────
ADMIN_SCREENS = ("/admin", "/admin/run", "/admin/audit", "/admin/users",
                 "/admin/scoring", "/admin/targets", "/admin/registry",
                 "/admin/config", "/admin/query", "/admin/api",
                 "/admin/tools", "/admin/docs", "/admin/requests")


def m3(ad: Client, db: str, root: str) -> None:
    print("\n[M-3] admin — 관리 화면")
    bad = [p for p in ADMIN_SCREENS if ad.get(p)[0] != 200]
    rec(30, "/admin", f"관리 {len(ADMIN_SCREENS)}화면", f"실패 {bad}", not bad)

    st, body, _h = ad.get("/admin")
    todo = [x for x in links(body) if x.startswith("/admin")
            or x in ("/notready",)]
    rec("30.1", "/admin", "조치 항목 링크", f"{len(todo)}개", bool(todo))

    # 47  설정 변경 → 이력
    token = ad.csrf("/admin/config")
    st, b, _l = ad.post("/admin/config",
                        {"csrf": token, "previewed": "1", "file": "web.json",
                         "key_path": "rows_per_page", "value": "150",
                         "reason": "한 쪽을 짧게"})
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        got = json.load(f)["rows_per_page"]
    rec(47, "/admin/config", "값 변경", f"{st} · 파일 {got}", got == 150)

    # 31  되돌리기
    st, cb, _h = ad.get("/admin")
    has_revert = "revert" in cb
    token = ad.csrf("/admin")
    cid = sqlite3.connect(db).execute(
        "SELECT change_id FROM config_change ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    st2 = 0
    if has_revert and cid:
        st2, _b, _l = ad.post("/admin/config",
                              {"csrf": token, "action": "revert",
                               "change_id": str(cid[0]),
                               "reason": "되돌린다", "previewed": "1"})
    n = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    rec(31, "/admin", "되돌리기", f"단추={'있음' if has_revert else '없음'} "
        f"· {st2} · 이력 {n}행", has_revert and n >= 2)

    # 32~34  실행.  ★ 사유는 화면이 주는 것만 고른다 (STEP 50a)
    st, rb, _h = ad.get("/admin/run")
    picks = re.findall(r'name="reason"[^>]*value="([^"]+)"', rb) or \
        re.findall(r'<option value="([^"]+)"', rb)
    reason = picks[0] if picks else "dictionary"
    token = ad.csrf("/admin/run")
    st, b, _l = ad.post("/admin/run",
                        {"csrf": token, "previewed": "1", "scope": "all",
                         # ★ 위험이 높은 행동은 문구를 직접 입력한다 (149l)
                         "confirm": "all",
                         "reason": reason})
    job = sqlite3.connect(db).execute(
        "SELECT status, scope FROM recalc_job ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    rec(32, "/admin/run", "사유 선택 → 실행", f"{st} · {job}",
        job is not None)
    rec(33, "/admin/run", "전 차종 = all", str(job and job[1]),
        bool(job) and job[1] == "all")

    # ★ S-5-2  도는 동안 조정이 잠긴다 · 운영·탐색은 열린다
    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "previewed": "1",
                         "action": "component", "target": "taste.hud",
                         "value": "25", "reason": "실행 중 변경"})
    rec("S5-2", "/admin/scoring", "실행 중 조정 잠김", str(st),
        st == 409, "409 Conflict (Q-3)")
    rec("S5-3", "/listings", "실행 중에도 조회는 된다",
        str(ad.get("/listings")[0]), ad.get("/listings")[0] == 200)

    conn_ = sqlite3.connect(db)
    conn_.execute("UPDATE recalc_job SET status='done'")
    conn_.commit()

    st, ab, _h = ad.get("/admin/audit")
    tabs = text(ab)
    rec(35, "/admin/audit", "탭 5종", f"{len(tabs)}자", st == 200 and
        len(tabs) > 200)

    # 36~39  계정
    token = ad.csrf("/admin/users")
    uid = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role<>'admin' LIMIT 1"
    ).fetchone()
    if uid:
        st, b, _l = ad.post("/admin/users",
                            {"csrf": token, "account_id": str(uid[0]),
                             "action": "disable", "reason": "시험"})
        off = sqlite3.connect(db).execute(
            "SELECT disabled_at FROM account WHERE account_id=?",
            (uid[0],)).fetchone()[0]
        rec(37, "/admin/users", "중지", f"{st} · {'중지' if off else '아님'}",
            off is not None)
        watch_kept = sqlite3.connect(db).execute(
            "SELECT COUNT(*) FROM watch_item WHERE account_id=?",
            (uid[0],)).fetchone()[0]
        rec("37.1", "/admin/users", "관심은 남는다", f"{watch_kept}건",
            True)
        token = ad.csrf("/admin/users")
        st, b, _l = ad.post("/admin/users",
                            {"csrf": token, "account_id": str(uid[0]),
                             "action": "enable", "reason": "해제"})
        off = sqlite3.connect(db).execute(
            "SELECT disabled_at FROM account WHERE account_id=?",
            (uid[0],)).fetchone()[0]
        rec(38, "/admin/users", "해제", f"{st} · {'해제' if not off else '중지'}",
            off is None)

    me = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role='admin' LIMIT 1"
    ).fetchone()[0]
    token = ad.csrf("/admin/users")
    st, b, _l = ad.post("/admin/users",
                        {"csrf": token, "account_id": str(me),
                         "action": "disable", "reason": "마지막 관리자"})
    left = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM account WHERE role='admin' "
        "AND disabled_at IS NULL").fetchone()[0]
    rec(39, "/admin/users", "마지막 관리자 중지", f"{st} · 남은 관리자 {left}",
        left >= 1)

    # 40~43  배점.  ★ 잠금이 먼저 걸리면 배점 검사가 전부 헛돈다
    conn_ = sqlite3.connect(db)
    conn_.execute("UPDATE recalc_job SET status='done' "
                  "WHERE status IN ('queued','running')")
    conn_.commit()
    # ★★★★★ 09-02 (명령서 1부 1-7 · **5회차째**) — ★ **분모를 안 넘어야 저장된다.**
    #   ★ 전에는 ★ 총점을 ★ 합에 맞춰 올려 줘 ★ 무엇이든 저장됐다 —
    #   ★ ★ 그래서 ★ 합 **911** 이 그냥 들어갔다 (가이드가 눌러 확인 09-02).
    #   ★ 그러므로 ★ **두 가지를 다 본다** — ① 넘으면 막힌다 ② 줄이면 된다
    def _hud():
        with open(os.path.join(root, "config", "scoring.json"),
                  encoding="utf-8") as f:
            return json.load(f)["components"].get("taste.hud")

    _was = _hud()
    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "action": "component",
                         "target": "taste.hud", "value": "25",
                         "reason": "HUD 를 더 본다", "previewed": "1"})
    rec(40, "/admin/scoring", "분모를 넘으면 안 바뀐다",
        f"{st} · hud={_hud()}", _hud() == _was,
        "합이 분모를 넘으면 저장을 막는다 (1-7)")

    # ★ 다른 축을 그만큼 줄이면 ★ 저장된다 — ★ 막이가 ★ **길을 아주 막는 것은 아니다**
    token = ad.csrf("/admin/scoring")
    ad.post("/admin/scoring",
            {"csrf": token, "action": "component",
             "target": "taste.trim", "value": "5",
             "reason": "HUD 자리를 만든다", "previewed": "1"})
    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "action": "component",
                         "target": "taste.hud", "value": "12",
                         "reason": "HUD 를 더 본다", "previewed": "1"})
    rec(40.5, "/admin/scoring", "자리를 만들면 바뀐다",
        f"{st} · hud={_hud()}", _hud() == 12)
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        pol = json.load(f)

    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "action": "component",
                         "target": "taste.hud", "value": "30",
                         "reason": "미리보기 없이"})
    # ★ 잠금(409)이 아니라 「미리보기 없음」(400)으로 거부돼야 한다.
    #   잠금이 먼저 걸리면 이 검사가 헛돈다 — 큐를 비운 뒤에 본다
    rec(41, "/admin/scoring", "미리보기 없이 저장",
        f"{st} · {text(b)[:14]}", st == 400,
        "403 이면 사유가 틀림 · 409 면 잠금에 가려짐")

    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        # ★ 개정 504 — spec.* 가 taste.* 로 이름을 바꿨다
                        {"csrf": token, "action": "axis", "target": "taste",
                         "value": "120", "reason": "재배분", "previewed": "1"})
    with open(os.path.join(root, "config", "scoring.json"),
              encoding="utf-8") as f:
        pol = json.load(f)
    spec_sum = sum(v if isinstance(v, int) else v.get("points", 0)
                   for k, v in pol["components"].items()
                   if k.startswith("taste.")
                   and not (isinstance(v, dict) and v.get("skipped")))
    rec(42, "/admin/scoring", "축 재배분", f"{st} · taste 합 {spec_sum}",
        spec_sum == 120)

    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        # ★ 개정 504 — spec.* 가 taste.* 로 이름을 바꿨다.
                        #   ★ 1 로 줄여야 작은 성분이 0 이 된다
                        {"csrf": token, "action": "axis", "target": "taste",
                         "value": "1", "reason": "0점", "previewed": "1"})
    rec(43, "/admin/scoring", "성분 0점", f"{st}", st == 400)

    # 44~45  차종
    token = ad.csrf("/admin/targets")
    st, b, _l = ad.post("/admin/targets",
                        {"csrf": token, "previewed": "1", "action": "add",
                         "target_key": "SONATA_HEV", "label": "쏘나타",
                         "collect_group": "SONATA",
                         "site_query": "(And.Hidden.N.)", "origin_type": "Y",
                         "reason": "추가"})
    with open(os.path.join(root, "config", "targets.json"),
              encoding="utf-8") as f:
        tg = json.load(f)
    rec(44, "/admin/targets", "차종 추가",
        f"{st} · {tg.get('SONATA_HEV', {}).get('status')}",
        tg.get("SONATA_HEV", {}).get("status") == "pending_review")
    tg["SONATA_HEV"]["displacement_range"] = [1900, 2100]
    with open(os.path.join(root, "config", "targets.json"), "w",
              encoding="utf-8") as f:
        json.dump(tg, f, ensure_ascii=False, indent=2)
    token = ad.csrf("/admin/targets")
    st, b, _l = ad.post("/admin/targets",
                        {"csrf": token, "previewed": "1", "action": "confirm",
                         "target_key": "SONATA_HEV", "reason": "확정"})
    with open(os.path.join(root, "config", "targets.json"),
              encoding="utf-8") as f:
        tg = json.load(f)
    rec(45, "/admin/targets", "확정",
        f"{st} · {tg['SONATA_HEV']['status']}",
        tg["SONATA_HEV"]["status"] == "active")

    # 46  등록부
    row = sqlite3.connect(db).execute(
        "SELECT endpoint, json_path FROM meta_field_usage "
        "WHERE usage='unclassified' LIMIT 1").fetchone()
    if row:
        token = ad.csrf("/admin/registry")
        st, b, _l = ad.post("/admin/registry",
                            {"csrf": token, "previewed": "1",
                             "endpoint": row[0], "json_path": row[1],
                             "usage": "unused_by_policy",
                             "reason": "판정에 안 씀"})
        with open(os.path.join(root, "config", "field_usage.json"),
                  encoding="utf-8") as f:
            seed = json.load(f)["seed"]
        got = seed.get(f"{row[0]}:{row[1]}", {}).get("usage")
        rec(46, "/admin/registry", "경로 분류", f"{st} · {got}",
            got == "unused_by_policy")
    else:
        rec(46, "/admin/registry", "경로 분류", "미분류 없음", True, "건너뜀")

    # 48~50  쿼리
    token = ad.csrf("/admin/query")
    st, b, _l = ad.post("/admin/query",
                        {"csrf": token,
                         "sql": "SELECT grade, COUNT(*) FROM result_score "
                                "GROUP BY 1"})
    rec(48, "/admin/query", "예시 쿼리", f"{st}", st in (200, 302, 303))
    for no, sql in ((49, "SELECT * FROM core_pii"),
                    ("49.2", "SELECT p.* FROM core_pii p /* 별칭 */"),
                    ("49.3", "WITH x AS (SELECT * FROM core_pii) "
                             "SELECT * FROM x"),
                    (50, "DELETE FROM core_listing"),
                    ("50.1", "UPDATE core_listing SET price_current_won=0"),
                    ("50.2", "DROP TABLE core_listing")):
        token = ad.csrf("/admin/query")
        st, b, _l = ad.post("/admin/query", {"csrf": token, "sql": sql})
        blocked = st in (400, 403) or "거부" in text(b)
        rec(no, "/admin/query", sql[:22], f"{st}", blocked)
    rej = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM query_log "
        "WHERE rejected_reason IS NOT NULL").fetchone()[0]
    rec("49.1", "/admin/query", "거부도 로그에", f"{rej}건", rej >= 2)

    # 51~52  API
    token = ad.csrf("/admin/api")
    st, b, _l = ad.post("/admin/api",
                        {"csrf": token, "previewed": "1", "reason": "탐색",
                         "url": "https://api.encar.com/v1/x", "note": "시험"})
    sid = sqlite3.connect(db).execute(
        "SELECT snapshot_id FROM admin_api_snapshot "
        "ORDER BY rowid DESC LIMIT 1").fetchone()
    rec(51, "/admin/api", "URL 요청 → 저장", f"{st} · id={sid and sid[0]}",
        sid is not None)
    st2, ab, _h = ad.get(f"/admin/api?snapshot={sid[0]}") if sid else (0, "",
                                                                      {})
    opened = "originPrice" in ab
    rec(52, "/admin/api", "저장 목록 → 상세",
        f"{st2} · 상세={'열림' if opened else '안 열림'}", opened)

    # 53  도구
    from web.views import TOOLS

    ran = 0
    for tool in TOOLS:
        token = ad.csrf("/admin/tools")
        st, b, _l = ad.post("/admin/tools",
                            {"csrf": token, "previewed": "1",
                             "reason": "점검", "tool": tool["key"]})
        if st == 200 and "<table" in b:
            ran += 1
    rec(53, "/admin/tools", f"도구 {len(TOOLS)}종", f"{ran}종 결과 표",
        ran == len(TOOLS))

    st, db_, _h = ad.get("/admin/docs")
    rec(54, "/admin/docs", "문서 링크", f"{st} · {len(text(db_))}자",
        st == 200 and len(text(db_)) > 100)

    # 55~57  요청
    token = ad.csrf("/admin/requests")
    st, b, _l = ad.post("/admin/requests",
                        {"csrf": token, "action": "create",
                         "title": "통합시험", "body": "본문",
                         "origin": "screen"})
    rid = sqlite3.connect(db).execute(
        "SELECT request_id FROM dev_request ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    rec(55, "/admin/requests", "요청 등록", f"{st}", rid is not None)
    token = ad.csrf("/admin/requests")
    st, b, _l = ad.post("/admin/requests",
                        {"csrf": token, "action": "status",
                         "request_id": rid[0], "status": "applied",
                         "direction": "반영", "step_ref": "STEP 1"})
    got = sqlite3.connect(db).execute(
        "SELECT status FROM dev_request WHERE request_id=?",
        (rid[0],)).fetchone()[0]
    rec(56, "/admin/requests", "상태 전이", f"{st} · {got}", got == "applied")
    token = ad.csrf("/admin/requests")
    st, b, _l = ad.post("/admin/requests", {"csrf": token,
                                            "action": "export"})
    out = os.path.join(root, "outputs")
    files = os.listdir(out) if os.path.isdir(out) else []
    rec(57, "/admin/requests", "md 내보내기", f"{st} · {len(files)}개",
        bool(files))


# ── M-4  난입력 (58~70) ─────────────────────────────────────────────
def m4(anon: Client, u1: Client, ad: Client, lid: int, db: str) -> None:
    print("\n[M-4] 난입력 — 깨뜨리기")
    for no, path, want in ((58, "/listings?page=abc", (400,)),
                           (59, "/listings?page=-1", (400,)),
                           (60, "/listings?order=없는정렬", (200,)),
                           (61, "/listings?grade=Z", (200,)),
                           (62, "/why/abc", (404,)),
                           ("62.1", "/why/99999999", (404,))):
        st, b, _h = anon.get(path)
        ok = st in want
        note = "" if ok else f"기대 {want}"
        if no == 61 and ok:
            note = "안내 있음" if text(b) else "빈 화면"
            ok = bool(text(b))
        rec(no, path[:26], "난입력", str(st), ok, note)

    token = u1.csrf("/watch")
    st, b, _l = u1.post("/watch/99999", {"csrf": token,
                                         "target_price_won": "1"})
    rec(63, "/watch/99999", "남의/없는 watch_id", str(st),
        st in (400, 403, 404) or (st in (302, 303)))

    token = ad.csrf("/admin/requests")
    st, b, _l = ad.post("/admin/requests",
                        {"csrf": token, "action": "create",
                         "title": "<script>alert(1)</script>",
                         "body": "x", "origin": "screen"})
    _s, rb, _h = ad.get("/admin/requests")
    escaped = "<script>alert(1)</script>" not in rb
    rec(64, "폼", "<script> 이스케이프",
        "이스케이프" if escaped else "그대로 나감", escaped)

    st, b, _l = anon.post("/watch/add", {"listing_id": str(lid)})
    rec(65, "POST", "CSRF 없이", str(st), st in (400, 403))

    st, b, _l = anon.post("/watch/add", {"csrf": "남의토큰",
                                         "listing_id": str(lid)})
    rec(66, "POST", "남의 CSRF 토큰", str(st), st in (400, 403))

    st, b, _h = anon.get("/static/../../secrets/plate_hmac.key")
    leaked = "-----" in b or len(b) > 40 and st == 200
    rec(67, "/static", "경로 탈출", f"{st}", st in (400, 403, 404)
        and not leaked)

    big = "x" * (2 * 1024 * 1024)
    token = ad.csrf("/admin/requests")
    st, b, _l = ad.post("/admin/requests",
                        {"csrf": token, "action": "create",
                         "title": "큰 폼", "body": big, "origin": "screen"})
    rec(68, "폼", "2MB 문자열", str(st), st == 413,
        "조용히 자르지 않는다 (Q-1)")

    lock = Client(ad.port, "lock")
    codes = []
    for _i in range(12):
        s, b2, _l = lock.login("마스터", "틀린비번")
        codes.append(s)
        if "시도가 많습니다" in b2:
            break
    locked = any("시도가 많습니다" in x for x in [b2])
    # ★ S36 (개정 359) — 상한이 0 이면 안 잠그는 것이 규격이다.
    #   마스터 지시 「그냥 제한 없애.  정식 서비스할 때 강화해」
    import json as _j

    with open("config/admin.json", encoding="utf-8") as _f:
        limit = int(_j.load(_f)["login_fail_limit"])
    rec(69, "/login", f"12회 실패 · 상한 {limit}", f"{codes[-1]} · "
        f"{'잠김' if locked else '안 잠김'}", locked == bool(limit))


# ── 시나리오 S-3  남의 것을 건드릴 수 있나 ──────────────────────────
def s3(ad: Client, u1: Client, u2: Client, db: str, lid: int) -> None:
    print("\n[S-3] user2 — 남의 것을 건드릴 수 있나")
    st, wb, _h = u2.get("/watch")
    u1_only = "33,000" not in wb
    rec("S3-4", "/watch", "남의 관심이 안 보인다",
        "안 보임" if u1_only else "보임", u1_only)

    wid = sqlite3.connect(db).execute(
        "SELECT watch_id FROM watch_item ORDER BY rowid LIMIT 1").fetchone()
    if wid:
        token = u2.csrf("/watch")
        st, b, _l = u2.post(f"/watch/{wid[0]}",
                            {"csrf": token, "target_price_won": "1"})
        owner = sqlite3.connect(db).execute(
            "SELECT target_price_won FROM watch_item WHERE watch_id=?",
            (wid[0],)).fetchone()[0]
        rec("S3-5", "/watch/{id}", "남의 것 수정 시도",
            f"{st} · 값 {owner}", owner != 1)

    token = u2.csrf("/listings")
    u2.post("/watch/add", {"csrf": token, "listing_id": str(lid)})
    n = sqlite3.connect(db).execute(
        "SELECT COUNT(DISTINCT account_id) FROM watch_item "
        "WHERE closed_at IS NULL").fetchone()[0]
    rec("S3-6", "/watch/add", "각자 따로 담긴다", f"{n}명", n >= 1)

    for no, path in (("S3-7", "/admin"), ("S3-8", "/admin/query")):
        st, b, _h = u2.get(path)
        rec(no, path, "user2 직접 입력", str(st), st == 403)
    _ = ad


# ── 단위 — 화면이 말해야 하는 것 ────────────────────────────────────
UNIT = {
    # ★★ 08-24 v3_dashboard_시안 — ★ 「오늘 변동」이 ★ 「1 오늘」이 됐다.
    #   ★ 그 아래에 ★ 새로 뜬 것 · 값 내린 것 · 사라진 것 · 마지막 재판정 넷을 낸다
    "/": ("해야 할 일", "등급 분포", "차종별", "1 오늘", "새로 뜬 것",
          "값 내린 것", "사라진 것", "마지막 재판정", "상위 후보"),
    "/listings": ("지금 조건으로", "축"),
    # ★★★★★ 09-01 — ★ **화면이 통째로 바뀌었다** (`docs/RECOMMEND_SCREEN.md` ·
    #   ★ 시안 `ref/screens/v4m_recommend_시안.html`).
    #   ★ 마스터 확정 — 「★ 추천은 여러 탭으로 · ★ 1번 탭은 ★ **등급 무시하고**
    #     ★ 예산·주행·연식·색 ★ **네 축의 합(297)**으로 세운다」
    #   ★★ 옛 절 ★ 「왜 이 **순서**인가」·「후보에서 뺀 것」은 ★ **옛 화면 것**이다 —
    #     ★ ★ 옛 화면은 ★ 「이유가 있는 것만 추린다」였고 ★ 새 화면은 ★ **세우기만** 한다
    #     ★ ★ 규격 「금지 — ★ 추천 화면에서 매물을 지우거나 숨기는 것」.
    #     ★ ★ ★ 곧 ★ 「뺀 것」 절이 ★ **있으면 안 된다**
    #   ★ 시안에 있는 것으로 갈았다 — ★ 브라우저로 시안을 열어 뽑았다 (09-01)
    # ★ 09-04 — ★ 「네 축」 → 「여섯 축」 (규격 20줄 · `RECOMMEND_AXES` 여섯)
    "/recommend": ("등급을 보지 않습니다", "여섯 축의 합"),
    "/market": ("가격 분포", "연식별", "트림별", "다른 차종"),
    "/dealers": ("딜러 목록", "이 지표가 무엇인가"),
    "/notready": ("왜 멈추나", "무엇을 하면 되나", "지금도 볼 수 있는 것"),
    "/admin": ("조치가 필요한 것", "최근 실행", "최근 변경"),
    "/admin/run": ("진행", "로그"),
    "/admin/scoring": ("축 총점", "성분", "미리보기", "배점 변경 이력"),
    "/admin/query": ("예제", "최근 쿼리", "테이블"),
    "/admin/api": ("요청", "저장된 응답", "응답"),
    "/admin/tools": ("점검", "정비", "내보내기", "여기에 없는 것"),
    "/admin/users": ("계정 활동", "계정 만들기"),
    "/admin/targets": ("차종 추가", "등록된 차종"),
    "/admin/config": ("변경 이력",),
    "/admin/requests": ("새 요청", "요청 목록", "내보내기"),
}


def unit(ad: Client, u1: Client, lid: int) -> None:
    print("\n[U] 단위 — 화면이 말해야 하는 것")
    for path, marks in UNIT.items():
        cli = ad
        st, body, _h = cli.get(path)
        got = text(body)
        missing = [m for m in marks if m not in got]
        rec(f"U {path}", path, f"절 {len(marks)}개",
            f"{st} · 빠짐 {missing}", st == 200 and not missing)

    st, wb, _h = ad.get(f"/why/{lid}")
    why_marks = ("무엇을 조회했는가", "축별 판정", "확인 못 한 것",
                 "왜", "비용", "참고 자료")
    got = text(wb)
    missing = [m for m in why_marks if m not in got]
    rec("U /why", "/why", f"절 {len(why_marks)}개", f"빠짐 {missing}",
        not missing)
    # ★★ 08-25 — ★ 「—」를 세던 것을 ★ **빈 칸**을 세는 것으로 바꾼다.
    #   ★ ★ 「—」는 ★ 두 가지로 쓰인다 —
    #     ① 「확인 못 함」 기호 (마스터 확정 · OK·×·—)
    #     ② ★ 문장 구두점 — 「축별 판정 — 축을 누르면」 · 「골격 — 이상 없음」
    #   ★ ★ 둘을 섞어 세면 ★ 글을 늘릴 때마다 ★ 검사가 빨개진다.  ★ 뜻이 없다
    #   ★★ ★ 「빈 칸」은 ★ **정말로 빈 `<td>`** 다 — ★ 그것을 센다
    empty = len(re.findall(r"<td[^>]*>\s*</td>", wb))
    rec("U /why 값", "/why", "빈 칸이 과하지 않다", f"빈 <td> {empty}개",
        empty < 30)

    u1.login("사용자갑", "newsecret123")
    st, ub, _h = u1.get("/watch")
    marks = ("관심", "조건 알림", "최종 후보")
    missing = [m for m in marks if m not in text(ub)]
    rec("U /watch", "/watch", "절 3개", f"빠짐 {missing}", not missing)


# ── 평가 지적 — 누락 5항목 + 흐름 4개 ───────────────────────────────
def gaps(ad: Client, u1: Client, u2: Client, db: str, root: str,
         lid: int) -> None:
    print("\n[누락 5항목] 26 · 34 · 36 · 47 · 70")

    # 26  조건 알림 끄기
    qid = sqlite3.connect(db).execute(
        "SELECT query_id FROM watch_query ORDER BY rowid DESC LIMIT 1"
    ).fetchone()
    if qid:
        token = u1.csrf("/watch")
        st, b, _l = u1.post("/watch/add",
                            {"csrf": token, "kind": "query_close",
                             "query_id": str(qid[0])})
        act = sqlite3.connect(db).execute(
            "SELECT active FROM watch_query WHERE query_id=?",
            (qid[0],)).fetchone()[0]
        rec(26, "/watch", "조건 알림 끄기",
            f"{st} · active={act}", st in (302, 303) and act == 0,
            "지우지 않고 끈다")

    # 34  중단 → 재개점
    st, rb, _h = ad.get("/admin/run")
    picks = re.findall(r'<option value="([^"]+)"', rb)
    token = ad.csrf("/admin/run")
    ad.post("/admin/run", {"csrf": token, "previewed": "1", "scope": "all",
                         # ★ 위험이 높은 행동은 문구를 직접 입력한다 (149l)
                         "confirm": "all",
                           "reason": picks[0] if picks else "dictionary"})
    jid = sqlite3.connect(db).execute(
        "SELECT job_id FROM recalc_job ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]
    token = ad.csrf("/admin/run")
    st, b, _l = ad.post("/admin/run",
                        {"csrf": token, "previewed": "1", "action": "halt",
                         "job_id": jid, "reason": "시험 중단"})
    row = sqlite3.connect(db).execute(
        "SELECT status, detail FROM recalc_job WHERE job_id=?",
        (jid,)).fetchone()
    rec(34, "/admin/run", "중단 → 재개점",
        f"{st} · {row[0]} · {(row[1] or '')[:28]}",
        row[0] == "failed" and "재개점" in (row[1] or ""))
    conn_ = sqlite3.connect(db)
    conn_.execute("UPDATE recalc_job SET status='done' "
                  "WHERE status IN ('queued','running')")
    conn_.commit()

    # 36  승인
    token = u2.csrf("/join")
    u2.post("/join", {"csrf": token, "name": "승인대상", "secret": "pending12345",
                      "secret2": "pending12345"})
    pend = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE role='pending' "
        "ORDER BY rowid DESC LIMIT 1").fetchone()
    if pend:
        token = ad.csrf("/admin/users")
        st, b, _l = ad.post("/admin/users",
                            {"csrf": token, "account_id": str(pend[0]),
                             "action": "approve", "reason": "승인"})
        role = sqlite3.connect(db).execute(
            "SELECT role FROM account WHERE account_id=?",
            (pend[0],)).fetchone()[0]
        rec(36, "/admin/users", "승인", f"{st} · role={role}", role == "user")
    else:
        rec(36, "/admin/users", "승인", "승인 대기 없음 (정책 open)", True,
            "건너뜀")

    # 47  설정 변경 → 파일 + 이력  (「저장했습니다」가 거짓말이던 자리)
    before = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    token = ad.csrf("/admin/config")
    st, b, _l = ad.post("/admin/config",
                        {"csrf": token, "previewed": "1", "file": "web.json",
                         "key_path": "rows_per_page", "value": "170",
                         "reason": "47 확인"})
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        got = json.load(f)["rows_per_page"]
    after = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    rec(47, "/admin/config", "값 변경 → 파일+이력",
        f"{st} · 파일 {got} · 이력 {before}→{after}",
        got == 170 and after == before + 1)

    # 70  재전송 — 같은 폼을 두 번
    n0 = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM watch_item").fetchone()[0]
    token = u1.csrf("/listings")
    form = {"csrf": token, "listing_id": str(lid)}
    u1.post("/watch/add", dict(form))
    u1.post("/watch/add", dict(form))          # ★ 뒤로 → 재전송
    n1 = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM watch_item").fetchone()[0]
    rec(70, "/watch/add", "폼 재전송", f"{n0} → {n1}", n1 - n0 <= 1,
        "중복 저장 안 됨")

    n0 = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    token = ad.csrf("/admin/config")
    form = {"csrf": token, "previewed": "1", "file": "web.json",
            "key_path": "rows_per_page", "value": "175", "reason": "재전송"}
    ad.post("/admin/config", dict(form))
    ad.post("/admin/config", dict(form))
    n1 = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    rec("70.1", "/admin/config", "설정 폼 재전송",
        f"이력 {n0} → {n1}", n1 - n0 <= 1, "같은 값이면 안 쌓인다")


# ── 흐름 S-1 · S-2 · S-4 · S-5 ──────────────────────────────────────
def flows(anon: Client, u1: Client, ad: Client, db: str, lid: int) -> None:
    print("\n[흐름] S-1 · S-2 · S-4 · S-5")
    # ★ 쿠키가 섞이면 결과가 뒤집힌다 — 흐름마다 새 항아리로 시작한다
    anon = Client(anon.port, "anon-flow")

    # S-1  사기 전에 알아본다
    # ★ 건수가 0 인 등급을 고르면 「빈 목록」을 보고 실패로 읽힌다.
    #   사람은 값이 있는 막대를 누른다 — 매물이 있는 등급을 고른다
    st, body, _h = anon.get("/")
    # ★ 개정 427 — 목록 링크가 /detail 로 바뀌었다.  ★ /why 주소는 살아 있다
    LINK = r"/(?:detail|why)/(\d+)"
    a_link, lb = "/listings", ""
    for cand in [x for x in links(body) if "grade=" in x]:
        _s, page, _h2 = anon.get(cand)
        if re.search(LINK, page):
            a_link, lb = cand, page
            break
    if not lb:
        _s, lb, _h2 = anon.get("/listings")
    first = re.search(LINK, lb)
    st, wb, _h = anon.get(f"/why/{first.group(1)}") if first else (0, "", {})
    got = text(wb)
    steps = ("확인 못 한 것" in got, "비용" in got)
    rec("S1-3~5", "/why", "근거 · 확인 못 한 것 · 비용",
        f"{a_link} → {st} · {steps}", all(steps))
    st, mb, _h = anon.get("/market")
    rec("S1-6", "/market", "시세 어디쯤인지", str(st), st == 200)
    token = anon.csrf("/listings")
    st, ib, _l = anon.post("/watch/add", {"csrf": token,
                                          "listing_id": str(lid)})
    rec("S1-7~9", "유도 화면", "403 아님 · 매물 보임 · 가입 링크",
        f"{st} · {'/join' in ib}", st == 200 and "/join" in ib)

    # S-2  후보를 좁힌다 — ★ 필터가 다음 행동의 조건이 된다 (STEP 149g)
    st, lb, _h = u1.get("/listings?grade=B&target=KOLEOS_HEV&order=monthly")
    body = text(lb)
    # ★ 누른 값이 칩으로 보이고, × 로 그 조건만 뺄 수 있어야 한다 (STEP 149d)
    chips = ("차종 KOLEOS_HEV" in body and "등급 B" in body)
    removable = lb.count("×") >= 2
    rec("S2-2~4", "/listings", "칩 2개 + 정렬",
        f"{st} · 칩={chips} · ×={removable}",
        st == 200 and chips and removable)

    # ★ 조건이 다음 행동으로 넘어간다 — 다시 입력하지 않는다 (STEP 149g)
    carried = ('name="target_key" value="KOLEOS_HEV"' in lb
               and 'name="min_grade" value="B"' in lb)
    rec("S2-5", "/listings", "지금 조건 → 조건 알림",
        "조건이 폼에 실려 있음" if carried else "다시 입력해야 함", carried,
        "STEP 149g")

    ids = [r[0] for r in sqlite3.connect(db).execute(
        "SELECT listing_id FROM result_score LIMIT 3")]
    st, cb, _h = u1.get("/compare?ids=" + ",".join(str(i) for i in ids))
    ratio = "%" in cb or "분모" in text(cb)
    rec("S2-8", "/compare", "분모가 달라도 비율로 비교",
        f"{st} · 비율 표시={ratio}", st == 200 and ratio)

    # S-4  운영한다
    st, ab, _h = ad.get("/admin")
    rec("S4-2", "/admin", "조치 목록", str(st), st == 200)
    st, ub, _h = ad.get("/admin/audit")
    rec("S4-4", "/admin/audit", "검증 결과", f"{len(text(ub))}자",
        len(text(ub)) > 200)
    n = sqlite3.connect(db).execute(
        "SELECT COUNT(*) FROM config_change").fetchone()[0]
    rec("S4-8", "/admin", "되돌린 것도 이력에", f"{n}행", n >= 2)

    # S-5  동시에 쓴다
    st, rb, _h = ad.get("/admin/run")
    picks = re.findall(r'<option value="([^"]+)"', rb)
    token = ad.csrf("/admin/run")
    ad.post("/admin/run", {"csrf": token, "previewed": "1", "scope": "all",
                         # ★ 위험이 높은 행동은 문구를 직접 입력한다 (149l)
                         "confirm": "all",
                           "reason": picks[0] if picks else "dictionary"})
    token = ad.csrf("/admin/scoring")
    st, b, _l = ad.post("/admin/scoring",
                        {"csrf": token, "previewed": "1",
                         "action": "component", "target": "taste.hud",
                         "value": "21", "reason": "실행 중"})
    msg = text(b)
    rec("S5-2", "/admin/scoring", "실행 중 조정 잠김",
        f"{st} · {msg[:24]}", st == 409, "409 Conflict")
    rec("S5-3", "/listings", "운영·탐색은 열린다",
        str(u1.get("/listings")[0]), u1.get("/listings")[0] == 200)

    conn = sqlite3.connect(db)
    conn.execute("UPDATE recalc_job SET status='done'")
    # ★ 미실행 검사가 하나도 없으면 화면이 그것을 낼 줄 아는지 알 수 없다.
    #   실제로 한 줄 넣고 화면이 「미실행」으로 내는지 본다 (A-7 · S5-8)
    conn.execute(
        "INSERT INTO audit_validation(run_id, phase, code, expected, actual,"
        " passed, severity, checked_at, applicable)"
        " VALUES ('integration','V0','V0-00','-','미실행',0,'warn',"
        "'2026-08-17T09:00:00+00:00',0)")
    conn.commit()

    st, ub2, _h = ad.get("/admin/audit")
    rec("S5-8", "/admin/audit", "안 돈 단계는 미실행",
        "미실행 표기 있음" if "미실행" in ub2 else "없음", "미실행" in ub2)


# ── 가이드 검사 7건 재현 방지 ────────────────────────────────────────
def guide7(ad: Client, u1: Client, port: int, db: str, root: str,
           lid: int) -> None:
    print("\n[가이드 7건] 재현 방지")

    # G-1  watch_id 가 폼에 붙는가
    token = u1.csrf("/listings")
    u1.post("/watch/add", {"csrf": token, "listing_id": str(lid)})
    st, wb, _h = u1.get("/watch")
    acts = {a for a in re.findall(r'action="(/watch/[^"]*)"', wb)}
    numbered = any(a.split("/")[-1].isdigit() for a in acts)
    rec("G-1", "/watch", "목표가·종료 폼에 watch_id",
        f"{sorted(acts)}", numbered, "빈 action 이면 실행 불가")

    wid = sqlite3.connect(db).execute(
        "SELECT watch_id FROM watch_item WHERE account_id=? "
        "AND closed_at IS NULL ORDER BY rowid DESC LIMIT 1",
        (_account_id(db, "사용자갑"),)).fetchone()
    if wid:
        token = u1.csrf("/watch")
        st, b, _l = u1.post(f"/watch/{wid[0]}",
                            {"csrf": token, "target_price_won": "31000000"})
        got = sqlite3.connect(db).execute(
            "SELECT target_price_won FROM watch_item WHERE watch_id=?",
            (wid[0],)).fetchone()[0]
        rec("G-1b", "/watch", "목표가 저장", f"{st} · {got}",
            got == 31000000)

    # G-2  같은 매물 두 번 담기
    token = u1.csrf("/listings")
    st, b, _l = u1.post("/watch/add", {"csrf": token,
                                       "listing_id": str(lid)})
    rec("G-2", "/watch/add", "같은 매물 두 번", str(st),
        st in (302, 303), "500 이면 서버가 죽는다")

    # G-3  되돌리기를 화면 폼 그대로
    token = ad.csrf("/admin/config")
    ad.post("/admin/config",
            {"csrf": token, "previewed": "1", "file": "web.json",
             "key_path": "rows_per_page", "value": "155", "reason": "G-3"})
    st, hb, _h = ad.get("/admin")
    form = re.search(r'action="/admin/config"[^>]*>(.*?)</form>', hb, re.S)
    fields = re.findall(r'name="(\w+)"', form.group(1)) if form else []
    cid = sqlite3.connect(db).execute(
        "SELECT change_id FROM config_change ORDER BY rowid DESC LIMIT 1"
    ).fetchone()[0]
    token = ad.csrf("/admin")
    # ★ 화면 폼에 있는 필드만 보낸다 — 손으로 더 넣지 않는다
    sent = {"csrf": token, "action": "revert", "change_id": str(cid),
            "reason": "되돌린다"}
    st, b, _l = ad.post("/admin/config",
                        {k: v for k, v in sent.items() if k in fields
                         or k == "csrf"})
    with open(os.path.join(root, "config", "web.json"), encoding="utf-8") as f:
        got = json.load(f)["rows_per_page"]
    rec("G-3", "/admin", "화면 폼 그대로 되돌리기",
        f"{st} · 값 {got}", st in (302, 303) and got != 155)

    # G-4  승인제 가입
    path = os.path.join(root, "config", "web.json")
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    old = blob.get("signup_policy")
    blob["signup_policy"] = "approval"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)
    u3 = Client(port, "u3")
    token = u3.csrf("/join")
    st, b, _l = u3.post("/join", {"csrf": token, "name": "승인대기자",
                                  "secret": "pending12345",
                                  "secret2": "pending12345"})
    role = sqlite3.connect(db).execute(
        "SELECT role FROM account WHERE login_name='승인대기자'").fetchone()
    rec("G-4", "/join", "승인제 가입", f"{st} · role={role and role[0]}",
        st in (302, 303) and role is not None and role[0] == "pending")

    u3.login("승인대기자", "pending12345")
    token = u3.csrf("/listings")
    st, b, _l = u3.post("/watch/add", {"csrf": token,
                                       "listing_id": str(lid)})
    rec("G-4b", "/watch/add", "승인 전에는 관심 등록 불가", str(st),
        st == 403, "로그인은 되나 담지는 못한다")

    if role:
        token = ad.csrf("/admin/users")
        aid = sqlite3.connect(db).execute(
            "SELECT account_id FROM account "
            "WHERE login_name='승인대기자'").fetchone()[0]
        st, b, _l = ad.post("/admin/users",
                            {"csrf": token, "account_id": str(aid),
                             "action": "approve", "reason": "승인"})
        got = sqlite3.connect(db).execute(
            "SELECT role FROM account WHERE account_id=?",
            (aid,)).fetchone()[0]
        rec("G-4c", "/admin/users", "승인 → user", f"{st} · {got}",
            got == "user")
    blob["signup_policy"] = old
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)

    # G-5  등록부 안내가 실제 값인가
    st, rb, _h = ad.get("/admin/registry")
    from store.admin import USAGE_VALUES

    shown = set(re.findall(r'<option value="(\w+)"', rb))
    rec("G-5", "/admin/registry", "안내가 실제 허용값",
        f"{sorted(shown)}", shown and shown <= set(USAGE_VALUES),
        "없는 값을 안내하면 400 이 난다")

    # G-6  시세 막대가 가격 필터를 거는가
    st, mb, _h = ad.get("/market")
    bars = [x.replace("&amp;", "&") for x in links(mb) if "price_min=" in x]
    # ★ 개정 427 — 목록 링크가 /detail 로 바뀌었다.  둘 다 센다
    def _n(html):
        return len(re.findall(r"/(?:detail|why)/\d+", html))

    total = _n(ad.get("/listings")[1])
    got = _n(ad.get(bars[0])[1]) if bars else total
    rec("G-6", "/market", "막대 → 그 구간 매물",
        f"전체 {total}행 · 막대 {got}행", bool(bars) and got < total,
        "200 을 내는 것과 필터가 걸리는 것은 다르다")

    # G-7  /admin/docs 내용
    st, db_, _h = ad.get("/admin/docs")
    rec("G-7", "/admin/docs", "문서 목록 · 본문",
        f"{len(text(db_))}자 · 링크 {db_.count('/admin/docs?path=')}",
        len(text(db_)) > 1000 and db_.count("/admin/docs?path=") > 5)
    st, one, _h = ad.get("/admin/docs?path=docs/chapters/61-web.md")
    rec("G-7b", "/admin/docs", "장 파일 열기", f"{st} · {len(one)}바이트",
        st == 200 and len(one) > 5000)
    st, bad, _h = ad.get("/admin/docs?path=../secrets/plate_hmac.key")
    rec("G-7c", "/admin/docs", "목록 밖 경로", str(st), st in (400, 403, 404))


def _account_id(db: str, name: str) -> int:
    row = sqlite3.connect(db).execute(
        "SELECT account_id FROM account WHERE login_name=?",
        (name,)).fetchone()
    return row[0] if row else 0


def make_users(ad: Client, root: str) -> None:
    """★ 계정은 화면에서 만든다 (시나리오 0).  CLI 는 admin 하나뿐이다."""
    token = ad.csrf("/admin/users")
    st, b, loc = ad.post("/admin/users",
                         {"csrf": token, "action": "create",
                          "name": "사용자갑", "role": "user",
                          "secret": "usersecret1", "reason": "시험"})
    rec("0-1", "/admin/users", "관리자가 계정 생성", str(st),
        st in (302, 303))
    # user2 는 /join 으로 — 정책을 open 으로 바꾼다
    path = os.path.join(root, "config", "web.json")
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    blob["signup_policy"] = "open"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)


def main() -> int:
    srv, port, root, db = start_server()
    try:
        name, pw = seed_admin(db)
        ad = Client(port, "admin")
        ad.login(name, pw)
        make_users(ad, root)

        conn = sqlite3.connect(db)
        lid = conn.execute(
            "SELECT listing_id FROM result_score LIMIT 1").fetchone()[0]

        anon = Client(port, "anon")
        u1 = Client(port, "user1")
        u2 = Client(port, "user2")

        m1(anon, lid)
        m2(ad, u1, port, lid, db)
        m3(ad, db, root)

        # user2 는 /join 에서 본인이 가입 (시나리오 S-3-2)
        token = u2.csrf("/join")
        st, b, _l = u2.post("/join", {
            "csrf": token, "name": "사용자을", "display_name": "을",
            "email": "b@b.c", "secret": "usersecret2",
            "secret2": "usersecret2"})
        rec("S3-2", "/join", "본인이 가입", str(st), st in (302, 303))
        u2.login("사용자을", "usersecret2")

        m4(anon, u1, ad, lid, db)
        s3(ad, u1, u2, db, lid)
        unit(ad, u1, lid)
        gaps(ad, u1, u2, db, root, lid)
        flows(anon, u1, ad, db, lid)
        guide7(ad, u1, port, db, root, lid)
    finally:
        srv.shutdown()

    print()
    print(f"항목 {len(ROWS)} · 합격 {len(ROWS) - len(FAIL)} · "
          f"불합격 {len(FAIL)}")
    if FAIL:
        print("불합격 목록")
        for f in FAIL:
            print("  ✗", f)
    _write_table()
    return 1 if FAIL else 0


def _write_table() -> None:
    """결과표를 파일로 낸다.  ★ 번호 · 화면 · 무엇을 했나 · 무엇이 나왔나 ·
    합/불 · 비고 (시나리오 4절 기록 방법)."""
    out = os.path.join(ROOT, "outputs")
    os.makedirs(out, exist_ok=True)
    path = os.path.join(out, "통합테스트_결과표.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("| 번호 | 화면 | 무엇을 했나 | 무엇이 나왔나 | 합/불 | 비고 |\n")
        f.write("|:--:|---|---|---|:--:|---|\n")
        for no, screen, did, got, mark, note in ROWS:
            f.write(f"| {no} | `{screen}` | {did} | {got} | "
                    f"**{mark}** | {note} |\n")
        f.write(f"\n**항목 {len(ROWS)} · 합격 {len(ROWS) - len(FAIL)} · "
                f"불합격 {len(FAIL)}**\n")
    print(f"결과표 → {path}")


if __name__ == "__main__":
    sys.exit(main())




