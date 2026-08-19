# -*- coding: utf-8 -*-
"""시험용 씨앗 DB — 운영 DB 를 복사하지 않는다.

지시서   0장 「시험은 격리된 상태에서 돈다」 (개정 246) · 부록 E `S24`
근거     ★ 운영 DB 를 복사하면 거기 남은 상태가 시험 결과를 바꾼다.
         실측 08-16 — `queued` 인 recalc_job 1건 때문에 관리 화면이 409 로
         잠기고 test_spec_ui 가 9건 무더기로 실패했다.  코드는 안 바뀌었다
필수     같은 코드면 언제 돌려도 같은 결과가 나온다
금지     shutil.copy(ROOT/carwatch.db, ...)
사용     from tests.seed import build_seed_db
         build_seed_db(db_path, root)
"""
from __future__ import annotations

import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

from adapters.encar import EncarAdapter          # noqa: E402
from collect.pipeline import run_pipeline        # noqa: E402
from collect.runner import (                     # noqa: E402
    load_targets, make_executors, make_registry_executor,
    make_score_executors, make_validate_executor,
)
from contracts import RunContext                 # noqa: E402
from store.raw import open_db                    # noqa: E402

# 씨앗에 넣을 매물 수.  ★ 화면 시험이 「분포」를 보므로 1~2건으로는 모자란다
SEED_LISTINGS = 12

# 씨앗 매물 ID 대역.  ★ 0·1·2 는 다른 시험이 쓰는 탐색 URL 과 겹친다
SEED_ID_BASE = 900000

# 판정까지 끝난 DB 를 만드는 단계.  S11 은 시험이 스스로 돌린다
SEED_STEPS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
              "S7", "S8", "S8.5", "S9", "S10")


def _cfg(root: str, name: str) -> dict:
    with open(os.path.join(root, "config", name), encoding="utf-8") as f:
        return json.load(f)


def build_seed_db(dest: str, root: str = ROOT,
                  total: int = SEED_LISTINGS) -> str:
    """스텁 응답으로 S0~S10 을 돌려 판정까지 끝난 DB 를 만든다.

    ★ 네트워크를 부르지 않는다.  StubEncar 가 전 엔드포인트를 대신한다
    ★ 씨앗은 결정적이다 — rng 씨앗과 시각을 고정한다
    반환   dest (같은 경로)
    """
    from test_run import Clock, StubEncar

    cfg = dict(_cfg(root, "endpoints.json")["encar"])
    cfg["interval_sec"] = [0.0, 0.0]      # 시험에서는 대기하지 않는다
    targets = load_targets(os.path.join(root, "config", "targets.json"))
    # ★ 한 collect_group 만 쓴다.  스텁이 G80 을 낸다
    targets = {k: v for k, v in targets.items()
               if v.get("collect_group") == "encar:G80"}
    _ensure_secrets(root)
    adapter = EncarAdapter(cfg)
    # ★ DDL 은 소스다 — 사본 root 가 아니라 저장소에서 읽는다.
    #   config 만 사본에서 읽는다 (시험이 config 를 바꿔 보기 때문이다)
    conn = open_db(dest, os.path.join(ROOT, "sql", "ddl"))
    ctx = RunContext("seed", "encar", Clock().now(), "p1", "d1", "c1",
                     "h", "h", "h", [])
    ex = make_executors(adapter, StubEncar(total, id_base=SEED_ID_BASE),
                        Clock(), cfg, targets,
                        rng=random.Random(1), root_dir=root)
    ex.update(make_score_executors(root, Clock(), targets,
                                   _cfg(root, "scoring.json"),
                                   _cfg(root, "depreciation.json")))
    ex.update(make_registry_executor(root, Clock(),
                                     _cfg(root, "field_usage.json")))
    ex.update(make_validate_executor(_cfg(root, "scoring.json"),
                                     _cfg(root, "depreciation.json"),
                                     target_keys=tuple(targets)))
    reps = run_pipeline(conn, ctx, ex, steps=SEED_STEPS)
    halted = [f"{r.step}: {r.halt_reason}" for r in reps if r.halted]
    if halted:
        # ★ 씨앗이 조용히 비면 시험 전체가 「0건이라 통과」가 된다
        raise RuntimeError("씨앗 DB 를 만들지 못했다 — " + " / ".join(halted))
    n = conn.execute("SELECT COUNT(*) FROM result_score").fetchone()[0]
    if not n:
        raise RuntimeError("씨앗 DB 에 판정 결과가 0건이다")
    _seed_unclassified(conn)
    _confirm_dict(conn)
    conn.close()
    return dest


def _confirm_dict(conn) -> None:
    """남은 pending 사전을 확정으로 둔다.

    ★ 씨앗은 「판정까지 끝난 정상 상태」다.  실물에서는 새 값이 pending 으로
      생기고 사람이 확인해 확정한다 (12장 STEP 44) — 그 확인을 마친 상태다
    ★ 0장 불변식 ⑥ 「사전 미분류 0건」이 그 상태를 전제한다
    금지   판정 축의 pending 을 코드가 조용히 확정하는 것 — 여기는 시험 씨앗이다
    """
    conn.execute("UPDATE dict_enum SET status='confirmed' "
                 "WHERE status='pending'")
    conn.commit()


_CACHED: dict = {}


def seed_db_path(root: str = ROOT) -> str:
    """한 프로세스에서 한 번만 만들어 돌려쓴다.

    ★ 씨앗 만들기는 전 단계를 도는 일이다.  시험마다 다시 만들면 느리다
    """
    if "path" not in _CACHED:
        import tempfile

        _CACHED["path"] = build_seed_db(
            os.path.join(tempfile.mkdtemp(), "seed.db"), root)
    return _CACHED["path"]


def _ensure_secrets(root: str) -> None:
    """사본 root 에 HMAC 키가 없으면 저장소 것을 가져온다.

    ★ 키가 다르면 plate_hash 가 전건 불일치한다 (V4-01).  씨앗은 저장소 키를
      그대로 써서 같은 코드면 같은 결과가 나오게 한다
    """
    import shutil

    dest = os.path.join(root, "secrets")
    if os.path.isdir(dest):
        return
    src = os.path.join(ROOT, "secrets")
    if os.path.isdir(src):
        shutil.copytree(src, dest)


def _seed_unclassified(conn) -> None:
    """미분류 경로 1건을 넣는다.

    ★ 스텁 응답이 좁아 전 경로가 분류돼 버린다.  실물은 늘 미분류가 남는다
      (실측 08-16 운영 DB 48건).  없으면 /admin/registry 의 분류 폼이
      아예 안 그려져 「분류 화면이 도는가」를 못 본다
    """
    at = "2026-08-10T00:00:00+00:00"
    # ★★ 씨앗이 만든 경로는 씨앗이 정한다 (S24).
    #   판정을 막는 미분류는 「마스터가 정할 일」이다 — 운영 DB 의 몫이다.
    #   씨앗 DB 에 그것이 남아 있으면 test_endtoend 가 사람의 판단을 기다리며
    #   영영 실패한다.  실측 08-19 — V4-11 16건이 그래서 걸려 있었다
    #   ★ unused_by_policy 다 — in_use 는 core_column 을 요구한다 (V4-07)
    from parse.encar.paths import WHOLE_CONTAINERS, parser_paths

    used = parser_paths()
    rows = conn.execute(
        "SELECT endpoint, json_path FROM meta_field_usage"
        " WHERE usage='unclassified'").fetchall()
    for endpoint, path in rows:
        bare = path.replace("[]", "")
        if bare in used or path.split("[]")[0] in WHOLE_CONTAINERS:
            conn.execute(
                "UPDATE meta_field_usage SET usage='unused_by_policy',"
                " reason=?"
                " WHERE endpoint=? AND json_path=?",
                ("씨앗 자료다 — 판정에 안 쓰기로 정한다 (S24). "
                 "★ 운영에서는 마스터가 정한다", endpoint, path))
    # ★ 판정을 막지 않는 미분류 1건은 남긴다 —
    #   없으면 /admin/registry 의 분류 폼이 아예 안 그려진다
    conn.execute(
        "INSERT OR IGNORE INTO meta_field_usage"
        "(site,endpoint,json_path,core_column,usage,reason,"
        " miss_streak,first_seen,last_seen)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        ("encar", "detail", "seed.unclassified_path", None, "unclassified",
         "씨앗이 넣은 미분류 1건 — 분류 화면을 재려면 대상이 있어야 한다",
         0, at, at))
    conn.commit()


if __name__ == "__main__":
    import tempfile

    path = build_seed_db(os.path.join(tempfile.mkdtemp(), "seed.db"))
    import sqlite3

    c = sqlite3.connect(path)
    for q in ("SELECT COUNT(*) FROM core_listing",
              "SELECT COUNT(*) FROM result_score",
              "SELECT COUNT(*) FROM result_axis",
              "SELECT COUNT(*) FROM raw_response",
              "SELECT COUNT(*) FROM dict_enum"):
        print(f"{q:45} {c.execute(q).fetchone()[0]}")
    print("등급:", c.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY grade").fetchall())
    print(path)
