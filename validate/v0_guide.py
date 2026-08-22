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
        text = _read(q)
        for m in re.finditer(r"`((?:state|history|value|spec|taste|warranty)\.[a-z_]+)`", text):
            if m.group(1) in real:
                continue
            # ★ 「옛 이름 → 새 이름」 대조표의 왼쪽은 ★ 있어야 맞다 —
            #   같은 줄에 ★ config 에 있는 이름이 함께 있으면 대조표로 본다
            head = text.rfind("\n", 0, m.start()) + 1
            line = text[head:text.find("\n", m.start())]
            if any(f"`{r}`" in line for r in real):
                continue
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


def s43_2b_axis_renamed() -> tuple[bool, str]:
    """★ config 의 축 id 가 ★ 규격 이름인가 (개정 504 · 마스터 확정).

    ★ S43-2 는 「규격에 config 에 없는 이름이 있나」를 본다 —
      ★ 규격이 규격 이름만 쓰면 ★ 통과한다.  ★ 코드가 옛 이름이어도 안 잡힌다
    ★ 그래서 ★ 반대 방향을 따로 본다 — 「config 에 ★ 옛 이름이 남았나」
    """
    RENAME = {
        "value.depreciation": "value.origin",
        "state.repair": "state.my_cost",
        "history.usage": "history.use",
        "history.lien": "history.seizing",
        "spec.trim": "taste.trim",
        "spec.options": "taste.option",
        "taste.picked": "taste.fitting",
    }
    try:
        cfg = json.loads(_read(SCORING) or "{}")
    except json.JSONDecodeError:
        return False, "config/scoring.json 을 읽을 수 없다"
    left = [f"{k}→{v}" for k, v in RENAME.items() if k in cfg.get("components", {})]
    if left:
        return False, f"config 에 옛 축 이름이 {len(left)}개 남았다 — " + " · ".join(left)
    return True, "config 가 규격 이름을 쓴다"


def s43_2c_no_hda() -> tuple[bool, str]:
    """★ HDA 가 저장소 어디에도 없는가 (개정 505 · 마스터 확정 「옵션이잖아. 됐어 버려」).

    ★ 기록(`03_이력` · `06_오판대장` · `outputs/`)은 뺀다 —
      ★ 지웠다는 사실이 남는 것이 맞다.
    ★ 08-22 — 「줄 번호로 지운다」가 17곳만 잡아 11곳이 살아남았다.
      ★ 그래서 ★ 파일 전체를 훑는 검사로 둔다.
    """
    SKIP_NAME = ("03_이력.md", "06_오판대장.md", "07_밀린일대장.md",
                 "00_버전.md")  # ★ 버전표는 기록이다
    SKIP_DIR = ("outputs", ".git", "__pycache__", "node_modules")
    pat = re.compile(r"HDA|hda", re.I)
    bad: list[str] = []
    for q in ROOT.rglob("*"):
        if not q.is_file() or q.suffix not in (".md", ".py", ".json", ".html"):
            continue
        if any(d in q.parts for d in SKIP_DIR) or q.name in SKIP_NAME:
            continue
        # ★ 이 검사 파일 자신은 뺀다 — 낱말을 적어 두어야 잡을 수 있다
        if q.name == "v0_guide.py":
            continue
        for i, line in enumerate(_read(q).split("\n"), 1):
            if not pat.search(line):
                continue
            # ★ 「HDA 축이 없음」을 지키는 시험은 ★ 살린다 — 되살아나면 그것이 잡는다
            if "test_hda_gate" in line or "축은 더 없다" in line or "축이 없어졌다" in line \
                    or "축은 개정" in line or "not in COMPONENTS" in line:
                continue
            bad.append(f"{q.relative_to(ROOT)}:{i}")
    if bad:
        return False, f"HDA 가 {len(bad)}곳 남았다 — " + " · ".join(bad[:6])
    return True, "HDA 가 저장소에 없다 (기록 제외)"


def s45_3_spec_totals() -> tuple[bool, str]:
    """★ 문서에 ★ 옛 총점이 남아 있는가 (개정 508·510).

    ★ 총점은 605 → 675 → 850 → 910 으로 갔다.  ★ 옛 값이 남으면
      ★ 개발측이 그것을 읽는다 (개정 475 — 850 사고가 그렇게 났다).
    ★★ 개정 510 — 「낱말이 옆에 있을 때」만 보니 ★ 표 칸(| 555 |)을 통째로 놓쳤다.
      ★ 「지키는 척」이었다.  ★ 표 칸과 「555 기준」 「555 를 승계」 꼴도 잡는다.
    ★ 기록만 뺀다 (`03_이력` · `06_오판대장` · `07_밀린일대장` · `00_버전` · `outputs/`).

    ★ 예외 — 아래는 ★ 배점이 아니다.  ★ 바꾸면 사실이 틀어진다
        `SOURCE.md` 32·286        625 = `parse/encar/mapping.py` 줄 수
        `MULTISITE_MAPPING.md` 218  495 = K카 경위 서술
        `f-table` 422·442          675 = `boardStateType` 코드값·건수
        `f-table` 1005             3,555 = 매물 건수
        `INDEX.md` 76              495 = `j-admin-mock2.md` 의 ★ 줄 수 (자동 생성)
    """
    STALE = ("675", "625", "850", "555", "530", "495")
    SKIP_NAME = ("03_이력.md", "06_오판대장.md", "07_밀린일대장.md", "00_버전.md")
    SKIP_DIR = ("outputs", ".git", "__pycache__")
    # ★ 배점이 아닌 자리 — 파일:줄 로 못 박는다 (위 주석에 왜인지 적었다)
    ALLOW = {("docs/SOURCE.md", 32), ("docs/SOURCE.md", 286),
             ("docs/MULTISITE_MAPPING.md", 218),
             ("docs/chapters/30-score/f-table.md", 422),
             ("docs/chapters/30-score/f-table.md", 442),
             ("docs/chapters/30-score/f-table.md", 1005),
             ("docs/INDEX.md", 76)}
    pats = []
    for n in STALE:
        pats += [
            re.compile(rf"(?:총점|분모|배점|합계|grade_base|total_points)\D{{0,12}}{n}\b"),
            re.compile(rf"/\s*{n}\b"),
            re.compile(rf"\b{n}\s*점"),
            re.compile(rf"\|\s*\*{{0,2}}{n}\*{{0,2}}\s*\|"),      # ★ 표 칸
            re.compile(rf"\b{n}\s*(?:기준|을 승계|를 승계|판|짜리)"),   # ★ 「555 기준」
        ]
    bad: list[str] = []
    for q in (ROOT / "docs").rglob("*.md"):
        if any(d in q.parts for d in SKIP_DIR) or q.name in SKIP_NAME:
            continue
        rel = str(q.relative_to(ROOT))
        for i, line in enumerate(_read(q).split("\n"), 1):
            if (rel, i) in ALLOW:
                continue
            if any(p.search(line) for p in pats):
                bad.append(f"{rel}:{i}")
    if bad:
        return False, f"옛 총점이 {len(bad)}곳 — " + " · ".join(bad[:6])
    return True, "옛 총점이 없다 (기록·예외 제외)"


def s45_2_mock_numbers() -> tuple[bool, str]:
    """★ 시안에 ★ 배점·분모 숫자가 남아 있는가 (개정 506).

    ★ 시안은 ★ 모양이 정본이고 ★ 숫자는 `f-table` 5장-2a 가 정본이다 (README).
    ★ 08-22 — 555/530 이 12개 파일에 살아 있어 ★ 화면이 낡은 분모를 냈다.
    ★ 이번 차례는 ★ 분모 규칙 문장까지다.  ★ 배점 숫자는 다음 차례라 ★ 실패가 맞다.
    """
    STALE = ("555", "530", "495", "625", "675", "850")
    mocks = ROOT / "ref" / "screens"
    if not mocks.is_dir():
        return False, "ref/screens 가 없다"
    bad: list[str] = []
    for q in sorted(mocks.glob("*.html")):
        hit = {n for n in STALE if re.search(rf"(?<!\d){n}(?!\d)", _read(q))}
        if hit:
            bad.append(f"{q.name}({'·'.join(sorted(hit))})")
    if bad:
        return False, f"시안 {len(bad)}개에 옛 배점·분모가 있다 — " + " · ".join(bad[:5])
    return True, "시안에 옛 배점·분모가 없다"


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
    ("S43-2b", "config 축 id 가 규격 이름인가", s43_2b_axis_renamed),
    ("S43-2c", "HDA 가 저장소에 없는가", s43_2c_no_hda),
    ("S43-3", "버전이 이력 마지막과 같은가", s43_3_version_matches),
    ("S44-1", "가리키는 명령서가 실제로 있는가", s44_1_order_exists),
    ("S44-2", "명령서가 하나뿐인가", s44_2_one_order),
    ("S45-1", "f-table 절 제목과 표가 같은가", s45_1_one_version),
    ("S45-2", "시안에 옛 배점·분모가 없는가", s45_2_mock_numbers),
    ("S45-3", "규격에 옛 총점이 없는가", s45_3_spec_totals),
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
