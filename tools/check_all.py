# -*- coding: utf-8 -*-
"""실측 DB 회귀 — V1~V5 · V10 전건을 한 번에 돌린다.

지시서   개선요청 4-1 (실측 DB 회귀)
근거     ★ 실패 1건 고치고 「다시 돌려보십시오」 금지.
         전 검사를 돌려 남은 것을 한 번에 낸다.
         모의 응답 시험만으로는 마스터 실행이 개발측 시험을 대신하게 된다
사용     python tools/check_all.py [carwatch.db] [--target KOLEOS_HEV]
"""
from __future__ import annotations

import io
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from validate.base import PHASE_ORDER, run_phase, save_results  # noqa: E402
from validate.v0_guide import PHASE as PHASE_GUIDE  # noqa: E402
from validate.v0_guide import results as guide_results  # noqa: E402

# ★ 환경에 따라 갈리는 검사.  결함이 아니라 차이다 (개선요청 4-2)
ENV_DEPENDENT = {
    "V4-01": "HMAC 키가 다르면 plate_hash 가 전건 불일치한다",
    "V1-05": "실행 시작 시각 기준이라 DB 만으로는 재현되지 않는다",
}
WIDTH = 52


def _first_fetch(conn) -> datetime:
    row = conn.execute(
        "SELECT MIN(fetched_at) FROM raw_response").fetchone()
    if row and row[0]:
        try:
            return datetime.fromisoformat(row[0])
        except ValueError:
            pass
    return datetime.now(timezone.utc)


def _now() -> str:
    """★ 남기는 시각.  ★ UTC 로 적는다 (DTZ005 — naive 를 안 쓴다)."""
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    args = sys.argv[1:]
    db = next((a for a in args if a.endswith(".db")),
              os.path.join(ROOT, "carwatch.db"))
    targets = tuple(args[i + 1] for i, a in enumerate(args)
                    if a == "--target" and i + 1 < len(args))
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 2
    conn = sqlite3.connect(db)

    class Ctx:
        run_id = (conn.execute("SELECT run_id FROM audit_request "
                               "ORDER BY rowid DESC LIMIT 1").fetchone()
                  or ("-",))[0]
        policy_raw = json.load(io.open(os.path.join(ROOT, "config",
                                                    "scoring.json"),
                                       encoding="utf-8"))
        depreciation = json.load(io.open(os.path.join(ROOT, "config",
                                                      "depreciation.json"),
                                         encoding="utf-8"))
        target_keys = targets
        # ★ 빈 DB 에서도 돈다 (B-5 · V1-18).
        #   수집 전에 검사를 못 돌리면 첫 실행을 시험할 수 없다
        started_at = _first_fetch(conn)

    fatal, warn, env, skip, ok = [], [], [], [], 0
    # ★★★ 08-26 마스터 지시 — 「★ 검사 결과를 ★ `audit_validation` 에 남겨라.
    #   ★ ★ **안 남긴 것이 결함이다**」 (`11-store/c-result.md:149`)
    #   ★★ ★ 실측 08-26 — ★ `validate/v0_guide.py` 의 ★ S43~S46 은
    #     ★ ★ **어느 도구도 안 부르고 있었다** — ★ 손으로 쳐야 돌았다.
    #     ★ ★ 그래서 ★ 색인의 「마지막 통과」가 ★ 늘 「없음」이었다
    #   ★ 여기서 함께 돌린다 — ★ 규칙 3 의 두 도구 안에 들어와야 뜻이 있다
    phases = (PHASE_GUIDE, *PHASE_ORDER)
    for phase in phases:
        try:
            results = (guide_results(Ctx.run_id) if phase == PHASE_GUIDE
                       else run_phase(conn, Ctx(), phase))
            save_results(conn, results, _now())
        except Exception as e:                      # noqa: BLE001
            fatal.append((phase, f"검사가 예외로 죽었다: {type(e).__name__}: {e}"))
            continue
        for r in results:
            if not r.applicable:
                # ★ 이번 실행에서 안 돈 단계.  통과로 세지 않는다 (V1-16)
                skip.append((r.check.code, r.actual))
            elif r.passed:
                ok += 1
            elif r.check.code in ENV_DEPENDENT:
                env.append((r.check.code, ENV_DEPENDENT[r.check.code]))
            elif r.check.severity == "fatal":
                fatal.append((r.check.code, f"{r.check.title} — {r.actual}"))
            else:
                warn.append((r.check.code, f"{r.check.title} — {r.actual}"))

    print(f"DB {os.path.basename(db)} · run {Ctx.run_id}"
          + (f" · 범위 {', '.join(targets)}" if targets else ""))
    print(f"통과 {ok} · fatal {len(fatal)} · warn {len(warn)}"
          f" · 환경 차이 {len(env)} · 미실행 {len(skip)}\n")
    for title, rows in (("■ FATAL — 고쳐야 한다", fatal),
                        ("■ warn — 진행은 된다", warn),
                        ("■ 환경 차이 — 결함이 아니다", env),
                        ("■ 미실행 — 이번 실행에서 그 단계를 안 돌았다", skip)):
        if not rows:
            continue
        print(title)
        for code, detail in rows:
            print(f"  {code:9} {detail[:WIDTH * 2]}")
        print()
    # ★★★★★ 08-30 (마스터 0순위) — ★ **여기가 12GB 가 쌓인 자리다.**
    #   ★ `run_tests` 는 끝에 치웠는데 ★ `check_all` 은 ★ **한 번도 안 치웠다.**
    #   ★ ★ 검사기 넷이 `outputs/check-tmp` 에 쓰고 ★ 내가 하루에 수십 번 돌려
    #   ★ ★ 9,039개 · 12GB 가 됐다 (디스크 30G 중 7.2G 만 남았었다).
    #   ★ 두 도구가 ★ **같은 청소기**를 쓴다 — ★ 한쪽만 고치면 또 샌다
    try:
        from tools.run_tests import _sweep_temp

        swept = _sweep_temp()
        if swept:
            print(f"  임시 DB {swept}개 치움 (검사가 디스크를 채우지 않는다)")
    except Exception as exc:                                   # noqa: BLE001
        # ★ 치우기가 실패해도 ★ 검사 결과를 못 내면 안 된다 — ★ 말하고 넘어간다
        print(f"  ★ 임시 DB 치우기가 실패했다 — {exc}")
    return 1 if fatal else 0


if __name__ == "__main__":
    sys.exit(main())
