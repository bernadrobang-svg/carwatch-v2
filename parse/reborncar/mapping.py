# -*- coding: utf-8 -*-
"""리본카 상세 → `core_listing` (명령서 39 · `docs/REBORNCAR_API.md` 1b).

실측     2026-08-24 · 표본 `C26011900046` (320KB)
★ 값이 `<dt>이름</dt><dd>값</dd>` 로 온다 — ★ 이름이 41가지다
★ ★ 모바일 UA 로 받아야 참값이 온다 — ★ 데스크톱은 「용도변경 없음」이 거짓이다 (2a장)
금지     ★ 없는 값을 지어내는 것.  ★ 안 오면 None 이다 (모름)
"""
from __future__ import annotations

import json
import re

WON_PER_MANWON = 10_000
RE_PAIR = re.compile(r"<dt[^>]*>(.{1,20}?)</dt>\s*<dd[^>]*>(.{1,200}?)</dd>", re.S)
RE_TAG = re.compile(r"<[^>]+>")
# ★ 「2018년 10월」 → 201810 (MULTISITE_MAPPING 5a② — YYYYMM)
RE_YM = re.compile(r"(20\d{2})\s*년\s*(\d{1,2})\s*월")
RE_NUM = re.compile(r"([\d,]+)")
# ★ 차명은 <title> 에 있다 — 「지프 지프 랭글러(JL) 2.0 루비콘 4DR | 직영중고차 리본카」
#   ★ 상세에 차종 칸이 따로 없다 (BOBAEDREAM 과 같다)
RE_TITLE = re.compile(r"<title>([^<|]{4,90})", re.I)


def _txt(s: str) -> str:
    return re.sub(r"\s+", " ", RE_TAG.sub(" ", s)).replace("&gt;", "").strip()


def _int(s: str | None) -> int | None:
    got = RE_NUM.search(s or "")
    try:
        return int(got.group(1).replace(",", "")) if got else None
    except ValueError:
        return None


def fields(html: str) -> dict:
    """`<dt>·<dd>` 짝을 이름→값 으로.  ★ 먼저 나온 것이 이긴다."""
    out: dict = {}
    for got in RE_PAIR.finditer(html):
        k, v = got.group(1), got.group(2)
        key, val = _txt(k), _txt(v)
        # ★ `${...}` 는 화면 틀이다 — ★ 값이 아니다
        if not key or not val or "${" in key or "${" in val:
            continue
        out.setdefault(key, val)
    return out


def title_name(html: str) -> str | None:
    """차명.  ★ 사이트가 제조사를 두 번 적기도 한다 — ★ 그대로 둔다."""
    got = RE_TITLE.search(html)
    return _txt(got.group(1)) if got else None


def parse_detail(html: str, site: str, source_id: str) -> dict | None:
    f = fields(html)
    if not f:
        return None
    out: dict = {"site": site, "source_id": str(source_id), "price_unit": "won"}
    name = title_name(html)
    if name:
        out["site_model"] = name

    ym = RE_YM.search(f.get("연식") or "")
    if ym:
        out["year_month"] = f"{ym.group(1)}{int(ym.group(2)):02d}"
        out["form_year"] = int(ym.group(1))

    for key, col in (("주행거리", "mileage_km"), ("배기량", "displacement_cc")):
        got = _int(f.get(key))
        if got is not None:
            out[col] = got
    for key, col in (("차량가격", "price_current_won"),
                     ("신차출고가", "price_origin_won")):
        got = _int(f.get(key))
        if got is not None:
            out[col] = got * WON_PER_MANWON
    for key, col in (("연료", "fuel_raw"), ("색상", "color_ext_raw"),
                     ("변속기", "transmission")):
        if f.get(key):
            out[col] = f[key]
    # ★ 차량번호 — ★ `split_pii` 가 해시로 바꾼다.  ★ 원문을 안 남긴다
    if f.get("차량번호"):
        out["_pii_plate_no"] = f["차량번호"]
    # ★★ 제원 둘 (마스터 확정 08-24) — ★ 없으면 안 넣는다 (NULL = 모름)
    n = seats_of(f)
    if n is not None:
        out["spec_seats"] = n
    kmpl = kmpl_of(f)
    if kmpl is not None:
        out["spec_fuel_economy_kmpl"] = kmpl

    # ★★★ 사진 (명령서 73장 · 실측 08-26).  ★ 리본카는 ★ **상세**에만 사진이 있다.
    #   ★ 그 매물의 사진은 ★ `cdn.autoplus.co.kr/PRODUCT/{source_id}/…` 아래 있다 —
    #     ★ 같은 쪽의 `manage/`(딜러 얼굴) · `CONVENIENCE/`(옵션 아이콘)는 뺀다
    photos = _photos(html, str(source_id))
    if photos:
        out["photo_main"] = photos[0]
        out["photo_list_json"] = json.dumps(photos, ensure_ascii=False)
    return out


def _photos(html: str, source_id: str) -> list:
    """그 매물의 사진 (명령서 73장).  ★ 없으면 빈 목록 — ★ 지어내지 않는다."""
    want = re.compile(
        r"https?://cdn\.autoplus\.co\.kr/PRODUCT/"
        + re.escape(source_id)
        + r"/[^\"'\s<>]+?\.(?:jpg|jpeg|png|webp)", re.I)
    seen, out = set(), []
    for url in want.findall(html or ""):
        if url in seen:
            continue
        seen.add(url)
        out.append(url)
    return out


def seats_of(f: dict) -> int | None:
    """승차정원 — ★ 「5인승」.  ★ 리본카는 ★ `승차인원` 이라 적는다."""
    return _int(f.get("승차인원") or f.get("승차정원"))


def kmpl_of(f: dict) -> float | None:
    """복합연비 — ★ 「12.3km/L」.  ★ 단위 글자는 사이트마다 다르다."""
    got = re.search(r"([\d.]+)\s*km", f.get("복합연비") or f.get("연비") or "")
    return float(got.group(1)) if got else None


def seats(html: str) -> int | None:
    """승차인원 — ★ 「5인승」 (UI_REVIEW 10 · `spec_seats`)."""
    return seats_of(fields(html))


def marks(html: str) -> dict:
    """사이트가 사실로 주는 것 — ★ 사고·침수·용도변경·패널·프레임."""
    f = fields(html)
    return {k: f[k] for k in ("사고여부", "침수여부", "용도변경",
                              "외부 패널", "프레임") if f.get(k)}


# ★★★★★ 08-30 (명령서 r990 · 1-4) — ★ 리본카 골격·외판.
#   ★★ **가르는 규칙을 내가 지어내지 않았다** — ★ 사이트 제 스크립트가 적어 준다
#     (상세 원문 안 · 실측 08-30 · 표본 60건 중 31건에 값이 있다) —
#
#       $('.frame-map').find('i').each(function() {
#         var str = $(this).data('value');            // ★ 「w03」·「x18」
#         var cssType     = str.substring(0, 1);      // ★ 앞 한 글자
#         var cssPosition = parseInt(str.substring(1, 3));
#         if (cssPosition <= 8) {                     // ★ 1~8  = 패널(외판)
#             if (cssType == 'w') data.panelCnt1 += 1;   // ★ 판금
#             else if (cssType == 'x') data.panelCnt2 += 1;  // ★ 교환
#         } else {                                    // ★ 9 이상 = 프레임(골격)
#             if (cssType == 'w') data.frameCnt1 += 1;
#             else if (cssType == 'x') data.frameCnt2 += 1;
#         }
#       })
#
#   ★★ 사이트도 ★ `w`·`x` 만 센다 — ★ 실측에 나온 `t02`·`u02`·`u08` 은
#     ★ ★ 사이트 자신이 ★ **안 센다.**  ★ 우리도 ★ **미확인으로 두고 안 낸다** (금지 6)
RE_FRAME_MAP = re.compile(
    r'class="[^"]*frame-map[^"]*"(.*?)</(?:div|ul|section)>', re.S)
RE_MAP_VALUE = re.compile(r'<i[^>]*data-value="([a-z])(\d{2})[^"]*"')
# ★ 축이 보는 낱말 (`analyze/axis/state.py` SWAP_TITLES · SHEET_TITLES)
RB_TYPE = {"w": ("W", "판금/용접"), "x": ("X", "교환(교체)")}
# ★ 무리 — ★ 축은 ★ 「어느 무리에 드는가」로만 본다 (`_rank_worst`).
#   ★ 리본카는 ★ A·B·C 나 1·2 를 안 준다 — ★ 무리의 첫 값이 곧 무리 이름이다
RB_OUTER, RB_BONE = "RANK_ONE", "RANK_A"
RB_OUTER_MAX = 8            # ★ 1~8 이 패널이다 (위 스크립트)

RB_UNKNOWN: list = []


def panels_of(html: str) -> list | None:
    """`.frame-map` → 엔카 `inspection_panel_json` 과 같은 꼴.

    돌려줌  판 목록.  ★ 빈 배열이면 ★ 「진단표는 있는데 손댄 자리가 없다」다.
           ★ `.frame-map` 자체가 없으면 ★ `None` — ★ 「못 봤다」다 (0 이 아니다)
    """
    if not html:
        return None
    got = RE_FRAME_MAP.search(html)
    if not got:
        return None                     # ★ 진단표가 없다 — ★ 「이상 없음」으로 치지 않는다
    out = []
    for kind, pos in RE_MAP_VALUE.findall(got.group(1)):
        pair = RB_TYPE.get(kind)
        if not pair:
            RB_UNKNOWN.append(kind + pos)
            continue                    # ★ 사이트도 안 세는 부호 — ★ 미확인
        code, title = pair
        rank = RB_OUTER if int(pos) <= RB_OUTER_MAX else RB_BONE
        out.append({"type": {"code": kind + pos, "title": kind + pos},
                    "statusTypes": [{"code": code, "title": title}],
                    "attributes": [rank]})
    return out


def counts_of(html: str) -> dict:
    """★ 사이트가 세는 것과 ★ 같은 셈 — ★ 판금·교환을 패널/프레임으로 나눠 센다.

    ★ 우리 셈이 사이트 화면과 어긋나지 않는지 ★ 대볼 때 쓴다
    """
    pan = panels_of(html)
    if pan is None:
        return {}
    got = {"panelCnt1": 0, "panelCnt2": 0, "frameCnt1": 0, "frameCnt2": 0}
    for one in pan:
        head = "panel" if one["attributes"][0] == RB_OUTER else "frame"
        tail = "1" if one["statusTypes"][0]["code"] == "W" else "2"
        got[head + "Cnt" + tail] += 1
    return got


# ★★★★★ 08-31 (명령서 r1007 · 1b) — ★ **옵션 창구가 열린다.**
#   ★ 가이드 창에서는 ★ 999(봇 차단)였다.  ★ 우리 서버에서 ★ **200 · 16,032B** 다.
#   ★ 가른 것 하나 — ★ **쿠키를 이어야 한다** (`JSESSIONID`).
#     ★ ★ 상세 쪽을 받은 ★ 그 세션으로 ★ 창구를 두드려야 한다.
#     ★ ★ 토큰만 옮겨서는 안 된다 — ★ `RB_TOKEN` 은 ★ 30분짜리 JWT 다
#   ★ 열쇠 셋 — ★ `Authorization: {RB_TOKEN}` · `X-CSRF-TOKEN: {_csrf}` · `X-Ajax-call: true`
#   ★ 실측 08-31 [표본 C26082400119] — ★ 75종 · ★ 달린 것 39종 ·
#     ★ ★ 갈래 CE 15 · IE 26 · SE 16 · TE 18 · ★ HUD·썬루프가 다 있다
RE_RB_TOKEN = re.compile(r'RB_TOKEN\s*=\s*"([^"]+)"')
RE_RB_CSRF = re.compile(r'name="_csrf"[^>]*value="([^"]+)"')


def option_keys(html: str) -> tuple:
    """상세 쪽에서 ★ 창구 열쇠 둘을 뽑는다.  ★ 없으면 ★ (None, None)."""
    tok = RE_RB_TOKEN.search(html or "")
    csrf = RE_RB_CSRF.search(html or "")
    return (tok.group(1) if tok else None, csrf.group(1) if csrf else None)


def options_of(payload) -> dict | None:
    """`carOption.rb` 응답 → ★ 달린 것 · 안 달린 것.

    ★ `carApply` 가 ★ `"1"` 이면 달렸다 · `"0"` 이면 안 달렸다 —
      ★ ★ 둘은 다르다.  ★ 「안 달렸다」는 ★ **확인한 사실**이지 「모른다」가 아니다
    ★ 못 받았으면 ★ `None` 이다 (금지 12)
    """
    if isinstance(payload, (bytes, str)):
        try:
            payload = json.loads(payload)
        except ValueError:
            return None
    if not isinstance(payload, dict):
        return None
    if not ((payload.get("header") or {}).get("isSuccessful")):
        return None
    rows = payload.get("data")
    if not isinstance(rows, list):
        return None
    on, off = [], []
    for one in rows:
        if not isinstance(one, dict) or not one.get("optCode"):
            continue
        (on if str(one.get("carApply")) == "1" else off).append(
            {"code": one["optCode"], "name": one.get("codeNm")})
    return {"on": on, "off": off}
