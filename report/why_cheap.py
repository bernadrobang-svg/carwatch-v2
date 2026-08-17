# -*- coding: utf-8 -*-
"""「왜 싼가」 — 싼 이유를 순서대로 찾아 낸다 (개정 299 · V3-52).

지시서   5장 「★★★ 「왜 싼가」를 말한다」 (개정 299)
근거     마스터 지적 — 「엔카 보증이 없는 것이 가격이 왜 싼지가 중요해.
        1차로 엔카 보증이 없으니 불안하고, 이 케이스는 엔진성능을
        판매자가 직접 올렸고 렌트카야」
        ★ 실측 — 같은 차를 우리는 A·89.9%·「렌트 아님」으로 봤다.
          싼 데는 이유가 있었고 우리는 그것을 「좋은 것」으로 읽었다
필수     이유를 못 찾으면 그것도 낸다 — ★ 그것이 오히려 위험 신호다
금지     「시세차 −1,100만」만 내고 끝내는 것
"""
from __future__ import annotations

from analyze.trust import (
    FORMAT_SELLER, SOURCE_WORDS, TRUST_LOW, TRUST_NONE, platform_trust,
)

NOT_FOUND = "싼 이유를 찾지 못했습니다.  직접 확인하십시오"
# 단위 환산 (2장 상수표 · V4-13)
WON_PER_MANWON = 10_000

# 이유 후보를 확인하는 순서 (개정 299).  ★ 순서가 규격이다
ORDER = ("platform", "inspection", "rental", "accident", "mileage",
         "color", "not_join")


def reasons(row) -> list:
    """싼 이유를 순서대로 (개정 299 ①~⑦).

    row 는 화면 행이다 — 이미 판정이 끝난 값만 읽는다.
    ★ 여기서 다시 판정하지 않는다.  같은 사실을 두 곳에서 만들면 어긋난다
    """
    out = []
    trust, why = platform_trust(row.get("inspection_formats"),
                               row.get("diagnosis_car"),
                               row.get("has_warranty"))
    # ① 플랫폼 진단·보증이 없다
    if trust in (TRUST_LOW, TRUST_NONE) or why:
        out += why
    # ② 성능점검을 판매자가 올렸다 — ①에서 이미 담았으면 겹치지 않는다
    src = row.get("inspection_source")
    if src == FORMAT_SELLER and SOURCE_WORDS[FORMAT_SELLER] not in out:
        out.append(SOURCE_WORDS[FORMAT_SELLER])
    # ③ 렌트·리스 이력
    if row.get("rental_note"):
        out.append(row["rental_note"])
    # ④ 사고 · 단순수리
    n = row.get("accident_cnt")
    if n:
        out.append(f"사고 이력 {n}회")
    if row.get("repair_won"):
        out.append(f"자차 수리비 {int(row['repair_won']) // WON_PER_MANWON:,}만원")
    # ⑤ 주행거리 · 연식
    if row.get("mileage_note"):
        out.append(row["mileage_note"])
    # ⑥ 인기 없는 색
    if row.get("color_note"):
        out.append(row["color_note"])
    # ★ 전기차는 배터리가 값을 가른다 (개정 296).  SOH 가 낮으면 그것이 이유다
    soh = row.get("battery_soh")
    if soh is not None and soh < (row.get("battery_soh_low") or 0):
        out.append(f"배터리 SOH {soh}%")
    # ⑦ 자차 미가입 기간 — ★ 몇 달인지가 사실이다 (개정 294)
    got = row.get("not_join")
    if got:
        out.append(f"자차 미가입 {got}개월")
    return out


def verdict(gap_won, row) -> tuple:
    """(문구, 이유들).  ★ 「싸다」를 말할 때만 부른다 (개정 299).

    금지   「시세차 −1,100만」만 내고 끝내는 것
    """
    got = reasons(row)
    if not got:
        # ★ 이유를 못 찾은 것이 오히려 위험 신호다.  조용히 넘기지 않는다
        return NOT_FOUND, []
    return f"싼 이유 {len(got)}가지를 찾았습니다", got
