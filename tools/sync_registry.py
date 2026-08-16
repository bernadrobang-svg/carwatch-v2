# -*- coding: utf-8 -*-
"""RAW 경로 전수 → meta_field_usage.

지시서   8장 STEP 87 · 6장 STEP 61 (V4-06 · 06b)
근거     등록부는 산문이 아니라 테이블이다.  문서는 기계가 검증할 수 없다.
         v1 방치의 근본 원인은 미사용 목록이 문서에만 있었다는 것이다.
필수     ★ 형식 검증을 통과한 원문만 훑는다.  endpoint 라벨이 아니라 내용으로 판정한다.
         v1 record 를 라벨로 훑으면 142경로가 나온다.  실제는 49개이고
         나머지는 점검부 오염분이다.  등록부에 record 가 master·outers 를
         갖는 것으로 기록된다.
금지     endpoint 컬럼만 믿고 경로를 추출하는 것.
         시드를 손으로 적어 넣는 것 — 전량은 여기가 RAW 에서 만든다.
사용     python3 tools/sync_registry.py <db>
"""
from __future__ import annotations

from contracts import json_paths  # noqa: F401

import json
import sqlite3
import sys
from dataclasses import dataclass

sys.path.insert(0, ".")

from adapters.encar import SITE_CODE, _SCHEMA  # noqa: E402
from collect.fetcher import verify_shape  # noqa: E402
from contracts import FetchResult  # noqa: E402

@dataclass(frozen=True)
class FieldUsage:
    """8장 정의서 구조체."""

    site: str
    endpoint: str
    json_path: str
    core_column: str | None
    usage: str
    reason: str
    unblock_condition: str | None
    use_when: str | None
    priority: int | None
    first_seen: str
    last_seen: str


@dataclass
class RegistrySyncReport:
    added: int = 0
    seen: int = 0
    ghost: int = 0
    retired: int = 0


USAGE_UNCLASSIFIED = "unclassified"
USAGE_NOT_PROVIDED = "not_provided"

# 사람이 분류해야 하는 상태.  자동으로 덮어쓰지 않는다
HUMAN_OWNED = ("in_use", "display_only", "unused_by_policy",
               "deferred", "blocked", "not_provided")


# json_paths 는 contracts.py 다 — store/adminops 도 쓴다 (STEP 15a)


def facet_path(node) -> str:
    """facet 축은 (Name, Type) 을 합쳐 하나의 json_path 로 만든다 (STEP 87).

    금지   Name 만 쓰는 것 — Price · Mileage 가 서로를 덮어써 등록부가 2건 유실된다
    """
    return f"{node['Name']}#{node['Type']}"


def scan_paths(conn: sqlite3.Connection, endpoint: str) -> list[str]:
    """그 엔드포인트의 RAW 경로 전수.  형식 검증 통과분만 (STEP 87)."""
    return sorted({p for (e, p) in collect_paths(conn) if e == endpoint})


def shape_ok(endpoint: str, body) -> bool:
    """내용으로 판정한다.  라벨을 믿지 않는다 (STEP 18 required_keys).

    ★ 이 한 줄이 등록부 오염을 막는다.  V4-06b 역방향 검사로는 안 잡힌다 —
      오염분은 「있는 것처럼」 보이기 때문에 입력 단계에서 걸러야 한다.
    """
    spec = _SCHEMA.get(endpoint)
    if spec is None:
        return False
    res = FetchResult(endpoint, None, "ok", body, None, None, None)
    return verify_shape(res, spec)


def _walk_values(node, trail="", out=None):
    """(경로, 값).  분류 후보를 내려면 값을 봐야 한다."""
    out = out if out is not None else []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{trail}.{k}" if trail else k
            out.append((p, v))
            _walk_values(v, p, out)
    elif isinstance(node, list):
        for el in node:
            _walk_values(el, f"{trail}[]", out)
    return out


def collect_values(conn: sqlite3.Connection
                   ) -> dict[tuple[str, str], list]:
    """(endpoint, json_path) → 관측 값 목록.  형식 검증 통과분만."""
    seen: dict[tuple[str, str], list] = {}
    for endpoint, body in conn.execute(
        "SELECT endpoint, body FROM raw_response WHERE status='ok'"
    ):
        try:
            doc = json.loads(body)
        except (ValueError, TypeError):
            continue
        if not shape_ok(endpoint, doc):
            continue
        targets = [doc]
        if endpoint == "list":
            targets = (doc.get("SearchResults") or [])[:1] or [doc]
        for tgt in targets:
            for p, v in _walk_values(tgt):
                if isinstance(v, (dict, list)):
                    v = None
                seen.setdefault((endpoint, p), []).append(v)
    return seen


def collect_paths(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    """(endpoint, json_path) → 관측 건수.  형식 검증 통과분만."""
    seen: dict[tuple[str, str], int] = {}
    for endpoint, body in conn.execute(
        "SELECT endpoint, body FROM raw_response WHERE status='ok'"
    ):
        try:
            doc = json.loads(body)
        except (ValueError, TypeError):
            continue
        if not shape_ok(endpoint, doc):
            continue  # 오염분.  등록부에 넣지 않는다
        # 목록은 봉투다.  요소 경로를 함께 뽑는다 (STEP 18a)
        targets = [doc]
        if endpoint == "list":
            targets = (doc.get("SearchResults") or [])[:1] or [doc]
        for t in targets:
            for p in json_paths(t):
                key = (endpoint, p)
                seen[key] = seen.get(key, 0) + 1
    return seen


def _seed_for(cfg: dict, endpoint: str, path: str) -> dict:
    seed = cfg["seed"]
    hit = seed.get(f"{endpoint}:{path}")
    if hit:
        return hit
    star = seed.get(f"{endpoint}:*")
    if star:
        return star
    return cfg["default"]


def sync_registry(conn: sqlite3.Connection, cfg: dict, at: str,
                  site: str = SITE_CODE) -> RegistrySyncReport:
    """RAW → 등록부.  CORE 컬럼이 없는 경로도 등록한다.

    「매핑표에 없으니 등록도 안 한다」가 v1 방치의 경로였다.
    반환   RegistrySyncReport
    """
    observed = collect_paths(conn)
    stat = RegistrySyncReport()

    for (endpoint, path), _n in sorted(observed.items()):
        row = conn.execute(
            "SELECT usage FROM meta_field_usage "
            "WHERE site=? AND endpoint=? AND json_path=?",
            (site, endpoint, path)).fetchone()
        if row is None:
            s = _seed_for(cfg, endpoint, path)
            conn.execute(
                "INSERT INTO meta_field_usage"
                "(site,endpoint,json_path,core_column,usage,reason,"
                " unblock_condition,use_when,priority,miss_streak,"
                " first_seen,last_seen) VALUES (?,?,?,?,?,?,?,?,?,0,?,?)",
                (site, endpoint, path, s.get("core_column"), s["usage"],
                 s["reason"], s.get("unblock_condition"), s.get("use_when"),
                 s.get("priority"), at, at))
            stat.added += 1
        else:
            # ★ 사람이 field_usage.json 을 채운 뒤 재실행하면 반영돼야 한다.
            #   기존 행이라고 건너뛰면 분류가 영영 안 붙는다 (실측: 305건)
            s = _seed_for(cfg, endpoint, path)
            if row[0] == USAGE_UNCLASSIFIED and s["usage"] != USAGE_UNCLASSIFIED:
                conn.execute(
                    "UPDATE meta_field_usage SET usage=?, reason=?,"
                    " core_column=?, unblock_condition=?, use_when=?,"
                    " priority=?, last_seen=?, miss_streak=0"
                    " WHERE site=? AND endpoint=? AND json_path=?",
                    (s["usage"], s["reason"], s.get("core_column"),
                     s.get("unblock_condition"), s.get("use_when"),
                     s.get("priority"), at, site, endpoint, path))
                stat.added += 1
            else:
                conn.execute(
                    "UPDATE meta_field_usage SET last_seen=?, miss_streak=0 "
                    "WHERE site=? AND endpoint=? AND json_path=?",
                    (at, site, endpoint, path))
                stat.seen += 1

    # ★ 유령 경로 — 등록부에만 있는 항목 (STEP 87)
    #   「미사용으로 분류했다」고 안심하게 만드는데 그 필드는 애초에 없었다
    limit = cfg["ghost_miss_limit"]
    for endpoint, path, usage, streak in conn.execute(
        "SELECT endpoint, json_path, usage, miss_streak FROM meta_field_usage "
        "WHERE site=?", (site,)
    ).fetchall():
        if (endpoint, path) in observed:
            continue
        streak += 1
        stat.ghost += 1
        new_usage = usage
        if streak >= limit and usage != USAGE_NOT_PROVIDED:
            new_usage = USAGE_NOT_PROVIDED
            stat.retired += 1
        conn.execute(
            "UPDATE meta_field_usage SET miss_streak=?, usage=?, "
            "reason=reason || ? WHERE site=? AND endpoint=? AND json_path=?",
            (streak, new_usage,
             f" | {streak}회 연속 미관측" if new_usage != usage else "",
             site, endpoint, path))
    conn.commit()
    return stat


# ── 분류 후보 (STEP 87) ──────────────────────────────────────────────
# 사람은 후보를 확인·수정만 한다.  빈 표에서 시작하지 않는다.
# 금지   제안을 그대로 적용하는 것.  suggested → field_usage 이동은 사람이 한다
SUGGEST_UNUSED = "unused_by_policy"
SUGGEST_NOT_PROVIDED = "not_provided"
SUGGEST_IN_USE = "in_use"

SAMPLE_KEEP = 3


def suggest_usage(values: list, mapped: bool) -> tuple[str, str]:
    """반환   (후보 usage, 근거)"""
    if mapped:
        return SUGGEST_IN_USE, "매핑표에 있는 경로"
    kinds = {json.dumps(v, ensure_ascii=False, sort_keys=True) for v in values}
    if all(v is None or v is False for v in values):
        return SUGGEST_NOT_PROVIDED, "전건 null·false"
    if len(kinds) == 1 and len(values) > 1:
        return SUGGEST_UNUSED, "값이 전건 동일 — 변별력 0"
    return USAGE_UNCLASSIFIED, "판단 근거 없음. 사람이 정한다"


def write_suggested(conn: sqlite3.Connection, path: str,
                    mapped_paths: set[str], site: str = SITE_CODE) -> int:
    """미분류 경로에 후보를 붙여 낸다.

    ★ 수백 건이 부담인 것이 아니라, 아무 단서 없이 422줄을 보는 것이 어렵다
    """
    values = collect_values(conn)
    rows = {}
    for endpoint, jp in list_by_usage(conn, USAGE_UNCLASSIFIED, site):
        obs = values.get((endpoint, jp), [])
        usage, why = suggest_usage(obs, jp in mapped_paths)
        rows[f"{endpoint}:{jp}"] = {
            "suggested_usage": usage,
            "reason_hint": why,
            "observed": len(obs),
            "samples": [v for v in obs[:SAMPLE_KEEP]],
        }
    with open(path, "w", encoding="utf-8") as f:
        json.dump({
            "_note": ("sync_registry 가 낸 분류 후보다. 정본은 config/field_usage.json "
                      "이다. 그대로 옮기지 않는다 — 사람이 확인·수정한다"),
            "count": len(rows),
            "candidates": rows,
        }, f, ensure_ascii=False, indent=2)
    return len(rows)


def halt_report(conn: sqlite3.Connection, blocked: list,
                site: str = SITE_CODE) -> str:
    """중단은 리포트를 막는 것이 아니라 판정을 막는 것이다 (STEP 87).

    빈 화면으로 끝내지 않는다.
    """
    lines = ["■ 중단 사유"]
    for r in blocked:
        lines.append(f"  {r.check.code} {r.check.title} — {r.actual}")
    un = list_by_usage(conn, USAGE_UNCLASSIFIED, site)
    if un:
        values = collect_values(conn)
        lines.append(f"\n■ 미분류 경로 {len(un)}건")
        for endpoint, jp in un:
            obs = values.get((endpoint, jp), [])
            s = ", ".join(str(v)[:30] for v in obs[:SAMPLE_KEEP])
            lines.append(f"  {endpoint:11} {jp:44} 관측 {len(obs):4}  {s}")
        lines.append("\n■ 조치")
        lines.append("  config/field_usage.suggested.json 의 후보를 확인·수정해")
        lines.append("  config/field_usage.json 으로 옮긴 뒤 재실행한다")
    return "\n".join(lines)


def list_by_usage(conn: sqlite3.Connection, usage: str,
                  site: str = SITE_CODE) -> list[tuple[str, str]]:
    return [(r[0], r[1]) for r in conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage "
        "WHERE site=? AND usage=? ORDER BY endpoint, json_path", (site, usage))]


def assert_registered(conn: sqlite3.Connection, site: str = SITE_CODE) -> None:
    """unclassified 가 있으면 fatal 이다 (V4-11).

    사람이 분류하기 전에는 그 경로를 판정에 쓸 수 없다.
    """
    from errors import ValidationError

    rows = list_by_usage(conn, USAGE_UNCLASSIFIED, site)
    if rows:
        raise ValidationError(
            f"미분류 경로 {len(rows)}건: "
            + ", ".join(f"{e}:{p}" for e, p in rows[:10]),
            step="STEP 87")


if __name__ == "__main__":
    from datetime import datetime, timezone

    db = sys.argv[1]
    with open("config/field_usage.json", encoding="utf-8") as f:
        cfg = json.load(f)
    c = sqlite3.connect(db)
    st = sync_registry(c, cfg, datetime.now(timezone.utc).isoformat())
    print(f"신규 {st.added} · 기존 {st.seen} · 유령 {st.ghost}"
          f" · not_provided 전환 {st.retired}")
    for endpoint, n in c.execute(
        "SELECT endpoint, COUNT(*) FROM meta_field_usage GROUP BY endpoint"
    ):
        print(f"  {endpoint:12} {n}경로")
    un = len(list_by_usage(c, USAGE_UNCLASSIFIED))
    print(f"\nunclassified {un}건 — 분류 전에는 V4-11 이 fatal 이다")
