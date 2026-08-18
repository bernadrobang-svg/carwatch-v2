# -*- coding: utf-8 -*-
"""다중 사이트 확장 (12장).

지시서   STEP 121 (착수 조건) · 123 (동일 차량) · 123a (V9) · 124 (회귀)
근거     1차에서 자리를 만들어 뒀으므로 이 장은 어댑터와 매핑 작업이다
금지     사이트별 점수를 직접 비교하는 것 — 수집 항목이 달라 분모가 다르다
         active 사이트가 1개인데 「단독 매물」이라 쓰는 것.  비교하지 않았을 뿐이다
         추정 결합.  결합 근거가 불명이면 표시하지 않는다
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field

from contracts import RegressionReport

STATUS_ACTIVE = "active"

WON_PER_MANWON = 10000
# 부동소수 비교 오차.  임계값이 아니라 수치 규격이다
FLOAT_EPSILON = 1e-9

# STEP 123 판정 문구.  active 사이트 수를 보고 고른다
MSG_NO_PEER = "비교 대상 없음 (수집 사이트 1곳)"
MSG_ONLY_HERE = "{site} 단독 매물"
MSG_MULTI = "{n}개 사이트에 게시 · 가격차 {spread}만"


@dataclass(frozen=True)
class CrossSiteMatch:
    vehicle_id: int
    listings: list[tuple[str, str, int]]  # (site, listing_id, price_won)
    price_spread_won: int
    match_source: str  # plate · vin · site_id
    confidence: str  # confirmed · probable
    message: str = ""


@dataclass
class ReadinessReport:
    """STEP 121 착수 조건.  하나라도 아니면 1차를 먼저 정리한다."""

    checks: dict[str, bool] = field(default_factory=dict)

    @property
    def ready(self) -> bool:
        return all(self.checks.values())


def active_sites(sites_cfg: dict) -> list[str]:
    return sorted(k for k, v in sites_cfg.items()
                  if isinstance(v, dict) and v.get("status") == STATUS_ACTIVE)


def match_cross_site(conn: sqlite3.Connection, vehicle_id: int,
                     sites_cfg: dict) -> CrossSiteMatch | None:
    """사이트 간 동일 차량.  가격만 비교한다 (STEP 123).

    ★ 1차는 active 사이트가 엔카 하나다.  「단독 매물」이라 쓰면 거짓이 된다.
    """
    rows = conn.execute(
        "SELECT site, listing_id, price_current_won FROM core_listing "
        "WHERE vehicle_id = ? AND status = 'active' ORDER BY site, listing_id",
        (vehicle_id,)).fetchall()
    if not rows:
        return None
    # 결합 근거는 vehicle_identity 가 갖는다 (STEP 30)
    head = conn.execute(
        "SELECT kind, confidence FROM vehicle_identity WHERE vehicle_id = ? "
        "ORDER BY CASE kind WHEN 'plate' THEN 1 WHEN 'vin' THEN 2 ELSE 3 END "
        "LIMIT 1", (vehicle_id,)).fetchone()
    if head is None:
        return None  # 결합 근거 불명 — 표시하지 않는다

    prices = [r[2] for r in rows if r[2] is not None]
    spread = (max(prices) - min(prices)) if len(prices) > 1 else 0
    sites = sorted({r[0] for r in rows})
    n_active = len(active_sites(sites_cfg))

    if n_active <= 1:
        msg = MSG_NO_PEER
    elif len(sites) == 1:
        msg = MSG_ONLY_HERE.format(site=sites[0])
    else:
        msg = MSG_MULTI.format(n=len(sites), spread=spread // WON_PER_MANWON)

    return CrossSiteMatch(vehicle_id, [tuple(r) for r in rows], spread,
                          head[0], head[1], msg)


def site_prices_of(conn: sqlite3.Connection, listing_id: int) -> list:
    """같은 차가 다른 사이트에 얼마로 올라 있는가 (개정 353 · V11-121).

    ★ 결합 근거는 vehicle_id 다 — 차대번호·번호판으로 이은 것이다 (STEP 30).
      제목이 같다는 이유로 잇지 않는다
    돌려줌   [(사이트, 표시가)] — 자기 자신은 뺀다.  사이트당 가장 싼 것 하나
    """
    rows = conn.execute(
        "SELECT o.site, MIN(o.price_current_won) FROM core_listing me"
        " JOIN core_listing o ON o.vehicle_id = me.vehicle_id"
        " WHERE me.listing_id = ? AND me.vehicle_id IS NOT NULL"
        "   AND o.listing_id <> me.listing_id AND o.site <> me.site"
        "   AND o.status = 'active' AND o.price_current_won IS NOT NULL"
        " GROUP BY o.site ORDER BY o.site", (listing_id,)).fetchall()
    return [(r[0], r[1]) for r in rows]


def rebuild_core_vehicle(conn: sqlite3.Connection, at: str) -> int:
    """core_vehicle 집계 갱신.  site_count 는 실제 사이트 수다."""
    n = 0
    for vk, sites, cnt, lo, hi in conn.execute(
        "SELECT vehicle_id, COUNT(DISTINCT site), COUNT(*),"
        " MIN(price_current_won), MAX(price_current_won) FROM core_listing "
        "WHERE vehicle_id IS NOT NULL GROUP BY vehicle_id"
    ).fetchall():
        conn.execute(
            "UPDATE core_vehicle SET site_count=?, listing_count=?,"
            " min_price_won=?, max_price_won=?, price_spread_won=?,"
            " updated_at=? WHERE vehicle_id=?",
            (sites, cnt, lo, hi,
             None if lo is None or hi is None else hi - lo, at, vk))
        n += 1
    conn.commit()
    return n


def regression_check(conn: sqlite3.Connection, baseline: dict,
                     calc_version: str, site: str = "encar"
                     ) -> RegressionReport:
    """사이트를 추가했는데 기존 점수가 바뀌면 CORE 가 오염된 것이다 (STEP 124).

    금지   「새 사이트 때문에 조금 바뀐 것」으로 넘기는 것
    """
    smis = gmis = dmis = 0
    samples: list[str] = []
    n = 0
    for lid, total, denom, grade in conn.execute(
        "SELECT s.listing_id, s.score_total, s.denominator, s.grade "
        "FROM result_score s JOIN core_listing l ON l.listing_id=s.listing_id "
        "WHERE s.calc_version=? AND l.site=?", (calc_version, site)
    ).fetchall():
        base = baseline.get(lid)
        if base is None:
            continue
        n += 1
        if abs(base["score_total"] - total) > FLOAT_EPSILON:
            smis += 1
            samples.append(f"{lid} score {base['score_total']}→{total}")
        if base["grade"] != grade:
            gmis += 1
            samples.append(f"{lid} grade {base['grade']}→{grade}")
        if abs(base["denominator"] - denom) > FLOAT_EPSILON:
            dmis += 1
            samples.append(f"{lid} denom {base['denominator']}→{denom}")
    return RegressionReport(calc_version, n, smis, gmis, dmis, samples[:20])


def snapshot_baseline(conn: sqlite3.Connection, calc_version: str,
                      site: str = "encar") -> dict:
    """회귀 시험 기준선.  1차 완료 시점 결과를 얼려 둔다 (STEP 121)."""
    return {
        r[0]: {"score_total": r[1], "denominator": r[2], "grade": r[3]}
        for r in conn.execute(
            "SELECT s.listing_id, s.score_total, s.denominator, s.grade "
            "FROM result_score s JOIN core_listing l "
            "ON l.listing_id=s.listing_id WHERE s.calc_version=? AND l.site=?",
            (calc_version, site))
    }


# ── STEP 121 착수 조건 ───────────────────────────────────────────────
# ★ core_vehicle 은 사이트를 가로지르는 개체다.  site 단일 컬럼을 갖지 않는다.
#   한 차량이 여러 사이트에 걸치므로 site_count 가 그 자리를 대신한다 (3장 STEP 35).
SITE_KEYED_TABLES = ("dict_enum", "dict_option_code",
                     "coefficient_history", "core_dealer")
CROSS_SITE_TABLES = {"core_vehicle": "site_count"}

# CORE 컬럼명에 들어 있으면 안 되는 사이트 고유 명칭 (0장 STEP 4)
SITE_SPECIFIC_WORDS = ("encar", "kcar", "kbcha")


def readiness(conn: sqlite3.Connection, sites_cfg: dict, target_site: str,
              calc_version: str) -> ReadinessReport:
    """하나라도 아니면 1차를 먼저 정리한다.

    그러지 않으면 2차를 붙이며 CORE 를 고치게 된다.
    """
    rep = ReadinessReport()
    rep.checks["1차 수집·판정·채점 동작"] = bool(conn.execute(
        "SELECT COUNT(*) FROM result_score").fetchone()[0])
    rep.checks["기준선 calc_version 고정"] = bool(conn.execute(
        "SELECT COUNT(*) FROM result_score WHERE calc_version=?",
        (calc_version,)).fetchone()[0])
    spec = sites_cfg.get(target_site)
    rep.checks["sites.json 에 planned 등록"] = bool(
        spec and spec.get("status") in ("planned", STATUS_ACTIVE))

    ok = True
    for table in SITE_KEYED_TABLES:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        if "site" not in cols:
            ok = False
    for table, col in CROSS_SITE_TABLES.items():
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        if col not in cols:
            ok = False
    rep.checks["site 키가 들어가 있다"] = ok

    bad = []
    for table in ("core_listing", "core_inspection", "core_record"):
        for r in conn.execute(f"PRAGMA table_info({table})"):
            name = r[1].lower()
            if name.startswith("site_"):
                continue  # site_* 는 사이트 고유값 전용 접두다 (STEP 4)
            if any(w in name for w in SITE_SPECIFIC_WORDS):
                bad.append(f"{table}.{r[1]}")
    rep.checks["CORE 컬럼명에 사이트 고유 명칭 없음"] = not bad
    return rep


def load_sites(path: str = "config/sites.json") -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def site_addition_regression(conn, before: dict, site: str) -> list[str]:
    """★ 사이트를 늘려도 기존 사이트 결과가 바뀌면 안 된다 (V9-04 · STEP 124).

    before   {listing_id: (score_total, grade)}  새 사이트 추가 전 스냅샷
    금지     새 사이트 매물이 기존 매물의 점수·등급을 흔드는 것
    근거     결합은 「같은 차인가」를 볼 뿐이다.  판정은 매물마다 독립이다
    """
    bad = []
    for lid, (score, grade) in before.items():
        row = conn.execute(
            "SELECT s.score_total, s.grade FROM result_score s "
            "JOIN core_listing l USING(listing_id) "
            "WHERE s.listing_id = ? AND l.site <> ?", (lid, site)).fetchone()
        if row and (abs(row[0] - score) > FLOAT_EPSILON or row[1] != grade):
            bad.append(f"listing {lid}: {score}/{grade} → {row[0]}/{row[1]}")
    return bad
