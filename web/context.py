# -*- coding: utf-8 -*-
"""화면 문맥과 오류 (14장 STEP 144 · 148).

지시서   STEP 144 (공통 레이아웃) · STEP 148 (오류 화면)
근거     ★ 버전이 없으면 어느 규칙으로 나온 화면인지 모른다.
         「어제 본 등급과 다른데 왜」의 답이 꼬리에 있다
금지     화면마다 다른 문구를 쓰는 것
         스택 트레이스를 화면에 내는 것 — 경로·쿼리가 노출된다
"""
from __future__ import annotations

from dataclasses import dataclass, field

from contracts import ROLE_ADMIN

# 상태 코드 (STEP 148).
# ★ 표준 라이브러리를 쓴다 — 숫자를 손으로 적지 않고 상수표도 안 늘린다
from http import HTTPStatus

HTTP_OK = HTTPStatus.OK
HTTP_SEE_OTHER = HTTPStatus.SEE_OTHER
HTTP_BAD_REQUEST = HTTPStatus.BAD_REQUEST
HTTP_FORBIDDEN = HTTPStatus.FORBIDDEN
HTTP_NOT_FOUND = HTTPStatus.NOT_FOUND
# 지금이 아닐 뿐 — 보낸 값은 정상이다 (Q-3)
HTTP_CONFLICT = HTTPStatus.CONFLICT
HTTP_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR


@dataclass(frozen=True)
class MenuItem:
    label: str
    path: str
    group: str | None = None
    locked: bool = False


@dataclass(frozen=True)
class Banner:
    """미분류 · 미확정 · 중단.  ★ 있을 때만 낸다 (STEP 144)."""

    kind: str          # unclassified · pending · halted
    text: str
    action: str = ""


@dataclass(frozen=True)
class PageContext:
    """전 화면이 같은 것을 낸다 (STEP 144).

    ★ 꼬리의 버전 표시를 접거나 숨기지 않는다
    """

    title: str
    body_html: str
    viewer: object                       # ViewerState (10장)
    menu: list = field(default_factory=list)
    banners: list = field(default_factory=list)
    flashes: list = field(default_factory=list)
    calc_version: str = ""
    dict_version: str = ""
    parse_version: str = ""
    run_id: str = ""
    generated_at: str = ""
    csrf_token: str = ""

    @property
    def is_admin(self) -> bool:
        return getattr(self.viewer, "role", "") == ROLE_ADMIN


@dataclass(frozen=True)
class ErrorPage:
    """★ 「오류가 발생했습니다」만 내지 않는다.  다음 행동이 있다."""

    status: int
    title: str
    reason: str
    action: str
    run_id: str = ""


NOT_FOUND = ErrorPage(HTTP_NOT_FOUND, "그런 화면이 없습니다",
                      "주소를 다시 확인해 주십시오.",
                      "매물 목록으로 돌아간다  (/listings)")
# 승인 대기.  ★ 「관리자로 로그인하라」고 하면 이미 로그인한 사람이 헤맨다
PENDING_WAIT = ErrorPage(
    HTTP_FORBIDDEN, "승인을 기다리는 중입니다",
    "관리자가 승인하면 관심 등록과 조건 알림을 쓸 수 있습니다.",
    "승인 전에도 등급 · 판정 근거 · 시세는 볼 수 있습니다  (/listings)")
FORBIDDEN = ErrorPage(HTTP_FORBIDDEN, "관리자만 볼 수 있습니다",
                      "이 화면은 관리자 권한이 필요합니다.",
                      "관리자로 로그인한다  (/login)")


# 권한 부족을 가리키는 말.  ★ 그 밖의 PolicyError 는 절차 위반이다 (C-2)
PERMISSION_MARKS = ("권한 부족", "권한이 없", "로그인", "관리자만",
                    "남의 ", "역할",
                    # ★ CSRF 실패는 형식 오류가 아니라 위조 시도다 (Q-2).
                    #   400 「보낸 값이 잘못됐다」가 아니라
                    #   403 「해도 되는 일이 아니다」가 맞다
                    "요청을 확인하지 못했습니다")

# 지금이 아닐 뿐인 것.  ★ 보낸 값은 정상이다 — 400 이면 사용자가
# 「내가 뭘 잘못 적었나」를 찾게 된다 (Q-3)
CONFLICT_MARKS = ("실행 중", "도는 동안", "재계산", "잠깁니다", "잠긴다")


def _is_permission(exc: Exception) -> bool:
    text = str(exc)
    return any(m in text for m in PERMISSION_MARKS)


def _is_conflict(exc: Exception) -> bool:
    text = str(exc)
    return any(m in text for m in CONFLICT_MARKS)


def _clean(exc: Exception) -> str:
    """★ 「[step=STEP 82]」는 내부 표기다.  화면에 내지 않는다."""
    import re

    return re.sub(r"\s*\[step=[^\]]*\]\s*$", "", str(exc)).strip()


def error_page(exc: Exception, run_id: str = "") -> ErrorPage:
    """도메인 예외는 사유와 조치를 낸다.  그 외는 run_id 만 낸다.

    ★ CarWatchError 는 사용자에게 보여도 되는 문장이어야 한다
      「저당 여부를 확인하지 못했습니다」  O
      「seizing_cnt is None」              X
    """
    from errors import CarWatchError, PolicyError, WiringError

    # ★ 배선 누락은 우리 잘못이다.  403 으로 내면 사용자가 원인을 못 찾는다 (C-2)
    if isinstance(exc, WiringError):
        return ErrorPage(HTTP_SERVER_ERROR, "내부 오류", _clean(exc),
                         f"run_id {run_id} 로 로그를 확인한다", run_id)
    if isinstance(exc, PolicyError):
        # ★ 「권한이 없다」와 「절차를 안 밟았다」는 다르다.
        #   미리보기를 안 본 관리자에게 「관리자로 로그인하라」고 하면
        #   이미 관리자라서 무엇을 할지 모른다 (C-2)
        if _is_permission(exc):
            return ErrorPage(HTTP_FORBIDDEN, "권한이 없습니다", _clean(exc),
                             getattr(exc, "action", "")
                             or "관리자로 로그인한다  (/login)", run_id)
        if _is_conflict(exc):
            # ★ 409 다.  보낸 값은 정상이고 「지금이 아닐 뿐」이다 (Q-3)
            return ErrorPage(HTTP_CONFLICT, "지금은 바꿀 수 없습니다",
                             _clean(exc),
                             "수집·재계산이 끝난 뒤 다시 시도한다  "
                             "(/admin/run 에서 진행을 봅니다)", run_id)
        return ErrorPage(HTTP_BAD_REQUEST, "아직 저장할 수 없습니다",
                         _clean(exc),
                         getattr(exc, "action", "")
                         or "화면의 안내대로 절차를 마친 뒤 다시 누른다",
                         run_id)
    if isinstance(exc, CarWatchError):
        return ErrorPage(HTTP_BAD_REQUEST, "처리하지 못했습니다", _clean(exc),
                         getattr(exc, "action", "")
                         or "입력을 확인하고 다시 시도한다", run_id)
    # ★ 스택 트레이스를 내지 않는다.  run_id 가 로그를 찾는 좌표다
    return ErrorPage(HTTP_SERVER_ERROR, "내부 오류",
                     "처리 중 예상하지 못한 문제가 생겼습니다.",
                     f"run_id {run_id} 로 로그를 확인한다  "
                     f"(collect_*.log · audit_validation)", run_id)
