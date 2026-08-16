# -*- coding: utf-8 -*-
"""개인정보 분리 (L4).

지시서   3장 STEP 35 · 6장 V2-09 · V2-10 · V2-11 · V2-12
근거     ★ 번호판은 결합 키다.  암호화하면 비교가 안 된다.
         원본은 core_pii 에, 결합용 해시와 표시용 마스킹만 core_listing 에 둔다.
금지     core_pii · core_dealer_pii 를 직접 SELECT 하는 것.  get_pii() 로만 읽는다
         결합 키를 가역 암호화하는 것 — 매번 복호화해야 비교가 된다
         무염 해시 — 번호판은 형식이 정해진 유한 집합이라 전수 대조로 뚫린다
         키를 config 나 코드에 두는 것
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3

from store.raw import commit

HASH_HEX_LEN = 16
KEY_BYTES = 32
# ★ 뿌리 기준이다.  cwd 가 바뀌면 키를 못 찾아 해시가 전건 어긋난다 (A-7)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEY_PATH = os.path.join(ROOT, "secrets", "plate_hmac.key")
FILE_MODE_OWNER_ONLY = 0o600  # 소유자만 읽는다.  임계값이 아니라 권한 규격이다

SCOPE_LISTING = "listing"
SCOPE_DEALER = "dealer"

PII_FIELDS = {
    SCOPE_LISTING: ("plate_no", "plate_history_json", "record_plate_no"),
    SCOPE_DEALER: ("dealer_name", "phone", "address"),
}

# ★ 렌터카 판정용 파생값 (7장 STEP 78).  is_rental_plate 불리언이 아니다.
#   불리언이면 나중에 「허와 하가 다른가」를 물을 때 재파싱해야 한다.
#   한 글자는 원본이 아니고, 판정에 필요한 전부다
USE_CHARS = ("허", "하", "호")


def load_key(path: str = KEY_PATH) -> bytes:
    """키가 없으면 시작하지 않는다.

    임시 키로 돌리면 다음 실행과 결합이 깨진다 (STEP 35).
    부트스트랩은 make_key() 가 한 번만 한다.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"{path} 가 없다. python3 -m store.pii init 로 생성한다. "
            "임시 키로 돌리면 다음 실행과 결합이 깨진다")
    with open(path, "rb") as f:
        key = f.read().strip()
    if len(key) < KEY_BYTES:
        raise ValueError(f"{path} 키 길이 부족")
    return key


def make_key(path: str = KEY_PATH) -> str:
    """없을 때만 만든다.  덮어쓰지 않는다 — 기존 해시가 전부 무효가 된다."""
    if os.path.isfile(path):
        return path
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(secrets.token_hex(KEY_BYTES))
    os.chmod(path, FILE_MODE_OWNER_ONLY)
    return path


def plate_hash(plate_no: str | None, key: bytes) -> str | None:
    """HMAC-SHA256 앞 16자.  결정적이어야 결합에 쓸 수 있다."""
    if not plate_no:
        return None
    mac = hmac.new(key, str(plate_no).strip().encode("utf-8"), hashlib.sha256)
    return mac.hexdigest()[:HASH_HEX_LEN]


def plate_use_char(plate_no: str | None) -> str | None:
    """번호판의 용도 문자.  '허' · '하' · '호' · None (그 외).

    ★ 마스킹 컬럼을 두지 않는다.  「확보 여부」는 hash IS NOT NULL 로 충분하다.
      중간값을 저장하면 PII 판단이 원본/마스킹/해시 셋으로 갈린다 (STEP 35).
    """
    if not plate_no:
        return None
    for ch in str(plate_no):
        if ch in USE_CHARS:
            return ch
    return None


def hash_list(values, key: bytes) -> list[str]:
    """과거 번호도 해시한다.  합집합 매칭에 쓰이므로 원본만 두면 결합이 깨진다."""
    out = []
    for v in values or []:
        h = plate_hash(v if isinstance(v, str) else (v or {}).get("carNo"), key)
        if h:
            out.append(h)
    return out


def save_listing_pii(conn: sqlite3.Connection, listing_id: str,
                     plate_no: str | None, plate_history_json: str | None,
                     at: str, record_plate_no: str | None = None) -> None:
    """이미 있는 값은 덮어쓰지 않는다 — detail 과 record 가 따로 들어온다."""
    conn.execute(
        "INSERT INTO core_pii"
        "(listing_id,plate_no,plate_history_json,record_plate_no,created_at)"
        " VALUES (?,?,?,?,?) ON CONFLICT(listing_id) DO UPDATE SET"
        " plate_no=COALESCE(excluded.plate_no, plate_no),"
        " plate_history_json=COALESCE(excluded.plate_history_json,"
        "                             plate_history_json),"
        " record_plate_no=COALESCE(excluded.record_plate_no, record_plate_no)",
        (listing_id, plate_no, plate_history_json, record_plate_no, at))
    commit(conn)


def save_dealer_pii(conn: sqlite3.Connection, dealer_id: int,
                    dealer_name: str | None, phone: str | None,
                    address: str | None, at: str) -> None:
    """★ 딜러 단위다.  매물마다 연락처를 복제하지 않는다.  core_dealer 와 1:1"""
    conn.execute(
        "INSERT OR REPLACE INTO core_dealer_pii"
        "(dealer_id,dealer_name,phone,address,created_at) VALUES (?,?,?,?,?)",
        (dealer_id, dealer_name, phone, address, at))
    commit(conn)


def get_pii(conn: sqlite3.Connection, scope: str, key: tuple,
            field: str) -> str | None:
    """PII 는 이 함수로만 읽는다 (STEP 35).

    나중에 이 함수 안에서만 복호화하면 된다.  호출부를 안 고친다.
    scope   'listing' → (listing_id,)   ·   'dealer' → (dealer_id,)
    """
    if field not in PII_FIELDS.get(scope, ()):
        raise KeyError(f"{scope} 범위에 없는 PII 필드: {field}")
    if scope == SCOPE_LISTING:
        row = conn.execute(
            f"SELECT {field} FROM core_pii WHERE listing_id = ?", key
        ).fetchone()
    elif scope == SCOPE_DEALER:
        row = conn.execute(
            f"SELECT {field} FROM core_dealer_pii WHERE dealer_id = ?",
            key).fetchone()
    else:
        raise KeyError(f"알 수 없는 범위: {scope}")
    return row[0] if row else None

# ★ 실행 코드를 두지 않는다.  import 만으로 아무 일도 안 일어난다 (STEP 15a).
#   키 생성은 run.py · tools/ 가 부른다 — python tools/menu.py setup
