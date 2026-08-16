# -*- coding: utf-8 -*-
"""도메인 예외 5종.

지시서   0장 STEP 3
근거     언어별 예외 체계 차이를 흡수한다 (STEP 2 · 예외 표준화).
         이 5종 외의 예외를 계층 밖으로 던지지 않는다.  하위 예외는 감싸서 올린다.
금지     맨몸 Exception 을 상위 계층으로 전파하는 것.
         v1 은 「포기」만 찍혀 원인을 알 수 없었다 (STEP 3).
필수     listing_id · endpoint · step 을 반드시 담는다.
"""
from __future__ import annotations


class CarWatchError(Exception):
    """5종의 공통 조상.  직접 던지지 않는다.

    맥락 3종은 지시서 STEP 3 이 명시한 필수 항목이다.  모르면 None 을 넣되
    자리는 항상 만든다.  자리가 없으면 나중에 채울 수 없다.
    """

    def __init__(
        self,
        message: str,
        listing_id: str | None = None,
        endpoint: str | None = None,
        step: str | None = None,
        action: str | None = None,
    ) -> None:
        """action  ★ 「그럼 무엇을 하면 되는가」.

        없으면 화면이 일반 문구를 낸다 — 「절차를 마친 뒤 다시 누르십시오」가
        나오는데 마칠 절차가 없으면 사용자가 갇힌다 (실측 08-15)
        """
        super().__init__(message)
        self.action = action or ""
        self.message = message
        self.listing_id = listing_id
        self.endpoint = endpoint
        self.step = step

    def context(self) -> dict[str, str | None]:
        return {
            "kind": type(self).__name__,
            "message": self.message,
            "listing_id": self.listing_id,
            "endpoint": self.endpoint,
            "step": self.step,
        }

    def __str__(self) -> str:
        tail = " ".join(
            f"{k}={v}"
            for k, v in (
                ("listing_id", self.listing_id),
                ("endpoint", self.endpoint),
                ("step", self.step),
            )
            if v is not None
        )
        return f"{self.message} [{tail}]" if tail else self.message


class CollectError(CarWatchError):
    """수집 실패 — 네트워크 · 4xx · 5xx.

    404 는 여기 오지 않는다.  404 는 실패가 아니라 not_found 결과다 (2장 STEP 24).
    """


class FormatError(CarWatchError):
    """응답 형식 불일치 — 라벨↔내용 (2장 STEP 18).

    raw_response_reject 로 보낸 뒤 이 예외를 기록한다.  조용히 버리지 않는다.
    """


class ParseError(CarWatchError):
    """원문 → 필드 변환 실패 (L3)."""


class ValidationError(CarWatchError):
    """검증 단계 위반.

    put() 에 BANNED_SOURCES 가 들어온 경우도 이것이다 (1장 STEP 14 · 7장 STEP 69).
    불변 필드가 말없이 바뀐 경우도 이것이다 (3장 STEP 29).
    """


class PolicyError(CarWatchError):
    """설정 · 정책 모순 — 배점 합 불일치 등 (0장 STEP 7 불변식 ⑤)."""


DOMAIN_ERRORS: tuple[type[CarWatchError], ...] = (
    CollectError,
    FormatError,
    ParseError,
    ValidationError,
    PolicyError,
)


class WiringError(CarWatchError):
    """배선 누락.  ★ 사용자 잘못이 아니라 우리 잘못이다 — 500 이다.

    실측 08-15: make_app(plan=...) 을 빠뜨렸는데 403 「권한이 없습니다」가
    나왔다.  관리자로 로그인해도 안 되니 원인을 못 찾는다 (C-2)
    """


class AlreadyWatched(CarWatchError):
    """이미 담은 차량이다.

    ★ 결함이 아니라 「이미 그 상태」다 — 뒤로가기 재전송에서 흔하다.
      500 을 내면 남의 조작으로 서버가 죽는 것처럼 보인다 (실측 08-15)
    """
