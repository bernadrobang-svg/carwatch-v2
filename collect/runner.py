# -*- coding: utf-8 -*-
"""수집 실행 규칙.

지시서   2장 STEP 23 (facet 필수 축) · STEP 24 (요청 정책 · 실패 3종)
         STEP 25 (매물당 요청 구성) · STEP 27 (수집 검증 훅)
근거     수집은 받아서 저장만 한다.  해석은 L3 이 한다.
금지     skip_done 류 건너뛰기 플래그.  v1 은 208건 중 76건만 받았고
         점검부 55% · 이력 63% · 틴팅 불명 95% 가 그 결과였다.
         축 수로 검증하는 것 — 38축 차종에서 fatal 이 난다.  필수 축 집합으로 본다.
"""
from __future__ import annotations

import json
from dataclasses import dataclass

from adapters.encar import FACET_REQUEST_KINDS
from contracts import TargetSpec

# ── 코드 상수 (2장 상수표) ───────────────────────────────────────────
# 「이것만은 반드시 있어야 한다」는 규칙이므로 코드가 맞다.
REQUIRED_FACET_AXES: frozenset[str] = frozenset(
    {
        "Options",
        "JatoOptions",
        "FuelType",
        "Color",
        "SeatColor",
        "Condition",
        "SellType",
        "LeaseType",
    }
)
# ★ Badge 는 facet 에 오지 않는다 (실측).  트림 원천은 목록 응답이다
TRIM_FIELD = "Badge"

# 매물당 요청.  condition 값과 무관하게 전부 던진다 (STEP 25).
# ★ 어댑터가 정본이다.  두 곳에 적으면 순서가 어긋나 status 가 뒤섞인다
from adapters.encar import LISTING_ENDPOINT_KINDS as LISTING_ENDPOINTS  # noqa: E402
# ★ 진단 원문이 오는 값.  1·2 는 404 다 (2026-08-14 실측 3요청 · STEP 21b)
from validate.v1_collect import DIAG_HAS_REPORT  # noqa: E402
from parse.encar.mapping import (  # noqa: E402
    parse_platform_check, parse_ev_battery, parse_inspection_summary,
    parse_record_summary, parse_sellingpoint,
)

EXTRA_PARSERS = {
    "record_summary": parse_record_summary,
    "platform_check": parse_platform_check,
    "inspection_summary": parse_inspection_summary,
    "ev_battery": parse_ev_battery,
    "sellingpoint": parse_sellingpoint,
}

# 개정 296·297 로 늘어난 원문의 파서.  ★ core_listing 을 보강만 한다 —
# 새 표를 만들지 않는다.  매물당 한 줄짜리 값들이다
# 축은 Type 이 'Aspect' 인 노드다.  Name 만으로 훑지 않는다 (STEP 23).
ASPECT = "Aspect"

# 진행 표시 주기.  건마다 찍으면 화면이 넘친다 (형식)
PROGRESS_EVERY = 20
# 단위 환산 (2장 상수표 · V4-13).  ★ 옵션가 사전은 만원 단위다 (개정 292 ③)
WON_PER_MANWON = 10_000


# ── 차종 · collect_group (STEP 23 collect_group) ─────────────────────
@dataclass(frozen=True)
class CollectGroup:
    """같은 쿼리를 공유하는 target 묶음.  수집은 이 단위로 1회다.

    실측   G80_25T 와 G80_EV 는 ModelGroup.G80 하나의 쿼리다.  연료 조건이 없다.
    ★      facet 도 이 단위다.  「G80_EV 의 facet」은 존재하지 않는다.
           이것을 EV 근거로 쓰면 안 된다 (7장 STEP 79 실사고).
    """

    group_key: str
    site: str
    site_query: dict
    target_keys: tuple[str, ...]

    def as_target_spec(self) -> TargetSpec:
        return TargetSpec(
            target_key=self.group_key,
            label=self.group_key,
            site_query={self.site: self.site_query},
        )

    # site_query 는 계층 조건이고, 범위 조건(year·price)은 target 최상위다.
    # build_q 는 둘을 합친 dict 를 받는다 (STEP 17a).


def load_targets(path: str = "config/targets.json") -> dict[str, dict]:
    """본문 예시(0장 STEP 6)가 정본이다 — 최상위가 target_key 다.

    SPEC_DEFAULT_* · _ 로 시작하는 메타 키는 차종이 아니다.
    """
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        k: v for k, v in raw.items()
        if isinstance(v, dict) and "collect_group" in v
    }


def collect_groups(targets: dict[str, dict], site: str) -> list[CollectGroup]:
    """target 을 collect_group 으로 묶는다.

    expected 산출은 target 수가 아니라 이 목록의 길이로 센다 (5장 STEP 53).
    묶지 않으면 같은 매물을 두 번 받고 두 target 에 중복 적재된다.
    """
    # ★★ 묶는 열쇠는 ★ 이름이 아니라 ★ 쿼리다 (개정 632 · 마스터 「한 사이트 전담으로 묶지 마라」).
    #   ★ 실측 08-24 — 수입 8종이 ★ `collect_group="multi"` 로 한 이름이 되자
    #     ★ 먼저 온 BMW X3 쿼리 ★ 하나만 남고 ★ 나머지 일곱이 조용히 사라졌다
    #   ★ 같은 쿼리끼리만 묶는다 — ★ G80_25T·G80_EV 는 쿼리가 같아 그대로 한 묶음이다
    bucket: dict[tuple, list[str]] = {}
    query: dict[tuple, dict] = {}
    label: dict[tuple, str] = {}
    for key, spec in targets.items():
        if site not in spec["site_query"]:
            continue
        merged = {k: v for k, v in spec["site_query"][site].items()
                  if not str(k).startswith("_")}
        merged["Hidden"] = "N"
        merged["MultiViewHidden"] = "N"
        if spec.get("year_range"):
            merged["Year_range"] = spec["year_range"]
        if spec.get("price_range"):
            merged["Price_range"] = spec["price_range"]
        gk = (spec["collect_group"],
              tuple(sorted((k, str(v)) for k, v in merged.items())))
        bucket.setdefault(gk, []).append(key)
        query.setdefault(gk, merged)
        # ★ 이름이 겹치면 ★ 무엇으로 갈렸는지 이름에 적는다 — ★ 화면이 그것을 낸다
        said = spec["collect_group"]
        if said == "multi":
            said = f"multi:{merged.get('ModelGroup') or key}"
        label.setdefault(gk, said)
    return [
        CollectGroup(label[gk], site, query[gk], tuple(sorted(keys)))
        for gk, keys in sorted(bucket.items(), key=lambda kv: label[kv[0]])
    ]


# ── facet 축 (STEP 23) ───────────────────────────────────────────────
def facet_axes(body: dict) -> dict[tuple[str, str], dict]:
    """(Name, Type) 을 키로 축을 뽑는다.

    금지   Name 을 키로 하는 dict 에 담는 것.
           Price 는 Type=RangeAction 과 Type=Aspect 두 노드로 온다.
           Name 만 쓰면 RangeAction 이 Aspect 를 덮어쓰거나 중복 등록된다.
    """
    out: dict[tuple[str, str], dict] = {}
    stack = [body]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            name, typ = node.get("Name"), node.get("Type")
            if isinstance(name, str) and isinstance(typ, str):
                out[(name, typ)] = node
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(v for v in node if isinstance(v, (dict, list)))
    return out


def aspect_names(body: dict) -> set[str]:
    return {n for (n, t) in facet_axes(body) if t == ASPECT}


def check_facet_axes(unspecified_body: dict,
                     _unused: dict | None = None) -> list[str]:
    """필수 축 집합 검사.  축 수로 보지 않는다 (STEP 23).

    ★ Badge 는 검사하지 않는다.  facet 이 주지 않는다 —
      계층의 다음 단계만 주므로 ModelGroup 지정 시 Model 이 온다.
    반환   위반 목록.  빈 목록이면 통과 (V4-12 · fatal)
    """
    have = aspect_names(unspecified_body)
    return [f"미지정 응답에 필수 축 없음: {axis}"
            for axis in sorted(REQUIRED_FACET_AXES - have)]


# ── 실패 3종 해석 (STEP 24 · STEP 25a) ───────────────────────────────
def interpret_failure(
    http_codes: list[int | None], ok_count: int, result_count: int
) -> tuple[str, str]:
    """관측 → 원인 판정 → 조치.

    전량 오류는 코드 문제로 가정한다.  차단으로 단정하지 않는다.
    v1 은 record 후보 5개가 전부 404 였을 때 「없는 엔드포인트」로 단정했다.
    실제로는 /open 접미사 문제였다.

    반환   (판정, 조치)
    """
    n = len(http_codes)
    if n and ok_count == 0 and len(set(http_codes)) == 1:
        code = http_codes[0]
        if code == 404:
            return ("경로 오류", "URL 실측 요청 (STEP 25a)")
        if code in (401, 403):
            return ("헤더 · 인증", "헤더 실측 요청 (STEP 25a)")
        if code == 400:
            return ("쿼리 문법", "쿼리 조립 규칙 확인")
        return ("전량 오류", "마스터에게 URL 검증 요청 (STEP 25a)")
    if ok_count > 0 and result_count == 0:
        return ("수집 쿼리 오류", "매물 없음으로 단정하지 않는다. 쿼리 조립 확인")
    if ok_count < n:
        return ("개별 매물 사유", "not_found · empty 로 기록. 정상")
    return ("정상", "")


# ── 수집 종료 자동 산출 (STEP 27) ────────────────────────────────────
def collect_check(expected: int, requested: int, tally: dict[str, int],
                  raw_rows: int, rejected: int,
                  not_requested: int | None = None) -> list[str]:
    """어긋나면 다음 STEP 으로 넘어가지 않는다.

    ①⑥ 이 핵심이다.  v1 은 「애초에 안 던진 것」을 아무도 세지 않았다.

    not_requested   None 이면 expected - requested 로 유도한다.
                    이때 ① 은 항등식이라 아무것도 잡지 못한다.
                    *_status 에서 독립적으로 센 값을 넘겨야 ① 이 일한다 —
                    「던졌다고 보고한 수」와 「상태가 남은 수」의 어긋남이 v1 사고다.
    """
    bad = []
    if not_requested is None:
        not_requested = expected - requested
    answered = sum(tally.get(k, 0) for k in ("ok", "empty", "not_found", "error"))
    if requested + not_requested != expected:
        bad.append(f"① expected {expected} != requested {requested} + not_requested {not_requested}")
    if requested != answered:
        bad.append(f"② requested {requested} != 응답 합 {answered}")
    if rejected:
        bad.append(f"③ 형식 검증 거부 {rejected}건 — URL · 응답 변경 의심 (STEP 25a)")
    if tally.get("ok", 0) == 0:
        bad.append("④ ok 0건 — 수집 0건은 성공이 아니다")
    if raw_rows != answered:
        bad.append(f"⑤ raw_response 신규 {raw_rows} != 응답 합 {answered}")
    if not_requested:
        bad.append(f"⑥ not_requested {not_requested}건 — 미완성 매물이 남았다")
    return bad


# ★ 요청 조립은 SiteAdapter 메서드다 (STEP 17a · 2장 정의서).
#   별도 build_* 래퍼를 두지 않는다.  runner 는 어댑터에 위임한다.
#   지시서 15판에서 build_list_request 계열이 SiteAdapter.list_url 로 일원화됐다.


# ── 단계 실행기 (STEP 47 S0~S3) ──────────────────────────────────────
# run_step 이 주입받아 호출한다.  순서 · 조건 · 중단은 pipeline 이 책임진다.
import random  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import time  # noqa: E402


from collect.fetcher import fetch  # noqa: E402
from collect.pipeline import step_report  # noqa: E402
from parse.classify import classify  # noqa: E402
from parse.encar.mapping import (  # noqa: F401
    parse_diagnosis,
    parse_diagnosis_items,
    parse_with_issues,  # noqa: E402
    parse_detail, parse_inspection, parse_list_item, parse_record,
    unpack_envelope,
)
from store.core import (  # noqa: E402
    build_identities, flush_dealer_pii, resolve_dealer_id, resolve_listing_id, resolve_vehicle_id,
    split_pii, upsert_child, upsert_core, upsert_dealer, upsert_vehicle,
)
from store.pii import load_key  # noqa: E402
from collect.fetcher import reject_reason, verify_shape  # noqa: E402
from store.raw import raw_body, save_facet, save_raw  # noqa: E402
from store.core import sweep_gone  # noqa: E402
# ★ 배치 단계가 쓰기 잠금을 오래 쥐지 않게 끊는다 (08-26)
from store.raw import tick as raw_tick  # noqa: E402


# 단위 환산.  임계값이 아니다 (V4-13 은 임계·경계·비율·표본 수를 막는다)
MS_PER_SEC = 1000


class FailStreak:
    """같은 http_code 로 연속 N회 실패하면 즉시 중단한다 (STEP 52).

    ★ 같은 코드일 때만 센다.
      404 가 20건 연속인 것은 「그 매물들이 없는 것」일 수 있다 — 그건 결과다.
      403 · 429 · 5xx 가 연속이면 차단 · 과부하다.
    필수   ok 가 하나라도 나오면 카운터를 0 으로 되돌린다
    금지   전체 실패율로 판정하는 것.  앞이 성공했으면 비율이 안 오른다
    """

    def __init__(self, limit: int) -> None:
        self.limit = int(limit)
        self.code: int | None = None
        self.count = 0

    def observe(self, res) -> None:
        if res.status == "ok" or res.status == "empty":
            self.code, self.count = None, 0
            return
        code = getattr(res, "http_code", None)
        if code is not None and code == self.code:
            self.count += 1
        else:
            self.code, self.count = code, 1

    @property
    def tripped(self) -> bool:
        return self.limit > 0 and self.count >= self.limit

    def reason(self) -> str:
        return (f"같은 응답 코드 {self.code} 로 연속 {self.count}회 실패. "
                f"차단·과부하를 의심한다 (STEP 25a · 52)")


def _sleep(cfg, rng) -> None:
    """간격은 정책값이다.  코드에 박지 않는다 (STEP 24)."""
    lo, hi = cfg["interval_sec"]
    time.sleep(rng.uniform(lo, hi))


def _log_request(conn, ctx, kind, source_id, url, res, elapsed_ms, attempt=1):
    conn.execute(
        "INSERT INTO audit_request"
        "(run_id,site,kind,source_id,url,http_code,status,elapsed_ms,attempt,"
        " requested_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (ctx.run_id, ctx.site, kind, source_id, url, res.http_code, res.status,
         elapsed_ms, attempt, res.fetched_at.isoformat()),
    )
    conn.commit()


def _save_issues(conn, listing_id: int, issues: list, parse_version: str,
                 at: str) -> None:
    """★ 「값이 없다」와 「우리가 못 읽었다」를 가른다 (STEP 19a)."""
    for endpoint, path, reason, sample in issues:
        conn.execute(
            "INSERT OR REPLACE INTO core_parse_issue"
            "(listing_id,endpoint,json_path,reason,raw_sample,parse_version,"
            " detected_at) VALUES (?,?,?,?,?,?,?)",
            (listing_id, endpoint, path, reason, sample, parse_version, at))


def make_executors(adapter, fetcher, clock, cfg, targets: dict,
                   backup_path: str | None = None, rng=None,
                   root_dir: str = ".", progress=None,
                   resume: bool = False) -> dict:
    """S0~S3 실행기.  I/O 는 전부 주입받는다 (0장 STEP 2).

    progress   진행 표시.  ★ 없으면 단계가 끝나야 한 줄이 나와
               멈춘 것과 구분이 안 된다 (STEP 53)
    resume     끊긴 실행을 이어서 한다 (5장 STEP 52).
               ★ 기본은 False 다 — 새 수집은 전건을 다시 던진다.
                 skip_done 을 기본으로 두면 v1 처럼 208건 중 76건만 받는다
               ★ True 일 때만 should_refetch 를 본다.  ok·empty·not_found 는
                 이미 답을 받은 것이라 다시 안 던진다.  error·미요청만 던진다
    """
    from collect.pipeline import silent_progress

    say = progress or silent_progress
    rng = rng or random.Random()
    groups = collect_groups(targets, adapter.site_code)
    schema = adapter.endpoint_schema()
    # ★ 키가 없으면 시작하지 않는다.  임시 키는 다음 실행과 결합을 깬다 (STEP 35)
    pii_key = load_key(os.path.join(root_dir, "secrets", "plate_hmac.key"))

    # ── S0 백업 ──────────────────────────────────────────────────────
    def s0(conn, ctx):
        if backup_path:
            src = conn.execute("PRAGMA database_list").fetchall()[0][2]
            if src:
                shutil.copy2(src, backup_path)
        return step_report("S0", None, 1, {"ok": 1}, 0, 0.0), 1

    # ── S1 목록 ──────────────────────────────────────────────────────
    streak_limit = int(cfg.get("fail_streak_limit") or 0)

    # ★ --target 은 S1·S2 만이 아니라 뒤 단계에도 걸려야 한다.
    #   S5 는 core_listing 의 active 를 읽으므로, 앞선 전 차종 실행의
    #   매물이 남아 있으면 범위를 벗어난 요청이 나간다 (실측: 240건 지정에 30,580요청)
    scope = tuple(sorted(targets))

    def _scope(sql: str, alias: str = "") -> tuple[str, tuple]:
        """★ 차종 범위 ＋ ★ **사이트**로 좁힌다.

        ★★★ 08-27 실측 — ★ 사이트를 안 좁혀 ★ 엔카 상세 API 에
          ★ ★ **현대인증 162 · K카 4 · 헤이딜러 1** 의 매물번호를 넣고 있었다.
          ★ ★ `https://api.encar.com/v1/readside/vehicle/GJU260527028268` → ★ **400**
          ★ ★ 그 회차의 ★ `detail` · `inspection` 이 ★ **전량 실패**였다.
            ★ 마지막으로 성공한 상세가 ★ 08-24T07:41 이다
        ★★ ★ `V1-08`(동일 코드 실패율 100%)이 ★ 여러 회차 이것을 말하고 있었다 —
          ★ 나는 ★ 「수집이 도는 중이라 그렇다」로 ★ 넘겼다.  ★ 내 잘못이다
        ★ ★ 뿌리는 ★ 하나다 — ★ `core_listing` 에 ★ 여러 사이트가 들어왔는데
          ★ ★ **엔카 전용 경로가 사이트로 안 좁혀 있었다** (`S46-78` 과 같은 자리다)
        """
        col = f"{alias}.target_key" if alias else "target_key"
        site_col = f"{alias}.site" if alias else "site"
        return (f"{sql} AND {site_col} = ?"
                f" AND {col} IN ({','.join('?' * len(scope))})",
                (adapter.site_code, *scope))

    def s1(conn, ctx):
        """봉투 1건 = raw_response 1행.  매물 단위로 쪼개지 않는다 (STEP 18a)."""
        t0 = time.time()
        tally = {"ok": 0, "empty": 0, "not_found": 0, "error": 0}
        rejected = rows = expected = 0
        streak = FailStreak(streak_limit)
        halted = None
        for gi, g in enumerate(groups, start=1):
            spec = g.as_target_spec()
            page = 0
            seen = 0
            total = None
            while True:
                # ★ 진행 분모를 요청 수로 통일한다.  완료 줄과 단위가 같아야 한다
                say("S1", f"{g.group_key} p{page + 1}"
                    + (f" · 매물 {seen}/{total}" if total else ""),
                    rows, expected or 0)
                req = adapter.list_url(spec, page)
                st = time.time()
                res = fetch(req, fetcher, "list", clock)
                _log_request(conn, ctx, "list", None, req.url, res,
                             int((time.time() - st) * MS_PER_SEC))
                tally[res.status] = tally.get(res.status, 0) + 1
                streak.observe(res)
                if streak.tripped:
                    halted = streak.reason()
                    break
                r = save_raw(conn, res, schema["list"], adapter.site_code, None,
                             req.url, req.headers, verify=verify_shape, reason=reject_reason,
                            run_id=ctx.run_id)
                rows += 1
                if r == "rejected":
                    rejected += 1
                    break
                if res.status != "ok":
                    break
                body = res.raw or {}
                items = body.get("SearchResults") or []
                if total is None:
                    # ★ 페이지 수는 첫 응답의 Count 로 확정된다 (STEP 18a)
                    total = int(body.get("Count") or 0)
                    expected += _pages_for(total, adapter._page_size)
                seen += len(items)
                if not items or seen >= total:
                    break
                page += 1
                _sleep(cfg, rng)
        rep = step_report("S1", None, max(expected, rows), tally, rejected,
                          time.time() - t0)
        if halted:
            rep.halted = True
            rep.halt_reason = halted
        return rep, rows

    # ── S2 facet ─────────────────────────────────────────────────────
    def s2(conn, ctx):
        """collect_group 당 2회.  미지정만으로는 Badge 가 오지 않는다 (STEP 23)."""
        t0 = time.time()
        tally = {"ok": 0, "empty": 0, "not_found": 0, "error": 0}
        rejected = rows = 0
        streak = FailStreak(streak_limit)
        halted = None
        bodies: dict[str, dict[str, dict]] = {}
        for gi, g in enumerate(groups, start=1):
            reqs = adapter.facet_urls(g.as_target_spec())
            for kind, req in zip(FACET_REQUEST_KINDS, reqs, strict=True):
                say("S2", f"{g.group_key} {kind}", rows,
                    len(groups) * len(FACET_REQUEST_KINDS))
                st = time.time()
                res = fetch(req, fetcher, "facet", clock)
                _log_request(conn, ctx, "facet", None, req.url, res,
                             int((time.time() - st) * MS_PER_SEC))
                tally[res.status] = tally.get(res.status, 0) + 1
                streak.observe(res)
                if streak.tripped:
                    halted = streak.reason()
                    break
                rows += 1
                if res.status != "ok":
                    _sleep(cfg, rng)
                    continue
                axes = aspect_names(res.raw)
                save_facet(conn, res, adapter.site_code, g.group_key, kind,
                           req.url, len(axes))
                bodies.setdefault(g.group_key, {})[kind] = res.raw
                _sleep(cfg, rng)
        # 필수 축 집합 검사.  축 수로 보지 않는다 (V4-12 · fatal)
        problems = []
        for gk, b in bodies.items():
            for msg in check_facet_axes(b.get("unspecified") or {}):
                problems.append(f"{gk}: {msg}")
        rep = step_report("S2", None, len(groups) * len(FACET_REQUEST_KINDS),
                          tally, rejected, time.time() - t0)
        if problems:
            rep.halted = True
            rep.halt_reason = " / ".join(problems)
        if halted:
            rep.halted = True
            rep.halt_reason = halted
        return rep, rows

    # ── S3 사전 ──────────────────────────────────────────────────────
    def s3(conn, ctx):
        from tools.build_dict import AXIS_SOURCES, build_dict

        t0 = time.time()
        at = clock.now().isoformat()
        r = build_dict(conn, adapter.site_code, ctx.dict_version, at)
        n = len(AXIS_SOURCES) - 1  # option_model 은 S8 이 담당한다
        rep = step_report("S3", None, n, {"ok": n}, 0, time.time() - t0)
        if r.conflicts:
            rep.halted = True
            rep.halt_reason = f"사전 충돌 {r.conflicts}"
        return rep, n

    # ── S4 목록 파싱 ─────────────────────────────────────────────────
    def s4(conn, ctx):
        """봉투를 펼쳐 core_listing 에 넣는다.  분류는 1단 잠정이다 (STEP 46).

        펼치는 것은 파싱이다.  저장이 아니다 (STEP 18a).
        """
        t0 = time.time()
        at = clock.now().isoformat()
        rows = ok = 0
        # ★ 신규 수집은 이번 run_id 봉투만 펼친다 (STEP 50a).
        #   옛 봉투는 이미 CORE 에 있다.  파싱 규칙이 바뀌면 전체를 훑는다
        from collect.pipeline import ENVELOPE_ALL, envelope_scope

        scope_kind = envelope_scope(getattr(ctx, "reprocess_reason", None))
        # ★ 반입분은 봉투가 아니다.  CSV·ID 목록을 json.loads 하면 죽는다.
        #   반입은 이미 core_listing 에 앉았다 — S4 가 다시 펼칠 것이 없다
        #   (13장 STEP 136a 「출력 S4 결과와 같은 형태로 core_listing 에 반영」)
        # ★ 봉투 시각을 함께 가져와 오래된 것부터 적용한다 (STEP 29).
        #   그래야 마지막에 적용되는 것이 가장 새 관측이다
        # ★★★★ 08-29 (개정 838) — ★ 「끝까지 받았나」를 알아야 ★ gone 을 매긴다.
        #   ★ 그러려면 ★ `request_url` 이 있어야 한다 — ★ 같은 질의의 쪽들을 묶는다
        # ★★★★ 08-29 — ★ **사이트를 좁힌다.**  ★ 없던 조건이다.
        #   ★ `endpoint='list'` 에는 ★ 엔카만 있는 것이 아니다 —
        #     ★ 실측 08-29 ★ `volvo_selekt` 40쪽 · `lexus_certified` 36쪽이 섞여 있다.
        #   ★ 이 파서는 ★ **엔카 봉투 전용**이다 (`parse.encar.unpack_envelope`).
        #   ★★ ★ 더 나쁜 것 — ★ 아래 gone 쓸기가 ★ 남의 사이트 목록을 보고
        #     ★ ★ **엔카 차종을 판정할 뻔했다**.  ★ 그것이 산 차를 죽인다.
        #   ★ S6 은 08-26 에 같은 까닭으로 이미 좁혔다 — ★ S4 만 남아 있었다
        sql = ("SELECT body, fetched_at, request_url FROM raw_response "
               "WHERE endpoint='list' AND status='ok' AND origin <> 'import'"
               "  AND site = ?")
        args: tuple = (adapter.site_code,)
        if scope_kind != ENVELOPE_ALL:
            # 실행 시작 시각으로 이번 실행분을 가른다.
            # ★ 밖에서 받아 온 봉투(browser)는 시각으로 못 가른다 —
            #   파이프라인 밖에서 먼저 저장되기 때문이다.  그것을 빼면
            #   목록을 392쪽 받아 두고도 S4 가 0건을 펼친다 (실측 08-16).
            #   다시 펼쳐도 upsert 라 결과가 같다 (STEP 50a 의 뜻은
            #   「옛 수집분을 매번 훑지 않는다」이지 「밖에서 온 것을 버린다」가 아니다)
            sql += " AND (fetched_at >= ? OR origin = 'browser')"
            args = (adapter.site_code, ctx.started_at.isoformat())
        sql += " ORDER BY fetched_at, id"
        skipped_old = 0
        # ★★★ 질의별로 ★ 「몇 건이라 했나(Count)」와 ★ 「몇 건을 봤나」를 센다.
        #   ★ 쪽넘김은 `sr=|…|offset|rows` 로 나뉜다 — ★ 그 자리를 지운 것이 질의다
        q_declared: dict = {}
        q_seen: dict = {}
        q_targets: dict = {}
        for _b, seen_at, _url in conn.execute(sql, args).fetchall():
            body = raw_body(_b)
            _count, items = unpack_envelope(json.loads(body))
            qkey = _query_key(_url)
            q_declared[qkey] = max(q_declared.get(qkey, 0), int(_count or 0))
            q_seen.setdefault(qkey, set())
            q_targets.setdefault(qkey, set())
            for item in items:
                rows += 1
                if rows % PROGRESS_EVERY == 0:
                    say("S4", "매물 적재", rows, 0)
                    # ★ 잠금 창을 끊는다 (08-26) — ★ 화면의 쓰기가 죽지 않게
                    raw_tick(conn, rows)
                parsed = parse_list_item(item, adapter.site_code)
                parsed["listing_id"] = resolve_listing_id(
                    conn, adapter.site_code, parsed["source_id"], at)
                # ★ 이미 더 새 관측이 있으면 적용하지 않는다.
                #   옛 봉투를 다시 읽어 옛 값을 새 값 위에 쓰면
                #   불변 가드(STEP 29)가 걸려 S4 가 통째로 멈춘다 —
                #   그 뒤 S5·S6 이 「선행 단계 미완료」로 줄줄이 실패했다
                #   (실측 08-18 — 큐 작업 40건이 그렇게 죽었다)
                # ★ 아직 안 실린 빈 행(status='new')은 건너뛰지 않는다.
                #   resolve_listing_id 가 방금 만든 행은 last_seen 이
                #   「지금」이라 모든 옛 봉투가 오래된 것으로 보인다 —
                #   그러면 새 매물이 영영 안 실린다 (실측 08-18: 38건)
                have = conn.execute(
                    "SELECT last_seen, status FROM core_listing"
                    " WHERE listing_id=?", (parsed["listing_id"],)).fetchone()
                if (have and have[1] != "new" and have[0] and seen_at
                        and str(have[0]) > str(seen_at)):
                    skipped_old += 1
                    continue
                cg = _group_of(parsed, groups)
                cls = classify_in_group(targets, groups, cg,
                                        parsed.get("fuel_raw"),
                               parsed.get("trim_badge"), None, None)
                parsed.update(
                    target_key=cls.target_key,
                    classify_stage=cls.stage,
                    classify_source=cls.source,
                    classify_conflict=1 if cls.conflict else 0,
                    # ★ 분류가 대상을 못 정하면 out_of_scope 다.
                    #   active 로 두면 S5 가 안 가져가는데 V1-07 은 4종 상태를
                    #   요구한다 — 「지정하지 않은 매물이 활성으로 남는다」
                    status="active" if cls.target_key else "out_of_scope",
                    collected_at=at,
                    parsed_at=at,
                    parse_version=ctx.parse_version,
                )
                upsert_core(conn, parsed, at)
                ok += 1
                # ★ 이 질의가 ★ 무엇을 봤나 · ★ 어느 차종에 닿았나
                q_seen[qkey].add(str(parsed["source_id"]))
                if cls.target_key:
                    q_targets[qkey].add(cls.target_key)
        if skipped_old:
            # ★ 조용히 건너뛰지 않는다.  몇 건을 왜 건너뛰었는지 남긴다
            say("S4", f"옛 봉투 {skipped_old}건 건너뜀 — 더 새 관측이 있다",
                rows, rows)
        # ★★ 건너뛴 옛 봉투는 「미완성」이 아니다 — 이미 더 새 값이 실려 있다.
        #   expected 에서 뺀다 (S5 의 done_before 와 같은 자리).
        #   ★ 실측 08-20 — 안 빼면 not_requested 26,865건으로 S4 가 매번
        #     중단하고, 그 뒤 S5·S6·S9·S10 이 통째로 안 돈다.
        #     목록을 저장할 때마다 실패한 작업만 쌓였다
        # ★★★★★ 08-29 (개정 838 · 오판 161) — ★ **팔린 차를 거른다.**
        #   ★ `mark_gone` 을 ★ `tools/collect_kcar.py` 하나만 불러
        #     ★ 일곱 사이트가 ★ 안 걸렀다.  ★ 엔카가 88% 다 —
        #     ★ ★ 마스터께서 ★ 두 달째 팔린 차를 보셨다.
        #   ★★ ★ **끝까지 받은 질의만** 쓴다 — ★ 「몇 건이라 했나(Count)」에
        #     ★ ★ 「몇 건을 봤나」가 닿아야 한다.
        #   ★★ ★ 안 끝난 질의가 ★ 건드린 차종은 ★ **통째로 뺀다** —
        #     ★ ★ 한 차종을 ★ 두 질의가 나눠 받았는데 ★ 하나만 끝났으면
        #       ★ ★ 반만 본 것이다.  ★ 반만 보고 매기면 ★ **산 차를 죽인다**
        swept = 0
        seen_by_target: dict = {}
        blocked_targets: set = set()
        for qkey, seen in q_seen.items():
            declared = q_declared.get(qkey, 0)
            done = declared > 0 and len(seen) >= declared
            for tk in q_targets.get(qkey, ()):
                if done:
                    seen_by_target.setdefault(tk, set()).update(seen)
                else:
                    blocked_targets.add(tk)
        for tk in sorted(set(seen_by_target) - blocked_targets):
            swept += sweep_gone(conn, adapter.site_code, tk,
                                seen_by_target[tk], at)
        if blocked_targets:
            # ★ 조용히 건너뛰지 않는다.  무엇을 왜 안 매겼는지 남긴다
            say("S4", f"끝까지 못 받은 차종 {len(blocked_targets)}종은 "
                      "gone 을 안 매겼다", rows, rows)
        if swept:
            say("S4", f"목록에 없어 gone 으로 매긴 것 {swept}건 "
                      f"({len(seen_by_target) - len(blocked_targets)}종)",
                rows, rows)
        rep = step_report("S4", None, rows - skipped_old, {"ok": ok}, 0,
                          time.time() - t0)
        return rep, ok

    # ── S5 상세 수집 ─────────────────────────────────────────────────
    def s5(conn, ctx):
        """매물당 4종 전건.  condition 값과 무관하게 전부 던진다 (STEP 25).

        금지   skip_done 류 건너뛰기 플래그
        """
        t0 = time.time()
        tally = {"ok": 0, "empty": 0, "not_found": 0, "error": 0}
        rejected = rows = 0
        streak = FailStreak(streak_limit)
        halted = None
        lids = conn.execute(
            *_scope("SELECT listing_id, source_id FROM core_listing "
                    "WHERE status='active'")
        ).fetchall()
        skipped = 0
        done_before = 0
        # ★ 재개일 때만 이미 답을 받은 것을 뺀다 (STEP 52 · should_refetch)
        have: dict = {}
        if resume:
            cols = ", ".join(f"{k}_status" for k in LISTING_ENDPOINTS)
            for row in conn.execute(
                    *_scope(f"SELECT listing_id, {cols} FROM core_listing "
                            f"WHERE status='active'")):
                have[row[0]] = dict(zip(LISTING_ENDPOINTS, row[1:],
                                        strict=True))
        for i, (lid, sid) in enumerate(lids, start=1):
            diag_grade = None
            for kind, req in zip(LISTING_ENDPOINTS, adapter.detail_urls(sid), strict=True):
                if resume:
                    from collect.pipeline import should_refetch

                    got = (have.get(lid) or {}).get(kind)
                    if got is not None and not should_refetch(got):
                        # ★ 이미 답을 받았다.  「건너뛴」 것이 아니라
                        #   「받은 것」이다 — expected 에서도 뺀다
                        done_before += 1
                        if kind == "detail":
                            diag_grade = None
                        continue
                # ★ 진단은 encarDiagnosis == 0 인 매물만 부른다 (STEP 21b).
                #   1·2 는 404 다.  전량 호출이 v1 에서 「원문 0건」을 만들었다
                if kind == "diagnosis" and diag_grade != DIAG_HAS_REPORT:
                    # ★ 「안 부른 것」은 미완성이 아니다.  진단이 없는 매물이다.
                    #   not_requested 에 넣으면 V1-02 가 결함으로 잡는다
                    skipped += 1
                    continue
                say("S5", f"매물 {sid} {kind}", (i - 1) * len(LISTING_ENDPOINTS),
                    len(lids) * len(LISTING_ENDPOINTS))
                st = time.time()
                res = fetch(req, fetcher, kind, clock, source_id=sid)
                _log_request(conn, ctx, kind, sid, req.url, res,
                             int((time.time() - st) * MS_PER_SEC))
                tally[res.status] = tally.get(res.status, 0) + 1
                if kind == "detail" and isinstance(res.raw, dict):
                    view = res.raw.get("view")
                    diag_grade = (view.get("encarDiagnosis")
                                  if isinstance(view, dict) else None)
                streak.observe(res)
                if streak.tripped:
                    halted = streak.reason()
                    break
                if save_raw(conn, res, schema[kind], adapter.site_code, lid,
                            req.url, req.headers, verify=verify_shape, reason=reject_reason,
                            run_id=ctx.run_id) == "rejected":
                    rejected += 1
                rows += 1
                conn.execute(
                    f"UPDATE core_listing SET {kind}_status=? WHERE listing_id=?",
                    (res.status, lid))
                conn.commit()
                _sleep(cfg, rng)
        # ★ 안 부르기로 한 것은 expected 에서 뺀다.
        #   빼지 않으면 「미완성 매물」로 잡힌다 (V1-01 · V1-02)
        expected = len(lids) * len(LISTING_ENDPOINTS) - skipped - done_before
        rep = step_report("S5", None, expected, tally,
                          rejected, time.time() - t0)
        if halted:
            rep.halted = True
            rep.halt_reason = halted
        return rep, rows

    # ── S6 상세 파싱 ─────────────────────────────────────────────────
    def s6(conn, ctx):
        """상세 A · 점검 · 이력 → CORE.  분류를 confirmed 로 올린다.

        진단은 건너뛴다 — core_diagnosis 가 없다 (3장 STEP 35).
        """
        t0 = time.time()
        at = clock.now().isoformat()
        n = 0
        for _lid, sid, kind, body in conn.execute(
            "SELECT r.listing_id, r.source_id, r.endpoint, r.body "
            "FROM raw_response r JOIN core_listing l "
            "ON l.site = r.site AND l.source_id = r.source_id "
            # ★ EXTRA_PARSERS 다섯을 함께 읽는다 (개정 296·297).
            #   전에는 넷만 읽어 record_summary · platform_check ·
            #   inspection_summary · ev_battery · sellingpoint 가
            #   8천 건씩 쌓여 있는데 아무도 안 펼쳤다 —
            #   platform_verified 가 전건 NULL 이었다 (실측 08-18)
            "WHERE r.endpoint IN ('detail','inspection','record',"
            f"'diagnosis',{','.join(repr(k) for k in EXTRA_PARSERS)}) "
            # ★★★ 08-26 — ★ 이 파서는 ★ 엔카 원문(JSON) 전용이다.
            #   ★ `raw_response` 에 ★ 다른 사이트도 들어온다 (명령서 3-2) —
            #   ★ ★ 좁히지 않으면 ★ KB 의 HTML 을 ★ `json.loads` 로 읽어 죽는다.
            #   ★ ★ 지금은 ★ 그 매물에 `target_key` 가 없어 ★ 우연히 안 걸릴 뿐이다
            f"AND r.status='ok' AND r.site=? AND l.target_key IN "
            f"({','.join('?' * len(scope))})", (adapter.site_code, *scope)
        ).fetchall():
            doc = json.loads(raw_body(body))
            if n % PROGRESS_EVERY == 0:
                say("S6", f"{kind} 파싱", n, 0)
                # ★ 잠금 창을 끊는다 (08-26).  ★ S6 은 13만 행이다
                raw_tick(conn, n)
            lid = resolve_listing_id(conn, adapter.site_code, sid, at)
            if kind == "detail":
                # ★ 필드 하나가 실패해도 나머지는 저장한다 (STEP 19a)
                parsed, issues = parse_with_issues(
                    parse_detail, doc, adapter.site_code, sid, kind)
                _save_issues(conn, lid, issues, ctx.parse_version, at)
                parsed["listing_id"] = lid
                parsed = split_pii(conn, parsed, adapter.site_code,
                                   pii_key, at)
                sdid = parsed.pop("_site_dealer_id", None)
                dealer_pii = parsed.pop("_pii_dealer", (None, None, None))
                if sdid:
                    parsed["dealer_id"] = resolve_dealer_id(
                        conn, adapter.site_code, sdid, at)
                    flush_dealer_pii(conn, parsed["dealer_id"], dealer_pii, at)
                cg = _group_of({"listing_id": lid}, groups, conn=conn)
                cls = classify_in_group(targets, groups, cg,
                                        _fuel_of(conn, lid),
                               _badge_of(conn, lid), parsed.get("trim_grade_name"),
                               parsed.get("displacement_cc"))
                vid, src, conf = resolve_vehicle_id(
                    conn,
                    build_identities(parsed.get("plate_hash"), None,
                                     parsed.get("vin"),
                                     f"{adapter.site_code}/{sid}"), at)
                parsed.update(
                    target_key=cls.target_key, classify_stage=cls.stage,
                    classify_source=cls.source,
                    classify_conflict=1 if cls.conflict else 0,
                    # ★ 2단에서 대상 외로 판명되면 status 도 따라가야 한다.
                    #   target_key 만 지우면 「차종 미정인데 active」가 남아
                    #   S5 가 계속 가져간다 (V2-31 · 실측 08-16)
                    status="active" if cls.target_key else "out_of_scope",
                    vehicle_id=vid, parsed_at=at,
                    parse_version=ctx.parse_version)
                upsert_core(conn, parsed, at)
                if not cls.target_key:
                    # ★ 판정은 대상에만 존재한다.  옛 판정을 남기면
                    #   등급 분포가 거짓이 된다 (개정 271 · V2-31)
                    conn.execute("DELETE FROM result_axis WHERE listing_id=?",
                                 (lid,))
                    conn.execute("DELETE FROM result_score WHERE listing_id=?",
                                 (lid,))
                upsert_vehicle(conn, vid, at)
                if parsed.get("dealer_id"):
                    upsert_dealer(conn, adapter.site_code, parsed["dealer_id"],
                                  parsed, ctx.run_id, at)
            elif kind == "inspection":
                ins, issues = parse_with_issues(
                    parse_inspection, doc, adapter.site_code, sid, kind)
                _save_issues(conn, lid, issues, ctx.parse_version, at)
                ins["listing_id"] = lid
                upsert_child(conn, "core_inspection", ins,
                             ctx.parse_version, at)
            elif kind == "record":
                rec, issues = parse_with_issues(
                    parse_record, doc, adapter.site_code, sid, kind)
                _save_issues(conn, lid, issues, ctx.parse_version, at)
                rec["listing_id"] = lid
                upsert_child(conn, "core_record",
                             split_pii(conn, rec, adapter.site_code,
                                       pii_key, at),
                             ctx.parse_version, at)
            elif kind in EXTRA_PARSERS:
                # ★ 개정 296·297 로 늘어난 원문 — core_listing 을 보강한다.
                #   원문에 있는 것만 넣는다.  추정하지 않는다
                got, issues = parse_with_issues(
                    EXTRA_PARSERS[kind], doc, adapter.site_code, sid, kind)
                _save_issues(conn, lid, issues, ctx.parse_version, at)
                fields = {k: v for k, v in got.items() if k != "row_status"}
                if fields:
                    sets = ", ".join(f"{k}=?" for k in fields)
                    conn.execute(
                        f"UPDATE core_listing SET {sets} WHERE listing_id=?",
                        [*fields.values(), lid])
            else:
                # ★ 표시용이다.  교환 판정은 outers 가 한다 (STEP 21b)
                dg, issues = parse_with_issues(
                    parse_diagnosis, doc, adapter.site_code, sid, kind)
                _save_issues(conn, lid, issues, ctx.parse_version, at)
                dg["listing_id"] = lid
                upsert_child(conn, "core_diagnosis", dg,
                             ctx.parse_version, at)
                # ★ 부위는 표로 편다.  소견은 core_diagnosis 컬럼이다
                conn.execute("DELETE FROM core_diagnosis_item "
                             "WHERE listing_id = ?", (lid,))
                for it in parse_diagnosis_items(doc):
                    conn.execute(
                        "INSERT INTO core_diagnosis_item"
                        "(listing_id,item_code,part_name,result_code,"
                        " result_text) VALUES (?,?,?,?,?)",
                        (lid, it["item_code"], it["part_name"],
                         it["result_code"], it["result_text"]))
            n += 1
        rep = step_report("S6", None, n, {"ok": n}, 0, time.time() - t0)
        return rep, n

    # ── S7 카탈로그 수집 ─────────────────────────────────────────────
    def s7(conn, ctx):
        """모델(jatoVehicleId) 단위 1회.  캐시에 없는 키만 (STEP 53)."""
        t0 = time.time()
        tally = {"ok": 0, "empty": 0, "not_found": 0, "error": 0}
        rejected = rows = 0
        streak = FailStreak(streak_limit)
        halted = None
        # ★ 호출은 매물 ID · 중복 제거는 모델 키다 (실측).
        #   응답이 모델-연식 카탈로그라 모델당 1회면 된다
        # ★ GROUP BY 는 WHERE 뒤에 와야 한다 — _scope 가 조건을 덧붙이므로
        #   여기서는 직접 조립한다
        # ★ 대표를 여럿 들고 온다.  하나가 404 여도 조합이 없는 것이 아니다 —
        #   실측 08-18: 같은 조합 23매물 중 셋은 404, 셋은 200 [] 이었다.
        #   대표 하나로 포기하면 「없다」와 「못 물어봤다」가 섞인다 (개정 327)
        sql, args = _scope(
            "SELECT model_catalog_key, source_id FROM core_listing "
            "WHERE model_catalog_key IS NOT NULL AND status='active' "
            "AND model_catalog_key NOT IN (SELECT source_id "
            "FROM raw_response WHERE endpoint='catalog')")
        reps: dict = {}
        for k, sid in conn.execute(sql + " ORDER BY source_id", args):
            if k:
                reps.setdefault(k, []).append(sid)
        keys = sorted(reps)
        for k in keys:
            say("S7", f"카탈로그 {k}", rows, len(keys))
            res = req = None
            for rep_sid in reps[k][:int(cfg.get("catalog_reps") or 1)]:
                req = adapter.catalog_url(rep_sid)
                st = time.time()
                # 저장 키는 모델이다 — 다음 실행의 중복 제거가 이 값으로 돈다
                res = fetch(req, fetcher, "catalog", clock, source_id=k)
                _log_request(conn, ctx, "catalog", k, req.url, res,
                             int((time.time() - st) * MS_PER_SEC))
                if res.status != "not_found":
                    break
                # ★ 이 매물만 사라진 것일 수 있다 — 다음 대표로 다시 묻는다
                _sleep(cfg, rng)
            tally[res.status] = tally.get(res.status, 0) + 1
            streak.observe(res)
            if streak.tripped:
                halted = streak.reason()
                break
            if save_raw(conn, res, schema["catalog"], adapter.site_code, None,
                        req.url, req.headers, verify=verify_shape, reason=reject_reason,
                            run_id=ctx.run_id) == "rejected":
                rejected += 1
            rows += 1
            _sleep(cfg, rng)
        rep = step_report("S7", None, len(keys), tally, rejected,
                          time.time() - t0)
        if halted:
            rep.halted = True
            rep.halt_reason = halted
        return rep, rows

    # ── S8 카탈로그 사전 ─────────────────────────────────────────────
    def s8(conn, ctx):
        from tools.build_dict import build_catalog_dict

        t0 = time.time()
        n = build_catalog_dict(conn, adapter.site_code, ctx.dict_version,
                               clock.now().isoformat())
        return step_report("S8", None, n, {"ok": n}, 0, time.time() - t0), n

    # ── S8.5 계수 산출 ───────────────────────────────────────────────
    def s85(conn, ctx):
        """★ 판정·채점 결과를 쓰지 않는다 (STEP 64 · V5-08).

        계수 = 실매물 가격 중앙값 ÷ 기대가 중앙값.  둘 다 S6 까지면 있다.
        임계(coefficient_min_sample 등)가 미확정인 동안은 산출하지 않는다 —
        추정으로 계수를 만들면 가격 200점 전체가 그 위에 얹힌다 (v1 사고).
        """
        t0 = time.time()
        dep = cfg.get("_depreciation") or {}
        if not dep.get("curve") or dep.get("coefficient_min_sample") is None:
            rep = step_report("S8.5", None, 0, {}, 0, time.time() - t0)
            rep.halt_reason = "감가 곡선·표본 기준 미확정 — 계수 산출 생략 (STEP 26-5)"
            return rep, 0
        return step_report("S8.5", None, 0, {}, 0, time.time() - t0), 0

    return {"S0": s0, "S1": s1, "S2": s2, "S3": s3,
            "S4": s4, "S5": s5, "S6": s6, "S7": s7, "S8": s8, "S8.5": s85}


def classify_in_group(targets: dict, groups, cg: str, *args):
    """★ 그 묶음의 차종만 후보로 두고 분류한다.

    ★★ 왜 — ★ `collect_group` 이 ★ 18종 ★ 전부 「multi」가 됐다 (개정 632).
      ★ 그러면 ★ `classify` 가 ★ 열여덟을 ★ 한 후보군으로 본다 —
      ★ G80_25T 와 G70_25T 는 ★ 연료·배기량이 같아 ★ 「후보 둘」로 ★ 아무것도 안 붙는다
      ★ 그리고 ★ 묶음 이름이 ★ 「multi:G80」이라 ★ 「multi」와 안 맞아 ★ 후보가 0 이 된다
      ★ ★ 실측 08-24 — ★ 그래서 ★ 전건 `out_of_scope` 가 되어 ★ 씨앗이 죽었다
    ★ `CollectGroup` 은 ★ 제 차종을 안다 (`target_keys`) — ★ 그것으로 좁힌다.
      ★ 한 묶음은 ★ 쿼리가 같은 것들이라 ★ 좁혀도 잃는 것이 없다
    """
    got = next((g for g in groups if g.group_key == cg), None)
    if got is None:
        return classify(targets, cg, *args)
    cands = {k: v for k, v in targets.items() if k in got.target_keys}
    if not cands:
        return classify(targets, cg, *args)
    said = next(iter(cands.values())).get("collect_group") or cg
    return classify(cands, said, *args)


# ★★★ 08-29 (개정 838) — ★ 쪽넘김을 지운 ★ 「질의」.
#   ★ 엔카 목록 주소는 ★ `sr=%7CMobileModifiedDate%7C{offset}%7C{rows}` 로 쪽을 나눈다.
#     ★ 그 자리만 지우면 ★ 같은 질의의 쪽들이 ★ 한 묶음이 된다.
#   ★★ 숫자를 통째로 지우지 않는다 — ★ 그러면 ★ 연식 범위·차종 코드까지 뭉개져
#     ★ ★ **다른 차종의 질의가 한 묶음이 된다**.  ★ 그것이 산 차를 죽인다.
#   ★ ★ 쪽넘김 칸(`sr`)만 지운다.  ★ 정렬 기준은 결과 집합을 안 바꾼다
#   ★ 못 묶으면 ★ 그 질의는 ★ 「안 끝났다」가 되어 ★ **안 매긴다** —
#     ★ 틀리는 쪽이 아니라 ★ 안 하는 쪽으로 기운다
def _query_key(url) -> str:
    import re as _re

    if not url:
        return ""
    return _re.sub(r"(?i)([?&]sr=)[^&]*", r"\1*", str(url))


def _group_of(parsed, groups, conn=None) -> str:
    """매물이 어느 collect_group 에서 왔는가."""
    if conn is not None:
        row = conn.execute(
            "SELECT site_model_group FROM core_listing WHERE listing_id=?",
            (parsed["listing_id"],)).fetchone()
        mg = row[0] if row else None
    else:
        mg = parsed.get("site_model_group")
    for g in groups:
        if g.site_query.get("ModelGroup") == mg:
            return g.group_key
    return groups[0].group_key if groups else ""


def _fuel_of(conn, lid):
    r = conn.execute(
        "SELECT fuel_raw FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    return r[0] if r else None


def _badge_of(conn, lid):
    r = conn.execute(
        "SELECT trim_badge FROM core_listing WHERE listing_id=?", (lid,)).fetchone()
    return r[0] if r else None


def _pages_for(total: int, page_size: int) -> int:
    return (total + page_size - 1) // page_size if total else 1


# ── S9 판정 · S10 채점 (STEP 47) ─────────────────────────────────────
from analyze.absolute import absolute_check  # noqa: E402
from analyze.axes import COMPONENTS, AxisContext, DictionarySet, ScoringPolicy  # noqa: E402
from analyze.engine import analyze_listing  # noqa: E402
from score.grade import grade_of  # noqa: E402
from score.scorer import score as score_listing  # noqa: E402
from dataclasses import replace  # noqa: E402
from store.core import load_snapshot  # noqa: E402


def _dicts(conn, root: str) -> DictionarySet:
    """Analyzer 는 순수 함수다.  DB 를 여기서 미리 읽어 넘긴다 (0장 STEP 2)."""
    desc = {
        code: (d or "")
        for code, d in conn.execute(
            "SELECT option_code, description FROM dict_model_option")
    }
    names = {
        code: n for code, n in conn.execute(
            "SELECT option_code, option_name FROM dict_model_option")
    }
    with open(os.path.join(root, "config", "dictionaries",
                           "tint_keywords.json"), encoding="utf-8") as f:
        tk = tuple(json.load(f)["keywords"])
    with open(os.path.join(root, "config", "dictionaries",
                           "color_grade.json"), encoding="utf-8") as f:
        cg = json.load(f)
    grade = {c: "preferred" for c in cg["preferred"]}
    grade.update({c: "neutral" for c in cg["neutral"]})
    # 선택 옵션가 (원).  ★ 사전은 만원 단위다 (개정 292 ③)
    # ★ 같은 코드가 카탈로그마다 있다 (10001 은 52행).  중앙값을 쓴다 —
    #   합치면 옵션 합이 4.7억이 됐다 (실측 08-17)
    by_code: dict = {}
    for code, mw in conn.execute(
        "SELECT option_code, price_manwon FROM dict_model_option"
        " WHERE price_manwon IS NOT NULL"
    ):
        by_code.setdefault(code, []).append(int(mw))
    prices = {code: sorted(v)[len(v) // 2] * WON_PER_MANWON
              for code, v in by_code.items()}
    return DictionarySet(option_names=names, option_descriptions=desc,
                         option_prices=prices,
                         tint_keywords=tk, color_grade=grade,
                         color_default=cg["default"])


def _option_medians(conn, prices: dict) -> tuple:
    """트림별 옵션가 중앙값 · 차종별 신차가 중앙값 (개정 421).

    마스터 — 「옵션의 총합 가격도 트림별 가격 차이도 가격 점수에 넣자」

    ★ 있는 데이터로 낸다.  새로 받을 것은 없다
    ★ 트림은 Badge + BadgeDetail 이다 (개정 313).  Badge 만으로 묶으면
      「깡통」과 「풀옵션 최고트림」이 한 무리가 된다 — 보정의 뜻이 없어진다
    ★ 매물 단위로 풀어 둔다 — 스냅샷에는 트림 칸이 없다.
      축 함수가 트림을 다시 뒤지게 하지 않는다 (F-1)
    돌려줌   {listing_id: (트림 옵션가 중앙값, 표본수, 차종 신차가 중앙값)}
    """
    import json as _j

    def _mid(rows: list) -> int:
        rows = sorted(rows)
        m = len(rows) // 2
        return int(rows[m] if len(rows) % 2
                   else (rows[m - 1] + rows[m]) / 2)

    by_trim: dict = {}
    by_model: dict = {}
    where: dict = {}
    for lid, tk, badge, detail, opt_json, origin in conn.execute(
        "SELECT listing_id, target_key, trim_badge, trim_badge_detail,"
        " options_choice_json, price_origin_won FROM core_listing"
        " WHERE status='active' AND target_key IS NOT NULL"
    ):
        try:
            codes = _j.loads(opt_json) if opt_json else []
        except (ValueError, TypeError):
            codes = []
        if not isinstance(codes, list):
            codes = []
        won = sum(prices.get(c, 0) for c in codes)
        key = (tk, badge or "", detail or "")
        by_trim.setdefault(key, []).append(won)
        where[lid] = (key, tk)
        if origin:
            by_model.setdefault(tk, []).append(int(origin))
    trim_mid = {k: (_mid(v), len(v)) for k, v in by_trim.items()}
    model_mid = {k: _mid(v) for k, v in by_model.items()}
    return {lid: (*trim_mid[key], model_mid.get(tk))
            for lid, (key, tk) in where.items()}


def _market_medians(conn, need: int) -> dict:
    """매물별 「같은 차종·트림·연식」 실매물 중앙값 (개정 292 ①).

    ★ 이론가가 아니다.  실제로 팔리고 있는 값이다.
      표본이 need 미만이면 넣지 않는다 — 그 매물은 시세 축이 excluded 다
    금지   렌트·리스 승계를 표본에 넣는 것.  같은 차의 값이 아니다
    """
    groups: dict = {}
    for lid, tk, trim, ym, price in conn.execute(
        "SELECT listing_id, target_key, trim_badge, substr(year_month,1,4),"
        " price_current_won FROM core_listing"
        " WHERE status='active' AND price_current_won IS NOT NULL"
        " AND target_key IS NOT NULL"
        " AND (advertisement_type IS NULL OR advertisement_type='NORMAL')"
    ):
        groups.setdefault((tk, trim, ym), []).append((lid, price))
    out: dict = {}
    for rows in groups.values():
        if len(rows) < need:
            continue
        prices = sorted(p for _lid, p in rows)
        mid = len(prices) // 2
        median = (prices[mid] if len(prices) % 2
                  else (prices[mid - 1] + prices[mid]) / 2)
        for lid, _p in rows:
            out[lid] = (median, len(prices))
    return out


def _trim_ladders(conn) -> dict:
    """차종별 트림 신차가 사다리 (개정 292 ③).

    ★ 백분위를 매기려면 그 차종의 트림을 다 알아야 한다.
      매물이 아니라 트림 단위로 센다 — 인기 트림이 여러 번 세지면 안 된다
    """
    # ★ trim_badge 는 차종 안에서 1~7종뿐이다 — target_key 가 이미 트림을 담는다.
    #   서로 다른 「등급 기준 신차가」가 실제 트림이다 (실측 08-17: 차종당 3~21종)
    ladder: dict = {}
    for tk, origin in conn.execute(
        "SELECT DISTINCT target_key, price_origin_won FROM core_listing"
        " WHERE target_key IS NOT NULL AND price_origin_won IS NOT NULL"
    ):
        ladder.setdefault(tk, []).append(int(origin))
    return ladder


def _option_base(conn, prices: dict, pct: float, need: int) -> dict:
    """차종별 옵션가 합의 P90 (F-scoring ④-2).

    ★ 최대값을 쓰면 한 매물이 기준을 좌우한다.  P90 이 그 흔들림을 막는다
    """
    import json as _json

    sums: dict = {}
    for tk, raw in conn.execute(
        "SELECT target_key, options_choice_json FROM core_listing"
        " WHERE target_key IS NOT NULL AND options_choice_json IS NOT NULL"
    ):
        try:
            codes = _json.loads(raw)
        except (ValueError, TypeError):
            continue
        if not isinstance(codes, list) or not codes:
            continue
        got = sum(prices.get(c, 0) for c in codes)
        if got:
            sums.setdefault(tk, []).append(got)
    out = {}
    for tk, vals in sums.items():
        if len(vals) < need:
            continue
        vals.sort()
        out[tk] = vals[min(len(vals) - 1, int(len(vals) * pct))]
    return out


def _site_grade_rules(root: str) -> dict:
    """사이트별 보증 규칙 (개정 365 · V3-55).

    ★ config/sites.json 이 정본이다.  코드에 사이트 이름을 박지 않는다
    ★★ 개정 428 로 「항목 여럿의 합」에서 **단계**로 돌아갔다 —
      엔카진단++ 52 · 엔카진단+ 40 · 엔카진단 26 · 없음 0.
      ★ warranty_grades 를 안 넘기면 축이 옛 합산(10+10+30)을 그대로 쓴다
      (실측 08-21 — V3-87 이 「단계 밖의 값 10·20」을 잡았다)
    """
    with open(os.path.join(root, "config", "sites.json"), encoding="utf-8") as f:
        return {k: {"warranty_items": v.get("warranty_items") or [],
                    "warranty_evidence": v.get("warranty_evidence"),
                    "warranty_grades": v.get("warranty_grades") or []}
                for k, v in json.load(f).items() if isinstance(v, dict)}


def _listing_config(conn, lid: str, targets: dict, dep: dict, as_of: str,
                    ladder: dict, site_rule: dict, opt_base: dict) -> dict:
    """차종 설정만 담는다.

    ★ 매물별 값은 여기 넣지 않는다 (F-1 · V4-24).
      dict 에 숨기면 어떤 값이 판정에 쓰이는지 시그니처로 알 수 없다 —
      매물 값은 _listing_values 가 ListingSnapshot 으로 올린다
    """
    row = conn.execute(
        "SELECT target_key FROM core_listing WHERE listing_id = ?",
        (lid,)).fetchone()
    tk = (targets.get(row[0]) or {}) if row else {}
    return {
        "as_of": as_of,
        "depreciation": dep,
        "SPEC_DEFAULT_ON": tk.get("SPEC_DEFAULT_ON"),
        "SPEC_DEFAULT_OFF": tk.get("SPEC_DEFAULT_OFF"),
        # ★ 개정 292 — 트림 사다리는 차종 단위다.  전 매물을 한 번만 훑는다
        "trim_ladder": ladder, "option_base": opt_base,
        # ★ 개정 365 — 사이트마다 「무엇이 몇 점인가」가 다르다.
        #   코드에 사이트 이름을 박지 않는다 (V3-55)
        "site_warranty": site_rule,
    }


def _listing_values(conn, lid: str) -> dict:
    """매물별 판정 값 7종 → ListingSnapshot 필드 (F-1 · 개정 302)."""
    row = conn.execute(
        "SELECT l.diagnosis_car, l.warranty_extend, l.warranty_deemed,"
        " l.advertisement_type, l.lease_rent_info_json,"
        " i.usage_change_types_json, r.use1_json"
        " FROM core_listing l LEFT JOIN core_inspection i"
        " ON i.listing_id = l.listing_id"
        " LEFT JOIN core_record r ON r.listing_id = l.listing_id"
        " WHERE l.listing_id = ?", (lid,)
    ).fetchone()
    if row is None:
        return {}
    return {"diagnosis_car": row[0], "warranty_extend": row[1],
            "warranty_deemed": row[2], "advertisement_type": row[3],
            "lease_rent_info": row[4], "usage_change_types_json": row[5],
            "record_use_json": row[6]}


def _option_money(snap, prices: dict) -> dict:
    """선택 옵션가 합과 신차가 합 (개정 301 · F-scoring ①-2 · ④-2).

    ★ 신차가 = 등급기준 + 선택옵션가 합.  그래서 옵션 많은 차가 자동 반영된다
    ★ 카탈로그에 값이 없으면 None 이다 — 「0원」이 아니다 (개정 325)
    """
    codes = snap.options_choice
    if codes is None:
        return {"option_total_won": None, "origin_total_won": snap.price_origin_won}
    if not codes:
        total = 0
    else:
        got = [prices.get(c) for c in codes]
        total = sum(x for x in got if x) if any(x for x in got) else None
    origin = snap.price_origin_won
    return {"option_total_won": total,
            "origin_total_won": (origin + (total or 0)) if origin else None}


def _owned_months(snap, as_of: str) -> int | None:
    """보유 개월 — 최초등록부터 지금까지 (개정 322).

    ★ 자차 미가입 「기간」이 아니라 「보유 기간의 몇 %」가 흠이다.
      3년 중 1달과 3년 중 3년은 다른 사실이다
    """
    from analyze.axis._util import months_between

    return months_between(
        snap.first_registration_date or snap.year_month, as_of)


def _option_of(opts: dict, lid: str) -> dict:
    """옵션 보정에 쓸 값 (개정 421).  ★ 트림은 Badge + BadgeDetail 이다."""
    got = opts.get(lid)
    return {"option_median_by_trim_won": got[0] if got else None,
            "option_trim_sample_n": got[1] if got else None,
            "origin_median_by_model_won": got[2] if got else None}


def _market_of(market: dict, lid: str) -> dict:
    """매물별 시세 중앙값 → ListingSnapshot (F-1 · V4-24).

    ★ target_config 에 담으면 어떤 값이 판정에 쓰이는지 시그니처로 알 수 없다
    """
    got = market.get(lid)
    return {"market_median_won": int(got[0]) if got else None,
            "market_sample_n": got[1] if got else None}


def _group_sums(policy, verdict) -> tuple:
    """갈래 합 다섯 (개정 428 · v189 권고).

    ★ 이미 더하고 있는 값이다.  저장만 한다 —
      점수 필터가 JOIN 없이 걸리고 목록 막대 넷을 한 번에 읽는다
    ★ 갈래 ↔ 성분 접두어는 config/scoring.json groups 가 정본이다.
      코드에 두 벌로 적지 않는다 (S14)
    """
    # ★★ 08-24 실측 — ★ `제조사 보증`·`사이트 검증` 이 ★ `groups` 에 ★ 없다.
    #   ★ f-table 의 갈래는 ★ 넷이다 (차량·값·보증·취향).  ★ 그 둘은 ★ 갈래가 아니라
    #   ★ 화면이 「보증」을 나눠 내는 이름이다 — ★ `group_parts` 가 정본이다.
    #   ★ 그래서 ★ 4,043건 ★ 전건이 ★ group_warranty·group_site = 0 이었다
    #   ★ 목록 카드의 보증 막대가 ★ 50/50 0 으로 보이던 까닭이다 (UI_REVIEW 1장)
    groups = dict(policy.raw.get("groups") or {},
                  **(policy.raw.get("group_parts") or {}))
    order = ("값", "차량", "제조사 보증", "사이트 검증", "취향")
    out = []
    for name in order:
        pres = groups.get(name) or []
        out.append(float(sum(
            verdict.values.get(k) or 0
            for k in verdict.values
            if k not in verdict.excluded
            and any(k == p or k.startswith(p) for p in pres))))
    return tuple(out)



def _origin_lend_table(conn) -> dict:
    """★★★★ ③ 「차종·트림의 속성은 ★ 다른 사이트 표에서 끌어온다」 (`f-table` 5장).

    ★★★ 마스터 지시 08-30 — 「★ 밑감은 **현대 인증**이다 (상세 표본 8건 전건에
      ★ 값이 있고 ★ 서로 다르다).  ★ 열쇠 넷(**제조사·모델·트림·연식**)이
      ★ ★ **다 같을 때만** 쓴다.  ★ 하나라도 다르면 ★ **0점＋미확인**」
    ★ 규격 — `f-table.md:210` 「③ 의 매칭 키 — 제조사 · 모델 · 트림 · 연식.
      ★ 매칭 안 되면 0점 + 「미확인」」
    ★★ 지어내지 않는다 — ★ 넷 중 하나라도 비면 ★ 그 줄을 표에 안 넣는다.
    ★ 같은 열쇠에 값이 여럿이면 ★ **가장 낮은 것**을 쓴다 —
      ★ 높은 쪽을 쓰면 ★ 감가율이 부풀어 ★ 점수를 지어 주는 꼴이 된다
      (`DEDUP_CROSS_SITE` 는 「둘 다면 높은 쪽」이라 적었으나 ★ 그것은
       ★ **같은 차**를 합칠 때다.  ★ 여기는 ★ 다른 차의 속성을 빌리는 것이라
       ★ ★ 보수적으로 낮은 쪽을 쓴다 — ★ 만점을 지어 주지 않는다 · `f-table` 금지)
    돌려줌  {(제조사, 모델, 트림, 연식): 신차가}
    """
    out: dict = {}
    for mfr, model, trim, ym, won in conn.execute(
        "SELECT site_manufacturer, site_model, trim_badge,"
        "       substr(year_month, 1, 4), MIN(price_origin_won)"
        "  FROM core_listing"
        " WHERE price_origin_won IS NOT NULL"
        "   AND site_manufacturer IS NOT NULL AND site_model IS NOT NULL"
        "   AND trim_badge IS NOT NULL AND year_month IS NOT NULL"
        " GROUP BY 1, 2, 3, 4"
    ):
        out[(mfr, model, trim, ym)] = won
    return out


def _origin_keys(conn, lids: list) -> dict:
    """★ 매물마다 ★ 열쇠 넷을 한 번에 받는다 (제조사·모델·트림·연식).

    ★ 스냅샷에는 이 셋이 없다 — ★ 스냅샷을 늘리지 않고 ★ 여기서 읽는다.
      ★ ★ 한 매물씩 물으면 ★ 수천 쿼리가 된다 (V11-34) — ★ 한 번에 받는다
    """
    if not lids:
        return {}
    out: dict = {}
    marks = ",".join("?" * len(lids))
    for lid, mfr, model, trim, ym, own in conn.execute(
        f"SELECT listing_id, site_manufacturer, site_model, trim_badge,"
        f"       substr(year_month, 1, 4), price_origin_won"
        f"  FROM core_listing WHERE listing_id IN ({marks})", tuple(lids)
    ):
        out[lid] = (mfr, model, trim, ym, own)
    return out


def _origin_lent(lid, keys: dict, table: dict):
    """★ 이 매물에 ★ 끌어올 신차가가 있나.  ★ 넷이 다 있고 다 같을 때만.

    ★ 이미 제 신차가가 있으면 ★ 안 빌린다 — ★ 원문이 언제나 먼저다
    돌려줌  (신차가, 어디서 왔나) · 또는 (None, None)
    """
    got = keys.get(lid)
    if not table or not got:
        return None, None
    mfr, model, trim, ym, own = got
    if own:
        return None, None
    key = (mfr, model, trim, ym)
    if not all(key):
        # ★ 넷 중 하나라도 비면 ★ 안 빌린다 — ★ 0점＋미확인이 맞다 (f-table:210)
        return None, None
    won = table.get(key)
    return (won, "origin_price_lent") if won else (None, None)


def make_score_executors(root: str, clock, targets: dict, policy_raw: dict,
                         depreciation: dict) -> dict:
    policy = ScoringPolicy(policy_raw)
    # ★ --target 범위는 판정·채점에도 걸린다 (S5 와 같은 이유)
    scope = tuple(sorted(targets))

    def _scope(sql: str) -> tuple[str, tuple]:
        return (f"{sql} AND target_key IN ({','.join('?' * len(scope))})",
                scope)

    def s9(conn, ctx):
        """판정.  result_axis 는 Component 단위 17행이다 (STEP 68)."""
        t0 = time.time()
        at = clock.now().isoformat()
        dicts = _dicts(conn, root)
        # ★ 시세·트림 사다리는 전 매물을 한 번만 훑는다 (개정 292)
        market = _market_medians(conn, policy.rule("value")["market_min_sample"])
        ladder = _trim_ladders(conn)
        # ★ 트림별 옵션가 중앙값 · 차종별 신차가 중앙값 (개정 421).
        #   한 번만 낸다 — 매물마다 세면 3,843번 훑는다 (V11-34 와 같은 이유)
        opt_meds = _option_medians(conn, dicts.option_prices)
        opt_base = _option_base(conn, dicts.option_prices,
                                float(policy.rule("taste")["option_percentile"]),
                                int(policy.rule("taste")["option_min_sample"]))
        site_rules = _site_grade_rules(root)
        # ★ 차종이 안 붙은 매물의 옛 판정을 치운다 (개정 271 · V2-31).
        #   S6 은 target_key 로 범위를 잡아 NULL 행을 아예 못 본다 —
        #   그대로 두면 등급 분포에 대상 아닌 것이 섞인다
        conn.execute(
            "DELETE FROM result_axis WHERE listing_id IN "
            "(SELECT listing_id FROM core_listing WHERE target_key IS NULL)")
        conn.execute(
            "DELETE FROM result_score WHERE listing_id IN "
            "(SELECT listing_id FROM core_listing WHERE target_key IS NULL)")
        conn.execute(
            "UPDATE core_listing SET status='out_of_scope' "
            "WHERE target_key IS NULL AND status='active'")
        conn.commit()
        lids = [r[0] for r in conn.execute(
            *_scope("SELECT listing_id FROM core_listing "
                    "WHERE status='active'"))]
        # ★ 배점이 바뀌면 옛 성분 행이 남는다 (개정 292 실측 — 17 → 14 성분).
        #   그대로 두면 화면과 검사가 없어진 축을 계속 읽는다
        gone = [r[0] for r in conn.execute(
            "SELECT DISTINCT axis FROM result_axis") if r[0] not in COMPONENTS]
        if gone:
            conn.execute("DELETE FROM result_axis WHERE axis IN "
                         f"({','.join('?' * len(gone))})", tuple(gone))
            conn.commit()
        # ★ ③ 끌어오기 밑감 — ★ 한 번만 만든다 (마스터 지시 3 · 08-30)
        _otable = _origin_lend_table(conn)
        _okeys = _origin_keys(conn, lids)
        rows = 0
        for _i9, lid in enumerate(lids):
            # ★★ 08-28 — ★ 잠금 창을 끊는다.  ★ 전에는 S4·S6 에만 넣어
            #   ★ ★ S9 이 도는 동안 ★ `POST /login` 이 ★ 500 이었다
            #   ★ ★ (Caddy 접근 로그 실측 — 500 두 건이 다 /login 이다)
            raw_tick(conn, _i9)
            # ★ 매물 값을 스냅샷으로 올린다.  축 함수가 dict 를 뒤지지 않게 (F-1)
            snap = replace(load_snapshot(conn, lid), **_listing_values(conn, lid),
                           **_market_of(market, lid))
            # ★★★★★ 08-30 (마스터 지시 3 · `f-table` 5장 갈래 ③) —
            #   ★ 신차가가 없으면 ★ **다른 사이트 표에서 끌어온다.**
            #   ★ 열쇠 넷(제조사·모델·트림·연식)이 ★ **다 같을 때만** 쓴다 —
            #   ★ ★ 하나라도 다르면 ★ 안 빌린다 (0점＋미확인이 그대로 간다)
            _lent, _lent_src = _origin_lent(lid, _okeys, _otable)
            if _lent:
                snap = replace(snap, price_origin_won=_lent,
                               origin_lent_from=_lent_src)
            snap = replace(snap, owned_months=_owned_months(snap, at),
                           **_option_money(snap, dicts.option_prices))
            # ★ 옵션·트림 보정 (개정 421).  깡통과 풀옵션을 같은 값으로 안 본다
            snap = replace(snap, **_option_of(opt_meds, lid))
            tc = _listing_config(conn, lid, targets, depreciation, at, ladder,
                                 site_rules.get(snap.site, {}), opt_base)
            actx = AxisContext(snap, dicts, policy,
                               TargetSpec(snap.target_key or "", "", {}), tc)
            v = analyze_listing(actx)
            for comp in COMPONENTS:
                if comp not in v.values:
                    continue
                conn.execute(
                    "INSERT OR REPLACE INTO result_axis"
                    "(listing_id,calc_version,dict_version,axis,value,source,"
                    " prio,excluded,max_points) VALUES (?,?,?,?,?,?,?,?,?)",
                    (lid, ctx.calc_version, ctx.dict_version, comp,
                     v.values[comp], v.sources[comp], v.prios[comp],
                     1 if comp in v.excluded else 0, policy.comp(comp)))
                rows += 1
            # ★ 충돌을 버리지 않는다 (A-5 · V3-35).
            #   같은 우선순위에서 다른 값이 나온 것은 규칙이 겹쳤다는 뜻이다.
            #   첫 값 유지는 임시 조치이고, 겹친 규칙을 고쳐야 한다
            conn.execute("DELETE FROM result_axis_conflict "
                         "WHERE listing_id=? AND calc_version=?",
                         (lid, ctx.calc_version))
            for axis, prio, value in v.conflicts:
                conn.execute(
                    "INSERT INTO result_axis_conflict"
                    "(listing_id,calc_version,axis,prio,value,source)"
                    " VALUES (?,?,?,?,?,?)",
                    (lid, ctx.calc_version, axis, prio, str(value),
                     v.sources.get(axis)))
            conn.commit()
        rep = step_report("S9", None, len(lids) * len(COMPONENTS),
                          {"ok": rows}, 0, time.time() - t0)
        return rep, rows

    def s10(conn, ctx):
        """채점 · 등급.  NULL 이 아니라 excluded 가 분모를 결정한다 (STEP 83)."""
        t0 = time.time()
        at = clock.now().isoformat()
        dicts = _dicts(conn, root)
        # ★ 시세·트림 사다리는 전 매물을 한 번만 훑는다 (개정 292)
        market = _market_medians(conn, policy.rule("value")["market_min_sample"])
        ladder = _trim_ladders(conn)
        # ★ 트림별 옵션가 중앙값 · 차종별 신차가 중앙값 (개정 421).
        #   한 번만 낸다 — 매물마다 세면 3,843번 훑는다 (V11-34 와 같은 이유)
        opt_meds = _option_medians(conn, dicts.option_prices)
        opt_base = _option_base(conn, dicts.option_prices,
                                float(policy.rule("taste")["option_percentile"]),
                                int(policy.rule("taste")["option_min_sample"]))
        site_rules = _site_grade_rules(root)
        # ★ 차종이 안 붙은 매물의 옛 판정을 치운다 (개정 271 · V2-31).
        #   S6 은 target_key 로 범위를 잡아 NULL 행을 아예 못 본다 —
        #   그대로 두면 등급 분포에 대상 아닌 것이 섞인다
        conn.execute(
            "DELETE FROM result_axis WHERE listing_id IN "
            "(SELECT listing_id FROM core_listing WHERE target_key IS NULL)")
        conn.execute(
            "DELETE FROM result_score WHERE listing_id IN "
            "(SELECT listing_id FROM core_listing WHERE target_key IS NULL)")
        conn.execute(
            "UPDATE core_listing SET status='out_of_scope' "
            "WHERE target_key IS NULL AND status='active'")
        conn.commit()
        lids = [r[0] for r in conn.execute(
            *_scope("SELECT listing_id FROM core_listing "
                    "WHERE status='active'"))]
        # ★ ③ 끌어오기 밑감 — ★ 한 번만 만든다 (마스터 지시 3 · 08-30)
        _otable = _origin_lend_table(conn)
        _okeys = _origin_keys(conn, lids)
        for _i10, lid in enumerate(lids):
            # ★ 잠금 창을 끊는다 (08-28) — ★ S9 과 같은 까닭이다
            raw_tick(conn, _i10)
            # ★ 매물 값을 스냅샷으로 올린다.  축 함수가 dict 를 뒤지지 않게 (F-1)
            snap = replace(load_snapshot(conn, lid), **_listing_values(conn, lid),
                           **_market_of(market, lid))
            # ★★★★★ 08-30 (마스터 지시 3 · `f-table` 5장 갈래 ③) —
            #   ★ 신차가가 없으면 ★ **다른 사이트 표에서 끌어온다.**
            #   ★ 열쇠 넷(제조사·모델·트림·연식)이 ★ **다 같을 때만** 쓴다 —
            #   ★ ★ 하나라도 다르면 ★ 안 빌린다 (0점＋미확인이 그대로 간다)
            _lent, _lent_src = _origin_lent(lid, _okeys, _otable)
            if _lent:
                snap = replace(snap, price_origin_won=_lent,
                               origin_lent_from=_lent_src)
            snap = replace(snap, owned_months=_owned_months(snap, at),
                           **_option_money(snap, dicts.option_prices))
            # ★ 옵션·트림 보정 (개정 421).  깡통과 풀옵션을 같은 값으로 안 본다
            snap = replace(snap, **_option_of(opt_meds, lid))
            tc = _listing_config(conn, lid, targets, depreciation, at, ladder,
                                 site_rules.get(snap.site, {}), opt_base)
            actx = AxisContext(snap, dicts, policy,
                               TargetSpec(snap.target_key or "", "", {}), tc)
            v = analyze_listing(actx)
            fails, unknown = absolute_check(actx)
            for reason in unknown:
                # ★ 모르는 것을 조용히 안전으로 두지 않는다 (영향분석 4)
                conn.execute(
                    "INSERT OR REPLACE INTO listing_warning"
                    "(listing_id,warning_code,severity,evidence,detected_at)"
                    " VALUES (?,?,?,?,?)",
                    (lid, "seizing_unknown", "info", reason, at))
            # ★ 마이너스는 스냅샷을 봐야 정해진다 (개정 322)
            res = score_listing(v, policy, fails, snapshot=snap)
            conn.execute(
                # ★ earned 를 함께 남긴다.  등급은 earned/denominator 다 (E-1)
                #   not_rated_reason 이 없으면 「왜 판정 못 했나」를 못 낸다
                "INSERT OR REPLACE INTO result_score"
                "(listing_id,calc_version,dict_version,score_total,earned,"
                " denominator,grade,absolute_fail,not_rated_reason,"
                " grade_earned,grade_base,confirmed_points,"
                " group_value,group_car,group_warranty,group_site,"
                " group_taste,penalties_json,"
                " bonuses_json, calculated_at)"
                " VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (lid, ctx.calc_version, ctx.dict_version, res.score_total,
                 res.earned, res.denominator, grade_of(res, policy),
                 res.absolute_fail, res.not_rated_reason,
                 res.grade_earned, res.grade_base, res.confirmed,
                 *_group_sums(policy, v),
                 json.dumps([list(p) for p in res.penalties],
                            ensure_ascii=False),
                 # ★ 가점도 남긴다.  화면이 「배터리 SOH 94.6% (+24)」를 낸다
                 json.dumps([list(b) for b in res.bonuses],
                            ensure_ascii=False), at))
        conn.commit()
        # ★ 매 실행 후 조건을 돌린다 (STEP 117a).
        #   매물은 사라지지만 조건은 남는다 — 새로 맞는 매물을 쌓는다
        from store.watch import run_watch_queries

        hits = run_watch_queries(conn, ctx.calc_version, at)
        rep = step_report("S10", None, len(lids), {"ok": len(lids)}, 0,
                          time.time() - t0)
        if hits:
            rep.halt_reason = (rep.halt_reason or "") + \
                f" · 조건 알림 신규 {sum(hits.values())}건"
        return rep, len(lids)

    return {"S9": s9, "S10": s10}


# ── S11 검증 (STEP 47 · 6장) ─────────────────────────────────────────
def make_validate_executor(policy_raw: dict, depreciation: dict,
                           target_keys=None) -> dict:
    """5차 검증.  fatal 1건이라도 실패하면 다음 단계를 실행하지 않는다 (STEP 66)."""
    from validate.base import PHASE_ORDER, gate, run_phase, save_results

    @dataclass
    class _VCtx:
        """검증 전용 문맥.  RunContext 는 frozen 이라 확장하지 않는다."""

        run_id: str
        policy_raw: dict
        depreciation: dict
        target_keys: tuple = ()      # --target 범위 (V1-07)
        started_at: object = None    # 이번 실행 시작 (V1-05)

    def s11(conn, ctx):
        t0 = time.time()
        at = ctx.started_at.isoformat()
        vctx = _VCtx(ctx.run_id, policy_raw, depreciation,
                     tuple(sorted(target_keys or ())), ctx.started_at)
        results = []
        for phase in PHASE_ORDER:
            results += run_phase(conn, vctx, phase)
        save_results(conn, results, at)
        blocked = gate(results)
        if blocked:
            from tools.sync_registry import halt_report
            print(halt_report(conn, blocked))
        rep = step_report("S11", None, len(results),
                          {"ok": sum(1 for r in results if r.passed),
                           "error": sum(1 for r in results if not r.passed)},
                          0, time.time() - t0)
        if blocked:
            rep.halted = True
            rep.halt_reason = " / ".join(
                f"{r.check.code} {r.check.title}: {r.actual}" for r in blocked)
        return rep, len(results)

    return {"S11": s11}


# ── S6a 등록부 동기화 (8장 STEP 87) ──────────────────────────────────
def make_registry_executor(root: str, clock, field_usage: dict) -> dict:
    """S6 직후에 돈다.  A안 — 미분류는 V4-11 이 fatal 로 잡는다.

    중단은 리포트를 막는 것이 아니라 판정을 막는 것이다.
    빈 화면으로 끝내지 않도록 suggested.json 을 함께 낸다.
    """
    from tools.sync_registry import sync_registry, write_suggested

    def s6a(conn, ctx):
        t0 = time.time()
        at = clock.now().isoformat()
        st = sync_registry(conn, field_usage, at)
        # ★ option3 사전은 여기서 채운다 (STEP 42).
        #   S3 은 S1·S2 뒤라 detail 원문이 아직 없다 — 거기서 뽑으면 빈다.
        #   halt 축이라 비어 있으면 S9 가 통째로 멈춘다 (V3-30 · 실측 08-15)
        from tools.build_dict import build_late_dict

        opt = build_late_dict(conn, ctx.site, ctx.dict_version, at)
        mapped = {r[1] for r in conn.execute(
            "SELECT site, json_path FROM meta_field_usage WHERE core_column IS NOT NULL")}
        n = write_suggested(
            conn, os.path.join(root, "config", "field_usage.suggested.json"),
            mapped)
        total = st.added + st.seen
        rep = step_report("S6a", None, total, {"ok": total}, 0, time.time() - t0)
        rep.halt_reason = (f"신규 {st.added} · 기존 {st.seen} · 유령 {st.ghost}"
                           f" · 분류 후보 {n}건 · 늦은 사전 {opt}종")
        return rep, total

    return {"S6a": s6a}
