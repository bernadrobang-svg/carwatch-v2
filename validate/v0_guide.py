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
import sys
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

    08-22 — 가이드가 여섯을 지어냈다.
    ★★ 개정 512 — 마스터가 「규격이 기준」으로 정하셨다 (개정 504).
      ★ 규격 이름은 ★ 옳은 것이고 ★ config 가 따라와야 한다.
      ★ 그러므로 ★ 대응표에 있는 규격 이름은 ★ 여기서 잡지 않는다 —
        ★ `S43-2b` 가 ★ 반대 방향(config 에 옛 이름이 남았나)으로 잡는다.
      ★ 대응표에 없는 이름을 지어내면 ★ 여전히 여기서 잡힌다.
    """
    SPEC_NAMES = {"value.origin", "state.my_cost", "history.use", "history.seizing",
                  "taste.trim", "taste.option", "taste.fitting"}
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
            if m.group(1) in real or m.group(1) in SPEC_NAMES:
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


def s44_4_scope_written() -> tuple[bool, str]:
    """★ 수집 범위가 ★ 명령서에 적혀 있는가 (개정 542 · 마스터 확정).

    ★ 마스터 — 「★ 전체 수집이 아니다.  ★ 차종에 해당되는 것만 받는다」
    ★ 08-23 — 사이트 규격 아홉을 쓰면서 ★ 범위를 안 적어 ★ 12만 건 논의가 나왔다.
    ★ 보는 것 — 명령서에 ★ 「전량을 받지 않는다」와 ★ 사이트별 상한 표가 있는가.
    ★★ 개정 543 — ★ 「적혀 있는가」만 보니 ★ 틀린 범위를 통과시켰다.
      ★ 기아를 「facet 에 차종 필터가 없다」로 적었는데 ★ `modelCodeNames` 가 먹었다.
      → ★ 좁힌 건수가 ★ 숫자로 적혀 있는지까지 본다 (「전체 N → 대상 M」).
      ★ 숫자가 없으면 ★ 실측을 안 한 것이다.
    """
    orders = _order_files()
    if not orders:
        return False, "명령서가 없다"
    text = " ".join(_read(q) for q in orders)
    need = ("전량을 받지 않는다", "targets.json", "상한")
    miss = [w for w in need if w not in text]
    if miss:
        return False, "명령서에 수집 범위가 없다 — 빠진 말: " + " · ".join(miss)
    if "빈 쪽까지 늘려" in text and "금지" not in text.split("빈 쪽까지 늘려")[0][-60:]:
        return False, "명령서가 아직 「빈 쪽까지」를 시킨다"
    # ★ 좁힌 건수가 ★ 숫자로 적혀 있는가 — ★ 「전체 N → 대상 M」 꼴
    if not re.search(r"[\d,]{3,}\s*→\s*★?\s*[\d,]+", text):
        return False, "범위가 적혀 있으나 ★ 좁힌 건수가 숫자로 없다 (실측을 안 했다)"
    # ★ 「없다」로 단정한 자리가 남았는가 — ★ 못 찾은 것은 「못 찾았다」로 적는다
    bad_word = [ln.strip()[:44] for ln in text.split("\n")
                if "좁히" in ln and "★ **없다**" in ln]
    if bad_word:
        return False, "「없다」로 단정한 자리가 있다 — " + " · ".join(bad_word[:2])
    return True, "수집 범위가 건수까지 적혀 있다"


def s44_5_site_consistent() -> tuple[bool, str]:
    """★ 명령서 안에서 ★ 같은 사이트가 ★ 두 가지로 적혀 있는가 (개정 542).

    ★ 08-23 — K카가 ★ 세 곳에 다르게 적혀 있었다 —
      3장 머리 「목록만」 · 3-3 「상세까지」 · 10단계 「상세만」.
      ★ 개정 485 에서 지적된 것이 ★ 56개 개정 뒤에도 남아 있었다.
    ★ 보는 것 — ★ 한 사이트에 ★ 서로 어긋나는 말이 함께 있는가.
    """
    CONFLICT = {
        "K카": (("목록만",), ("상세까지",), ("상세만",)),
    }
    orders = _order_files()
    if not orders:
        return False, "명령서가 없다"
    text = " ".join(_read(q) for q in orders)
    bad: list[str] = []
    for site, groups in CONFLICT.items():
        hit = []
        for g in groups:
            for w in g:
                # ★ 「폐기」·「되살리지 마라」가 같은 줄에 있으면 ★ 기록이다
                for line in text.split("\n"):
                    if site in line and w in line and "폐기" not in line \
                            and "되살리지" not in line and "아니다" not in line:
                        hit.append(w)
                        break
        if len(set(hit)) > 1:
            bad.append(f"{site}({'·'.join(sorted(set(hit)))})")
    if bad:
        return False, "명령서가 같은 사이트를 두 가지로 적는다 — " + " · ".join(bad)
    return True, "명령서가 사이트를 한 가지로 적는다"


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
    star: list[str] = []
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
            # ★★ 무늬(`*`)로 가리키면 ★ 검사가 못 잡는다 (명령서 26장) —
            #   ★ `ORDER_*.md` 라 적으면 ★ 「어느 파일인가」가 사라진다.
            #   ★ 하나를 가리키라고 만든 검사인데 ★ 무늬가 그것을 비껴간다
            if "*" in m.group(1) or "?" in m.group(1):
                star.append(f"{q.name}→{m.group(1)}")
                continue
            if m.group(1) not in here:
                bad.append(f"{q.name}→{m.group(1)}")
    if star:
        return False, ("★ 무늬로 가리킨다 (하나를 콕 집어야 한다) — "
                       + " · ".join(sorted(set(star))))
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
                 "00_버전.md",        # ★ 버전표는 기록이다
                 # ★ 요구 추적표는 ★ 「폐기된 것을 지우지 않는다」 (01_요구사항.md:31)
                 # ★ 05_가이드역할 ㉻ 은 ★ HDA 사고를 ★ 본보기로 든다 — 둘 다 기록이다
                 "01_요구사항.md", "05_가이드역할.md")
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
        # ★★ 생성물도 뺀다 (실측 08-24) — ★ `docs/SOURCE.md` 가 ★ 코드의 함수
        #   이름을 그대로 싣는데 ★ 이 검사의 이름이 ★ `s43_2c_no_hda` 다.
        #   ★ 생성기가 살아나자 ★ 자기 이름 때문에 ★ 자기가 걸렸다.
        #   ★ 생성물은 ★ 코드를 비추는 거울이라 ★ 거기서 잡을 것이 아니다 —
        #   ★ 진짜 HDA 가 코드에 있으면 ★ 그 코드 파일에서 잡힌다
        if q.name in ("SOURCE.md", "CHECKS.md", "INDEX.md", "SCHEMA.md"):
            continue
        for i, line in enumerate(_read(q).split("\n"), 1):
            if not pat.search(line):
                continue
            # ★ 「HDA 축이 없음」을 지키는 시험은 ★ 살린다 — 되살아나면 그것이 잡는다
            # ★ 파수 시험과 ★ 「왜 지웠나」 경위 주석은 살린다 — 되살아나면 그것이 잡는다
            # ★★ 08-25 — ★ 「HDA 를 **축으로 안 쓴다**」고 적어 둔 줄도 ★ 경위다.
            #   ★ ★ 마스터 확정 08-25 — 「고속도로 주행보조」를 ★ 거르개 묶음으로 두되
            #     ★ ★ **약자(HDA)로 걸지 않는다 · 축이 아니라 거르개다**.
            #     ★ ★ 그 까닭을 적은 줄이 ★ 일곱 곳이다 — ★ 지우면 ★ 왜 그런지가 사라진다
            #   ★ ★ 「축이 아니라」·「축 폐기」가 든 줄은 ★ 살린다
            if "test_hda_gate" in line or "축은 더 없다" in line or "축이 없어졌다" in line \
                    or "축은 개정" in line or "not in COMPONENTS" in line \
                    or "를 지우면서" in line or "지웠다" in line \
                    or "축이 아니라" in line or "축 폐기" in line \
                    or "약자" in line \
                    or "고속도로 주행 보조(HDA)" in line:
                continue
            bad.append(f"{q.relative_to(ROOT)}:{i}")
    if bad:
        return False, f"HDA 가 {len(bad)}곳 남았다 — " + " · ".join(bad[:6])
    return True, "HDA 가 저장소에 없다 (기록 제외)"


def s45_5_no_axis_scores() -> tuple[bool, str]:
    """★ 규격 문서가 ★ 축 배점을 손으로 적고 있는가 (개정 513).

    ★ 마스터 — 「해당 페이지를 바라보게」.  ★ 배점은 `f-table` 5장-2a 하나가 정한다.
    ★ 사본을 적으면 ★ 배점이 바뀔 때 낡는다 (개정 495·511 이 그렇게 났다).

    ★ 남기는 것 — ★ 사본이 아니라 ★ 사실인 자리
      `docs/*_API.md` · `MULTISITE_MAPPING.md`
        → 「이 사이트가 어느 축 몇 점을 채우나」는 ★ 그 사이트의 사실이다.
          ★ f-table 을 베낀 것이 아니라 ★ 그 사이트를 잰 결과다
      `f-table.md` 자신 — ★ 정본이다
      `guide/00_개요.md` · `01_시작.md` · `00-standard.md` · `40-report.md`
        → 「가격 200점 전체가 그 위에 얹혀 있었다」처럼 ★ v1 실패의 경위다
      「0점」 · 「N점이 아니다」 — ★ 배점이 아니라 ★ 규칙이다
    """
    AXES = ("사고 이력", "골격", "외판", "자차 수리비", "특수 사고", "소모품", "누유",
            "진정성", "용도", "자차 미가입", "소유자 변경", "압류·저당", "주행 대비",
            "연식", "예산", "시세 대비", "동력계", "일반·차체", "사이트 검증",
            "트림", "옵션", "HUD", "지정 옵션", "색상", "선루프")
    SKIP_NAME = ("03_이력.md", "06_오판대장.md", "07_밀린일대장.md", "00_버전.md",
                 "f-table.md", "MULTISITE_MAPPING.md", "00_개요.md", "01_시작.md",
                 "00-standard.md", "40-report.md")
    pat = re.compile(rf"({'|'.join(AXES)})\D{{0,4}}\*{{0,2}}(\d{{1,3}})\*{{0,2}}\s*점")
    bad: list[str] = []
    for q in (ROOT / "docs").rglob("*.md"):
        if any(d in q.parts for d in ("outputs", ".git")) or q.name in SKIP_NAME:
            continue
        if q.name.endswith("_API.md"):      # ★ 사이트를 잰 결과다.  사본이 아니다
            continue
        for i, line in enumerate(_read(q).split("\n"), 1):
            m = pat.search(line)
            if m and m.group(2) != "0":     # ★ 「0점」은 규칙이다
                bad.append(f"{q.relative_to(ROOT)}:{i}({m.group(1)} {m.group(2)}점)")
    if bad:
        return False, f"규격이 배점을 손으로 적은 곳 {len(bad)} — " + " · ".join(bad[:5])
    return True, "규격이 배점을 손으로 적지 않는다"


def s45_4_table_generated() -> tuple[bool, str]:
    """★ f-table 배점표가 ★ config 에서 생성한 것과 같은가 (개정 512).

    ★ 사본을 감시하지 않고 ★ 사본을 없앤다 — 표는 `tools/gen_table.py` 가 쓴다.
    ★ 제목의 「N축」도 생성한다 — ★ 08-22 에 「27축」이 손으로 센 숫자라
      표가 26 행이 되어도 안 고쳐졌다 (개정 511).
    ★ 그래서 ★ 개수를 세는 검사가 ★ 따로 필요 없다 — 생성물과 대조하면 다 잡힌다.
    """
    import subprocess
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "gen_table.py"), "--check"],
                       capture_output=True, text=True, cwd=str(ROOT))
    msg = (r.stdout or r.stderr).strip().split("\n")[-1]
    return r.returncode == 0, msg or "gen_table.py 를 돌리지 못했다"


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
    # ★ 배점이 아닌 자리 — ★ 줄 번호가 아니라 ★ 그 줄의 내용으로 가른다
    #   ★ 줄 번호로 두었더니 ★ AUTO 블록이 들어가며 밀려 어긋났다 (개정 512)
    ALLOW_TEXT = (
        "같은 뿌리다",           # 인수인계 — 「왜 850 이 됐나」 경위
        "1시간 차다",            # 〃
        "V3-90",                # CHECKS.md — 자동 생성 · 원본은 v3_logic.py 주석
        "boardStateType",        # f-table — 675 는 코드값·건수
        "못 읽는다",              # f-table — 675 건 (갈래별 건수)
        "확인 안 됨 0/3,555",     # f-table — 3,555 는 매물 건수
        "mapping.py",            # SOURCE — 625 는 줄 수
        "j-admin-mock2.md`",     # INDEX — 495 는 줄 수 (자동 생성)
        "K카",                   # MULTISITE_MAPPING — 495 는 경위 서술
    )
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
            if any(w in line for w in ALLOW_TEXT):
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


def s44_3_specs_in_order() -> tuple[bool, str]:
    """★ 가이드가 쓴 규격이 ★ 명령서에서 ★ 가리켜지고 있는가 (개정 540).

    ★ 08-23 — `TARGET_KEY_MAP.md` 를 08-22 에 써 놓고 ★ 명령서에 한 줄도 안 적었다.
      ★ 개발측은 명령서를 보고 일한다 — ★ 규격만 쓰면 ★ 없는 것과 같다.
      ★ 그래서 새 사이트 2,134건이 ★ 통째로 「차종 미정」으로 들어갔다.
    ★ 보는 것 — ★ 사이트 규격(`*_API.md`)과 ★ 다사이트 매핑 · 차종 대응표.
      ★ 자동 생성(`CHECKS`·`INDEX`·`SOURCE`)과 ★ 스키마·안내(`SCHEMA`·`README`·`MAPPING`)는 뺀다
      ★ `ENCAR_API` 는 ★ 이미 붙어 있는 사이트라 뺀다
    """
    orders = _order_files()
    if not orders:
        return False, "명령서가 없다"
    text = " ".join(_read(q) for q in orders)
    bad: list[str] = []
    SKIP = {"CHECKS.md", "INDEX.md", "SOURCE.md", "SCHEMA.md",
            "README.md", "MAPPING.md", "ENCAR_API.md"}
    for q in sorted((ROOT / "docs").glob("*.md")):
        if not re.match(r"^[A-Z][A-Z0-9_]+\.md$", q.name) or q.name in SKIP:
            continue
        if q.stem not in text:
            bad.append(q.name)
    # ★ 반대 방향도 본다 — ★ 명령서가 ★ 없는 규격을 가리키는가 (개정 541)
    #   ★ 08-23 — 명령서가 `KCAR_LIST_API.md` 를 가리켰는데 ★ 그 파일이 없었다
    dead: list[str] = []
    for m in re.finditer(r"`?docs/([A-Z][A-Z0-9_]+\.md)`?", text):
        if not (ROOT / "docs" / m.group(1)).exists():
            dead.append(m.group(1))
    if bad or dead:
        msg = []
        if bad:
            msg.append(f"명령서가 안 가리키는 규격 {len(bad)}개 — " + " · ".join(bad))
        if dead:
            msg.append(f"★ 없는 규격을 가리킨다 {len(set(dead))}개 — " + " · ".join(sorted(set(dead))))
        return False, " / ".join(msg)
    return True, "가이드 규격과 명령서가 서로 맞는다"


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



# ── S46-21 · S46-22 — ★ 시안이 ★ 기계에 걸리게 한다 (명령서 20-5) ────────
# ★ 뿌리 — ★ 08-20 뒤 ★ 개발 기록 열둘에 ★ `ref/screens` 언급이 ★ 0회다.
#   ★ 검사가 시안을 안 보니 ★ 가이드가 매번 표로 옮겨야 했고 ★ 빠뜨리면 조용히 사라졌다.
#   ★ 상세 사진이 ★ 정확히 그 자리였다
SCREENS = ROOT / "ref" / "screens"
TEMPLATES = ROOT / "web" / "templates"
# ★ 시안 ↔ 실제 화면.  ★ 짝이 있는 것만 절 차례를 잰다
SIAN_PAIRS = (("v3_detail_시안.html", "detail.html"),)
# ★ 화면이 아니라 ★ 메모인 <h2>.  ★ 세지 않는다 (실측 08-24 — v3 넷에 다 있다)
SIAN_NOTE_H2 = ("지켜야 하는 것",)


def _h_tags(text: str, tag: str) -> list:
    """`<h2>`·`<h3>` 알맹이를 ★ 나온 차례대로.  ★ 꾸밈은 지운다.

    ★★ 주석을 ★ 먼저 지운다 — ★ 개발 주석 안에 `<h3>` 라는 글자가 있으면
       ★ 거기서부터 ★ 진짜 `</h3>` 까지 통째로 잡힌다 (실측 08-24 — 내가 그랬다)
    """
    text = re.sub(r"<!--.*?-->", "", text or "", flags=re.S)
    out = []
    for got in re.findall(rf"<{tag}[^>]*>(.*?)</{tag}>", text, re.S):
        said = re.sub(r"<[^>]+>", "", got)
        said = re.sub(r"\s+", " ", said).strip()
        if said:
            out.append(said)
    return out


def s46_21_one_screen_per_file() -> tuple[bool, str]:
    """★ 시안 한 파일에 ★ 화면이 둘 이상이면 실패 (명령서 20-5).

    ★ 한 파일에 셋을 담으니 ★ 어느 표가 어느 화면인지 알 수 없었다 (오판 84)
    ★ `<h2>` 로 화면을 센다
    """
    if not SCREENS.is_dir():
        return False, "ref/screens 가 없다"
    bad, old = [], []
    for q in sorted(SCREENS.glob("*.html")):
        got = [x for x in _h_tags(_read(q), "h2")
               if not any(x.startswith(n) for n in SIAN_NOTE_H2)]
        if len(got) <= 1:
            continue
        said = f"{q.name} — 화면 {len(got)}개 ({' · '.join(got)})"
        # ★ 지금 판(v3)만 ★ 실패다.  ★ 옛 판(v2)은 ★ 세어서 알린다 —
        #   ★ 가이드가 v3 를 화면마다 갈랐다 (개정 631).  ★ v2 는 손대지 않는다 (규칙 2)
        (bad if q.name.startswith("v3_") else old).append(said)
    if bad:
        return False, f"{len(bad)}개에 화면이 둘 이상 — " + " / ".join(bad[:3])
    n = len(list(SCREENS.glob("*.html")))
    tail = f" · ★ 옛 판(v2) {len(old)}개는 여러 화면이다 (가이드 몫)" if old else ""
    return True, f"지금 판 시안이 한 파일에 한 화면이다 (전체 {n}개){tail}"


def s46_22_section_order() -> tuple[bool, str]:
    """★ 시안의 절 차례와 ★ 실제 화면의 `<h3>` 차례가 같은가 (명령서 20-5).

    ★ V11-159 「절 차례는 바꾸지 마라」는 ★ 실제 상세의 열 절 차례를 뜻한다 —
      ★ 시안 표의 행 차례가 아니다 (개정 631)
    ★ 시안은 ★ `<div class="v3-lbl">1 판정</div>` 꼴로 절을 적는다.  ★ 번호를 뗀다
    """
    bad, seen = [], 0
    for sian, page in SIAN_PAIRS:
        q, t = SCREENS / sian, TEMPLATES / page
        if not q.is_file() or not t.is_file():
            bad.append(f"{sian} 또는 {page} 가 없다")
            continue
        # ★ 번호와 ★ 별표는 ★ 꾸밈이다 — ★ 양쪽에서 똑같이 뗀다
        def _bare(x: str) -> str:
            return re.sub(r"^[★\s\d]+", "", x).split("—")[0].strip()

        # ★★ 「이 화면은 무엇을 하는 곳인가」는 ★ **절이 아니다** — ★ 머리 상자다
        #   (명령서 1-5 · 시안 주황 상자).  ★ 시안이 그것도 `v3-lbl` 로 적는다.
        #   ★ ★ 화면은 그것을 `h2` 로 낸다 — ★ 절(`h3`)로 세면 ★ 수가 하나 어긋난다
        want = [_bare(x) for x in
                # ★ 마스터 ㉮ (r672) — ★ 시안 쪽에 `.v3-` 을 붙였다.  ★ 둘 다 받는다
                re.findall(r'<div class="(?:v3-)?lbl">([^<]+)</div>', _read(q))
                if "무엇을 하는 곳인가" not in x]
        got = [_bare(x) for x in _h_tags(_read(t), "h3")]
        seen += 1
        if not want:
            bad.append(f"{sian} 에 절이 없다 (<div class=\"v3-lbl\">)")
            continue
        if len(want) != len(got):
            bad.append(f"{page} 절 {len(got)}개 · 시안 {len(want)}개")
            continue
        for i, (a, b) in enumerate(zip(want, got, strict=True), 1):
            if a != b:
                bad.append(f"{page} {i}번째 — 시안 「{a}」 · 화면 「{b}」")
    if bad:
        return False, " / ".join(bad[:3])
    return True, f"시안 {seen}쌍의 절 차례가 화면과 같다"



# ── S46-23 · S46-24 — ★ 엔카에서도 받는다 (명령서 21장 · 개정 632) ──────
TARGETS = ROOT / "config" / "targets.json"


def _targets() -> dict:
    got = json.loads(_read(TARGETS) or "{}")
    return {k: v for k, v in got.items()
            if isinstance(v, dict) and "collect_group" in v}


def s46_23_site_query_filled() -> tuple[bool, str]:
    """★ `site_query` 가 빈 차종이 있으면 실패 (명령서 21장 ④).

    ★ 비면 ★ `collect_groups` 가 ★ 조용히 건너뛴다 — ★ 그 차종은 영영 안 들어온다
    ★ 407 은 ★ 수입차 제약이 아니라 ★ 서버 회선 제약이다.  ★ 브라우저 수집으로 받는다
    """
    got = _targets()
    if not got:
        return False, "config/targets.json 에 차종이 없다"
    bad = [k for k, v in got.items() if not (v.get("site_query") or {})]
    if bad:
        return False, f"{len(bad)}종이 site_query 가 비었다 — " + " · ".join(bad[:6])
    return True, f"차종 {len(got)}종이 전부 site_query 를 가졌다"


def s46_24_facet_unconfirmed() -> tuple[bool, str]:
    """★ 「_확인」이 남은 차종 수를 센다.  ★ 0 이 되면 끝이다 (명령서 21장 ④).

    ★ `ModelGroup` 을 ★ 이름으로 넣어 둔 것이라 ★ facet 으로 맞는지 봐야 한다
    ★ 확인 안 하고 ★ 「_확인」 줄만 지우는 것이 ★ 지어내는 것이다 (금지 6)
    """
    left = []
    for key, spec in _targets().items():
        for site, sq in (spec.get("site_query") or {}).items():
            if any(str(k).startswith("_확인") for k in sq):
                left.append(f"{key}.{site}")
    if left:
        return False, (f"★ facet 미확인 {len(left)}종 — " + " · ".join(left[:6])
                       + "  (「facet 만」으로 확인한 뒤 그 줄을 지운다)")
    return True, "facet 미확인 차종이 없다"


def s46_30_index_covers_docs() -> tuple[bool, str]:
    """★ `docs/**/*.md` 중 ★ INDEX 가 ★ 안 가리키는 것이 있으면 알린다 (명령서 26장).

    ★ 규칙 10 이 ★ 「`docs/INDEX.md` 를 먼저 본다」인데 ★ 거기 없는 문서는
      ★ 아무도 못 찾는다 — ★ 있어도 없는 것과 같다
    ★ WARN 이다 — ★ 새 규격이 들어온 그 순간에는 ★ 늘 잠깐 어긋난다
    """
    docs = ROOT / "docs"
    idx = docs / "INDEX.md"
    if not idx.is_file():
        return False, "docs/INDEX.md 가 없다"
    text = _read(idx) + _read(docs / "MAPPING.md")
    miss = []
    for q in sorted(docs.rglob("*.md")):
        rel = q.relative_to(docs).as_posix()
        if rel in ("INDEX.md", "MAPPING.md", "CHECKS.md", "SOURCE.md"):
            continue
        if rel in text or q.name in text:
            continue
        miss.append(rel)
    if miss:
        return False, (f"★ INDEX 가 안 가리키는 문서 {len(miss)}개 — "
                       + " · ".join(miss[:6]))
    return True, "INDEX 가 docs 를 다 가리킨다"



# ── S46-31 · S46-32 (명령서 29장 ②③) ────────────────────────────────
ENDPOINTS = ROOT / "config" / "endpoints.json"
# ★★ 규격 파일 이름과 ★ config 키가 ★ 늘 같지는 않다.  ★ 짝을 여기 적는다 —
#   ★ 짝 표 없이 만들면 ★ 검사가 늘 빨간불이 되어 ★ 아무도 안 본다 (명령서 29장 ③)
SITE_NAME_PAIRS = {
    "hyundai_certified": "hyundai_cert",
}
# ★ 사이트가 아닌 규격 — ★ 세지 않는다
NOT_A_SITE = ("multisite_mapping", "dedup_cross_site", "server_survival",
              "target_key_map", "ui_review", "encar_robots")


def s46_31_spec_sites_in_config() -> tuple[bool, str]:
    """★ 규격이 있는 사이트가 ★ `config/endpoints.json` 에 있는가 (명령서 29장 ③).

    ★ 규격만 쓰고 ★ 부르는 자리를 안 만들면 ★ 그 사이트는 ★ 영영 안 들어온다
    """
    got = json.loads(_read(ENDPOINTS) or "{}")
    have = {k.lower() for k in got if not k.startswith("_")}
    miss = []
    for q in sorted((ROOT / "docs").glob("*_API.md")):
        name = q.name[:-len("_API.md")].lower()
        if name in NOT_A_SITE:
            continue
        key = SITE_NAME_PAIRS.get(name, name)
        if key not in have:
            miss.append(f"{q.name} → {key}")
    if miss:
        return False, (f"규격은 있는데 config 에 없다 {len(miss)}개 — "
                       + " · ".join(miss))
    return True, f"규격이 있는 사이트 전부가 config 에 있다 (사이트 {len(have)}개)"


def s46_32_generated_fresh() -> tuple[bool, str]:
    """★ 생성물(INDEX · CHECKS · SOURCE · SCHEMA)이 ★ 낡았으면 실패 (명령서 29장 ②).

    ★ 실측 08-24 — ★ `build_index.py` 가 ★ 194행에서 죽어 있는 동안
      ★ 생성물이 ★ 낡은 채 굳었다 (줄 수 29곳 어긋남).
      ★★ 이 검사가 있었으면 ★ 죽은 날 바로 잡혔다
    ★ 생성기를 ★ `--check` 로 돌린다 — ★ 파일을 고치지 않고 ★ 재 보고 되돌린다
    """
    import subprocess

    tool = ROOT / "tools" / "build_index.py"
    if not tool.is_file():
        return False, "tools/build_index.py 가 없다"
    # ★★ 생성물은 ★ 다섯이다 (명령서 29-4 · 31-3) —
    #   ★ INDEX · CHECKS · SOURCE · SCHEMA (build_index) ＋ ★ f-table 배점표 (gen_table)
    #   ★ 검사 하나로 ★ 다섯을 다 잡는다
    bad, said = [], []
    for tool, what in ((tool, "INDEX·CHECKS·SOURCE·SCHEMA"),
                       (ROOT / "tools" / "gen_table.py", "f-table 배점표")):
        if not tool.is_file():
            bad.append(f"{tool.name} 이 없다")
            continue
        got = subprocess.run([sys.executable, str(tool), "--check"],
                             capture_output=True, text=True, cwd=str(ROOT))
        if got.returncode != 0:
            bad.append(f"{what} — " + (" ".join(got.stdout.split())[:90]
                                       or f"{tool.name} 가 죽었다"))
        else:
            said.append(what)
    if bad:
        return False, "★ 생성물이 낡았다 — " + " / ".join(bad)
    return True, "생성물 다섯이 ★ 최신이다 (" + " · ".join(said) + ")"



# ── S46-36 · S46-40 — ★ 요구 추적표를 기계가 읽는다 (명령서 31-3 · 32-4) ──
REQS = GUIDE / "01_요구사항.md"
# ★ 추적표 한 줄 — | # | 날짜 | 원문 | 상태 | 바뀐 문서 | 검사 | 폐기 사유 |
RE_REQ_ROW = re.compile(r"^\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*([\d-]+)\s*\|"
                        r"(.+?)\|(.+?)\|(.+?)\|(.+?)\|(.*?)\|\s*$", re.M)


def _req_rows() -> list:
    """요구 추적표를 ★ 줄로 읽는다.  ★ 꾸밈(★·굵게)은 뗀다."""
    out = []
    for got in RE_REQ_ROW.finditer(_read(REQS)):
        n, day, said, state, docs_, checks, why = got.groups()
        clean = lambda x: re.sub(r"[★*`]", "", x).strip()      # noqa: E731
        out.append({"n": int(n), "day": clean(day), "said": clean(said),
                    "state": clean(state), "docs": clean(docs_),
                    "checks": clean(checks), "why": clean(why)})
    return out


def _tokens(said: str) -> list:
    """★ 마스터 원문에서 ★ 말조각을 뽑는다 (두 글자 이상).

    ★ 이름표 하나(`carCd`)만으로는 안 센다 — ★ 그것은 ★ 그냥 밭 이름이라
      ★ 규격 곳곳에 ★ 정상으로 나온다.  ★ 실측 08-24 — ★ 헛잡이 넷
    ★ 그러므로 ★ 한 줄에 ★ 말조각 ★ 둘부터 ★ 「살아 있다」로 본다
    """
    drop = ("것을", "것이", "하지", "말고", "그리고", "가이드가")
    return [w for w in re.findall(r"[\w가-힣]{2,}", said) if w not in drop]


# ★ 「이 말은 이제 죽었다」고 적어 둔 줄은 ★ 살아 있는 것이 아니다
DEAD_MARK = ("틀렸다", "폐기", "취소", "물렸다", "아니다", "안 준다", "✘", "정정")


def _named_docs(cell: str) -> list:
    """★ 「바뀐 문서」 칸이 가리키는 ★ 실제 파일을 찾는다."""
    out = []
    for name in re.findall(r"[\w/.-]{3,}", cell):
        if name in ("명령서", "이", "표"):
            continue
        for q in (ROOT / "docs").rglob("*.md"):
            if name in q.stem or name in q.as_posix():
                out.append(q)
    return sorted(set(out))


def s46_36_dropped_not_alive() -> tuple[bool, str]:
    """★ 폐기된 요구가 ★ 규격에 ★ 아직 살아 있는가 (명령서 31-3).

    ★ 재는 법 — ★ 추적표에서 상태가 「폐기」인 줄을 뽑아
      ★ 그 줄의 ★ 「바뀐 문서」를 열고
      ★ 마스터 원문의 ★ 말조각이 ★ 아직 ★ 지시하는 줄에 남아 있으면 ★ 실패
    ★ 말조각 ★ 둘이 ★ 한 줄에 같이 있으면 ★ 그 요구가 살아 있는 것이다
    ★ 「틀렸다 · 정정 · 폐기」라 적어 둔 줄은 ★ 죽은 것으로 본다
    ★ 머리글(#)은 ★ 지시가 아니므로 ★ 안 본다
    """
    rows = [r for r in _req_rows() if r["state"].startswith("폐기")]
    if not rows:
        return False, "요구 추적표에서 「폐기」 줄을 못 읽었다"
    bad = []
    for r in rows:
        toks = _tokens(r["said"])
        for q in _named_docs(r["docs"]):
            for i, line in enumerate(_read(q).split("\n"), 1):
                if line.lstrip().startswith("#") or any(d in line for d in DEAD_MARK):
                    continue
                if sum(1 for t in toks if t in line) >= 2:
                    bad.append(f"요구 {r['n']} → {q.name}:{i}")
    if bad:
        return False, (f"★ 폐기된 요구가 규격에 살아 있다 {len(bad)}곳 — "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, f"폐기된 요구 {len(rows)}건이 규격에 안 남아 있다"


def s46_40_progress_docs_changed() -> tuple[bool, str]:
    """★ 「진행」인 요구의 ★ 「바뀐 문서」가 ★ 실제로 바뀌었는가 (명령서 32-4).

    ★★ 마스터 — 「지적받은 것이 다 고쳐졌는지 ★ 사람이 세지 않게 하라」 (요구 80)
    ★ 재는 법 — ★ 그 문서의 `version` 날짜가 ★ 요구 날짜보다 오래면 ★ 실패
    ★ 가리키는 문서를 ★ 하나도 못 찾은 줄도 ★ 실패다 — ★ 빈 칸은 안 센 것이다
    """
    rows = [r for r in _req_rows() if r["state"].startswith("진행")]
    if not rows:
        return True, "「진행」인 요구가 없다"
    bad, seen = [], 0
    for r in rows:
        docs = _named_docs(r["docs"])
        if not docs:
            continue                      # ★ 「이 표」처럼 ★ 파일이 아닌 것은 넘긴다
        for q in docs:
            seen += 1
            got = re.search(r"SPEC-\d{4}\.(\d{2})\.(\d{2})", _read(q))
            if not got:
                bad.append(f"요구 {r['n']} → {q.name} (version 이 없다)")
                continue
            ver = f"{got.group(1)}-{got.group(2)}"
            if r["day"] and ver < r["day"]:
                bad.append(f"요구 {r['n']} → {q.name} (문서 {ver} · 요구 {r['day']})")
    if bad:
        return False, ("★ 「진행」인데 문서가 안 바뀌었다 — "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, f"「진행」 {len(rows)}건의 바뀐 문서 {seen}개가 다 최신이다"



def s46_41_site_status_known() -> tuple[bool, str]:
    """★ `sites.json` 의 status 가 ★ 규격이 정한 셋 안인가.

    ★ 규격 — `docs/chapters/00-standard.md:616`
      「sites.json  사이트 목록 · status (active · planned · paused)」
    ★★ 실측 08-24 — ★ 내가 r654 에서 ★ 사이트 다섯을 ★ `pending` 으로 넣었다.
      ★ 규격에 없는 말이라 ★ `V9-10` 이 그 다섯을 ★ 「active 인데 배점이 없다」로
      읽어 ★ fatal 이 났다.  ★ 값 하나가 ★ 조용히 새 뜻을 만들었다
    """
    import json as _j
    known = set()
    for line in _read(ROOT / "docs" / "chapters" / "00-standard.md").split("\n"):
        if "sites.json" in line and "status" in line:
            got = re.search(r"status\s*\(([^)]+)\)", line)
            if got:
                known = {w.strip() for w in got.group(1).split("·") if w.strip()}
            break
    if not known:
        return False, "규격에서 사이트 status 목록을 못 읽었다 (00-standard.md)"
    with open(ROOT / "config" / "sites.json", encoding="utf-8") as fp:
        raw = _j.load(fp)
    sites = raw.get("sites", raw)
    bad = [f"{n} — status={o.get('status')!r}"
           for n, o in sites.items()
           if isinstance(o, dict) and o.get("status") not in known]
    if bad:
        return False, (f"★ 규격에 없는 status — 허용 {'·'.join(sorted(known))} — "
                       + " · ".join(bad[:5]))
    return True, f"사이트 {len(sites)}개의 status 가 다 규격 안이다 ({'·'.join(sorted(known))})"



# ★★ 제원 — ★ 상세·비교에만 (UI_REVIEW 10 · 마스터 확정 08-24)
SPEC_SCREENS_OK = ("detail.html", "compare.html")
# ★ 제원이 화면에 나왔음을 알리는 글자 — ★ 칸 이름과 단위 둘 다 본다
SPEC_WORDS = ("spec_fuel_economy_kmpl", "spec_seats", "km/L", "인승")
# ★★ 마스터 확정 금지 — ★ 「살지 말지가 안 갈리는 것」 (UI_REVIEW 10-2).
#   ★ 금지가 ★ 열둘에서 ★ 열로 줄었다 — ★ 풀린 것이 아니다
SPEC_FORBIDDEN = ("제로백", "공차중량", "타이어 규격", "전장", "전폭", "전고",
                  "배기량", "출력", "토크", "축거")


def _templates() -> list:
    got = ROOT / "web" / "templates"
    return sorted(p for p in got.glob("*.html")) if got.is_dir() else []


def s46_45_spec_not_in_list() -> tuple[bool, str]:
    """★ 제원이 ★ 목록 카드에 ★ 안 나오는가 (UI_REVIEW 10-3 · 마스터 결정).

    ★ 마스터가 ★ 「B — 상세에만」으로 정하셨다.  ★ 비교에도 낸다 (견주는 자리다)
    ★ ★ 목록에 내면 ★ 카드가 카탈로그가 된다 — ★ 「살지 말지」를 못 고른다
    """
    bad = []
    for q in _templates():
        if q.name in SPEC_SCREENS_OK:
            continue
        text = _read(q)
        for w in SPEC_WORDS:
            if w in text:
                bad.append(f"{q.name} — 「{w}」")
    if bad:
        return False, ("★ 제원이 상세·비교 밖에 나왔다 — "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, f"제원은 {'·'.join(SPEC_SCREENS_OK)} 에만 있다"


def s46_46_spec_forbidden_ten() -> tuple[bool, str]:
    """★ 금지 열 항목이 ★ 화면에 안 나오는가 (UI_REVIEW 10-2 · 마스터 확정).

    ★ 제로백 · 공차중량 · 타이어 규격 · 전장·전폭·전고 · 배기량 · 출력 · 토크 · 축거
    ★★ 까닭 — ★ 그것으로 ★ 「살지 말지」가 ★ 안 갈린다.  ★ 카탈로그를 보러 온 것이 아니다
    ★ 주석은 안 센다 — ★ 「내지 마라」라고 적어 둔 줄이 잡히면 안 된다
    ★★ 관리 화면(`admin_*`)은 뺀다 — ★ 거기 「배기량」은 ★ **갈래를 고르는 규칙**이다
      (`targets.json` 의 `displacement_range`).  ★ 제원을 보여 주는 것이 아니다.
      ★ ★ 금지의 까닭은 ★ 「사는 사람이 살지 말지를 못 고른다」이므로
        ★ ★ 사는 사람이 보는 화면만 본다
    """
    bad = []
    for q in _templates():
        if q.name.startswith("admin"):
            continue
        for line in re.sub(r"<!--.*?-->", " ", _read(q), flags=re.S).split("\n"):
            for w in SPEC_FORBIDDEN:
                if w in line:
                    bad.append(f"{q.name} — 「{w}」")
    if bad:
        return False, (f"★ 금지 제원이 화면에 있다 {len(set(bad))}곳 — "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, f"금지 제원 열 항목이 화면에 없다 ({len(SPEC_FORBIDDEN)}개 확인)"



def s46_66_links_encoded() -> tuple[bool, str]:
    """★ 화면이 낸 링크에 ★ 공백·한글이 그대로 있으면 ★ 실패 (마스터 지적 08-25 · 57장).

    ★★ 왜 — ★ 마스터께서 ★ 「링크가 작동 안 한다」 하셨다.
      ★ ★ 실측 — `/listings?color_int=검정색 계열` → ★ **000 (응답 없음)**.
        ★ ★ 색 단추 ★ 21가지가 ★ 하나도 안 먹었다
    ★ ★ 템플릿 글자를 본다 — ★ `href="...?키={{ 값 }}"` 에 ★ `| url` 이 있는가
    ★★ ★ **파이썬 소스도 본다** (마스터 지적 08-25 · 오판 119) —
      ★ ★ 템플릿만 보면 ★ `f"/listings?option_group={key}"` 를 ★ 못 잡는다.
        ★ ★ 실측 — ★ 그 한 줄 때문에 ★ 배포에서 ★ 400 이 났다
    ★ ★ 값이 한글일 수 있는 키만 본다 — ★ 숫자 키(page·price_max)는 안 본다
    """
    keys = ("color_ext", "color_int", "target", "trim", "site", "q", "fuel",
            "region", "option_name", "option_group", "sell_type", "dealer")
    names = "|".join(keys)
    pat = re.compile(r'([?&](?:' + names + r')=)\{\{ ([^}|]+?) \}\}')
    # ★ 파이썬 f-string — ★ `?키={값}` 에 ★ `quote(` 가 안 붙은 것
    py = re.compile(r'([?&](?:' + names + r')=)\{([^{}]+?)\}')
    bad = []
    got = ROOT / "web" / "templates"
    for q in sorted(got.glob("*.html")) if got.is_dir() else ():
        for one in pat.finditer(_read(q)):
            bad.append(f"{q.name} — {one.group(1)}{{{{ {one.group(2).strip()} }}}}")
    for folder in ("web", "report"):
        base = ROOT / folder
        if not base.is_dir():
            continue
        for q in sorted(base.rglob("*.py")):
            for one in py.finditer(_read(q)):
                if "quote(" in one.group(2):
                    continue          # ★ 이미 인코딩한다
                bad.append(f"{q.name} — {one.group(1)}{{{one.group(2).strip()}}}")
    if bad:
        return False, (f"★ 인코딩 안 한 링크 {len(bad)}곳 — ★ `| url` 을 붙여라 — "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, "화면이 낸 링크가 다 인코딩돼 있다 (| url)"



def s46_65_verdict_fresh() -> tuple[bool, str]:
    """★ 판본이 ★ **하루 넘게** 오래됐으면 알린다 (마스터 확정 08-25 · 56장).

    ★★ 「네 시간」이 아니다 — ★ 재판정은 ★ **하루 한 번**이다.
      ★ ★ 못 돌았을 때만 ★ 네 시간 뒤 ★ 한 번 더 부른다 (`Restart=on-failure`)
    ★★ ★ 실측 08-24 — ★ 07:40 에 죽은 작업 하나가 ★ 13:00 을 막아
      ★ ★ 판본이 ★ `20260824T074027` 에서 ★ 하루 넘게 멈췄다.
      ★ ★ 그런데 ★ 아무 검사도 ★ 그것을 안 봤다 — ★ 이것이 그 자리다
    """
    import sqlite3 as _s
    from datetime import datetime, timezone

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    conn = _s.connect(str(db))
    try:
        got = conn.execute(
            "SELECT MAX(calculated_at) FROM result_score").fetchone()
    finally:
        conn.close()
    if not got or not got[0]:
        return False, "★ 판본이 하나도 없다 — 재판정이 한 번도 안 돌았다"
    try:
        seen = datetime.fromisoformat(str(got[0]))
    except ValueError:
        return False, f"판본 시각을 못 읽었다 — {got[0]!r}"
    if seen.tzinfo is None:
        seen = seen.replace(tzinfo=timezone.utc)
    hours = (datetime.now(timezone.utc) - seen).total_seconds() / 3600
    if hours >= 24:
        return False, (f"★ 판본이 ★ {hours / 24:.1f}일째 오래됐다 "
                       f"({got[0][:16]}) — ★ 재판정이 안 돌고 있다. "
                       "★ `recalc_job` 에 ★ 숨 끊긴 running 이 있는지 보라")
    return True, f"판본이 {hours:.1f}시간 전 것이다 ({got[0][:16]})"



def s46_67_sian_names_dont_clash() -> tuple[bool, str]:
    """★ 시안이 정한 이름이 ★ `app.css` 와 ★ 안 겹치는가 (마스터 확정 ㉮ · 08-24).

    ★★ 마스터 — 「★ ㉮ 로 간다.  ★ **시안 쪽에 `.v3-` 을 붙인다**.
      ★ 실제 `app.css` 는 안 건드린다」
    ★★ ★ 왜 검사가 필요한가 — ★ 08-25 에 ★ `.chg` 하나가 ★ 접두사를 안 달고 들어와
      ★ ★ `app.css` 의 `.chg`(다른 뜻)와 ★ 이름이 겹쳤다.
      ★ ★ `V11-60` 이 ★ 「값이 다르다」로 잡았으나 ★ **까닭이 이름 충돌임을 안 말했다**
    ★ ★ 이 검사는 ★ 「겹쳤다」를 ★ 곧장 말한다 — ★ 고칠 곳이 바로 보인다
    ★ `.v3-` 로 시작하면 ★ 겹칠 수 없다 — ★ 그것이 ㉮ 의 뜻이다
    """
    css = ROOT / "web" / "static" / "app.css"
    sian = ROOT / "ref" / "screens"
    if not css.is_file() or not sian.is_dir():
        return True, "app.css 나 시안이 없다 — 잴 것이 없다"
    # ★ 주석(/* … */)은 안 센다 — ★ 「이름을 바꿨다」고 적어 둔 줄이 잡히면 안 된다
    body = re.sub(r"/\*.*?\*/", " ", _read(css), flags=re.S)
    have = set(re.findall(r"\.([a-zA-Z][\w-]*)", body))
    bad = []
    for q in sorted(sian.glob("v3_*.html")):
        for sel in re.findall(r"\n\.([\w-]+)\s*\{", _read(q)):
            if sel in have:
                bad.append(f"{q.name} — .{sel}")
    if bad:
        return False, (f"★ 시안 이름이 app.css 와 겹친다 {len(bad)}곳 — "
                       "★ 시안 쪽에 `.v3-` 을 붙여라 (마스터 확정 ㉮) — "
                       + " · ".join(sorted(set(bad))[:5]))
    n = sum(len(re.findall(r"\n\.([\w-]+)\s*\{", _read(q)))
            for q in sorted(sian.glob("v3_*.html")))
    return True, f"시안 이름 {n}개가 app.css 와 안 겹친다 (충돌 0)"


CHECKS = (
    ("S43-2", "규격의 축 id 가 config 에 있는가", s43_2_axis_ids),
    ("S43-2b", "config 축 id 가 규격 이름인가", s43_2b_axis_renamed),
    ("S43-2c", "HDA 가 저장소에 없는가", s43_2c_no_hda),
    ("S43-3", "버전이 이력 마지막과 같은가", s43_3_version_matches),
    ("S44-1", "가리키는 명령서가 실제로 있는가", s44_1_order_exists),
    ("S44-2", "명령서가 하나뿐인가", s44_2_one_order),
    ("S44-3", "규격을 명령서가 가리키는가", s44_3_specs_in_order),
    ("S44-4", "명령서에 수집 범위가 있는가", s44_4_scope_written),
    ("S44-5", "명령서이 사이트를 한 가지로 적는가", s44_5_site_consistent),
    ("S45-1", "f-table 절 제목과 표가 같은가", s45_1_one_version),
    ("S45-2", "시안에 옛 배점·분모가 없는가", s45_2_mock_numbers),
    ("S45-3", "규격에 옛 총점이 없는가", s45_3_spec_totals),
    ("S45-4", "배점표가 config 에서 생성한 것과 같은가", s45_4_table_generated),
    ("S45-5", "규격이 배점을 손으로 적지 않는가", s45_5_no_axis_scores),
    ("S46-21", "시안 한 파일에 화면이 하나인가", s46_21_one_screen_per_file),
    ("S46-22", "시안 절 차례가 화면과 같은가", s46_22_section_order),
    ("S46-23", "빈 site_query 가 없는가", s46_23_site_query_filled),
    # ★ WARN — ★ 「아직 안 한 것」을 세는 검사다.  ★ 마스터 회선이라야 지워진다.
    #   ★ 이것 하나로 ★ 검사가 늘 빨간불이면 ★ 진짜 실패가 묻힌다 (명령서 26장)
    ("S46-24", "facet 미확인 차종이 없는가", s46_24_facet_unconfirmed, "warn"),
    ("S46-30", "INDEX 가 docs 를 다 가리키는가", s46_30_index_covers_docs, "warn"),
    ("S46-31", "규격이 있는 사이트가 config 에 있는가", s46_31_spec_sites_in_config),
    ("S46-32", "생성물이 최신인가", s46_32_generated_fresh),
    # ★ 마스터가 가장 원하시는 것 — ★ 처음부터 실패로 둔다 (명령서 31-3)
    ("S46-36", "폐기된 요구가 규격에 안 살아 있는가", s46_36_dropped_not_alive),
    ("S46-40", "「진행」인 요구의 문서가 바뀌었는가", s46_40_progress_docs_changed, "warn"),
    ("S46-41", "사이트 status 가 규격의 셋 안인가", s46_41_site_status_known),
    ("S46-45", "제원이 목록에 안 나오는가", s46_45_spec_not_in_list),
    ("S46-46", "금지 제원 열 항목이 화면에 없는가", s46_46_spec_forbidden_ten),
    ("S46-65", "판본이 하루 넘게 오래되지 않았는가", s46_65_verdict_fresh),
    ("S46-66", "화면이 낸 링크가 인코딩돼 있는가", s46_66_links_encoded),
    ("S46-67", "시안 이름이 app.css 와 안 겹치는가", s46_67_sian_names_dont_clash),
)


def run() -> int:
    """★ 돌려서 ★ fatal 실패 수를 돌려준다.  ★ warn 은 ★ 세지 않는다.

    ★ 「아직 안 한 것」을 세는 검사가 ★ 늘 빨간불이면 ★ 진짜 실패가 묻힌다
    """
    bad = warn = 0
    for row in CHECKS:
        code, name, fn = row[0], row[1], row[2]
        kind = row[3] if len(row) > 3 else "fatal"
        ok, msg = fn()
        if ok:
            head = "OK  "
        elif kind == "warn":
            head = "warn"
            warn += 1
        else:
            head = "★ 실패"
            bad += 1
        print(f"  {head} {code} {name} — {msg}")
    if warn:
        print(f"  ★ warn {warn}건 — 「아직 안 한 것」이다.  ★ 실패로 세지 않는다")
    return bad

# ★ __main__ 블록을 두지 않는다 (V4-23) — 「import 만으로 아무 일도 안 일어나야
#   한다.  실행은 run.py · tools/ 에서만」이 규격이다.
#   ★ 돌리려면  python3.11 -c "from validate.v0_guide import run; \
#                              raise SystemExit(1 if run() else 0)"
