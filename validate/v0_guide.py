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
    """
    tools = ROOT / "tools"
    if not tools.is_dir():
        return False, "tools/ 가 없다"
    bad, seen = [], 0
    for q in sorted(tools.glob("collect_*.py")):
        # ★ 엔카는 ★ `collect/runner.py` 가 ★ `save_raw` 로 남긴다 — ★ 결이 다르다
        body = _read(q)
        if "save_site_raw" not in body and "save_raw" not in body:
            bad.append(q.name)
        seen += 1
    if bad:
        return False, ("★ 원문을 안 남기는 수집기 — " + " · ".join(bad)
                       + " (명령서 3-2 필수)")
    return True, f"수집기 {seen}개가 다 원문을 남긴다"



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
            try:
                doc = json.loads(body)
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
            try:
                doc = json.loads(body[0])
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
