# -*- coding: utf-8 -*-
"""마스터 회선으로 받기 (`/fetch`) — ★ 지시 `r1200` L-1 ~ L-9.

★★★ 왜 있나 — ★ 엔카는 ★ **서버 IP 를 막는다**(407).  ★ 목록·성능점검·보험이력이
  ★ 다 막힌다.  ★ 마스터 회선은 열린다 (0.1초에도 200).
★ 그러므로 ★ **서버가 「받아야 할 주소」를 만들고** ·
  ★ **화면이 폰 회선으로 받아 서버에 올린다.**  ★ 주소를 손으로 옮기지 않는다.
★★ 폰에서 ★ **파싱하지 않는다** — ★ 원문 그대로 올린다.  ★ 파싱은 서버가 한다.
★★★ 크기로 가른다 — ★ 작은 안내문은 ★ 상세가 아니다 (가이드 실측 09-06).
"""
from __future__ import annotations

import sqlite3

from report.screens.build import load_config

# ★ 단계는 ★ **차례가 있다** — ★ 앞 단계가 있어야 뒤 단계 주소가 나온다.
#   ★ 이름·설명은 ★ 시안 `v4m_fetch_시안.html` 그대로다
STEPS: tuple = (
    {"no": 1, "kind": "list", "name": "목록",
     "desc": "목록이 있어야 상세 주소가 나옵니다"},
    {"no": 2, "kind": "detail", "name": "상세",
     "desc": "차 정보·옵션·트림·신차가. 상세가 있어야 성능·보험 주소가 나옵니다"},
    {"no": 3, "kind": "inspection", "name": "성능점검",
     "desc": "판금·교환 자리, 용도변경(렌트), 주행거리 계기 상태"},
    {"no": 4, "kind": "record", "name": "보험이력",
     "desc": "사고 금액, 영업용(대여) 이력, 정보제공 불가능기간"},
    {"no": 5, "kind": "catalog", "name": "catalog",
     "desc": "신차가와 옵션 가격. 지금 0.8% 뿐이라 감가율이 안 나옵니다"},
)
# ★ 큐에서 뺄 상태 (L-3) — ★ 「받았다」와 「그 차가 없다」 둘.
#   ★ `error` 는 ★ **안 뺀다** — ★ 407 로 막힌 것이라 ★ 다시 받아야 한다
DONE = ("ok", "not_found")
# ★★★★★ 09-06 (r1204 L-11) — ★ **「전부 받기」를 만들지 않는다.**
#   ★ 마스터 실측 — ★ 성능·보험은 ★ **1분에 2~3건**이다.
#   ★ ★ 9,317건이면 ★ **50시간이 넘는다** — ★ 누를 수 있는 단추로 두면 안 된다
CHUNKS = (10, 30, 100)


def _cfg(root: str = ".") -> dict:
    return (load_config(f"{root}/config/endpoints.json") or {}).get("encar") or {}


def _col(kind: str) -> str:
    return "detail_status" if kind == "list" else f"{kind}_status"


def _has_col(conn, name: str) -> bool:
    return name in {r[1] for r in conn.execute("PRAGMA table_info(core_listing)")}


def step_counts(conn: sqlite3.Connection, site: str = "encar") -> list:
    """단계마다 ★ 「받을 것 N / 전체 M」.

    ★ 큐 크기를 ★ **미리 정하지 않는다** — ★ 그때그때 세어서 낸다 (지시 L).
    """
    total = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE site = ?"
        " AND status IN ('active','new','relisted')", (site,)).fetchone()[0]
    out = []
    for st in STEPS:
        col = _col(st["kind"])
        if st["kind"] == "list":
            # ★ 목록은 ★ 이미 매물이 있으면 받은 것이다
            need = 0
        elif not _has_col(conn, col):
            need = total
        else:
            marks = ",".join("?" * len(DONE))
            need = conn.execute(
                f"SELECT COUNT(*) FROM core_listing WHERE site = ?"
                f" AND status IN ('active','new','relisted')"
                f" AND ({col} IS NULL OR {col} NOT IN ({marks}))",
                (site, *DONE)).fetchone()[0]
        out.append({**st, "need": need, "total": total,
                    "pct": round((total - need) * 100 / total) if total else 0,
                    "done": need == 0})
    return out


def queue(conn: sqlite3.Connection, step: int, n: int = 500,
          site: str = "encar", root: str = ".",
          retry: bool = False) -> dict:
    """★ L-2 — 받을 주소를 ★ JSON 으로 준다.

    ★ L-3 — ★ 이미 받은 것은 뺀다 (`ok`·`not_found`).
    ★ L-7 — ★ `retry` 면 ★ **실패한 것만**(`error`) 준다
    """
    got = next((s for s in STEPS if s["no"] == int(step)), None)
    if got is None or got["kind"] == "list":
        return {"step": step, "kind": None, "rows": [],
                "said": "그 단계는 이 화면이 받지 않습니다"}
    kind, col = got["kind"], _col(got["kind"])
    if not _has_col(conn, col):
        return {"step": step, "kind": kind, "rows": [],
                "said": f"{col} 칸이 없습니다"}
    if retry:
        where, args = f"{col} = 'error'", []
    else:
        marks = ",".join("?" * len(DONE))
        where, args = f"({col} IS NULL OR {col} NOT IN ({marks}))", list(DONE)
    rows = conn.execute(
        "SELECT source_id FROM core_listing WHERE site = ?"
        " AND status IN ('active','new','relisted')"
        f" AND {where} ORDER BY listing_id LIMIT ?",
        (site, *args, int(n))).fetchall()

    # ★★★★★ 09-06 — ★ `adapters/` 를 ★ **안 부른다** (`V4-22` 의존 방향).
    #   ★ 주소는 ★ `config/endpoints.json` 의 ★ `base` ＋ `paths` 가 정본이다 (`S14`)
    cfg = _cfg(root)
    base = str(cfg.get("base_url") or "").rstrip("/")
    path = (cfg.get("paths") or {}).get(kind)
    if not base or not path:
        return {"step": step, "kind": kind, "rows": [],
                "said": f"config/endpoints.json 에 {kind} 주소가 없습니다"}
    out = [{"kind": kind, "source_id": str(sid),
            "url": base + path.format(source_id=str(sid))}
           for (sid,) in rows]
    return {"step": step, "kind": kind, "rows": out, "said": ""}


def one_car(conn: sqlite3.Connection, listing_id: int,
            root: str = ".") -> dict:
    """★ L-12 — ★ **그 차 하나**의 못 받은 창구를 준다 (상세 화면에서 바로 받는 길).

    ★ 마스터께서 ★ 「이 차」를 고르셨을 때 ★ 9,317건을 다 받으실 까닭이 없다.
      ★ ★ 성능점검·보험이력만 ★ 두 번 부르면 된다 — ★ 2분이면 끝난다.
    ★ 이미 받은 창구는 ★ 뺀다.  ★ 없으면 ★ 빈 목록이다 (「다 받았습니다」)
    """
    row = conn.execute(
        "SELECT site, source_id FROM core_listing WHERE listing_id = ?",
        (int(listing_id),)).fetchone()
    if not row or str(row[0]) != "encar":
        return {"rows": [], "said": "엔카 매물만 이 길로 받습니다"}
    site, sid = str(row[0]), str(row[1])
    cfg = _cfg(root)
    base = str(cfg.get("base_url") or "").rstrip("/")
    paths = cfg.get("paths") or {}
    out, done = [], []
    for st in STEPS:
        kind = st["kind"]
        if kind == "list" or kind not in paths:
            continue
        col = _col(kind)
        if not _has_col(conn, col):
            continue
        got = conn.execute(
            f"SELECT {col} FROM core_listing WHERE listing_id = ?",
            (int(listing_id),)).fetchone()
        if got and str(got[0] or "") in DONE:
            done.append(st["name"])
            continue
        out.append({"kind": kind, "name": st["name"], "source_id": sid,
                    "url": base + paths[kind].format(source_id=sid)})
    return {"rows": out, "site": site, "source_id": sid,
            "done": done,
            "said": "" if out else "이 차는 다 받았습니다"}


def put_one(conn: sqlite3.Connection, site: str, kind: str, source_id: str,
            url: str, http_code: int, body: str, root: str = ".") -> dict:
    """★ L-5 — 폰이 받은 ★ **원문 그대로**를 남긴다.  ★ 파싱은 서버가 한다.

    ★ 크기로 가른다 — ★ 200 이라도 ★ 작은 안내문은 상세가 아니다.
      ★ ★ 기준은 `config/endpoints.json` `min_detail_bytes` 다 (없으면 안 잰다)
    """
    from store.rawfile import save

    cut = int(_cfg(root).get("min_detail_bytes") or 0)
    n = len(body or "")
    if http_code == 404:
        status = "not_found"
    elif http_code != 200:
        status = "error"
    elif cut and n < cut:
        # ★ 「없다」가 아니라 ★ **안내문**이다 — ★ `ok` 로 굳히지 않는다
        status = "empty"
    else:
        status = "ok"
    save(site, kind, source_id, url, body or "", http_code=http_code,
         status=status, origin="browser", root=root)
    col = _col(kind)
    if _has_col(conn, col):
        conn.execute(
            f"UPDATE core_listing SET {col} = ? WHERE site = ? AND source_id = ?",
            (status, site, str(source_id)))
        conn.commit()
    return {"status": status, "bytes": n}


def view_fetch(conn: sqlite3.Connection, query: dict | None = None,
               root: str = ".") -> dict:
    """화면에 넘길 값.  ★ 시안 `v4m_fetch_시안.html` 의 이름 그대로."""
    q = query or {}
    site = str(q.get("site") or "encar")
    n = str(q.get("n") or str(CHUNKS[1]))
    steps = step_counts(conn, site)
    # ★★★★★ 09-06 (r1204 L-10) — ★ 「지금 단계」를 ★ **주소가 정할 수 있다.**
    #   ★ 창구마다 ★ 묶음·쉼이 다르므로 (`상세`는 안 쉬고 `성능·보험`은 3건에 60초)
    #   ★ ★ 화면이 ★ **그 단계의 값**을 실어야 한다 — ★ 아니면 안 쉬고 몰아친다
    want = str(q.get("step") or "")
    now = None
    if want.isdigit():
        now = next((s for s in steps if s["no"] == int(want)), None)
    if now is None:
        now = next((s for s in steps if not s["done"]), steps[-1])
    try:
        size = int(n)
    except ValueError:
        size = CHUNKS[1]
    secs = eta_secs(now["kind"], size, root)
    return {
        "steps": steps,
        "site": site,
        # ★ L-11 — ★ 「전부」가 없다.  ★ 끊어서만 받는다
        "chunks": [{"n": str(c), "label": f"{c:,}건", "on": n == str(c)}
                   for c in CHUNKS],
        "n": n,
        "now_no": now["no"], "now_name": now["name"], "now_need": now["need"],
        "go_label": f"{now['no']}단계 {now['name']} {size:,}건 받기 ▸",
        "eta": _say_secs(secs),
        "interval_ms": int(float(
            _cfg(root).get("browser_interval_sec") or 0.1) * 1000),
        # ★ L-10 — ★ 창구마다 ★ 「몇 건 받고 몇 초 쉬나」.  ★ 값은 config 가 준다
        "batch_n": _batch(now["kind"], root)[0],
        "batch_rest_ms": _batch(now["kind"], root)[1] * 1000,
        "batch_said": _batch_said(now["kind"], root),
        "tabs": [{"site": "encar", "label": "엔카", "on": site == "encar"},
                 {"site": "kbchachacha", "label": "KB차차차",
                  "on": site == "kbchachacha"},
                 {"site": "kcar", "label": "K카", "on": site == "kcar"}],
        "last": _last_run(conn),
    }


def _last_run(conn: sqlite3.Connection) -> dict:
    """★ 지난번 결과.  ★ 없으면 ★ 빈 것을 준다 — ★ 0 을 지어내지 않는다."""
    try:
        row = conn.execute(
            "SELECT at, ok, empty, not_found, error, secs FROM fetch_run"
            " ORDER BY run_no DESC LIMIT 1").fetchone()
    except sqlite3.Error:
        return {}
    if not row:
        return {}
    return {"at": row[0], "ok": row[1], "empty": row[2],
            "not_found": row[3], "error": row[4], "secs": row[5]}


def save_last(conn: sqlite3.Connection, got: dict) -> None:
    """★ 한 판의 셈을 남긴다.  ★ 파일이 아니라 표다 (`fetch_run`)."""
    def _n(k):
        try:
            return int(str(got.get(k) or 0) or 0)
        except ValueError:
            return 0

    from datetime import datetime, timezone

    at = datetime.now(timezone.utc).isoformat()[:16].replace("T", " ")
    conn.execute(
        "INSERT INTO fetch_run(at, ok, empty, not_found, error, secs)"
        " VALUES(?,?,?,?,?,?)",
        (at, _n("ok"), _n("empty"), _n("not_found"), _n("error"), _n("secs")))
    conn.commit()


def _batch(kind: str, root: str = ".") -> tuple:
    """★ L-10 — ★ 그 창구는 ★ 몇 건 받고 몇 초 쉬나.

    ★ 실측 09-06 (마스터 회선) — ★ 성능점검·보험이력은 ★ **2~3건에서 잠긴다.**
      ★ ★ 간격을 2.0초로 늘려도 ★ 200 이 **0건**이다 — ★ 느리게 해서 될 일이 아니다.
      ★ ★ ★ 다만 ★ **1분이면 풀린다.**
    ★ 상세는 서버에서도 열리므로 ★ 묶지 않는다 — ★ `(0, 0)` 이면 안 쉰다.
    ★ 값은 ★ `config/endpoints.json` `browser_batch` 가 정본이다 (`S14`)
    """
    got = (_cfg(root).get("browser_batch") or {}).get(kind) or {}
    return int(got.get("n") or 0), int(got.get("rest_sec") or 0)


def _batch_said(kind: str, root: str = ".") -> str:
    n, rest = _batch(kind, root)
    if not n:
        return "쉬지 않고 이어 받습니다"
    return f"{n}건 받고 {rest}초 쉽니다 — 그 창구는 몰아치면 잠깁니다"


def eta_secs(kind: str, size: int, root: str = ".") -> int:
    """★ 걸리는 시간.  ★ 쉬는 시간을 ★ **빼놓지 않는다** — 그러면 거짓말이 된다."""
    gap = float(_cfg(root).get("browser_interval_sec") or 0.1)
    n, rest = _batch(kind, root)
    secs = size * gap
    if n:
        secs += (max(0, size - 1) // n) * rest
    return round(secs)


def _say_secs(secs: int) -> str:
    if secs < 60:
        return f"{secs:,}초"
    if secs < 3600:
        return f"{secs // 60}분 {secs % 60}초"
    return f"{secs // 3600}시간 {(secs % 3600) // 60}분"
