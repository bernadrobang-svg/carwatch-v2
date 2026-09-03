"""★★★★★ 09-03 (가이드 지시 ①) — ★ **config 의 길만 읽는 어댑터.**

★★★ 가이드 — 「★ `run.py` 가 ★ **어댑터를 사이트별로 골라 받게**.
  ★ ★ 이것이 먼저다.  ★ 지금 ★ 열한 사이트가 ★ **파이프라인을 안 탄다**」

★★ 왜 하나로 되나 — ★ `endpoints.json` 이 ★ 이미 ★ **길을 다 갖고 있다**.
  ★ ★ 전에는 ★ 그 길이 ★ `tools/collect_*.py` 안에도 흩어져 있어
  ★ ★ ★ 판이 그것을 못 봤을 뿐이다.
★ 사이트마다 다른 것은 ★ **길과 머리(headers)** 뿐이다 —
  ★ ★ 그 둘은 ★ config 가 준다.  ★ 코드에 안 박는다 (`S14`)
★★★ 못 하는 것은 ★ **못 한다고 말한다** (금지 12) —
  ★ 길이 없으면 ★ `PolicyError` 다.  ★ 지어내지 않는다
"""
from __future__ import annotations

from contracts import EndpointSpec, Request, TargetSpec
from errors import PolicyError

GET = "GET"


class GenericAdapter:
    """★ `SiteAdapter` 구현 — ★ 길을 ★ `config/endpoints.json` 에서만 읽는다."""

    def __init__(self, cfg: dict, site_code: str) -> None:
        self.site_code = site_code
        self._cfg = cfg
        self._base = str(cfg.get("base_url") or "").rstrip("/")
        self._paths = dict(cfg.get("paths") or {})
        self._timeout = float(cfg.get("timeout_sec") or 30)
        if not self._base:
            raise PolicyError(
                f"config/endpoints.json {site_code}.base_url 이 없다",
                endpoint="*", step="STEP 25a")

    def headers(self) -> dict[str, str]:
        return {k: v for k, v in (self._cfg.get("headers") or {}).items() if v}

    def _url(self, kind: str, **kw) -> str:
        path = self._paths.get(kind)
        if not path:
            raise PolicyError(
                f"{self.site_code} 에 {kind} 길이 없다 — "
                f"있는 것: {', '.join(sorted(self._paths)) or '없음'}",
                endpoint=kind, step="STEP 25a")
        try:
            return self._base + str(path).format(**kw)
        except KeyError as e:
            # ★ 길이 바라는 칸이 없다 — ★ **빈 값으로 메우지 않는다**
            raise PolicyError(
                f"{self.site_code}.{kind} 길이 {e} 를 바라는데 안 줬다",
                endpoint=kind, step="STEP 25a") from e

    def list_url(self, target: TargetSpec | None, page: int = 1,
                 **kw) -> Request:
        return Request(GET, self._url("list", page=page, **kw),
                       self.headers(), self._timeout)

    def detail_urls(self, source_id: str, **kw) -> list[Request]:
        """★ 상세 하나.  ★ 딸린 창구(점검·이력)는 ★ 길이 있을 때만 낸다."""
        out = [Request(GET, self._url("detail", source_id=source_id, **kw),
                       self.headers(), self._timeout)]
        for extra in ("inspection", "record", "carhistory"):
            if extra in self._paths:
                try:
                    out.append(Request(
                        GET, self._url(extra, source_id=source_id, **kw),
                        self.headers(), self._timeout))
                except PolicyError:
                    continue      # ★ 그 길이 다른 칸을 바란다 — ★ 건너뛴다
        return out

    def facet_urls(self, target: TargetSpec | None) -> list[Request]:
        """★ 사이트마다 ★ facet 이 없을 수 있다 — ★ 없으면 ★ **빈 목록**이다."""
        out = []
        for kind in sorted(k for k in self._paths if k.startswith("facet")):
            out.append(Request(GET, self._url(kind), self.headers(),
                               self._timeout))
        return out

    def endpoint_schema(self) -> dict[str, EndpointSpec]:
        """★ 형식은 ★ config 가 말한다 — ★ 없으면 ★ 「모른다」로 둔다.

        ★ `required_keys` 를 ★ 지어내면 ★ 멀쩡한 원문이 거부된다 —
          ★ ★ 그래서 ★ **비워 둔다** (검증은 통과시키고 파서가 본다)
        """
        got: dict = {}
        for kind in self._paths:
            got[kind] = EndpointSpec(
                kind=kind,
                scope="listing" if kind != "list" else "target",
                required_keys=[],
                root_type=str((self._cfg.get("root_type") or {}).get(kind)
                              or "object"),
                per_call="listing" if kind != "list" else "page")
        return got
