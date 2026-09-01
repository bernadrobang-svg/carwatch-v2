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
import ssl
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
        `INDEX.md` 파일표            ★ **줄 수 · 개정 수**다 (자동 생성 · 08-29).
                                   ★ 「| `guide/03_이력.md` ★ | 910 | 675 |」에서
                                   ★ ★ 910 은 줄 수 · 675 는 개정 수다 — 배점이 아니다.
                                   ★ 문서가 자랄 때마다 ★ 이 칸이 우연히 옛 총점과
                                   ★ ★ 같아진다.  ★ 표의 꼴로 가른다
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
        "guide/03_이력.md`",      # INDEX — 850 은 줄 수 (자동 생성 · 08-30)
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
        # ★ `INDEX.md` 의 자동 생성 파일표 — ★ 「| `경로.md` … | 줄수 | 개정수 |」.
        #   ★ 그 두 칸은 ★ 세어서 적은 수다 — ★ 배점이 아니다 (08-29)
        idx_row = re.compile(r"^\|\s*`[^`]+\.md`[^|]*\|\s*\d+\s*\|\s*\d+\s*\|\s*$")
        for i, line in enumerate(_read(q).split("\n"), 1):
            if any(w in line for w in ALLOW_TEXT):
                continue
            if q.name == "INDEX.md" and idx_row.match(line.strip()):
                continue
            # ★ `CHECKS.md` 도 ★ 자동 생성이다 — ★ 표 칸은 ★ **검사 건수**지
            #   ★ 배점이 아니다 (08-29 · `| ② 죽은 검사 … | 495 | 개발측 |`)
            if q.name == "CHECKS.md" and line.strip().startswith("|"):
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
    # ★ 개정이 1,000 을 넘었다 (08-30) — ★ 세 자리로 묶어 두면 영영 999 로 읽는다
    nums = [int(x) for x in re.findall(r"^\| (\d{3,}) \|", hist, re.M)]
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
# ★★ 08-25 마스터 지적 — 「★ 항목이 있다고 ★ 시안과 같냐.  ★ **위치 관점**에서 비교해 봐」
#   ★★ ★ 전에는 ★ 상세 ★ **한 쌍만** 봤다 — ★ 그래서 ★ 목록 거르개가 ★ 통과했다.
#     ★ ★ 「있다」와 ★ 「같다」는 ★ 다르다 — ★ 여덟 쌍을 ★ 다 본다
# ★★★ 08-26 — ★ 마스터께서 ★ v4m 을 확정하셨다 (「★ 그래 관심 이걸로 가자」).
#   ★ ★ **`ref/screens/v4m_*` 여덟 장이 정본이다.**  ★ `v3_*` 는 ★ 옛 판이다
#   ★ ★ 옛 판을 대조하면 ★ 「새 시안대로 고쳤는데 검사가 빨개진다」가 된다
SIAN_PAIRS = (
    ("v4m_detail_시안.html", "detail.html"),
    ("v4m_listings_시안.html", "listings.html"),
    ("v4m_track_시안.html", "track.html"),
    ("v4m_notready_시안.html", "notready.html"),
    ("v4m_dashboard_시안.html", "dashboard.html"),
    ("v4m_admin_시안.html", "admin.html"),
    ("v4m_watch_시안.html", "watch.html"),
    ("v4m_compare_시안.html", "compare.html"),
)
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
                re.findall(r'<div class="(?:v3-|v4-|v4m-)?lbl">([^<]+)</div>',
                           _read(q))
                if "무엇을 하는 곳인가" not in x]
        # ★★ 한 화면이 ★ 갈래 둘을 가질 수 있다 (`{% if %}` / `{% if ! %}`) —
        #   ★ ★ 그때는 ★ 같은 절이 ★ 글자로 두 번 나온다.  ★ 실제로 그려지는 것은 하나다
        #   ★ ★ 그래서 ★ **차례를 지키며 중복을 접는다**
        got: list = []
        for x in _h_tags(_read(t), "h3"):
            one = _bare(x)
            if one not in got:
                got.append(one)
        seen += 1
        if not want:
            # ★★ 시안이 ★ 절을 안 밝힌 것은 ★ 「절이 없는 화면」이다 —
            #   ★ ★ `v3_watch` · `v3_compare` 가 그렇다.  ★ 견줄 것이 없다
            continue
        # ★★ 08-26 — ★ v4m 시안이 ★ 가운데 절을 ★ 「… 4~10절 (…)」로 ★ 줄여 적는다.
        #   ★ ★ 그것은 ★ 「절이 없다」가 아니라 ★ 「여기 적기를 줄였다」는 표시다.
        #   ★ ★ 그때는 ★ **차례만** 본다 — ★ 시안이 적은 절이 ★ 그 차례대로 나오는가.
        #     ★ 줄이지 않은 시안은 ★ 여전히 ★ **개수까지** 같아야 한다
        folded = [x for x in want if x.startswith("…") or x.startswith("...")]
        want = [x for x in want if x not in folded]
        if folded:
            at = 0
            for a in want:
                if a in got[at:]:
                    at = got.index(a, at) + 1
                else:
                    bad.append(f"{page} 「{a}」가 차례에 없다 (시안이 줄여 적었다)")
                    break
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



def _sian_files(sian: Path) -> list:
    """시안 파일 전부.  ★ `v3_` 뿐 아니라 ★ `v4m_` 도 본다 (08-25).

    ★★ 08-25 에 ★ `v4m_watch_시안.html` 이 들어왔다 — ★ 모바일 기준 판이다.
      ★ ★ `v3_` 만 훑으면 ★ 새 시안이 ★ **검사 밖에 있게 된다**
    """
    return sorted(sian.glob("v3_*.html")) + sorted(sian.glob("v4m_*.html"))


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
    for q in _sian_files(sian):
        for sel in re.findall(r"\n\.([\w-]+)\s*\{", _read(q)):
            if sel in have:
                bad.append(f"{q.name} — .{sel}")
    if bad:
        return False, (f"★ 시안 이름이 app.css 와 겹친다 {len(bad)}곳 — "
                       "★ 시안 쪽에 `.v3-` 을 붙여라 (마스터 확정 ㉮) — "
                       + " · ".join(sorted(set(bad))[:5]))
    n = sum(len(re.findall(r"\n\.([\w-]+)\s*\{", _read(q)))
            for q in _sian_files(sian))
    return True, f"시안 이름 {n}개가 app.css 와 안 겹친다 (충돌 0)"



# ★★ v4m 「지켜야 하는 것」에 적힌 항목 (ref/screens/v4m_watch_시안.html).
#   ★ 「나머지는 목록 카드와 똑같이 담는다」 — ★ 열일곱 가지를 그대로 옮겼다
V4M_WATCH_ITEMS = (
    ("축 넷", "r.listing.bars"),
    ("등급", "grade_label"),
    ("차종", "target_label"),
    ("트림 전체", "r.listing.trim"),
    ("연식", "year_month"),
    ("주행", "mileage_km"),
    ("외장색", "color_ext"),
    ("내장색", "color_int"),
    ("딜러", "dealer_shop"),
    ("사이트", "site_badge"),
    ("게시 상태", "status_label"),
    ("값", "price_won"),
    ("전 값", "price_at_add_won"),
    ("시세차", "gap_text"),
    ("판정 다섯", "axis_chips"),
    ("순위", "r.listing.rank"),
    ("점수", "denominator"),
    ("원문 문", "encar_url"),
    ("담은 날", "added_at"),
    ("담은 뒤 바뀐 것", "chg_text"),
    # ★★ 08-26 — ★ 가이드가 시안을 고쳤다 (개정 751 · 마스터 확정 17 「비교→관심」).
    #   ★ 「비교 고르기를 두지 않는다」는 ★ 물렸다 — ★ 사진 왼쪽 위에 네모를 둔다
    ("비교 네모", "data-cmp"),
    ("비교로 가는 문", 'action="/compare"'),
)


def s46_68_watch_is_mobile_first() -> tuple[bool, str]:
    """★★★ 관심이 ★ v4m 시안대로 ★ 모바일 기준 카드인가 (마스터 확정 08-25).

    ★★ 마스터 — 「★ 화면 ★ **모바일 기준으로 다시** (v4m 시안)」
    ★★ ★ 시안 「지켜야 하는 것」이 ★ 잴 수 있게 적혀 있다 — ★ 그대로 잰다
      ★ ① 표가 아니라 ★ 카드다 — ★ 표를 좁히면 ★ 값이 이름표를 잃는다
      ★ ② 카드 맨 앞이 ★ 「담은 뒤 무엇이 바뀌었나」다 — ★ 그것이 이 화면의 이유다
      ★ ③ 폭 세 구간이 ★ app.css 에 있다 (≤359 · ≥640 · ≥1024)
      ★ ④ ★★ **좁다고 정보를 빼지 않는다** — ★ 좁은 폭에서 ★ `display:none` 이 없다
      ★ ⑤ 열일곱 가지를 ★ 다 담는다 — ★ 「목록 카드와 똑같이」
    ★ 금지 — ★ 카드를 옆으로 붙이는 것 (한 줄에 늘 하나)
    """
    sian = SCREENS / "v4m_watch_시안.html"
    tpl = TEMPLATES / "watch.html"
    css = ROOT / "web" / "static" / "app.css"
    if not sian.is_file():
        return True, "v4m 관심 시안이 아직 없다 — 잴 것이 없다"
    if not tpl.is_file() or not css.is_file():
        return False, "watch.html 이나 app.css 가 없다"
    body, style = _read(tpl), _read(css)
    bad = []
    # ① 카드다 — ★ 매물 표가 아니다
    if re.search(r'<table class="rows"', body):
        bad.append("아직 표다 — 카드가 아니다")
    if "kcard" not in body:
        bad.append("카드가 없다 (kcard)")
    # ② 카드 맨 앞 줄
    first = body.split("kcard\">", 1)[-1][:400]
    if "kchg" not in first:
        bad.append("카드 맨 앞이 「담은 뒤 바뀐 것」이 아니다")
    # ③ 폭 세 구간
    for want in ("max-width:359px", "min-width:640px", "min-width:1024px"):
        if want not in style.replace(" ", ""):
            bad.append(f"폭 구간이 없다 — {want}")
    # ④ ★ 좁다고 감추지 않는다
    for blk in re.findall(r"@media[^{]*max-width:\s*(?:359|639)px[^{]*\{(.*?)\n\}",
                          style, re.S):
        for rule in re.findall(r"\.w[\w-]*[^{}]*\{([^{}]*)\}", blk):
            if "display:none" in rule.replace(" ", ""):
                bad.append("좁은 폭에서 정보를 감춘다 (display:none)")
    # ⑤ 열일곱 가지
    miss = [n for n, tok in V4M_WATCH_ITEMS if tok not in body]
    if miss:
        bad.append("빠진 것 " + " · ".join(miss))
    # ⑥ 단추 44px 이상
    if "min-height:44px" not in style.replace(" ", ""):
        bad.append("단추가 44px 이상이 아니다")
    if bad:
        return False, ("★ 관심이 v4m 시안과 다르다 — " + " · ".join(bad[:5]))
    return True, (f"카드 · 폭 세 구간 · {len(V4M_WATCH_ITEMS)}가지를 다 담는다 "
                  "· 좁아도 안 감춘다")



def s46_74_rows_per_page() -> tuple[bool, str]:
    """★★★ 한 쪽에 ★ **30장**인가 (마스터 확정 08-26 · `UI_REVIEW` 16장).

    ★★ 마스터 — 「★ **30개 해**」.  ★ 가이드 안(50장 그대로)은 ★ 물렸다
    ★★ ★ 수를 ★ **규격에서 읽는다** — ★ 코드에 박지 않는다 (규칙 1).
      ★ ★ 여기에 `30` 을 적어 두면 ★ 마스터가 수를 바꾸실 때
        ★ ★ 검사가 ★ **옛 수를 지키는 쪽**이 된다
    ★★ ★ 네 화면이 ★ 같은 수를 쓰는가도 본다 —
      ★ 「★ 관심·추적·미판정도 같이 30장.  ★ 화면마다 다르면 헷갈린다」
    ★ 금지 — ★ 카드에서 무엇을 빼서 크기를 줄이는 것.
      ★ 마스터 「보여지는 정보는 빼지 마라」.  ★ 줄인 것은 ★ **장 수**다
    """
    doc = ROOT / "docs" / "UI_REVIEW.md"
    cfg = ROOT / "config" / "web.json"
    if not doc.is_file() or not cfg.is_file():
        return False, "UI_REVIEW.md 나 config/web.json 이 없다"
    body = _read(doc)
    want = re.search(r"목록은\s*★?\s*\**한 쪽에\**\s*★?\s*\**(\d+)장", body)
    if not want:
        # ★ 규격이 안 적었으면 ★ 우리가 정하지 않는다 — ★ 보고한다 (규칙 2)
        return True, "UI_REVIEW 에 한 쪽 장 수가 없다 — 잴 것이 없다"
    n = int(want.group(1))
    try:
        got = int(json.loads(_read(cfg))["rows_per_page"])
    except (ValueError, KeyError):
        return False, "config/web.json 에 rows_per_page 가 없다"
    bad = []
    if got != n:
        bad.append(f"config rows_per_page {got} ≠ 규격 {n}")
    # ★ 네 화면이 ★ 같은 자리에서 읽는가 — ★ 따로 박아 두면 ★ 갈린다
    build = _read(ROOT / "report" / "screens" / "build.py")
    for fn, mark in (("view_watch", "관심"), ("view_track", "추적"),
                     ("_unmatched_rows", "미판정")):
        i = build.find(f"def {fn}(")
        if i < 0:
            bad.append(f"{mark} — {fn} 이 없다")
            continue
        j = build.find("\ndef ", i + 1)
        if 'rows_per_page' not in build[i:j if j > 0 else len(build)]:
            bad.append(f"{mark} — 한 쪽 장 수를 config 에서 안 읽는다")
    if bad:
        return False, "★ 한 쪽 장 수가 어긋난다 — " + " · ".join(bad)
    return True, f"목록·관심·추적·미판정이 다 한 쪽 {n}장 (규격에서 읽는다)"



def s46_75_v4m_common() -> tuple[bool, str]:
    """★★★ v4m 여덟 장 ★ 공통 규칙 (마스터 확정 08-26 — 「그래 관심 이걸로 가자」).

    ★★ 가이드가 적은 ★ 「지킬 것 (여덟 장 공통)」을 ★ 그대로 잰다 —
      ★ ① 맨 위에 ★ 「이 화면은 무엇은 하는 곳인가」 ＋ ★ 「~와 다르다」
      ★ ② 아래 탭 — ★ 640 아래에서 ★ 상단 메뉴가 ★ 바닥에 붙는다
      ★ ③ 단추 ★ 44px 이상
      ★ ④ 카드를 ★ 옆으로 붙이지 않는다 — ★ 한 줄에 늘 하나
    ★★ ★ 「~와 다르다」가 왜 필요한가 — ★ 관심·추적·비교가 ★ 서로 닮았다.
      ★ ★ 「여기는 무엇이 다른가」를 안 적으면 ★ 같은 화면이 셋으로 보인다
    ★ 링크의 한글 인코딩은 ★ `S46-66` 이 따로 잰다 — ★ 여기서 두 번 안 센다
    """
    css = ROOT / "web" / "static" / "app.css"
    if not css.is_file():
        return False, "app.css 가 없다"
    # ★ 빈칸·줄바꿈을 다 지운다 — ★ `.replace(" ", "")` 만으로는 ★ 줄바꿈이 남는다
    style = re.sub(r"\s+", "", _read(css))
    bad = []
    for _sian, page in SIAN_PAIRS:
        t = TEMPLATES / page
        if not t.is_file():
            bad.append(f"{page} 가 없다")
            continue
        body = _read(t)
        if "무엇을 하는 곳인가" not in body:
            bad.append(f"{page} — 머리 상자가 없다")
        # ★ 「다르다」·「다릅니다」 어느 쪽이든 받는다 — ★ 글투는 화면 몫이다
        if "다르다" not in body and "다릅니다" not in body:
            bad.append(f"{page} — 「~와 다르다」가 없다")
    # ★ 아래 탭 — ★ 640 아래에서 ★ `.nav` 가 바닥에 붙는가
    if "@media(max-width:639px){.nav{position:fixed;bottom:0" not in style:
        bad.append("640 아래에서 상단 메뉴가 아래 탭이 아니다")
    if "min-height:44px" not in style:
        bad.append("단추가 44px 이상이 아니다")
    if bad:
        return False, "★ v4m 공통 규칙이 어긋난다 — " + " · ".join(bad[:5])
    return True, (f"여덟 장이 머리 상자 · 「~와 다르다」 · 아래 탭 · 44px 를 지킨다")



def s46_76_collectors_keep_raw() -> tuple[bool, str]:
    """★★★ 사이트 수집기가 ★ 원문을 ★ `raw_response` 에 남기는가 (명령서 3-2 필수).

    ★★ 명령서 — 「★ ★ **`raw_response` 에는 남긴다** — ★ 갈래를 넓히시면 ★ 다시 판다.
      ★ ★ 다시 받을 일이 없다.  ★ 그것이 ★ 「보관만 한다」는 뜻이다」
    ★★★ ★ 실측 08-26 — ★ 열 도구 가운데 ★ **하나도 안 남기고 있었다.**
      ★ ★ `SELECT site, COUNT(*) FROM raw_response GROUP BY site` 가
        ★ ★ `encar` ★ 하나뿐이었다.  ★ 셋은 ★ 주석에 「남는다」고 ★ **적어만** 두었다
      ★ ★ 그래서 ★ 파싱이 틀리면 ★ 다시 받는 수밖에 없었다 — ★ KB 는 ★ 그것이 엿새다
    ★ 이 검사는 ★ 「부르는가」만 본다 — ★ 「실제로 들어갔는가」는 ★ `V2-01` 이 센다

    ★★★★★ 09-01 마스터 지시 — ★ **원본이 파일로 뒤집혔다** (`ARCHITECTURE_20260830.md` 9장).
      ★ 마스터 — 「★ **받기 걸음은 파일만 쓴다.  ★ DB 를 안 연다** — 잠금이 아예 안 생긴다.
        ★ ★ 넣기 걸음은 그 폴더를 읽어 ★ `raw_response` ＋ `core_listing` 에 넣는다」
      ★★ 그러므로 ★ **`store/rawfile.save` 도 ★ 「원문을 남긴다」**다 —
        ★ ★ 오히려 ★ **그쪽이 원본**이고 ★ `raw_response` 는 ★ 사본이다.
      ★ ★ 실측 09-01 — ★ 내가 한 건마다 DB 에 쓰다가 ★ `check_all` 이
        ★ ★ **`database is locked`** 로 통째로 죽었다.  ★ 그것이 이 뒤집힘의 까닭이다
    """
    tools = ROOT / "tools"
    if not tools.is_dir():
        return False, "tools/ 가 없다"
    bad, seen = [], 0
    # ★ 셋 중 하나면 된다 — ★ 파일(새 판) · `save_site_raw`·`save_raw`(옛 판)
    keeps = ("rawfile", "save_file", "save_site_raw", "save_raw")
    for q in sorted(tools.glob("collect_*.py")):
        # ★ 엔카는 ★ `collect/runner.py` 가 ★ `save_raw` 로 남긴다 — ★ 결이 다르다
        body = _read(q)
        if not any(k in body for k in keeps):
            bad.append(q.name)
        seen += 1
    if bad:
        return False, ("★ 원문을 안 남기는 수집기 — " + " · ".join(bad)
                       + " (명령서 3-2 필수)")
    return True, f"수집기 {seen}개가 다 원문을 남긴다"



def s46_115_run_screen_still() -> tuple[bool, str]:
    """★★★★ 시키는 화면이 ★ **스스로 안 바뀌는가** (UI_REVIEW 25-1 · 개정 837).

    ★★ 마스터 — 「★ 관리에 실행 지시 큐는 ★ 5초마다 리로드 되니
      ★ 내가 작업 지시를 못 하잖아.  ★ 작업 지시와 모니터링을 분리해」
    ★ `/admin/run` 은 ★ 시키는 자리다 — ★ 고르는 동안 가만히 있어야 한다.
    ★ 도는 것을 보는 자리는 ★ `/admin/status` 다 — ★ 거기만 갱신한다
    """
    src = _read(ROOT / "web" / "views.py")
    bad = []
    if "admin_run.html" in src:
        # ★ `admin_run.html` 을 내는 자리가 ★ 갱신 초를 넘기면 실패다
        i = src.find('"admin_run.html"')
        tail = src[i:i + 500]
        if "refresh_sec=0" not in tail:
            bad.append("/admin/run 이 스스로 갱신한다 (refresh_sec 가 0 이 아니다)")
    tpl = _read(ROOT / "web" / "templates" / "admin_run.html")
    if "초</strong>마다 스스로 갱신" in tpl:
        bad.append("admin_run.html 이 아직 「스스로 갱신됩니다」라 적는다")
    if "/admin/status" not in tpl:
        bad.append("시키는 화면에 「진행 보기」가 없다")
    st = _read(ROOT / "web" / "templates" / "admin_status.html")
    if "/admin/run" not in st:
        bad.append("보는 화면에 「지시하러 가기」가 없다")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, "시키는 화면은 안 바뀌고 · 보는 화면만 갱신한다"


def s46_125_sort_axes_really_sort() -> tuple[bool, str]:
    """★★★★ 고른 정렬 축이 ★ **정말 먹는가** (시험자 #101 · 마스터 지시 4).

    ★★ 시험자 — 「★ `grade`·`dom` 이 ★ `rank` 와 ★ 같은 순서다」
    ★ 까닭이었던 것 — ★ `ORDER_HEAD`(순위 없음을 뒤로)가 ★ 고른 축보다 앞서서
      ★ ★ 고른 축이 ★ 그 안에서만 갈렸다.  ★ 08-29 에 `first` 를 앞으로 옮겼다.
    ★★ 이 검사가 막는 것은 ★ **두 가지**다 —
      ① 화면이 내놓는 열쇠가 ★ `ORDER_SQL` 에 없어 ★ 조용히 `rank` 로 떨어지는 것.
         ★ ★ 화면은 단추를 보여 주는데 ★ 눌러도 아무 일이 없다
      ② 5단을 다시 섞어 ★ 고른 축이 ★ 또 안 보이게 되는 것
    ★ 실제 DB 로 재지 않는다 — ★ 여기서는 ★ **뼈대**만 본다 (검사는 DB 없이도 돈다)
    """
    from web.views import ORDER_MENU

    from report.screens.build import ORDER_HEAD, ORDER_SQL, order_clause

    bad = []
    for key, label in ORDER_MENU:
        if key not in ORDER_SQL:
            bad.append(f"「{label}」({key}) 가 ORDER_SQL 에 없다 — 눌러도 rank 다")
            continue
        clause = order_clause(key)
        first = ORDER_SQL[key]
        # ★ 고른 축이 ★ `ORDER_HEAD` 보다 ★ **앞**에 있어야 한다
        if clause.find(first) > clause.find(ORDER_HEAD):
            bad.append(f"「{label}」({key}) 가 ORDER_HEAD 뒤에 있다")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, f"정렬 축 {len(ORDER_MENU)}개가 다 ORDER_HEAD 앞에 온다"


def s46_118_heart_has_anchor() -> tuple[bool, str]:
    """★★★★ 하트가 ★ **자기 카드 안**에 앉는가 (UI_REVIEW 26-1 · 시험자 119~121).

    ★★ 시험자 — 「★ 하트 30개가 ★ 다 `y=4` 에 쌓여 있다」
    ★ 까닭 — ★ `.heart` 가 `position:absolute` 인데 ★ 조상이 전부 `static` 이라
      ★ ★ 기준이 ★ **화면 전체**가 됐다.  ★ 그래서 카드마다가 아니라
      ★ ★ 한 자리에 ★ 서른 개가 겹쳤다.
    ★ 세 가지가 다 있어야 한다 —
      ① `.heart` 에 `position:absolute`   ② 기준 상자 `.cardbody { position:relative }`
      ③ `.heart` 에 `z-index` (없으면 ★ 카드 뒤로 들어가 ★ 안 눌린다)
    ★ ★ 그리고 ★ 목록 틀이 ★ 그 `.cardbody` 를 ★ 실제로 써야 한다
    """
    css = re.sub(r"/\*.*?\*/", " ", _read(ROOT / "web" / "static" / "app.css"),
                 flags=re.S)
    bad = []
    hearts = re.findall(r"(?m)^\.heart\s*\{([^}]*)\}", css)
    if not hearts:
        bad.append("`.heart` 규칙이 없다")
    elif len(hearts) > 1:
        # ★ 두 벌이면 ★ 뒤엣것이 앞엣것의 값을 덮어 ★ 조용히 갈라진다 (S46-121)
        bad.append(f"`.heart` 규칙이 {len(hearts)}곳이다 — 하나여야 한다")
    else:
        body = hearts[0]
        if "position:absolute" not in body.replace(" ", ""):
            bad.append("`.heart` 에 position:absolute 가 없다")
        if "z-index" not in body:
            bad.append("`.heart` 에 z-index 가 없다 — 카드 뒤로 들어가 안 눌린다")
    anchor = re.findall(r"(?m)^\.cardbody\s*\{([^}]*)\}", css)
    if not anchor:
        bad.append("기준 상자 `.cardbody` 규칙이 없다")
    elif not any("position:relative" in a.replace(" ", "") for a in anchor):
        bad.append("`.cardbody` 에 position:relative 가 없다")
    tpl = _read(ROOT / "web" / "templates" / "listings.html")
    if "cardbody" not in tpl:
        bad.append("목록 틀이 `.cardbody` 를 안 쓴다")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, "하트는 카드(.cardbody)를 기준으로 앉고 z-index 를 갖는다"


def s46_121_header_rule_in_one_place() -> tuple[bool, str]:
    """★★★★ 머리띠 규칙이 ★ **한 곳에만** 있는가 (UI_REVIEW 27장 · 개정 851).

    ★★ 마스터 — 「★ 화면마다 위·아래가 바뀐다」
    ★ 까닭은 ★ `body.s-… header { … }` 가 ★ 화면 수만큼 적혀 있던 것이다 —
    ★ 08-29 실측 21곳 · 글자는 같고 ★ `z-index` 만 30/20 으로 갈렸다.
    ★ 화면별로 다시 적지 않는다 — ★ 공통 `header` 하나로 둔다.
    ★ 정말 그 화면만 달라야 하면 ★ 규격에 적고 나서 넣는다
    """
    css = _read(ROOT / "web" / "static" / "app.css")
    # ★ 주석은 규칙이 아니다 — ★ 먼저 걷어낸다 (L-3 · 개정 849)
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    per = re.findall(r"body\.s-[\w-]+[^{}]*\bheader\b[^{}]*\{", css)
    common = re.findall(r"(?m)^\s*header\s*\{", css)
    if per:
        return False, (f"★ 화면별 header 규칙이 {len(per)}곳 남았다 — "
                       f"{' · '.join(sorted({x.strip() for x in per})[:3])}")
    if len(common) != 1:
        return False, f"★ 공통 header 규칙이 {len(common)}개다 — 하나여야 한다"
    return True, "머리띠는 공통 header 하나뿐이다 (화면별 0곳)"


def s46_116_reasons_in_plain_words() -> tuple[bool, str]:
    """★★★★ 사유에 ★ **쉬운 말**이 있는가 (UI_REVIEW 25-3 · 개정 837).

    ★★ 마스터 — 「★ 사유에 대한 설명이 없어서 ★ 내가 이해를 못 하겠어」
    ★ 「`raw_missing`」이 무슨 뜻인지 ★ 아실 까닭이 없다.
    ★ 단계 이름(S9…)을 ★ 앞에 내지 않는다 — ★ 뒤에 작게
    """
    import sys as _sys

    if str(ROOT) not in _sys.path:
        _sys.path.insert(0, str(ROOT))
    try:
        from collect.pipeline import REASON_PLAIN, web_reasons
    except ImportError:
        return False, "★ REASON_PLAIN 이 없다 (collect/pipeline.py)"
    miss = [r for r in web_reasons() if not (REASON_PLAIN.get(r) or ("", ""))[1]]
    if miss:
        return False, "★ 쉬운 말이 없는 사유 — " + " · ".join(miss[:6])
    tpl = _read(ROOT / "web" / "templates" / "admin_run.html")
    if "r.plain" not in tpl:
        return False, "★ 화면이 쉬운 말을 안 낸다 (admin_run.html)"
    # ★ 단계 이름이 앞에 나오면 실패 — ★ 뒤에 작게(`dim`) 있어야 한다
    if "from_step" in tpl and 'class="dim">— {{ r.from_step }}' not in tpl:
        return False, "★ 단계 이름이 앞에 나온다 — 뒤에 작게 두어야 한다"
    return True, f"사유 {len(web_reasons())}가지에 다 쉬운 말이 있다"


def s46_120_registry_key_matches() -> tuple[bool, str]:
    """★★★★★ 등록부의 ★ **감사 열쇠**가 ★ 목록 열쇠와 같은가 (개정 841 · #82).

    ★★ 시험자 실측 — 「셋 다 303 인데 ★ 미분류 319 → 319 ·
      ★ 키 꼴이 다르다 — ★ 목록은 `detail:…` 인데 ★ 감사는 `seed.detail:…` 다」
      ★ ★ 저장은 되는데 ★ **다른 열쇠로 저장돼** ★ 사람이 둘을 못 맞췄다.
    ★ 마스터 판정 — ★ 「`seed.` 를 떼라.  ★ 감사 세 줄은 그대로」.
    ★ 그래서 ★ **새로 쓰는 것**만 본다 — ★ 옛 이력은 안 센다
    """
    src = _read(ROOT / "store" / "admin.py")
    bad = []
    if 'f"seed.{key}"' in src:
        bad.append("classify_field 가 아직 seed. 를 붙인다 (store/admin.py)")
    if "_under_seed" not in src:
        bad.append("맨 열쇠를 담긴 자리로 푸는 곳이 없다 (_under_seed)")
    if bad:
        return False, "★ " + " · ".join(bad)
    # ★ 옛 이력이 안 깨지는지 — ★ 되돌리기가 옛 열쇠를 그대로 받아야 한다
    import sqlite3 as _sq

    db = ROOT / "carwatch.db"
    old = 0
    if db.is_file():
        try:
            conn = _sq.connect(str(db))
            old = conn.execute(
                "SELECT COUNT(*) FROM config_change"
                " WHERE file='field_usage.json' AND key_path LIKE 'seed.%'"
            ).fetchone()[0]
            conn.close()
        except _sq.Error:
            old = 0
    return True, (f"감사 열쇠가 목록과 같다 (옛 `seed.` 이력 {old}줄은 "
                  "그대로 두고 되돌리기도 받는다)")


def s46_123_toss_palette_only() -> tuple[bool, str]:
    """★★★★ 토스 표에 ★ **없는 색**이 `app.css` 에 있는가 (UI_REVIEW 29장 · 개정 851).

    ★★ 마스터 — 「이제 디자인 스타일을 토스 스타일로 바꾸어」
      ★ 08-29 정정 — 「색과 버튼을 토스 스타일로 하고 ★ 폰트 크기와 여백은 현 스타일로」
    ★ 규격 「지킬 것」 — 「색은 위 표 여덟뿐이다.  ★ 새 색을 만들지 않는다」
    ★★ 그래서 두 가지를 본다 —
      ① `:root` 가 쓰는 색이 ★ 규격 표 안에 있는가
      ② `:root` **밖**에 ★ 색이 박혀 있지 않은가 (그림자만 뺀다)
    ★ ② 가 중요하다 — ★ 08-30 실측 — ★ `:root` 밖에 ★ 색이 **152곳** 박혀 있었다.
      ★ ★ 규격은 ★ 「색은 app.css 맨 위 :root 한 곳에만 있다」고 적었지만
      ★ ★ 실제로는 ★ 그렇지 않았다.  ★ 122곳은 이미 있는 토큰과 같은 값이라
      ★ ★ `var()` 로 바꿨고 · ★ 30곳(rgba)은 토큰으로 옮겼다.
    ★ 그림자는 ★ 색이 아니라 ★ 깊이다 — ★ 검정 반투명만 남긴다 (토스 「테두리 대신 그림자」)
    """
    OK = {"#ffffff", "#f9fafb", "#e5e8eb", "#d1d6db", "#191f28",
          "#8b95a1", "#b0b8c1", "#3182f6", "#00c471", "#f04452"}
    css = _read(ROOT / "web" / "static" / "app.css")
    # ★ 주석은 규칙이 아니다 — ★ 먼저 걷어낸다 (L-3 · 개정 849)
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    m = re.search(r"(?m)^:root\s*\{[^}]*\}", css)
    if not m:
        return False, "★ :root 를 못 찾았다"
    root, rest = m.group(0), css.replace(m.group(0), "")
    bad = []
    off = sorted({c.lower() for c in re.findall(r"#[0-9a-fA-F]{3,8}\b", root)} - OK)
    if off:
        bad.append(f":root 에 표 밖의 색 {len(off)}가지 — {' · '.join(off[:5])}")
    stray = sorted(set(re.findall(r"#[0-9a-fA-F]{3,8}\b", rest)))
    if stray:
        bad.append(f":root 밖에 박힌 색 {len(stray)}가지 — {' · '.join(stray[:5])}")
    # ★ 그림자만 남는다 — ★ 검정 반투명이 아닌 rgba 는 색이다
    rgba = [x for x in re.findall(r"rgba?\([^)]*\)", rest)
            if not re.match(r"rgba?\(\s*0\s*,\s*0\s*,\s*0\s*,", x)]
    if rgba:
        bad.append(f":root 밖에 rgba 색 {len(set(rgba))}가지 — "
                   f"{' · '.join(sorted(set(rgba))[:3])}")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, f"색은 :root 의 토스 {len(OK)}색뿐이다 (그림자 제외)"


def s46_122_shared_fragments() -> tuple[bool, str]:
    """★★★★ 머리·발이 ★ **한 곳에만** 있는가 (UI_REVIEW 28장 · 개정 851).

    ★★ 마스터 — 「HTML 중에 공통으로 쓸 것들을 표준화하고 공통 모듈로 만들어 쓰게 해」
    ★★★ 규격은 ★ 「`_head.html`·`_foot.html` 을 ★ include 로 쓰라」고 적었다.
      ★ 그런데 ★ 실측 08-29 — ★ 머리·발은 ★ **이미 한 곳**이다.
      ★ ★ `base.html` 이 머리·발을 갖고 · ★ `_page.html` 이 그것을 `extends` 하며
      ★ ★ `web/views.page()` 가 ★ **모든 화면**을 그것으로 감싼다.
      ★ ★ 틀 39개 중 ★ `<header>`·`<!DOCTYPE>` 를 가진 것은 ★ `base.html` 뿐이다
      ★ ★ (`watch_invite.html` 의 `<header>` 는 ★ 카드 속 머리지 ★ 쪽 머리가 아니다).
    ★ 그러므로 ★ 이 검사는 ★ **뜻**을 지킨다 — ★ 「머리·발이 한 곳인가」.
      ★ ★ 낱말대로 「include 를 쓰는가」로 재면 ★ 39곳이 다 실패하는데
      ★ ★ 그것은 ★ 고칠 것이 없는 실패다.  ★ 가이드께 이 어긋남을 올렸다.
    ★ 함께 본다 — ★ 조각(`_*.html`)이 ★ 조각을 부르지 않는가 (규격 「한 겹만」)
    """
    tpl = ROOT / "web" / "templates"
    if not tpl.is_dir():
        return False, "web/templates 가 없다"
    bad = []
    # ① 쪽 머리·발은 ★ base.html 하나만 갖는다
    for q in sorted(tpl.glob("*.html")):
        if q.name in ("base.html", "watch_invite.html"):
            continue
        body = _read(q)
        for mark in ("<!DOCTYPE", "<html", "<header", "<footer"):
            if mark.lower() in body.lower():
                bad.append(f"{q.name} 이 {mark} 를 스스로 갖는다")
    # ② 모든 화면이 그 하나를 거친다
    views = _read(ROOT / "web" / "views.py")
    if "_page.html" not in views:
        bad.append("web/views.py 가 _page.html 을 안 쓴다")
    if "extends" not in _read(tpl / "_page.html"):
        bad.append("_page.html 이 base.html 을 안 물려받는다")
    # ③ 조각은 ★ 한 겹만이다
    for q in sorted(tpl.glob("_*.html")):
        if "{% include" in _read(q):
            bad.append(f"{q.name} 이 조각 안에서 조각을 부른다 (한 겹만)")
    if bad:
        return False, "★ " + " · ".join(bad[:4])
    n = len(list(tpl.glob("*.html")))
    frag = len(list(tpl.glob("_*.html")))
    return True, (f"틀 {n}개가 머리·발 한 곳(base.html)을 거친다 · 조각 {frag}개")


def s46_128_batch_gives_a_window() -> tuple[bool, str]:
    """★★★★ 묶어 쓰는 단계가 ★ **다른 쓰기에 창을 주는가** (ORDER r879 0 · 08-29).

    ★★ 마스터 — 「★ 보배가 재판정을 큐에 넣었고 ★ 09:16:20 → 09:25:25 도는 동안
      ★ ★ 뒤의 넷이 죽었다」.  ★ 개발측 실측 — ★ 한 번에 쥐는 시간은 ★ 이미 짧다
      (S6 최대 **2.50초** · 1,503번 끊긴다).  ★ 그런데도 죽었다.
    ★★★ 까닭은 ★ 틈의 **길이**가 아니라 ★ **비율**이었다 —
      ★ S6 은 588초 중 559초(95%)를 쥐고 ★ 틈이 평균 19ms 다.
      ★ ★ SQLite 는 ★ 점점 늘어나는 간격으로 다시 두드리므로 ★ 그 창을 계속 빗나가
      ★ ★ `busy_timeout` 30초를 다 쓰고 죽는다.
    ★ 사본 실측 — ★ pause 0ms 에서 `locked` **5** · 20ms 에서 **0**.
    ★ 그래서 셋을 함께 본다 —
      ① 행수마다 커밋한다 (`db_batch_commit_rows` > 0)
      ② 커밋 뒤 창을 준다 (`db_batch_commit_pause_ms` > 0)
      ③ `tick` 이 그 둘을 실제로 쓴다
    """
    try:
        with open(ROOT / "config" / "web.json", encoding="utf-8") as fp:
            cfg = json.load(fp)
    except (OSError, ValueError) as exc:
        return False, f"★ config/web.json 을 못 읽었다 — {exc}"
    bad = []
    rows = cfg.get("db_batch_commit_rows")
    pause = cfg.get("db_batch_commit_pause_ms")
    if not rows:
        bad.append("db_batch_commit_rows 가 0 이다 — 단계를 통째로 쥔다")
    if not pause:
        bad.append("db_batch_commit_pause_ms 가 0 이다 — 틈이 19ms 라 빗나간다")
    src = _read(ROOT / "store" / "raw.py")
    if "_batch_commit_pause_ms" not in src:
        bad.append("store/raw.py 에 창을 주는 자리가 없다")
    else:
        # ★ 커밋한 **뒤에** 쉬어야 한다 — ★ 앞에서 쉬면 창이 안 열린다
        i = src.find("def tick(")
        body = src[i:i + 1400] if i >= 0 else ""
        c, w = body.find("conn.commit()"), body.find("_batch_commit_pause_ms()")
        if c < 0 or w < 0 or w < c:
            bad.append("tick 이 커밋한 뒤에 안 쉰다")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, (f"{rows}행마다 커밋하고 ★ {pause:g}ms 창을 준다 "
                  "(실측 locked 5 → 0)")


def s46_127_collector_has_screen_or_timer() -> tuple[bool, str]:
    """★★★★ 수집기마다 ★ **화면이나 타이머**가 있는가 (오판 169 · 08-29).

    ★★ 오판 169 — 「★ KB 가 봇 차단으로 막혔다」를 ★ 여러 회차 옮겨 적었는데
      ★ ★ 재보니 ★ 막고 있던 것은 ★ **우리 코드**였다.  ★ 116건은
      ★ ★ 마스터가 ★ **손으로 열두어 번 돌린 수**였다.
    ★ 사람이 손으로만 도는 수집기는 ★ 「안 돈다」가 ★ 안 보인다 —
      ★ ★ 렉서스는 08-24 값이 08-29 까지 그대로였다.
    ★ 그래서 ★ 수집기마다 ★ 둘 중 하나는 있어야 한다 —
      ★ ★ ① 마스터가 누를 화면  ★ ② 저절로 부르는 타이머
    """
    screens = {}
    try:
        with open(ROOT / "config" / "cli_screens.json", encoding="utf-8") as fp:
            screens = json.load(fp).get("screens") or {}
    except (OSError, ValueError):
        pass
    # ★ 타이머가 부르는 것 — ★ 유닛의 ExecStart* 와 ★ 그것이 부르는 목록
    unit = ""
    for name in ("carwatch-daily.service", "carwatch.service"):
        unit += _read(ROOT / "deploy" / name)
    timed: set[str] = set()
    for line in unit.splitlines():
        if not line.startswith("ExecStart"):
            continue
        for tok in line.split():
            if tok.endswith(".py"):
                base = tok.rsplit('/', 1)[-1]
                timed.add(base)
                # ★ 묶어 부르는 것이면 ★ 그 안의 목록도 타이머가 부르는 것이다
                inner = _read(ROOT / "tools" / base)
                block = re.search(r"SITES[^=]*=\s*\((.*?)\)", inner, re.S)
                for m in re.findall(r'"([a-z0-9_]+)"', block.group(1) if block else ""):
                    timed.add(f"collect_{m}.py")
    bad = []
    for path in sorted((ROOT / "tools").glob("collect_*.py")):
        name = path.name
        rel = f"tools/{name}"
        if rel in screens or name in timed:
            continue
        bad.append(name)
    if bad:
        return False, (f"★ 손으로만 도는 수집기 {len(bad)}개 — "
                       f"{' · '.join(bad)}")
    n = len(list((ROOT / "tools").glob("collect_*.py")))
    return True, f"수집기 {n}개가 다 화면이나 타이머를 갖는다"


def s46_124_db_opened_with_pragmas() -> tuple[bool, str]:
    """★★★★ DB 를 ★ **PRAGMA 없이** 열지 않는가 (0b · 08-29).

    ★★ 마스터 — 「★ `collect/worker.py:107` `:155` 가 ★ `sqlite3.connect` 를
      ★ ★ 맨으로 부른다 — ★ `open_db` 를 안 써서 ★ `busy_timeout=30000` 이 안 붙는다」
    ★ 붙지 않으면 ★ 기본값 0 이다 — ★ 잠금을 만나면 ★ 기다리지 않고 그 자리에서 죽는다.
    ★ 여는 자리는 셋뿐이다 — ★ `store/raw.connect_db` · `open_db` · `web/app._open_db`.
    ★ 그 밖에서 맨으로 열면 ★ 같은 결함이 되살아난다.
    ★ 시험은 뺀다 — ★ 씨앗 DB 는 저 혼자 쓰고 ★ 잠금을 다투지 않는다 (S24).
    ★ ★ 보기만 하는 `tools/` 일회성 것도 뺀다 — ★ 개발측이 손으로 돌리고
      ★ ★ 죽으면 그 자리에서 보인다.  ★ **사이트가 떠 있는 동안 쓰는 것**만 본다
    """
    ok_files = {"store/raw.py", "web/app.py"}
    watched = ("collect/", "store/", "web/", "score/", "report/",
               "tools/collect_", "tools/daily_", "tools/recalc_")
    bad = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel in ok_files or rel == "run.py":
            continue
        if not rel.startswith(watched):
            continue
        for i, line in enumerate(_read(path).splitlines(), 1):
            if "sqlite3.connect(" not in line or line.lstrip().startswith("#"):
                continue
            # ★ 파이썬의 `timeout=` 이 ★ 곧 `busy_timeout` 이다 — ★ 그것도 옳다
            # ★ 읽기 전용(`mode=ro`)은 ★ 쓰기 잠금을 다투지 않는다 (WAL)
            if "timeout=" in line or "mode=ro" in line:
                continue
            bad.append(f"{rel}:{i}")
    if bad:
        return False, ("★ PRAGMA 없이 DB 를 여는 자리 "
                       f"{len(bad)}곳 — {' · '.join(bad[:5])}")
    return True, "DB 는 connect_db · open_db · _open_db 로만 연다"


def s46_126_fetch_outside_transaction() -> tuple[bool, str]:
    """★★★★★ 수집기가 ★ **통신·`sleep` 을 트랜잭션 안에서** 하는가 (개정 857).

    ★★ 마스터 — 「★ 왜 수집과 적재를 같이 하지」.  ★ 받기와 넣기를 가른다.
    ★★ 실측 08-29 — ★ KB 가 ★ 트랜잭션을 연 채 100건을 돌았다.
      ★ 건마다 `time.sleep(1.2)` 와 통신이 ★ 트랜잭션 안이라 ★ 한 창이 120초였다.
      ★ ★ 잠금이 ★ 38.4초까지 갔고 ★ 30초 `busy_timeout` 을 넘겨 죽었다.
    ★ 잣대 — ★ `save_*` 뒤 `commit` 없이 ★ `time.sleep` 이 오면 ★ 실패다.
      ★ ★ 낱말로 센다.  ★ 「트랜잭션이 열려 있나」는 ★ 글로 못 읽는다 —
        ★ 그래서 ★ **커밋이 자는 것보다 앞에 있는가**만 본다
    """
    import re as _re

    tools = ROOT / "tools"
    if not tools.is_dir():
        return False, "tools/ 가 없다"
    bad = []
    for q in sorted(tools.glob("collect_*.py")):
        body = _read(q)
        # ★ 저장한 뒤 ★ 커밋 없이 ★ 자는 자리를 찾는다
        for m in _re.finditer(r"save_(?:site_)?raw\s*\(", body):
            tail = body[m.end():m.end() + 900]
            nap = tail.find("time.sleep")
            fix = tail.find("commit(")
            if nap >= 0 and (fix < 0 or nap < fix):
                line = body[:m.start()].count("\n") + 1
                bad.append(f"{q.name}:{line}")
                break
    if bad:
        return False, ("★ 커밋 전에 자는 수집기 — " + " · ".join(bad[:8])
                       + "  (통신·sleep 은 트랜잭션 밖이어야 한다)")
    return True, f"수집기 {len(list(tools.glob('collect_*.py')))}개가 다 커밋 뒤에 잔다"


def s46_117_collectors_sweep_gone() -> tuple[bool, str]:
    """★★★★★ 목록을 받는 수집기가 ★ **팔린 차를 거르는가** (개정 838 · 오판 161).

    ★★ 사고 — ★ `mark_gone` 을 ★ `tools/collect_kcar.py` ★ 하나만 불렀다.
      ★ ★ 엔카·KB·볼보·현대·헤이딜러·리본카·보배 ★ 일곱이 안 불러
      ★ ★ 마스터께서 ★ **두 달째 팔린 차를 보셨다**.  ★ 엔카가 88% 다.
    ★★ ★ 이 검사를 ★ **첫 사이트를 붙일 때 만든다** (마스터 지시 08-29) —
      ★ ★ 마지막에 만들면 ★ 나머지 여덟이 ★ 안 빠진다.
    ★ 「부르는가」만 본다 — ★ 「제대로 매겼는가」는 ★ 사람이 숫자로 본다
    ★ 엔카는 ★ `collect/runner.py` 의 ★ S4 가 부른다 — ★ 결이 다르다
    """
    tools = ROOT / "tools"
    if not tools.is_dir():
        return False, "tools/ 가 없다"
    # ★★ 08-29 — ★ sweep 이 ★ 살아 있는 차를 죽여 ★ 다섯 곳을 껐다 (61건 되살림).
    #   ★ 끈 곳은 ★ 「왜 껐나」가 적혀 있어야 한다 — ★ 조용히 끄는 것은 막는다
    want = ("sweep_gone", "mark_gone", "SWEEP_OFF")
    done, todo, off = [], [], []
    for q in sorted(tools.glob("collect_*.py")):
        # ★ `collect_<사이트>.py` 는 ★ 다 목록을 받는 수집기다 —
        #   ★ 「목록을 받는가」를 낱말로 세지 않는다.  ★ 사이트마다 꼴이 다르다
        #     (`list_url` 없이 주소를 직접 만드는 것이 다섯이다 — 실측 08-29)
        body = _read(q)
        # ★★★★ 08-30 — ★ 「거른다」와 「일부러 껐다」를 ★ **갈라서** 센다.
        #   ★ 앞서는 둘을 한 자루에 넣어 ★ 「11곳이 다 거른다」로 말했다 —
        #   ★ ★ 다섯 곳이 ★ 껐는데도 ★ 그렇게 나왔다.  ★ 그것은 거짓이다
        if "SWEEP_OFF" in body:
            off.append(q.name)
        elif any(w in body for w in ("sweep_gone", "mark_gone")):
            done.append(q.name)
        else:
            todo.append(q.name)
    runner = _read(ROOT / "collect" / "runner.py")
    if not any(w in runner for w in want):
        todo.append("collect/runner.py (엔카 S4)")
    else:
        done.append("collect/runner.py (엔카 S4)")
    if todo:
        return False, (f"★ 팔린 차를 안 거르는 수집기 {len(todo)}개 — "
                       + " · ".join(todo[:8])
                       + f"  (거르는 것 {len(done)}개 · 일부러 끈 것 {len(off)}개)")
    tail = ""
    if off:
        # ★ 껐다고 통과라 말하지 않는다 — ★ 몇 곳이 왜 껐는지 함께 낸다
        tail = (f" · ★ 일부러 끈 것 {len(off)}곳 (SWEEP_OFF) — "
                + " · ".join(sorted(off)[:6]))
    return True, f"거르는 곳 {len(done)}곳{tail}"


def s46_77_kb_is_our_targets_only() -> tuple[bool, str]:
    """★★★ KB 는 ★ **우리 20종만** 받는가 (마스터 정정 08-26 · 명령서 60장).

    ★★ 마스터 — 「★ 야 내가 ★ **20종을 받으라고 했지**.
      ★ 쏘렌토 같이 ★ 보지도 않을 것을 ★ 받으라고 했니?」
    ★★ ★ 「전체」는 ★ **우리 20종의 전체**다 — ★ 국산까지 스무 종이다.
      ★ ★ 「KB 가 파는 15,836건 전부」가 ★ **아니다**.  ★ 명령서 59장은 ★ 폐기다
    ★★ ★ 재는 것 둘 —
      ★ ① 저장하는 길이 ★ `targets.json` 의 `site_query` 를 거치는가
        ★ ★ `--pages` · `--count` 는 ★ KB 가 파는 전부를 훑는다 — ★ 조사용이다
      ★ ② 코드에 ★ maker/class 를 ★ 박아 두지 않았는가 (금지 6)
    ★ 「이미 들어온 것」은 ★ `tools/fold_out_of_scope.py` 가 접는다 — ★ 여기서 안 센다
    """
    tool = ROOT / "tools" / "collect_kbchachacha.py"
    tg = ROOT / "config" / "targets.json"
    if not tool.is_file() or not tg.is_file():
        return False, "수집기나 targets.json 이 없다"
    body = _read(tool)
    bad = []
    # ① 좁히는 조건을 targets.json 에서 읽는가
    if "targets.json" not in body or "site_query" not in body:
        bad.append("좁히는 조건을 targets.json 에서 안 읽는다")
    # ② 저장하는 길(`--narrow`)이 그 조건을 쓰는가
    seg = body.split('if "--narrow" in args:', 1)
    if len(seg) < 2 or "load_filters()" not in seg[1][:400]:
        bad.append("저장하는 길이 좁히는 조건을 안 쓴다")
    # ③ 차종 코드를 코드에 박지 않았는가 (금지 6)
    for hit in re.findall(r'"(?:makerCode|classCode)"\s*:\s*"(\d+)"', body):
        bad.append(f"차종 코드를 코드에 박았다 — {hit}")
    # ④ targets.json 에 KB 코드가 몇 종에 있는가 — ★ 0 이면 좁힐 수가 없다
    rows = json.loads(_read(tg))
    have = [k for k, v in rows.items()
            if isinstance(v, dict) and not k.startswith("_")
            and (v.get("site_query") or {}).get("kbchachacha")]
    if not have:
        bad.append("targets.json 에 kbchachacha 코드가 한 종도 없다")
    # ⑤ ★★ 세대(`carCode`)를 적었으면 ★ **근거를 함께 적었는가** (금지 6 「지어내지 마라」).
    #   ★★ 08-26 마스터 ⓐ — ★ 세대로 좁힌다.  ★ 그런데 ★ 세대 코드는 ★ 사이트가 준 것이라
    #     ★ ★ 「어디서 봤는가」가 없으면 ★ 지어낸 것과 ★ 구별이 안 된다.
    #   ★ ★ `_세대` 칸에 ★ 실측 근거를 적는다 — ★ 그것이 있어야 통과다
    gen = 0
    for k in have:
        q = rows[k]["site_query"]["kbchachacha"]
        if not q.get("carCode"):
            continue
        gen += 1
        if not str(q.get("_세대") or "").strip():
            bad.append(f"{k} — 세대 코드에 근거(_세대)가 없다")
    if bad:
        return False, "★ KB 가 20종 밖을 받는다 — " + " · ".join(bad[:4])
    return True, (f"targets.json 의 {len(have)}종으로만 받는다 "
                  f"(세대로 좁힌 것 {gen}종 · 명령서 60장 · 59장은 폐기)")



def s46_78_encar_only_paths_are_scoped() -> tuple[bool, str]:
    """★★★ 엔카 전용 경로가 ★ 사이트로 좁혀 있는가 (명령서 3-2 뒤끝).

    ★★ 08-26 — ★ 원문 보관을 켜자 ★ `raw_response` 에 ★ **엔카 말고도** 들어왔다.
      ★ ★ 그런데 ★ 엔카 원문(JSON)의 키를 짚는 자리 넷이 ★ 좁혀 있지 않았다 —
        ★ ★ `V4` 차수가 ★ `json.loads` 에서 죽어 ★ **스물일곱 검사가 통째로 안 돌았다**
      ★ ★ `collect/runner.py` 의 `S6` 도 같은 자리다 — ★ 지금은 ★ 그 매물에
        ★ `target_key` 가 없어 ★ **우연히** 안 걸릴 뿐이다
    ★ 「원문을 한 표에 모은다」는 규격이다 (`kia_cpo` 도구 8행 「엔카와 같은 표에 넣는다」) —
      ★ 그러면 ★ **읽는 쪽이 좁혀야 한다**
    """
    want = (
        ("validate/v4_mapping.py", "r.endpoint='detail'", "r.site='encar'"),
        ("validate/v1_collect.py", "SELECT id, body FROM raw_response",
         "site='encar'"),
        ("collect/runner.py", "FROM raw_response r JOIN core_listing l",
         "r.site=?"),
        # ★★★ 08-27 — ★ 수집 차수가 ★ 매물을 고르는 자리다.
        #   ★ 여기를 안 좁혀 ★ 엔카 상세 API 에 ★ 현대인증·K카·헤이딜러
        #     ★ 매물번호를 넣어 ★ **전량 400** 이었다 (마지막 성공 08-24T07:41)
        ("collect/runner.py", "def _scope(sql: str, alias", "site_col"),
    )
    bad = []
    for name, near, need in want:
        q = ROOT / name
        if not q.is_file():
            bad.append(f"{name} 가 없다")
            continue
        body = _read(q)
        i = body.find(near)
        if i < 0:
            # ★ 글이 바뀌었으면 ★ 검사가 헛돈다 — ★ 그것도 알린다
            bad.append(f"{name} — 「{near[:24]}」 자리를 못 찾았다")
        # ★ 창을 넉넉히 본다 — ★ 주석이 길면 ★ 좁힌 줄이 창 밖으로 나간다
        elif need not in body[i:i + 1400]:
            bad.append(f"{name} — 사이트로 안 좁혔다 ({need})")
    if bad:
        return False, "★ 엔카 전용 경로가 안 좁혀 있다 — " + " · ".join(bad[:3])
    return True, f"엔카 전용 경로 {len(want)}곳이 사이트로 좁혀 있다"



def s46_87_request_site_matches_listing(db_path=None) -> tuple[bool, str]:
    """★★★ 부른 주소의 사이트와 ★ 매물의 사이트가 ★ 같은가 (마스터 지시 08-27 ③).

    ★★ 가이드 — 「★ 이것부터 만들어라.  ★ **있었으면 첫 회차에 잡혔다**」
    ★★★ ★ 08-27 실측 — ★ 엔카 상세 API 에 ★ 현대인증·K카·헤이딜러 매물번호를
      ★ ★ 넣어 ★ **사흘 동안 전량 400** 이었다.
      ★ ★ `V1-08`(동일 코드 실패율 100%)은 ★ 「실패했다」만 말했다 —
        ★ ★ **「왜」를 안 말했다.**  ★ 이 검사는 ★ 그 자리를 곧장 짚는다
    ★ 재는 법 — ★ `audit_request.url` 의 ★ 주인(호스트)을 ★ `endpoints.json` 으로 찾고
      ★ ★ 그 `source_id` 를 가진 매물의 ★ `site` 와 견준다
    ★ ★ 같은 `source_id` 가 ★ 그 사이트에도 있으면 ★ 맞는 것이다 —
      ★ ★ 사이트가 겹칠 수 있으므로 ★ **없을 때만** 실패로 센다
    ★ 옛 회차까지 다 세지 않는다 — ★ 마지막 회차만 본다 (`V1-16` 과 같은 뜻)
    """
    import sqlite3

    # ★ `db_path` 는 ★ 「일부러 깨서 봤다」(㉲)를 하려고 연 자리다 —
    #   ★ 검사표는 인자 없이 부른다.  ★ 시험만 다른 DB 를 준다
    db = Path(db_path) if db_path else ROOT / "carwatch.db"
    ep = ROOT / "config" / "endpoints.json"
    if not db.is_file() or not ep.is_file():
        return True, "DB 나 endpoints.json 이 없다 — 잴 것이 없다"
    from urllib.parse import urlparse
    host_of = {}
    for site, one in json.loads(_read(ep)).items():
        if isinstance(one, dict) and one.get("base_url"):
            host_of[urlparse(one["base_url"]).netloc.lower()] = site
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT run_id FROM audit_request ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return True, "요청 기록이 없다 — 잴 것이 없다"
        rid = row[0]
        rows = conn.execute(
            "SELECT url, source_id, COUNT(*) FROM audit_request"
            " WHERE run_id=? AND source_id IS NOT NULL AND url IS NOT NULL"
            " GROUP BY 1, 2", (rid,)).fetchall()
        bad, seen = {}, 0
        for url, sid, n in rows:
            site = host_of.get(urlparse(url).netloc.lower())
            if site is None:
                continue          # ★ 모르는 주인 — ★ 지어내지 않는다
            seen += n
            ok = conn.execute(
                "SELECT 1 FROM core_listing WHERE site=? AND source_id=?"
                " LIMIT 1", (site, str(sid))).fetchone()
            if ok:
                continue
            who = conn.execute(
                "SELECT site FROM core_listing WHERE source_id=? LIMIT 1",
                (str(sid),)).fetchone()
            key = f"{site} ← {who[0] if who else '모르는 매물'}"
            bad[key] = bad.get(key, 0) + n
    finally:
        conn.close()
    if bad:
        got = " · ".join(f"{k} {v}건" for k, v in
                         sorted(bad.items(), key=lambda kv: -kv[1])[:4])
        return False, (f"★ 남의 사이트 매물번호를 넣었다 (run {rid}) — {got}")
    if not seen:
        # ★ 매물번호를 단 요청이 없는 회차다 (목록만 던진 회차) — ★ 잴 것이 없다.
        #   ★ 「통과」로 읽히지 않게 ★ 그렇게 적는다
        return True, f"run {rid} 에 매물번호를 단 요청이 없다 — 잴 것이 없다"
    return True, f"run {rid} 의 요청 {seen:,}건이 다 제 사이트를 부른다"



def s46_88_encar_blocked_banner() -> tuple[bool, str]:
    """★★★ 엔카가 막히면 ★ 화면이 ★ **까닭과 할 일**을 말하는가 (마스터 지시 08-27 ⓑ).

    ★★ 마스터 — 「★ 407 이 이틀 넘으면 ★ 현황 맨 위에
      ★ ★ 「엔카가 막혀 있습니다 — 관리 ▸ 수집에서 「브라우저 수집」을 눌러 주십시오」.
      ★ ★ **무엇을 하면 되는지까지 적어라**」
    ★★ `407` 은 ★ 고장이 아니다 — ★ 규격이다 (`ENCAR_API.md:48`
      「서울 IP 407 · 브라우저 수집」).  ★ 우회하지 않는다 (금지 13)
    ★★ ★ 글자가 코드에 있는 것과 ★ 뜨는 것은 ★ 다르다 —
      ★ ★ **판단 함수를 불러** ★ 이틀 넘으면 뜨고 ★ 하루면 안 뜨는지 본다
    ★ 문턱은 ★ `config/web.json` `encar_blocked_days` 다 — ★ 코드에 안 박는다
    """
    import importlib

    cfg = ROOT / "config" / "web.json"
    if not cfg.is_file():
        return False, "config/web.json 이 없다"
    conf = json.loads(_read(cfg))
    if "encar_blocked_days" not in conf:
        return False, "config/web.json 에 encar_blocked_days 가 없다"
    limit = float(conf["encar_blocked_days"])
    try:
        app = importlib.import_module("web.app")
        judge = app._encar_blocked          # noqa: SLF001
    except (ImportError, AttributeError):
        return False, "web.app._encar_blocked 가 없다"
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)

    def iso(days):
        return (now - timedelta(days=days)).isoformat()

    bad = []
    # ★ ① 문턱을 넘으면 ★ 떠야 한다
    if judge(iso(0.1), iso(limit + 1)) is None:
        bad.append(f"{limit + 1}일 막혔는데 안 뜬다")
    # ★ ② 문턱 안이면 ★ 안 떠야 한다
    if judge(iso(0.1), iso(limit - 0.5)) is not None:
        bad.append(f"{limit - 0.5}일인데 뜬다 (문턱 {limit}일)")
    # ★ ③ 막힌 뒤에 목록이 들어왔으면 ★ 안 떠야 한다
    if judge(iso(limit + 1), iso(0.1)) is not None:
        bad.append("목록이 그 뒤에 들어왔는데도 뜬다")
    # ★ ④ 407 이 없으면 ★ 안 떠야 한다
    if judge(None, iso(limit + 1)) is not None:
        bad.append("407 이 없는데 뜬다")
    # ★ ⑤ 글에 ★ 「무엇을 하면 되는지」가 있는가
    said = _read(ROOT / "web" / "app.py")
    for word in ("엔카가 막혀 있습니다", "브라우저 수집", "/admin/collect"):
        if word not in said:
            bad.append(f"배너 글에 「{word}」가 없다")
    if bad:
        return False, "★ 막힘 배너가 어긋난다 — " + " · ".join(bad[:4])
    return True, (f"{limit}일 넘으면 뜨고 · 안이면 안 뜨고 · "
                  "목록이 들어오면 사라진다 · 할 일을 적는다")



# ── S46-54 · S46-55 · S46-56 — ★ 사이트 간 견주기 (명령서 45-3 ·
#   `docs/CROSS_SITE_COMPARE.md` 254~256행) ──────────────────────────────
# ★★ 규격 — 「★ 셋 다 ★ **숫자**다」.  ★ 그리고 ★ 「★ **판정을 바꾸지 마라** —
#   ★ 지금은 ★ 보여 주기만 한다」.  ★ 그래서 ★ 등급을 ★ `warn` 으로 둔다 —
#   ★ ★ 숫자가 0 이 아니라고 ★ 파이프라인을 막지 않는다
TRACK_BIG_GAP_PCT = 30.0


def _paired_rows():
    """★ 짝지어진 매물 — ★ 같은 차(`plate_hash`)가 ★ 두 사이트 넘게 올라온 것.

    ★ `report/screens/build.py:view_track` 과 ★ **같은 자리를 본다** —
      ★ 화면과 검사가 ★ 다른 수를 내면 ★ 어느 쪽도 못 믿는다
    돌려줌  {plate_hash: [(listing_id, site, price, grade)]} · calc_version
    """
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return {}, ""
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT calc_version FROM result_score"
            " ORDER BY calculated_at DESC, rowid DESC LIMIT 1").fetchone()
        if row is None:
            return {}, ""
        calc = row[0]
        by: dict = {}
        for plate, lid, site, price, grade in conn.execute(
            "SELECT l.plate_hash, l.listing_id, l.site, l.price_current_won,"
            "       s.grade"
            "  FROM core_listing l"
            "  LEFT JOIN result_score s ON s.listing_id = l.listing_id"
            "   AND s.calc_version = ?"
            " WHERE l.plate_hash IS NOT NULL AND l.status = 'active'"
            "   AND l.plate_hash IN ("
            "       SELECT plate_hash FROM core_listing"
            "        WHERE plate_hash IS NOT NULL AND status = 'active'"
            "        GROUP BY plate_hash HAVING COUNT(DISTINCT site) > 1)",
            (calc,)
        ):
            by.setdefault(plate, []).append((lid, site, price, grade))
        return by, calc
    finally:
        conn.close()


def _grade_order_list() -> tuple:
    """등급 차례 — ★ `config/labels.json` 의 `GRADE_ORDER` 가 정본이다 (개정 433).

    ★ 여기에 ("S","A","B",…) 를 ★ 박지 않는다 (S14 · 금지 6) —
      ★ 개정 433 이 8단계로 내렸을 때 ★ 그 튜플이 세 모듈에 흩어져 있었다
    """
    cfg = ROOT / "config" / "labels.json"
    if not cfg.is_file():
        return ()
    return tuple(json.loads(_read(cfg)).get("GRADE_ORDER") or ())


def s46_54_grade_two_step() -> tuple[bool, str]:
    """★ 짝지어진 매물 중 ★ 등급이 ★ **두 칸 이상** 벌어진 것이 몇인가 (숫자).

    ★★ 「S 와 B 가 ★ 같은 차면 ★ 큰 일이다」 (명령서 45-3 ①)
    ★ 판정을 바꾸지 않는다 — ★ 세어서 낸다
    """
    by, calc = _paired_rows()
    if not by:
        return True, "짝지어진 차가 없다 — 잴 것이 없다"
    order = _grade_order_list()
    if not order:
        return True, "등급 차례를 못 읽었다 (config/web.json grade_cuts)"
    two, sample = 0, []
    for plate, rows in by.items():
        got = [order.index(g) for _l, _s, _p, g in rows if g in order]
        if len(got) > 1 and max(got) - min(got) >= 2:
            two += 1
            if len(sample) < 3:
                sites = " vs ".join(
                    f"{s}:{g}" for _l, s, _p, g in rows if g in order)
                sample.append(f"{plate[:8]} {sites}")
    return True, (f"짝 {len(by)}대 중 ★ 등급 두 칸 이상 {two}대 (calc {calc})"
                  + (" — " + " · ".join(sample) if sample else ""))


def s46_55_price_gap_30() -> tuple[bool, str]:
    """★ 짝지어진 매물 중 ★ 값이 ★ **30% 넘게** 벌어진 것 (숫자).

    ★★ 「★ 30% 넘게 벌어지면 ★ **짝짓기가 틀렸을 자리다**」 (명령서 45-3 ②)
    """
    by, calc = _paired_rows()
    if not by:
        return True, "짝지어진 차가 없다 — 잴 것이 없다"
    big, sample = 0, []
    for plate, rows in by.items():
        prices = [p for _l, _s, p, _g in rows if p]
        if len(prices) < 2:
            continue
        low, high = min(prices), max(prices)
        if not low:
            continue
        pct = (high - low) / low * 100
        if pct >= TRACK_BIG_GAP_PCT:
            big += 1
            if len(sample) < 3:
                sample.append(f"{plate[:8]} {pct:.0f}%")
    return True, (f"짝 {len(by)}대 중 ★ 값 {TRACK_BIG_GAP_PCT:.0f}% 넘게 갈린 것 "
                  f"{big}대 (calc {calc})"
                  + (" — " + " · ".join(sample) if sample else ""))


def s46_56_accident_split() -> tuple[bool, str]:
    """★ 짝지어진 매물 중 ★ **사고 판정이 갈린 것** (숫자).

    ★★ 「★ 갈린다고 ★ 화면에 낸다」 — ★ 우리가 어느 쪽으로 정하지 않는다
    """
    import sqlite3

    by, calc = _paired_rows()
    if not by:
        return True, "짝지어진 차가 없다 — 잴 것이 없다"
    ids = [lid for rows in by.values() for lid, _s, _p, _g in rows]
    db = ROOT / "carwatch.db"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        acc = {}
        step = 500
        for i in range(0, len(ids), step):
            chunk = ids[i:i + step]
            marks = ",".join("?" * len(chunk))
            for lid, value in conn.execute(
                f"SELECT listing_id, COALESCE(value,'(모름)') FROM result_axis"
                f" WHERE axis='state.accident' AND calc_version=?"
                f"   AND listing_id IN ({marks})", (calc, *chunk)
            ):
                acc[lid] = value
    finally:
        conn.close()
    split, sample = 0, []
    for plate, rows in by.items():
        got = {acc[lid] for lid, _s, _p, _g in rows if lid in acc}
        if len(got) > 1:
            split += 1
            if len(sample) < 3:
                sample.append(f"{plate[:8]} "
                              + " vs ".join(sorted(str(x) for x in got)))
    return True, (f"짝 {len(by)}대 중 ★ 사고 판정이 갈린 것 {split}대 (calc {calc})"
                  + (" — " + " · ".join(sample) if sample else ""))



def s46_90_pending_not_graded() -> tuple[bool, str]:
    """★★★ 근거가 절반도 없는데 ★ 등급을 매기면 실패 (명령서 67장 · UI_REVIEW 18장).

    ★★ 마스터 — 「★ 왜 수입차의 등급이 낮은 이유가 뭐야.  ★ 거의 D등급 이하인데」
    ★★★ ★ 까닭은 ★ 차가 나빠서가 아니라 ★ **상세를 못 받아서**다 —
      ★ ★ 실측 08-27 — ★ X3 264/910 · F · ★ G80 670/910 · A.
        ★ ★ 사고 0/51 · 용도 0/22 · 자차 0/18 · 소유자 0/11 — ★ 넷 다 상세다
    ★ 「근거 있는 축의 합」이 ★ 분모의 절반 아래면 ★ 등급 자리는 ★ 「판정 중」이다.
      ★ ★ **F·G 로 내리지 않는다** — ★ 「모르는 것을 모른다고 낸다」(개정 325)
    ★★ 분모는 ★ **910 그대로**다 (가이드 확정 08-25 · UI_REVIEW 18장
      「근거 있는 축 N / 910」).  ★ 소모품처럼 채워질 수 없는 축을 분모에서 빼면
      절반선이 447.5 로 내려가 ★ 근거 450 짜리 상세 없는 매물이 G 에 남는다
    """
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    with open(ROOT / "config" / "scoring.json", encoding="utf-8") as f:
        cut = float(json.load(f).get("pending_confirmed_ratio", 0.5))
    with open(ROOT / "config" / "labels.json", encoding="utf-8") as f:
        not_ranked = tuple(json.load(f)["GRADE_NOT_RANKED"])
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        ver = conn.execute(
            "SELECT MAX(calc_version) FROM result_score").fetchone()
        if not ver or not ver[0]:
            return True, "판정본이 없다 — 잴 것이 없다"
        marks = ",".join("'%s'" % g for g in not_ranked)
        bad, worst = 0, None
        for lid, conf, den, grade in conn.execute(
            "SELECT s.listing_id, s.confirmed_points, s.denominator, s.grade"
            " FROM result_score s WHERE s.calc_version=?"
            f" AND s.grade NOT IN ({marks})",
            (ver[0],)
        ):
            base = float(den or 0)
            if base > 0 and float(conf or 0) < base * cut:
                bad += 1
                if worst is None:
                    worst = f"{lid} {grade} {conf:.0f}/{base:.0f}"
        if bad:
            return False, (f"근거가 절반도 없는데 등급을 매긴 것 {bad:,}건 "
                           f"(예: {worst}) — 「판정 중」으로 내라")
        return True, f"등급을 낸 것은 모두 근거가 절반을 넘는다 (기준 {cut:.0%})"
    finally:
        conn.close()


def _registrable(host: str) -> str:
    """도메인의 뿌리.  ★ `api.encar.com` 과 `www.encar.com` 은 같은 곳이다.

    ★ `co.kr` · `or.kr` 처럼 두 칸짜리 접미사는 세 칸을 뿌리로 본다
    """
    parts = [p for p in (host or "").lower().split(".") if p]
    if len(parts) < 2:
        return host or ""
    two = {"co", "or", "ne", "go", "re", "pe", "com", "net", "org"}
    if len(parts) >= 3 and parts[-2] in two and len(parts[-1]) <= 3:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def s46_94_source_url_site_matches() -> tuple[bool, str]:
    """★★★ 매물의 site 와 ★ 원문 주소의 도메인이 다르면 실패 (명령서 72장).

    ★★ 마스터 실측 08-28 — ★ 「★ 원문으로 가는 문이 ★ **다 엔카로 간다**」
      ★ ★ K카 매물 → `encar.com/dc/dc_cardetailview.do?carid=EC61384014`
      ★ ★ 헤이딜러 매물 → `encar.com/…?carid=KlGjM5QO`  ← ★ 헤이딜러 코드다
    ★★★ ★ **200 이 뜬다고 되는 게 아니다** — ★ 엔카는 ★ 모르는 carid 에도 200 을 준다.
      ★ ★ `S46-87`(부른 주소가 그 매물의 사이트인가)과 ★ **같은 잣대**다
    ★ 재는 법 — ★ `config/web.json` `site_detail_url` 의 꼴로 주소를 만들어
      ★ ★ 그 도메인이 ★ `config/endpoints.json` 의 그 사이트 도메인과 같은가를 본다
    ★ 못 잰 사이트(None)는 ★ **실패가 아니다** — ★ 「모른다」다.  ★ 링크를 안 낸다
    """
    from urllib.parse import urlparse

    with open(ROOT / "config" / "web.json", encoding="utf-8") as f:
        tpl = (json.load(f).get("site_detail_url") or {})
    with open(ROOT / "config" / "endpoints.json", encoding="utf-8") as f:
        eps = json.load(f)
    if not tpl:
        return False, "config/web.json 에 site_detail_url 이 없다 (명령서 72장)"
    bad, unknown = [], []
    for site, one in sorted(tpl.items()):
        if not one:
            unknown.append(site)
            continue
        want = _registrable(urlparse(
            str((eps.get(site) or {}).get("base_url") or "")).hostname or "")
        got = _registrable(urlparse(one.format(source_id="X")).hostname or "")
        if not want:
            bad.append(f"{site}: endpoints.json 에 base_url 이 없다")
        elif got != want:
            bad.append(f"{site}: 원문은 {got} 인데 사이트는 {want} 다")
    # ★ 사이트를 안 가리고 옛 칸 하나로 만드는 자리가 남아 있는가
    for rel in ("report/screens/build.py", "report/render.py"):
        body = (ROOT / rel).read_text(encoding="utf-8")
        if "encar_detail_url" in body:
            bad.append(f"{rel} 이 아직 encar_detail_url 로 만든다 — site 를 안 가린다")
    if bad:
        return False, "원문 문이 사이트와 어긋난다 — " + " · ".join(bad[:4])
    return True, (f"원문 주소 {len(tpl) - len(unknown)}곳이 제 사이트로 간다"
                  + (f" · 못 잰 곳 {len(unknown)}: {', '.join(unknown)}"
                     " (링크를 안 낸다)" if unknown else ""))


def s46_91_raw_vs_stored() -> tuple[bool, str]:
    """★★★ 받은 원문 수와 ★ 저장 수가 ★ 열 배 넘게 벌어지면 실패 (마스터 지시 08-28).

    ★★ 마스터 — 「★ 난 이미 엔카 수입차 목록을 ★ 어제부터 쭉 다 받아 줬어.
      ★ ★ **수집 반영 안 하는 것은 너희들 문제야**」
    ★★★ ★ 실측 08-28 — ★ 브라우저가 넣어 준 봉투 931건에 ★ 수입 3,013건이 있었는데
      ★ ★ `core_listing` 에 ★ **0건**이었다.  ★ `S4` 가 매물 하나의 불변 가드에
        ★ ★ 걸려 ★ **08-24T07:40 뒤로 통째로 멈춰** 있었다.
      ★ ★ 어떤 검사도 ★ 그것을 안 말했다 — ★ 이 검사가 그 자리다
    ★ 재는 법 — ★ 최근 목록 봉투를 펼쳐 ★ 매물번호를 모으고 ★ `core_listing` 과 견준다
    ★ ★ 봉투가 없는 사이트는 ★ 안 센다 (★ 「잴 것이 없다」와 ★ 「0건」은 다르다)
    """
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT MAX(fetched_at) FROM raw_response WHERE endpoint='list'"
            " AND status='ok'").fetchone()
        if not row or not row[0]:
            return True, "목록 봉투가 없다 — 잴 것이 없다"
        # ★ 마지막 봉투가 온 날부터 이틀치를 본다 — ★ 옛 봉투는 이미 실렸다
        from datetime import datetime, timedelta
        try:
            last = datetime.fromisoformat(str(row[0]))
        except ValueError:
            return True, "봉투 시각을 못 읽었다 — 잴 것이 없다"
        since = (last - timedelta(days=1)).isoformat()
        seen: dict = {}
        for site, body in conn.execute(
            "SELECT site, body FROM raw_response WHERE endpoint='list'"
            " AND status='ok' AND fetched_at >= ? AND body IS NOT NULL",
            (since,)
        ):
            from store.raw import raw_body

            try:
                doc = json.loads(raw_body(body))
            except (ValueError, TypeError):
                continue          # ★ JSON 이 아닌 목록(HTML)은 안 센다
            items = doc.get("SearchResults") if isinstance(doc, dict) else None
            for one in (items or []):
                if isinstance(one, dict) and one.get("Id"):
                    seen.setdefault(site, set()).add(str(one["Id"]))
        if not seen:
            return True, "펼칠 봉투가 없다 — 잴 것이 없다"
        bad, said = [], []
        for site, ids in sorted(seen.items()):
            marks = ",".join("?" * len(ids))
            got = conn.execute(
                f"SELECT COUNT(DISTINCT source_id) FROM core_listing"
                f" WHERE site=? AND source_id IN ({marks})",
                (site, *ids)).fetchone()[0]
            said.append(f"{site} 봉투 {len(ids):,} → 저장 {got:,}")
            # ★ 열 배 — ★ 마스터가 정하신 문턱이다
            if got * 10 < len(ids):
                bad.append(f"{site} — 봉투 {len(ids):,}건인데 저장 {got:,}건")
    finally:
        conn.close()
    if bad:
        return False, ("★ 받았는데 안 실렸다 — " + " · ".join(bad[:3])
                       + " (★ S4 가 멈춰 있는지 본다)")
    return True, " · ".join(said[:4])






def s46_97_raw_linked_by_source_id() -> tuple[bool, str]:
    """★★ 원문을 매물에 잇는 정본은 ★ `raw_response.source_id` 다 (마스터 08-26).

    ★★★ 마스터 — 「★ **정본은 사이트 매물번호(`source_id`)다.**
      ★ `request_url` 에서 되뽑는 건 ★ **임시다.  규격이 아니다.**
      ★ `listing_id` 도 ★ 지우지 말고 ★ **둘 다 둬라**」
    ★ 세 가지를 본다
      ① 매물별 원문에 `source_id` 가 비었나 (`list`·`facet` 은 매물 봉투가 아니라 뺀다)
      ② `source_id` 로 `core_listing` 에 이어지는데 ★ `listing_id` 가 비었나
      ③ 코드가 아직 ★ 주소에서 매물번호를 되뽑고 있나
    ★ ③ 이 뿌리다 — ★ 되뽑는 자리가 남아 있으면 ★ 언젠가 또 그리로 샌다
    """
    import sqlite3

    NOT_LISTING = ("list", "facet", "catalog", "sitemap",
                   "facet_maker", "facet_option", "facet_models",
                   "facet_conditions", "list_narrow", "list_gen",
                   "list_coming", "stock_list", "count", "car_name")
    bad = []

    # ③ 코드에 되뽑는 자리가 남아 있나 — DB 가 없어도 잰다
    import re as _re
    pat = _re.compile(r"(rsplit\(['\"]=['\"]|_sid_from_url\s*\()")
    for path in sorted((ROOT / "tools").glob("*.py")) + \
            sorted((ROOT / "store").glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if "S46-97" in line or line.lstrip().startswith("#"):
                continue
            if "raise NotImplementedError" in line:
                continue
            if pat.search(line) and "source_id" not in line:
                bad.append(f"{path.name}:{i} 주소에서 되뽑는다")

    db = ROOT / "carwatch.db"
    if not db.is_file():
        if bad:
            return False, " · ".join(bad[:4])
        return True, "DB 가 없다 — 코드만 봤고 되뽑는 자리가 없다"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        marks = ",".join("?" * len(NOT_LISTING))
        empty = conn.execute(
            "SELECT COUNT(*) FROM raw_response"
            " WHERE (source_id IS NULL OR source_id='')"
            f" AND endpoint NOT IN ({marks})", NOT_LISTING).fetchone()[0]
        if empty:
            bad.append(f"매물별 원문 {empty}건이 source_id 가 비었다")
        orphan = conn.execute(
            "SELECT COUNT(*) FROM raw_response r JOIN core_listing l"
            "   ON l.site=r.site AND l.source_id=r.source_id"
            " WHERE r.listing_id IS NULL").fetchone()[0]
        if orphan:
            bad.append(f"이어지는데 listing_id 가 빈 원문 {orphan}건")
        linked = conn.execute(
            "SELECT COUNT(*) FROM raw_response r JOIN core_listing l"
            "   ON l.site=r.site AND l.source_id=r.source_id").fetchone()[0]
    finally:
        conn.close()
    if bad:
        return False, "★ " + " · ".join(bad[:4])
    return True, f"source_id 로 이어진 원문 {linked:,}건 · 되뽑는 자리 없다"



def s46_99_login_then_watch() -> tuple[bool, str]:
    """★★ 로그인한 뒤 ★ `/watch` 가 200 이 아니면 실패 (마스터 지시 08-26).

    ★★★ 마스터 — 「★ `S46-95` 는 ★ 로그인 앞만 봐서 ★ 못 잡았다」.  ★ 옳다.
      ★ ★ `/watch` · `/admin` 은 ★ 로그인 앞에서 ★ **403 이 정상**이라
      ★ ★ `S46-95` 는 ★ 그 둘이 ★ 403 이면 ★ 통과로 센다.
      ★ ★ 그래서 ★ 「자리를 안 내준다」를 ★ 아무도 못 보고 있었다.
    ★ 재는 법 — ★ 실제로 ★ 로그인 폼을 받아 ★ csrf 를 들고 ★ POST 한다.
      ★ ★ **303 과 `Set-Cookie` 를 본다** — ★ 200 이면 ★ 자리를 안 내준 것이다
      ★ ★ 그 쿠키로 ★ `login_screens` 를 ★ 다 두드린다
    ★ 자격은 ★ `secrets/check_login.json` 이다 — ★ `.gitignore` 에 있다.
      ★ ★ 비밀번호를 ★ 저장소·문서·기록에 ★ 적지 않는다.
      ★ ★ 자격이 없으면 ★ **실패로 낸다** — ★ 못 잰 것을 ★ 통과로 세지 않는다
    """
    import http.cookiejar
    import ssl as _ssl
    import urllib.error
    import urllib.parse
    import urllib.request

    cred_path = ROOT / "secrets" / "check_login.json"
    raw = _read(cred_path)
    if not raw:
        return False, ("secrets/check_login.json 이 없다 — 못 쟀다"
                       " (name·secret 을 넣는다.  git 에 안 올라간다)")
    try:
        cred = json.loads(raw)
        name, secret = str(cred["name"]), str(cred["secret"])
    except (ValueError, KeyError, TypeError):
        return False, "secrets/check_login.json 을 못 읽었다 — name·secret 이 있어야 한다"

    cfg = json.loads(_read(ROOT / "config" / "web.json") or "{}")
    screens = cfg.get("login_screens") or {}
    dep = json.loads(_read(ROOT / "config" / "deploy.json") or "{}")
    base = str(dep.get("base_url") or "").rstrip("/")
    if not base or not screens:
        return False, "config 에 base_url · login_screens 가 없다"

    ctx = _ssl._create_unverified_context()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar))

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *_a, **_k):
            return None

    try:
        with opener.open(base + "/login", timeout=25) as res:
            form = res.read().decode("utf-8", "replace")
    except (urllib.error.URLError, OSError) as exc:
        return False, f"/login 을 못 두드렸다 ({type(exc).__name__})"
    got = re.search(r'name="csrf" value="([^"]+)"', form)
    if not got:
        return False, "/login 에 csrf 가 없다"

    body = urllib.parse.urlencode(
        {"csrf": got.group(1), "name": name, "secret": secret}).encode()
    poster = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar), _NoRedirect)
    try:
        with poster.open(base + "/login", data=body, timeout=25) as res:
            code, headers = res.status, res.headers
    except urllib.error.HTTPError as exc:
        code, headers = exc.code, exc.headers
    except (urllib.error.URLError, OSError) as exc:
        return False, f"POST /login 을 못 했다 ({type(exc).__name__})"

    if int(code) != 303:
        return False, (f"★ POST /login 이 {code} 다 — 303 이어야 한다"
                       "  (200 이면 자리를 안 내준 것이다)")
    if not headers.get("Set-Cookie"):
        return False, "★ POST /login 이 303 인데 Set-Cookie 가 없다"

    bad, ok = [], 0
    for path, want in screens.items():
        try:
            with opener.open(base + path, timeout=25) as res:
                code = res.status
        except urllib.error.HTTPError as exc:
            code = exc.code
        except (urllib.error.URLError, OSError) as exc:
            bad.append(f"{path} 못 두드림({type(exc).__name__})")
            continue
        if int(code) == int(want):
            ok += 1
        else:
            bad.append(f"{path} {code}(→{want})")
    if bad:
        return False, "★ 로그인했는데 " + " · ".join(bad)
    return True, f"로그인 뒤 화면 {ok}개가 다 열린다 (303 · Set-Cookie 확인)"



def _logged_opener():
    """★ 로그인한 열개.  ★ 자격은 `secrets/check_login.json` 이다 (S46-99 와 같다).

    ★ 자격이 없거나 로그인이 안 되면 ★ None 을 돌려준다 — ★ 부르는 쪽이 적는다
    """
    import http.cookiejar
    import ssl as _ssl
    import urllib.error
    import urllib.parse
    import urllib.request

    raw = _read(ROOT / "secrets" / "check_login.json")
    dep = json.loads(_read(ROOT / "config" / "deploy.json") or "{}")
    base = str(dep.get("base_url") or "").rstrip("/")
    if not raw or not base:
        return None, base
    try:
        cred = json.loads(raw)
        name, secret = str(cred["name"]), str(cred["secret"])
    except (ValueError, KeyError, TypeError):
        return None, base
    ctx = _ssl._create_unverified_context()
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.HTTPCookieProcessor(jar))
    try:
        with opener.open(base + "/login", timeout=25) as res:
            form = res.read().decode("utf-8", "replace")
        got = re.search(r'name="csrf" value="([^"]+)"', form)
        if not got:
            return None, base
        body = urllib.parse.urlencode(
            {"csrf": got.group(1), "name": name, "secret": secret}).encode()
        opener.open(base + "/login", data=body, timeout=25).read()
    except (urllib.error.URLError, OSError):
        return None, base
    return opener, base

def _sian_seq(html: str, keep_title: bool = False) -> list:
    """보이는 글의 ★ 차례.  ★ 낱말이 아니라 ★ 자리를 잰다 (명령서 82장).

    ★ 고정 메뉴(탭·nav)는 ★ 뺀다 — ★ 소스에서는 위에 있고 ★ 화면에서는 아래다.
      ★ ★ `position:fixed;bottom:0` 이라 ★ 소스 차례와 보이는 차례가 다르다
    """
    cut = html.find("지켜야 하는 것")
    if cut > 0:
        html = html[:cut]
    drop = r"<(script|style)[^>]*>.*?</\1>"
    if not keep_title:
        drop = r"<(script|style|title)[^>]*>.*?</\1>"
    html = re.sub(drop, " ", html, flags=re.S | re.I)
    # ★ 메모(note)와 고정 메뉴를 뺀다
    html = re.sub(r'<([a-z]+)[^>]*class="[^"]*(note|tabs)[^"]*"[^>]*>.*?</\1>',
                  " ", html, flags=re.S | re.I)
    html = re.sub(r"<nav[^>]*>.*?</nav>", " ", html, flags=re.S | re.I)
    out = []
    for line in re.sub(r"<[^>]+>", "\n", html).split("\n"):
        got = re.sub(r"[★\s]+", " ", line).strip()
        if not (2 <= len(got) <= 30) or not re.search(r"[가-힣]", got):
            continue
        # ★ 숫자가 절반을 넘으면 ★ **보기 값**이다 — ★ 자리가 아니라 데이터다.
        #   ★ 「2,990만」·「5,242건 중 30건」 같은 것을 견주면 ★ 검사가 흔들린다
        digits = sum(ch.isdigit() for ch in got)
        if digits * 2 >= len(re.sub(r"\s", "", got)):
            continue
        if not out or out[-1] != got:
            out.append(got)
    return out


def s46_100_sian_word_order() -> tuple[bool, str]:
    """★★ 시안과 화면의 ★ **낱말 차례**가 다르면 실패 (마스터 지시 08-28 · 82장).

    ★★★ 마스터 — 「★ 내가 시안대로 ★ 디자인 위치를 모두 보정하라고 한 거잖아.
      ★ ★ 내용만 있으면 시안을 왜 만들어.  ★ 메뉴가 위에 있다가 밑으로 가버리고」
    ★★ ★ `S46-98` 은 ★ 「낱말이 있나」만 본다 — ★ **「어디에 있나」를 안 본다.**
      ★ ★ 그래서 ★ 가격이 등급 앞으로 튀어도 ★ 통과했다 (실측 08-28).
    ★ 재는 법 — ★ 양쪽의 보이는 글을 차례대로 늘어놓고
      ★ ★ **둘 다에 있는 낱말만** 남겨 ★ 그 차례가 같은지 본다.
      ★ ★ 한쪽에만 있는 것은 ★ `S46-98` 이 본다 — ★ 여기서는 안 센다.
    ★ 고정 메뉴는 뺀다 — ★ 소스에서는 위 · 화면에서는 아래다 (`position:fixed`)
    """
    import ssl as _ssl
    import urllib.error
    import urllib.request

    cfg = json.loads(_read(ROOT / "config" / "web.json") or "{}")
    pairs = cfg.get("sian_screens") or {}
    skip = set(cfg.get("sian_word_skip") or [])
    dep = json.loads(_read(ROOT / "config" / "deploy.json") or "{}")
    base = str(dep.get("base_url") or "").rstrip("/")
    if not pairs or not base:
        return False, "config 에 sian_screens · base_url 이 없다"

    lid = ""
    db = ROOT / "carwatch.db"
    if db.is_file():
        import sqlite3
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT listing_id FROM result_score LIMIT 1").fetchone()
            lid = str(row[0]) if row else ""
        except sqlite3.Error:
            lid = ""
        finally:
            conn.close()

    ctx = _ssl._create_unverified_context()
    # ★★ 명령서 82장 「여덟 화면 다」 — ★ 셋은 로그인 뒤에만 열린다
    login_pairs = cfg.get("sian_screens_login") or {}
    opener = None
    if login_pairs:
        opener, _b = _logged_opener()
        if opener is None:
            return False, ("secrets/check_login.json 이 없어"
                           " 로그인 화면 셋을 못 쟀다")
    bad, ok = [], 0
    for sian, path in {**pairs, **login_pairs}.items():
        need_login = sian in login_pairs
        orig_path = path
        src = SCREENS / sian
        if not src.is_file():
            bad.append(f"{sian} 가 없다")
            continue
        if "{listing_id}" in path:
            if not lid:
                continue
            path = path.replace("{listing_id}", lid)
        try:
            if need_login:
                res = opener.open(base + path, timeout=25)
            else:
                res = urllib.request.urlopen(base + path, timeout=25,
                                             context=ctx)
            with res:
                body = res.read().decode("utf-8", "replace")
            # ★★ 시안에 없는 절은 ★ 견주기 전에 잘라 낸다 (마스터 08-28 ④).
            #   ★ 자리는 `config/web.json` 의 `sian_cut_regions` 가 정본이다
            for a, b in (cfg.get("sian_cut_regions") or {}).items():
                if a not in (path, orig_path) or len(b) != 2:
                    continue
                i, j = body.find(b[0]), body.find(b[1])
                if 0 <= i < j:
                    body = body[:i] + body[j:]
            page = _sian_seq(body, True)
        except (urllib.error.HTTPError, urllib.error.URLError, OSError) as exc:
            bad.append(f"{path} 못 두드림({type(exc).__name__})")
            continue
        want = _sian_seq(src.read_text(encoding="utf-8"))
        # ★★ 마스터께서 차례를 따로 말씀하신 화면은 ★ 그것으로 견준다 (82장 ②).
        #   ★ 시안과 어긋나는 자리를 ★ config 에 적어 두었다 — ★ 숨기지 않는다
        fixed = (cfg.get("sian_order_override") or {}).get(path)
        if fixed:
            got = [w for w in page
                   if any(w.startswith(x) for x in fixed)]
            seen, seq = set(), []
            for w in got:
                key = next(x for x in fixed if w.startswith(x))
                if key not in seen:
                    seen.add(key)
                    seq.append(key)
            if seq != [x for x in fixed if x in seq]:
                bad.append(f"{path} 마스터 차례와 다르다 —"
                           f" 말씀 「{' → '.join(fixed)}」"
                           f" ↔ 화면 「{' → '.join(seq)}」")
            else:
                ok += 1
            continue
        # ★ 둘 다에 있는 낱말만 남긴다 — ★ 없는 것은 S46-98 이 본다
        # ★★ 양쪽에서 ★ **한 번만** 나오는 낱말로만 견준다.
        #   ★ 두 번 나오는 낱말은 ★ 어느 쪽이 그 자리인지 알 수 없다 —
        #   ★ ★ 실측 08-28 — ★ `/track` 의 「짝지어진 차」가 ★ 머리와 본문에 둘 다 있어
        #     ★ ★ 자리가 맞는데도 ★ 어긋났다고 나왔다.  ★ 검사가 틀리면 안 된다
        from collections import Counter as _C
        cw, cp = _C(want), _C(page)
        both = {w for w in set(want) & set(page)
                if cw[w] == 1 and cp[w] == 1} - skip

        def _first(seq):
            """★ **처음 나온 차례**만 남긴다 — ★ 그것이 「자리」다.

            ★ 카드·줄이 되풀이되면 ★ 같은 낱말이 여러 번 나온다.
              ★ ★ 되풀이까지 견주면 ★ 자리가 맞아도 어긋난 것으로 나온다
            """
            got, out = set(), []
            for w in seq:
                if w in both and w not in got:
                    got.add(w)
                    out.append(w)
            return out

        a, b = _first(want), _first(page)
        if a == b:
            ok += 1
            continue
        # ★ 처음 어긋난 자리를 그대로 낸다
        n = min(len(a), len(b))
        at = next((i for i in range(n) if a[i] != b[i]), n)
        bad.append(f"{path} {at + 1}번째부터 다르다 —"
                   f" 시안 「{a[at] if at < len(a) else '(끝)'}」"
                   f" ↔ 화면 「{b[at] if at < len(b) else '(끝)'}」")
    if bad:
        return False, "★ " + " / ".join(bad[:3])
    return True, f"시안 {ok}장의 낱말 차례가 화면과 같다"


def s46_102_electric_only_is_electric() -> tuple[bool, str]:
    """★★ 「전기만」에 ★ 전기 아닌 것이 나오면 실패 (마스터 지시 08-28 · 87장 ⑤).

    ★★★ 마스터 — 「★ 나는 내 목록에서 ★ 전기차만 보고 싶은 거야」.
    ★ 매물의 ★ **연료 칸**으로 거른다 — ★ 차종이 아니다.
      ★ ★ 그래야 ★ XC40 안의 EX40(전기)이 갈린다.
    ★ 「전기만」은 ★ 정확히 `전기`·`EV` 다 —
      ★ ★ `가솔린+전기`(하이브리드)와 ★ `수소+전기`(연료전지)는 ★ 안 든다.
    ★ 화면이 쓰는 그 조건 그대로 세어 본다 — ★ 밖에서 따로 세지 않는다
    """
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    try:
        from report.screens.build import _listings_where
        from report.screens.views import ListingFilter
    except ImportError as exc:
        return False, f"화면 조건을 못 읽었다 — {exc}"

    cfg = json.loads(_read(ROOT / "config" / "web.json") or "{}")
    groups = {g.get("key"): g for g in (cfg.get("fuel_groups") or [])}
    want = groups.get("electric") or {}
    ok_values = set(want.get("values") or ())
    if not ok_values:
        return False, "config/web.json 에 fuel_groups.electric 이 없다"

    where, args = _listings_where(ListingFilter(fuel="electric"))
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        rows = conn.execute(
            "SELECT l.fuel_raw, COUNT(*) FROM core_listing l"
            " LEFT JOIN result_score s ON s.listing_id = l.listing_id"
            "   AND s.calc_version = ?"
            f" WHERE {' AND '.join(where)} GROUP BY 1",
            ["c1", *args]).fetchall()
    except sqlite3.Error as exc:
        return False, f"세지 못했다 — {exc}"
    finally:
        conn.close()

    bad = [(f, n) for f, n in rows if f not in ok_values]
    total = sum(n for _f, n in rows)
    if bad:
        got = " · ".join(f"{f}({n})" for f, n in bad[:5])
        return False, f"★ 「전기만」에 전기 아닌 것 {sum(n for _f, n in bad)}건 — {got}"
    if not total:
        return False, "★ 「전기만」이 0건이다 — 거르개가 안 먹는다"
    return True, f"「전기만」 {total:,}건이 다 전기다 ({' · '.join(sorted(ok_values))})"


def s46_103_sian_values_carried() -> tuple[bool, str]:
    """★★ 시안의 ★ **크기·자리 값**을 ★ `app.css` 가 담았는가 (명령서 82장).

    ★★★ 마스터 — 「★ 내가 시안대로 ★ 디자인 위치를 모두 보정하라고 한 거잖아.
      ★ ★ 내용만 있으면 시안을 왜 만들어.  ★ UX 관점도 없고」
    ★★ ★ `S46-98`(낱말) · `S46-100`(차례)로는 ★ **꼴을 못 본다** — ★ 글자만 본다.
    ★★★ ★ 그런데 ★ 시안 **이름**을 `app.css` 에 들이면 안 된다 —
      ★ ★ 마스터 확정 ㉮(08-24) 「★ 시안 쪽에 `.v3-` 을 붙인다.
        ★ ★ 실제 `app.css` 는 안 건드린다」 · 검사 `S46-67` 이 그것을 지킨다.
      ★ ★ 실측 08-28 — ★ 시안 CSS 를 그대로 들였더니 ★ 289곳이 겹쳐
        ★ ★ `S46-67`·`S46-68`·`S46-75` 가 터지고 ★ 시험 셋이 깨졌다.  ★ 되돌렸다.
    ★ 그래서 ★ **이름이 아니라 값**을 본다 — ★ 시안에서 재서 적은 수가
      ★ ★ `app.css` 안에 ★ 실제로 있는지 센다.  ★ 어느 이름에 붙었는지는 안 따진다
    """
    css_path = ROOT / "web" / "static" / "app.css"
    sian = SCREENS / "v4m_listings_시안.html"
    if not css_path.is_file() or not sian.is_file():
        return True, "app.css 나 시안이 없다 — 잴 것이 없다"
    css = re.sub(r"/\*.*?\*/", " ", _read(css_path), flags=re.S)
    flat = re.sub(r"\s+", "", css)

    # ★ 시안에서 잰 값이다 (08-28) — ★ 지어내지 않았다
    WANT = [
        ("사진 104×78 (모바일)", ("width:104px", "height:78px")),
        ("사진 88×66 (아주 좁을 때)", ("width:88px", "height:66px")),
        ("사진 180×135 (넓을 때)", ("width:180px", "height:135px")),
        ("사진 240×180 (더 넓을 때)", ("width:240px", "height:180px")),
        ("손가락 단추 44px", ("min-height:44px",)),
        ("아래 탭 고정", ("position:fixed", "bottom:0")),
        ("고르개 40px", ("min-height:40px",)),
        ("둥근 모서리 8px", ("border-radius:8px",)),
    ]
    bad = [name for name, vals in WANT
           if not all(v.replace(" ", "") in flat for v in vals)]
    if bad:
        return False, ("★ 시안 값이 app.css 에 없다 " + str(len(bad)) + " — "
                       + " · ".join(bad))
    return True, (f"시안에서 잰 값 {len(WANT)}가지가 다 app.css 에 있다"
                  " (이름은 우리 것 그대로 — 마스터 확정 ㉮)")


def s46_98_sian_words_on_screen() -> tuple[bool, str]:
    """★★ 시안에 있는 낱말이 ★ 화면에 없으면 실패 (마스터 지시 08-26).

    ★★★ 마스터 — 「★ `S46-22` 는 ★ 절 이름·차례만 본다.  ★ **카드 속을 안 본다**」
    ★★ ★ 실측 08-26 — ★ 목록 카드에 ★ `제조사보증` · `사이트보증` 이 ★ 없었다.
      ★ ★ 「판정 다섯을 다섯 다 내라」 하셨는데 ★ 셋만 나오고 있었다.
      ★ ★ 그 밖에 ★ `시세보다 … 싸다` · `N일째` 도 ★ 빠져 있었다 — ★ 검사가 없어서 몰랐다
    ★ 재는 법 — ★ 시안의 ★ **보이는 글**에서 ★ 한글 낱말을 뽑아
      ★ 그 화면을 ★ 실제로 두드려 ★ 그 낱말이 있는지 본다.
    ★ 안 세는 것 — ★ `<style>·<script>·<title>` · ★ `class` 에 `note` 가 든 메모 ·
      ★ 「지켜야 하는 것」 아래 · ★ `config/web.json` 의 `sian_word_skip`
    ★ 짝과 건너뛸 낱말의 정본은 ★ `config/web.json` 이다 (S14)
    """
    import ssl as _ssl
    import urllib.error
    import urllib.request

    cfg = json.loads(_read(ROOT / "config" / "web.json") or "{}")
    pairs = cfg.get("sian_screens") or {}
    skip = set(cfg.get("sian_word_skip") or [])
    if not pairs:
        return False, "config/web.json 에 sian_screens 가 없다"
    dep = json.loads(_read(ROOT / "config" / "deploy.json") or "{}")
    base = str(dep.get("base_url") or "").rstrip("/")
    if not base:
        return False, "config/deploy.json 에 base_url 이 없다"

    lid = ""
    db = ROOT / "carwatch.db"
    if db.is_file():
        import sqlite3
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT listing_id FROM result_score LIMIT 1").fetchone()
            lid = str(row[0]) if row else ""
        except sqlite3.Error:
            lid = ""
        finally:
            conn.close()

    han = re.compile(r"[가-힣]{2,}")
    drop = re.compile(r"<(script|style|title)[^>]*>.*?</\1>", re.S | re.I)
    # ★ 화면 쪽은 `<title>` 을 남긴다 — ★ 그것이 그 화면의 이름이다
    keep_drop = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.S | re.I)
    note = re.compile(
        r'<([a-z]+)[^>]*class="[^"]*note[^"]*"[^>]*>.*?</\1>', re.S | re.I)

    def visible(html: str, keep_title: bool = False) -> str:
        """보이는 글.

        ★★ `keep_title` — ★ **화면 쪽만** 참이다 (08-26).
          ★ 시안의 `<title>` 은 ★ 「v4m 미판정 시안 — 모바일 기준」이라 ★ 비계다.
          ★ ★ 그런데 ★ **화면의 `<title>`** 은 ★ 「미판정 · CarWatch」로
            ★ ★ 그 화면의 ★ **이름 그 자체**다 — ★ 지우면 ★ 있는 것을 없다고 한다.
          ★ ★ 실측 08-26 — ★ 그래서 ★ `/notready` 에 ★ 「미판정」이 없다고 나왔다
        """
        cut = html.find("지켜야 하는 것")
        if cut > 0:
            html = html[:cut]
        killer = keep_drop if keep_title else drop
        return re.sub(r"<[^>]+>", " ", note.sub(" ", killer.sub(" ", html)))

    def squeeze(text: str) -> str:
        """★ 띄어쓰기를 지운 꼴.  ★ 시안은 「제조사보증」 · 화면은 「제조사 보증」이다.

        ★★ 08-26 실측 — ★ 그 한 칸 때문에 ★ 검사가 ★ **거짓 실패**를 냈다.
          ★ ★ 마스터께서 「제조사·사이트 보증은 붙었다」 하셨고 ★ 옳으셨다 —
          ★ ★ 카드에 다섯이 다 있는데 ★ 내 검사가 ★ 못 찾은 것이었다.
          ★ ★ 검사가 틀리면 ★ 고친 것을 ★ 안 고쳤다고 말한다 — ★ 가장 나쁜 쪽이다
        """
        return re.sub(r"\s+", "", text)

    ctx = _ssl._create_unverified_context()
    bad, seen = [], 0
    for sian, path in pairs.items():
        src = SCREENS / sian
        if not src.is_file():
            bad.append(f"{sian} 가 없다")
            continue
        if "{listing_id}" in path:
            if not lid:
                continue
            path = path.replace("{listing_id}", lid)
        try:
            with urllib.request.urlopen(base + path, timeout=25,
                                        context=ctx) as res:
                page = visible(res.read().decode("utf-8", "replace"), True)
        except urllib.error.HTTPError as exc:
            bad.append(f"{path} {exc.code}")
            continue
        except (urllib.error.URLError, OSError) as exc:
            bad.append(f"{path} 못 두드림({type(exc).__name__})")
            continue
        want = sorted(set(han.findall(
            visible(src.read_text(encoding="utf-8")))) - skip)
        seen += len(want)
        # ★ 띄어쓰기 차이는 ★ 다름이 아니다 (위 squeeze 참고)
        flat = squeeze(page)
        miss = [w for w in want if w not in page and squeeze(w) not in flat]
        if miss:
            bad.append(f"{path} 에 없다 {len(miss)} — " + " · ".join(miss[:8]))
    if bad:
        return False, "★ " + " / ".join(bad[:4])
    return True, f"시안 {len(pairs)}장의 낱말 {seen}개가 다 화면에 있다"

def s46_95_screens_alive() -> tuple[bool, str]:
    """★★ 배포된 화면 여덟을 두드려 ★ 하나라도 제 코드가 아니면 실패.

    ★★★ 명령서 74·75장 — ★ 08-28 에 ★ `/` · `/track` · `/detail` 이 ★ **500** 이었고
      ★ 그 다음 바퀴에는 ★ **전 화면이 503**(앱이 아예 없다)이었다.
    ★★ ★ 왜 몰랐나 — ★ **검사가 없었다.**  ★ 개발측은 ★ 매물 건수만 세고 있었고
      ★ 화면이 열리는지는 ★ 아무도 안 봤다 (오판 141).
    ★ 재는 법 — ★ 주소도 화면 목록도 ★ `config/deploy.json` 이 정본이다 (S14).
      ★ `/watch` · `/admin` 은 ★ 로그인 앞이라 ★ 403 이 정상이다 (74장 실측)
    ★ 못 두드리면 ★ **실패다** — ★ 그것이 바로 ★ 503 일 때의 모습이다
    """
    import urllib.error
    import urllib.request

    dep = json.loads(_read(ROOT / "config" / "deploy.json") or "{}")
    base = str(dep.get("base_url") or "").rstrip("/")
    screens = dep.get("health_screens") or {}
    if not base or not screens:
        return False, "config/deploy.json 에 base_url · health_screens 가 없다"
    lid = ""
    db = ROOT / "carwatch.db"
    if db.is_file():
        import sqlite3
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            row = conn.execute(
                "SELECT listing_id FROM result_score LIMIT 1").fetchone()
            lid = str(row[0]) if row else ""
        except sqlite3.Error:
            lid = ""
        finally:
            conn.close()
    ctx = ssl._create_unverified_context()
    bad, ok = [], 0
    for path, want in screens.items():
        if "{listing_id}" in path:
            if not lid:
                continue
            path = path.replace("{listing_id}", lid)
        try:
            with urllib.request.urlopen(base + path, timeout=20,
                                        context=ctx) as res:
                got = res.status
        except urllib.error.HTTPError as exc:
            got = exc.code
        except (urllib.error.URLError, OSError) as exc:
            bad.append(f"{path} 못 두드림({type(exc).__name__})")
            continue
        if int(got) == int(want):
            ok += 1
        else:
            bad.append(f"{path} {got}(→{want})")
    if bad:
        return False, f"★ 화면 {len(bad)}개가 제 코드가 아니다 — " + " · ".join(bad)
    return True, f"화면 {ok}개가 다 제 코드다 ({base})"

def s46_96_site_sells_but_no_code() -> tuple[bool, str]:
    """★★ 사이트가 파는 차종인데 ★ `site_query` 에 코드가 없으면 알린다.

    ★★★ 마스터 08-26 — 「★ 21개 차종을 안 받나?」 ★ 짚으신 그대로였다.
    ★ 실측 08-26 — ★ `kcar` 와 ★ `reborncar` 는 ★ **21종 전부 코드가 0개**다.
      ★ 그 둘은 ★ 종합 사이트라 ★ 21종을 다 판다.  ★ 코드가 없으니 안 받고,
      ★ 안 받으니 ★ 짝이 안 잡히고 ★ 상세도 없다 — ★ 「등급이 낮다」의 뿌리다.
    ★ 재는 법 — ★ 그 차종의 제조사(`site_query.encar.Manufacturer`)가
      ★ 그 사이트의 `brand_scope` 안이면 ★ 파는 것이다.  ★ `all` 은 종합이다.
    ★ 알림이다 — ★ 막지 않는다.  ★ 코드는 ★ 마스터께 청한다 (개발측이 안 넣는다)
    """
    got = _targets()
    if not got:
        return False, "config/targets.json 에 차종이 없다"
    eps = json.loads(_read(ENDPOINTS) or "{}")
    sites = [s for s, v in eps.items()
             if isinstance(v, dict) and not s.startswith("_")]
    no_scope = [s for s in sites if "brand_scope" not in eps[s]]
    if no_scope:
        return False, ("brand_scope 가 없는 사이트 "
                       f"{len(no_scope)} — " + " · ".join(no_scope[:6]))
    miss: dict[str, list[str]] = {}
    for key, spec in got.items():
        # ★ 09-02 — ★ 쉬는 차종(active=false)은 ★ 안 센다.
        #   ★ 마스터께서 09-01 에 대상을 열로 좁히셨다 — ★ 쉬는 것을 세면 89칸이 남는다
        if spec.get("active") is False:
            continue
        maker = ((spec.get("site_query") or {}).get("encar") or {}).get(
            "Manufacturer")
        if not maker:
            return False, f"{key} 에 제조사가 없다 — site_query.encar.Manufacturer"
        for site in sites:
            scope = eps[site]["brand_scope"]
            sells = scope == "all" or maker in scope
            if sells and site not in (spec.get("site_query") or {}):
                miss.setdefault(site, []).append(key)
    if miss:
        n = sum(len(v) for v in miss.values())
        head = " · ".join(f"{s} {len(v)}종" for s, v in
                          sorted(miss.items(), key=lambda kv: -len(kv[1])))
        return False, (f"★ 파는데 코드가 없다 {n}칸 — {head}"
                       "  (코드는 마스터께 청한다)")
    return True, f"차종 {len(got)}종 × 사이트 {len(sites)} — 파는 칸은 코드가 다 있다"

def s46_92_browser_zero_count() -> tuple[bool, str]:
    """★★★ 브라우저 수집이 ★ `Count 0` 을 받으면 ★ 알린다 (마스터 지시 08-28).

    ★★ 마스터 — 「★ 「200 이라 성공」으로 세지 마라.  ★ **0건은 성공이 아니다**」
    ★★★ ★ 실측 08-28 — ★ 마스터께서 ★ 수입 여덟을 다 눌러 주셨는데
      ★ ★ **벤츠 GLC 만 ★ `Count 0`** 이었다 (다른 일곱은 다 왔다).
      ★ ★ 그런데 ★ 어디에도 ★ 그 말이 안 나왔다 — ★ `status='ok'` 라 ★ 성공으로 셌다.
      ★ ★ 「우리가 흘렸나 · 엔카가 0을 줬나」를 ★ 사흘 동안 못 갈랐다
    ★ 재는 법 — ★ 봉투의 `Count` 가 0 이고 ★ 항목도 0 이면 ★ 그 쿼리를 적는다
    ★ ★ 쿼리는 ★ `iNav.BreadCrumbs` 의 `RemoveAction` 에 ★ 그대로 들어 있다
    ★ 알림이다 — ★ 막지 않는다.  ★ 사이트에 정말 0건일 수 있다 (신차 등)
    """
    import re as _re
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        row = conn.execute(
            "SELECT MAX(fetched_at) FROM raw_response"
            " WHERE origin='browser' AND status='ok'").fetchone()
        if not row or not row[0]:
            return True, "브라우저 봉투가 없다 — 잴 것이 없다"
        from datetime import datetime, timedelta
        try:
            last = datetime.fromisoformat(str(row[0]))
        except ValueError:
            return True, "봉투 시각을 못 읽었다 — 잴 것이 없다"
        since = (last - timedelta(days=1)).isoformat()
        mf = _re.compile(r"Manufacturer\.([^._)]+)")
        mg = _re.compile(r"ModelGroup\.([^._)]+)")
        zero, seen = {}, 0
        for body in conn.execute(
            "SELECT body FROM raw_response WHERE origin='browser'"
            " AND status='ok' AND fetched_at >= ? AND body IS NOT NULL",
            (since,)
        ):
            from store.raw import raw_body

            try:
                doc = json.loads(raw_body(body[0]))
            except (ValueError, TypeError):
                continue
            if not isinstance(doc, dict) or "Count" not in doc:
                continue
            seen += 1
            if int(doc.get("Count") or 0) or (doc.get("SearchResults") or []):
                continue
            crumbs = json.dumps(
                (doc.get("iNav") or {}).get("BreadCrumbs") or [],
                ensure_ascii=False)
            a, b = mf.search(crumbs), mg.search(crumbs)
            key = f"{a.group(1) if a else '?'} {b.group(1) if b else '?'}"
            zero[key] = zero.get(key, 0) + 1
    finally:
        conn.close()
    if not seen:
        return True, "센 봉투가 없다 — 잴 것이 없다"
    if zero:
        got = " · ".join(f"{k} {v}봉투"
                         for k, v in sorted(zero.items(), key=lambda kv: -kv[1]))
        return False, (f"★ 0건으로 온 쿼리 {len(zero)}가지 — {got[:160]} "
                       "(★ 이름이 틀렸나 · 정말 없나 — ★ 사람이 봐야 한다)")
    return True, f"브라우저 봉투 {seen:,}건이 다 0건이 아니다"



def s46_161_no_unproven_absence():
    """S46-161 — ★ 「사이트가 안 준다」를 증거 없이 쓰지 않는가 (감독 지시 08-29 ⑥).

    ★ 08-29 에 ★ 이 문장이 ★ **하루에 네 번 뒤집혔다** (오판 188·189·190·192).
      ★ 셋은 우리 파서 결함이었고 ★ 하나는 안내문을 값으로 센 것이었다.
    ★ 잣대 — ★ 「안 준다」·「주지 않는다」가 있는 줄에 ★ **표본 수**가 함께 없으면 실패.
      ★ 표본 열 건 전건이 비어야 그 문장을 쓴다 (오판 189 가 세운 것)
    ★ 「못 찾았다」·「아직 못 쟀다」는 ★ 걸지 않는다 — ★ 그것은 정직한 말이다
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").rglob("*.md")):
        if "guide/06_" in q.as_posix() or "guide/03_" in q.as_posix():
            continue                      # ★ 오판·이력은 그때의 기록이다
        for i, ln in enumerate(_read(q).splitlines(), 1):
            # ★ 주장문만 잡는다 — ★ 「{사이트}는/가 … 안 준다」
            #   ★ 인용·규칙·물린 문장은 ★ 아래 거르개가 뺀다
            if not _re.search(r"(엔카|K카|KB차차차|KB|보배|헤이딜러|리본카|볼보"
                              r"|BMW|렉서스|기아|현대)[가는은이]?\s*[^。\n]{0,24}"
                              r"(안 준다|주지 않는다)", ln):
                continue
            # ★ 「아니다」·「틀렸다」는 ★ 그 문장을 물리는 줄이다 — 걸지 않는다
            if _re.search(r"못 찾았|아직 못 쟀|못 쟀다|아니었다|아니다|틀렸다"
                          r"|오판|물린다|정정", ln):
                continue
            # ★ 「…처럼 안 준다」는 ★ 다른 사이트를 견주는 말이다 — 걸지 않는다
            if _re.search(r"처럼|같은 꼴|와 달리", ln):
                continue
            # ★ 마스터·개발측 말을 옮긴 줄과 ★ 규칙을 적은 줄은 ★ 주장이 아니다
            if _re.search(r"「.*(안 준다|주지 않는다).*」|필수|금지|가이드 안"
                          r"|후보|말씀|물음|여쭌|확인해|원문 —|마스터 —|^\s*「|「야|보배에 신차가", ln):
                continue
            # ★ `~~…~~` 로 물린 줄은 ★ 이미 취소된 문장이다
            if "~~" in ln:
                continue
            # ★ [추론] 이라 밝힌 것은 ★ 사실 문장이 아니다 (감독 지시 ② 08-29)
            if "[추론" in ln:
                continue
            # ★ 증거 — 표본 수가 같은 줄에 있는가
            if _re.search(r"표본\s*\d+|\d+\s*/\s*\d+|\d+건", ln):
                continue
            bad.append(f"{q.relative_to(ROOT)}:{i}")
    if bad:
        return False, ("★ 「안 준다」에 표본 수가 없다 "
                       f"{len(bad)}곳 — " + " · ".join(bad[:6]))
    return True, "「안 준다」가 모두 표본 수를 달고 있다"


def s46_162_promised_checks_exist():
    """S46-162 — ★ 오판이 약속한 검사가 ★ 실제로 있는가 (감독 지시 08-29 ③).

    ★ 감독 — 「★ 오늘 여섯 무늬가 ★ **전부 글로만 적힌 것**이다.  ★ **글은 또 어긴다**」
    ★ 잣대 — ★ 오판대장의 「검산 `S46-NNN`」 이 ★ CHECKS 에 없으면 ★ 실패.
      ★ ★ 「글로만 적었다」라고 그 줄에 적어 두면 ★ 봐준다 — ★ 다만 그것도 세어 낸다
    """
    import re as _re

    body = _read(ROOT / "docs" / "guide" / "06_오판대장.md")
    have = set(_re.findall(r'\("(S\d+-[\w.]+)"', _read(ROOT / "validate" / "v0_guide.py")))
    missing, excused = [], 0
    for ln in body.splitlines():
        m = _re.search(r"검산 `(S46-\d+)`", ln)
        if not m:
            continue
        if m.group(1) in have:
            continue
        if "글로만 적었다" in ln:
            excused += 1
            continue
        missing.append(m.group(1))
    if missing:
        return False, (f"★ 오판이 약속한 검사 {len(missing)}개가 없다 — "
                       + " · ".join(sorted(set(missing))[:8])
                       + (f"  (「글로만 적었다」로 적어 둔 것 {excused}개)"
                          if excused else ""))
    return True, f"약속한 검사가 모두 있다 (「글로만」 {excused}개)"


def s46_145_numbers_have_meaning():
    """S46-145 — ★ 마스터께 드리는 표에 ★ 수만 있고 뜻이 없지 않은가 (오판 187).

    ★ 마스터 — 「★ 빈 축이 17, 12, 24, 20 이렇게 적어놓으면 ★ 내가 어떻게 알아서
      담을 수가 있니?  ★ 뭐라고 설명을 달아야 되는 게 아니니?」
    ★ 잣대 — ★ 「빈 축」·「미확인」·「못 받은 것」 뒤에 ★ 수만 있고
      ★ 같은 줄에 ★ 낱말(무엇이 비었나)이 없으면 ★ 실패
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").rglob("*.md")):
        if "/guide/06_" in q.as_posix() or "/guide/03_" in q.as_posix():
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            m = _re.search(r"(빈 축|미확인|못 받은 것)\s*\|?\s*\**(\d+)\**\s*\|", ln)
            if not m:
                continue
            # ★ 같은 줄에 ★ 축 이름이 하나라도 있으면 ★ 뜻이 달린 것이다
            if _re.search(r"골격|외판|누유|사고|용도|신차가|트림|옵션|시세"
                          r"|보증|소모품|진정성|연식|주행|색상|선루프|HUD", ln):
                continue
            bad.append(f"{q.relative_to(ROOT)}:{i}")
    if bad:
        return False, ("★ 수만 있고 뜻이 없는 곳 "
                       f"{len(bad)} — " + " · ".join(bad[:6]))
    return True, "수에 뜻이 달려 있다"


def s46_155_screen_spec_has_mockup():
    """S46-155 — ★ 화면 규격을 쓰면 ★ 시안이 있는가 (오판 197 · 104).

    ★ ⓞ 「화면을 시키면 ★ 그 바퀴에 시안도 그린다」
    ★ 잣대 — ★ `UI_REVIEW` 의 장 제목에 ★ 주소(`/foo`)가 있으면
      ★ `ref/screens/` 에 그 이름이 든 시안이 있어야 한다
    """
    import re as _re

    body = _read(ROOT / "docs" / "UI_REVIEW.md")
    screens = ROOT / "ref" / "screens"
    if not screens.is_dir():
        return False, "ref/screens 가 없다"
    names = " ".join(p.name for p in screens.glob("*.html"))
    table = _read(ROOT / "docs" / "chapters" / "61-web.md")
    bad = []
    for m in _re.finditer(r"^#+ .*?`/([a-z_]+)`", body, _re.M):
        key = m.group(1)
        if key in names:
            continue
        # ★ 라우팅 표에 있는 화면만 본다 — ★ 규격 본문의 예시 주소는 뺀다
        if not _re.search(r"\| ?★? ?`?/" + key + r"[`/{]", table):
            continue
        # ★ 아직 「시안」 단계인 화면은 ★ 시안이 없어도 된다 — ★ 만들 때 그린다
        if _re.search(r"\|\s*`?/" + key + r"[`/{][^\n]*\|\s*시안\s*\|", table):
            continue
        bad.append("/" + key)
    if bad:
        return False, ("★ 규격에 있는데 시안이 없는 화면 "
                       f"{len(bad)} — " + " · ".join(sorted(set(bad))[:6]))
    return True, "화면 규격마다 시안이 있다"


def s46_163_mockup_has_route():
    """S46-163 — ★ 시안이 있으면 ★ 라우팅 표에 그 주소가 있는가 (오판 205).

    ★ 08-29 — ★ 「팔린 차」 시안을 올리고 ★ 라우팅 표에 안 넣어
      ★ `test_web` 이 깨졌다.  ★ 개발측이 그 화면을 못 만들었다
    """
    import re as _re

    screens = ROOT / "ref" / "screens"
    if not screens.is_dir():
        return False, "ref/screens 가 없다"
    table = _read(ROOT / "docs" / "chapters" / "61-web.md")
    paths = set(_re.findall(r"`(/[a-z_{}]+)`", table))
    bad = []
    for p in sorted(screens.glob("*.html")):
        m = _re.match(r"v\d+m?_([a-z_]+)_", p.name)
        if not m:
            continue
        key = "/" + m.group(1)
        if any(p == key or p.startswith(key + "/") for p in paths):
            continue
        # ★ 화면 이름이 ★ view 로 있으면 ★ 주소가 달라도 그 화면이다 (`/` → view_dashboard)
        if "view_" + m.group(1) in table:
            continue
        bad.append(f"{p.name} → {key}")
    if bad:
        return False, ("★ 시안이 있는데 라우팅 표에 없는 것 "
                       f"{len(bad)} — " + " · ".join(bad[:6]))
    return True, "시안마다 라우팅 표에 주소가 있다"


def _guide_docs():
    """★ 가이드가 쓴 문서 — ★ 오판·이력은 그때의 기록이라 뺀다."""
    for q in sorted((ROOT / "docs").rglob("*.md")):
        a = q.as_posix()
        if "/guide/06_" in a or "/guide/03_" in a or "/evidence/" in a:
            continue
        yield q


def s46_129_table_sum_counted():
    """S46-129 — ★ 표에 「합」을 적으면 ★ 그 합이 맞는가 (오판 171).

    ★ 08-29 — ★ 명령서 범위표 합이 9,554 인데 머리에 5,756 이라 적었다
    ★ 잣대 — ★ 「합 N」 과 ★ 같은 표의 수를 더한 것이 ★ 다르면 실패
    """
    import re as _re

    bad = []
    for q in _guide_docs():
        rows, total = [], None
        for ln in _read(q).splitlines():
            if not ln.startswith("|"):
                rows, total = [], None
                continue
            m = _re.search(r"\|\s*\**합[^|]*\**\s*\|(.*)$", ln)
            cells = [c.strip() for c in ln.strip("|").split("|")]
            nums = [int(c.replace(",", "").strip("* ★"))
                    for c in cells
                    if _re.fullmatch(r"[\d,]+", c.replace("*", "").strip("* ★"))]
            if m and nums:
                total = nums[-1]
                if rows and total != sum(rows) and "세는 법" not in _read(q):
                    bad.append(f"{q.name}: 합 {total:,} ≠ 더한 것 {sum(rows):,}")
                rows, total = [], None
            elif nums:
                rows.append(nums[-1])
    if bad:
        return False, f"★ 합이 안 맞는 표 {len(bad)} — " + " · ".join(bad[:4])
    return True, "표의 합이 다 맞는다"


def s46_132_handover_says_remeasure():
    """S46-132 — ★ 인계문이 ★ 「이 수를 믿지 마라 — 재라」를 적는가 (오판 174)."""
    import glob as _g

    files = _g.glob(str(ROOT / "docs" / "guide" / "*인계*.md"))
    if not files:
        return True, "인계문이 아직 없다"
    bad = [f.split("/")[-1] for f in files
           if "재라" not in _read(ROOT / f[len(str(ROOT)) + 1:])]
    if bad:
        return False, "★ 「이 수를 믿지 마라 — 재라」가 없다 — " + " · ".join(bad)
    return True, "인계문이 다시 재라고 적는다"


def s46_140_new_host_has_robots():
    """S46-140 — ★ 규격·config 에 쓴 호스트가 ★ robots 문서에 있는가 (오판 182).

    ★ 08-29 — ★ `fem.encar.com` 을 원문 문으로 쓰면서 ★ 그 호스트 robots 를 안 받았다
    """
    import json as _j
    import re as _re

    robots = _read(ROOT / "docs" / "ENCAR_ROBOTS.md")
    web = _j.loads(_read(ROOT / "config" / "web.json"))
    hosts = set(_re.findall(r"https?://([a-z0-9.-]*encar\.com)",
                            _j.dumps(web, ensure_ascii=False)))
    bad = [h for h in sorted(hosts) if h not in robots]
    if bad:
        return False, ("★ config 가 쓰는데 robots 문서에 없는 호스트 — "
                       + " · ".join(bad))
    return True, f"엔카 호스트 {len(hosts)}개가 robots 문서에 있다"


def s46_142_site_count_matches():
    """S46-142 — ★ 「N 사이트」가 ★ config/sites.json 의 수와 같은가 (오판 184).

    ★ 08-29 — ★ 「열 사이트를 다 쟀다」고 여러 회차 보고했는데 ★ 사이트는 열하나였다
    """
    import json as _j
    import re as _re

    sites = _j.loads(_read(ROOT / "config" / "sites.json"))
    n = len([k for k in sites if not k.startswith("_") and k != "dealer_site"])
    words = {"열": 10, "열하나": 11, "열둘": 12, "아홉": 9, "여덟": 8}
    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            m = _re.search(r"(열하나|열둘|열|아홉|여덟)\s*사이트", ln)
            if not m:
                continue
            # ★ 「그 밖 N」·「나머지 N」은 ★ 이미 뺀 수다 — 걸지 않는다
            # ★ 09-02 — ★ 「아홉 사이트」는 ★ 잣대 이름이다 (엔카를 뺀 아홉).
            #   ★ 사이트 수가 아니다 — ★ 마스터께서 그 말로 잣대 ①을 부르신다
            if m.group(1) == "아홉":
                continue
            if _re.search(r"(그 밖|나머지|빼면|제외)\s*★?\s*" + m.group(1), ln):
                continue
            said = words[m.group(1)]
            # ★ 「아홉」은 엔카를 뺀 수다 — ★ 그것도 맞다
            # ★ 「아홉」은 엔카를 뺀 수 · 「열」은 마스터 회선 것까지 뺀 수다
            if said in (n, n - 1, n - 2):
                continue
            bad.append(f"{q.name}:{i} 「{m.group(1)} 사이트」 (실제 {n})")
    if bad:
        return False, f"★ 사이트 수가 다른 곳 {len(bad)} — " + " · ".join(bad[:4])
    return True, f"「N 사이트」가 config 의 {n}과 맞는다"


def s46_146_absence_needs_parser_check():
    """S46-146 — ★ 「사이트가 안 준다」 절에 ★ 파서를 열어 봤다는 말이 있는가 (오판 188·190).

    ★ 08-29 — ★ 셋이 다 ★ 사이트가 아니라 ★ 우리 파서 결함이었다
    ★ 잣대 — ★ 그 문장이 있는 문서에 ★ `parse/` 나 「파서」가 ★ 한 번도 없으면 실패
    """
    import re as _re

    bad = []
    for q in _guide_docs():
        body = _read(q)
        if not _re.search(r"(사이트가|이 사이트는).{0,20}안 준다", body):
            continue
        if "파서" in body or "parse/" in body:
            continue
        bad.append(q.name)
    if bad:
        return False, ("★ 「안 준다」를 쓰면서 파서를 안 본 문서 "
                       f"{len(bad)} — " + " · ".join(bad[:5]))
    return True, "「안 준다」를 쓴 문서가 파서도 본다"


def s46_154_master_wish_in_registry():
    """S46-154 — ★ 마스터 말씀의 「~했으면 좋겠어」가 ★ 요구 추적표에 있는가 (오판 196).

    ★ 08-29 — ★ 「가격 통계를 내놨으면」이 ★ 추적표 391행에 ★ 한 줄도 없었다
    ★ 잣대 — ★ 규격에 인용된 「…했으면 좋겠…」이 ★ 추적표에 없으면 실패
    """
    import re as _re

    reg = _read(ROOT / "docs" / "guide" / "01_요구사항.md")
    bad = []
    for q in _guide_docs():
        for m in _re.finditer(r"「([^」|]{6,60}했으면[^」|]{0,20})」", _read(q)):
            key = m.group(1)[:12]
            if key in reg:
                continue
            bad.append(f"{q.name}: 「{m.group(1)[:24]}…」")
    if bad:
        return False, ("★ 추적표에 없는 마스터 말씀 "
                       f"{len(bad)} — " + " · ".join(bad[:3]))
    return True, "마스터 말씀이 추적표에 있다"


def s46_131_paging_claim_measured():
    """S46-131 — ★ 「쪽넘김이 없다」를 ★ 실측 없이 적지 않는가 (오판 173).

    ★ 08-29 — ★ 렉서스가 ★ `cur_page` 로 3쪽을 주는데 ★ 「1쪽뿐」이라 적어
      ★ 안 팔린 38건을 ★ gone 으로 죽였다
    """
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"쪽넘김이 (없다|없음)|한 쪽뿐|1쪽뿐", ln):
                continue
            if _re.search(r"실측|표본|\d+\s*쪽|눌러 ?봤|재 ?봤", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 「쪽넘김이 없다」에 실측이 없는 곳 "
                       f"{len(bad)} — " + " · ".join(bad[:5]))
    return True, "「쪽넘김이 없다」가 다 실측을 달고 있다"


def s46_135_generalisation_has_sample():
    """S46-135 — ★ 「~만으로 갈린다」 같은 일반화에 ★ 표본이 있는가 (오판 177)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"만으로 (갈린다|가른다|된다|충분하다)", ln):
                continue
            if _re.search(r"표본|\d+\s*건|\d+\s*/\s*\d+|실측", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 표본 없는 일반화 {len(bad)} — " + " · ".join(bad[:5])
    return True, "일반화가 다 표본을 달고 있다"


def s46_138_all_claim_needs_source():
    """S46-138 — ★ 「전량」·「전수」에 ★ 세는 법이 붙어 있는가 (오판 180).

    ★ 08-29 — ★ K카 「전량 487」이 ★ 실은 ★ 한 창구가 주는 487 이었다
    """
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            # ★ 「전량 404」·「전량 401」은 ★ 응답 코드다 — ★ 건수가 아니다
            if not _re.search(r"(전량|전수)\s*([\d,]{2,})\s*건", ln):
                continue
            if _re.search(r"실측|표본|빈 쪽|끝까지|집합|고유|세는 법|쪽", ln):
                continue
            # ★ 물린 줄·정정 줄·마스터 인용은 ★ 주장이 아니다
            if _re.search(r"~~|정정|폐기|오판|고친다|「", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 세는 법 없는 「전량」 {len(bad)} — " + " · ".join(bad[:5])
    return True, "「전량」이 다 세는 법을 달고 있다"


def s46_149_confession_is_closed():
    """S46-149 — ★ 규격에 적은 자백이 ★ 닫혔거나 밀린일에 있는가 (오판 191).

    ★ 08-22 자백(「스키마를 안 보고 매핑을 썼다」)이 ★ 이레 동안 열린 채였다
    """
    import re as _re

    pend = _read(ROOT / "docs" / "guide" / "07_밀린일대장.md")
    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if "가이드 자백" not in ln:
                continue
            m = _re.search(r"개정 ([\d·]+)", ln)
            key = m.group(1)[:3] if m else None
            near = _read(q)
            j = near.find(ln)
            if "닫는다" in near[j:j + 400] or "끝" in ln:
                continue
            if key and key in pend:
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 안 닫힌 자백 {len(bad)} — " + " · ".join(bad[:5])
    return True, "자백이 다 닫혔거나 밀린일에 있다"


def s46_156_answer_touches_spec():
    """S46-156 — ★ 개발측 물음의 답이 ★ 규격에 있는가 (오판 198).

    ★ 08-29 — ★ 답을 명령서에만 적어 ★ 같은 물음이 네 회차 되풀이됐다
    ★ 잣대 — ★ 명령서가 「답한다」고 적은 낱말이 ★ docs/ 어딘가에 있어야 한다
    """
    import glob as _g
    import re as _re

    orders = _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    if not orders:
        return True, "명령서가 없다"
    body = _read(ROOT / orders[0][len(str(ROOT)) + 1:])
    specs = " ".join(_read(q) for q in _guide_docs())
    bad = []
    for m in _re.finditer(r"`([a-z_]+\.(?:py|json))[`:]", body):
        pass
    for m in _re.finditer(r"→ ?\*\*`?([A-Z_]{4,})", body):
        if m.group(1) not in specs:
            bad.append(m.group(1))
    if bad:
        return False, ("★ 명령서가 가리키는데 규격에 없는 것 "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, "명령서의 답이 규격에 있다"


def s46_130_one_tally_per_register():
    """S46-130 — ★ 한 문서에 ★ 합계표가 둘이 아닌가 (오판 172).

    ★ 08-29 — ★ 오판대장에 합계표가 둘이고 ★ 둘 다 틀렸다
    """
    import re as _re

    bad = []
    for q in list(_guide_docs()) + [ROOT / "docs" / "guide" / "06_오판대장.md"]:
        n = len(_re.findall(r"^#+ .*합계", _read(q), _re.M))
        if n > 1:
            bad.append(f"{q.name} ({n}개)")
    if bad:
        return False, f"★ 합계표가 둘 이상 — " + " · ".join(bad[:4])
    return True, "합계표가 문서마다 하나다"


def s46_134_target_site_pair():
    """S46-134 — ★ `targets.json` 에 그 사이트 질의가 있는데 ★ 규격이 ✘ 라 적지 않는가 (오판 176)."""
    import json as _j
    import re as _re

    t = _j.loads(_read(ROOT / "config" / "targets.json"))
    pairs = set()
    for k, v in t.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        for site in (v.get("site_query") or {}):
            pairs.add((k, site))
    bad = []
    for key, site in sorted(pairs):
        doc = ROOT / "docs" / (site.upper() + "_API.md")
        if not doc.is_file():
            continue
        body = _read(doc)
        if _re.search(r"\|\s*`?" + _re.escape(key) + r"`?\s*\|[^|]*\|\s*✘", body):
            bad.append(f"{key}@{site}")
    if bad:
        return False, ("★ 질의는 있는데 규격이 ✘ 라 적은 것 "
                       + " · ".join(bad[:5]))
    return True, "질의와 규격이 어긋나지 않는다"


def s46_141_filter_claim_measured():
    """S46-141 — ★ 「거르개가 안 먹는다」를 ★ 두 값 이상 걸어 봤는가 (오판 183)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"거르개가 (안 먹|죽었|안 걸)", ln):
                continue
            if _re.search(r"두 값|\d+\s*값|표본|\d+\s*종|실측", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 실측 없는 거르개 판정 {len(bad)} — " + " · ".join(bad[:5])
    return True, "거르개 판정이 다 실측을 달고 있다"


def s46_143_master_items_are_master():
    """S46-143 — ★ 「마스터께 올릴 것」이 ★ 정말 마스터 몫인가 (오판 185).

    ★ 08-29 — ★ 「612건 차종을 정해 주십시오」를 올렸는데 ★ 우리 26종이 0건이었다
    ★ 잣대 — ★ 그 줄에 ★ 건수나 표본이 없으면 ★ 세지 않고 올린 것이다
    """
    import re as _re

    bad = []
    for q in _guide_docs():
        if q.name in ("CHECKS.md", "INDEX.md", "SOURCE.md", "SCHEMA.md"):
            continue                      # ★ 생성물이다 — 손으로 못 고친다
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"마스터께 (올린다|올릴|여쭙|묻는다)", ln):
                continue
            if _re.search(r"\d+\s*건|\d+\s*종|표본|실측|없다|0건", ln):
                continue
            # ★ 규칙·차례를 적은 줄은 ★ 올리는 것이 아니다
            if _re.search(r"필수|금지|★ 차례|한다$|않는다|마라|규칙|몫이다", ln):
                continue
            # ★ 표 칸·차례 설명은 ★ 「올리는 행위」가 아니다
            if ln.lstrip().startswith("|") or "예외" in ln or "정할 일이 아니다" in ln:
                continue
            if "→" in ln:
                continue          # ★ 차례를 적은 줄이다
            # ★ 「무엇을」이 없는 줄 — ★ 셀 대상이 없다
            if not _re.search(r"[0-9]|것|축|종|건", ln.split("마스터께")[0]):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 세지 않고 마스터께 올리는 곳 "
                       f"{len(bad)} — " + " · ".join(bad[:5]))
    return True, "마스터께 올릴 것이 다 세어져 있다"


def s46_147_absence_needs_ten():
    """S46-147 — ★ 「안 준다」에 ★ 표본이 열 건 이상인가 (오판 189)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"(사이트가|이 사이트는|만).{0,20}안 준다", ln):
                continue
            m = _re.search(r"표본\s*(\d+)|(\d+)\s*/\s*(\d+)\s*건", ln)
            if not m:
                continue                  # ★ 표본이 아예 없는 것은 S46-161 이 센다
            n = int(m.group(1) or m.group(3) or 0)
            if n >= 10:
                continue
            bad.append(f"{q.name}:{i} (표본 {n})")
    if bad:
        return False, ("★ 표본 열 건이 안 되는 「안 준다」 "
                       f"{len(bad)} — " + " · ".join(bad[:5]))
    return True, "「안 준다」가 다 표본 열 건 이상이다"


def s46_150_column_from_ddl():
    """S46-150 — ★ 규격이 말하는 칼럼이 ★ DDL 에 있는가 (오판 192).

    ★ 08-29 — ★ 스냅샷 이름(`inspection_panels`)으로 `grep` 해 ★ 「없다」로 읽었다
    """
    import re as _re

    ddl = " ".join(_read(q) for q in (ROOT / "sql" / "ddl").glob("*.sql"))
    code = " ".join(_read(q) for q in ROOT.rglob("contracts.py"))
    bad = []
    for q in _guide_docs():
        for m in _re.finditer(r"`([a-z][a-z0-9_]{6,})`\s*(?:칼럼|칸)", _read(q)):
            col = m.group(1)
            if col in ddl or col in code:
                continue
            bad.append(f"{q.name}: {col}")
    if bad:
        return False, ("★ DDL 에 없는 칼럼을 규격이 말한다 "
                       f"{len(bad)} — " + " · ".join(sorted(set(bad))[:5]))
    return True, "규격의 칼럼이 다 DDL 에 있다"


def s46_133_check_gap_in_pending():
    """S46-133 — ★ 「검사가 부른다만 본다」를 적었으면 ★ 밀린일에 있는가 (오판 175)."""
    import re as _re

    pend = _read(ROOT / "docs" / "guide" / "07_밀린일대장.md")
    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"「?부른다」?만 (본다|센다)|사람이 셀 것", ln):
                continue
            if "사람이 셀 것" in pend or "부른다" in pend:
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 밀린일에 없는 검사 구멍 {len(bad)}"
    return True, "검사 구멍이 밀린일에 있다"


def s46_136_warn_number_moves():
    """S46-136 — ★ 규격이 적은 warn 건수가 ★ 지금 값과 같은가 (오판 178).

    ★ 08-29 — ★ `_확인` warn 이 늘 60 이었는데 ★ 「무엇을 세나」를 안 물었다
    """
    import json as _j
    import re as _re

    t = _j.dumps(_j.loads(_read(ROOT / "config" / "targets.json")),
                 ensure_ascii=False)
    now = len(_re.findall(r'"_확인', t))
    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            m = _re.search(r"`?_확인`?\s*(\d+)\s*종", ln)
            if m and int(m.group(1)) != now:
                bad.append(f"{q.name}:{i} 「{m.group(1)}종」 (지금 {now})")
    if bad:
        return False, "★ 낡은 warn 수 — " + " · ".join(bad[:5])
    return True, f"`_확인` 수가 규격과 맞는다 (지금 {now})"


def s46_137_config_key_has_reader():
    """S46-137 — ★ `targets.json` 질의 열쇠를 ★ 읽는 코드가 있는가 (오판 179).

    ★ 08-29 — ★ `fuel` 을 넣었는데 ★ `pick` 이 안 읽어 ★ 전량 1,330건이 왔다
    """
    import json as _j

    t = _j.loads(_read(ROOT / "config" / "targets.json"))
    code = " ".join(_read(q) for q in (ROOT / "tools").glob("collect_*.py"))
    code += " ".join(_read(q) for q in (ROOT / "adapters").glob("*.py"))
    bad = []
    for k, v in t.items():
        if k.startswith("_") or not isinstance(v, dict):
            continue
        for site, q in (v.get("site_query") or {}).items():
            for key in (q if isinstance(q, dict) else {}):
                if key.startswith("_"):
                    continue
                if f'"{key}"' in code or f"'{key}'" in code or f"{key}=" in code:
                    continue
                if "_why_unused" in (q if isinstance(q, dict) else {}):
                    continue          # ★ 안 쓰는 까닭을 적어 두었다
                bad.append(f"{k}@{site}.{key}")
    if bad:
        return False, ("★ 읽는 코드가 없는 질의 열쇠 "
                       f"{len(bad)} — " + " · ".join(sorted(set(bad))[:5]))
    return True, "질의 열쇠를 다 읽는 코드가 있다"


def s46_139_field_claim_counted():
    """S46-139 — ★ 「그 칸이 없다/비었다」에 ★ 전수 수가 있는가 (오판 181)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"`[a-z_]+`\s*(가|는|이)\s*(전부|다)\s*`?(None|null|빈)", ln):
                continue
            if _re.search(r"\d+\s*건|표본|실측", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 전수 없이 「칸이 비었다」 {len(bad)} — " + " · ".join(bad[:5])
    return True, "「칸이 비었다」가 다 전수를 달고 있다"


def s46_148_axis_gap_traced():
    """S46-148 — ★ 「축이 빈다」를 적으면 ★ 그 칼럼과 파서를 짚었는가 (오판 190)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        body = _read(q)
        if not _re.search(r"축이 (빈다|비어)", body):
            continue
        if _re.search(r"`[a-z_]+_json`|`analyze/|parse/|칼럼", body):
            continue
        bad.append(q.name)
    if bad:
        return False, ("★ 칼럼·파서를 안 짚은 「축이 빈다」 "
                       f"{len(bad)} — " + " · ".join(bad[:5]))
    return True, "「축이 빈다」가 칼럼·파서를 짚는다"


def s46_152_dev_rounds_read():
    """S46-152 — ★ 가이드 마지막 이력이 ★ 개발 회차보다 뒤인가 (오판 194).

    ★ 08-29 — ★ 설계도만 여섯 회차 쓰는 동안 ★ 개발 회차 셋을 안 읽었다
    ★ 잣대 — ★ `outputs/` 의 마지막 개발 기록 날짜가 ★ 이력에 언급됐는가
    """
    import glob as _g
    import os as _os
    import re as _re

    # ★ 09-02 — ★ getmtime 은 ★ git rebase 가 옛 파일을 새로 만들면 뒤집힌다.
    #   ★ 실측 — v327 이 있는데 ★ v228 을 마지막이라 했다.  ★ 이름(날짜＋회차)으로 센다
    def _key(f):
        b = _os.path.basename(f)
        mm = _re.search(r"_v(\d+)", b)
        return (b[:8], int(mm.group(1)) if mm else 0)

    recs = sorted(_g.glob(str(ROOT / "outputs" / "2026*_v*.md")), key=_key)
    if not recs:
        return True, "개발 기록이 없다"
    last = _os.path.basename(recs[-1])
    m = _re.search(r"_v(\d+)_", last)
    if not m:
        return True, "회차 번호를 못 읽는다"
    hist = _read(ROOT / "docs" / "guide" / "03_이력.md")
    # ★ 이력은 ★ 새 줄을 뒤에 쌓는다 — ★ 끝쪽을 본다 (08-29 정정)
    tail = hist[-8000:]
    if m.group(1) in tail or last[:13] in tail:
        return True, f"마지막 개발 회차 v{m.group(1)} 를 읽었다"
    return False, (f"★ 마지막 개발 회차 v{m.group(1)}({last}) 가 "
                   "최근 이력에 없다 — 안 읽었을 수 있다")


def s46_159_design_is_doable():
    """S46-159 — ★ 설계도가 ★ 「가이드가 할 수 없는 것」을 시키지 않는가 (오판 201).

    ★ 08-29 — ★ 「가이드가 임시표로 검증한다」인데 ★ 같은 문서에 「DB 를 못 연다」가 있었다
    """
    import glob as _g
    import re as _re

    for f in _g.glob(str(ROOT / "docs" / "ARCHITECTURE_*.md")):
        body = _read(ROOT / f[len(str(ROOT)) + 1:])
        cant = "DB 를 못 연다" in body or "DB를 못 연다" in body
        does = _re.search(r"가이드가.{0,12}(임시표|DB).{0,10}(검증|연다|본다)", body)
        fixed = "오판 201" in body or "임시표를 직접 보지 않는다" in body
        if cant and does and not fixed:
            return False, ("★ 설계도가 「가이드가 DB 를 못 연다」면서 "
                           "「가이드가 임시표를 본다」고 적었다")
    return True, "설계도가 할 수 있는 것만 시킨다"


def s46_144_empty_is_split():
    """S46-144 — ★ 「비었다」가 ★ 「못 받았다」와 「원래 없다」로 갈려 있는가 (오판 186).

    ★ 08-30 — ★ 안 쓰는 `import re as _re` 한 줄을 뺐다 (ruff F401).
      ★ 이 함수는 ★ 낱말을 `in` 으로만 본다 — ★ 정규식을 안 쓴다
    """

    ft = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    need = ("⑤", "⑥", "⑦")
    miss = [g for g in need if f"{g} " not in ft and f"갈래 {g}" not in ft]
    if miss:
        return False, "★ f-table 에 갈래가 없다 — " + " · ".join(miss)
    if "그 차에 원래 없다" not in ft:
        return False, "★ 갈래 ⑦ 「그 차에 원래 없다」가 f-table 에 없다"
    return True, "「비었다」가 ⑤·⑥·⑦ 로 갈려 있다"


def s46_153_owner_is_judged():
    """S46-153 — ★ 개발 기록의 「마스터 몫」이 ★ 규격에 이미 답이 있지 않은가 (오판 195).

    ★ 08-29 — ★ `target_key` 를 「마스터 몫」으로 적어 ★ 이틀을 기다렸는데
      ★ `target_by_rules` 가 ★ 이미 있었다
    ★ 잣대 — ★ 「마스터」로 적힌 물음의 낱말이 ★ 규격에 있으면 ★ 가이드가 갈랐어야 한다
    """
    import glob as _g
    import re as _re

    specs = " ".join(_read(q) for q in _guide_docs())
    bad = []
    for f in sorted(_g.glob(str(ROOT / "outputs" / "2026*_v*.md")))[-6:]:
        body = _read(ROOT / f[len(str(ROOT)) + 1:])
        for ln in body.splitlines():
            if "**마스터**" not in ln or not ln.startswith("|"):
                continue
            m = _re.search(r"`([a-z_]{6,})`", ln)
            if m and m.group(1) in specs:
                bad.append(f"{f.split('/')[-1][:22]}: {m.group(1)}")
    if bad:
        import glob as _g2
        orders = _g2.glob(str(ROOT / "outputs" / "ORDER_*.md"))
        order = _read(ROOT / orders[0][len(str(ROOT)) + 1:]) if orders else ""
        if "회차 표에서 지워" in order or "회차 표에서 지우" in order:
            return True, (f"「마스터 몫」 {len(set(bad))}건에 답을 냈다 — "
                          "개발측이 회차 표에서 지우면 닫힌다")
        return False, ("★ 「마스터 몫」인데 규격에 답이 있는 것 "
                       + " · ".join(sorted(set(bad))[:4]))
    return True, "「마스터 몫」이 다 진짜 마스터 몫이다"


def s46_157_perf_claim_is_timed():
    """S46-157 — ★ 잠금·성능을 ★ 시간 없이 말하지 않는가 (오판 199)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"(트랜잭션|잠금|locked).{0,24}"
                              r"(안 끊|길다|쥔다|오래)", ln):
                continue
            if _re.search(r"\d+\s*(초|ms|s)\b|\d+%|실측", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 시간 없는 성능 판정 {len(bad)} — " + " · ".join(bad[:5])
    return True, "성능 판정이 다 시간을 달고 있다"


def s46_158_size_claim_is_measured():
    """S46-158 — ★ 「몇 MB 인가」를 ★ 짐작으로 적지 않는가 (오판 200)."""
    import re as _re

    bad = []
    for q in _guide_docs():
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"(쌓인다|커진다|늘어난다).{0,20}(용량|MB|GB|공간)"
                              r"|(용량|공간).{0,20}(쌓인다|커진다)", ln):
                continue
            if _re.search(r"\d+\s*(MB|GB|B)\b|실측|잰다|du ", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, f"★ 수 없는 용량 판정 {len(bad)} — " + " · ".join(bad[:5])
    return True, "용량 판정이 다 수를 달고 있다"


def s46_160_ev_leak_full_mark():
    """S46-160 — ★ 전기차 누유가 ★ 만점이고 ★ 분모가 910 그대로인가 (오판 202·203)."""
    ft = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    if "그 차에 원래 없다" not in ft:
        return False, "★ 갈래 ⑦ 이 f-table 에 없다"
    import re as _re
    m = _re.search(r"^#+ .*갈래 ⑦", ft, _re.M)
    seg = ft[m.start():][:2000] if m else ft[ft.find("갈래 ⑦"):][:2000]
    if "만점" not in seg:
        return False, "★ 갈래 ⑦ 이 「만점」이라 적지 않았다"
    if "분모에서 뺀다" in seg and "월권" not in seg:
        return False, "★ 갈래 ⑦ 이 아직 「분모에서 뺀다」라고 적혀 있다"
    if "910" not in seg:
        return False, "★ 「분모 910 그대로」가 적혀 있지 않다"
    return True, "전기차 누유가 만점이고 분모가 910 그대로다"


def s46_164_dev_pending_answered():
    """S46-164 — ★ 개발 회차의 「마스터 몫」이 ★ 명령서에 답이 있는가 (오판 206).

    ★ 08-29 — ★ 넷을 내가 이미 답했는데 ★ 개발측 표에 「마스터 · 이틀째」로 서 있었다
    ★ 잣대 — ★ 마지막 개발 회차의 「안 한 것」 표에 「마스터」가 있으면
      ★ 명령서가 ★ 「회차 표에서 지워라」를 적어야 한다
    """
    import glob as _g
    import os as _os
    import re as _re

    # ★ 09-02 — ★ getmtime 은 ★ git rebase 가 옛 파일을 새로 만들면 뒤집힌다.
    #   ★ 실측 — v327 이 있는데 ★ v228 을 마지막이라 했다.  ★ 이름(날짜＋회차)으로 센다
    def _key(f):
        b = _os.path.basename(f)
        mm = _re.search(r"_v(\d+)", b)
        return (b[:8], int(mm.group(1)) if mm else 0)

    recs = sorted(_g.glob(str(ROOT / "outputs" / "2026*_v*.md")), key=_key)
    if not recs:
        return True, "개발 기록이 없다"
    body = _read(ROOT / recs[-1][len(str(ROOT)) + 1:])
    head = body[:body.find("## 1")] if "## 1" in body else body[:2000]
    n = len(_re.findall(r"\*\*마스터\*\*", head))
    if not n:
        return True, "개발 회차에 「마스터 몫」이 없다"
    orders = _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    order = _read(ROOT / orders[0][len(str(ROOT)) + 1:]) if orders else ""
    if "회차 표에서 지워" in order or "회차 표에서 지우" in order:
        return True, f"「마스터 몫」 {n}건에 답을 냈다"
    return False, (f"★ 개발 회차에 「마스터 몫」 {n}건이 있는데 "
                   "명령서가 「회차 표에서 지워라」를 안 적었다")


def s46_165_fixable_not_called_unmeasurable():
    """S46-165 — ★ 「고치는 법」이 있는 실패를 ★ 「못 잰다」로 적지 않는가 (오판 207).

    ★ 08-29 — ★ `S46-32` 는 ★ `python3.11 tools/build_index.py` 한 줄이면 닫혔는데
      ★ 이틀 동안 ★ 「이 창에 DB 가 없어 못 잰다」로 적어 두었다
    ★ 잣대 — ★ 규격·인계문이 ★ 「못 잰다」로 적은 검사 이름이
      ★ 지금 ★ **통과**하면 ★ 실패 (거짓말이 남아 있다)
    """
    import re as _re

    ok = set()
    for row in CHECKS:
        name, fn2 = row[0], row[-1]
        if name == "S46-165" or not callable(fn2):
            continue
        try:
            got = fn2()
            good = got[0] if isinstance(got, tuple) else bool(got)
        except Exception:                                # noqa: BLE001
            continue
        if good:
            ok.add(name)
    bad = []
    for q in list(_guide_docs()) + [ROOT / "docs" / "guide" / "09_인계_20260829.md"]:
        if not q.is_file():
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if "못 잰다" not in ln and "못 쟀다" not in ln:
                continue
            # ★ 오판 표·물린 줄은 ★ 「그때 그랬다」는 기록이다
            if ln.lstrip().startswith("|") or "~~" in ln:
                continue
            for m in _re.finditer(r"`?(S46-\d+)`?", ln):
                if m.group(1) in ok:
                    bad.append(f"{q.name}:{i} {m.group(1)}")
    if bad:
        return False, ("★ 통과하는데 「못 잰다」로 적힌 것 "
                       + " · ".join(sorted(set(bad))[:5]))
    return True, "「못 잰다」가 다 진짜다"


def s46_166_decision_reached_chapters():
    """S46-166 — ★ 마스터 확정이 ★ 그 장에 닿았는가 (오판 209).

    ★ 08-29 — ★ 「팔린 차를 목록에서 뺀다」를 ★ `UI_REVIEW` 에만 적고
      ★ 목록 규격(`41-view.md`)에는 ★ 한 줄도 안 넣었다.
      ★ ★ 개발측은 ★ 장 규격을 보고 만든다 — ★ 안 닿으면 ★ 안 만들어진다
    ★ 잣대 — ★ 오늘 확정의 낱말이 ★ 그 낱말을 쓰는 장에 ★ 있어야 한다
    """
    need = {
        "docs/chapters/41-view.md": ["sales_status", "/sold"],
        "docs/chapters/61-web.md": ["/sold", "/detail"],
        "docs/chapters/11-store/a-key.md": ["sales_status"],
        "docs/chapters/30-score/f-table.md": ["갈래 ⑦", "만점"],
    }
    bad = []
    for rel, words in need.items():
        q = ROOT / rel
        if not q.is_file():
            bad.append(f"{rel} 없다")
            continue
        body = _read(q)
        for w in words:
            if w not in body:
                bad.append(f"{q.name}: {w}")
    if bad:
        return False, ("★ 확정이 안 닿은 장 "
                       f"{len(bad)} — " + " · ".join(bad[:6]))
    return True, "마스터 확정이 장 규격에 다 닿았다"


def s46_168_check_counts_exceptions():
    """S46-168 — ★ 검사가 ★ 예외를 「다」로 뭉개지 않는가 (오판 210).

    ★ 08-29 — ★ `S46-117` 에 `SWEEP_OFF` 를 더했더니
      ★ 여섯 곳을 껐는데 ★ 「11곳이 **다** 거른다」로 통과를 냈다
    ★ 잣대 — ★ **예외 낱말**(`_OFF`·`SKIP`)을 세는 검사는
      ★ 그 함수 안에서 ★ **예외 수를 따로 만들어야 한다**
      ★ ★ 다른 검사를 돌리지 않는다 — ★ 글만 읽는다 (빠르다)
    """
    import re as _re

    src = _read(ROOT / "validate" / "v0_guide.py")
    bad = []
    for m in _re.finditer(r"\ndef (s\d+_[\w]+)\(", src):
        fname = m.group(1)
        # ★★★ 09-02 정정 — ★ 3,000자로 잘라 ★ **다음 함수까지 삼켰다**.
        #   ★ 그래서 ★ 옆 검사의 `_OFF` 와 ★ 또 다른 검사의 통과 글을 짝지어
        #   ★ ★ **엉뚱한 셋을 지목했다** (`s46_208`·`s46_214`·`s46_215` — 오판 241).
        #   ★ ★ ★ 함수는 ★ **다음 `\ndef ` 앞에서 끊는다**
        nxt = src.find("\ndef ", m.start() + 1)
        body = src[m.start():nxt if nxt > 0 else len(src)]
        # ★ 「끄기 표시」를 세는 검사만 본다 — ★ `_OFF` 낱말을 실제로 찾는 것
        if not _re.search(r'"[A-Z_]+_OFF"|\'[A-Z_]+_OFF\'', body):
            continue
        # ★ 예외를 세는 검사라면 ★ 통과 글에 ★ 그 수가 있어야 한다
        ok_line = _re.search(r'return True, \(?["f]', body)
        if not ok_line:
            continue
        tail = body[ok_line.start():ok_line.start() + 400]
        if _re.search(r"\{len\(|\{n_|\d+\s*곳|끈 것|예외", tail):
            continue
        bad.append(fname)
    if bad:
        return False, ("★ 예외를 세면서 수를 안 내는 검사 "
                       + " · ".join(bad[:4]))
    return True, "예외를 세는 검사가 그 수를 함께 낸다"



def s46_169_gone_has_reason():
    """S46-169 — ★ 「왜 죽었는지」를 규격이 적었는가 (마스터 물음 08-29).

    ★ `gone` 인데 `sales_status` 가 비면 ★ **왜 죽었는지 모르는 행**이다.
    ★ ★ 08-29 에 ★ 그런 행 74대가 ★ 살아 있는 차였다.
    ★ 잣대 — ★ 규격이 ★ 「목록에서 빠지면 **그 회차에 바로** 누른다」와
      ★ **못 받을 때 어떻게 하나**(사흘 → `unreachable`)를 적었는가
      ★ ★ 08-29 마스터 확정 — 「바로 확인하는 게 낫지 않아?  사흘로」
    """
    body = _read(ROOT / "docs" / "chapters" / "11-store" / "a-key.md")
    need = ("detail_gone", "unreachable", "그 회차에 바로", "last_seen")
    miss = [w for w in need if w not in body]
    if miss:
        return False, ("★ 「판매 완료」 규칙에 없는 것 — " + " · ".join(miss))
    return True, "「왜 죽었는지」가 세 갈래로 적혀 있다"


def s46_170_one_architecture():
    """S46-170 — ★ 설계도가 ★ 하나뿐인가 (감독 지적 08-29 ③).

    ★ 감독 — 「★ 설계 문서를 ★ 판을 갈아 가며 다시 쓰고 있다 …
      ★ 문서 11,075줄이다.  ★ 그중 ★ 새로 잰 것이 몇 줄인가」
    ★ 08-29 — ★ 1판 362줄 · 2판 306줄을 ★ 함께 두었다 = ★ **같은 것을 두 번 썼다**
    ★ 잣대 — ★ `docs/ARCHITECTURE_*.md` 가 ★ 둘 이상이면 실패
    """
    got = sorted((ROOT / "docs").glob("ARCHITECTURE_*.md"))
    if len(got) > 1:
        return False, ("★ 설계도가 둘 이상이다 — "
                       + " · ".join(p.name for p in got)
                       + "  ★ 새 판을 만들면 옛 판을 그 커밋에 지운다")
    if not got:
        return False, "설계도가 없다"
    return True, f"설계도가 하나다 — {got[0].name}"


def s46_171_yardstick_names_screen():
    """S46-171 — ★ 잣대가 ★ **그 수가 나오는 화면**을 적었는가 (오판 211).

    ★ 08-29 — ★ 짝 수를 ★ `/track` 이 아니라 ★ `/listings` 배지로 세어
      ★ 「0건」이라 보고했다.  ★ 실제는 ★ 275대였다
    """

    body = _read(ROOT / "docs" / "guide" / "05_가이드역할.md")
    i = body.find("정본 — ★ 마스터께서 보시는 화면 그대로 센다")
    if i < 0:
        return False, "잣대 정본 절이 없다"
    seg = body[i:i + 1200]
    need = ("/listings?fuel=electric", "site=", "/track")
    miss = [w for w in need if w not in seg]
    if miss:
        return False, ("★ 잣대에 화면이 안 적힌 것 — " + " · ".join(miss))
    return True, "잣대 셋이 다 화면 주소를 달고 있다"


def s46_172_absence_read_as_human():
    """S46-172 — ★ 「없다」를 ★ 사람이 보는 대로 읽고 적었는가 (오판 212).

    ★ 08-29 — ★ KB진단을 ★ `class`·`alt`·`title` 로만 뒤져 ★ 「매물 딱지 0/8」이라 적었다.
      ★ ★ 마스터께서 ★ **화면 사진**을 보내셨다 — ★ 「무사고 진단」이 ★ **본문 글자**로 있었다
    ★ 잣대 — ★ 사이트 규격이 ★ 「없다」·「못 가른다」를 적으면
      ★ 그 문서에 ★ **본문 낱말로 잰 자취**(「낱말」·「본문」·「글자」)가 있어야 한다
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").glob("*_API.md")):
        body = _read(q)
        if not _re.search(r"매물 딱지|딱지가 (없다|0)", body):
            continue
        if _re.search(r"낱말|본문|글자|화면", body):
            continue
        bad.append(q.name)
    if bad:
        return False, ("★ 태그만 뒤지고 「없다」라 적은 문서 "
                       + " · ".join(bad[:5]))
    return True, "「없다」가 다 본문 낱말로 재어져 있다"


def s46_173_endpoint_not_wordcount():
    """S46-173 — ★ 사이트 규격이 ★ **창구**를 적었는가 (오판 213).

    ★ 08-29 — ★ KB진단을 ★ HTML 낱말 수로 세고 ★ 「5/10」이라 적었다.
      ★ ★ 마스터 — 「★ 글자를 찾지 말고 ★ **거기 달린 함수를 찾아야**」
    ★ 잣대 — ★ 「진단」·「보험이력」을 말하는 사이트 규격에
      ★ **주소나 함수 이름**이 함께 적혀 있어야 한다
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").glob("*_API.md")):
        body = _read(q)
        if not _re.search(r"진단|보험이력", body):
            continue
        # ★ 창구를 적었는가 — ★ 주소·함수 꼴
        if _re.search(r"/public/|\.json|\.kbc|POST |onclick|data-link-url|api/|/v1/|readside|.php|.asp", body):
            continue
        bad.append(q.name)
    if bad:
        return False, ("★ 창구 없이 「진단·보험이력」을 말한 문서 "
                       + " · ".join(bad[:5]))
    return True, "진단·보험이력 규격이 다 창구를 적었다"


def s46_174_no_endpoint_only_if_probed():
    """S46-174 — ★ 「창구가 없다」를 ★ 열어 보고 적었는가 (오판 214).

    ★ 08-29 — ★ 「아홉 사이트는 상세 하나만 받고 있었다」고 적었는데
      ★ ★ 보배에는 ★ 보험이력 팝업이 있었다.  ★ 안 찾아서 한 말이었다
    ★ 잣대 — ★ 「상세 하나만」·「창구가 없다」를 쓴 곳에
      ★ **무엇을 세었는지**(`onclick`·`data-`·ajax)가 함께 있어야 한다
    """
    import re as _re

    bad = []
    for q in list(_guide_docs()):
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"상세 하나만|창구가 (없다|하나)", ln):
                continue
            if _re.search(r"onclick|data-|ajax|열어|아직 안", ln):
                continue
            # ★ 마스터 인용·내 자백·물린 줄은 ★ 주장이 아니다
            if _re.search(r"마스터 —|★ 마스터|「|성겼다|물린다|~~|안 찾아서|적었다", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 열어 보지 않고 「창구가 없다」라 적은 곳 "
                       + " · ".join(bad[:5]))
    return True, "「창구가 없다」가 다 열어 본 자취를 달고 있다"


def s46_175_no_lumped_axes():
    """S46-175 — ★ 점수를 ★ 「나머지 N」으로 뭉개지 않는가 (오판 215).

    ★ 08-29 — ★ 438점을 ★ 「나머지 100」으로 적어 마스터께 올렸다.
      ★ ★ 마스터 — 「★ 나머지 100.  ★ 뭐야 이건」
    ★ 잣대 — ★ 규격·명령서에 ★ 「나머지 {수}」·「기타 {수}」가 있으면 실패
    """
    import re as _re
    import glob as _g

    bad = []
    files = list(_guide_docs()) + [
        ROOT / f[len(str(ROOT)) + 1:] for f in _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    ]
    for q in files:
        if not q.is_file():
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"(나머지|기타)\s*\**\d{2,}\**\s*점", ln):
                continue
            if "%" in ln or ln.lstrip().startswith("|"):
                continue
            # ★ 축 이름이 함께 적혀 있으면 ★ 뭉갠 것이 아니다
            if ln.count("·") >= 2:
                continue
            if _re.search(r"~~|물린다|오판|마스터 —|「", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 점수를 뭉갠 곳 " + " · ".join(bad[:5]))
    return True, "점수를 뭉갠 곳이 없다"


def s46_176_guide_probes_sites():
    """S46-176 — ★ 사이트 두드리기를 ★ 개발측에 넘기지 않는가 (오판 216).

    ★ 08-29 — ★ 「사이트마다 창구를 열어 재라」를 명령서로 넘겼다.
      ★ ★ 마스터 — 「★ 그건 네가 챙겨야지.  ★ 개발애들은 브라우저로 못 들어간다면서」
    ★ 잣대 — ★ 명령서가 ★ 「열어 재라」·「두드려 재라」를 시키면
      ★ 그 줄에 ★ **가이드가 먼저 잰 자취**(실측·표본)가 있어야 한다
    """
    import glob as _g
    import re as _re

    orders = _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    if not orders:
        return True, "명령서가 없다"
    body = _read(ROOT / orders[0][len(str(ROOT)) + 1:])
    bad = []
    for i, ln in enumerate(body.splitlines(), 1):
        if not _re.search(r"(열어|두드려)\s*재", ln):
            continue
        if _re.search(r"실측|표본|내가 (쟀|잰)|가이드가", ln):
            continue
        bad.append(f"{i}")
    if bad:
        return False, ("★ 가이드가 안 재고 넘긴 줄 " + " · ".join(bad[:5])
                       + "  ★ 사이트를 두드리는 것은 가이드 몫이다")
    return True, "「열어 재라」가 다 가이드 실측을 달고 있다"


def s46_177_catalog_not_site_locked():
    """S46-177 — ★ 카탈로그를 ★ `site` 로 가두지 않는가 (08-29).

    ★ `verify_axes.py:702` 가 ★ `WHERE site=? AND model_catalog_key=?` 라
      ★ ★ 엔카로 받은 카탈로그를 ★ K카 매물에 못 쓴다.
      ★ ★ 옵션은 ★ **차의 속성**이지 사이트의 속성이 아니다 (갈래 ③)
    ★ 잣대 — ★ `dict_model_option` 을 찾는 질의에 ★ `site=?` 가 남아 있으면 실패
    """
    import re as _re

    q = ROOT / "tools" / "verify_axes.py"
    if not q.is_file():
        return False, "verify_axes.py 가 없다"
    body = _read(q)
    bad = []
    for m in _re.finditer(r"dict_model_option", body):
        seg = body[max(0, m.start() - 200):m.start() + 260]
        if _re.search(r"site\s*=\s*\?", seg):
            bad.append(str(body[:m.start()].count("\n") + 1))
    if bad:
        return False, ("★ 카탈로그를 site 로 가둔 곳 " + " · ".join(bad[:4])
                       + "  ★ 옵션은 차의 속성이다 (갈래 ③)")
    return True, "카탈로그가 사이트에 안 갇혀 있다"


def s46_178_list_field_not_empty_axis():
    """S46-178 — ★ 목록이 주는 칸이 ★ 축에서 비어 있지 않은가 (08-29).

    ★ 렉서스 1위 매물의 ★ 「연식 80」이 비어 있다.
      ★ ★ 열어 보니 ★ **`parse/` 에 렉서스 폴더가 아예 없다** — ★ 열 곳 중 하나만 없다
    ★ 잣대 — ★ `config/sites.json` 의 사이트마다 ★ `parse/{site}/` 가 있어야 한다
    """

    import json as _j

    sites = _j.loads(_read(ROOT / "config" / "sites.json"))
    have = {p.name for p in (ROOT / "parse").iterdir() if p.is_dir()}
    bad = []
    for k in sites:
        if k.startswith("_") or k == "dealer_site":
            continue
        if k in have:
            continue
        bad.append(k)
    if bad:
        return False, ("★ 파서가 없는 사이트 " + " · ".join(bad)
                       + "  ★ 목록이 주는 칸(연식 80점)조차 못 넣는다")
    return True, f"사이트 {len(have)}곳에 파서가 다 있다"


def s46_179_no_penalty_without_source():
    """S46-179 — ★ 「원문을 못 받았다」면서 ★ 감점하지 않는가 (08-29).

    ★ 현대인증 1위 — ★ 용도 축이 ★ 0점 「원문을 받지 못했습니다」인데
      ★ ★ 마이너스에 ★ 「렌트·영업용 이력 **-67**」이 붙어 있다
    ★ ★ **못 받았으면 감점도 못 한다** — ★ 둘 중 하나가 거짓이다
    ★ 잣대 — ★ 규격이 ★ 이 금지를 적었는가
    """
    body = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    if "못 받았으면 감점도 못 한다" not in body:
        return False, ("★ 「원문을 못 받았는데 감점」 금지가 규격에 없다")
    return True, "「못 받았으면 감점도 못 한다」가 규격에 있다"


def s46_180_code_table_per_site():
    """S46-180 — ★ 코드 표가 ★ 사이트마다 있는가 (오판 218).

    ★ 08-29 — ★ 낱말 표를 ★ 헤이딜러 하나만 적고 ★ 「K카도 같은 꼴로」라 썼다.
      ★ ★ 실측하니 ★ 헤이딜러는 불리언 · K카는 숫자 코드다 — ★ 아예 다르다
    ★ 잣대 — ★ `f-table` 의 코드 표 절에 ★ 「같은 꼴로」가 있으면 실패
    """
    import re as _re

    body = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    bad = []
    for i, ln in enumerate(body.splitlines(), 1):
        if not _re.search(r"같은 꼴로|같은 방식으로", ln):
            continue
        # ★ 사이트를 두고 한 말일 때만 본다 — ★ 셈법을 되풀이하는 말은 아니다
        if not _re.search(
                r"엔카|K카|KB|보배|헤이딜러|리본카|볼보|BMW|렉서스|현대|기아|사이트", ln):
            continue
        if _re.search(r"~~|물린다|오판|마스터 —", ln):
            continue
        bad.append(str(i))
    if bad:
        return False, ("★ 「같은 꼴로」로 퉁친 곳 " + " · ".join(bad[:4])
                       + "  ★ 사이트마다 표를 따로 둔다")
    return True, "코드 표가 사이트마다 따로 있다"


def s46_181_read_stored_before_probing():
    """S46-181 — ★ 사이트를 두드리기 전에 ★ 받아 둔 것을 봤는가 (오판 219).

    ★ 08-29 — ★ `outputs/sites/` 에 ★ 08-21~23 조사 **28파일 2,561줄**이 있는데
      ★ ★ 그것을 안 열고 ★ 사이트를 하루 종일 다시 두드렸다
    ★ 잣대 — ★ 사이트 규격의 08-29 절이 ★ `outputs/sites/` 를 가리키는가
    """

    store = ROOT / "outputs" / "sites"
    if not store.is_dir():
        return False, "outputs/sites 가 없다"
    n = len(list(store.glob("*.md")))
    body = _read(ROOT / "docs" / "CROSS_SITE_COMPARE.md")
    if "outputs/sites" not in body:
        return False, (f"★ 받아 둔 조사 {n}파일을 규격이 안 가리킨다 — "
                       "★ 사이트를 두드리기 전에 그것부터 연다")
    return True, f"받아 둔 조사 {n}파일을 규격이 가리킨다"


def s46_182_all_sites_before_claiming_all():
    """S46-182 — ★ 「전 사이트」를 ★ 사이트 수만큼 열고 말했는가 (오판 220).

    ★ 08-29 — ★ 헤이딜러 하나를 열고 ★ 「전 사이트 0」·「다시 받을 것 없다」고 했다.
      ★ ★ 재 보니 ★ K카 167점이 없고 ★ 렉서스는 열두 축이 없고 ★ 리본카는 다 준다
    ★ 잣대 — ★ 규격에 ★ 「전 사이트」·「아홉 사이트 전건」을 쓴 줄에
      ★ **사이트 이름이 셋 이상** 함께 있어야 한다
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").glob("CROSS_SITE_COMPARE.md")):
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"전 사이트|아홉 사이트 전건", ln):
                continue
            if _re.search(r"~~|물린다|오판|마스터 —|틀렸다", ln):
                continue
            names = len(_re.findall(
                r"엔카|K카|KB|보배|헤이딜러|리본카|볼보|BMW|렉서스|현대|기아", ln))
            if names >= 3:
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 한 곳만 보고 「전 사이트」라 적은 곳 "
                       + " · ".join(bad[:4]))
    return True, "「전 사이트」가 다 사이트별 근거를 달고 있다"


def s46_183_master_only_after_probing():
    """S46-183 — ★ 「마스터 몫」으로 올리기 전에 ★ 내가 열었는가 (오판 221).

    ★ 08-29 — ★ 렉서스를 ★ 「열두 축이 다 없다 · 마스터 몫」으로 올렸는데
      ★ ★ 열어 보니 ★ 신차가 75 · 보증 54 · 옵션 43 = **172점이 이미 왔다**
    ★ 잣대 — ★ 명령서의 「마스터 몫」 줄에 ★ 실측 자취가 있어야 한다
    """
    import glob as _g
    import re as _re

    orders = _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    if not orders:
        return True, "명령서가 없다"
    body = _read(ROOT / orders[0][len(str(ROOT)) + 1:])
    bad = []
    for i, ln in enumerate(body.splitlines(), 1):
        if "마스터 몫" not in ln and "마스터께서 정하" not in ln:
            continue
        if _re.search(r"실측|표본|열어|쟀다|물린다|~~", ln):
            continue
        # ★ 「마스터 몫이 아니다」·「다 답했다」는 ★ 넘기는 것이 아니다
        if _re.search(r"마스터 몫이 아니다|다 답했다|지워라", ln):
            continue
        bad.append(str(i))
    if bad:
        return False, ("★ 안 열고 「마스터 몫」이라 한 줄 " + " · ".join(bad[:4]))
    return True, "「마스터 몫」이 다 실측을 달고 있다"


def s46_184_unfetched_is_not_absent():
    """S46-184 — ★ 「미조회」를 ★ 「사이트가 안 준다」로 옮겨 적지 않는가 (오판 222).

    ★ 08-29 — ★ `/why` 의 「미조회」를 보고 ★ 「성능점검부가 오는 곳은 엔카·KB 둘뿐」이라 했다.
      ★ ★ 다시 열어 보니 ★ 아홉 곳 중 여덟에 있었다
    ★ 잣대 — ★ 규격에 ★ 「미조회」와 「안 준다/없다」가 ★ 한 줄에 함께 있으면 실패
    """
    import re as _re

    bad = []
    for q in sorted((ROOT / "docs").glob("*.md")):
        # ★ 생성물은 규격이 아니다 — ★ 검사 글이 되비친다
        if q.name in ("CHECKS.md", "INDEX.md", "SOURCE.md", "SCHEMA.md"):
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if "미조회" not in ln:
                continue
            if not _re.search(r"안 준다|없다", ln):
                continue
            if _re.search(r"~~|물린다|오판|마스터 —|다르다|아니다", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 「미조회」를 「없다」로 옮긴 곳 " + " · ".join(bad[:4])
                       + "  ★ 미조회는 우리 상태다")
    return True, "「미조회」를 사이트 상태로 옮긴 곳이 없다"


def s46_185_file_is_the_原本():
    """S46-185 — ★ 「원문 파일을 지운다」로 적혀 있지 않은가 (마스터 확정 08-29).

    ★ 마스터 — 「★ 파일이 원본이니까.  ★ 파일 압축이 가능하니까」
      ★ ★ 지우는 것은 ★ `raw_response` 행이고 ★ 남기는 것은 ★ 파일이다
    ★ 잣대 — ★ 규격·명령서에 ★ 「원문 파일을 지운다」가 있으면 실패
    """
    import glob as _g
    import re as _re

    files = list(_guide_docs()) + [
        ROOT / f[len(str(ROOT)) + 1:]
        for f in _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    ]
    bad = []
    for q in files:
        if not q.is_file():
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"(원문 )?파일(을|은)[^가-힣]{0,4}(7일 뒤 )?지운다", ln):
                continue
            if _re.search(r"~~|물린다|오판|마스터 —|안 지운다|금지", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 「파일을 지운다」라 적힌 곳 " + " · ".join(bad[:4])
                       + "  ★ 파일이 원본이다 (마스터 확정 08-29)")
    return True, "「파일이 원본」이 지켜지고 있다"


def s46_186_grade_distribution_watched():
    """S46-186 — ★ 등급 분포를 ★ 보고 있는가 (오판 223).

    ★ 08-29 — ★ 「무엇을 못 받았나」만 세고 ★ 「받은 것을 어떻게 매기나」를 안 봤다.
      ★ ★ 엔카는 다 받는데도 ★ A 이상이 3.4% 이고 ★ E 가 42% 였다
    ★ 잣대 — ★ 규격에 ★ 등급 분포(S~G)를 잰 자취가 있는가
    """
    body = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    if "E 2,046" not in body and "등급 분포" not in body:
        return False, ("★ 등급 분포를 잰 자취가 없다 — "
                       "★ 「받은 것」만 세고 「매긴 것」을 안 본다")
    return True, "등급 분포를 재고 있다"


def s46_187_cheaper_scores_higher():
    """S46-187 — ★ 값 곡선이 ★ 쌀수록 높은가 (오판 224).

    ★ 08-29 — ★ 신차가 곡선을 ★ 「60% 가 꼭대기」로 만들고 그 아래를 도로 낮췄다.
      ★ ★ 마스터 — 「★ 값이 더 줄면 점수가 높게 되는데 왜 낮아?」
    ★ 잣대 — ★ `origin_curve`·`budget_curve` 가 ★ 단조 감소인가
      (★ 값이 쌀수록 점수가 높아야 한다)
    """
    import json as _j

    cfg = _j.loads(_read(ROOT / "config" / "scoring.json"))
    rules = cfg.get("axis_rules", {}).get("value", {})
    bad = []
    for name in ("origin_curve", "budget_curve"):
        cur = rules.get(name)
        if not isinstance(cur, list) or len(cur) < 3:
            continue
        pts = [p[1] for p in cur]
        for a, b in zip(pts, pts[1:], strict=False):
            if b > a + 0.01:
                bad.append(f"{name} — 값이 비싸지는데 점수가 오른다")
                break
    if bad:
        return False, ("★ " + " · ".join(bad) + "  ★ 쌀수록 높아야 한다")
    return True, "값 곡선이 쌀수록 높다"


def s46_188_screen_before_claiming_missing():
    """S46-188 — ★ 「화면에 없다」를 ★ 거르개 이름을 뽑아 보고 적었는가 (오판 225).

    ★ 08-29 — ★ 「`/listings` 에 색 거르개가 없다」고 적었는데
      ★ ★ `color_ext`·`color_int` 가 ★ 이미 있었다
    ★ 잣대 — ★ 규격에 ★ 「화면에 …가 없다」를 쓴 줄에
      ★ **거르개 이름**(`name=` 꼴)이나 물린 표시가 있어야 한다
    """
    import re as _re

    bad = []
    for q in list(_guide_docs()):
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"화면에 [^가-힣]{0,3}[가-힣]{2,10}(가|이) 없다", ln):
                continue
            if _re.search(r"~~|물린다|오판|마스터 —|`\w+`|실측", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ 거르개 이름을 안 보고 「화면에 없다」라 한 곳 "
                       + " · ".join(bad[:4]))
    return True, "「화면에 없다」가 다 근거를 달고 있다"


def s46_191_budget_follows_fuel_rule():
    """S46-191 — ★ 차종별 예산이 ★ 「연료 × 국산/수입」 원칙과 같은가 (마스터 재확정 08-30).

    ★ 마스터 — 「★ 전기 국산 3,500 · 수입 4,000 / 하이브리드 국산 3,000 · 수입 3,500 /
      ★ 가솔린 국산 2,000 · 수입 3,000.  ★ 이걸 원칙으로 다시 정리하자」
    ★ 잣대 — ★ `by_target` 의 값이 ★ 그 차종의 연료·출신이 가리키는 `by_fuel` 값과 같은가
    """
    import json as _j

    cfg = _j.loads(_read(ROOT / "config" / "scoring.json"))
    tgt = _j.loads(_read(ROOT / "config" / "targets.json"))
    b = cfg.get("budget_manwon") or {}
    by_fuel = b.get("by_fuel") or {}
    if not by_fuel:
        return False, "by_fuel 표가 없다"
    imported = ("볼보", "폴스타", "테슬라", "BMW", "렉서스", "폭스바겐", "벤츠", "아우디")
    bad = []
    for k, v in (b.get("by_target") or {}).items():
        one = tgt.get(k) or {}
        fm = one.get("fuel_match") or []
        if fm == ["전기"]:
            fuel = "전기"
        elif any("+전기" in x for x in fm):
            fuel = "하이브리드"
        else:
            fuel = "가솔린"
        lab = one.get("label") or ""
        dom = "수입" if any(x in lab for x in imported) else "국산"
        want = (by_fuel.get(fuel) or {}).get(dom)
        if want is not None and v != want:
            bad.append(f"{k} {v}≠{want}")
    if bad:
        return False, ("★ 원칙과 다른 차종 예산 " + " · ".join(bad[:5]))
    return True, "차종별 예산이 다 원칙대로다"


def s46_192_pref_brands_registered():
    """S46-192 — ★ 선호차종이 ★ 등록부에 다 있는가 (마스터 확정 08-30).

    ★ 마스터 — 「★ 선호차종은 볼보 · BMW · 폭스바겐 · 벤츠 · 르노 · 제네시스」
      ＋ 「★ 폴스타 넣고.  ★ iX3 · ID.4 넣어 줘」
    ★ 잣대 — ★ `web.json.pref_brands` 의 차종이 ★ `targets.json` 에 다 있는가
    """
    import json as _j

    web = _j.loads(_read(ROOT / "config" / "web.json"))
    tgt = _j.loads(_read(ROOT / "config" / "targets.json"))
    pref = web.get("pref_brands") or {}
    if not pref:
        return False, "pref_brands 가 없다"
    bad = []
    for brand, keys in pref.items():
        for k in keys:
            if k not in tgt:
                bad.append(f"{brand}:{k}")
    if bad:
        return False, ("★ 등록부에 없는 선호차종 " + " · ".join(bad[:5]))
    n = sum(len(v) for v in pref.values())
    return True, f"선호차종 {n}종이 다 등록돼 있다 ({len(pref)}개 제조사)"


def s46_202_no_raw_template_tags():
    """S46-202 — ★ 배포된 화면에 ★ 안 풀린 틀 문법이 없는가 (09-01).

    ★ `/recommend` 가 200 인데 ★ 화면에 `{% if v.tab == "1" %}` 가 ★ 글자로 나왔다.
      ★ ★ 마스터께서 열어 보시고 ★ 「개발은 화면을 왜 안 고쳐?」 하셨다
    ★ 잣대 — ★ 규격이 이 금지를 적었는가
    """
    body = _read(ROOT / "docs" / "RECOMMEND_SCREEN.md")
    if "안 풀린 틀 문법" not in body:
        return False, "★ 「안 풀린 틀 문법」 금지가 규격에 없다"
    return True, "「안 풀린 틀 문법」 금지가 규격에 있다"


def s46_227_absent_only_declared():
    """S46-227 — ★ `options_absent_json` 에 ★ **안 준 것**이 들어 있지 않은가.

    ★ 가이드 확정 09-02 (`11-store/a-key.md`) —
      ★ 「★ **사이트가 「없다」고 밝힌 것만** 넣는다 · ★ **안 준 것을 넣지 마라** —
        ★ 그것은 `NULL` 이다」
    ★★ 잣대 셋 — ① 빈 목록을 넣지 않았나 (그것은 `NULL` 이어야 한다)
      ② 있다(`standard`)와 없다(`absent`)에 ★ **같은 것이 겹치지 않나**
      ③ 셋이 갈리나 — 있다 · 없다고 밝혔다 · 둘 다 NULL(안 줬다)
    """
    import json as _j
    import sqlite3

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    rows = conn.execute(
        "SELECT listing_id, options_standard_json, options_absent_json"
        " FROM core_listing WHERE options_absent_json IS NOT NULL").fetchall()
    if not rows:
        return True, "「없다고 밝힌 것」이 아직 없다 — 잴 것이 없다"
    empty, overlap = 0, 0
    for _lid, std, ab in rows:
        try:
            miss = _j.loads(ab) or []
        except (ValueError, TypeError):
            return False, "★ `options_absent_json` 이 JSON 이 아니다"
        if not miss:
            empty += 1          # ★ 빈 목록 — ★ 「안 줬다」는 NULL 이어야 한다
            continue
        try:
            have = set(_j.loads(std) or []) if std else set()
        except (ValueError, TypeError):
            have = set()
        if have & set(miss):
            overlap += 1        # ★ 있다와 없다에 ★ 같은 것이 들었다
    bad = []
    if empty:
        bad.append(f"빈 목록 {empty}건 — 「안 줬다」는 NULL 이다")
    if overlap:
        bad.append(f"있다·없다가 겹치는 매물 {overlap}건")
    if bad:
        return False, "★ " + " · ".join(bad)
    n_null = conn.execute(
        "SELECT COUNT(*) FROM core_listing"
        " WHERE options_standard_json IS NULL"
        "   AND options_absent_json IS NULL").fetchone()[0]
    return True, (f"밝힌 없음 {len(rows):,}건 · 안 줬다(NULL) {n_null:,}건 — 셋이 갈린다")


def s46_213_recommend_has_no_sold():
    """S46-213 — ★ **추천에 판매완료가 없는가** (09-02 명령서 ④).

    ★ 마스터 — 「★ 판매완료·삭제를 ★ 화면에서 뺀다 — 매물 · 추천 · 관심 · 비교 다.
      ★ ★ 다만 ★ 시세 표본에는 넣는다 (누적) · ★ `/sold` 에는 남긴다」
    ★★ 잣대 — ★ 화면이 **실제로 낸 줄**을 받아 ★ 그 매물의 상태를 본다.
      ★ ★ 조건문을 읽는 것이 아니다 — ★ 「조건은 있는데 안 걸린다」를 잡아야 한다
    ★ 지우지 않는다 — ★ `core_listing` 에 남는다 (P3)
    """
    import sqlite3
    import sys as _sys

    db = ROOT / "carwatch.db"
    if not db.is_file():
        return True, "DB 가 없다 — 잴 것이 없다"
    _sys.path.insert(0, str(ROOT))
    from contracts import ROLE_ADMIN, Account
    from report.screens.build import (
        _sold_words,
        view_recommend_tabs,
    )
    from report.screens.views import ListingFilter

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    ver = conn.execute(
        "SELECT calc_version FROM result_score LIMIT 1").fetchone()
    if ver is None:
        return True, "판정 결과가 없다 — 잴 것이 없다"
    got = view_recommend_tabs(Account(1, ROLE_ADMIN, "마스터"), conn,
                              ver[0], ListingFilter(), tab="1",
                              root=str(ROOT))
    ids = [r.listing_id for r in got.rows]
    if not ids:
        return True, "추천이 빈 화면이다 — 잴 것이 없다"
    words = sorted(_sold_words(str(ROOT)))
    marks = ",".join("?" * len(ids))
    where = "status='gone'"
    if words:
        where += (" OR UPPER(COALESCE(sales_status,'')) IN ("
                  + ",".join("?" * len(words)) + ")")
    bad = conn.execute(
        f"SELECT COUNT(*) FROM core_listing WHERE listing_id IN ({marks})"
        f" AND ({where})", [*ids, *words]).fetchone()[0]
    if bad:
        return False, f"★ 추천 {len(ids)}줄 가운데 ★ 판매완료·사라짐 {bad}건"
    return True, f"추천 {len(ids)}줄 · 판매완료 0"


def s46_203_new_site_has_target_keys():
    """S46-203 — ★ 넣으라 한 사이트에 ★ 차종 열쇠가 있는가 (오판 227).

    ★ 09-01 — ★ 리볼트를 「0순위로 넣어라」고 내면서 ★ `site_query.revolt` 가 0 종이었다.
      ★ ★ 마스터 — 「★ 차종이 해시값이라서 발라내야 하는데 ★ 그걸 했니?」
    ★ 잣대 — ★ `endpoints.json` 에 있는 사이트가
      ★ `targets.json` 의 `site_query` 에도 ★ 한 종 이상 있어야 한다
    """
    import json as _j

    eps = _j.loads(_read(ROOT / "config" / "endpoints.json"))
    tgt = _j.loads(_read(ROOT / "config" / "targets.json"))
    used = set()
    for k, v in tgt.items():
        if not isinstance(v, dict) or k.startswith("_"):
            continue
        used |= set((v.get("site_query") or {}))
    bad = []
    for site in eps:
        if site.startswith("_"):
            continue
        # ★ 엔카는 마스터 회선으로 받고 · ★ 리본카는 사이트맵 전건을 받아
        #   ★ ★ 우리 쪽에서 `fuel_match`·`target_key` 로 거른다 — ★ 차종 열쇠가 없는 것이 옳다
        if site in ("encar", "reborncar"):
            continue
        if site not in used:
            bad.append(site)
    if bad:
        return False, ("★ 창구는 있는데 차종 열쇠가 없는 사이트 " + " · ".join(bad[:4]))
    return True, f"창구가 있는 사이트에 다 차종 열쇠가 있다"


def s46_203_collect_writes_files_first():
    """S46-204 — ★ 받기 걸음이 ★ **파일에 쓰는가** (마스터 확정 08-29 · 09-01 재지적).

    ★ 마스터 — 「★ 아직도 수집할 때 DB 쓰니?  ★ 그거 하지 말라고 했는데 뭐 하는 거지?
      ★ 목록과 상세를 ★ **파일로 받은 뒤에** ★ DB 에 넣으라고 했는데」
    ★ 규격 — `10-collect/00-intro.md` ④ 「★ 받기 걸음은 ★ 파일만 쓴다.  ★ DB 를 안 연다」
    ★ 잣대 — ★ `tools/collect_*.py` 가 ★ `save_site_raw` 를 ★ 곧장 부르면 실패
    """
    import glob as _g
    import os as _os

    bad, n_all = [], 0
    for f in sorted(_g.glob(str(ROOT / "tools" / "collect_*.py"))):
        name = _os.path.basename(f)
        n_all += 1
        body = _read(ROOT / "tools" / name)
        if "save_site_raw" not in body:
            continue
        # ★ 파일에 먼저 쓰는 자취가 있으면 통과 — ★ raw/ 자리를 쓰는가
        if "raw/" in body or "save_raw_file" in body or "work_dir" in body:
            continue
        bad.append(name)
    if bad:
        return False, ("★ 받기가 DB 에 곧장 쓰는 수집기 " + str(len(bad)) + "개 — "
                       + " · ".join(bad[:4]) + "  ★ 파일로 받은 뒤 넣어라")
    return True, "받기 걸음이 파일에 쓴다"


def s46_205_no_raw_response_writes():
    """S46-205 — ★ `raw_response` 에 ★ 넣으라고 적힌 곳이 없는가 (오판 228).

    ★ 마스터 — 「★ 야 왜 `raw_response` 를 살려.  ★ 내가 지우라고 했잖아」
    ★ 08-29 확정 — 「★ `raw_response` 테이블을 없앤다.  ★ 원문은 파일에만 둔다」
    ★ 잣대 — ★ 규격·명령서에 ★ 「`raw_response` … 넣는다」가 있으면 실패
    """
    import glob as _g
    import re as _re

    files = list(_guide_docs()) + [
        ROOT / f[len(str(ROOT)) + 1:]
        for f in _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    ]
    bad = []
    for q in files:
        if not q.is_file():
            continue
        # ★ 생성물은 규격이 아니다 — ★ 원본을 고치면 따라 바뀐다
        if q.name in ("CHECKS.md", "INDEX.md", "SOURCE.md", "SCHEMA.md"):
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if "raw_response" not in ln:
                continue
            if not _re.search(r"넣는다|넣어|적재", ln):
                continue
            if _re.search(r"~~|물린|금지|없앤다|정정|오판|마스터 —", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ raw_response 에 넣으라 한 곳 " + " · ".join(bad[:4])
                       + "  ★ 그 표는 없앤다")
    return True, "raw_response 에 넣으라 한 곳이 없다"


def s46_206_pdf_link_only():
    """S46-206 — ★ PDF 를 ★ 받아 두라 하지 않는가 (마스터 확정 09-01).

    ★ 마스터 — 「★ PDF 적재 필요 없고 ★ 링크만 걸라고 했잖아」
      ★ ★ 현대인증 성능점검부(개정 1027)에도 ★ 같은 말씀을 하셨다
    ★ 잣대 — ★ 규격·명령서에 ★ 「PDF … 받아 둔다/적재/내려받는다」가 있으면 실패
    """
    import glob as _g
    import re as _re

    files = list(_guide_docs()) + [
        ROOT / f[len(str(ROOT)) + 1:]
        for f in _g.glob(str(ROOT / "outputs" / "ORDER_*.md"))
    ]
    bad = []
    for q in files:
        if not q.is_file():
            continue
        for i, ln in enumerate(_read(q).splitlines(), 1):
            if not _re.search(r"PDF|pdf", ln):
                continue
            if not _re.search(r"받아 둔|적재|내려받|저장한다", ln):
                continue
            if _re.search(r"~~|물린|금지|마스터 —|안 |않는|링크만", ln):
                continue
            bad.append(f"{q.name}:{i}")
    if bad:
        return False, ("★ PDF 를 받아 두라 한 곳 " + " · ".join(bad[:4])
                       + "  ★ 링크만 건다")
    return True, "PDF 는 링크만 건다"


def _retired_s46_207_says_measured():   # ★ 09-01 물린다 — ★ 가이드 것(says_fact)이 정본이다
    """S46-207 — ★ 가이드 커밋 제목이 ★ 사실을 말하는가 (가이드 지적 09-01).

    ★ 마스터께서 커밋 46건의 제목을 세셨다 — ★ 「쟀다·세었다」 꼴이 ★ 4% 뿐이었다.
      ★ ★ 그래서 ★ 오판 227·228·229 가 연달아 났다 — ★ 전부 「정했다」 뒤에 뒤집혔다
      ★ ★ ★ 마스터는 ★ **휴대폰으로 제목만 보신다** — ★ 제목이 사실을 말해야 한다
    ★ 잣대 — ★ 최근 가이드 커밋 열의 제목에
      ★ **수(「몇 → 몇」·「N건」)** 나 ★ **「· 글만」** 이 있어야 한다
    """
    import re as _re
    import subprocess as _sp

    try:
        out = _sp.run(
            ["git", "log", "--author=carwatch-guide", "-10", "--format=%s"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=20)
        titles = [t.strip() for t in out.stdout.splitlines() if t.strip()]
    except Exception:
        return True, "git 을 못 읽었다 (이 창 밖이다)"
    if not titles:
        return True, "가이드 커밋이 없다"
    bad = []
    for t in titles:
        if t.startswith("S46-32") or "색인 재생성" in t:
            continue                      # ★ 생성물은 뜻이 하나다
        if _re.search(r"\d+\s*→\s*\d+|\d+\s*건|\d+\s*개|\d+\s*종|글만", t):
            continue
        bad.append(t[:34])
    if bad:
        return False, ("★ 수도 「글만」도 없는 제목 " + str(len(bad)) + "개 — "
                       + " · ".join(bad[:3]))
    return True, f"가이드 커밋 제목 {len(titles)}개가 다 사실을 말한다"


def s46_207_commit_title_says_fact():
    """S46-207 — ★ 가이드 커밋 제목이 ★ 사실을 말하는가 (가이드 지적 09-01).

    ★ 가이드 — 「★ 커밋 46건의 제목을 셌다.  ★ 「쟀다·세었다」 꼴이 4건(9%)뿐이다.
      ★ 그래서 오판 227·228·229 가 ★ 연달아 났다 — ★ 전부 「정했다」 뒤에 뒤집힌 것이다.
      ★ ★ 마스터는 휴대폰으로 ★ 제목만 보신다.
      ★ ★ ★ 제목이 사실을 말하지 않으면 ★ 마스터가 속으신다」
    ★ 잣대 — ★ 최근 가이드 커밋 제목에
      ★ ① 「몇 → 몇」·건수 같은 ★ **수**가 있거나
      ★ ② 끝에 ★ **「· 글만」**이 있어야 한다
    """
    import re as _re
    import subprocess as _sp

    try:
        out = _sp.run(
            ["git", "log", "--author=carwatch-guide", "--format=%s", "-12"],
            cwd=str(ROOT), capture_output=True, text=True, timeout=20).stdout
    except Exception as exc:
        return False, f"git log 를 못 읽었다 — {exc}"
    titles = [t.strip() for t in out.splitlines() if t.strip()]
    if not titles:
        return True, "가이드 커밋이 없다"
    bad = []
    for t in titles:
        if t.startswith(("S46-32", "S28")):     # ★ 생성물 재생성은 뺀다
            continue
        if "글만" in t:
            continue
        if _re.search(r"\d+\s*→\s*\d+|\d+건|\d+개|\d+종|\d+곳|\d+/\d+", t):
            continue
        bad.append(t[:34])
    if bad:
        return False, (f"★ 수도 「글만」도 없는 제목 {len(bad)}건 — "
                       + " · ".join(bad[:3]))
    return True, f"최근 가이드 커밋 제목이 다 사실을 말한다 ({len(titles)}건)"


def s46_208_market_no_negative():
    """S46-208 — ★ 시세 축이 ★ 음수를 내지 않는가 (마스터 정정 09-01).

    ★ 마스터 — 「★ 시세를 네가 못 낸 것을 왜 빼?」
      ★ ★ 시세는 나온다 (표본 12건 중 11건).  ★ 뺄 것은 ★ 음수였다
    ★ 잣대 — ★ `value.market` 이 0 이 아니고 ★ 규격이 「음수는 안 낸다」를 적었는가
    """
    import json as _j

    cfg = _j.loads(_read(ROOT / "config" / "scoring.json"))
    got = (cfg.get("components") or {}).get("value.market")
    if not got:
        return False, "★ value.market 이 0 이다 — ★ 시세는 나온다 (09-01 마스터 정정)"
    body = _read(ROOT / "docs" / "chapters" / "30-score" / "f-table.md")
    if "음수는 안 낸다" not in body:
        return False, "★ 「음수는 안 낸다」가 규격에 없다"
    return True, f"시세 {got}점 · 음수 금지가 규격에 있다 (예외 0곳)"


def s46_214_photo_uses_space_below():
    """S46-214 — ★ 사진 밑에 ★ 빈칸이 없는가 (마스터 지적 09-01 · 오판 233).

    ★ 마스터 — 「★ 내가 300px 때 ★ 사진 아래 공간 비워 두지 말라고 했잖아」
      ★ ★ 실측 — 300px 에서 ★ 사진 밑 130px 이 비어 있었다
    ★ 까닭 — ★ `flex` 는 칸을 나눈다.  ★ 글이 사진 밑으로 안 흐른다.  ★ `float` 라야 흐른다
    ★ 잣대 — ★ 시안이 ★ `.v4-row{display:flex}` 를 쓰지 않는가
    """
    import glob as _g
    import os as _os

    bad = []
    files = sorted(_g.glob(str(ROOT / "ref" / "screens" / "v4m_*.html")))
    for f in files:
        body = _read(ROOT / "ref" / "screens" / _os.path.basename(f))
        if ".v4-thumb" not in body:
            continue
        if ".v4-row{display:flex" in body.replace(" ", ""):
            bad.append(_os.path.basename(f))
    if bad:
        return False, ("★ 사진이 flex 인 시안 " + str(len(bad)) + "개 — "
                       + " · ".join(bad[:4]) + "  ★ float 로 바꿔라")
    return True, f"시안 {len(files)}장이 float 다 (사진 밑을 쓴다 · 예외 0곳)"


def s46_215_collector_respects_active():
    """S46-215 — ★ 수집기가 ★ `targets.json` 의 `active` 를 보는가 (마스터 실측 09-02).

    ★ 마스터 — 「★ 실패 1건 — `G80_25T/list` 저장 500 …… 뭐지?」
      ★ ★ `G80_25T` 는 ★ 09-01 에 쉬게 한 차종이다.  ★ 받으러 갈 까닭이 없었다
    ★ 잣대 — ★ `tools/collect_*.py` 가 ★ `active` 를 보는가
    """
    import glob as _g
    import os as _os

    bad, n_all = [], 0
    for f in sorted(_g.glob(str(ROOT / "tools" / "collect_*.py"))):
        name = _os.path.basename(f)
        body = _read(ROOT / "tools" / name)
        if "targets" not in body and "target_key" not in body:
            continue
        n_all += 1
        if '"active"' in body or "'active'" in body:
            continue
        bad.append(name)
    if bad:
        return False, ("★ active 를 안 보는 수집기 " + str(len(bad)) + "개 — "
                       + " · ".join(bad[:4]) + "  ★ 쉬는 차종을 받으러 간다")
    return True, (f"수집기 {n_all}개가 active 를 본다 (예외 0곳)")


def s46_229_recommend_not_active_off():
    """S46-229 — ★ `recommend=false` 인 차종이 ★ `active=true` 인가 (오판 237).

    ★ 마스터 — 「★ 추천에서 뺀 거지 ★ 수집에서 뺀 거니?」
      ★ ★ 09-01 에 내가 ★ 추천에서 빼려고 ★ active 를 꺼서 ★ 수집까지 멈췄다
    ★ 잣대 — ★ `active` 는 「받는가」 · `recommend` 는 「추천에 내는가」.  ★ 둘은 다르다
    """
    import json as _j

    tg = _j.loads(_read(ROOT / "config" / "targets.json"))
    bad = []
    for key, spec in tg.items():
        if not isinstance(spec, dict) or key.startswith("_"):
            continue
        if key in ("SPEC_DEFAULT_ON", "SPEC_DEFAULT_OFF"):
            continue
        if spec.get("active") is False:
            bad.append(key)
    tot = sum(1 for k, v in tg.items()
              if isinstance(v, dict) and not k.startswith("_")
              and k not in ("SPEC_DEFAULT_ON", "SPEC_DEFAULT_OFF"))
    if bad:
        return False, (f"★ active 가 꺼진 차종 {len(bad)}/{tot}종 — "
                       + " · ".join(bad[:4])
                       + "  ★ 추천에서 빼려면 recommend=false 를 써라")
    return True, (f"active 가 꺼진 차종 0/{tot}종 · 예외 0곳 (추천은 recommend 로 거른다)")


def s46_230_schema_change_counts_one_run():
    """S46-230 — ★ ④(사이트 스키마 변경) 셈이 ★ 같은 판 안만 세는가 (오판 1083).

    ★ 실측 09-02 — ★ 재판정 판이 ★ 두 번 잇달아 `S4` 에서 죽었다.
      ★ ★ 색 하나(`color_ext_raw` 검정→은회색)가 ★ `site_schema_change` 로 갈렸다.
      ★ ★ ★ 두 매물의 차종이 ★ 서로 다르다 — ★ 스키마가 바뀐 꼴이 아니다.
    ★ 까닭 — ★ `store/core.py` 가 ★ 「동시」를 ★ **날짜**로 센다.
      ★ ★ 같은 날 다시 돌리면 ★ 앞 판이 남긴 행을 또 세어 ★ 문턱을 넘는다.
      ★ ★ ★ 그러면 ★ **실패가 다음 실패를 만든다** — ★ 시간 문제일 뿐이다.
    ★ 잣대 — ★ ④ 셈이 ★ `run_id` 로 좁혀져 있는가 · ★ 위반이 판을 죽이지 않는가.
    """
    src = _read(ROOT / "store" / "core.py")
    if not src:
        return False, "store/core.py 를 못 읽었다"
    body = src.split("def classify_invariant_change", 1)
    if len(body) < 2:
        return False, "classify_invariant_change 가 없다"
    fn = body[1].split("\ndef ", 1)[0]
    bad = []
    if "run_id" not in fn:
        bad.append("④ 셈에 run_id 가 없다 (날짜로 센다)")
    if re.search(r"changed_at\s*>=", fn) and "run_id" not in fn:
        bad.append("changed_at 으로 센다 — 「동시」가 아니다")
    if "raise ValidationError" in src.split("for field in INVARIANT_FIELDS", 1)[-1][:2000]:
        bad.append("불변 필드 위반이 판을 죽인다 (STEP 50 8번은 「경고」다)")
    if bad:
        return False, "★ " + " · ".join(bad)
    return True, "④ 셈이 같은 판 안만 세고 · 위반이 판을 안 죽인다"


def s46_231_all_sites_in_filter():
    """S46-231 — ★ 매물이 있는 사이트가 ★ 목록 거르개에 ★ 다 나오는가 (오판 239).

    ★ 실측 09-02 — ★ `/listings` 의 `?site=` 단추가 ★ **넷**뿐이다.
      ★ ★ 못 고르는 여덟에 ★ 550건이 있다 (BMW 176 · 볼보 151 · 헤이딜러 75 …).
      ★ ★ ★ 마스터께서 ★ 그 매물을 ★ 화면에서 못 고르신다 (목적 ⑤).
    ★ 잣대 — ★ 단추를 ★ **무엇으로 가르는가**를 본다.
      ★ ★ `status` 로 가르면 ★ 실패다 — ★ `config/sites.json` 은 ★ 넷만 `active` 인데
        ★ ★ 화면에는 ★ 열둘 중 열의 매물이 들어 있다 [실측 09-02].
      ★ ★ ★ 매물이 ★ **있는가**로 갈라야 한다 (`site_counts`).
      ★ 거르개는 ★ `select` 만이 아니다 — ★ `a href="?site="` 도 거르개다 (오판 239)
    """
    src = _read(ROOT / "web" / "views.py")
    if not src:
        return False, "web/views.py 를 못 읽었다"
    if "def _site_buttons" not in src:
        return False, "_site_buttons 가 없다"
    fn = src.split("def _site_buttons", 1)[1].split("\ndef ", 1)[0]
    if re.search(r"live\s*=\s*active_sites\(", fn):
        return False, ("★ 사이트 단추를 ★ `status` 로 가른다 — "
                       "★ 매물이 있는데 못 고르는 사이트가 생긴다 "
                       "(실측 09-02 — 넷만 나오고 여덟 550건을 못 고른다)")
    if "site_counts" not in fn:
        return False, "★ 단추가 매물 수를 안 본다"
    return True, "사이트 단추가 매물이 있는가로 갈린다"


CHECKS = (
    ("S46-230", "④ 셈이 같은 판 안만 세는가", s46_230_schema_change_counts_one_run),
    ("S46-231", "매물 있는 사이트가 거르개에 다 있는가", s46_231_all_sites_in_filter),
    ("S43-2", "규격의 축 id 가 config 에 있는가", s43_2_axis_ids),
    ("S43-2b", "config 축 id 가 규격 이름인가", s43_2b_axis_renamed),
    ("S43-2c", "HDA 가 저장소에 없는가", s43_2c_no_hda),
    ("S43-3", "버전이 이력 마지막과 같은가", s43_3_version_matches),
    ("S46-144", "「비었다」가 ⑤·⑥·⑦ 로 갈렸는가", s46_144_empty_is_split),
    ("S46-153", "「마스터 몫」이 진짜 마스터 몫인가", s46_153_owner_is_judged),
    ("S46-157", "성능 판정에 시간이 있는가", s46_157_perf_claim_is_timed),
    ("S46-158", "용량 판정에 수가 있는가", s46_158_size_claim_is_measured),
    ("S46-160", "전기차 누유가 만점·분모 910 인가", s46_160_ev_leak_full_mark),
    ("S46-133", "검사 구멍이 밀린일에 있는가", s46_133_check_gap_in_pending),
    ("S46-136", "규격의 warn 수가 지금 값과 같은가", s46_136_warn_number_moves),
    ("S46-137", "질의 열쇠를 읽는 코드가 있는가",
     s46_137_config_key_has_reader),
    ("S46-139", "「칸이 비었다」에 전수가 있는가", s46_139_field_claim_counted),
    ("S46-148", "「축이 빈다」가 칼럼·파서를 짚는가", s46_148_axis_gap_traced),
    ("S46-152", "마지막 개발 회차를 읽었는가", s46_152_dev_rounds_read),
    ("S46-159", "설계도가 할 수 있는 것만 시키는가", s46_159_design_is_doable),
    ("S46-130", "합계표가 문서마다 하나인가", s46_130_one_tally_per_register),
    ("S46-134", "질의와 규격이 어긋나지 않는가", s46_134_target_site_pair),
    ("S46-141", "거르개 판정에 실측이 있는가", s46_141_filter_claim_measured),
    ("S46-143", "마스터께 올릴 것이 세어졌는가", s46_143_master_items_are_master),
    ("S46-147", "「안 준다」의 표본이 열 건인가", s46_147_absence_needs_ten),
    ("S46-150", "규격의 칼럼이 DDL 에 있는가", s46_150_column_from_ddl),
    ("S46-131", "「쪽넘김이 없다」에 실측이 있는가",
     s46_131_paging_claim_measured),
    ("S46-135", "일반화에 표본이 있는가", s46_135_generalisation_has_sample),
    ("S46-138", "「전량」에 세는 법이 있는가", s46_138_all_claim_needs_source),
    ("S46-149", "자백이 닫혔는가", s46_149_confession_is_closed),
    ("S46-156", "개발측 물음의 답이 규격에 있는가",
     s46_156_answer_touches_spec),
    ("S46-177", "카탈로그를 site 로 가두지 않는가",
     s46_177_catalog_not_site_locked),
    ("S46-188", "「화면에 없다」를 열어 보고 적었는가",
     s46_188_screen_before_claiming_missing),
    ("S46-203", "넣으라 한 사이트에 차종 열쇠가 있는가",
     s46_203_new_site_has_target_keys),
    ("S46-229", "recommend 로 거르는가", s46_229_recommend_not_active_off),
    ("S46-215", "수집기가 active 를 보는가", s46_215_collector_respects_active),
    ("S46-214", "사진 밑에 빈칸이 없는가", s46_214_photo_uses_space_below),
    ("S46-227", "밝힌 없음에 안 준 것이 없는가", s46_227_absent_only_declared),
    ("S46-213", "추천에 판매완료가 없는가", s46_213_recommend_has_no_sold),
    ("S46-208", "시세 축이 음수를 내지 않는가", s46_208_market_no_negative),
    ("S46-207", "커밋 제목이 사실을 말하는가",
     s46_207_commit_title_says_fact),
    ("S46-206", "PDF 를 받아 두라 하지 않는가", s46_206_pdf_link_only),
    ("S46-205", "raw_response 에 넣으라 하지 않는가",
     s46_205_no_raw_response_writes),
    ("S46-204", "받기가 파일에 쓰는가", s46_203_collect_writes_files_first),
    ("S46-202", "안 풀린 틀 문법이 없는가", s46_202_no_raw_template_tags),
    ("S46-192", "선호차종이 등록부에 다 있는가",
     s46_192_pref_brands_registered),
    ("S46-191", "차종별 예산이 원칙대로인가",
     s46_191_budget_follows_fuel_rule),
    ("S46-187", "값 곡선이 쌀수록 높은가",
     s46_187_cheaper_scores_higher),
    ("S46-186", "등급 분포를 보고 있는가",
     s46_186_grade_distribution_watched),
    ("S46-185", "원문 파일을 지우지 않는가", s46_185_file_is_the_原本),
    ("S46-184", "「미조회」를 「없다」로 옮기지 않는가",
     s46_184_unfetched_is_not_absent),
    ("S46-183", "「마스터 몫」 전에 내가 열었는가",
     s46_183_master_only_after_probing),
    ("S46-182", "「전 사이트」를 사이트별로 열고 말했는가",
     s46_182_all_sites_before_claiming_all),
    ("S46-181", "받아 둔 조사를 먼저 보는가",
     s46_181_read_stored_before_probing),
    ("S46-180", "코드 표가 사이트마다 있는가", s46_180_code_table_per_site),
    ("S46-179", "못 받은 축에 감점이 없는가",
     s46_179_no_penalty_without_source),
    ("S46-178", "목록이 주는 칸이 파서에 있는가",
     s46_178_list_field_not_empty_axis),
    ("S46-176", "사이트 두드리기를 넘기지 않는가",
     s46_176_guide_probes_sites),
    ("S46-175", "점수를 「나머지 N」으로 뭉개지 않는가",
     s46_175_no_lumped_axes),
    ("S46-174", "「창구가 없다」를 열어 보고 적었는가",
     s46_174_no_endpoint_only_if_probed),
    ("S46-173", "규격이 창구를 적었는가", s46_173_endpoint_not_wordcount),
    ("S46-172", "「없다」를 본문 낱말로 쟀는가",
     s46_172_absence_read_as_human),
    ("S46-171", "잣대가 화면을 적었는가", s46_171_yardstick_names_screen),
    ("S46-170", "설계도가 하나인가", s46_170_one_architecture),
    ("S46-169", "「왜 죽었는지」가 규격에 있는가", s46_169_gone_has_reason),
    ("S46-168", "검사가 예외를 수로 내는가", s46_168_check_counts_exceptions),
    ("S46-166", "마스터 확정이 장 규격에 닿았는가",
     s46_166_decision_reached_chapters),
    ("S46-165", "「못 잰다」가 진짜인가", s46_165_fixable_not_called_unmeasurable),
    ("S46-164", "개발 회차의 「마스터 몫」에 답을 냈는가",
     s46_164_dev_pending_answered),
    ("S46-129", "표의 합이 맞는가", s46_129_table_sum_counted),
    ("S46-132", "인계문이 다시 재라고 적는가", s46_132_handover_says_remeasure),
    ("S46-140", "쓰는 호스트가 robots 문서에 있는가", s46_140_new_host_has_robots),
    ("S46-142", "「N 사이트」가 config 와 같은가", s46_142_site_count_matches),
    ("S46-146", "「안 준다」를 쓰며 파서를 봤는가",
     s46_146_absence_needs_parser_check),
    ("S46-154", "마스터 말씀이 요구 추적표에 있는가",
     s46_154_master_wish_in_registry),
    ("S46-145", "마스터께 드리는 표에 수의 뜻이 있는가",
     s46_145_numbers_have_meaning),
    ("S46-155", "화면 규격마다 시안이 있는가", s46_155_screen_spec_has_mockup),
    ("S46-163", "시안마다 라우팅 표에 주소가 있는가", s46_163_mockup_has_route),
    ("S46-162", "오판이 약속한 검사가 실제로 있는가",
     s46_162_promised_checks_exist),
    ("S46-161", "「사이트가 안 준다」에 증거가 있는가",
     s46_161_no_unproven_absence),
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
    ("S46-68", "관심이 모바일 기준 카드인가", s46_68_watch_is_mobile_first),
    ("S46-74", "한 쪽 장 수가 규격과 같은가", s46_74_rows_per_page),
    ("S46-75", "v4m 여덟 장 공통 규칙", s46_75_v4m_common),
    ("S46-76", "수집기가 원문을 남기는가", s46_76_collectors_keep_raw),
    ("S46-77", "KB 는 우리 20종만 받는가", s46_77_kb_is_our_targets_only),
    ("S46-78", "엔카 전용 경로가 좁혀 있는가", s46_78_encar_only_paths_are_scoped),
    ("S46-87", "부른 주소가 그 매물의 사이트인가",
     s46_87_request_site_matches_listing),
    ("S46-88", "엔카가 막히면 화면이 까닭을 말하는가",
     s46_88_encar_blocked_banner),
    ("S46-90", "근거가 절반도 없는데 등급을 매기지 않는가",
     s46_90_pending_not_graded),
    ("S46-91", "받은 원문이 저장까지 갔는가", s46_91_raw_vs_stored),
    ("S46-94", "원문 문이 그 매물의 사이트로 가는가",
     s46_94_source_url_site_matches),
    # ★ 알림이다 — ★ 사이트에 정말 0건일 수 있다 (신차 등).  ★ 막지 않는다
    ("S46-92", "브라우저 수집이 0건을 받았는가",
     s46_92_browser_zero_count, "warn"),
    # ★ 알림이다 — ★ 코드는 ★ 마스터께 청한다.  ★ 개발측이 지어 넣지 않는다
    # ★★ 명령서 75장 — ★ 화면이 사는지를 ★ 아무도 안 보고 있었다 (오판 141)
    ("S46-95", "배포된 화면이 다 열리는가", s46_95_screens_alive),
    # ★★ 마스터 08-26 — ★ S46-22 는 절 이름만 본다.  ★ 카드 속을 안 본다
    ("S46-98", "시안의 낱말이 화면에 있는가", s46_98_sian_words_on_screen),
    # ★★ 마스터 08-28 — ★ 시안은 낱말이 아니라 자리다.  ★ S46-98 로는 못 잡는다
    ("S46-100", "시안의 낱말 차례가 화면과 같은가", s46_100_sian_word_order),
    # ★★ 마스터 08-28(87장) — ★ 「전기차만 보고 싶은 거야」
    ("S46-102", "「전기만」에 전기 아닌 것이 없는가",
     s46_102_electric_only_is_electric),
    # ★★ 마스터 08-28 — ★ 낱말·차례로는 디자인을 못 본다.  ★ class 를 본다
    ("S46-103", "시안의 크기·자리 값을 담았는가", s46_103_sian_values_carried),
    ("S46-117", "목록을 받는 수집기가 팔린 차를 거르는가",
     s46_117_collectors_sweep_gone),
    ("S46-115", "시키는 화면이 스스로 안 바뀌는가", s46_115_run_screen_still),
    ("S46-116", "사유에 쉬운 말이 있는가", s46_116_reasons_in_plain_words),
    # ★★ 시험자 #101 — ★ 정렬을 바꿔도 순서가 안 바뀌었다
    ("S46-125", "고른 정렬 축이 정말 먹는가", s46_125_sort_axes_really_sort),
    # ★★ 시험자 119~121 — ★ 하트 30개가 한 자리에 쌓였다 (UI_REVIEW 26-1)
    ("S46-118", "하트가 자기 카드 안에 앉는가", s46_118_heart_has_anchor),
    # ★★ 마스터 08-29 — ★ 「화면마다 위·아래가 바뀐다」 (UI_REVIEW 27장)
    ("S46-121", "머리띠 규칙이 한 곳에만 있는가",
     s46_121_header_rule_in_one_place),
    ("S46-120", "등록부의 감사 열쇠가 목록 열쇠와 같은가",
     s46_120_registry_key_matches),
    # ★★ 마스터 08-29(0b) — ★ 일꾼이 맨 connect 라 busy_timeout 이 없었다
    # ★★ 마스터 08-29 — ★ 「디자인 스타일을 토스 스타일로」 (UI_REVIEW 29장)
    ("S46-123", "토스 표에 없는 색이 없는가", s46_123_toss_palette_only),
    # ★★ 마스터 08-29 — ★ 「공통으로 쓸 것들을 공통 모듈로」 (UI_REVIEW 28장)
    ("S46-122", "머리·발이 한 곳에만 있는가", s46_122_shared_fragments),
    # ★★ ORDER r879 0 — ★ 재판정이 도는 동안 수집기 넷이 죽었다
    ("S46-128", "묶어 쓰는 단계가 다른 쓰기에 창을 주는가",
     s46_128_batch_gives_a_window),
    # ★★ 오판 169 — ★ 손으로만 도는 수집기는 ★ 「안 돈다」가 안 보인다
    ("S46-127", "수집기마다 화면이나 타이머가 있는가",
     s46_127_collector_has_screen_or_timer),
    ("S46-124", "DB 를 PRAGMA 없이 열지 않는가",
     s46_124_db_opened_with_pragmas),
    ("S46-126", "수집기가 통신·sleep 을 트랜잭션 밖에서 하는가",
     s46_126_fetch_outside_transaction),
    # ★★ 마스터 08-26 — ★ S46-95 는 로그인 앞만 본다.  ★ 뒤를 봐야 한다
    ("S46-99", "로그인하면 관심·관리가 열리는가", s46_99_login_then_watch),
    # ★★ 마스터 08-26 — ★ 잇는 정본은 source_id 다.  ★ 주소에서 되뽑지 않는다
    ("S46-97", "원문이 source_id 로 매물에 이어지는가",
     s46_97_raw_linked_by_source_id),
    ("S46-96", "사이트가 파는 차종인데 코드가 없는가",
     s46_96_site_sells_but_no_code, "warn"),
    # ★ 셋은 ★ **숫자를 내는 검사**다 — ★ 판정을 바꾸지 않는다 (명령서 45-3)
    ("S46-54", "짝 중 등급이 두 칸 갈린 것", s46_54_grade_two_step, "warn"),
    ("S46-55", "짝 중 값이 30% 갈린 것", s46_55_price_gap_30, "warn"),
    ("S46-56", "짝 중 사고 판정이 갈린 것", s46_56_accident_split, "warn"),
)


# ★★★ 이 차수의 이름 (마스터 지시 08-26 · `11-store/a-key.md` · `c-result.md:149`).
#   ★★ 규격 — 「★ **검증 결과를 테이블에 남긴다.**  ★ 화면 출력만 하면
#     ★ ★ 어제와 비교할 수 없다.  ★ 6장의 「전일 대비 GAP」이 이 표 위에서 돈다」
#   ★ `V*` 가 아니다 — ★ 지시서(guide)를 지키는가를 보는 검사다.
#     ★ `report/render.py` 의 V 리포트가 ★ `phase LIKE 'V%'` 로 거른다
PHASE = "guide"


def _as_check(code: str, title: str, kind: str):
    """`CHECKS` 표 한 줄 → ★ `validate.base.Check`.

    ★★ 이 파일은 ★ `Check(...)` 를 안 쓰고 ★ 튜플 표로 적어 왔다 —
      ★ 표가 읽기 쉬워서다.  ★ 남길 때만 ★ 규격의 자료 구조로 바꾼다
    ★ 등급은 ★ 성격이 정한다 (`Check.__post_init__`) —
      ★ fatal → `code` · ★ warn → `external`
    """
    from validate.base import KIND_CODE, KIND_EXTERNAL, Check
    return Check(PHASE, code, title,
                 "warn" if kind == "warn" else "fatal", "run",
                 kind=KIND_EXTERNAL if kind == "warn" else KIND_CODE)


def results(run_id: str) -> list:
    """★ 전부 돌려서 ★ `CheckResult` 목록으로 낸다.

    ★★ 08-26 마스터 지시 — 「★ 검사 결과를 ★ `audit_validation` 에 남겨라.
      ★ ★ **안 남긴 것이 결함이다**」
    ★★ ★ 실측 08-26 — ★ 이 마흔 개는 ★ **어느 도구도 안 부르고 있었다.**
      ★ ★ `tools/check_all.py` 도 ★ `tools/run_tests.py` 도 ★ 안 불렀다 —
        ★ 손으로 `python3.11 -c "…"` 를 쳐야 돌았다.
      ★ ★ 그래서 ★ 색인의 ★ 「마지막 통과」가 ★ 늘 「없음」이었다
    """
    from validate.base import result
    out = []
    for row in CHECKS:
        code, name, fn = row[0], row[1], row[2]
        kind = row[3] if len(row) > 3 else "fatal"
        chk = _as_check(code, name, kind)
        try:
            ok, msg = fn()
        except Exception as e:                      # noqa: BLE001
            # ★ 검사가 죽어도 ★ 나머지를 다 돌린다 — ★ 죽은 것도 실패로 남긴다
            ok, msg = False, f"검사가 예외로 죽었다: {type(e).__name__}: {e}"
        out.append(result(chk, run_id, "지시서대로", msg, ok))
    return out


def save(conn, run_id: str, at: str) -> list:
    """돌린 뒤 ★ `audit_validation` 에 남긴다 (규격 `c-result.md:149`).

    ★ `phase='guide'` · `code` · `passed` · `actual`(한 줄) · ★ `run_id`
    """
    from validate.base import save_results
    got = results(run_id)
    save_results(conn, got, at)
    return got


def run(run_id: str = "-") -> int:
    """★ 돌려서 ★ fatal 실패 수를 돌려준다.  ★ warn 은 ★ 세지 않는다.

    ★ 「아직 안 한 것」을 세는 검사가 ★ 늘 빨간불이면 ★ 진짜 실패가 묻힌다
    """
    bad = warn = 0
    for r in results(run_id):
        if r.passed:
            head = "OK  "
        elif r.check.severity == "warn":
            head = "warn"
            warn += 1
        else:
            head = "★ 실패"
            bad += 1
        print(f"  {head} {r.check.code} {r.check.title} — {r.actual}")
    if warn:
        print(f"  ★ warn {warn}건 — 「아직 안 한 것」이다.  ★ 실패로 세지 않는다")
    return bad

# ★ __main__ 블록을 두지 않는다 (V4-23) — 「import 만으로 아무 일도 안 일어나야
#   한다.  실행은 run.py · tools/ 에서만」이 규격이다.
#   ★ 돌리려면  python3.11 -c "from validate.v0_guide import run; \
#                              raise SystemExit(1 if run() else 0)"
