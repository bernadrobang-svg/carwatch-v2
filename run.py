# -*- coding: utf-8 -*-
"""CarWatch v2 진입점.

지시서   5장 STEP 47 (단계) · STEP 49 (실행 순서) · STEP 53 (산출 보고)
사용     python3 run.py collect        S0~S11
         python3 run.py collect --target KOLEOS_HEV   범위 제한 (여러 번 가능)
         python3 run.py collect --diagnose            결함을 한 번에 모은다 (재수집 없음)
         python3 run.py collect --only S11            단계 하나만
         python3 run.py collect --resume              끊긴 실행을 이어서 (STEP 52)
         python3 run.py web                          화면 (127.0.0.1:8765)
         python3 run.py admin create --name <이름>   최초 관리자 (STEP 126)
         python3 run.py setup                        HMAC 키 + 최초 관리자
         python3 run.py dry                          run.py collect --dry 와 같다
         python3 run.py migrate                      DDL 변경을 기존 DB 에 반영
         python3 run.py export --format csv          매물 · 판정 · 축별 근거
         python3 run.py report                       L1~L3 리포트 재생성
         python3 run.py collect --dry  요청 없이 조립만 확인
금지     조건 미충족을 경고만 남기고 진행하는 것.  중단하고 보고한다.
"""
from __future__ import annotations

import json
import os
import random
import sys
from datetime import datetime, timezone

from adapters.encar import EncarAdapter
from collect.fetcher import SystemClock, UrlFetcher
from errors import PolicyError  # noqa: E402
from collect.pipeline import (
    completed_steps, diagnose, format_defects,
    build_run_context_fields, print_progress, run_pipeline,
)
from collect.runner import (
    collect_groups, load_targets, make_executors, make_score_executors,
    make_registry_executor, make_validate_executor,
)
from contracts import RunContext
from store.raw import open_db

ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(ROOT, "carwatch.db")
BACKUP_PATH = os.path.join(ROOT, "carwatch.backup.db")

PARSE_VERSION = "p1"
DICT_VERSION = "d1"
CALC_VERSION = "c1"


def load(name: str) -> dict:
    with open(os.path.join(ROOT, "config", name), encoding="utf-8") as f:
        return json.load(f)


def make_context(site: str) -> RunContext:
    now = datetime.now(timezone.utc)
    return RunContext(
        run_id=now.strftime("%Y%m%dT%H%M%S"),
        site=site,
        started_at=now,
        parse_version=PARSE_VERSION,
        dict_version=DICT_VERSION,
        calc_version=CALC_VERSION,
        targets=[],
        **build_run_context_fields(os.path.join(ROOT, "config")),
    )


def _filter_targets(targets: dict, only: list[str]) -> dict:
    """★ targets.json 을 편집하지 않는다.  인자로 범위를 준다.

    파일을 고치면 되돌리는 것을 잊어 전 차종 수집이 조용히 빠진다.
    """
    if not only:
        return targets
    unknown = sorted(set(only) - set(targets))
    if unknown:
        raise PolicyError(
            f"targets.json 에 없는 차종: {unknown}. "
            f"가능: {sorted(targets)}", step="STEP 22")
    return {k: v for k, v in targets.items() if k in only}


ALL_STEPS = ("S0", "S1", "S2", "S3", "S4", "S5", "S6", "S6a",
             "S7", "S8", "S8.5", "S9", "S10", "S11")


def _steps_from(name: str | None) -> tuple[str, ...]:
    """★ 이어서 돈다.  수집이 끝났으면 다시 요청하지 않는다.

    사용   --from S9    S9 부터 끝까지
          --only S11   S11 만
    """
    if name is None:
        return ALL_STEPS
    if name not in ALL_STEPS:
        raise PolicyError(f"없는 단계: {name}. 가능: {list(ALL_STEPS)}",
                          step="STEP 47")
    return ALL_STEPS[ALL_STEPS.index(name):]


def cmd_collect(dry: bool, only: list[str] | None = None,
                from_step: str | None = None,
                only_step: str | None = None,
                diagnose_mode: bool = False,
                refetch: bool = False, resume: bool = False) -> int:
    cfg = load("endpoints.json")["encar"]
    targets = _filter_targets(
        load_targets(os.path.join(ROOT, "config", "targets.json")), only or [])
    if only:
        print(f"★ 범위 제한: {', '.join(only)}  (targets.json 은 그대로다)")
    adapter = EncarAdapter(cfg)
    groups = collect_groups(targets, adapter.site_code)

    print(f"차종 {len(targets)}종 · collect_group {len(groups)}개")
    for g in groups:
        print(f"  {g.group_key:20} {'·'.join(g.target_keys)}")
        print(f"    q = {adapter.build_q(g.site_query)}")
    if dry:
        print("\n--dry: 요청하지 않았다")
        return 0

    conn = open_db(DB_PATH, os.path.join(ROOT, "sql", "ddl"))
    ctx = make_context(adapter.site_code)
    ex = make_executors(adapter, UrlFetcher(), SystemClock(), cfg, targets,
                        backup_path=BACKUP_PATH, rng=random.Random(),
                        root_dir=ROOT, progress=print_progress, resume=resume)
    ex.update(make_score_executors(ROOT, SystemClock(), targets,
                                   load("scoring.json"),
                                   load("depreciation.json")))
    ex.update(make_registry_executor(ROOT, SystemClock(),
                                     load("field_usage.json")))
    ex.update(make_validate_executor(load("scoring.json"),
                                     load("depreciation.json"),
                                     target_keys=tuple(targets)))
    if resume:
        print("★ 재개 — 이미 답을 받은 요청은 다시 던지지 않는다 (STEP 52)")

    print(f"\nrun_id {ctx.run_id}")
    print("진행 — 단계 · 건수 · 대상\n")
    if diagnose_mode:
        # ★ 진단은 읽기다.  판정 결과를 남기지 않는다 (STEP 50b)
        print("\n★ 진단 모드 — 결함을 한 번에 모은다.  재수집하지 않는다")
        rep = diagnose(conn, ctx, ex, steps=_steps_from(from_step),
                       progress=print_progress, refetch=refetch)
        print()
        print(format_defects(rep))
        return 1 if any(d.severity == "fatal" for d in rep.defects) else 0

    steps = (only_step,) if only_step else _steps_from(from_step)
    if only_step and only_step not in ALL_STEPS:
        raise PolicyError(f"없는 단계: {only_step}", step="STEP 47")
    if steps != ALL_STEPS:
        print(f"★ 단계 제한: {' → '.join(steps)}  (앞 단계는 지난 실행 결과를 쓴다)")
    reports = run_pipeline(conn, ctx, ex, progress=print_progress, steps=steps,
                           done=completed_steps(conn))

    print("\n\n단계        expected requested   ok empty n/f error 거부  상태")
    for r in reports:
        mark = "중단" if r.halted else "정상"
        print(f"{r.step:10} {r.expected:8} {r.requested:9} {r.ok:4} {r.empty:5}"
              f" {r.not_found:3} {r.error:5} {r.rejected:4}  {mark}")
        if r.halted:
            print(f"           ↳ {r.halt_reason}")
    if not any(r.halted for r in reports):
        _grade_summary(conn)
    return 1 if any(r.halted for r in reports) else 0


def _grade_summary(conn) -> None:
    print("\n등급 분포")
    for g, n in conn.execute(
        "SELECT grade, COUNT(*) FROM result_score GROUP BY grade "
        "ORDER BY COUNT(*) DESC"
    ):
        print(f"  {g:10} {n}")
    print("\n축별 excluded 비율 (분모에서 빠진 것)")
    for axis, ex, tot in conn.execute(
        "SELECT axis, SUM(excluded), COUNT(*) FROM result_axis "
        "GROUP BY axis ORDER BY axis"
    ):
        print(f"  {axis:32} {ex}/{tot}")


def cmd_admin_create(name: str) -> int:
    """최초 관리자.  ★ 웹에서 만들지 않는다 — 누구나 관리자가 된다 (STEP 126)."""
    from datetime import datetime, timezone

    from contracts import ROLE_ADMIN
    from store.admin import account_count, create_account

    conn = open_db(DB_PATH, os.path.join(ROOT, "sql", "ddl"))
    role = ROLE_ADMIN if account_count(conn) == 0 else ROLE_ADMIN
    aid, temp = create_account(conn, name, role,
                               datetime.now(timezone.utc).isoformat())
    print(f"account_id {aid} · {name}")
    print(f"임시 비밀번호  {temp}")
    print("★ 한 번만 표시된다.  저장되지 않는다.  첫 로그인 시 변경을 강제한다")
    return 0


def _collect_urls(target_key: str | None = None) -> list[dict]:
    """브라우저가 부를 주소를 만든다 (13장 STEP 136c · 264).

    ★ 어댑터가 q 를 조립한다.  web 은 adapters 를 못 부른다 (STEP 15a).
      화면이 URL 을 손으로 만들면 수집분과 다른 조건이 된다
    ★ 목록은 쪽수를 미리 모른다 — Count 를 받아야 안다.
      그래서 {offset} 자리를 남긴 틀을 준다.  JS 가 이어서 부른다
    반환   [{'kind','target_key','targets','label','url','url_template','rows'}]
    """
    cfg = load("endpoints.json")["encar"]
    web = load("web.json")
    rows = int(web["browser_collect_rows"])
    adapter = EncarAdapter(cfg)
    targets = load_targets(os.path.join(ROOT, "config", "targets.json"))
    out = []
    # ★ 수집 단위는 collect_group 이다.  facet 은 그 단위로만 존재한다
    #   (2장 STEP 23 · 「G80_EV 의 facet」은 없다)
    for group in collect_groups(targets, adapter.site_code):
        if target_key and target_key not in group.target_keys:
            continue
        spec = group.as_target_spec()
        keys = " · ".join(group.target_keys)
        # ★ facet 을 먼저 둔다.  facet 이 없으면 S2 가 안 열려 그 뒤가 전부
        #   막힌다 — 목록을 아무리 받아도 소용없다 (실측 08-16 · V4-25)
        for req in adapter.facet_urls(spec):
            out.append({"kind": "facet", "target_key": group.target_keys[0],
                        "targets": keys, "label": f"{keys} facet",
                        "url": req.url, "url_template": req.url,
                        "rows": rows})
        out.append({"kind": "list", "target_key": group.target_keys[0],
                    "targets": keys, "label": f"{keys} 목록",
                    "url": _page_url(adapter, spec, 0, rows),
                    "url_template": _page_url(adapter, spec, None, rows),
                    "rows": rows})
    return out


def _page_url(adapter, spec, offset: int | None, rows: int) -> str:
    """목록 한 쪽의 주소.  offset 이 None 이면 {offset} 자리를 남긴다.

    ★ 문자열을 손으로 조립하지 않는다.  어댑터가 만든 것에서 sr 의
      |offset|limit 자리만 바꿔 끼운다 (STEP 136c · 개정 263)
    """
    url = adapter.list_url(spec, 0).url
    head, sep, tail = url.partition("%7C0%7C")     # sr=|MobileModifiedDate|0|limit
    if not sep:
        return url
    parts = tail.split("&", 1)
    rest = "&" + parts[1] if len(parts) > 1 else ""
    at = "{offset}" if offset is None else str(offset)
    # ★ 건수도 자리로 남긴다.  바이트가 상한을 넘으면 JS 가 건수를 줄여
    #   같은 자리를 다시 부른다 — 건수로 나누면 바이트가 안 묶인다 (실측 08-16)
    lim = "{rows}" if offset is None else str(rows)
    return head + "%7C" + at + "%7C" + lim + rest


def cmd_web(host: str | None, port: str | None) -> int:
    """화면을 띄운다 (14장 STEP 141).  ★ 기본은 127.0.0.1 이다."""
    from web.app import make_app
    from web.server import serve

    # ★ 재처리 결정표를 주입한다.  web 은 collect 를 모른다 (STEP 15a)
    from collect.pipeline import (
        REPROCESS_TABLE, check_recalc_origin, from_step_for, web_reasons,
    )

    def plan(reason, origin):
        check_recalc_origin(reason, origin)
        return from_step_for(reason)

    rows = [{"key": r, "label": r,
             "from_step": REPROCESS_TABLE[r].steps[0]
             if REPROCESS_TABLE[r].steps else "—"} for r in web_reasons()]
    from collect.pipeline import resume_point

    app = make_app(DB_PATH, ROOT, plan=plan, reason_rows=rows,
                   fetch=_api_fetch, resume=resume_point,
                   collect_urls=_collect_urls)
    # ★ 큐를 가져가는 소비기를 함께 띄운다 (STEP 132a · 개정 261).
    #   넣기만 하고 아무도 안 가져가면 화면이 거짓말을 하게 된다
    from collect.worker import start as start_worker

    start_worker(DB_PATH, make_worker_ctx, make_worker_executors, ROOT)
    print("큐 소비기 시작 — /admin/run 에서 진행을 봅니다")
    return serve(app, host, int(port) if port else None, ROOT)


def make_worker_ctx():
    """소비기가 쓸 실행 맥락.  ★ 실행마다 새 run_id 다."""
    cfg = load("endpoints.json")["encar"]
    return make_context(EncarAdapter(cfg).site_code)


def make_worker_executors():
    """소비기가 쓸 단계 실행기.  ★ CLI 와 같은 것을 쓴다 —
    화면으로 돌린 것과 터미널로 돌린 것이 다르면 안 된다 (B-6)."""
    cfg = load("endpoints.json")["encar"]
    targets = load_targets(os.path.join(ROOT, "config", "targets.json"))
    adapter = EncarAdapter(cfg)
    ex = make_executors(adapter, UrlFetcher(), SystemClock(), cfg, targets,
                        backup_path=BACKUP_PATH, rng=random.Random(),
                        root_dir=ROOT, progress=print_progress)
    ex.update(make_score_executors(ROOT, SystemClock(), targets,
                                   load("scoring.json"),
                                   load("depreciation.json")))
    ex.update(make_registry_executor(ROOT, SystemClock(),
                                     load("field_usage.json")))
    ex.update(make_validate_executor(load("scoring.json"),
                                     load("depreciation.json"),
                                     target_keys=tuple(targets)))
    return ex


# 도구로 넘기는 명령 (B-6 · V1-13).
# ★ 껍데기와 직접 실행의 인자가 같아야 한다.
#   run.py 는 되고 menu.py 는 안 되면 문서를 어느 쪽으로도 못 쓴다
DELEGATED = {
    "migrate": "tools/migrate.py",
    "export": "tools/export_cli.py",
    "report": "tools/report_cli.py",
}


def cmd_delegate(name: str, rest: list) -> int:
    """★ 인자를 그대로 넘긴다.  중간에서 걸러내면 두 경로가 갈린다."""
    import subprocess

    script = os.path.join(ROOT, DELEGATED[name])
    if not os.path.isfile(script):
        print(f"[X] {DELEGATED[name]} 가 없다")
        return 2
    return subprocess.run([sys.executable, script, *rest], cwd=ROOT).returncode


def _api_fetch(url: str):
    """API 조회 화면이 쓰는 조회기 (STEP 134).

    ★ web 계층이 네트워크를 직접 부르지 않는다.  여기서 주입한다 (STEP 15a)
    ★ 응답을 가공하지 않는다 — 원문 그대로 넘긴다
    """
    res = UrlFetcher().get(url, {"User-Agent": "CarWatch/2"})
    return res.http_code, res.content_type, res.body_text


def cmd_setup() -> int:
    """HMAC 키 + 최초 관리자 (STEP 35 · 126).

    ★ 키는 없을 때만 만든다.  덮어쓰면 기존 plate_hash 가 전부 무효가 된다
    """
    from store.pii import make_key

    print("\n== HMAC 키 ==")
    print("   없을 때만 만듭니다. 덮어쓰지 않습니다 —")
    print("   덮어쓰면 기존 plate_hash 가 전부 무효가 됩니다.")
    path = os.path.join(ROOT, "secrets", "plate_hmac.key")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"   키: {make_key(path)}")

    print("\n== 관리자 계정 ==")
    name = input("   이름 (비우면 건너뜀): ").strip()
    return cmd_admin_create(name) if name else 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["setup"]:
        sys.exit(cmd_setup())
    if args[:1] == ["dry"]:
        # ★ 껍데기와 같은 뜻이어야 한다 (V1-13).  별명이지 다른 명령이 아니다
        args = ["collect", "--dry", *args[1:]]
    if args[:1] and args[0] in DELEGATED:
        sys.exit(cmd_delegate(args[0], args[1:]))
    if args[:1] == ["web"]:
        def _o(name):
            return (args[args.index(name) + 1]
                    if name in args and args.index(name) + 1 < len(args)
                    else None)

        sys.exit(cmd_web(_o("--host"), _o("--port")))
    if args[:2] == ["admin", "create"]:
        idx = args.index("--name") + 1 if "--name" in args else -1
        if idx <= 0 or idx >= len(args):
            print("python run.py admin create --name <이름>")
            sys.exit(2)
        sys.exit(cmd_admin_create(args[idx]))
    if not args or args[0] != "collect":
        print(__doc__)
        sys.exit(2)
    only = [args[i + 1] for i, a in enumerate(args)
            if a == "--target" and i + 1 < len(args)]

    def opt(name):
        return (args[args.index(name) + 1]
                if name in args and args.index(name) + 1 < len(args) else None)

    try:
        sys.exit(cmd_collect("--dry" in args, only, opt("--from"),
                             opt("--only"), "--diagnose" in args,
                             "--refetch" in args, "--resume" in args))
    except PolicyError as e:
        print(f"[X] {e}")
        sys.exit(2)
