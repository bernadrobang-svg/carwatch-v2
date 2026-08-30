# -*- coding: utf-8 -*-
"""KB차차차 성능점검부 → ★ **부위별** (규격 `KBCHACHACHA_API.md` 3장 · 268~269줄).

★★★★★ 08-30 (밀린일 「KB 부위별」 4일째 · 명령서 r974 뒤) — ★ **찾았다.**

★ 어디에 있나 — ★ KB 상세 안의 ★ `data-link-url` 이 ★ 성능점검부 쪽으로 간다
    <a data-link-url="http://autocafe.co.kr/ASSO/CarCheck_Form.asp?OnCarNo=…">
  ★ ★ 그 쪽은 ★ **네모 칸 그림**이라 ★ 글로는 안 읽힌다 —
  ★ ★ 칸을 칠하는 것은 ★ **스크립트 변수 둘**이다 [실측 08-30 · 표본 20건 중 16건]

    var ucAccOutCheck  = '{"1":"X","2":"X","5":"X"}'   ★ 외판
    var ucAccBoneCheck = '{"18":"W"}'                  ★ 주요 골격

★ 상태 부호는 ★ **그 쪽의 범례**가 적어 준다 —
    ※ 상태표시 부호 : (교환), (판금 또는 용접), (흠집), (요철), (부식), (손상)
★ 부위 번호 ↔ 이름 ↔ 랭크도 ★ **그 쪽에 인쇄돼 있다** —
    외판 1랭크 1.후드 2.프론트휀더 3.도어 4.트렁크리드 5.라디에이터 서포트
    외판 2랭크 6.쿼터패널 7.루프패널 8.사이드실 패널
    주요 골격 A랭크 9·10·11·17·18 · B랭크 12·13·14·19 · C랭크 15·16

★★ **그래서 표를 내가 짓지 않는다** — ★ 쪽에서 읽는다 (금지 6 · 짐작으로 이름을 짓지 마라).
  ★ ★ 쪽이 바뀌면 ★ 읽기가 함께 바뀐다.  ★ 박아 두면 ★ 조용히 틀린다

★ 내는 꼴은 ★ 엔카 `inspection_panel_json` 과 ★ **같다** — ★ 축이 그것을 읽는다
    {"type": {"code": "8", "title": "사이드실 패널"},
     "statusTypes": [{"code": "X", "title": "교환(교체)"}],
     "attributes": ["RANK_TWO"]}
"""
from __future__ import annotations

import json
import re

# ★ 축이 보는 낱말 (`analyze/axis/state.py` `SWAP_TITLES`·`SHEET_TITLES`)
STATUS = {"X": "교환(교체)", "W": "판금/용접"}
# ★ 축이 보는 등급 (`config/scoring.json` `frame_ranks`·`outer_ranks`)
OUTER_RANK = {"1": "RANK_ONE", "2": "RANK_TWO"}
BONE_RANK = {"A": "RANK_A", "B": "RANK_B", "C": "RANK_C"}

RE_VAR = r"var\s+{name}\s*=\s*'([^']*)'"
RE_TAG = re.compile(r"<[^>]+>")
# ★ 「5.라디에이터 서포트(볼트체결부품)」·「14.필러패널 ( A, B, C )」처럼
#   ★ 이름 안에 ★ 괄호와 숫자가 들어온다.  ★ 다음 「N.」 앞까지를 이름으로 본다
RE_PART = re.compile(r"(?<![\d.])(\d{1,2})\s*\.\s*"
                     r"(.{2,40}?)(?=\s*(?<![\d.])\d{1,2}\s*\.\s*\D|\s*$)", re.S)


# ★ 이름 뒤에 ★ 표의 다른 칸이 딸려 온다 (「만원」·「&nbsp;」·「(2/4쪽)」).
#   ★ 이름만 남긴다 — ★ 점수는 등급·부호가 정한다.  ★ 이름은 화면 글이다
RE_TAIL = re.compile(r"\s*(?:만원|&nbsp;|\(\d+/\d+쪽\)|자동차 세부상태).*$")


def _clean(name: str) -> str:
    return RE_TAIL.sub("", name or "").strip(" ·&;")


def _text(html: str) -> str:
    return re.sub(r"\s+", " ", RE_TAG.sub(" ", html or ""))


def _blob(html: str, name: str) -> dict:
    """★ 스크립트 변수 하나.  ★ 없거나 못 읽으면 ★ 빈 것이 아니라 ★ None 이다."""
    got = re.search(RE_VAR.format(name=name), html or "")
    if not got:
        return None
    try:
        val = json.loads(got.group(1) or "{}")
    except ValueError:
        return None
    return val if isinstance(val, dict) else None


def legend(html: str) -> dict:
    """부위번호 → (이름, 등급).  ★ 쪽에 인쇄된 범례에서 읽는다.

    ★ 못 읽으면 ★ 빈 표다 — ★ 그러면 부위를 안 낸다.  ★ 지어내지 않는다
    """
    txt = _text(html)
    i = txt.find("외판 부위")
    if i < 0:
        i = txt.find("외판부위")
    if i < 0:
        return {}
    j = txt.find("주요 골격", i)
    if j < 0:
        j = txt.find("주요골격", i)
    out: dict = {}
    # ★ 범례 뒤에 ★ 다음 절이 붙어 온다 — ★ 거기서 끊는다.
    #   ★ 안 끊으면 ★ 마지막 부위(16.플로어패널)의 이름이 ★ 다음 절을 삼킨다
    def cut(seg: str) -> str:
        for word in ("자동차 세부상태", "⑭", "유의사항"):
            at = seg.find(word)
            if at > 0:
                seg = seg[:at]
        return seg

    for seg, ranks in ((cut(txt[i:j if j > 0 else len(txt)]), OUTER_RANK),
                       (cut(txt[j:j + 700]) if j > 0 else "", BONE_RANK)):
        marks = [(m.start(), m.group(1))
                 for m in re.finditer(r"([12ABC])\s*랭크", seg)
                 if m.group(1) in ranks]
        for k, (at, key) in enumerate(marks):
            stop = marks[k + 1][0] if k + 1 < len(marks) else len(seg)
            for num, name in RE_PART.findall(seg[at:stop]):
                out.setdefault(num, (_clean(name), ranks[key]))
    return out


def panels(html: str) -> list | None:
    """성능점검부 한 쪽 → 엔카 `inspection_panel_json` 과 같은 꼴.

    돌려줌  판 목록 (이상 없으면 ★ 빈 목록 — ★ 「확인한 사실」이다)
           ★ 변수가 아예 없으면 ★ None (★ 「못 봤다」다.  ★ 빈 목록과 다르다)
    """
    out_c = _blob(html, "ucAccOutCheck")
    bone_c = _blob(html, "ucAccBoneCheck")
    if out_c is None and bone_c is None:
        return None                    # ★ 이 쪽은 우리가 아는 꼴이 아니다
    table = legend(html)
    if not table:
        return None                    # ★ 범례를 못 읽었다 — ★ 등급을 지어내지 않는다
    got = []
    for blob in (out_c or {}, bone_c or {}):
        for num, code in blob.items():
            name, rank = table.get(str(num), (None, None))
            if not rank:
                continue               # ★ 범례에 없는 번호 — ★ 안 낸다
            title = STATUS.get(str(code).upper())
            if not title:
                continue               # ★ 모르는 부호 — ★ 안 낸다 (흠집·부식은 축 밖이다)
            got.append({"type": {"code": str(num), "title": name},
                        "statusTypes": [{"code": str(code).upper(),
                                         "title": title}],
                        "attributes": [rank]})
    return got


def report_url(detail_html: str) -> str | None:
    """상세에서 ★ 성능점검부 주소를 뽑는다 (`data-link-url`)."""
    got = re.search(r'data-link-url="(https?://[^"]+)"', detail_html or "")
    return got.group(1) if got else None
