# -*- coding: utf-8 -*-
"""사전 저장소 (L5).  RAW 에서 생성한다.

지시서   3장 STEP 36 · 4장 STEP 40 (코드 체계) · STEP 41 (축 · 축별 특성)
         STEP 42 (생성 규칙) · STEP 43 (완전 일치 · Count=0) · STEP 44 · STEP 45
근거     사전은 손으로 적지 않는다.  v1 은 「프론트펜더」로 적었고 원문은
         「프론트 휀더(우)」여서 가장 흔한 부위 344건이 미분류였다.
금지     신규 값을 조용히 무시하는 것.  대체값·기본값 반환.
         부분 문자열 검색 — "LPG" in fuel 은 LPG(일반인 구입) 과 가솔린+LPG 를 못 가른다.
         unknown 이라는 상태는 없다 — pending 이다.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date

from errors import ValidationError
from store.raw import commit

STATUS_CONFIRMED = "confirmed"
STATUS_PENDING = "pending"
STATUS_RETIRED = "retired"

SCOPE_GLOBAL = "global"
SCOPE_TARGET = "target"
SCOPE_MODEL = "model"


@dataclass(frozen=True)
class CodeEntry:
    """4장 정의서 구조체."""

    site: str
    scope: str
    axis: str
    code: str
    display: str
    count_seen: int
    first_seen: date
    last_seen: date
    status: str


# ── 축별 정책 (STEP 41 축별 특성 표) ─────────────────────────────────
# 축마다 같은 처리를 하면 안 된다.
#   panel_rank 는 5값 고정이다.  새 값은 점검 양식 변경이므로 판정 규칙 전체를 다시 봐야 한다
#   trim 은 차종·연식마다 늘어난다.  중단시키면 수집이 멈춘다
#
# on_new 를 가르는 것은 「값의 출처」가 아니라 「판정이 그 값에 걸려 있는가」다.
#              confirm  facet 이 선언한 열거값.  Count=0 도 사이트가 정의한 값이다 (STEP 43)
#                       사이트가 정의한 값이지 우리가 관측한 값이 아니다
#              pending  표시 전용이거나, 판정이 다른 축에 걸려 있는 값
#              halt     새 값이 뜨면 판정 방향을 알 수 없는 축
# on_conflict  같은 (scope_key, axis, code) 에 display 가 둘일 때
@dataclass(frozen=True)
class AxisPolicy:
    scope: str
    on_new: str  # confirm · pending · halt
    on_conflict: str  # halt · pending · allow


# 판정에 쓰는 축.  ★ 부위명(panel)은 표시 전용이라 여기 없다 (STEP 44).
#   표시 전용 축이 판정을 막으면 새 부위명 하나에 전 매물이 멈춘다
JUDGING_AXES: tuple[str, ...] = ("color_ext", "color_int", "fuel",
                                 "accident_type", "panel_rank",
                                 "panel_status")

AXIS_POLICY: dict[str, AxisPolicy] = {
    "option3": AxisPolicy(SCOPE_GLOBAL, "confirm", "halt"),
    "fuel": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "color_ext": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "color_int": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "sell_type": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "condition_flag": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "lease_type": AxisPolicy(SCOPE_GLOBAL, "confirm", "pending"),
    "trim": AxisPolicy(SCOPE_TARGET, "confirm", "pending"),
    "option_model": AxisPolicy(SCOPE_MODEL, "confirm", "allow"),
    # panel 은 표시 전용이다.  판정은 attributes(panel_rank) 가 한다.
    # 새 부위명이 떠도 랭크가 있으면 판정은 정상이다 — halt 로 두면 자주 멈춘다
    "panel": AxisPolicy(SCOPE_GLOBAL, "pending", "halt"),
    # panel_status 는 감점 대상 여부가 이 값에 직접 걸려 있다 (4값)
    # 새 값이 뜨면 감점인지 아닌지 알 수 없다
    "panel_status": AxisPolicy(SCOPE_GLOBAL, "halt", "halt"),
    # accident_type 은 1·2=내 차 피해 · 3=타 차 가해다 (3값)
    # 새 값이면 어느 쪽인지 모른다.  금액 집계가 통째로 틀린다
    "accident_type": AxisPolicy(SCOPE_GLOBAL, "halt", "halt"),
    # ★ 5값 고정.  새 값이 뜨면 점검 양식이 바뀐 것이다.  pending 으로 넘기지 않는다
    "panel_rank": AxisPolicy(SCOPE_GLOBAL, "halt", "halt"),
}

PANEL_RANK_VALUES: frozenset[str] = frozenset(
    {"RANK_ONE", "RANK_TWO", "RANK_A", "RANK_B", "RANK_C"}
)


def policy(axis: str) -> AxisPolicy:
    if axis not in AXIS_POLICY:
        raise ValidationError(
            f"축 정책 미정의: {axis}. STEP 41 표에 행을 추가한다", step="STEP 41"
        )
    return AXIS_POLICY[axis]


def scope_key(scope: str, site: str, target_key: str | None = None,
              model_catalog_key: str | None = None) -> str:
    """scope → scope_key (STEP 40).

    사전 키는 (scope_key, axis, code) 다.  code 단독으로 유일하지 않다.
    2차 사이트가 붙으면 같은 code 가 다른 사이트에서 다른 뜻이 된다.
    """
    if scope == SCOPE_GLOBAL:
        return site
    if scope == SCOPE_TARGET:
        if not target_key:
            raise ValidationError("scope=target 인데 target_key 가 없다", step="STEP 40")
        return f"{site}/{target_key}"
    if scope == SCOPE_MODEL:
        if not model_catalog_key:
            raise ValidationError(
                "scope=model 인데 model_catalog_key 가 없다. "
                "4~5자리 코드를 모델 없이 조회하는 것은 금지다",
                step="STEP 40",
            )
        return f"{site}/{model_catalog_key}"
    raise ValidationError(f"알 수 없는 scope: {scope}", step="STEP 40")


# ── 부트스트랩 (STEP 41) ─────────────────────────────────────────────
def seed_fixed_enums(conn: sqlite3.Connection, site: str, fixed: dict,
                     dict_version: str, at: str) -> int:
    """on_new=halt 인 축의 고정 집합을 미리 심는다.

    ★ 첫 수집에는 사전이 비어 있어 전 값이 「새 값」이 된다.
      그대로 두면 S3 이 항상 멈춘다 — 의도가 아니다.
    지시서가 값 집합을 명시한 축만 심는다.  여기 없는 값이 나오면 그때 멈춘다.
    금지   halt 축을 confirm 으로 바꾸는 것.  새 값을 못 잡게 된다
    """
    n = 0
    for axis, values in fixed.items():
        if axis.startswith("_"):
            continue
        if policy(axis).on_new != "halt":
            raise ValidationError(
                f"{axis} 는 halt 축이 아니다. 부트스트랩 대상이 아니다",
                step="STEP 41")
        for value in values:
            cur = conn.execute(
                "SELECT 1 FROM dict_enum WHERE site=? AND axis=? AND value=?",
                (site, axis, value)).fetchone()
            if cur:
                continue
            conn.execute(
                "INSERT INTO dict_enum"
                "(site,axis,value,display,count_seen,status,source_endpoint,"
                " dict_version,first_seen,last_seen)"
                " VALUES (?,?,?,?,0,?,'bootstrap',?,?,?)",
                (site, axis, value, value, STATUS_CONFIRMED, dict_version,
                 at, at))
            n += 1
    commit(conn)
    return n


# ── 적재 (STEP 42) ───────────────────────────────────────────────────
_MAPPED: dict | None = None


def mapped_of(axis: str, value: str) -> str | None:
    """사이트가 분류를 포기한 값을 우리 갈래로 (개정 398).

    ★ 값은 `config/dictionaries/mapped_values.json` 에 있다.
      가이드가 정하는 것이라 코드에 적지 않는다 (규칙 2 · S14)
    돌려줌   None 이면 값 그대로다.  「모름」이 아니다
    """
    global _MAPPED

    if _MAPPED is None:
        import json as _j
        import os as _o

        root = _o.path.dirname(_o.path.dirname(_o.path.abspath(__file__)))
        path = _o.path.join(root, "config", "dictionaries",
                            "mapped_values.json")
        _MAPPED = ((_j.load(open(path, encoding="utf-8")).get("mapped") or {})
                   if _o.path.isfile(path) else {})
    return (_MAPPED.get(axis) or {}).get(value)


def upsert_enum(conn: sqlite3.Connection, site: str, axis: str, value: str,
                display: str, count_seen: int, source_endpoint: str,
                dict_version: str, at: str,
                force_pending: bool = False) -> str:
    """반환   'new' · 'seen' · 'conflict'

    Count=0 이라고 건너뛰지 않는다.  사이트가 정의한 열거값이다 (STEP 43).

    force_pending   facet 없이 목록에서 관측한 값이다 (개정 266).
                    ★ 「전체 집합을 봤다」가 아니므로 confirmed 로 올리지 않는다
    """
    pol = policy(axis)
    cur = conn.execute(
        "SELECT status, display FROM dict_enum WHERE site=? AND axis=? AND value=?",
        (site, axis, value),
    ).fetchone()

    if cur is None:
        if pol.on_new == "halt":
            raise ValidationError(
                f"{axis} 에 새 값: {value!r}. 이 축은 값이 늘어날 수 없다. "
                "점검 양식 변경을 의심한다",
                step="STEP 41",
            )
        status = STATUS_CONFIRMED if pol.on_new == "confirm" else STATUS_PENDING
        if force_pending:
            status = STATUS_PENDING
        conn.execute(
            "INSERT INTO dict_enum"
            "(site,axis,value,display,mapped,count_seen,status,"
            " source_endpoint,dict_version,first_seen,last_seen)"
            " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (site, axis, value, display, mapped_of(axis, value), count_seen,
             status, source_endpoint, dict_version, at, at),
        )
        conn.commit()
        return "new"

    if cur[1] != display:
        return _handle_conflict(conn, pol, site, axis, value, cur[1], display, at)

    conn.execute(
        "UPDATE dict_enum SET count_seen=?, last_seen=?, mapped=?, "
        "status=CASE WHEN status=? THEN ? ELSE status END "
        "WHERE site=? AND axis=? AND value=?",
        (count_seen, at, mapped_of(axis, value),
         STATUS_RETIRED, STATUS_CONFIRMED, site, axis, value),
    )
    conn.commit()
    return "seen"


def _handle_conflict(conn, pol, site, axis, value, old_display,
                     new_display, at) -> str:
    """충돌은 최신 값으로 덮어쓰지 않는다.  사람이 판정한다 (STEP 45).

    판정 전까지 그 코드는 판정에 쓰지 않는다.
    """
    if pol.on_conflict == "allow":
        return "seen"
    if pol.on_conflict == "halt":
        raise ValidationError(
            f"{axis} 충돌: {value!r} → {old_display!r} / {new_display!r}. 전제가 깨졌다",
            step="STEP 45",
        )
    conn.execute(
        "UPDATE dict_enum SET status=?, last_seen=? WHERE site=? AND axis=? AND value=?",
        (STATUS_PENDING, at, site, axis, value),
    )
    conn.commit()
    return "conflict"


def upsert_option3(conn: sqlite3.Connection, site: str, target_key: str,
                   code: str, display: str, count_seen: int,
                   dict_version: str, at: str) -> str:
    """3자리 코드는 전 차종 공통이다 — 그러나 그것도 실측 결과다.

    같은 (site, code) 에 display 가 둘이면 공통성 가정이 깨진 것이다.
    조용히 넘기면 P1 전체가 무너진다 (STEP 40 · 45).
    """
    clash = conn.execute(
        "SELECT target_key, display FROM dict_option_code "
        "WHERE site=? AND code=? AND display<>?",
        (site, code, display),
    ).fetchone()
    if clash is not None:
        raise ValidationError(
            f"3자리 코드 충돌: {code} → {clash[1]!r} / {display!r}. "
            "「전 차종 공통」 가정이 깨졌다",
            step="STEP 45",
        )
    exists = conn.execute(
        "SELECT 1 FROM dict_option_code WHERE site=? AND target_key=? AND code=?",
        (site, target_key, code),
    ).fetchone()
    conn.execute(
        "INSERT OR REPLACE INTO dict_option_code"
        "(site,target_key,code,display,count_seen,status,dict_version,"
        " first_seen,last_seen) VALUES (?,?,?,?,?,?,?,"
        " COALESCE((SELECT first_seen FROM dict_option_code"
        "           WHERE site=? AND target_key=? AND code=?), ?), ?)",
        (site, target_key, code, display, count_seen, STATUS_CONFIRMED,
         dict_version, site, target_key, code, at, at),
    )
    conn.commit()
    return "seen" if exists else "new"


def retire_unseen(conn: sqlite3.Connection, site: str, axis: str, at: str) -> int:
    """이번 수집에 없던 값은 retired.  삭제하지 않는다 (STEP 42).

    「미관측」이지 「존재하지 않음」이 아니다.  과거 매물 해석에 필요하다.
    """
    cur = conn.execute(
        "UPDATE dict_enum SET status=? WHERE site=? AND axis=? "
        "AND last_seen < ? AND status<>?",
        (STATUS_RETIRED, site, axis, at, STATUS_PENDING),
    )
    conn.commit()
    return cur.rowcount


# ── 조회 (STEP 40 · 44 · 1장 STEP 14.1) ──────────────────────────────
def resolve_code(conn: sqlite3.Connection, axis: str, code: str,
                 scope_key_value: str) -> CodeEntry | None:
    """코드 → 표시명.  scope_key 를 반드시 받는다.

    금지   scope_key 없이 code 만으로 조회하는 API 를 만드는 것 (STEP 40)
    """
    pol = policy(axis)
    site = scope_key_value.split("/")[0]
    if pol.scope == SCOPE_MODEL:
        model = scope_key_value.split("/", 1)[1]
        row = conn.execute(
            "SELECT option_name, status, first_seen, last_seen "
            "FROM dict_model_option WHERE site=? AND model_catalog_key=? "
            "AND option_code=?",
            (site, model, code),
        ).fetchone()
        if row is None:
            return None
        return CodeEntry(site, pol.scope, axis, code, row[0], 0,
                         row[2], row[3], row[1])
    if axis == "option3":
        row = conn.execute(
            "SELECT display, count_seen, status, first_seen, last_seen "
            "FROM dict_option_code WHERE site=? AND code=? LIMIT 1",
            (site, code),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT display, count_seen, status, first_seen, last_seen "
            "FROM dict_enum WHERE site=? AND axis=? AND value=?",
            (site, axis, code),
        ).fetchone()
    if row is None:
        return None
    return CodeEntry(site, pol.scope, axis, code, row[0], row[1] or 0,
                     row[3], row[4], row[2])


def installed_option_names(conn: sqlite3.Connection, site: str,
                           model_catalog_key: str, codes: list[str]) -> list[str]:
    """그 매물이 실제로 장착한 코드만 받는다 (1장 STEP 14.1).

    판별법   빈 codes 에 빈 목록을 반환하지 않으면 금지 위반이다.
             카탈로그 전체 목록을 장착으로 취급하면 전 매물이 '있음' 이 된다
    """
    if not codes:
        return []
    key = scope_key(SCOPE_MODEL, site, model_catalog_key=model_catalog_key)
    out = []
    for c in codes:
        e = resolve_code(conn, "option_model", c, key)
        if e is not None:
            out.append(e.display)
    return out


def normalize_enum(conn: sqlite3.Connection, site: str, axis: str,
                   raw_value: str) -> str | None:
    """관측된 표기 변형만 정규화한다.  의미 추론·분류·대체값 생성은 하지 않는다.

    금지   사전에 없는 값을 「비슷하니까」 기존 값으로 매핑
           공백 제거 · 괄호 제거 · 유사 문자 치환으로 억지 매칭
           부분 문자열 검색 (STEP 43)
    반환   confirmed 값 또는 None.  None 이면 호출측이 pending 에 적재한다
    """
    row = conn.execute(
        "SELECT value FROM dict_enum WHERE site=? AND axis=? AND value=? AND status=?",
        (site, axis, raw_value, STATUS_CONFIRMED),
    ).fetchone()
    return row[0] if row else None


def assert_no_unknown(conn: sqlite3.Connection, site: str, axis: str) -> None:
    """미분류 0건 시험 (STEP 45).

    pending 이 있으면 그 축을 쓰는 판정을 중단한다.  기본값으로 넘어가지 않는다.
    v1 은 미분류를 unknown 으로 삼켜 accident_type 전건 unknown 이 됐다.

    panel_rank 는 값 집합 자체를 확인한다.  5값 고정이기 때문이다.
    """
    if axis == "panel_rank":
        seen = {
            r[0] for r in conn.execute(
                "SELECT value FROM dict_enum WHERE site=? AND axis=?", (site, axis))
        }
        extra = seen - PANEL_RANK_VALUES
        if extra:
            raise ValidationError(
                f"panel_rank 에 정의 밖 값: {sorted(extra)}. 점검 양식 변경이다",
                step="STEP 41",
            )
    rows = conn.execute(
        "SELECT value FROM dict_enum WHERE site=? AND axis=? AND status=? LIMIT 20",
        (site, axis, STATUS_PENDING),
    ).fetchall()
    if rows:
        raise ValidationError(
            f"사전 미검토 {len(rows)}건 (axis={axis}): "
            + ", ".join(r[0] for r in rows),
            step="STEP 45",
        )

    # ★ 「미검토 0건」과 「사전이 없다」는 다르다 (A-4).
    #   pending 만 보면 dict_enum 이 0행이어도 통과한다 —
    #   v1 이 accident_type 전건 unknown 이 된 것과 같은 자리다
    total = conn.execute(
        "SELECT COUNT(*) FROM dict_enum WHERE site=? AND axis=?",
        (site, axis)).fetchone()[0]
    if not total:
        raise ValidationError(
            f"사전이 비어 있다 (axis={axis}). S3 을 먼저 돌린다",
            step="STEP 45",
        )


def bump_dict_version(current: str) -> str:
    """사전이 바뀌면 버전을 올린다 (STEP 45).

    올리지 않으면 「어제 점수 vs 오늘 점수」에서 사전 변경을 매물 변경으로 오인한다.
    """
    body = current.lstrip("d")
    return f"d{int(body) + 1}" if body.isdigit() else f"{current}.1"


# ── 검토 (STEP 45) ───────────────────────────────────────────────────
def list_pending(conn: sqlite3.Connection, site: str) -> list[tuple]:
    """검토 대기 목록.  사람이 확인하기 전에는 그 축이 판정에 안 쓰인다."""
    return conn.execute(
        "SELECT axis, value, display, count_seen, source_endpoint, first_seen "
        "FROM dict_enum WHERE site=? AND status=? "
        "ORDER BY axis, count_seen DESC", (site, STATUS_PENDING)).fetchall()


def confirm_enum(conn: sqlite3.Connection, site: str, axis: str,
                 value: str, at: str) -> str:
    """pending → confirmed.  ★ 사람이 원문을 보고 확정한다 (STEP 45).

    금지   전건 일괄 확정을 코드가 자동으로 하는 것.
          그러면 pending 이 있는 이유가 사라진다
    """
    cur = conn.execute(
        "SELECT status FROM dict_enum WHERE site=? AND axis=? AND value=?",
        (site, axis, value)).fetchone()
    if cur is None:
        raise ValidationError(f"없는 값: {axis}.{value}", step="STEP 45")
    if cur[0] != STATUS_PENDING:
        return cur[0]
    conn.execute(
        "UPDATE dict_enum SET status=?, last_seen=? "
        "WHERE site=? AND axis=? AND value=?",
        (STATUS_CONFIRMED, at, site, axis, value))
    commit(conn)
    return STATUS_CONFIRMED
