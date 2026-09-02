# -*- coding: utf-8 -*-
"""관리자 — 계정 · 권한 · config 변경 (13장 앞부분).

지시서   STEP 126 (권한 3단 · 부트스트랩) · STEP 127 (config 변경과 이력)
근거     ★ 관리자 화면에서 하는 일은 전부 config 변경 또는 실행 지시다.
         코드를 고치는 일은 여기 없다 — 그런 것은 개발 요청으로 간다 (STEP 137)
금지     화면 숨김만으로 권한을 대신하는 것.  서버가 막아야 한다
         파일을 직접 편집하는 것.  이력이 남지 않는다
         기본 비밀번호를 코드나 config 에 두는 것
         웹에서 최초 계정을 만드는 것 — 누구나 관리자가 될 수 있다
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from contracts import (
    ANONYMOUS, ROLE_ADMIN, ROLE_USER, Account, require_role,
)
from errors import PolicyError, ValidationError

# ★ Account · ROLE_* · require_role 은 contracts.py 다 (STEP 15).
#   계층 횡단 DTO 이므로 저장 계층이 소유하지 않는다
SECRET_BYTES = 24
TEMP_SECRET_BYTES = 9

# ★ 정책은 상수표에 못 넣는다 (2장 상수표).
#   session_hours   「12시간이 짧다」고 느끼면 바꾼다
#   hash_rounds     하드웨어가 빨라지면 올린다.  PBKDF2 는 라운드를 해시에
#                   함께 저장하므로 바꿔도 옛 해시가 깨지지 않는다
# 프로젝트 뿌리.  ★ 작업 디렉터리에 기대지 않는다 (A-7)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ★ 정본은 contracts 다.  두 곳에 두면 갈린다 (V4-21)
from contracts import ROLE_PENDING  # noqa: E402


def _admin_cfg(key, root: str | None = None):
    """관리 설정.

    ★ 두 곳에 나뉘어 있다 — 판정과 함께 도는 값은 scoring.admin,
      계정·잠금처럼 판정과 무관한 값은 admin.json (부록 B · 08-15).
      찾는 순서를 고정해 둔다.  갈리면 어느 쪽이 정본인지 알 수 없다
    """
    root = ROOT if root is None else root
    for name, sub in (("admin.json", None), ("scoring.json", "admin")):
        path = os.path.join(root, "config", name)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as f:
            node = json.load(f)
        if sub:
            node = node.get(sub, {})
        if key in node:
            return node[key]
    raise KeyError(f"관리 설정에 {key} 가 없다 (config/admin.json · scoring.admin)")


@dataclass(frozen=True)
class ConfigChange:
    change_id: str
    account_id: int
    file: str
    key_path: str
    before: str | None
    after: str | None
    reason: str | None
    applied_at: str
    reverted_at: str | None = None
    recalc_job_id: str | None = None


# 아직 끝나지 않은 상태.  ★ 큐에 든 것도 잠근다 (STEP 132).
#   지시해 두고 시작 전에 규칙을 바꾸면 어느 규칙으로 돈 결과인지 알 수 없다
JOB_OPEN = ("queued", "running")


def running_job(conn: sqlite3.Connection) -> str | None:
    """실행 중이거나 대기 중이면 config 변경을 잠근다 (V10-11 · STEP 132)."""
    marks = ",".join("?" * len(JOB_OPEN))
    row = conn.execute(
        f"SELECT job_id FROM recalc_job WHERE status IN ({marks}) "
        f"ORDER BY rowid LIMIT 1", JOB_OPEN).fetchone()
    return row[0] if row else None


# ── STEP 126 계정 · 권한 ─────────────────────────────────────────────
def hash_secret(secret: str, salt: str, rounds: int | None = None) -> str:
    """★ 라운드 수를 해시와 함께 저장한다.  바꿔도 옛 해시가 안 깨진다."""
    n = int(rounds or _admin_cfg("hash_rounds"))
    digest = hashlib.pbkdf2_hmac(
        "sha256", secret.encode("utf-8"), salt.encode("utf-8"), n).hex()
    return f"{n}${salt}${digest}"


def _split(stored: str) -> tuple[int, str, str]:
    rounds, salt, digest = stored.split("$")
    return int(rounds), salt, digest


def create_account(conn: sqlite3.Connection, login_name: str, role: str,
                   at: str, secret: str | None = None,
                   display_name: str | None = None,
                   email: str | None = None) -> tuple[int, str]:
    """반환   (account_id, 비밀번호).

    ★ 임시 비밀번호는 한 번만 표준출력에 낸다.  저장하지 않는다 (STEP 126).
      본인이 정한 비밀번호(secret)를 주면 변경 강제를 걸지 않는다
    ★ display_name 이 비면 login_name 을 넣는다.  NULL 로 두지 않는다 (STEP 34)
    """
    # ★ pending 은 승인제에서 「승인 전」이다.  막으면 가입 자체가 안 된다
    if role not in (ROLE_USER, ROLE_ADMIN, ROLE_PENDING):
        raise ValidationError(
            f"역할은 user·admin·pending 뿐이다: {role}", step="STEP 126")
    if not (login_name or "").strip():
        raise ValidationError("이름이 필요하다", step="STEP 126")
    if secret is not None:
        # ★ 본인이 정한 것이면 최소 길이를 건다 (STEP 126).
        #   ★ S36 (개정 359) — 마스터 지시로 지금은 1 이다.
        #     「보안은 제일 마지막에 해」.  정식 서비스 전에 되돌린다
        need = int(_admin_cfg("min_secret_length"))
        if len(secret) < need:
            raise ValidationError(f"비밀번호는 {need}자 이상이다",
                                  step="STEP 126")
    temp = secret or secrets.token_urlsafe(TEMP_SECRET_BYTES)
    salt = secrets.token_hex(SECRET_BYTES)
    cur = conn.execute(
        "INSERT INTO account(role,login_name,display_name,email,secret_hash,"
        "must_change_secret,created_at) VALUES (?,?,?,?,?,?,?)",
        (role, login_name, (display_name or "").strip() or login_name,
         (email or "").strip() or None, hash_secret(temp, salt),
         0 if secret else 1, at))
    conn.commit()
    return cur.lastrowid, temp


def account_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) FROM account").fetchone()[0]


def needs_bootstrap(conn: sqlite3.Connection) -> bool:
    """account 가 비어 있으면 웹은 「초기화 필요」 화면만 낸다 (STEP 126)."""
    return account_count(conn) == 0


REJECT_LOCKED = "로그인 시도가 많습니다. 잠시 뒤 다시 해 주십시오"


# 잠금을 푼 기록의 사유 머리말.  ★ 기록을 지우지 않고 한 줄을 더한다
UNLOCK_REASON = "관리자가 잠금을 풀었습니다"


def _recent_failures(conn: sqlite3.Connection, display_name: str,
                     now: datetime) -> int:
    """잠금 창 안의 연속 실패 수.  ★ 성공하면 0 으로 돌아간다."""
    from datetime import timedelta

    since = (now - timedelta(
        seconds=int(_admin_cfg("login_lock_sec")))).isoformat()
    rows = conn.execute(
        "SELECT succeeded FROM auth_login_attempt WHERE display_name=? "
        "AND attempted_at >= ? ORDER BY attempt_id DESC",
        (display_name, since)).fetchall()
    n = 0
    for (ok,) in rows:
        if ok:
            break
        n += 1
    return n


def _log_attempt(conn: sqlite3.Connection, display_name: str, ok: bool,
                 reason: str | None, now: datetime) -> None:
    conn.execute(
        "INSERT INTO auth_login_attempt(display_name,succeeded,reason,"
        "attempted_at) VALUES (?,?,?,?)",
        (display_name, int(ok), reason, now.isoformat()))
    conn.commit()



def is_locked(conn: sqlite3.Connection, display_name: str,
              now: datetime | None = None) -> bool:
    """지금 잠겨 있는가 (60-admin/a-auth).

    ★ 잠금은 시간이 지나면 스스로 풀린다.  「지금」을 묻는 것이다
    """
    from datetime import datetime as _dt, timezone as _tz

    limit = int(_admin_cfg("login_fail_limit"))
    if not limit:
        return False        # 상한이 0 이면 잠그지 않는다 (개정 359)
    now = now or _dt.now(_tz.utc)
    return _recent_failures(conn, display_name, now) >= limit


def unlock_account(conn: sqlite3.Connection, actor: Account,
                   display_name: str, reason: str, at: str) -> None:
    """관리자가 다른 관리자의 잠금을 화면에서 푼다 (60-admin/a-auth).

    ★ 마스터 지적 — 「PC 가 없어 CLI 로 못 푼다」.  화면에서 풀 수 있어야 한다
    ★ 시도 기록은 지우지 않는다 — 되돌릴 수 없는 것은 하지 않는다.
      「푼다」를 성공 시도 한 줄로 남긴다.  그러면 연속 실패가 0 으로 돌아간다
    ★ 누가 왜 풀었는지가 남는다 (감사)
    """
    from datetime import datetime as _dt, timezone as _tz

    require_role(actor, ROLE_ADMIN)
    if not (reason or "").strip():
        raise ValidationError("왜 푸는지 적어 주십시오", step="STEP 126")
    row = conn.execute(
        "SELECT 1 FROM account WHERE display_name=? OR login_name=?",
        (display_name, display_name)).fetchone()
    if row is None:
        raise ValidationError(f"없는 계정입니다: {display_name[:40]}",
                              step="STEP 126")
    conn.execute(
        "INSERT INTO auth_login_attempt(display_name,succeeded,reason,"
        "attempted_at) VALUES (?,1,?,?)",
        (display_name, f"{UNLOCK_REASON} — {actor.display_name}: {reason}",
         at or _dt.now(_tz.utc).isoformat()))
    conn.commit()


def authenticate(conn: sqlite3.Connection, display_name: str,
                 secret: str, now: datetime | None = None) -> Account:
    """로그인 실패도 anonymous 다.  예외를 던지지 않는다 (STEP 126).

    ★ 연속 실패가 상한을 넘으면 잠금 시간 동안 거부한다 (C-5 · V10-20).
      비밀번호가 8자 최소라 시도가 무제한이면 뚫린다
    """
    from datetime import datetime as _dt, timezone as _tz

    now = now or _dt.now(_tz.utc)
    # ★ S36 (개정 359) — login_fail_limit 이 0 이면 잠그지 않는다.
    #   마스터 지시 「그냥 제한 없애」.  ★ 시도 기록은 그대로 남긴다 —
    #   기록을 지우는 것은 되돌릴 수 없다 (규칙 「되돌릴 수 없는 것은 안 한다」)
    _limit = int(_admin_cfg("login_fail_limit"))
    if _limit and _recent_failures(conn, display_name, now) >= _limit:
        _log_attempt(conn, display_name, False, REJECT_LOCKED, now)
        raise PolicyError(REJECT_LOCKED, step="STEP 126")

    row = conn.execute(
        "SELECT account_id, role, display_name, secret_hash, "
        # ★ login_name 으로 찾는다.  display_name 은 중복 허용이라
        #   같은 별명이 둘이면 누구로 로그인되는지 알 수 없다 (STEP 34)
        "must_change_secret FROM account WHERE login_name=? "
        "AND disabled_at IS NULL", (display_name,)).fetchone()
    if row is None:
        _log_attempt(conn, display_name, False, "없는 계정", now)
        return ANONYMOUS
    rounds, salt, digest = _split(row[3])
    # 옛 해시는 저장된 라운드 수로 검증한다
    if not hmac.compare_digest(hash_secret(secret, salt, rounds), row[3]):
        _log_attempt(conn, display_name, False, "비밀번호 불일치", now)
        return ANONYMOUS
    _log_attempt(conn, display_name, True, None, now)
    return Account(row[0], row[1], row[2], must_change_secret=bool(row[4]))


def open_session(conn: sqlite3.Connection, account: Account, at: datetime,
                 hours: int | None = None) -> str:
    """세션을 연다.

    ★ pending 도 로그인한다.  「승인을 기다립니다」 화면을 보려면
      세션이 있어야 한다 — 막으면 승인제가 로그인부터 막힌다 (STEP 126)
    ★ 관심 등록은 각 화면이 ROLE_USER 로 막는다
    """
    require_role(account, ROLE_PENDING)
    hours = int(hours or _admin_cfg("session_hours"))
    sid = secrets.token_urlsafe(SECRET_BYTES)
    conn.execute(
        "INSERT INTO auth_session(session_id,account_id,created_at,expires_at)"
        " VALUES (?,?,?,?)",
        (sid, account.account_id, at.isoformat(),
         (at + timedelta(hours=hours)).isoformat()))
    conn.commit()
    return sid


def session_account(conn: sqlite3.Connection, session_id: str | None,
                    now: datetime) -> Account:
    """만료·폐기된 세션은 anonymous 다."""
    if not session_id:
        return ANONYMOUS
    row = conn.execute(
        "SELECT a.account_id, a.role, a.display_name, s.expires_at, "
        "s.revoked_at, a.must_change_secret, a.disabled_at FROM auth_session s "
        "JOIN account a ON a.account_id = s.account_id WHERE s.session_id=?",
        (session_id,)).fetchone()
    # ★ 중지된 계정은 세션이 살아 있어도 anonymous 다 (C-3).
    #   「로그인만 막습니다」가 되려면 이미 연 세션도 끊겨야 한다
    if row is None or row[4] or row[6] or row[3] <= now.isoformat():
        return ANONYMOUS
    return Account(row[0], row[1], row[2], must_change_secret=bool(row[5]))


def change_secret(conn: sqlite3.Connection, account: Account,
                  new_secret: str, at: str | None = None,
                  keep_session: str | None = None) -> None:
    """★ 바꾸면 다른 세션을 끊는다 (C-4 · 시안 v2_login).

    비밀번호를 바꾸는 이유가 「털렸다」일 수 있다.
    그때 남의 세션이 살아 있으면 바꾼 의미가 없다.
    keep_session   지금 쓰는 세션.  이것만 남긴다
    """
    from datetime import datetime, timezone

    salt = secrets.token_hex(SECRET_BYTES)
    conn.execute(
        "UPDATE account SET secret_hash=?, must_change_secret=0 "
        "WHERE account_id=?",
        (hash_secret(new_secret, salt), account.account_id))
    stamp = at or datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE auth_session SET revoked_at=? WHERE account_id=? "
        "AND revoked_at IS NULL AND session_id IS NOT ?",
        (stamp, account.account_id, keep_session))
    conn.commit()


def revoke_sessions(conn: sqlite3.Connection, account_id: int,
                    at: str) -> int:
    """★ 계정을 중지하면 세션도 끊는다 (C-3)."""
    cur = conn.execute(
        "UPDATE auth_session SET revoked_at=? WHERE account_id=? "
        "AND revoked_at IS NULL", (at, account_id))
    conn.commit()
    return cur.rowcount


# ── STEP 127 config 변경 ─────────────────────────────────────────────
# ★★★★★ 08-29 (마스터 판정 · 개정 841 · 시험자 #82) — ★ `seed.` 를 뗀다.
#   ★★ 시험자 실측 — 「셋 다 303 인데 ★ 미분류 319 → 319 ·
#     ★ **키 꼴이 다르다** — ★ 목록은 `detail:…` 인데 ★ 감사는 `seed.detail:…` 다.
#     ★ ★ 목록에 `seed.` 붙은 것이 하나도 없고 ★ 감사에 없는 것이 하나도 없다」
#   ★ ★ 곧 ★ **저장은 되는데 ★ 다른 열쇠로 저장된다** — ★ 사람이 둘을 못 맞춘다.
#   ★ 그래서 ★ 등록부는 ★ **맨 열쇠**(`detail:…`)로 적고 ★ 여기서 `seed` 아래로 푼다.
#   ★ 파일 꼴은 안 바꾼다 — ★ `field_usage.json` 은 그대로 `seed` 를 갖는다.
#   ★ 감사 세 줄(옛 `seed.…`)은 그대로 둔다 (마스터) — ★ 이력을 고쳐 쓰지 않는다.
#     ★ 옛 열쇠로 들어와도 그대로 풀린다 — ★ 되돌리기가 안 깨진다
_SEED_FILES = {"field_usage.json": "seed"}


def _under_seed(file: str, key_path: str) -> str:
    """등록부의 맨 열쇠를 ★ 담긴 자리로 푼다.  ★ 다른 파일은 그대로다."""
    box = _SEED_FILES.get(file)
    if not box or key_path.startswith(box + "."):
        return key_path              # ★ 옛 꼴이면 그대로 (되돌리기용)
    return f"{box}.{key_path}"


def _walk(blob: dict, key_path: str):
    """★ 키 자체에 점이 들어 있다 — components 의 'spec.hud' (STEP 68).

    각 단계에서 남은 경로 전체를 먼저 맞춰 본다.  안 맞으면 한 마디씩 줄인다.
    단순 split('.') 로 하면 'components.spec.hud' 를 찾지 못한다.
    반환   (부모 dict, 마지막 키) · 없으면 (None, None)
    """
    cur = blob
    rest = key_path
    while True:
        if not isinstance(cur, dict):
            return None, None
        if rest in cur:
            return cur, rest
        parts = rest.split(".")
        for n in range(len(parts) - 1, 0, -1):
            head = ".".join(parts[:n])
            if head in cur and isinstance(cur[head], dict):
                cur, rest = cur[head], ".".join(parts[n:])
                break
        else:
            return None, None


def get_path(blob: dict, key_path: str):
    parent, key = _walk(blob, key_path)
    return None if parent is None else parent[key]


def set_path(blob: dict, key_path: str, value) -> None:
    parent, key = _walk(blob, key_path)
    if parent is None:
        raise ValidationError(f"없는 경로: {key_path}", step="STEP 127")
    parent[key] = value


def _atomic_write(path: str, blob: dict) -> None:
    """임시 파일 → 교체.  쓰다 죽으면 원본이 남는다 (STEP 127)."""
    d = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(dir=d, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(blob, f, ensure_ascii=False, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def apply_config(conn: sqlite3.Connection, account: Account, file: str,
                 key_path: str, value, reason: str | None,
                 root: str = ".", at: str | None = None,
                 also: dict | None = None) -> ConfigChange:
    """저장 순서 — 1~4 가 실패하면 파일을 쓰지 않는다 (STEP 127).

    1 스키마 검증   키가 실재하는가
    2 값 검증      배점이면 Σ == total_points
    3 영향 산출    재처리 결정표에서 from_step (STEP 50a)
    4 이력 기록    ConfigChange
    5 파일 쓰기    원자적으로
    """
    require_role(account, ROLE_ADMIN)
    # ★ 실행 중에는 config 를 바꾸지 않는다 (V10-11).
    #   도는 중에 규칙이 바뀌면 어느 규칙으로 나온 결과인지 알 수 없다
    job = running_job(conn)
    if job:
        raise PolicyError(
            f"재계산 {job} 실행 중이다. 끝난 뒤 변경한다", step="STEP 132")
    at = at or datetime.now(timezone.utc).isoformat()
    path = os.path.join(root, "config", file)
    if not os.path.isfile(path):
        raise ValidationError(f"없는 파일: {file}", step="STEP 127")

    with open(path, encoding="utf-8") as f:
        blob = json.load(f)

    # ★ 등록부는 맨 열쇠로 들어온다 — ★ 담긴 자리로 푼다 (개정 841)
    where = _under_seed(file, key_path)
    # ★ 없는 키는 만들지 않는다.  STEP 6 표에 없는 키가 생긴다
    parent, _k = _walk(blob, where)
    if parent is None:
        raise ValidationError(f"없는 경로: {key_path}", step="STEP 127")
    before = get_path(blob, where)

    # ★ 값이 그대로면 이력을 만들지 않는다.  브라우저 뒤로 → 재전송으로
    #   같은 변경이 두 번 쌓이면 「누가 언제 바꿨나」가 흐려진다 (시나리오 70)
    before_now = get_path(blob, where)
    if before_now == value and not also:
        raise ValidationError(
            f"{key_path} 는 이미 그 값입니다: {value!r}", step="STEP 127")
    after_blob = json.loads(json.dumps(blob))
    set_path(after_blob, where, value)
    # ★ 함께 바뀌어야 하는 키 (STEP 128 의 total_points).
    #   따로 쓰면 중간 상태가 규칙을 깨서 검증이 막는다
    for k, v in (also or {}).items():
        set_path(after_blob, _under_seed(file, k), v)
    _validate_blob(file, after_blob)

    change = ConfigChange(
        change_id=secrets.token_hex(TEMP_SECRET_BYTES),
        account_id=account.account_id, file=file, key_path=key_path,
        before=json.dumps(before, ensure_ascii=False),
        after=json.dumps(value, ensure_ascii=False),
        reason=reason, applied_at=at)
    conn.execute(
        "INSERT INTO config_change(change_id,account_id,file,key_path,"
        "before_value,after_value,reason,applied_at) VALUES (?,?,?,?,?,?,?,?)",
        (change.change_id, change.account_id, file, key_path, change.before,
         change.after, reason, at))
    conn.commit()

    _atomic_write(path, after_blob)
    return change


def _validate_blob(file: str, blob: dict) -> None:
    """값 검증.  배점이면 Σ(skipped 아닌) ≤ total_points (STEP 128).

    ★★★★★ 08-30 (마스터 확정 08-29 밤 · r992 ①②) — ★ `value.market` 30 → 0 ·
      ★ `state.consumable` 15 → 0 인데 ★ 「★ **분모는 910 그대로** (모수를 안 바꾼다)」.
      ★ ★ 그래서 ★ 합이 ★ 865 다 — ★ 45점은 ★ **닿을 수 없는 자리**로 남는다.
    ★★ 「같아야 한다」를 ★ 「넘으면 안 된다」로 바꾼다.
      ★ 이 관문이 막던 것은 ★ **분모를 줄여 비율을 높이는 등급 인플레**다 (STEP 128).
      ★ ★ 합이 ★ 작은 것은 ★ 그 반대라 ★ 후하게 매겨질 길이 없다.
      ★ ★ 합이 ★ 큰 것은 ★ 여전히 막는다 — ★ 100%를 넘길 수 있다
    """
    if file != "scoring.json":
        return
    from contracts import total_of

    s = total_of(blob["components"])
    if s > blob["total_points"]:
        raise ValidationError(
            f"배점 합 {s} > total_points {blob['total_points']}",
            step="STEP 128")


def revert_config(conn: sqlite3.Connection, account: Account, change_id: str,
                  root: str = ".", at: str | None = None) -> ConfigChange:
    """before 값으로 되쓰고 새 ConfigChange 를 만든다.

    원래 행의 reverted_at 을 채운다.  삭제하지 않는다 (STEP 127).
    """
    require_role(account, ROLE_ADMIN)
    at = at or datetime.now(timezone.utc).isoformat()
    row = conn.execute(
        "SELECT file, key_path, before_value, reverted_at FROM config_change "
        "WHERE change_id=?", (change_id,)).fetchone()
    if row is None:
        raise ValidationError(f"없는 변경: {change_id}", step="STEP 127")
    if row[3]:
        raise ValidationError("이미 되돌린 변경이다", step="STEP 127")

    new = apply_config(conn, account, row[0], row[1], json.loads(row[2]),
                       f"revert of {change_id}", root, at)
    conn.execute("UPDATE config_change SET reverted_at=? WHERE change_id=?",
                 (at, change_id))
    conn.commit()
    return new


def history(conn: sqlite3.Connection, file: str | None = None) -> list[tuple]:
    sql = ("SELECT change_id, account_id, file, key_path, before_value,"
           " after_value, reason, applied_at, reverted_at FROM config_change")
    if file:
        return conn.execute(sql + " WHERE file=? ORDER BY applied_at",
                            (file,)).fetchall()
    return conn.execute(sql + " ORDER BY applied_at").fetchall()


# ── STEP 131 등록부 분류 변경 (8장) ──────────────────────────────────
# ★ config 를 웹에서 쓰는 곳은 전부 apply_config 를 거친다 (STEP 127).
#   field_usage.json 도 예외가 아니다 — 파일을 직접 쓰지 않는다
USAGE_VALUES = ("in_use", "display_only", "unused_by_policy",
                "deferred", "blocked", "not_provided", "unclassified")

# 분류마다 반드시 있어야 하는 필드 (6장 V4-07~10)
USAGE_REQUIRES = {
    "in_use": "core_column",
    "display_only": "core_column",
    "blocked": "unblock_condition",
    "deferred": "use_when",
}


def classify_field(conn: sqlite3.Connection, account: Account, endpoint: str,
                   json_path: str, usage: str, reason: str,
                   core_column: str | None = None,
                   unblock_condition: str | None = None,
                   use_when: str | None = None, priority: int | None = None,
                   root: str = ".", at: str | None = None) -> ConfigChange:
    """등록부 분류를 웹에서 바꾼다 (8장 STEP 131).

    ★ suggested.json 을 그대로 옮기지 않는다.  사람이 확인·수정한 값을 받는다
    금지   unclassified 로 되돌리는 것 — 분류를 지우는 것은 판단이 아니다
    """
    require_role(account, ROLE_ADMIN)
    if usage not in USAGE_VALUES:
        raise ValidationError(f"없는 분류: {usage}", step="STEP 131")
    if usage == "unclassified":
        raise ValidationError(
            "unclassified 로 되돌릴 수 없다. 분류를 지우는 것은 판단이 아니다",
            step="STEP 131")
    if not reason:
        raise ValidationError("사유가 없다. 「왜 이 분류인가」가 남아야 한다",
                              step="STEP 131")

    need = USAGE_REQUIRES.get(usage)
    got = {"core_column": core_column, "unblock_condition": unblock_condition,
           "use_when": use_when}
    if need and not got[need]:
        raise ValidationError(
            f"{usage} 에는 {need} 가 있어야 한다 (V4-07~10)", step="STEP 131")

    entry = {"usage": usage, "reason": reason}
    for k, v in got.items():
        if v:
            entry[k] = v
    if priority is not None:
        entry["priority"] = priority

    # 없는 키는 apply_config 가 막는다 — seed 에 자리를 먼저 만든다
    path = os.path.join(root, "config", "field_usage.json")
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    key = f"{endpoint}:{json_path}"
    if key not in blob["seed"]:
        blob["seed"][key] = {"usage": "unclassified", "reason": "신규"}
        _atomic_write(path, blob)

    # ★★ 08-29 (마스터 판정) — ★ `seed.` 를 안 붙인다.
    #   ★ 감사(`config_change.key_path`)에 ★ 목록과 **같은 열쇠**가 남아야
    #     ★ 사람이 둘을 맞춰 볼 수 있다 (시험자 #82)
    change = apply_config(conn, account, "field_usage.json", key,
                          entry, f"등록부 분류: {reason}", root=root, at=at)
    # ★★★★★ 09-02 (1부 1-8 · **5회차째**) — ★ **표도 함께 고친다.**
    #   ★ 전에는 ★ `config/field_usage.json` **파일에만** 썼다.
    #   ★ ★ 그런데 ★ 화면이 세는 것은 ★ **`meta_field_usage` 표**다
    #   ★ ★ ★ (`report/screens/admin.py:193` — ★ `WHERE usage='unclassified'`).
    #   ★★ 그래서 ★ 눌러도 ★ **미분류 333 → 333** 이었다.  ★ `303` 은 왔는데
    #     ★ ★ 화면 수가 안 움직였다 — ★ 가이드가 다섯 회차째 짚었다.
    #   ★ 표는 ★ **사이트마다 한 행**이라 ★ 같은 (endpoint, json_path) 를 다 고친다.
    #     ★ ★ 파일은 사이트를 안 나눈다 — ★ 분류는 「그 길이 무엇인가」이지
    #     ★ ★ ★ 「어느 사이트인가」가 아니다 (`tools/sync_registry.py` 도 그렇게 편다)
    conn.execute(
        "UPDATE meta_field_usage SET usage=?, reason=?, core_column=?,"
        " unblock_condition=?, use_when=?, priority=?"
        " WHERE endpoint=? AND json_path=?",
        (usage, reason, core_column, unblock_condition, use_when, priority,
         endpoint, json_path))
    conn.commit()
    return change


# ── 가입 · 사용자 관리 (13장 STEP 126 · 시안 v2_join · v2_admin_users) ──
# ★ 승인 전에는 관심 등록을 못 한다.  등급·시세는 계정 없이도 본다


def account_rows(conn: sqlite3.Connection) -> list:
    """계정 목록.  ★ secret_hash 는 내지 않는다 (STEP 35)."""
    # ★ 지금 잠겨 있는지도 낸다 — 화면에서 풀 수 있어야 한다 (60-admin/a-auth).
    #   마스터 지적 「PC 가 없어 CLI 로 못 푼다」
    return [{"account_id": r[0], "display_name": r[1], "role": r[2],
             "created_at": r[3], "last_seen_at": r[4],
             "disabled": bool(r[5]),
             "locked": is_locked(conn, r[1])}
            for r in conn.execute(
                "SELECT account_id, display_name, role, created_at, "
                "last_seen_at, disabled_at IS NOT NULL FROM account "
                "ORDER BY account_id")]


def admin_count(conn: sqlite3.Connection) -> int:
    """★ 관리자를 0명으로 만들 수 없다.  아무도 관리할 수 없게 된다."""
    return conn.execute(
        "SELECT COUNT(*) FROM account WHERE role = 'admin' "
        "AND disabled_at IS NULL").fetchone()[0]


def set_role(conn: sqlite3.Connection, account_id: int, role: str,
             at: str) -> None:
    """역할 변경.  ★ 마지막 관리자를 내리지 않는다."""
    cur = conn.execute("SELECT role FROM account WHERE account_id = ?",
                       (account_id,)).fetchone()
    if cur and cur[0] == ROLE_ADMIN and role != ROLE_ADMIN \
            and admin_count(conn) <= 1:
        raise PolicyError(
            "마지막 관리자의 역할은 내릴 수 없습니다",
            action="다른 계정을 먼저 관리자로 올린 뒤 바꾸십시오 "
                   "(/admin/users 의 역할 바꾸기)",
                          step="STEP 126")
    conn.execute("UPDATE account SET role = ? WHERE account_id = ?",
                 (role, account_id))
    conn.commit()


def set_disabled(conn: sqlite3.Connection, account_id: int, off: bool,
                 at: str) -> None:
    """★ 「중지」는 삭제가 아니다.  로그인만 막고 관심·이력은 남긴다."""
    cur = conn.execute("SELECT role FROM account WHERE account_id = ?",
                       (account_id,)).fetchone()
    if off and cur and cur[0] == ROLE_ADMIN and admin_count(conn) <= 1:
        raise PolicyError(
            "마지막 관리자는 중지할 수 없습니다",
            # ★ 덜 위험한 대안을 함께 낸다 (STEP 149l · 149m)
            action="다른 계정을 관리자로 올린 뒤 중지하십시오. "
                   "로그인만 막으려면 비밀번호를 바꾸는 편이 안전합니다",
                          step="STEP 126")
    conn.execute("UPDATE account SET disabled_at = ? WHERE account_id = ?",
                 (at if off else None, account_id))
    conn.commit()
    if off:
        # ★ 이미 연 세션도 끊는다.  안 끊으면 「중지」가 거짓이다 (C-3)
        revoke_sessions(conn, account_id, at)


def add_config_key(conn: sqlite3.Connection, account: Account, file: str,
                   key_path: str, value, reason: str | None,
                   root: str = ".", at: str | None = None) -> ConfigChange:
    """새 키를 만든다 (STEP 130 차종 추가 전용).

    ★ apply_config 는 없는 키를 만들지 않는다 — STEP 6 표에 없는 키가
      생기기 때문이다.  차종은 목록이 늘어나는 것이 정상이라 여기서 만든다
    금지   차종 밖의 파일에 새 키를 만드는 것
    """
    require_role(account, ROLE_ADMIN)
    if file != "targets.json":
        raise ValidationError(
            f"새 키를 만들 수 있는 파일은 targets.json 뿐이다: {file}",
            step="STEP 130")
    job = running_job(conn)
    if job:
        raise PolicyError(
            f"재계산 {job} 실행 중이다. 끝난 뒤 변경한다", step="STEP 132")
    if not reason or not str(reason).strip():
        raise ValidationError("사유 없이 차종을 추가하지 않는다",
                              step="STEP 130")
    at = at or datetime.now(timezone.utc).isoformat()
    path = os.path.join(root, "config", file)
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    if key_path in blob:
        raise ValidationError(f"이미 있는 키: {key_path}", step="STEP 130")

    after = json.loads(json.dumps(blob))
    after[key_path] = value
    change = ConfigChange(
        change_id=secrets.token_hex(TEMP_SECRET_BYTES),
        account_id=account.account_id, file=file, key_path=key_path,
        before="null", after=json.dumps(value, ensure_ascii=False),
        reason=reason, applied_at=at)
    conn.execute(
        "INSERT INTO config_change(change_id,account_id,file,key_path,"
        "before_value,after_value,reason,applied_at) VALUES (?,?,?,?,?,?,?,?)",
        (change.change_id, change.account_id, file, key_path, change.before,
         change.after, reason, at))
    conn.commit()
    _atomic_write(path, after)
    return change
