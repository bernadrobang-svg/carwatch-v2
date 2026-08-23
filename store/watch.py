# -*- coding: utf-8 -*-
"""후보 추적 (11장).

지시서   STEP 111 (alert_on_sold 재정의) · 112 (중복 3종) · 113 (스냅샷)
         114 (이벤트) · 115 (원인 분류) · 116 (알림) · 118 (최종 후보)
근거     ★ 같은 차량번호가 재등록이 아니다.  시간 축이 가른다 —
         겹치는가(동시 중복) · 이어지는가(재등록)
금지     sold_price · sold_at 컬럼을 만드는 것.  엔카는 판매 여부를 주지 않는다
         「판매되었습니다」로 알리는 것 — 「목록에서 사라졌습니다」다
         score_total · grade 를 watch_track 에 복제하는 것
         cause != 'listing' 인 변동을 알리는 것
"""
from __future__ import annotations

import json
import sqlite3

from errors import AlreadyWatched, PolicyError, ValidationError
from dataclasses import dataclass

# 중복 3종 (STEP 112)
DUP_SAME_DEALER = "concurrent_same_dealer"
DUP_CROSS_DEALER = "concurrent_cross_dealer"
DUP_RELIST = "relist"
# ★ 사이트 사이다 (docs/DEDUP_CROSS_SITE.md 2-3).  ★ 앞 둘은 「한 사이트 안에서」다 —
#   ★ 「엔카에도 KB 에도 있다」와 ★ 「한 딜러가 두 번 올렸다」는 ★ 다른 일이다
DUP_CROSS_SITE = "concurrent_cross_site"

# 이벤트 (STEP 114)
EV_PRICE_DROP = "price_drop"
EV_PRICE_RISE = "price_rise"
EV_TARGET_HIT = "target_hit"
EV_GONE = "gone"
EV_RELIST = "relist"
EV_GRADE_CHANGE = "grade_change"
EV_DOM = "dom_exceeded"

# 원인 (STEP 115).  listing 만 알린다
CAUSE_LISTING = "listing"
CAUSE_DICT = "dict"
CAUSE_CALC = "calc"
CAUSE_COEFFICIENT = "coefficient"

# 기본 알림 여부 (STEP 114)
NOTIFY_DEFAULT = {
    EV_PRICE_DROP: True, EV_PRICE_RISE: False, EV_TARGET_HIT: True,
    EV_GONE: True, EV_RELIST: True, EV_GRADE_CHANGE: True, EV_DOM: False,
}

ACTIVE = "active"
GONE = "gone"


WON_PER_MANWON = 10000


@dataclass(frozen=True)
class AlertConfig:
    """11장 정의서.  v1 alert_on_sold 는 on_gone 으로 대체됐다 (STEP 111)."""

    on_price_drop: bool
    on_target_price: bool
    on_gone: bool
    on_relist: bool
    on_grade_change: bool
    on_dom: bool
    dom_threshold_days: int | None


@dataclass(frozen=True)
class WatchItem:
    """★ 차량 단위다.  같은 차를 두 번 등록하지 않는다 (STEP 112a)."""

    watch_id: str
    vehicle_id: int
    primary_listing_id: str
    added_at: str
    memo: str | None
    target_price_won: int | None
    alerts: AlertConfig
    status: str
    closed_reason: str | None


@dataclass(frozen=True)
class TrackPoint:
    """watch_track 1행.  점수는 참조 키만 갖는다 (STEP 113)."""

    listing_id: str
    run_id: str
    observed_at: str
    price_won: int | None
    listing_status: str
    calc_version: str
    dict_version: str
    parse_version: str
    coefficient_id: int | None


@dataclass(frozen=True)
class TrackEvent:
    """11장 정의서 이름.  WatchEvent 와 같은 것이다."""

    listing_id: str
    vehicle_id: int | None
    kind: str
    before: str | None
    after: str | None
    cause: str
    occurred_at: str
    notified: bool


@dataclass(frozen=True)
class WatchEvent:
    listing_id: str
    vehicle_id: int | None
    run_id: str
    kind: str
    before_value: str | None
    after_value: str | None
    cause: str
    occurred_at: str


# ★ 리스·렌트는 ★ 살 수 있는 것이 아니다 — ★ 대표로 세우지 않는다 (명령서 0 「제외」)
LEASE_RENT = ("리스", "렌트")


def _cross_site_order(active: list) -> list:
    """대표 고르는 차례 (docs/DEDUP_CROSS_SITE.md 2-1).

    ① 리스·렌트가 아닌 것  ② 채워진 축이 많은 것  ③ 값이 싼 것
    ④ 먼저 관측된 것       ⑤ listing_id 가 작은 것
    ★ ①~⑤ 는 ★ 차례일 뿐 ★ 점수가 아니다 (원칙 1-a)
    ★ ⑤ 가 있어야 ★ 무작위가 없다 — ★ 같은 DB 면 ★ 늘 같은 대표가 나온다
    ★ ② 「채워진 축 수」는 ★ 이 자리에서 셀 수 없다 (점수는 뒤 단계다) —
      ★ 지금은 ★ ①③④⑤ 로 가른다.  ★ ② 는 판정이 붙은 뒤에 넣는다 (기록에 적었다)
    """
    def key(r):
        lease = any(w in (r[7] or "") for w in LEASE_RENT)
        return (1 if lease else 0,
                r[3] is None, r[3] if r[3] is not None else 0,
                r[4] or "", r[0])
    return sorted(active, key=key)


# ── STEP 112 중복 3종 ────────────────────────────────────────────────
def classify_duplicates(conn: sqlite3.Connection, vehicle_id: int) -> list[dict]:
    """같은 vehicle_id 의 매물을 3종으로 가른다.

    ★ 동시 중복을 relist 로 알리면 「같은 차가 다시 올라왔다」는 거짓 알림이
      1,111건 나간다.  시간 축이 가른다 — 겹치는가 · 이어지는가.
    대표   가장 싼 것.  같으면 먼저 관측된 것
    """
    rows = conn.execute(
        "SELECT listing_id, dealer_id, status, price_current_won, first_seen,"
        " gone_at, site, sell_type FROM core_listing WHERE vehicle_id = ? "
        "ORDER BY price_current_won IS NULL, price_current_won, first_seen",
        (vehicle_id,)).fetchall()
    if len(rows) < 2:
        return []

    active = [r for r in rows if r[2] == ACTIVE]
    out: list[dict] = []

    if len(active) >= 2:
        dealers = {r[1] for r in active}
        sites = {r[6] for r in active}
        if len(sites) > 1:
            # ★★ 사이트를 넘는다 — ★ 화면에는 ★ 한 번만 뜬다 (DEDUP_CROSS_SITE 2).
            #   ★ 목적 ⑤ 「사이트 안 가고 훑는다」가 ★ 두 번 뜨면 무너진다.
            #   ★ 대표는 ★ 하나다 — ★ 짝은 지우지 않는다 (축을 합쳐야 하기 때문이다)
            for i, r in enumerate(_cross_site_order(active)):
                out.append({
                    "listing_id": r[0], "kind": DUP_CROSS_SITE,
                    "representative": 1 if i == 0 else 0,
                    "peer_count": len(active),
                })
        else:
            kind = DUP_SAME_DEALER if len(dealers) == 1 else DUP_CROSS_DEALER
            for i, r in enumerate(active):
                out.append({
                    "listing_id": r[0], "kind": kind,
                    # 딜러 간 중복은 양쪽 다 보여준다.  가격 비교 대상이다
                    "representative": (1 if (kind == DUP_CROSS_DEALER or i == 0)
                                       else 0),
                    "peer_count": len(active),
                })

    # 이어지는 것 — gone 이후 새 listing_id 로 등장한 것
    gones = [r for r in rows if r[2] == GONE and r[5]]
    for g in gones:
        for a in active:
            if a[4] and g[5] and a[4] >= g[5]:
                out.append({"listing_id": a[0], "kind": DUP_RELIST,
                            "representative": 1, "peer_count": len(rows)})
                break
    return out


def sync_duplicates(conn: sqlite3.Connection, at: str) -> dict[str, int]:
    """vehicle_duplicate 갱신.  집계에서 동시 중복을 1건으로 세기 위한 것이다.

    중복을 그대로 세면 물량이 부풀려지고 딜러 지표가 왜곡된다.
    """
    stat = {DUP_SAME_DEALER: 0, DUP_CROSS_DEALER: 0, DUP_RELIST: 0,
            DUP_CROSS_SITE: 0}
    conn.execute("DELETE FROM vehicle_duplicate")
    for (vk,) in conn.execute(
        "SELECT vehicle_id FROM core_listing WHERE vehicle_id IS NOT NULL "
        "GROUP BY vehicle_id HAVING COUNT(*) > 1"
    ).fetchall():
        for d in classify_duplicates(conn, vk):
            conn.execute(
                "INSERT OR REPLACE INTO vehicle_duplicate"
                "(vehicle_id,listing_id,kind,representative,peer_count,"
                " detected_at) VALUES (?,?,?,?,?,?)",
                (vk, d["listing_id"], d["kind"], d["representative"],
                 d["peer_count"], at))
            stat[d["kind"]] += 1
    conn.commit()
    return stat


def deduped_count(conn: sqlite3.Connection, target_key: str) -> int:
    """차종별 매물 수 — 동시 중복은 1건으로 센다 (STEP 112)."""
    return conn.execute(
        "SELECT COUNT(*) FROM core_listing l WHERE l.target_key = ? "
        "AND NOT EXISTS (SELECT 1 FROM vehicle_duplicate d "
        " WHERE d.listing_id = l.listing_id AND d.representative = 0 "
        " AND d.kind = ?)", (target_key, DUP_SAME_DEALER)).fetchone()[0]


# ── STEP 112a 관심 등록 ─────────────────────────────────────────────
def watch_add(conn: sqlite3.Connection, vehicle_id: int,
              primary_listing_id: int, at: str, account_id: int,
              memo: str | None = None,
              target_price_won: int | None = None) -> int:
    """차량 단위 등록.  UNIQUE(account_id, vehicle_id) 가 중복을 막는다.

    ★ account_id 는 필수다.  여러 사람이 같은 차를 담을 수 있다 (STEP 111).
      빠뜨리면 NOT NULL 로 막힌다 — 화면에서 그 오류가 났다
    """
    # ★ 이미 담은 것을 또 담아도 죽지 않는다.  뒤로가기 재전송으로
    #   UNIQUE 위반이 나면 sqlite3.IntegrityError 가 그대로 올라가
    #   500 이 됐다 — 남의 조작으로 서버가 죽으면 안 된다 (실측 08-15)
    got = conn.execute(
        "SELECT watch_id, closed_at FROM watch_item "
        "WHERE account_id = ? AND vehicle_id = ?",
        (account_id, vehicle_id)).fetchone()
    if got is not None:
        if got[1] is None:
            raise AlreadyWatched(f"이미 관심에 담은 차량입니다: {vehicle_id}",
                                 step="STEP 111")
        # 껐던 것을 다시 담는 것은 정상이다 — 되살린다
        conn.execute(
            "UPDATE watch_item SET closed_at=NULL, added_at=?, "
            "primary_listing_id=? WHERE watch_id=?",
            (at, primary_listing_id, got[0]))
        conn.commit()
        return got[0]

    # ★ watch_id 는 INTEGER 대리키다.  DB 가 부여한다 (STEP 28)
    cur = conn.execute(
        "INSERT INTO watch_item(account_id,vehicle_id,"
        "primary_listing_id,added_at,memo,target_price_won) "
        "VALUES (?,?,?,?,?,?)",
        (account_id, vehicle_id, primary_listing_id, at, memo,
         target_price_won))
    conn.commit()
    return int(cur.lastrowid)


def assert_owner(conn: sqlite3.Connection, watch_id: int,
                 account_id: int) -> None:
    """★ 남의 관심을 고치거나 지우지 못한다 (C-1 · V7-12).

    watch_id 는 연속 정수다.  조회만 계정별로 막고 쓰기를 열어 두면
    번호를 바꿔 남의 것을 종료할 수 있다 — 실측으로 뚫렸다
    """
    row = conn.execute("SELECT account_id FROM watch_item WHERE watch_id=?",
                       (watch_id,)).fetchone()
    if row is None:
        raise ValidationError(f"없는 관심 항목: {watch_id}", step="STEP 111")
    if int(row[0]) != int(account_id):
        raise PolicyError("남의 관심 항목은 고칠 수 없습니다", step="STEP 111")


def watch_update(conn: sqlite3.Connection, watch_id: int, account_id: int,
                 alerts: AlertConfig | None = None,
                 target_price_won: int | None = None) -> None:
    assert_owner(conn, watch_id, account_id)
    if target_price_won is not None:
        conn.execute("UPDATE watch_item SET target_price_won=? "
                     "WHERE watch_id=? AND account_id=?",
                     (target_price_won, watch_id, account_id))
    if alerts is not None:
        conn.execute(
            "UPDATE watch_item SET on_price_drop=?, on_target_price=?,"
            " on_gone=?, on_relist=?, on_grade_change=?, on_dom=?,"
            " dom_threshold_days=? WHERE watch_id=? AND account_id=?",
            (int(alerts.on_price_drop), int(alerts.on_target_price),
             int(alerts.on_gone), int(alerts.on_relist),
             int(alerts.on_grade_change), int(alerts.on_dom),
             alerts.dom_threshold_days, watch_id, account_id))
    conn.commit()


def watch_close(conn: sqlite3.Connection, watch_id: int, reason: str,
                at: str, account_id: int) -> None:
    """closed_reason 은 bought · lost · dropped 뿐이다 (DDL CHECK)."""
    assert_owner(conn, watch_id, account_id)
    conn.execute(
        "UPDATE watch_item SET status='closed', closed_reason=?, closed_at=? "
        "WHERE watch_id=? AND account_id=?",
        (reason, at, watch_id, account_id))
    conn.commit()


# 진행 메모의 갈래 (개정 362).  ★ 순서가 아니다 — 정리하는 이름일 뿐이다.
#   ★ 계약 4단계를 폐기하고 이것이 대신 들어왔다.
#     마스터는 사는 사람이다.  파는 쪽을 대행하지 않는다
NOTE_KINDS: dict = {
    "contacted": "연락함",
    "visited": "보러 감",
    "done": "끝",
}


def note_add(conn: sqlite3.Connection, account_id: int, listing_id: int,
             kind: str, body: str, at: str) -> int:
    """담아 둔 매물에 진행을 적는다 (11장 STEP 118 · 개정 362 · V7-15).

    ★ 단계를 강제하지 않는다.  건너뛸 수 있다 —
      「연락함」 없이 「끝」을 적어도 된다.  전화만 하고 끝날 수도 있다
    ★ 메모가 본체다.  빈 메모는 받지 않는다
    금지   계약·대행 절차를 넣는 것
    금지   메모를 점수에 반영하는 것 (V7-08 이 잡는다)
    """
    if kind not in NOTE_KINDS:
        raise ValidationError(
            f"진행은 {' · '.join(NOTE_KINDS.values())} 셋입니다: {kind[:20]}",
            step="STEP 118")
    body = (body or "").strip()
    if not body:
        raise ValidationError(
            "무엇을 했는지 적어 주십시오.  메모가 본체입니다", step="STEP 118")
    cur = conn.execute(
        "INSERT INTO watch_note(account_id, listing_id, kind, body, noted_at)"
        " VALUES(?,?,?,?,?)", (account_id, listing_id, kind, body, at))
    conn.commit()
    return int(cur.lastrowid)


def notes_of(conn: sqlite3.Connection, account_id: int,
             listing_id: int | None = None) -> list:
    """내가 적은 진행 메모.  ★ 남의 메모는 안 보인다 (V7-12).

    돌려줌   [(note_id, listing_id, kind, 갈래이름, body, noted_at)]
            ★ 최근 것이 위다 — 무슨 일이 있었나를 거꾸로 읽는다
    """
    sql = ("SELECT note_id, listing_id, kind, body, noted_at FROM watch_note"
           " WHERE account_id = ?")
    args: list = [account_id]
    if listing_id is not None:
        sql += " AND listing_id = ?"
        args.append(listing_id)
    return [(r[0], r[1], r[2], NOTE_KINDS.get(r[2], r[2]), r[3], r[4])
            for r in conn.execute(sql + " ORDER BY noted_at DESC, note_id DESC",
                                  args)]


def note_delete(conn: sqlite3.Connection, note_id: int,
                account_id: int) -> None:
    """★ 남의 메모는 못 지운다.  note_id 는 연속 정수다 (V7-12)."""
    row = conn.execute("SELECT account_id FROM watch_note WHERE note_id=?",
                       (note_id,)).fetchone()
    if row is None:
        raise ValidationError(f"없는 메모: {note_id}", step="STEP 118")
    if int(row[0]) != int(account_id):
        raise PolicyError("남의 메모는 지울 수 없습니다", step="STEP 118")
    conn.execute("DELETE FROM watch_note WHERE note_id=? AND account_id=?",
                 (note_id, account_id))
    conn.commit()


# ── STEP 113 스냅샷 ──────────────────────────────────────────────────
def track_snapshot(conn: sqlite3.Connection, run_id: str, at: str,
             coefficient_id: int | None = None) -> int:
    """관심 매물만 기록한다.  전 매물 이력은 core_listing_change 가 담는다.

    금지   score_total · grade · denominator 복제 — 재채점 시 한쪽만 갱신된다
    """
    n = 0
    for lid, price, status, pv, cv, dv in conn.execute(
        "SELECT l.listing_id, l.price_current_won, l.status, l.parse_version,"
        " s.calc_version, s.dict_version FROM core_listing l "
        "JOIN watch_item w ON w.vehicle_id = l.vehicle_id "
        "LEFT JOIN result_score s ON s.listing_id = l.listing_id"
    ).fetchall():
        conn.execute(
            "INSERT OR REPLACE INTO watch_track"
            "(listing_id,run_id,observed_at,price_won,listing_status,"
            " calc_version,dict_version,parse_version,coefficient_id)"
            " VALUES (?,?,?,?,?,?,?,?,?)",
            (lid, run_id, at, price, status, cv or "", dv or "", pv or "",
             coefficient_id))
        n += 1
    conn.commit()
    return n


# 11장 함수표 이름과 짧은 별칭을 함께 둔다
snapshot = track_snapshot


def track_points(conn: sqlite3.Connection, listing_id: str) -> list[TrackPoint]:
    return [TrackPoint(*r) for r in conn.execute(
        "SELECT listing_id, run_id, observed_at, price_won, listing_status,"
        " calc_version, dict_version, parse_version, coefficient_id "
        "FROM watch_track WHERE listing_id=? ORDER BY observed_at",
        (listing_id,))]


# ── STEP 115 원인 분류 ───────────────────────────────────────────────
def classify_cause(prev: TrackPoint, cur: TrackPoint) -> str:
    """규칙이 바뀐 것을 매물이 바뀐 것처럼 알리지 않는다."""
    if prev.dict_version != cur.dict_version:
        return CAUSE_DICT
    if prev.calc_version != cur.calc_version:
        return CAUSE_CALC
    if prev.coefficient_id != cur.coefficient_id:
        return CAUSE_COEFFICIENT
    return CAUSE_LISTING


# ── STEP 114 이벤트 감지 ─────────────────────────────────────────────
def detect_events(conn: sqlite3.Connection, run_id: str,
                  at: str) -> list[WatchEvent]:
    """S12 리포트 직전.  검증 V1~V5 통과 후에만 부른다 (STEP 114).

    검증에 실패한 실행의 점수로 알림을 보내면 안 된다.
    """
    out: list[WatchEvent] = []
    for wid, vk, target, in_conn in conn.execute(
        "SELECT watch_id, vehicle_id, target_price_won, 1 FROM watch_item "
        "WHERE status = 'watching'"
    ).fetchall():
        lids = [r[0] for r in conn.execute(
            "SELECT listing_id FROM core_listing WHERE vehicle_id=?", (vk,))]
        for lid in lids:
            pts = track_points(conn, lid)
            if len(pts) < 2:
                continue
            prev, cur = pts[-2], pts[-1]
            cause = classify_cause(prev, cur)

            if (prev.price_won is not None and cur.price_won is not None
                    and cur.price_won != prev.price_won):
                kind = (EV_PRICE_DROP if cur.price_won < prev.price_won
                        else EV_PRICE_RISE)
                out.append(WatchEvent(lid, vk, run_id, kind,
                                      str(prev.price_won), str(cur.price_won),
                                      cause, at))
            if (target and cur.price_won is not None
                    and cur.price_won <= target
                    and (prev.price_won or 0) > target):
                out.append(WatchEvent(lid, vk, run_id, EV_TARGET_HIT,
                                      str(target), str(cur.price_won),
                                      cause, at))
            if prev.listing_status != GONE and cur.listing_status == GONE:
                out.append(WatchEvent(lid, vk, run_id, EV_GONE,
                                      prev.listing_status, GONE, cause, at))

        # 재등록 — 동시 중복과 구분한다 (STEP 112)
        for lid, kind in conn.execute(
            "SELECT listing_id, kind FROM vehicle_duplicate WHERE vehicle_id=?",
            (vk,)
        ).fetchall():
            if kind == DUP_RELIST:
                out.append(WatchEvent(lid, vk, run_id, EV_RELIST, None, None,
                                      CAUSE_LISTING, at))

    for e in out:
        conn.execute(
            "INSERT INTO watch_event"
            "(listing_id,vehicle_id,run_id,kind,before_value,after_value,"
            " cause,occurred_at,notified) VALUES (?,?,?,?,?,?,?,?,0)",
            (e.listing_id, e.vehicle_id, e.run_id, e.kind, e.before_value,
             e.after_value, e.cause, e.occurred_at))
    conn.commit()
    return out


# ── STEP 116 알림 ────────────────────────────────────────────────────
def message(event: WatchEvent, last_price: int | None = None,
            gone_at: str | None = None, key_source: str | None = None) -> str:
    """사실만 낸다.  「좋은 매물입니다」 같은 판단 문구를 쓰지 않는다.

    ★ gone 은 「목록에서 사라졌습니다」다.  「판매되었습니다」가 아니다
    """
    def man(v):
        return f"{int(v) // WON_PER_MANWON:,}만" if v not in (None, "") else "—"

    if event.kind == EV_PRICE_DROP or event.kind == EV_PRICE_RISE:
        d = int(event.after_value) - int(event.before_value)
        return (f"{man(event.before_value)} → {man(event.after_value)} "
                f"({'+' if d > 0 else '−'}{abs(d) // WON_PER_MANWON:,}만)")
    if event.kind == EV_TARGET_HIT:
        return (f"목표가 {man(event.before_value)} 도달 "
                f"(현재 {man(event.after_value)})")
    if event.kind == EV_GONE:
        return (f"목록에서 사라짐.  마지막 {man(last_price)}"
                f"{' · ' + gone_at if gone_at else ''}")
    if event.kind == EV_RELIST:
        src = f".  결합 근거 {key_source}" if key_source else ""
        return f"같은 차량이 새 매물로 등록{src}"
    if event.kind == EV_GRADE_CHANGE:
        return (f"{event.before_value} → {event.after_value}.  "
                f"원인 {event.cause}")
    return event.kind


def notify(conn: sqlite3.Connection, events: list[WatchEvent],
           send=None) -> dict[str, int]:
    """cause != 'listing' 이면 보내지 않는다 (STEP 115 · 120a).

    send   (event) -> bool   외부 채널.  ★ 1차는 None — 화면 표시가 발송이다
    실행당 1회.  같은 이벤트를 반복 발송하지 않는다.
    금지   발송 성공을 낙관해 notified=1 로 먼저 쓰는 것
          실패를 조용히 넘기는 것 — 실패도 남는다 (V7-10)
    """
    stat = {"sent": 0, "skipped_cause": 0, "skipped_default": 0,
            "skipped_duplicate": 0, "failed": 0}
    for e in events:
        if e.cause != CAUSE_LISTING:
            stat["skipped_cause"] += 1
            continue
        if not NOTIFY_DEFAULT.get(e.kind, False):
            stat["skipped_default"] += 1
            continue
        dup = conn.execute(
            "SELECT COUNT(*) FROM watch_event WHERE listing_id=? AND kind=? "
            "AND notified=1 AND run_id=?",
            (e.listing_id, e.kind, e.run_id)).fetchone()[0]
        if dup:
            stat["skipped_duplicate"] += 1
            continue
        # ★ 시도를 먼저 기록한다.  보낸 뒤 결과로 갱신한다 (STEP 120a)
        conn.execute(
            "UPDATE watch_event SET notify_attempted_at=? "
            "WHERE listing_id=? AND kind=? AND run_id=?",
            (e.occurred_at, e.listing_id, e.kind, e.run_id))
        ok = True if send is None else bool(send(e))
        if ok:
            conn.execute(
                "UPDATE watch_event SET notified=1 "
                "WHERE listing_id=? AND kind=? AND run_id=?",
                (e.listing_id, e.kind, e.run_id))
            stat["sent"] += 1
        else:
            # 실패해도 이벤트는 남는다.  다시 보낼 수 있어야 한다
            stat["failed"] += 1
    conn.commit()
    return stat


# ── STEP 117a 조건 추적 (Watch Query) ──────────────────────────────
# ★ 11장은 「이 매물」을 추적한다.  여기서는 「이런 차」를 추적한다.
#   매물은 사라진다.  조건은 남는다
# 금지   쿼리를 코드에 박는 것.  조건은 config 가 아니라 데이터다

# 조건에 쓸 수 있는 열.  ★ 임의 SQL 을 받지 않는다 — 열거된 것만이다
QUERY_FIELDS = {
    "target_key": "l.target_key = ?",
    "trim_badge": "l.trim_badge = ?",
    "year_min": "l.year_month >= ?",
    "mileage_max": "l.mileage_km <= ?",
}
# 축 조건.  ★ 「HUD 있는 차가 새로 뜨면 알림」이 이 도구를 쓰는 이유다.
#   목록에서 축으로 걸러 놓고 알림에 못 넘기면 조건을 다시 물어야 한다
#   (STEP 149g — 「행동할 때 조건을 다시 묻는 것」이 금지)
# ★ 목록 칩과 같은 기준을 쓴다 (report.screens.build.chip).
#   score 는 비어 있을 수 있다 — value 가 판정 결과다
AXIS_BUCKETS = {
    "1": "a.value > 0 AND a.excluded = 0",
    "0": "a.value = 0 AND a.excluded = 0",
    "unknown": "a.value IS NULL OR a.excluded = 1",
    "na": "a.value = -1",
}
import os as _os_lbl
_ROOT_LBL = _os_lbl.path.dirname(_os_lbl.path.dirname(_os_lbl.path.abspath(__file__)))


def _grade_order() -> tuple:
    """등급 차례.  ★ 정본은 config/labels.json GRADE_ORDER 다 (개정 433).

    ★ 여기에 ("S","A","B","C","D","E") 를 박지 않는다 — 개정 433 이 8단계로
      내렸을 때 이 튜플이 세 모듈에 흩어져 있어 전수로 찾아야 했다 (S14)
    """
    import json as _j
    import os as _o
    _p = _o.path.join(_ROOT_LBL, "config", "labels.json")
    with open(_p, encoding="utf-8") as _f:
        return tuple(_j.load(_f)["GRADE_ORDER"])


def _not_ranked() -> tuple:
    """순위를 안 매기는 것 — 제외 · 등급 없음 · 평가 불가 (개정 433)."""
    import json as _j
    import os as _o
    _p = _o.path.join(_ROOT_LBL, "config", "labels.json")
    with open(_p, encoding="utf-8") as _f:
        return tuple(_j.load(_f)["GRADE_NOT_RANKED"])


GRADE_ORDER = _grade_order()
NOT_RANKED = _not_ranked()



def add_watch_query(conn: sqlite3.Connection, account_id: int, name: str,
                    conditions: dict, at: str, min_grade: str | None = None,
                    max_price_won: int | None = None,
                    notify_on_new: bool = True,
                    notify_on_price: bool = True) -> int:
    """조건을 등록한다 (STEP 117a).

    ★ 사용자가 화면에서 만든다.  코드에 박지 않는다
    """
    bad = sorted(set(conditions) - set(QUERY_FIELDS) - {"axis", "bucket"})
    if bad:
        raise ValidationError(
            f"쓸 수 없는 조건: {', '.join(bad)}", step="STEP 117a")
    if conditions.get("bucket") and conditions["bucket"] not in AXIS_BUCKETS:
        raise ValidationError(
            f"없는 축 상태: {conditions['bucket']}", step="STEP 117a")
    if conditions.get("axis") and not conditions.get("bucket"):
        raise ValidationError(
            "축만으로는 조건이 되지 않는다 — 있음·없음·확인 못 함 중 "
            "하나를 함께 정한다", step="STEP 117a")
    if min_grade and min_grade not in GRADE_ORDER:
        raise ValidationError(f"없는 등급: {min_grade}", step="STEP 117a")
    if not (name or "").strip():
        raise ValidationError("조건에 이름이 필요하다", step="STEP 117a")
    cur = conn.execute(
        "INSERT INTO watch_query(account_id,name,conditions_json,min_grade,"
        "max_price_won,notify_on_new,notify_on_price,created_at,active)"
        " VALUES (?,?,?,?,?,?,?,?,1)",
        (account_id, name, json.dumps(conditions, ensure_ascii=False),
         min_grade, max_price_won, int(notify_on_new), int(notify_on_price),
         at))
    conn.commit()
    return int(cur.lastrowid)


def run_watch_queries(conn: sqlite3.Connection, calc_version: str,
                      at: str) -> dict:
    """활성 조건을 돌려 새로 맞는 매물을 적재한다 (STEP 117a).

    ★ 매 실행 후에 돈다.  신규는 hit 으로 쌓고, 기존은 가격 변동만 본다
    반환   {query_id: 새로 걸린 건수}
    """
    out: dict = {}
    rows = conn.execute(
        "SELECT query_id, conditions_json, min_grade, max_price_won "
        "FROM watch_query WHERE active = 1").fetchall()
    for qid, cond_json, min_grade, max_price in rows:
        cond = json.loads(cond_json or "{}")
        where = ["s.calc_version = ?"]
        args: list = [calc_version]
        for k, v in cond.items():
            clause = QUERY_FIELDS.get(k)
            if clause is None:
                continue          # 등록 시점에 막았지만 한 번 더 본다
            where.append(clause)
            args.append(v)
        # ★ 축 조건 (STEP 149g).  「HUD 있는 차」가 이 도구를 쓰는 이유다
        axis, bucket = cond.get("axis"), cond.get("bucket")
        if axis and bucket in AXIS_BUCKETS:
            where.append(
                "EXISTS (SELECT 1 FROM result_axis a "
                "WHERE a.listing_id = s.listing_id "
                "AND a.calc_version = s.calc_version "
                f"AND a.axis = ? AND {AXIS_BUCKETS[bucket]})")
            args.append(axis)
        if max_price is not None:
            where.append("l.price_current_won <= ?")
            args.append(max_price)
        if min_grade:
            # ★ 등급은 문자라 부등호가 안 통한다.  허용 목록으로 건다
            allowed = GRADE_ORDER[:GRADE_ORDER.index(min_grade) + 1]
            where.append(f"s.grade IN ({','.join('?' * len(allowed))})")
            args += list(allowed)
        sql = ("SELECT s.listing_id FROM result_score s "
               "JOIN core_listing l ON l.listing_id = s.listing_id WHERE "
               + " AND ".join(where))
        hits = [r[0] for r in conn.execute(sql, tuple(args))]
        added = 0
        for lid in hits:
            cur = conn.execute(
                "INSERT OR IGNORE INTO watch_query_hit"
                "(query_id,listing_id,first_hit_at,notified) VALUES (?,?,?,0)",
                (qid, lid, at))
            added += cur.rowcount or 0
        conn.execute("UPDATE watch_query SET last_run_at=? WHERE query_id=?",
                     (at, qid))
        out[qid] = added
    conn.commit()
    return out


def watch_query_rows(conn: sqlite3.Connection, account_id: int) -> list:
    """조건 목록과 지금 맞는 건수 (STEP 117a)."""
    return [{"query_id": q, "name": n, "conditions": json.loads(c or "{}"),
             "min_grade": g, "max_price_won": p, "active": bool(a),
             "last_run_at": lr, "hits": h}
            for q, n, c, g, p, a, lr, h in conn.execute(
                "SELECT w.query_id, w.name, w.conditions_json, w.min_grade, "
                "w.max_price_won, w.active, w.last_run_at, "
                "(SELECT COUNT(*) FROM watch_query_hit h "
                " WHERE h.query_id = w.query_id) "
                "FROM watch_query w WHERE w.account_id = ? "
                "ORDER BY w.query_id DESC", (account_id,))]


def close_watch_query(conn: sqlite3.Connection, query_id: int,
                      account_id: int) -> None:
    """조건 알림을 끈다 (STEP 117a).

    ★ 지우지 않는다.  active=0 으로 둔다 —
      「있었는데 껐다」가 기록되지 않으면 왜 안 오는지 알 수 없다
    ★ 남의 조건은 못 끈다 (STEP 111)
    """
    row = conn.execute(
        "SELECT account_id FROM watch_query WHERE query_id = ?",
        (query_id,)).fetchone()
    if row is None:
        raise ValidationError(f"그 조건이 없습니다: {query_id}",
                              step="STEP 117a")
    if row[0] != account_id:
        raise PolicyError("남의 조건은 끌 수 없습니다", step="STEP 111")
    conn.execute("UPDATE watch_query SET active = 0 WHERE query_id = ?",
                 (query_id,))
    conn.commit()
