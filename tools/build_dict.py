# -*- coding: utf-8 -*-
"""RAW → 사전 생성.

지시서   0장 STEP 6 (tools/build_dict.py 가 생성한다) · 3장 STEP 36
         4장 STEP 41 (사전 축 목록) · STEP 42 (생성 규칙)
근거     사전은 손으로 적지 않는다.  원문에서 뽑으면 「휀더/펜더」가 애초에 안 생긴다.
금지     신규 값을 조용히 무시하는 것.  표기 변형을 임의로 병합하는 것.
사용     python3 tools/build_dict.py <db> <dict_version>
"""
from __future__ import annotations

import json
import os
import sqlite3
import sys
from dataclasses import dataclass, field

sys.path.insert(0, ".")

from store.dictionary import (  # noqa: E402
    seed_fixed_enums, upsert_enum, upsert_option3,
)

# ── 사전 축 목록 (4장 STEP 41) ───────────────────────────────────────
# 표에 없는 축은 사전을 만들지 않는다.  축이 늘면 여기에 행을 추가한다.
# (axis, scope, endpoint, 원천 경로)
# 매물 원문(detail · inspection)이 있어야 채워지는 축.
# ★ S3 은 S1·S2 뒤라 이 원문이 아직 없다 — 거기서 뽑으면 사전이 빈다.
#   halt 축이라 비면 S9 가 통째로 멈춘다 (V3-30 · 실측 08-15)
LATE_AXES = frozenset({"option3", "panel"})

# facet 을 못 받았을 때 대신 볼 목록 경로 (개정 266).
# ★ facet 이 정본이다.  이것은 「지금 매물이 가진 값」일 뿐이라 pending 으로만 들어간다
LIST_FALLBACK: dict[str, str] = {
    "fuel": "SearchResults[].FuelType",
    "color_ext": "SearchResults[].Color",
    "color_int": "SearchResults[].SeatColor",
    "sell_type": "SearchResults[].SellType",
}

AXIS_SOURCES: tuple[tuple[str, str, str, str], ...] = (
    # ★ facet 은 옵션 열거를 주지 않는다 (실측 08-15 · raw_facet 에 Options 없음).
    #   detail.options 가 3자리 코드를 준다 — '001' · '1009' 형태다.
    #   code 자리에 한글 이름을 넣으면 사이트가 표기를 바꿀 때 전건이 새 코드가 된다
    ("option3", "global", "detail", "options.standard[]"),   # S6a 가 채운다
    ("option_model", "model", "catalog", "optionCd"),
    ("fuel", "global", "facet", "FuelType"),
    ("color_ext", "global", "facet", "Color"),
    ("color_int", "global", "facet", "SeatColor"),
    # ★ facet 이 Badge 를 주지 않는다 (실측).  목록 봉투에서 뽑는다
    ("trim", "target", "list", "SearchResults[].Badge"),
    ("sell_type", "global", "facet", "SellType"),
    ("condition_flag", "global", "facet", "Condition"),
    ("lease_type", "global", "facet", "LeaseType"),
    ("panel", "global", "inspection", "outers[].type.title"),
    ("panel_rank", "global", "inspection", "outers[].attributes"),
    ("panel_status", "global", "inspection", "outers[].statusTypes[].title"),
    ("accident_type", "global", "record", "accidents[].type"),
)


@dataclass
class DictBuildReport:
    """생성 결과.  신규 값은 pending 이므로 사람이 봐야 한다."""

    dict_version: str
    new_values: dict[str, list[str]] = field(default_factory=dict)
    conflicts: dict[str, list[str]] = field(default_factory=dict)
    seen_counts: dict[str, int] = field(default_factory=dict)
    # facet 없이 목록에서 관측한 축 (개정 266).  ★ 완전한 집합이 아니다
    from_list: dict[str, list[str]] = field(default_factory=dict)

    @property
    def pending_total(self) -> int:
        return sum(len(v) for v in self.new_values.values())


def extract_distinct(conn: sqlite3.Connection, endpoint: str,
                     json_path: str) -> list[tuple[str, int]]:
    """RAW 에서 값·빈도를 뽑는다.

    반환   [(값, 빈도)].  빈도는 분포 참고용이다 — 판정 근거가 아니다 (2장 STEP 23)
    """
    counts: dict[str, int] = {}
    if endpoint == "facet":
        rows = conn.execute("SELECT body FROM raw_facet")
        for (body,) in rows:
            for _name, value, cnt in _facet_values(json.loads(body), json_path):
                # ★ Count=0 도 넣는다.  「그 값이 없다」가 아니라
                #   「이 쿼리 범위에 없다」다.  사이트가 정의한 열거값이다 (STEP 43)
                counts[value] = counts.get(value, 0) + cnt
    else:
        # ★ 반입분은 사이트 응답이 아니다.  CSV·ID 목록을 json.loads 하면
        #   사전 만들기가 통째로 죽는다 (13장 STEP 136a · 실측 08-16)
        rows = conn.execute(
            "SELECT body FROM raw_response WHERE endpoint = ? "
            "AND status = 'ok' AND origin <> 'import'",
            (endpoint,),
        )
        from store.raw import raw_body

        # ★★★★★ 09-02 — ★ **원문이 다 JSON 은 아니다.**
        #   ★ 리본카·BMW BPS·보배드림·KB·현대인증·볼보는 ★ **HTML 쪽**을 준다 —
        #   ★ ★ 그것이 그 사이트의 ★ **바른 원문**이다 (실측 09-02 — 2,766건).
        #   ★★ 전에는 ★ `json.loads` 가 ★ 그 첫 줄에서 죽어 ★ **S6a 가 통째로 멎었다**
        #     ★ ★ (`JSONDecodeError: line 16 column 1` · 실측 09-02).
        #   ★ 건너뛰되 ★ **조용히 넘기지 않는다** — ★ 몇 건인지 낸다
        skipped = 0
        for (body,) in rows:
            try:
                doc = json.loads(raw_body(body))
            except (ValueError, TypeError):
                skipped += 1
                continue
            for value in _walk_path(doc, json_path):
                counts[value] = counts.get(value, 0) + 1
        if skipped:
            print(f"    ★ {endpoint} — JSON 이 아닌 원문 {skipped}건은 건너뛴다 "
                  f"(HTML 쪽을 주는 사이트다)")
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))


def _facet_values(body, axis_name: str):
    """축은 (Name, Type='Aspect') 인 노드다.  Name 만으로 훑지 않는다 (2장 STEP 23)."""
    stack = [body]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("Name") == axis_name and node.get("Type") == "Aspect":
                for f in node.get("Facets") or []:
                    val = f.get("Value")
                    if val is not None:
                        yield axis_name, str(val), int(f.get("Count") or 0)
            stack.extend(v for v in node.values() if isinstance(v, (dict, list)))
        elif isinstance(node, list):
            stack.extend(v for v in node if isinstance(v, (dict, list)))


def facet_value_set(conn: sqlite3.Connection, axis: str) -> set:
    """그 축에 대해 사이트가 인정하는 값의 전체 집합 (12-dict).

    ★ `dict_enum.source_endpoint` 로는 이것을 알 수 없다.  그 컬럼은
      「어디서 처음 봤나」지 「facet 에 있나」가 아니다 —
      facet 이 늦게 와도 이미 목록에서 본 값은 'list' 로 남는다.
      둘을 같은 것으로 읽어 V3-38 이 41건을 「facet 에 없다」고 했다 (실측 08-18)
    돌려줌   빈 집합이면 facet 이 그 축을 안 주는 것이다 (trim 이 그렇다)
    """
    name = {a: p for a, _s, ep, p in AXIS_SOURCES if ep == "facet"}.get(axis)
    if not name:
        return set()
    out = set()
    for (body,) in conn.execute("SELECT body FROM raw_facet"):
        for _n, value, _cnt in _facet_values(json.loads(body), name):
            out.add(value)
    return out


def _walk_path(body, path: str):
    """`outers[].type.title` 같은 경로를 따라간다."""
    cur = [body]
    for part in path.split("."):
        nxt = []
        arr = part.endswith("[]")
        key = part[:-2] if arr else part
        for node in cur:
            if not isinstance(node, dict):
                continue
            v = node.get(key)
            if v is None:
                continue
            if arr and isinstance(v, list):
                nxt.extend(v)
            else:
                nxt.append(v)
        cur = nxt
    for v in cur:
        if isinstance(v, list):
            for x in v:
                if isinstance(x, (str, int)):
                    yield str(x)
        elif isinstance(v, (str, int)):
            yield str(v)


def load_fixed_enums(root: str | None = None) -> dict:
    """고정 열거 집합.  지시서가 값을 명시한 halt 3축이다 (STEP 41)."""
    root = root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(root, "config", "dictionaries",
                           "fixed_enums.json"), encoding="utf-8") as f:
        return json.load(f)


def build_dict(conn: sqlite3.Connection, site: str, dict_version: str,
               at: str) -> DictBuildReport:
    """RAW → 사전 생성·갱신.

    신규 값은 status='pending' 으로 적재하고 알린다.
    사람이 확인하기 전에는 그 축을 쓰는 판정이 돌지 않는다 (4장 STEP 45).
    """
    # ★ on_new='halt' 축은 고정 집합을 먼저 심는다 (STEP 41).
    #   첫 수집에는 사전이 비어 있어 정상값(RANK_ONE)도 「새 값」이 된다
    seed_fixed_enums(conn, site, load_fixed_enums(), dict_version, at)

    rep = DictBuildReport(dict_version=dict_version)
    for axis, _scope, endpoint, path in AXIS_SOURCES:
        if axis == "option_model":
            continue  # 카탈로그는 build_catalog_dict 가 담당한다 (STEP 22)
        if axis in LATE_AXES:
            continue  # ★ 매물 원문이 필요하다 — S6a 가 담당한다 (V3-30)
        values = extract_distinct(conn, endpoint, path)
        # ★ facet 을 못 받으면 목록에서 관측한 값으로 pending 을 만든다
        #   (개정 266).  「전체 집합을 봤다」가 아니므로 confirmed 로 올리지 않는다
        observed = False
        if not values and endpoint == "facet" and axis in LIST_FALLBACK:
            endpoint = "list"
            path = LIST_FALLBACK[axis]
            values = extract_distinct(conn, endpoint, path)
            if values:
                observed = True
                rep.from_list.setdefault(axis, []).extend(v for v, _n in values)
        rep.seen_counts[axis] = len(values)
        for value, cnt in values:
            if axis == "option3":
                # ★ code 는 식별자다.  display 는 사람이 채운다 —
                #   원문이 이름을 안 주므로 code 를 그대로 두고 사람이 붙인다
                if upsert_option3(conn, site, "*", value, value, cnt,
                                  dict_version, at) == "new":
                    rep.new_values.setdefault(axis, []).append(value)
                continue
            # on_new='halt' 인 축은 여기서 ValidationError 가 올라온다.
            # 삼키지 않는다 — 새 값이 뜨면 판정 방향을 알 수 없는 축이다 (STEP 41)
            r = upsert_enum(conn, site, axis, value, value, cnt,
                            endpoint, dict_version, at,
                            force_pending=observed)
            if r == "new":
                rep.new_values.setdefault(axis, []).append(value)
            elif r == "conflict":
                rep.conflicts.setdefault(axis, []).append(value)
    if rep.from_list:
        _mark_facet_substituted(conn, rep, at)
    return rep


def _mark_facet_substituted(conn: sqlite3.Connection, rep: "DictBuildReport",
                            at: str) -> None:
    """facet 을 목록 관측이 대신했음을 남긴다 (개정 266 · 259 방식).

    ★ 근거 없이 단계를 열지 않는다.  실제로 관측한 축과 값 수를 함께 적는다
    ★ actual 을 'facet' 이나 'collector' 로 적지 않는다 —
      「전체 집합을 봤다」가 아니기 때문이다.  화면과 감사 기록이 그렇게 말한다
    """
    from contracts import S2_CODE, S4_EXPECTED
    from store.adminops import mark_step_imported

    mark_step_imported(
        conn, S2_CODE, at,
        {"substituted_by": "list",
         "reason": "facet 을 못 받아 목록 관측으로 대신한다 (개정 266)",
         "axes": {a: len(v) for a, v in rep.from_list.items()},
         "note": "전체 집합이 아니다 — 사전은 pending 으로만 들어간다",
         "expected": S4_EXPECTED},
        run_id="list", actual="list")
    # ★ mark_step_imported 는 커밋하지 않는다.  여기서 끝맺지 않으면
    #   CLI 로 돌렸을 때 그 행이 사라진다 (실측 08-16)
    conn.commit()


def build_catalog_dict(conn: sqlite3.Connection, site: str, dict_version: str,
                       at: str) -> int:
    """카탈로그 → dict_model_option (STEP 22).

    같은 코드가 모델마다 다른 옵션이다.  scope=model 이므로 충돌이 아니다.
    금지   이 목록을 그 매물의 장착으로 취급하는 것 (1장 STEP 14.1)
    """
    from store.raw import raw_body as _raw_body

    n = 0
    for (mck, body) in conn.execute(
        "SELECT source_id, body FROM raw_response "
        "WHERE endpoint='catalog' AND status='ok'"
    ):
        for item in json.loads(_raw_body(body)) or []:
            conn.execute(
                "INSERT OR REPLACE INTO dict_model_option"
                "(site,model_catalog_key,option_code,option_name,price_manwon,"
                " description,status,dict_version,first_seen,last_seen)"
                " VALUES (?,?,?,?,?,?,'confirmed',?,?,?)",
                (site, mck, str(item.get("optionCd")), item.get("optionName") or "",
                 item.get("price"), item.get("description"), dict_version, at, at),
            )
            n += 1
    conn.commit()
    return n


if __name__ == "__main__":
    from datetime import datetime, timezone

    db, version = sys.argv[1], sys.argv[2]
    c = sqlite3.connect(db)
    r = build_dict(c, "encar", version, datetime.now(timezone.utc).isoformat())
    for axis, n in sorted(r.seen_counts.items()):
        new = len(r.new_values.get(axis, []))
        print(f"{axis:16} 값 {n:4}  신규 {new}")
    print(f"\npending {r.pending_total}건 — 확정 전에는 판정이 돌지 않는다 (STEP 45)")


def build_late_dict(conn: sqlite3.Connection, site: str,
                    dict_version: str, at: str) -> int:
    """매물 원문이 있어야 채워지는 사전 (STEP 42 · S6a).

    ★ S3 에서 못 한다.  S3 은 S1·S2 뒤라 detail 원문이 아직 없다 —
      거기서 뽑으면 사전이 비고, halt 축이라 S9 가 통째로 멈춘다
    ★ code 는 식별자다.  원문이 이름을 주지 않으므로 display 도 코드다 —
      사람이 뜻을 붙인다 (V4-20)
    """
    n = 0
    # ★ options.etc 는 코드가 아니라 딜러 자유 입력이다 — 사전에 넣지 않는다.
    #   실측 08-17: 「타이어는 소모품으로 …」 「완전무사고 신차급차량 저렴한운용리스」
    #   같은 광고 문구 176건이 옵션 코드 사전에 들어와 V4-20 이 잡았다.
    #   이름·가격은 catalog(dict_model_option 1,474행)가 준다
    for path in ("options.standard[]", "options.choice[]",
                 "options.tuning[]"):
        for value, cnt in extract_distinct(conn, "detail", path):
            if upsert_option3(conn, site, "*", value, value, cnt,
                              dict_version, at) == "new":
                n += 1
    # ★ 부위명은 점검부에 있다.  S3 은 inspection 원문 전이라 비어 있었다
    for axis, _scope, endpoint, path in AXIS_SOURCES:
        if axis == "option3" or axis not in LATE_AXES:
            continue
        for value, cnt in extract_distinct(conn, endpoint, path):
            if upsert_enum(conn, site, axis, value, value, cnt,
                           endpoint, dict_version, at) == "new":
                n += 1
    return n
