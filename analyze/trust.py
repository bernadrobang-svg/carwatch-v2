# -*- coding: utf-8 -*-
"""플랫폼 신뢰도 — 점검 출처 · 엔카진단 · 엔카보증 (개정 300).

지시서   5장 「점검의 출처를 가른다」 (개정 300) · V3-53
근거     마스터 지적 — 「엔카 보증이 없으니 불안하다」
        ★ 같은 값이라도 누가 보증하느냐가 다르다
실물 문구 「해당 내용은 판매자가 직접 입력한 내용으로 모든 책임은 판매자에게 있습니다」
실측     inspection_formats  TABLE 2,884건 (엔카직영) · IMAGE 110건 (판매자 사진)
        · [] 430건 (점검 없음)

★ 규격 충돌 — 개정 292 배점표(값 250 · 상태 180 · 사양 75 · 취향 50)에
  플랫폼 신뢰도의 자리가 없다.  ②상태 180 은 70+40+30+25+15 로 이미 다 찼다.
  점수를 임의로 만들지 않고 「화면에 사실을 낸다」로만 구현했다 (덜 하는 쪽).
  배점을 받으면 축으로 올린다 — 가이드 판단이 필요하다
"""
from __future__ import annotations

# 점검 출처 — 원문 format 코드
FORMAT_OFFICIAL = "TABLE"     # 엔카직영 점검.  플랫폼이 책임진다
FORMAT_SELLER = "IMAGE"       # 판매자가 사진으로 올린 것

TRUST_HIGH = "높음"
TRUST_MEDIUM = "보통"
TRUST_LOW = "낮음"
TRUST_NONE = "없음"

# 화면에 그대로 낸다 (개정 300 「점검을 판매자가 올렸습니다」)
SOURCE_WORDS = {
    FORMAT_OFFICIAL: "엔카직영 점검",
    FORMAT_SELLER: "점검을 판매자가 올렸습니다",
}


def inspection_source(formats) -> str | None:
    """점검 출처.  ★ 엔카직영이 하나라도 있으면 직영이다."""
    if formats is None:
        return None
    if FORMAT_OFFICIAL in formats:
        return FORMAT_OFFICIAL
    if FORMAT_SELLER in formats:
        return FORMAT_SELLER
    return ""            # 빈 배열 — 점검 자체가 없다.  「모른다」와 다르다


def platform_trust(formats, diagnosis, warranty) -> tuple:
    """(신뢰도, 사유들).  셋을 묶어 낸다 (개정 300).

    높음   엔카진단 · 엔카보증 · 엔카직영 점검
    보통   엔카직영 점검만
    낮음   판매자 등록 점검만
    없음   점검 자체가 없음
    """
    src = inspection_source(formats)
    why = []
    if src is None:
        return None, []          # 확인 못 했다.  「없음」이 아니다
    if src == FORMAT_SELLER:
        why.append(SOURCE_WORDS[FORMAT_SELLER])
        return TRUST_LOW, why
    if src == "":
        why.append("성능점검이 없습니다")
        return TRUST_NONE, why
    # 여기부터 엔카직영 점검이다
    if not diagnosis:
        why.append("엔카진단이 없습니다")
    if not warranty:
        why.append("엔카보증이 없습니다")
    if diagnosis and warranty:
        return TRUST_HIGH, why
    return TRUST_MEDIUM, why
