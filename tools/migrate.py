# -*- coding: utf-8 -*-
"""스키마 이행 — 기존 DB 를 현재 DDL 에 맞춘다.

지시서   3장 STEP 31a · STEP 19a
근거     ★ CREATE TABLE IF NOT EXISTS 는 기존 테이블을 바꾸지 않는다.
         DDL 을 고쳐도 이미 만들어진 DB 는 옛 스키마로 남는다.
         「새로 만들면 되지」로 두면 실측 데이터를 매번 버리게 된다
금지     데이터를 지우는 이행.  원문은 무손실이다 (P3)
사용     python tools/migrate.py [carwatch.db]
"""
from __future__ import annotations

import os
import sqlite3
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DDL = os.path.join(ROOT, "sql", "ddl")

# (테이블, 컬럼, 무엇을 고치는가).  NOT NULL 을 떼는 것은 재작성이 필요하다
DROP_NOT_NULL: tuple[tuple[str, str, str], ...] = (
    ("dict_model_option", "option_name", "원문에서 온다 (STEP 31a)"),
)


def _table_sql(conn, table: str) -> str | None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
        (table,)).fetchone()
    return row[0] if row else None


def drop_not_null(conn: sqlite3.Connection, table: str, column: str) -> bool:
    """SQLite 는 컬럼 제약을 못 고친다.  새 표를 만들어 옮긴다.

    데이터는 전건 보존한다.
    """
    sql = _table_sql(conn, table)
    if sql is None:
        return False
    needle = f"{column}"
    if f"{needle}" not in sql or "NOT NULL" not in sql:
        return False
    lines = sql.splitlines()
    changed = False
    for i, line in enumerate(lines):
        if line.strip().startswith(column) and "NOT NULL" in line:
            lines[i] = line.replace(" NOT NULL", "")
            changed = True
    if not changed:
        return False
    new_sql = "\n".join(lines).replace(f"TABLE {table}", f"TABLE {table}__new", 1)
    new_sql = new_sql.replace(f"TABLE IF NOT EXISTS {table}",
                              f"TABLE {table}__new", 1)
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    names = ", ".join(cols)
    conn.execute(f"DROP TABLE IF EXISTS {table}__new")
    conn.execute(new_sql)
    conn.execute(f"INSERT INTO {table}__new ({names}) "
                 f"SELECT {names} FROM {table}")
    conn.execute(f"DROP TABLE {table}")
    conn.execute(f"ALTER TABLE {table}__new RENAME TO {table}")
    return True


def rebuild_to_ddl(conn: sqlite3.Connection, mem: sqlite3.Connection,
                   table: str) -> bool:
    """제약이 어긋난 표를 DDL 대로 재작성한다.

    ★ ALTER TABLE ADD COLUMN 은 NOT NULL 도 CHECK 도 못 붙인다 (A-7 실측).
      컬럼만 붙이고 끝내면 스키마가 DDL 과 영구히 갈린다 — V2-22 가 잡는다
    데이터는 전건 보존한다.  겹치는 컬럼만 옮긴다
    """
    want = _table_sql(mem, table)
    have = _table_sql(conn, table)
    if want is None or have is None or _norm(want) == _norm(have):
        return False
    new_sql = want.replace(f"TABLE IF NOT EXISTS {table}",
                           f"TABLE {table}__new", 1)
    new_sql = new_sql.replace(f"TABLE {table}", f"TABLE {table}__new", 1) \
        if "__new" not in new_sql else new_sql
    old_cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
    new_cols = [r[1] for r in mem.execute(f"PRAGMA table_info({table})")]
    shared = [c for c in new_cols if c in old_cols]
    names = ", ".join(shared)
    conn.execute(f"DROP TABLE IF EXISTS {table}__new")
    conn.execute(new_sql)
    conn.execute(f"INSERT INTO {table}__new ({names}) "
                 f"SELECT {names} FROM {table}")
    conn.execute(f"DROP TABLE {table}")
    conn.execute(f"ALTER TABLE {table}__new RENAME TO {table}")
    return True


def _norm(sql: str) -> str:
    """비교용 정규화.  ★ 공백·줄바꿈 차이는 어긋남이 아니다."""
    import re

    body = re.sub(r"--[^\n]*", " ", sql)
    return " ".join(body.split()).replace("IF NOT EXISTS ", "").lower()


def main() -> int:
    db = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT,
                                                            "carwatch.db")
    if not os.path.isfile(db):
        print(f"[X] {db} 가 없다")
        return 2
    conn = sqlite3.connect(db)
    conn.execute("PRAGMA foreign_keys = OFF")

    before = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for name in sorted(os.listdir(DDL)):
        if name.endswith(".sql"):
            conn.executescript(open(os.path.join(DDL, name),
                                    encoding="utf-8").read())
    after = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    added = sorted(after - before)

    # ★ CREATE TABLE IF NOT EXISTS 는 컬럼도 안 늘린다.
    #   ALTER TABLE ADD COLUMN 으로 채운다 (데이터 보존)
    added_cols = []
    mem = sqlite3.connect(":memory:")
    for name in sorted(os.listdir(DDL)):
        if name.endswith(".sql"):
            mem.executescript(open(os.path.join(DDL, name),
                                   encoding="utf-8").read())
    for (table,) in mem.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%'"
    ).fetchall():
        have = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        if not have:
            continue
        for r in mem.execute(f"PRAGMA table_info({table})"):
            col, ctype, notnull, default = r[1], r[2], r[3], r[4]
            if col in have:
                continue
            # NOT NULL 은 기존 행을 못 채운다 — 기본값이 있어야 붙인다
            tail = f" DEFAULT {default}" if default is not None else ""
            if notnull and default is None:
                added_cols.append(f"{table}.{col} — 건너뜀 (NOT NULL·기본값 없음)")
                continue
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ctype}{tail}")
            added_cols.append(f"{table}.{col}")

    fixed = []
    for table, column, why in DROP_NOT_NULL:
        if drop_not_null(conn, table, column):
            fixed.append(f"{table}.{column} — {why}")
    # ★ 컬럼만 붙이고 끝내면 제약이 DDL 과 갈린다 (A-7).  전 표를 대조한다
    for table in sorted(t for t in {r[0] for r in mem.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
            if not t.startswith("sqlite_")):
        if rebuild_to_ddl(conn, mem, table):
            fixed.append(f"{table} — DDL 대로 재작성 (제약 반영)")
    conn.commit()
    conn.execute("PRAGMA foreign_keys = ON")

    print(f"신규 테이블 {len(added)}개" + (f": {', '.join(added)}" if added else ""))
    print(f"컬럼 추가 {len(added_cols)}건")
    for a in added_cols:
        print(f"  {a}")
    print(f"제약 이행 {len(fixed)}건")
    for f in fixed:
        print(f"  {f}")
    print("\n데이터는 보존됐다.  원문은 무손실이다 (P3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
