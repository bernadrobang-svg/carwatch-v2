# -*- coding: utf-8 -*-
"""엔카 어댑터 — URL · 헤더 · 쿼리 조립.

지시서   2장 STEP 17 (엔드포인트) · STEP 18 (required_keys) · STEP 23 (facet 2요청)
         1장 STEP 11 (SiteAdapter 계약)
근거     사이트 종속 코드를 여기에 가둔다.  CORE · Analyzer · Scorer 는 이 파일을 모른다.
금지     detail 에 include 파라미터 부착 — 화이트리스트로 동작해 5개 블록이 조용히 사라진다
         record 에서 /open 접미사 누락 — 404 가 된다
         facet 에서 축을 열거하는 것 — 나중에 필요한 축이 빠져 재수집이 된다
실측     q 문법은 v1 raw_facet 의 iNav.BreadCrumbs[].RemoveAction 에서 역산됐다.
         추정 없음 (STEP 17a).
"""
from __future__ import annotations

import json
import os
from urllib.parse import quote

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

SITE_CODE = "encar"

# ── 형식 검증 근거 (STEP 18) ─────────────────────────────────────────
# 「그 kind 를 다른 kind 와 구분하는 최소 집합」이다.  all() 이지 any() 가 아니다.
# diagnosis 는 원문 0건이라 빈 목록이다 — all() 은 공집합에 참이므로 통과한다.
# 원문을 확보해 required_keys 를 채우면 그때부터 자동으로 걸린다 (STEP 21b).
_SCHEMA: dict[str, EndpointSpec] = {
    # ★ 목록 응답 루트는 봉투다 (STEP 18a).  Id · ModelGroup 은 요소 기준이라
    #   봉투를 저장하면서 그것으로 검증하면 전건 거부된다
    "list": EndpointSpec(
        kind="list",
        scope="target",
        required_keys=["Count", "SearchResults"],
        root_type="object",
        per_call="collect_group × page",
    ),
    # ── 개정 296·297 로 늘어난 6종 (docs/ENCAR_API.md 2절) ──
    # ★ required_keys 는 「그 응답이 맞는지」를 보는 것이다.  실측한 키만 적는다
    "record_summary": EndpointSpec(
        kind="record_summary", scope="listing",
        required_keys=["carNo", "use"], root_type="object", per_call="매물 1"),
    "inspection_summary": EndpointSpec(
        kind="inspection_summary", scope="listing",
        required_keys=["vehicleId"], root_type="object", per_call="매물 1"),
    "platform_check": EndpointSpec(
        kind="platform_check", scope="listing",
        required_keys=["vehicleId", "cleaned"], root_type="object",
        per_call="매물 1"),
    "sellingpoint": EndpointSpec(
        kind="sellingpoint", scope="listing",
        required_keys=["vehicleId"], root_type="object", per_call="매물 1"),
    "ev_battery": EndpointSpec(
        kind="ev_battery", scope="listing",
        required_keys=[], root_type="object", per_call="매물 1"),
    "extend_warrant": EndpointSpec(
        kind="extend_warrant", scope="listing",
        required_keys=["vehicleId"], root_type="object", per_call="매물 1"),
    "detail": EndpointSpec(
        kind="detail",
        scope="listing",
        required_keys=["category", "manage"],
        root_type="object",
        per_call="매물 1",
    ),
    "inspection": EndpointSpec(
        kind="inspection",
        scope="listing",
        required_keys=["master", "outers"],
        root_type="object",
        per_call="매물 1",
    ),
    "record": EndpointSpec(
        kind="record",
        scope="listing",
        required_keys=["carNo", "openData"],
        root_type="object",
        per_call="매물 1",
    ),
    "diagnosis": EndpointSpec(
        kind="diagnosis",
        scope="listing",
        required_keys=[],  # ★ 원문 0건.  추정으로 채우지 않는다 (STEP 21b · 26-1)
        root_type="object",
        per_call="매물 1",
    ),
    "catalog": EndpointSpec(
        kind="catalog",
        scope="model",
        required_keys=["optionCd"],
        root_type="array",
        per_call="model_catalog_key 1",
    ),
    "facet": EndpointSpec(
        kind="facet",
        scope="target",
        required_keys=["iNav"],
        root_type="object",
        per_call="collect_group × 1 (미지정)",
    ),
}

# ★ facet 요청 1종 (STEP 23 정정 · 실측).
#   inav=|Metadata|Badge 는 |Metadata| 와 같은 결과를 준다.
#   facet 은 계층의 「다음 한 단계」만 준다 —
#   q 가 ModelGroup 까지만 지정하므로 Model 이 오고 Badge 는 오지 않는다.
#   트림은 목록 응답의 Badge 필드에서 얻는다 (4장 STEP 42 정정)
FACET_REQUEST_KINDS: tuple[str, ...] = ("unspecified",)
_INAV = {"unspecified": "|Metadata|"}


# ── q 쿼리 문법 (STEP 17a) ───────────────────────────────────────────
# v1 raw_facet 의 iNav.BreadCrumbs[].RemoveAction 실측.  추정 없음.
SEP = "._."

# 조립 규칙이 있는 키.  ★ 여기 없는 키는 거부한다 — 조용히 무시하지 않는다
FLAG_KEYS: tuple[str, ...] = ("Hidden", "MultiViewHidden")
RANGE_KEYS: tuple[str, ...] = ("Year", "Price")
# 계층 순서.  엔카는 Manufacturer → ModelGroup → Model → BadgeGroup 이다
HIERARCHY: tuple[str, ...] = ("CarType", "Manufacturer", "ModelGroup", "Model",
                              "BadgeGroup")
KNOWN_QUERY_KEYS: frozenset[str] = frozenset(
    FLAG_KEYS + HIERARCHY + tuple(f"{k}_range" for k in RANGE_KEYS))


def escape_value(value: str) -> str:
    """값 안의 닫는 괄호 앞에 _ 를 넣는다.

    실측   르노코리아(삼성)  →  르노코리아(삼성_)
    근거   ) 가 계층 종료 기호와 충돌한다
    금지   URL 인코딩만으로 해결하려는 것.  문법 수준의 이스케이프다
    """
    return str(value).replace(")", "_)")


def unescape_value(value: str) -> str:
    """왕복 시험용 (STEP 17a 검증)."""
    return str(value).replace("_)", ")")


def _nest(keys: list[str], site_query: dict) -> str:
    """(C.{상위}._.{하위}.) 중첩 계층을 만든다."""
    head, rest = keys[0], keys[1:]
    inner = (
        _nest(rest, site_query)
        if len(rest) > 1
        else f"{rest[0]}.{escape_value(site_query[rest[0]])}."
    )
    return f"(C.{head}.{escape_value(site_query[head])}{SEP}{inner})"


def load_site_config(root: str = ".") -> dict:
    path = os.path.join(root, "config", "endpoints.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)[SITE_CODE]


# 매물당 던지는 요청 종류.  ★ 순서가 LISTING_ENDPOINTS 와 같아야 한다
LISTING_ENDPOINT_KINDS: tuple[str, ...] = (
    "detail", "inspection", "record", "diagnosis",
    # 개정 296·297 — 인증 없이 받을 수 있는 것 (docs/ENCAR_API.md)
    "record_summary", "inspection_summary", "platform_check",
    "sellingpoint", "ev_battery",
    # ★ extend_warrant 는 뺐다 — 실측 08-17: 쿠폰이 붙은 매물에만 있어
    #   160건 전량 404 였고 V1-08 이 「경로 오류」로 잡았다.
    #   경로는 맞지만 그 자원이 없는 것이다.  3,470 요청을 쓸 값이 없다.
    #   필요해지면 detail 의 advertisement 에서 쿠폰 유무를 보고 그때만 부른다
)


class EncarAdapter:
    """SiteAdapter 구현 (1장 STEP 11)."""

    site_code = SITE_CODE

    def __init__(self, cfg: dict) -> None:
        self._cfg = cfg
        self._base = cfg["base_url"]
        self._paths = cfg["paths"]
        self._timeout = float(cfg["timeout_sec"])
        self._page_size = int(cfg["page_size"])

    # ── 헤더 ─────────────────────────────────────────────────────────
    def headers(self) -> dict[str, str]:
        h = {k: v for k, v in (self._cfg.get("headers") or {}).items() if v}
        if not h:
            raise PolicyError(
                "config/endpoints.json encar.headers 가 비어 있다. "
                "STEP 25a 실측 절차로 확보한다",
                endpoint="*",
                step="STEP 25a",
            )
        return h

    # ── 쿼리 조립 (STEP 17a) ─────────────────────────────────────────
    def build_q(self, site_query: dict) -> str:
        """site_query(dict) → 엔카 q 문자열 (URL 인코딩 전).

        문법   전체    (And.{항}._.{항})
               계층    (C.{상위}._.{하위}.)
               범위    {축}.range({하한}..{상한})
               단일    {축}.{값}.
               구분자  ._.
        순서   ① Hidden · MultiViewHidden  ② range 조건  ③ 계층 조건
               순서가 다르면 같은 조건이라도 문자열이 달라져 캐시 키·로그 대조가 어긋난다
        금지   조건이 하나도 없으면 조립하지 않는다.  전체 매물을 받게 된다
        """
        if not site_query:
            raise PolicyError(
                "site_query 가 비어 있다. 전체 매물을 받게 된다",
                endpoint="list",
                step="STEP 17a",
            )
        # ★ 아는 키만 조립하고, 모르는 키가 있으면 중단한다.
        #   지정한 조건이 조용히 사라지면 안 된다 (V1-10).
        #   실제로 Model 을 넣었다가 조용히 빠져 잘못된 URL 이 나갔다
        unknown = sorted(set(site_query) - KNOWN_QUERY_KEYS)
        if unknown:
            raise PolicyError(
                f"site_query 에 조립 규칙이 없는 키: {unknown}. "
                f"조용히 무시하지 않는다. HIERARCHY 또는 RANGE_KEYS 에 추가한다",
                endpoint="list",
                step="STEP 17a")

        terms: list[str] = []
        for key in FLAG_KEYS:
            if key in site_query:
                terms.append(f"{key}.{escape_value(site_query[key])}")
        for key in RANGE_KEYS:
            rng = site_query.get(f"{key}_range")
            if rng:
                terms.append(f"{key}.range({rng})")
        hier = [k for k in HIERARCHY if k in site_query]
        if hier:
            terms.append(_nest(hier, site_query))
        return "(And." + SEP.join(terms) + ")"

    # ── SiteAdapter 계약 ─────────────────────────────────────────────
    def list_url(self, target: TargetSpec, page: int) -> Request:
        offset = page * self._page_size
        q = quote(self.build_q(target.site_query[SITE_CODE]), safe="")
        sr = quote(f"|MobileModifiedDate|{offset}|{self._page_size}", safe="")
        url = f"{self._base}{self._paths['list']}?count=true&sr={sr}&q={q}"
        return Request("GET", url, self.headers(), self._timeout)

    def detail_urls(self, source_id: str) -> list[Request]:
        """매물당 10종.  condition 값과 무관하게 전부 던진다 (STEP 25).

        ★ 뒤 6종은 개정 296·297 로 늘었다 (docs/ENCAR_API.md 2절).
          인증 없이 200 인 것만 넣는다 — /v2/verification/* 은 401 이라 뺐다
        금지   include 파라미터.  skip_done 류 건너뛰기 플래그
        """
        out = []
        for kind in LISTING_ENDPOINT_KINDS:
            url = self._base + self._paths[kind].format(source_id=source_id)
            out.append(Request("GET", url, self.headers(), self._timeout))
        return out

    def facet_urls(self, target: TargetSpec) -> list[Request]:
        """차종당 2회.  미지정만으로는 Badge 가 오지 않는다 (STEP 23 실측)."""
        q = quote(self.build_q(target.site_query[SITE_CODE]), safe="")
        sr = quote(f"|MobileModifiedDate|{0}|{1}", safe="")
        out = []
        for kind in FACET_REQUEST_KINDS:
            inav = quote(_INAV[kind], safe="")
            url = (
                f"{self._base}{self._paths['facet']}"
                f"?count=true&sr={sr}&q={q}&inav={inav}"
            )
            out.append(Request("GET", url, self.headers(), self._timeout))
        return out

    def catalog_url(self, listing_source_id: str) -> Request:
        """★ 매물 ID 로 호출한다.  jatoVehicleId 가 아니다 (실측).

        경로가 /vehicles/car/{id}/ 다 — car 는 매물을 가리킨다.
        응답은 모델-연식 카탈로그라서 모델당 1회면 된다 (STEP 22).
        그래서 「호출 키」와 「중복 제거 키」가 다르다.
        """
        url = self._base + self._paths["catalog"].format(
            source_id=listing_source_id)
        return Request("GET", url, self.headers(), self._timeout)

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        return dict(_SCHEMA)
