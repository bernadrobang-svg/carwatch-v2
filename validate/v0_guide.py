# -*- coding: utf-8 -*-
"""가이드 문서 자체를 검사한다 (V0 계열).

근거   인수인계 원칙 1「덧붙이지 마라. 고쳐라」· 원칙 1-a「값은 한 곳에만」
       원칙 2「명령서는 하나만」· 원칙 4「「했다」를 본문으로 확인」
까닭   08-22 에 원칙 다섯이 「★ 신설」로 적히고 ★ 검사에 등록되지 않았다.
       그래서 축 id 지어냄 · f-table 두 판 · 없는 명령서 참조가
       ★ 사람 손으로만 잡혔다 (오판대장 모양 ⑱).
금지   여기서 문서를 고치는 것.  ★ 검사는 잡기만 한다.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GUIDE = ROOT / "docs" / "guide"
FTABLE = ROOT / "docs" / "chapters" / "30-score" / "f-table.md"
SCORING = ROOT / "config" / "scoring.json"


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except OSError:
        return ""


def s43_2_axis_ids() -> tuple[bool, str]:
    """★ 규격의 축 id 가 config/scoring.json 에 있는가.

    08-22 — 가이드가 여섯을 지어냈다 (state.my_cost · history.use …).
    """
    try:
        real = set(json.loads(_read(SCORING) or "{}").get("components", {}))
    except json.JSONDecodeError:
        return False, "config/scoring.json 을 읽을 수 없다"
    if not real:
        return False, "config/scoring.json 에 components 가 없다"
    # ★ 03_이력.md 는 ★ 기록이다 — 옛 이름이 남는 것이 맞다.  ★ 살아 있는 규격만 본다
    bad: list[str] = []
    live = [q for q in GUIDE.glob("*.md") if q.name != "03_이력.md"] + [FTABLE]
    for q in live:
        for m in re.finditer(r"`((?:state|history|value|spec|taste|warranty)\.[a-z_]+)`", _read(q)):
            if m.group(1) not in real:
                bad.append(f"{q.name}:{m.group(1)}")
    if bad:
        return False, "config 에 없는 축 id — " + " · ".join(sorted(set(bad))[:8])
    return True, "축 id 가 config 와 같다"


def s45_1_one_version() -> tuple[bool, str]:
    """★ f-table 안에서 절 제목 배점과 그 절 표의 최고점이 같은가.

    08-22 — 제목만 910 으로 갈고 표를 안 갈아 12개 절이 어긋났다.
    """
    cur: tuple[str, int] | None = None
    top: dict[str, list[int]] = {}
    for line in _read(FTABLE).split("\n"):
        m = re.match(r"^## (\d-\d)\. \S+[^★]*? ★? ?(\d+)", line)
        if m:
            cur = (m.group(1), int(m.group(2)))
            top[cur[0]] = [cur[1], 0]
        elif line.startswith(("## ", "# ")):
            cur = None
        if cur and re.match(r"^\|[^|]+\|\s*\d+\s*\|$", line):
            v = int(re.search(r"(\d+)\s*\|$", line).group(1))
            top[cur[0]][1] = max(top[cur[0]][1], v)
    bad = [f"{k}(제목 {v[0]}·표 {v[1]})" for k, v in top.items() if v[1] and v[0] != v[1]]
    if bad:
        return False, "제목과 표가 어긋난다 — " + " · ".join(bad)
    return True, f"{len(top)}개 절의 제목과 표가 같다"


def _order_files() -> list[Path]:
    """★ 명령서가 놓일 수 있는 곳을 ★ 모두 센다.

    08-22 — `inbox/` 를 안 세서 여섯이 숨어 있었다 (밀린일 0-3).
    ★ 지금 `inbox/` 는 없다.  ★ 없어도 안 깨지게 glob 만 돈다.
    """
    got: list[Path] = []
    for d in (ROOT / "outputs", ROOT / "inbox"):
        if d.is_dir():
            got += d.glob("ORDER_*.md")
    return sorted(got)


def s44_1_order_exists() -> tuple[bool, str]:
    """★ 가이드가 가리키는 명령서 파일이 실제로 있는가.

    ★ `ORDER_20260822_r493.md` 꼴만 보지 않는다 —
      `ORDER_panels.md` 처럼 날짜 없는 이름도 잡는다 (밀린일 0-3 ②).
    ★ ★ 한글 이름도 잡는다 — `ORDER_00_순서.md` 가 ★ 이번 사태를 낸 이름이다 (개정 502).
      `[A-Za-z0-9_\-]+` 로는 한글이 빠져 ★ 그 이름을 적어도 통과했다.
    """
    # ★ 03_이력.md 는 기록이다 — 지난 명령서 이름이 남는 것이 맞다
    here = {q.name for q in _order_files()}
    bad: list[str] = []
    for q in GUIDE.glob("*.md"):
        if q.name == "03_이력.md":
            continue
        # ★ 한글 이름도 잡는다 — `ORDER_00_순서.md` 가 이번 사태를 냈다 (개정 502)
        text = _read(q)
        for m in re.finditer(r"`?(ORDER_[^\s`'\"]+\.md)`?", text):
            # ★ `ORDER_2026MMDD_rNNN.md` 는 ★ 이름 꼴 안내다.  실제 파일이 아니다
            if "MMDD" in m.group(1) or "NNN" in m.group(1):
                continue
            # ★ 닫힌 줄(~~취소선~~)은 ★ 기록이다 — 지운 파일 이름이 남는 것이 맞다
            head = text.rfind("\n", 0, m.start()) + 1
            line = text[head:text.find("\n", m.start())]
            if line.count("~~") >= 2:
                continue
            if m.group(1) not in here:
                bad.append(f"{q.name}→{m.group(1)}")
    if bad:
        return False, "없는 명령서를 가리킨다 — " + " · ".join(sorted(set(bad)))
    return True, f"가리키는 명령서가 모두 있다 (있는 것 {len(here)}개)"


def s44_2_one_order() -> tuple[bool, str]:
    """★ 명령서가 하나뿐인가 (원칙 2).

    ★ `outputs/` 만 세면 ★ 지키는 척한다 — `inbox/` 에 여섯이 숨어 있었다.
    ★ 두 곳을 함께 세고 ★ 합쳐 하나여야 한다 (밀린일 0-3 ①).
    """
    got = _order_files()
    if len(got) > 1:
        return False, (f"명령서가 {len(got)}개다 — "
                       + " · ".join(f"{p.parent.name}/{p.name}" for p in got))
    if not got:
        return False, "명령서가 없다 — outputs/ORDER_2026MMDD_rNNN.md 가 있어야 한다"
    return True, f"명령서가 하나다 — {got[0].parent.name}/{got[0].name}"


def s43_3_version_matches() -> tuple[bool, str]:
    """★ 00_버전.md 의 지금 버전이 03_이력.md 의 마지막 개정과 같은가 (V0-01)."""
    hist = _read(GUIDE / "03_이력.md")
    nums = [int(x) for x in re.findall(r"^\| (\d{3}) \|", hist, re.M)]
    ver = re.search(r"## 지금 버전\s*\n```\s*\n(SPEC-[\d.]+-r(\d+))", _read(GUIDE / "00_버전.md"))
    if not nums or not ver:
        return False, "버전 또는 이력을 읽을 수 없다"
    if int(ver.group(2)) != max(nums):
        return False, f"버전 r{ver.group(2)} · 이력 마지막 {max(nums)}"
    return True, f"버전과 이력이 r{max(nums)} 로 같다"


CHECKS = (
    ("S43-2", "규격의 축 id 가 config 에 있는가", s43_2_axis_ids),
    ("S43-3", "버전이 이력 마지막과 같은가", s43_3_version_matches),
    ("S44-1", "가리키는 명령서가 실제로 있는가", s44_1_order_exists),
    ("S44-2", "명령서가 하나뿐인가", s44_2_one_order),
    ("S45-1", "f-table 절 제목과 표가 같은가", s45_1_one_version),
)


def run() -> int:
    bad = 0
    for code, name, fn in CHECKS:
        ok, msg = fn()
        print(f"  {'OK  ' if ok else '★ 실패'} {code} {name} — {msg}")
        if not ok:
            bad += 1
    return bad


if __name__ == "__main__":
    raise SystemExit(1 if run() else 0)
