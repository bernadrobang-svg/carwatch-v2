# -*- coding: utf-8 -*-
"""배점표를 config 에서 생성한다 (개정 512).

왜     08-22 에 배점표가 ★ 사본으로 여럿 있어 하루를 버렸다 —
       정본 표가 675·850·910 세 열이라 개발측이 가운데를 읽었고(개정 475),
       절 제목만 갈고 표를 안 갈아 어긋남이 커졌고(개정 495),
       제목의 「27축」은 ★ 사람이 손으로 센 숫자라 26 이 되어도 안 고쳐졌다(개정 511).
무엇   `config/scoring.json` 을 읽어 ★ f-table 의 AUTO 블록만 다시 쓴다
       ★ 제목의 「N축」도 생성한다 — ★ 사람이 세지 않는다
사용   python3 tools/gen_table.py          — 다시 쓴다
       python3 tools/gen_table.py --check  — 파일과 같은지만 본다 (검사 S45-4)
금지   ★ AUTO 블록 밖을 건드리는 것.  ★ 뜻·근거는 사람이 쓴다
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCORING = ROOT / "config" / "scoring.json"
FTABLE = ROOT / "docs" / "chapters" / "30-score" / "f-table.md"

BEGIN = "<!-- AUTO:배점표 시작 -->"
END = "<!-- AUTO:배점표 끝 -->"

# ★ 코드가 아직 옛 이름을 쓴다 (명령서 1-2b · 개정 504).
#   ★ 규격 이름으로 내보내려고 여기서 옮긴다.
#   ★★ S43-2b 가 통과하면 ★ 이 표를 지운다 — 그때는 config 가 이미 규격 이름이다.
RENAME = {
    "value.depreciation": "value.origin",
    "state.repair": "state.my_cost",
    "history.usage": "history.use",
    "history.lien": "history.seizing",
    "spec.trim": "taste.trim",
    "spec.options": "taste.option",
    "taste.picked": "taste.fitting",
}

# 사람이 읽는 이름.  ★ 축 id 는 config 가 정하고 ★ 이름표만 여기 있다
LABEL = {
    "state.accident": "사고 이력", "state.frame": "골격", "state.outer": "외판",
    "state.my_cost": "자차 수리비", "state.special": "특수 사고",
    "state.consumable": "소모품", "state.leak": "누유", "state.integrity": "진정성",
    "state.year": "연식", "history.use": "용도", "history.not_join": "자차 미가입",
    "history.owner": "소유자 변경", "history.seizing": "압류·저당",
    "value.mileage": "주행 대비", "value.origin": "가격 (신차가 대비)",
    "value.budget": "예산", "value.market": "시세 대비",
    "warranty.power": "동력계", "warranty.general": "일반·차체",
    "warranty.site": "사이트 검증",
    "taste.trim": "트림", "taste.option": "옵션", "taste.hud": "HUD",
    "taste.fitting": "지정 옵션", "taste.color": "색상 (외장)",
    "taste.sunroof": "선루프",
    # ★★★ 개정 1084·1085 — ★ 마스터 확정 09-01 로 신설한 둘
    "taste.size": "크기 (전장)", "taste.color_int": "색상 (내장)",
}

# 갈래 — config `groups` 의 접두 규칙을 규격 이름 기준으로 다시 적는다
GROUPS = (
    ("① 차량", ("state.", "history.", "value.mileage")),
    ("② 값", ("value.origin", "value.budget", "value.market")),
    ("③ 보증", ("warranty.",)),
    ("④ 취향", ("taste.",)),
)


def _load() -> dict[str, int]:
    cfg = json.loads(SCORING.read_text(encoding="utf-8"))
    return {RENAME.get(k, k): v for k, v in cfg["components"].items()}


def _in_group(axis: str, rules: tuple) -> bool:
    return any(axis == r or (r.endswith(".") and axis.startswith(r)) for r in rules)


def build() -> str:
    comp = _load()
    used: set[str] = set()
    lines = ["| 갈래 | 축 | 축 id | **점수** |", "|---|---|---|--:|"]
    for gname, rules in GROUPS:
        axes = [a for a in comp if _in_group(a, rules) and a not in used]
        used |= set(axes)
        lines.append(f"| **{gname} {sum(comp[a] for a in axes)}** |  |  |  |")
        for a in axes:
            lines.append(f"|  | {LABEL.get(a, a)} | `{a}` | **{comp[a]}** |")
    left = [a for a in comp if a not in used]
    for a in left:  # ★ 갈래에 안 들어간 축이 있으면 드러낸다.  숨기지 않는다
        lines.append(f"| ★ **갈래 없음** | {LABEL.get(a, a)} | `{a}` | **{comp[a]}** |")
    lines.append(f"|  |  | **합 {len(comp)}축** | **{sum(comp.values())}** |")
    head = f"## 축 — {len(comp)}축"
    return BEGIN + "\n\n" + head + "\n\n" + "\n".join(lines) + "\n\n" + END


def apply(check_only: bool = False) -> int:
    want = build()
    text = FTABLE.read_text(encoding="utf-8")
    m = re.search(re.escape(BEGIN) + r".*?" + re.escape(END), text, re.S)
    if m is None:
        if check_only:
            print("★ 실패 — f-table 에 AUTO 블록이 없다")
            return 1
        print("★ AUTO 블록이 없다.  손으로 한 번 넣어야 한다")
        return 1
    if m.group(0) == want:
        print(f"OK — 배점표가 config 와 같다 ({want.count('| `')}축)")
        return 0
    if check_only:
        print("★ 실패 — 배점표가 config 와 다르다.  python3 tools/gen_table.py 로 다시 쓴다")
        return 1
    FTABLE.write_text(text[:m.start()] + want + text[m.end():], encoding="utf-8")
    print("배점표를 다시 썼다")
    return 0


if __name__ == "__main__":
    raise SystemExit(apply("--check" in sys.argv))
