# -*- coding: utf-8 -*-
"""실행 메뉴.

지시서   13장 STEP 126 (부트스트랩) · 5장 STEP 47 (단계)
근거     ★ 배치 파일에 한글을 넣지 않는다.
         .bat 은 콘솔 코드페이지가 아니라 OEM 코드페이지로 파싱된다.
         chcp 65001 은 출력만 바꾸므로 파일 안의 한글은 여전히 깨진다.
         → 문구는 전부 여기(Python)에 둔다.  run.bat 은 ASCII 만 갖는다
사용     python tools/menu.py
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

PY = sys.executable
CONSOLE_UTF8 = 65001   # Windows 콘솔 코드페이지 (형식)
RULE_WIDTH = 60        # 화면 구분선 폭 (형식)
SPEC = "개발지시서.md"
ALL_CHAPTERS = "0,1,2,3,4,5,6,7,8,9,10,11,12,13"


def _fix_console() -> None:
    """Windows 콘솔을 UTF-8 로 맞춘다.  깨지면 여기만 보면 된다."""
    if os.name != "nt":
        return
    try:
        subprocess.run(f"chcp {CONSOLE_UTF8}", shell=True,
                       capture_output=True)
    except OSError:
        pass
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def run(args: list[str], env_extra: dict | None = None) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUNBUFFERED"] = "1"
    env.update(env_extra or {})
    return subprocess.run([PY, *args], cwd=ROOT, env=env).returncode


def cmd_status() -> int:
    return run(["tools/setup_check.py"])


def cmd_setup() -> int:
    from store.pii import make_key

    print("\n== HMAC 키 ==")
    print("   없을 때만 만듭니다. 덮어쓰지 않습니다 —")
    print("   덮어쓰면 기존 plate_hash 가 전부 무효가 됩니다.")
    print(f"   키: {make_key(os.path.join(ROOT, 'secrets', 'plate_hmac.key'))}")

    print("\n== 관리자 계정 ==")
    name = input("   이름 (비우면 건너뜀): ").strip()
    if not name:
        return 0
    rc = run(["run.py", "admin", "create", "--name", name])
    if rc == 0:
        print("\n   ★ 임시 비밀번호는 한 번만 표시됩니다. 지금 적어두십시오.")
    return rc


def cmd_dry(passthru: list[str] | None = None) -> int:
    return run(["run.py", "collect", "--dry", *(passthru or [])])


FULL_RUN_REQUESTS = 31100   # 전 차종 대략치 (실측 7,775건 × 4)


def cmd_collect(passthru: list[str] | None = None) -> int:
    passthru = list(passthru or [])
    if not any(a == "--target" for a in passthru):
        # ★ 전 차종은 수 시간이고 되돌릴 수 없다.  한 번 더 묻는다
        print(f"\n★ 범위를 주지 않았습니다 — 전 차종입니다 "
              f"(약 {FULL_RUN_REQUESTS:,}요청 · 수 시간)")
        print("   한 차종만 하려면:  run.bat collect --target KOLEOS_HEV")
        if input("   전 차종을 진행하려면 'all' 을 입력: ").strip() != "all":
            print("   취소했습니다.")
            return 0
    print("\n== 수집 시작 ==")
    print("   첫 실행은 S6a 뒤 V4-11 로 멈춥니다. 설계대로입니다.")
    print("   config/field_usage.suggested.json 과 중단 리포트를 확인하십시오.\n")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M")
    log = os.path.join(ROOT, f"collect_{stamp}.log")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    # ★ 파이프로 받으면 자식의 stdout 이 블록 버퍼가 된다.
    #   진행 표시가 몇 분씩 안 나와 「멈춘 것처럼」 보인다
    env["PYTHONUNBUFFERED"] = "1"
    # ★ 인자를 해석하지 않는다.  run.py 가 정본이다 (V1-13).
    #   여기서 파싱하면 새 인자가 생길 때마다 조용히 사라진다 — 세 번 겪었다
    argv = [PY, "run.py", "collect", *passthru]
    proc = subprocess.Popen(
        argv, cwd=ROOT, env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding="utf-8", errors="replace", bufsize=1)
    with open(log, "w", encoding="utf-8") as f:
        for line in proc.stdout:
            sys.stdout.write(line)
            f.write(line)
    proc.wait()
    print(f"\n   기록: {os.path.basename(log)}")
    print("   이 파일을 그대로 보내주시면 됩니다.")
    return proc.returncode


def cmd_facet() -> int:
    """facet 원문에 실제로 어떤 축이 왔는지 본다 (STEP 25a)."""
    return run(["tools/inspect_facet.py"])


def cmd_dict() -> int:
    """사전 검토 — pending 값 확인·확정 (STEP 45)."""
    return run(["tools/inspect_dict.py", *sys.argv[2:]])


def cmd_screens() -> int:
    """화면 ↔ 시안 대조 (ref/screens 가 정본)."""
    return run(["tools/check_screens.py", *sys.argv[2:]])


def cmd_migrate() -> int:
    """스키마 이행 — DDL 변경을 기존 DB 에 반영 (STEP 31a)."""
    return run(["tools/migrate.py", *sys.argv[2:]])


def cmd_checkall() -> int:
    """실측 DB 로 V1~V5 · V10 전건 (개선요청 4-1)."""
    return run(["tools/check_all.py", *sys.argv[2:]])


def cmd_requests() -> int:
    """보낸 요청과 응답 코드를 본다 (STEP 25a)."""
    return run(["tools/inspect_requests.py",
                *(sys.argv[2:3] if len(sys.argv) > 2
                  and not sys.argv[2].startswith("-") else [])])


def cmd_check_spec() -> int:
    return run(["tools/check_spec.py", SPEC])


def cmd_check_src() -> int:
    return run(["tools/check_src.py", SPEC, "."],
               {"CW_CHAPTERS": ALL_CHAPTERS})


def cmd_test() -> int:
    return run(["tools/run_tests.py"])


MENU = (
    ("1", "초기 설정", "HMAC 키 생성 + 관리자 계정", cmd_setup),
    ("2", "조립 확인", "요청 없이 q 쿼리만 본다  (--dry)", cmd_dry),
    ("3", "수집 실행", "S0 ~ S11  (전 차종)", cmd_collect),
    ("3t", "범위 수집", "차종 하나만  (첫 실행 권장)", None),
    ("4", "문서 검사", "check_spec  11종", cmd_check_spec),
    ("5", "소스 검사", "check_src   15종", cmd_check_src),
    ("6", "시험 실행", "14종", cmd_test),
    ("7", "상태 보기", "", cmd_status),
    ("8", "facet 점검", "받은 축을 원문에서 본다 (S2 중단 시)", cmd_facet),
    ("9", "요청 점검", "보낸 URL 과 응답 코드 (전량 404 시)", cmd_requests),
    ("10", "사전 검토", "pending 값 확인·확정 (S9 중단 시)", cmd_dict),
    ("11", "전체 검사", "실측 DB 로 V1~V5 · V10 전건", cmd_checkall),
    ("12", "진단 실행", "결함을 한 번에 모은다 (재수집 없음)", None),
    ("13", "스키마 이행", "DDL 변경을 기존 DB 에 반영", cmd_migrate),
    ("14", "화면 대조", "시안과 다른 곳을 낸다", cmd_screens),
)
GROUP_BREAKS = ("3", "6")   # 메뉴 묶음 구분 위치
DIRECT = {"setup": cmd_setup, "dry": cmd_dry, "collect": cmd_collect,
          "spec": cmd_check_spec, "src": cmd_check_src, "test": cmd_test,
          "status": cmd_status, "facet": cmd_facet, "req": cmd_requests, "dict": cmd_dict,
          "checkall": cmd_checkall, "migrate": cmd_migrate,
          "screens": cmd_screens}

# 자기 인자를 직접 읽는 명령 (sys.argv[2:] 를 그대로 쓴다)
ARG_COMMANDS = (cmd_checkall, cmd_migrate, cmd_dict, cmd_requests,
                cmd_facet, cmd_screens)


def main() -> int:
    _fix_console()
    if len(sys.argv) > 1:
        fn = DIRECT.get(sys.argv[1])
        if fn is None:
            print("사용: run.bat [setup|dry|collect|spec|src|test|status|facet|req|dict|checkall|migrate|screens]"
                  "  [--target <차종>]")
            return 2
        # ★ 껍데기는 인자를 해석하지 않는다.  그대로 넘긴다 (V1-13).
        #   인자를 받는 명령을 명시한다 — 「안 받는 것」을 세면
        #   새 명령이 생길 때마다 조용히 막힌다 (checkall 이 그랬다)
        rest = sys.argv[2:]
        if fn in (cmd_collect, cmd_dry):
            return fn(rest)
        if fn in ARG_COMMANDS:
            return fn()          # sys.argv[2:] 를 각자 읽는다
        if rest:
            print(f"[X] {sys.argv[1]} 은 인자를 받지 않는다: {rest}")
            return 2
        return fn()

    while True:
        print("\n" + "=" * RULE_WIDTH)
        print("  CarWatch v2")
        print("=" * RULE_WIDTH)
        cmd_status()
        print()
        for key, title, note, _fn in MENU:
            print(f"  [{key}] {title:10} {note}")
            if key in GROUP_BREAKS:
                print()
        print("  [0] 종료")
        print("=" * RULE_WIDTH)
        try:
            sel = input("  선택: ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
        if sel == "0":
            return 0
        if sel == "12":
            name = input("  차종 (비우면 전체): ").strip()
            argv = ["--diagnose"] + (["--target", name] if name else [])
            cmd_collect(argv)
            input("\n  엔터를 누르면 메뉴로 돌아갑니다 ")
            continue
        if sel == "3t":
            name = input("  차종 (예: KOLEOS_HEV): ").strip()
            if name:
                cmd_collect(["--target", name])
            input("\n  엔터를 누르면 메뉴로 돌아갑니다 ")
            continue
        for key, _t, _n, fn in MENU:
            if sel == key and fn is not None:
                try:
                    fn()
                except Exception as e:  # 메뉴가 죽지 않게 한다
                    print(f"\n[X] 실패: {e}")
                input("\n  엔터를 누르면 메뉴로 돌아갑니다 ")
                break


if __name__ == "__main__":
    sys.exit(main())
