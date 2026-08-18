# -*- coding: utf-8 -*-
"""V11 표현 계층 검증 (14장 STEP 153).

지시서   STEP 153
근거     ★ 화면은 데이터를 읽는다.  만들지 않는다.
         SQL·산술이 web/ 에 있으면 같은 값이 두 곳에서 만들어진다
금지     검사기 자신을 대상으로 삼는 것 (여섯 번 겪었다)
"""
from __future__ import annotations

import ast
import os
from http import HTTPStatus
import re

from validate.base import (
    canon_text,
    Check,
    FATAL,
    KIND_CODE,
    KIND_CONTRACT,
    KIND_EXTERNAL,
    not_applicable,
    result,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "web")
TEMPLATES = os.path.join(WEB, "templates")

SQL_WORDS = ("SELECT ", "INSERT ", "UPDATE ", "DELETE ", " FROM ")
LOCAL_HOSTS = ("127.0.0.1", "localhost", "::1")
RE_ARITH = re.compile(r"\{\{[^}]*[+\-*/%][^}]*\}\}")

C = {
    "V11-01": Check("V11", "V11-01", "web/ 에 SQL 문자열이 없음", FATAL, "run",
                    "조회는 store · report 가 한다. 화면은 DTO 를 받는다",
                    KIND_CONTRACT),
    "V11-02": Check("V11", "V11-02", "기본 바인딩이 127.0.0.1", FATAL, "run",
                    "config/web.json 의 host 를 되돌린다. "
                    "외부 공개는 --host 로 명시한다",
                    KIND_CONTRACT),
    "V11-03": Check("V11", "V11-03", "전 Route 에 role 이 지정됨", FATAL, "run",
                    "라우팅 표에 role 을 적는다 (STEP 142)", KIND_CODE),
    "V11-04": Check("V11", "V11-04", "템플릿에 산술 연산이 없음", FATAL, "run",
                    "값은 view_* 가 만든다. 템플릿은 표시만 한다 (STEP 152)",
                    KIND_CODE),
    "V11-05": Check("V11", "V11-05", "{{! }} 사용처가 화이트리스트에 있음",
                    FATAL, "run",
                    "RAW_ALLOW 에 없으면 이스케이프한다. "
                    "사용자 입력을 원문으로 넣지 않는다",
                    KIND_CONTRACT),
    "V11-06": Check("V11", "V11-06", "정적 경로 탈출이 거부됨", FATAL, "run",
                    "static_path 의 realpath 검사를 확인한다", KIND_CONTRACT),
    "V11-07": Check("V11", "V11-07", "쿠키에 role 문자열이 없음", FATAL, "run",
                    "쿠키에는 session_id 만 담는다 (STEP 146)", KIND_CONTRACT),
    "V11-08": Check("V11", "V11-08", "상태 변경이 GET 경로에 없음", FATAL, "run",
                    "라우팅 표에서 그 경로를 POST 로 바꾼다 (STEP 147)",
                    KIND_CONTRACT),
    "V11-09": Check("V11", "V11-09", "미리보기 없이 저장이 안 됨", FATAL, "run",
                    "SaveGate 를 거치게 한다 (13장 STEP 138)", KIND_CONTRACT),
    "V11-10": Check("V11", "V11-10", "오류 화면에 스택 트레이스가 없음",
                    FATAL, "run",
                    "traceback 을 화면에 내지 않는다. run_id 만 낸다",
                    KIND_CONTRACT),
    "V11-11": Check("V11", "V11-11", "result_* 가 비었을 때 안내가 나옴",
                    FATAL, "run",
                    "empty_state 가 배너를 내는지 본다 (STEP 149)", KIND_CODE),
    "V11-28": Check("V11", "V11-28", "응답 헤더에 비 ASCII 없음", FATAL, "run",
                    "flash 는 서버가 들고 있다가 다음 GET 에서 낸다. "
                    "HTTP 헤더는 latin-1 이라 한글이면 서버가 죽는다",
                    KIND_CONTRACT),
    "V11-29": Check("V11", "V11-29", "렌더된 폼의 csrf_token 이 비어 있지 않음",
                    FATAL, "run",
                    "부분 템플릿에도 PageContext 를 넘긴다 (STEP 144)",
                    KIND_CODE),
    "V11-30": Check("V11", "V11-30", "시안 ↔ 템플릿 대조 통과", FATAL, "run",
                    "tools/check_screens.py 를 보고 시안을 먼저 확인한다",
                    KIND_CODE),
    "V11-31": Check("V11", "V11-31",
                    "must_change_secret=1 에서 /password 가 200",
                    FATAL, "run",
                    "바꾸는 화면 자체가 막히면 못 바꾼다. 예외를 늘리지 않는다",
                    KIND_CONTRACT),
    "V11-32": Check("V11", "V11-32", "known_issues 의 키가 전부 targets 에 있음",
                    FATAL, "run",
                    "없는 차종의 결함 메모는 화면에 못 뜬다. 오타를 잡는다",
                    KIND_EXTERNAL),
    "V11-13": Check("V11", "V11-13", "app.css 에 토큰 밖의 색값이 없음", FATAL, "run",
                    "STEP 145a 의 12 토큰만 쓴다. 색이 늘면 강조가 사라진다",
                    KIND_CODE),
    "V11-14": Check("V11", "V11-14", "숫자 셀에 mono 가 걸려 있음", FATAL, "run",
                    "자릿수가 세로로 맞아야 비교된다",
                    KIND_CODE),
    "V11-15": Check("V11", "V11-15", "화면이 빌드 산출물에 의존하지 않음", FATAL, "run",
                    "표준 라이브러리만 쓴다",
                    KIND_CONTRACT),
    "V11-16": Check("V11", "V11-16", "/why 가 전 Component 를 냄", FATAL, "run",
                    "17축 전건을 낸다",
                    KIND_CODE),
    "V11-17": Check("V11", "V11-17", "/why 가 조회 상태 절을 냄", FATAL, "run",
                    "excluded 축이 왜 비었는지 설명한다",
                    KIND_CODE),
    "V11-18": Check("V11", "V11-18", "축 태그가 전건 필터 링크임", FATAL, "run",
                    "값을 누르면 그 조건으로 걸러진다",
                    KIND_CODE),
    "V11-19": Check("V11", "V11-19", "폴링 실패 시 화면이 안 깨짐", FATAL, "run",
                    "JS 에 의존하지 않는다",
                    KIND_CODE),
    "V11-20": Check("V11", "V11-20", "분모 표시가 있음", FATAL, "run",
                    "earned/denominator 를 같은 자로 낸다",
                    KIND_CODE),
    "V11-21": Check("V11", "V11-21", "행동 요청 파라미터가 현재 필터와 일치", FATAL, "run",
                    "지금 조건이 다음 행동의 조건이다",
                    KIND_CODE),
    "V11-22": Check("V11", "V11-22", "excluded 축이 「—/N」 으로 표시됨", FATAL, "run",
                    "0 점이 아니라 제외다",
                    KIND_CODE),
    "V11-23": Check("V11", "V11-23", "비로그인 관심 POST 가 유도 화면을 냄", FATAL, "run",
                    "403 이 아니라 로그인을 유도한다",
                    KIND_CODE),
    "V11-24": Check("V11", "V11-24", "메뉴 분류가 잠금 단위와 일치", FATAL, "run",
                    "운영·조정·탐색 3분류",
                    KIND_CONTRACT),
    "V11-25": Check("V11", "V11-25", "사유 없이 설정이 저장되지 않음", FATAL, "run",
                    "왜 바꿨는지가 남아야 한다",
                    KIND_CONTRACT),
    "V11-26": Check("V11", "V11-26", "되돌릴 수 없는 행동에 확인이 있음", FATAL, "run",
                    "확인 문구를 넣는다",
                    KIND_CONTRACT),
    "V11-27": Check("V11", "V11-27", "가입 정책에 따라 화면이 바뀜", FATAL, "run",
                    "open·approval·closed",
                    KIND_CODE),
    "V11-33": Check("V11", "V11-33", "POST 가 저장 없이 성공 메시지를 내지 않음", FATAL, "run",
                    "실제로 저장하거나, 준비 중이라고 낸다",
                    KIND_CONTRACT),
    "V11-35": Check("V11", "V11-35", "중첩 if 가 안쪽부터 닫힘", FATAL, "run",
                    "짝을 세어 닫는다",
                    KIND_CODE),
    "V11-34": Check("V11", "V11-34", "화면이 요청당 쿼리 상한을 넘지 않음",
                    FATAL, "run",
                    "축 조회를 IN 절로 묶는다. 행마다 돌면 200행에 1,000쿼리다",
                    KIND_CODE),
    "V11-36": Check("V11", "V11-36", "잘못된 쿼리 파라미터가 500 을 내지 않음",
                    FATAL, "run",
                    "500 은 「우리 결함」이라는 뜻이다. 입력 오류는 400 이다",
                    KIND_CODE),
    "V11-37": Check("V11", "V11-37", "POST 가 예상 밖 500 을 내지 않음",
                    FATAL, "run",
                    "전 POST 를 눌러 본다. 500 은 우리 결함이라는 뜻이고 "
                    "입력 오류는 400, 권한은 403 이다",
                    KIND_CODE),
    "V11-38": Check("V11", "V11-38", "템플릿이 쓰는 값을 뷰가 넘김",
                    FATAL, "run",
                    "절만 만들고 값을 안 넘기면 화면이 조용히 빈 채로 뜬다. "
                    "엔진이 없는 이름을 빈 값으로 내주어 아무도 모른다",
                    KIND_CODE),
    "V11-39": Check("V11", "V11-39", "저장 단추가 실제로 저장함",
                    FATAL, "run",
                    "「저장」이라 적힌 단추가 아무것도 안 바꾸면 사람이 "
                    "바뀐 줄 알고 넘어간다. 준비 중이면 disabled 로 둔다",
                    KIND_CODE),
    "V11-12": Check("V11", "V11-12", "라우팅 표의 view 가 10·13장에 실재함",
                    FATAL, "run",
                    "없는 화면은 라우팅 표에서 뺀다", KIND_CODE),
    "V11-40": Check("V11", "V11-40", "반입분의 origin 이 'import' 임",
                    FATAL, "run",
                    "밖에서 받아 넣은 목록을 collector 로 남기면 "
                    "「우리가 받았다」가 된다 (STEP 136a)",
                    KIND_CODE),
    "V11-41": Check("V11", "V11-41", "반입 뒤 S5~S10 이 이어서 돎",
                    FATAL, "run",
                    "반입이 S4 완료를 안 남기면 precheck('S5') 가 "
                    "「선행 단계 미완료」로 막는다 (STEP 136b ④)",
                    KIND_CODE),
    "V11-43": Check("V11", "V11-43", "브라우저 수집분의 origin 이 'browser' 임",
                    FATAL, "run",
                    "사용자 회선으로 받은 것을 collector 로 남기면 "
                    "「서버가 받았다」가 된다 (STEP 136c)",
                    KIND_CODE),
    "V11-44": Check("V11", "V11-44", "사람 확인 없이 저장되지 않음",
                    FATAL, "run",
                    "②를 건너뛰고 자동 저장하면 무엇이 들어갔는지 모른다 "
                    "(STEP 136c · 149k)",
                    KIND_CODE),
    "V11-53": Check("V11", "V11-53",
                    "진행 판정이 큐만 보지 않음", FATAL, "run",
                    "큐를 안 거친 실행을 「할 일 없음」으로 단정하면 화면이 "
                    "스스로 모순된다 — 「도는 것이 없다」와 「0분 전 처리」가 "
                    "같은 화면에 있었다 (개정 273)",
                    KIND_CODE),
    "V11-54": Check("V11", "V11-54", "메뉴에 경로가 그대로 나오지 않음",
                    FATAL, "run",
                    "이름이 없으면 「/admin/status」가 메뉴에 그대로 뜬다. "
                    "13장 STEP 138 메뉴표가 정본이다 (개정 274)",
                    KIND_CODE),
    "V11-55": Check("V11", "V11-55", "목록에 전체 건수와 쪽이 표시됨",
                    FATAL, "run",
                    "200건만 보이면서 전체를 안 적으면 3,470건을 못 본다. "
                    "「3,470건 중 200건 · 1/18쪽」 (개정 274)",
                    KIND_CODE),
    "V11-56": Check("V11", "V11-56", "대표 사진 경로가 저장됨", FATAL, "run",
                    "차를 고르는 도구인데 차가 안 보인다. 원문에 이미 있다 "
                    "— 다시 받을 필요가 없다 (개정 274)",
                    KIND_EXTERNAL),
    "V11-57": Check("V11", "V11-57", "사진 없는 매물이 화면을 무너뜨리지 않음",
                    FATAL, "run",
                    "사진이 없다고 행을 숨기지 않는다. thumb-none 으로 "
                    "자리를 채운다 (개정 274)",
                    KIND_CODE),
    "V11-58": Check("V11", "V11-58", "쪽을 넘겨도 조건이 남음", FATAL, "run",
                    "2쪽에서 필터가 풀리면 무엇을 보고 있는지 알 수 없다 "
                    "(개정 274)",
                    KIND_CODE),
    "V11-59": Check("V11", "V11-59", "시안의 클래스가 CSS 에 있음", FATAL, "run",
                    "화면이 시안의 이름을 쓰는데 CSS 에 그 이름이 없으면 "
                    "표가 아니라 글자 뭉치가 된다 — .chips 가 그랬다 (개정 275)",
                    KIND_CODE),
    "V11-60": Check("V11", "V11-60", "시안 CSS 를 다시 만들지 않음", FATAL, "run",
                    "시안이 정본이다. 손으로 옮겨 적으면 값이 갈린다 "
                    "(개정 275)",
                    KIND_CODE),
    "V11-61": Check("V11", "V11-61", "이어질 수 있는 값이 링크임", FATAL, "run",
                    "절반만 링크면 사람이 「누를 수 있는 것」과 「없는 것」을 "
                    "구분 못 한다 (STEP 149p · 개정 276)",
                    KIND_CODE),
    "V11-62": Check("V11", "V11-62", "코드·줄임말에 title 이 있음", FATAL, "run",
                    "「320.0/415.0」이 무엇인지 아무도 모른다. "
                    "「O · · · ?」도 마찬가지다 (STEP 149p)",
                    KIND_CODE),
    "V11-63": Check("V11", "V11-63", "매물 화면에 원문 링크가 있음", FATAL, "run",
                    "우리 판정은 참고다. 실제 매물은 엔카에 있다 — "
                    "그 길을 막으면 도구가 아니라 벽이 된다 (STEP 149q)",
                    KIND_CODE),
    "V11-64": Check("V11", "V11-64", "고를 수 있는 값이 목록으로 제공됨",
                    FATAL, "run",
                    "「KOLEOS_HEV」를 외워 치라는 것은 도구가 아니다 "
                    "(STEP 149r)",
                    KIND_CODE),
    "V11-65": Check("V11", "V11-65", "기본 정렬이 규격대로임", FATAL, "run",
                    "볼 필요 없는 C·D·미분류가 앞에 잔뜩 나온다. "
                    "「A 이상만」을 한 번에 거는 단추를 둔다 (STEP 149s)",
                    KIND_CODE),
    "V11-66": Check("V11", "V11-66", "필터가 목록 위에 있음", FATAL, "run",
                    "조건을 걸려면 표의 값을 눌러야만 하면 안 된다 (STEP 149t)",
                    KIND_CODE),
    "V11-67": Check("V11", "V11-67", "단추가 켜짐·꺼짐을 오감", FATAL, "run",
                    "누르면 켜지고 다시 누르면 꺼진다. 켜진 것은 amber "
                    "(STEP 149t)",
                    KIND_CODE),
    "V11-68": Check("V11", "V11-68", "v1 이 낸 열이 v2 에도 있음",
                    FATAL, "run",
                    "v1 목록은 22열이고 축을 열로 갈랐다. 칩으로 뭉치면 "
                    "「이 차만 HUD 가 없다」가 안 보인다 (STEP 149o · 개정 277)",
                    KIND_CONTRACT),
    "V11-69": Check("V11", "V11-69", "v1 이 가진 조작이 v2 에도 있음",
                    FATAL, "run",
                    "단추 on/off · 정렬 드롭다운 · 건수 · 칩 해제 · 엔카 링크 · "
                    "미리보기 (STEP 149o)",
                    KIND_CONTRACT),
    "V11-70": Check("V11", "V11-70", "좁은 폭에서 값이 사라지지 않음",
                    FATAL, "run",
                    "「좁으니 뺀다」가 아니라 「좁으니 다르게 놓는다」다. "
                    "어느 폭에서도 한 매물의 전부가 보인다 (STEP 149o-2). "
                    "★ 부록 G 「좁음 (<640)」 도면이 뺀 칸만 접을 수 있다 "
                    "— config/web.json narrow_folded_labels 에 적은 것만 "
                    "(개정 332).  적지 않고 지우면 여기서 걸린다",
                    KIND_CODE),
    "V11-71": Check("V11", "V11-71", "가로 스크롤로 떠넘기지 않음", FATAL, "run",
                    "오른쪽에 무엇이 있는지 모른 채 스크롤하게 하지 않는다 "
                    "(STEP 149o-2 · 개정 278)",
                    KIND_CODE),
    "V11-72": Check("V11", "V11-72", "빈 주소로 가는 링크가 없음", FATAL, "run",
                    "주소가 될 값이 비었으면 링크를 만들지 않는다 — "
                    "「빈 링크」가 아니라 「링크 아님」이다.  실측 08-16: "
                    "마스터가 링크를 눌렀더니 주소가 null 이었다",
                    KIND_CODE),
    "V11-77": Check("V11", "V11-77", "시안의 시각 요소가 렌더 결과에 나옴",
                    FATAL, "run",
                    "CSS 에 있는 것과 화면에 쓰이는 것은 다르다. "
                    ".hist 를 CSS 에 넣어도 market.html 이 <table> 이면 "
                    "소용없다 — 실측 08-16 (검토 14)",
                    KIND_CODE),
    "V11-78": Check("V11", "V11-78", "좁은 폭에서 글자가 세로로 안 떨어짐",
                    FATAL, "run",
                    "표가 화면에 맞춰 쥐어짜이면 한 글자가 한 줄이 된다. "
                    "실측 08-16 admin_dict — 「프/론/트/휀/더」 (검토 17)",
                    KIND_CODE),
    "V11-104": Check("V11", "V11-104", "템플릿 문법이 화면에 새지 않음",
                     FATAL, "run",
                     "엔진이 모르는 문법은 글자 그대로 나온다 — "
                     "{# 주석 #} 과 {% if a == b %} 이 화면에 찍혔다 (개정 325)",
                     KIND_CODE),
    "V11-106": Check("V11", "V11-106", "값 자리에 「—」가 없음",
                     FATAL, "run",
                     "줄표는 못 받은 것인지 0 인지 안 봐도 되는 것인지를 감춘다. "
                     "가이드 지적 08-17 — 「—」가 21곳에서 41곳으로 늘었다. "
                     "값이 없으면 「없습니다」 · 0 이면 「0원」 · "
                     "모르면 「확인 못 함」 (부록 G · G-4)",
                     KIND_CODE),
    "V11-113": Check("V11", "V11-113", "다섯 폭 스크린샷이 있음",
                     FATAL, "run",
                     "360 · 640 · 900 · 1100 · 1400 — 경계 바로 안쪽·바깥쪽을 "
                     "함께 본다.  360·1400 둘만 찍어 가운데가 통째로 깨진 채 "
                     "있었다 (개정 337)",
                     KIND_CODE),
    "V11-114": Check("V11", "V11-114", "폭마다 부록 G 의 배치임",
                     FATAL, "run",
                     "좁음 카드 · 중간 표 2줄 · 넓음 표 1줄. "
                     "CSS 의 경계가 config 와 같은가 — 코드와 정책이 갈리면 "
                     "어느 쪽이 맞는지 아무도 모른다 (개정 337)",
                     KIND_CODE),
    "V11-115": Check("V11", "V11-115", "어느 폭에서도 글자가 세로로 안 떨어짐",
                     FATAL, "run",
                     "★ 한 칸 폭 ÷ 글자 폭 < 3 이면 실패 (개정 337). "
                     "마스터 실측 — 약 1200px 에서 「A 8 0 _ 2 5 T」로 "
                     "한 자씩 떨어졌다.  V11-78 은 좁은 폭만 봤다",
                     KIND_CODE),
    "V11-116": Check("V11", "V11-116", "카드 전체가 상세 링크임",
                     FATAL, "run",
                     "마스터 지적 — 「리스트를 클릭하면 상세나 툴팁이 보여야 "
                     "하는데 그것도 없고」.  「근거」 글자 하나만 링크면 "
                     "손가락으로 못 누른다 (개정 337)",
                     KIND_CODE),
    "V11-117": Check("V11", "V11-117", "터치로 미리보기가 뜸",
                     FATAL, "run",
                     "마스터는 휴대폰·태블릿으로 본다 — hover 가 없다. "
                     "한 번 대면 뜨고 다시 대면 상세로 간다 (개정 337)",
                     KIND_CODE),
    "V11-119": Check("V11", "V11-119", "화면마다 부록 G 가 정한 차트가 있음",
                     FATAL, "run",
                     "마스터 지적 — 「차트가 안 보이잖아」. "
                     "차트가 없으면 왜 없는지 적는다.  ★ 자리를 비워 두지 "
                     "않는다 (개정 340)",
                     KIND_CODE),
    "V11-110": Check("V11", "V11-110", "상세 절 순서가 부록 G 와 같음",
                     FATAL, "run",
                     "순서가 판단 순서다 — 값을 먼저 보고 근거를 나중에 본다. "
                     "★ 절 이름을 코드에 박지 않는다.  부록 G 3장에서 읽는다",
                     KIND_CODE),
    "V11-108": Check("V11", "V11-108", "좁은 폭에서 한 화면에 매물 2개 이상",
                     FATAL, "run",
                     "하나만 보이면 비교가 안 된다 (부록 G 줄 수 상한). "
                     "★ 격자 줄 수와 글자 크기로 카드 높이의 상한을 잡는다 "
                     "— 두 장이 700px 안에 들어가야 한다",
                     KIND_CODE),
    "V11-109": Check("V11", "V11-109", "카드가 부록 G 줄 수 상한을 안 넘음",
                     FATAL, "run",
                     "목록 6줄 · 추천 8줄 (부록 G).  ★ 한 줄의 칸 span 합이 "
                     "격자 칸 수를 넘으면 칸이 겹쳐 글자가 뭉갠다 — "
                     "실측 08-18 「용도」 하나가 span 6 이라 5줄이 15칸이 됐다",
                     KIND_CODE),
    "V11-107": Check("V11", "V11-107", "화면별 사진 크기가 부록 G 와 같음",
                     FATAL, "run",
                     "추천은 목록보다 작다 — 한 화면에 여러 후보가 보여야 한다. "
                     "크기를 CSS 로 고정한다 (부록 G 0절 · 개정 332)",
                     KIND_CONTRACT),
    "V11-105": Check("V11", "V11-105", "화면 위아래가 어긋나지 않음",
                     FATAL, "run",
                     "표는 「카탈로그 미조회」라 하고 문장은 「확인율 100%」라 "
                     "했다.  표가 옳고 문장이 표를 배신했다 (개정 325)",
                     KIND_CONTRACT),
    "V11-98": Check("V11", "V11-98", "큰 원문을 조각으로 보내고 이어붙이는가",
                    FATAL, "run",
                    "facet 은 하나의 JSON 이라 내용으로 못 나눈다 — "
                    "바이트를 나눈다.  상한을 올려 해결하지 않는다 (개정 307)",
                    KIND_CONTRACT),
    "V11-99": Check("V11", "V11-99", "같은 화면에서 여러 번 POST 가 되는가",
                    FATAL, "run",
                    "토큰을 서버 메모리에 두면 재시작에 전부 무효가 된다 — "
                    "마스터 실측 08-17: 전 차종 수집이 첫 묶음만 되고 "
                    "나머지 7개가 403 이었다 (개정 308)",
                    KIND_CONTRACT),
    "V11-92": Check("V11", "V11-92", "신차가가 등급기준 + 옵션 합", FATAL, "run",
                    "엔카는 6,547만(등급 5,787 + 옵션 760)인데 "
                    "우리는 5,787만만 냈다.  셋을 다 낸다 (개정 301)",
                    KIND_CONTRACT),
    "V11-82": Check("V11", "V11-82", "정적 파일에 버전이 붙음", FATAL, "run",
                    "화면을 고쳤는데 브라우저가 옛 CSS 를 쓰면 사람이 강제 "
                    "새로고침을 해야 한다 — 마스터가 히스토그램을 못 봤다 "
                    "(개정 282)",
                    KIND_CODE),
    "V11-79": Check("V11", "V11-79", "축 칸에 맨 숫자가 나오지 않음",
                    FATAL, "run",
                    "「HUD 0 은 있다는 거야 없다는 거야」 — 점수는 판정의 "
                    "결과이지 사람이 알고 싶은 것이 아니다 (STEP 149n · 개정 280)",
                    KIND_CODE),
    "V11-80": Check("V11", "V11-80", "사진이 최소 크기 이상", FATAL, "run",
                    "64px 은 차가 안 보인다.  차를 고르는 도구다 "
                    "(개정 281).  좁아도 줄이지 않는다",
                    KIND_CODE),
    "V11-81": Check("V11", "V11-81", "신차가 · 시세 · 가격 셋이 함께 나옴",
                    FATAL, "run",
                    "차이만 내면 무엇에서 뺀 것인지 모른다.  기준이 틀리면 "
                    "차이도 틀리다 (STEP 149n-3 · 개정 283)",
                    KIND_CODE),
    "V11-73": Check("V11", "V11-73", "화면마다 값이 나옴", FATAL, "run",
                    "「빈 화면」과 「값이 없는 화면」을 가른다 (방법 D안)",
                    KIND_CODE),
    "V11-74": Check("V11", "V11-74", "숫자가 단위와 함께 나옴", FATAL, "run",
                    "「3044」가 아니라 「3,044만」이다 (방법 D안)",
                    KIND_CODE),
    "V11-75": Check("V11", "V11-75", "링크가 유효함", FATAL, "run",
                    "링크가 몇 개이고 그중 몇 개가 유효한가 (방법 D안)",
                    KIND_CODE),
    "V11-76": Check("V11", "V11-76", "화면 크기·시간이 상한 안", FATAL, "run",
                    "dealers 139KB 는 이 검사가 잡아야 한다 (방법 D안)",
                    KIND_CODE),
    "V11-51": Check("V11", "V11-51", "진행 화면이 스스로 갱신됨", FATAL, "run",
                    "1시간짜리 수집을 손으로 새로고침하며 볼 수는 없다. "
                    "간격은 config 에 둔다 (STEP 136f · 개정 272)",
                    KIND_CODE),
    "V11-52": Check("V11", "V11-52", "진행 화면에 실행 단추가 없음", FATAL, "run",
                    "지켜보는 곳과 실행하는 곳을 나눈다.  보다가 또 누르면 "
                    "1만 호출이 도는 중에 다시 시작된다 (STEP 136f)",
                    KIND_CODE),
    "V11-47": Check("V11", "V11-47",
                    "브라우저 수집이 한 번에 max_form_bytes 를 넘기지 않음",
                    FATAL, "run",
                    "JS 가 나눠 보낸다.  사람에게 「나눠서 보내십시오」라고 "
                    "하지 않는다 (개정 263)",
                    KIND_CODE),
    "V11-48": Check("V11", "V11-48", "전 차종 수집에 확인 절차가 있음",
                    FATAL, "run",
                    "전 차종은 「높음」이다.  all 을 입력받는다 (STEP 149l)",
                    KIND_CODE),
    "V11-49": Check("V11", "V11-49", "한 차종 실패가 나머지를 멈추지 않음",
                    FATAL, "run",
                    "실패한 차종만 남기고 나머지를 이어서 한다 (개정 264)",
                    KIND_CODE),
    "V11-46": Check("V11", "V11-46", "반입으로 연 단계의 actual 이 'import' 임",
                    FATAL, "run",
                    "S1·S2·S4 를 반입이 대신했으면 그렇게 남긴다. "
                    "근거 없이 열면 「우리가 받았다」가 된다 (개정 259)",
                    KIND_CODE),
    "V11-42": Check("V11", "V11-42", "S4 완료 행의 actual 이 'import' 임",
                    FATAL, "run",
                    "반입인데 collector 로 남기면 감사 기록이 거짓이 된다 "
                    "(STEP 136b ④)",
                    KIND_CODE),
}

# ★ 상태를 바꾸는 이름.  GET 경로에 있으면 안 된다 (STEP 147)
MUTATING = ("add", "update", "delete", "create", "apply", "save", "logout",
            "revert", "confirm")
# 그래도 GET 이 허용되는 것 — 폼을 「보여주는」 화면이다
MUTATING_GET_OK = ("view_admin_run", "view_admin_scoring",
                   "view_admin_targets", "view_admin_registry",
                   "view_admin_config", "view_admin_query", "view_admin_api",
                   "view_admin_tools", "view_admin_requests")


def _web_sources() -> dict[str, str]:
    out = {}
    for base, dirs, files in os.walk(WEB):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(base, f)
                out[os.path.relpath(path, ROOT).replace("\\", "/")] = \
                    open(path, encoding="utf-8").read()
    return out


def run(conn, ctx) -> list:
    from web.routes import GET, POST, ROUTES
    from web.session import static_path
    from web.template import RAW_ALLOW
    from web.server import load_web_config

    rid = ctx.run_id
    src = _web_sources()
    out = []

    # V11-01 — 화면이 조회하지 않는다.  문자열 상수만 본다 (STEP 53)
    bad = []
    for rel, body in src.items():
        try:
            tree = ast.parse(body)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and any(w in n.value.upper() for w in SQL_WORDS):
                bad.append(f"{rel}: {n.value[:40]}")
    out.append(result(C["V11-01"], rid, 0, bad or 0, not bad, bad))

    # V11-02
    host = load_web_config(ROOT)["host"]
    out.append(result(C["V11-02"], rid, "127.0.0.1", host,
                      host in LOCAL_HOSTS))

    # V11-03
    bad = [r.path for r in ROUTES if not r.role]
    out.append(result(C["V11-03"], rid, 0, bad or 0, not bad, bad))

    # V11-04
    bad = []
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".html"):
            continue
        body = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        for m in RE_ARITH.finditer(body):
            bad.append(f"{name}: {m.group(0)[:30]}")
    out.append(result(C["V11-04"], rid, 0, bad or 0, not bad, bad))

    # V11-05
    bad = []
    for name in sorted(os.listdir(TEMPLATES)):
        if not name.endswith(".html"):
            continue
        body = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        for m in re.finditer(r"\{\{!\s*([\w.]+)\s*\}\}", body):
            if m.group(1) not in RAW_ALLOW:
                bad.append(f"{name}: {m.group(1)}")
    out.append(result(C["V11-05"], rid, 0, bad or 0, not bad, bad))

    # V11-06 — 실제로 던져 본다
    leaked = [p for p in ("../secrets/plate_hmac.key", "../../etc/passwd",
                          "/etc/passwd", "....//x")
              if static_path(p) is not None]
    out.append(result(C["V11-06"], rid, 0, leaked or 0, not leaked, leaked))

    # V11-07
    from web.session import set_cookie

    cookie = set_cookie("cw_session", "x", 1)
    has_role = "role" in cookie or "admin" in cookie
    out.append(result(C["V11-07"], rid, "없음",
                      "있음" if has_role else "없음", not has_role))

    # V11-08 — 상태 변경이 GET 으로 열려 있는가
    bad = []
    for r in ROUTES:
        if GET not in r.methods:
            continue
        if any(w in r.view for w in MUTATING) \
                and r.view not in MUTATING_GET_OK:
            bad.append(f"{r.path} ({r.view})")
    out.append(result(C["V11-08"], rid, 0, bad or 0, not bad, bad))

    # V11-09 — SaveGate 가 미리보기를 요구하는가
    from report.screens.admin import SaveGate

    gate = SaveGate(previewed=False, reason_given=True, locked=False)
    ok = not gate.can_save and SaveGate(True, True, False).can_save
    out.append(result(C["V11-09"], rid, "막힘", "막힘" if ok else "통과", ok))

    # V11-10 — 오류 화면이 내부 문구를 내는가
    from web.context import error_page

    page = error_page(RuntimeError("list index out of range"), "r1")
    leaked = [w for w in ("Traceback", "index", "File \"", "line ")
              if w in page.reason or w in page.action]
    out.append(result(C["V11-10"], rid, 0, leaked or 0, not leaked, leaked))

    # V11-11 — 비었을 때 안내
    from web.app import empty_state

    banner = empty_state(conn, ctx_account(ctx))
    total = _count(conn, "result_score")
    need = total == 0
    ok = (banner is not None) if need else True
    out.append(result(C["V11-11"], rid, "안내" if need else "해당 없음",
                      banner.text if banner else "없음", ok))

    # V11-12 — 지시서 표 ↔ 코드 ↔ HANDLERS 삼자 대조
    out.append(_routing_table_check(rid))
    out += _late_checks(rid)
    out += _screen_checks(conn, rid)
    _ = POST
    return out


def _late_checks(rid) -> list:
    """08-14 신설 5종 (STEP 153)."""
    import json
    import subprocess
    import sys as _s

    from contracts import ANONYMOUS, Account, ROLE_ADMIN
    from web.app import redirect
    from web.routes import GET, ROUTES, match
    from web.server import guard
    from web.template import render_str

    out = []

    # V11-28 — 헤더에 비 ASCII 가 있으면 서버가 죽는다
    _st, headers, _b = redirect("/watch", "관심에 담았습니다", "k")
    bad = []
    for k, v in headers.items():
        try:
            f"{k}: {v}".encode("latin-1")
        except UnicodeEncodeError:
            bad.append(f"{k}: 비 ASCII")
    out.append(result(C["V11-28"], rid, 0, bad or 0, not bad, bad))

    # V11-29 — 폼 템플릿이 page 없이 렌더되면 토큰이 빈다
    html = render_str('{{ page.csrf_token }}', {"page": {"csrf_token": "T"}})
    empty = render_str('{{ page.csrf_token }}', {})
    ok = html == "T" and empty == ""
    forms = _templates_with_form()
    missing = [f for f in forms if "page.csrf_token" not in
               open(os.path.join(TEMPLATES, f), encoding="utf-8").read()]
    bad = ([] if ok else ["템플릿 엔진이 page 를 못 읽는다"])
    bad += [f"{f}: 폼에 csrf 가 없다" for f in missing]
    out.append(result(C["V11-29"], rid, 0, bad or 0, not bad, bad))

    # V11-30 — 시안 대조.  ★ 검사를 검사한다
    r = subprocess.run([_s.executable,
                        os.path.join(ROOT, "tools", "check_screens.py")],
                       capture_output=True, text=True, cwd=ROOT)
    bad = [x.strip() for x in r.stdout.splitlines() if "✗" in x][:6]
    out.append(result(C["V11-30"], rid, 0, len(bad), r.returncode == 0, bad))

    # V11-31 — 바꾸는 화면 자체는 열린다
    tmp = Account(1, ROLE_ADMIN, "임시", must_change_secret=True)
    route = match("/password", GET)[0]
    ok = route is not None and guard(tmp, route) is None
    out.append(result(C["V11-31"], rid, "200", "200" if ok else "막힘", ok))

    # V11-32 — known_issues 의 키가 targets 에 있는가
    bad = []
    ki = os.path.join(ROOT, "config", "known_issues.json")
    tg = os.path.join(ROOT, "config", "targets.json")
    if os.path.isfile(ki) and os.path.isfile(tg):
        with open(ki, encoding="utf-8") as f:
            issues = json.load(f)
        with open(tg, encoding="utf-8") as f:
            keys = set(json.load(f))
        bad = [f"없는 차종: {k}" for k in issues
               if not k.startswith("_") and k not in keys]
    out.append(result(C["V11-32"], rid, 0, bad or 0, not bad, bad))
    _ = (ANONYMOUS, ROUTES)
    return out


def _templates_with_form() -> list:
    return [f for f in sorted(os.listdir(TEMPLATES))
            if f.endswith(".html")
            and "<form" in open(os.path.join(TEMPLATES, f),
                                encoding="utf-8").read()]


# 화면이 아닌 Route.  파일을 낸다 — HANDLERS 에 없는 것이 맞다
NON_SCREEN_VIEWS = ("serve_static",)


# 라우팅 표 행.  ★ 표가 여러 개로 나뉘어도 합쳐 센다 (실측: 26 + 3)
RE_ROUTE_ROW = re.compile(r"^\| \*?\*?`([^`]+)`\*?\*? \| *(?:GET|POST)",
                          re.M)


def _spec_routes() -> list | None:
    """지시서에서 라우팅 표 행을 전수 뽑는다.

    ★ 「path | method」 머리글만 찾으면 뒤에 이어지는 별표를 놓친다.
      실측: 본표 26 + 시안표 3 = 29 였는데 26 만 세어 3 을 놓쳤다
    """
    # ★ 장 파일이 정본이다.  통짜 지시서는 옛 판일 수 있다 (실측)
    for rel in (os.path.join("docs", "chapters", "61-web.md"),
                "개발지시서.md"):
        path = os.path.join(ROOT, rel)
        if not os.path.isfile(path):
            continue
        # 앞 파일이 있으면 그것만 본다 — 뒤 파일이 대신 통과시키지 않는다
        body = open(path, encoding="utf-8").read()
        rows = RE_ROUTE_ROW.findall(body)
        if rows:
            # ★ 첫 번째로 찾은 것을 쓴다.  「행이 적으면 다음 파일」로 넘어가면
            #   행을 지웠을 때 옛 판이 대신 통과시킨다 (실측)
            return rows
    return None


def _routing_table_check(rid):
    """★ 지시서 표를 실제로 센다.

    실측: 「표의 view 가 코드에 있는가」만 보고 표 자체는 안 봤다.
         그 결과 표 29 · 코드 30 이 어긋난 것을 검사가 못 잡았다.
    본다   ① 표에 있는데 코드에 없다  ② 코드에 있는데 표에 없다
          ③ 표의 view 가 HANDLERS 에 없다 (serve_static 제외)
    """
    from web.routes import ROUTES
    from web.views import HANDLERS

    bad = []
    code_paths = {r.path for r in ROUTES}
    rows = _spec_routes()

    if rows is None:
        bad.append("라우팅 표를 찾지 못했다 (개발지시서.md · docs/chapters)")
    else:
        table = set(rows)
        if len(rows) != len(table):
            bad.append(f"★ 표에 중복 행 {len(rows) - len(table)}개 — "
                       f"한 행에 한 경로다")
        bad += [f"표에만 있다: {p}" for p in sorted(table - code_paths)]
        bad += [f"표에 없다: {p}" for p in sorted(code_paths - table)]

    bad += [f"{r.path} → {r.view} 가 HANDLERS 에 없다" for r in ROUTES
            if r.view not in HANDLERS and r.view not in NON_SCREEN_VIEWS]
    n = len(HANDLERS) + len(NON_SCREEN_VIEWS)
    if n != len(ROUTES):
        bad.append(f"Route {len(ROUTES)} ≠ HANDLERS {len(HANDLERS)} "
                   f"+ 비화면 {len(NON_SCREEN_VIEWS)}")
    return result(C["V11-12"], rid, 0, len(bad), not bad, bad[:20])


def _count(conn, table: str) -> int:
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except Exception:                                    # noqa: BLE001
        return 0


def ctx_account(ctx):
    from contracts import ANONYMOUS

    return getattr(ctx, "account", ANONYMOUS)


def _view_exists(name: str) -> bool:
    """10장 화면 · 13장 관리자 화면 · 14장 어댑터 중 하나에 있으면 된다."""
    from report.screens import admin as admin_screens
    from report.screens import build as screens
    from web import views as web_views

    if name in getattr(web_views, "HANDLERS", {}):
        return True
    return any(hasattr(m, name) for m in (screens, admin_screens))


# ── V11-13 ~ V11-27 · V11-33 ~ V11-36 (STEP 153) ────────────────────
# ★ 화면 규격은 시안이 정본이다.  여기서는 「지켜졌는가」만 본다
RE_COLOR = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RE_ROOT = re.compile(r":root\s*\{[^}]*\}", re.S)
BUILD_ARTIFACTS = ("node_modules", "dist/", "webpack", "vite", ".min.js",
                   "npm run", "package.json")
# 되돌릴 수 없는 행동.  ★ 확인 없이 실행되면 안 된다 (V11-26)
IRREVERSIBLE = ("remove", "delete", "disable", "close", "revert")


def _tpl(name: str) -> str:
    path = os.path.join(TEMPLATES, name)
    return open(path, encoding="utf-8").read() if os.path.isfile(path) else ""


def _all_templates() -> dict:
    return {f: _tpl(f) for f in sorted(os.listdir(TEMPLATES))
            if f.endswith(".html")}


def _screen_checks(conn, rid) -> list:
    """08-14 신설 19종.  ★ D-1 이 가리고 있어 검사 밖에 있던 것들이다."""
    from web.routes import GET, ROUTES
    from web.template import FILTERS

    out = []
    css = _tpl("").join(()) if False else open(
        os.path.join(ROOT, "web", "static", "app.css"), encoding="utf-8"
    ).read() if os.path.isfile(
        os.path.join(ROOT, "web", "static", "app.css")) else ""
    tpls = _all_templates()

    # V11-13 — 토큰 밖 색값
    # ★ 시안이 쓴 색은 「늘린 색」이 아니다 — 시안이 정본이다 (개정 275).
    #   토큰 밖이면서 시안에도 없는 것만 결함이다.  손으로 고른 색을 막는다
    sian: set = set()
    if os.path.isdir(SIAN):
        for f in os.listdir(SIAN):
            if f.endswith(".html"):
                sian |= {c.lower() for c in RE_COLOR.findall(
                    open(os.path.join(SIAN, f), encoding="utf-8").read())}
    bad = sorted({c for c in RE_COLOR.findall(RE_ROOT.sub("", css))
                  if c.lower() not in sian})
    out.append(result(C["V11-13"], rid, 0, bad or 0, not bad, bad))

    # V11-14 — 숫자 셀에 mono
    has_mono = "--mono" in css and "var(--mono)" in css
    num_mono = re.search(r"\.num[^{]*\{[^}]*var\(--mono\)", css) is not None
    ok = has_mono and num_mono
    out.append(result(C["V11-14"], rid, "mono", "mono" if ok else "없음", ok,
                      [] if ok else [".num 에 var(--mono) 가 없다"]))

    # V11-15 — 빌드 산출물 의존
    bad = [f"{f}: {w}" for f, body in tpls.items()
           for w in BUILD_ARTIFACTS if w in body]
    bad += [f"app.css: {w}" for w in BUILD_ARTIFACTS if w in css]
    out.append(result(C["V11-15"], rid, 0, bad or 0, not bad, bad))

    # V11-16 · V11-17 · V11-20 · V11-22 — /why 절
    why = tpls.get("why.html", "")
    miss = [k for k, mark in (("전 Component", "v.axes"),
                              ("조회 상태", "diagnosis"),
                              ("분모 표시", "denominator"),
                              ("excluded 표기", "excluded"))
            if mark not in why]
    out.append(result(C["V11-16"], rid, 0,
                      0 if "v.axes" in why else 1, "v.axes" in why,
                      [] if "v.axes" in why else ["axes 반복이 없다"]))
    ok17 = "diagnosis" in why and "확인 못 한 것" in why
    out.append(result(C["V11-17"], rid, "조회 상태",
                      "있음" if ok17 else "없음", ok17))
    ok20 = "denominator" in why and "earned" in why
    out.append(result(C["V11-20"], rid, "분모 표시",
                      "있음" if ok20 else "없음", ok20,
                      [] if ok20 else ["earned/denominator 를 안 낸다"]))
    ok22 = "excluded" in why and "—" in why
    out.append(result(C["V11-22"], rid, "—/N",
                      "있음" if ok22 else "없음", ok22))
    _ = miss

    # V11-18 — 축 태그가 필터 링크
    lst = tpls.get("listings.html", "") + tpls.get("recommend.html", "")
    ok18 = "filter_url" in lst or "?axis=" in lst
    out.append(result(C["V11-18"], rid, "링크",
                      "링크" if ok18 else "글자만", ok18,
                      [] if ok18 else ["축 칩이 filter_url 을 안 쓴다"]))

    # V11-19 — 폴링 실패에도 화면이 안 깨진다.
    # ★ 개정 248 — 금지된 것은 빌드 도구이지 JS 자체가 아니다.
    #   「브라우저만 할 수 있는 일」(STEP 136c)에만 열어 준다.  나머지는 그대로 금지다
    JS_ALLOWED = ("admin_collect.html",)
    ok19 = not any(("setInterval" in b or "fetch(" in b)
                   for name, b in tpls.items() if name not in JS_ALLOWED)
    out.append(result(C["V11-19"], rid, "JS 없음",
                      "JS 없음" if ok19 else "JS 있음", ok19))

    # V11-21 — 행동 파라미터가 현재 필터와 일치
    ok21 = "filter" in tpls.get("listings.html", "") or "?" in lst
    out.append(result(C["V11-21"], rid, "일치",
                      "일치" if ok21 else "없음", ok21))

    # V11-23 — ★ 실제로 눌러 본다.  「담긴다」만 보면 안 된다.
    #   실측 08-14 에 403 이 나왔는데 통과였다 (STEP 149i)
    out.append(_watch_invite_check(conn, rid))

    # V11-24 — 메뉴 분류 == 잠금 단위
    groups = {r.menu for r in ROUTES if r.menu}
    ok24 = groups <= {"운영", "조정", "탐색"}
    out.append(result(C["V11-24"], rid, "3분류", sorted(groups), ok24))

    # V11-25 · V11-26 — 사유 · 확인
    forms = {f: b for f, b in tpls.items() if "<form" in b}
    admin_forms = {f: b for f, b in forms.items() if f.startswith("admin_")}
    # ★ 폼 안에 저장 단추가 있는 것만 본다 (V11-25).
    #   본문의 「저장하지 않습니다」 같은 설명이 걸리면
    #   설명을 쓸수록 검사가 붉어진다 — V6-03 과 같은 함정이다
    bad = []
    for f, b in admin_forms.items():
        for m in re.finditer(r"<form\b.*?</form>", b, re.S):
            chunk = m.group(0)
            if "저장" not in chunk:
                continue
            if 'name="reason"' not in chunk and "previewed" not in chunk:
                bad.append(f)
                break
    out.append(result(C["V11-25"], rid, 0, bad or 0, not bad, bad))
    # ★ 폼 단위로 본다.  파일에 그 낱말이 있다고 위험한 것이 아니다
    bad = []
    for f, b in forms.items():
        for m in re.finditer(r"<form\b.*?</form>", b, re.S):
            chunk = m.group(0)
            if any(f'value="{w}"' in chunk for w in IRREVERSIBLE) \
                    and "data-confirm" not in chunk:
                bad.append(f"{f}: 확인 없이 실행된다")
    out.append(result(C["V11-26"], rid, 0, bad or 0, not bad, bad))

    # V11-27 — 가입 정책에 따라 화면이 바뀐다
    join = tpls.get("join.html", "")
    ok27 = "closed" in join and "approval" in join
    out.append(result(C["V11-27"], rid, "3정책",
                      "반영" if ok27 else "고정", ok27))

    # V11-33 — 저장 없이 성공 메시지
    # ★ AST 로 본다.  정규식으로 함수 경계를 자르면 중첩 함수에서 깨진다
    import ast

    src = open(os.path.join(ROOT, "web", "views.py"), encoding="utf-8").read()
    bad = []
    tree = ast.parse(src)
    # ★ 가장 안쪽 함수만 본다.  바깥이 안쪽 본문을 품어 오탐이 난다
    inner = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
             and not any(isinstance(c, ast.FunctionDef)
                         for c in ast.walk(n) if c is not n)]
    for node in inner:
        body = ast.get_source_segment(src, node) or ""
        if "저장했습니다" in body and not re.search(
                r"\b(conn\.execute|apply_config|set_role|set_disabled|"
                r"enqueue_recalc|change_secret|classify_field|_upd|"
                r"watch_close|create_dev_request|preview_scoring|"
                r"import_listings|save_browser_catch)\b", body):
            bad.append(f"{node.name}: 저장 없이 성공을 낸다")
    out.append(result(C["V11-33"], rid, 0, bad or 0, not bad, bad))

    # V11-35 — 중첩 if
    from web.template import render_str

    got = render_str("A{% if !c %}B{% if a %}C{% endif %}D{% endif %}E",
                     {"c": 0, "a": 0})
    ok35 = got == "ABDE"
    out.append(result(C["V11-35"], rid, "ABDE", got, ok35))

    # V11-34 — 요청당 쿼리 상한
    out.append(_query_budget_check(conn, rid))
    # 반입 3종 (13장 STEP 136a · 136b)
    out.append(_import_origin_check(conn, rid))
    out.append(_import_resume_check(conn, rid))
    out.append(_import_step4_check(conn, rid))
    out.append(_import_opened_steps_check(conn, rid))
    # 브라우저 수집 2종 (13장 STEP 136c)
    out.append(_browser_origin_check(conn, rid))
    out.append(_browser_confirm_check(conn, rid))
    out.append(_browser_chunk_check(conn, rid))
    out += _status_screen_checks(rid)
    out.append(_status_liveness_check(conn, rid))
    out += _browser_scope_checks(rid)
    # 목록 화면 6종 (개정 274 · 275)
    out.append(_menu_label_check(rid))
    out += _listing_paging_checks(conn, rid)
    out += _photo_checks(conn, rid)
    out += _sian_css_checks(rid)
    # 링크 · 툴팁 · 원문 · 고르기 · 순서 · 필터 (개정 276)
    out += _link_tip_checks(rid)
    out.append(_origin_link_check(rid))
    out.append(_choose_check(rid))
    out += _order_filter_checks(rid)
    # v1 원본 대조 (개정 277)
    out += _v1_parity_checks(rid)
    out += _responsive_checks(rid)
    out.append(_null_link_check(conn, rid))
    out.append(_sian_visual_check(conn, rid))
    out.append(_cell_squeeze_check(rid))
    out.append(_static_version_check(rid))
    out.append(_axis_state_check(conn, rid))
    out.append(_photo_size_check(rid))
    out.append(_three_values_check(conn, rid))
    out += _render_metrics_checks(conn, rid)
    out.append(_post_smoke_check(conn, rid))
    out.append(_context_supplied_check(conn, rid))
    out.append(_save_button_check(conn, rid))

    # V11-36 — 잘못된 파라미터가 400 인가
    from errors import ValidationError
    from web.views import _int_param

    bad = []
    for raw in ("abc", "-1", "0", "1e3"):
        try:
            _int_param({"page": raw}, "page", 1)
            bad.append(f"page={raw} 를 받아들인다")
        except ValidationError:
            pass
    out.append(result(C["V11-36"], rid, 0, bad or 0, not bad, bad))

    _ = (GET, FILTERS, conn)
    return out


def _query_budget_check(conn, rid):
    """★ 실제로 세어 본다.  「IN 절로 묶었다」를 글로만 두지 않는다 (F-3)."""
    import json as _j
    import sqlite3 as _sq

    from contracts import ANONYMOUS
    from report.screens.build import view_listings
    from report.screens.views import ListingFilter

    with open(os.path.join(ROOT, "config", "web.json"),
              encoding="utf-8") as f:
        cap = int(_j.load(f)["max_queries_per_request"])
    # ★ MAX 는 글자 크기다.  화면이 읽는 것과 같은 것을 읽어야 실측이 된다
    from store.core import current_versions

    ver = current_versions(conn)["calc_version"]
    if not ver:
        return not_applicable(C["V11-34"], rid, "판정 결과가 없다")

    class Counting(_sq.Connection):
        n = 0

        def execute(self, *a, **k):
            Counting.n += 1
            return super().execute(*a, **k)

    # ★ 목록 하나만 세면 다른 화면이 검사 밖이다.
    #   실측 08-15: view_listings 3회는 통과인데 dashboard 는 21회였다 (B-2)

    path = conn.execute("PRAGMA database_list").fetchall()[0][2]
    probe = _sq.connect(path, factory=Counting)
    with open(os.path.join(ROOT, "config", "finance.json"),
              encoding="utf-8") as f:
        fin = _j.load(f)
    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS
    from web.server import guard

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    acc = Account(1, ROLE_ADMIN, "마스터")
    worst, bad = 0, []
    Counting.n = 0
    view_listings(ANONYMOUS, probe, ListingFilter(calc_version=ver), fin,
                  ROOT)
    worst = Counting.n
    if worst > cap:
        bad.append(f"/listings 한 쪽에 {worst} 쿼리")

    for route in ROUTES:
        if GET not in route.methods or route.view == "serve_static":
            continue
        fn = HANDLERS.get(route.view)
        if fn is None or guard(acc, route) is not None:
            continue
        pv = {}
        if "{" in route.path and row:
            pv = {route.path.split("{")[1].split("}")[0]: str(row[0])}
        Counting.n = 0
        try:
            fn(probe, acc, {"query": {}, "form": {}, "method": GET},
               path_vars=pv, csrf="t")
        except Exception:                                    # noqa: BLE001
            continue          # V11-30 이 잡는다
        worst = max(worst, Counting.n)
        if Counting.n > cap:
            bad.append(f"{route.path} 한 쪽에 {Counting.n} 쿼리")
    return result(C["V11-34"], rid, f"<= {cap}", worst, not bad, bad[:8])


def _import_origin_check(conn, rid):
    """V11-40 — 반입분이 수집분으로 위장하지 않는가 (STEP 136a).

    ★ 「origin 을 import 로 넣었다」를 코드 주석으로 두지 않는다.  세어 본다
    """
    from contracts import IMPORT_SOURCE
    from store.raw import ORIGIN_COLLECTOR

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    batches = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE origin=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings and not batches:
        return not_applicable(C["V11-40"], rid, "반입분이 없다")
    bad = []
    if listings and not batches:
        bad.append(f"반입 매물 {listings}건인데 origin='import' 원문이 0건")
    # ★ 반입분에 URL 이 있으면 「우리가 불렀다」가 된다 (STEP 136a 금지)
    with_url = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE origin=? "
        "AND request_url IS NOT NULL", (IMPORT_SOURCE,)).fetchone()[0]
    if with_url:
        bad.append(f"반입분 {with_url}건에 request_url 이 있다")
    # 코드 — 반입 경로가 collector 를 쓰지 않는가
    src = open(os.path.join(ROOT, "store", "adminops.py"),
               encoding="utf-8").read()
    body = src.split("def import_listings", 1)[-1].split("\ndef ", 1)[0]
    if ORIGIN_COLLECTOR in body or "'collector'" in body:
        bad.append("import_listings 가 collector 를 쓴다")
    return result(C["V11-40"], rid, IMPORT_SOURCE,
                  f"매물 {listings} · 원문 {batches}", not bad, bad)


def _import_step4_check(conn, rid):
    """V11-42 — S4 완료 행의 actual 이 'import' 인가 (STEP 136b ④)."""
    from contracts import IMPORT_SOURCE, S4_CODE

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings:
        return not_applicable(C["V11-42"], rid, "반입분이 없다")
    row = conn.execute(
        "SELECT actual, passed FROM audit_validation WHERE code=? "
        "ORDER BY checked_at DESC LIMIT 1", (S4_CODE,)).fetchone()
    if row is None:
        return result(C["V11-42"], rid, IMPORT_SOURCE, "S4 완료 행이 없다",
                      False, ["반입이 STEP53-S4 를 남기지 않았다"])
    actual, passed = row
    bad = []
    if actual != IMPORT_SOURCE:
        bad.append(f"actual={actual!r} — 반입인데 반입이라고 안 적혔다")
    if not passed:
        bad.append("passed=0 — S4 가 완료로 남지 않았다")
    return result(C["V11-42"], rid, IMPORT_SOURCE, str(actual), not bad, bad)


def _browser_origin_check(conn, rid):
    """V11-43 — 브라우저가 받은 것이 서버가 받은 것으로 안 보이는가 (136c)."""
    from contracts import ORIGIN_BROWSER
    from store.raw import ORIGIN_COLLECTOR

    n = conn.execute("SELECT COUNT(*) FROM raw_response WHERE origin=?",
                     (ORIGIN_BROWSER,)).fetchone()[0]
    src = open(os.path.join(ROOT, "store", "adminops.py"),
               encoding="utf-8").read()
    body = src.split("def save_browser_catch", 1)[-1].split("\ndef ", 1)[0]
    bad = []
    if ORIGIN_COLLECTOR in body or "'collector'" in body:
        bad.append("save_browser_catch 가 collector 를 쓴다")
    if not n and not bad:
        return not_applicable(C["V11-43"], rid, "브라우저 수집분이 없다")
    return result(C["V11-43"], rid, ORIGIN_BROWSER, f"{n}건", not bad, bad)


def _browser_confirm_check(conn, rid):
    """V11-44 — 사람 확인 없이 저장되지 않는가 (136c ② · STEP 149k).

    ★ 「사람이 본다」를 글로 두지 않는다.  저장 경로가 관문을 지나는지 본다
    """
    src = open(os.path.join(ROOT, "web", "views.py"), encoding="utf-8").read()
    body = src.split("def admin_collect", 1)[-1].split("\ndef ", 1)[0]
    bad = []
    if "_gate(" not in body:
        bad.append("admin_collect 의 POST 가 _gate 를 지나지 않는다")
    if "save_browser_catch" in body and "_gate(" not in body:
        bad.append("확인 없이 저장한다")
    tpl = os.path.join(ROOT, "web", "templates", "admin_collect.html")
    if os.path.isfile(tpl):
        html = open(tpl, encoding="utf-8").read()
        # ★ previewed 를 처음부터 1 로 박아 두면 ②를 건너뛴 것이다
        if 'name="previewed" id="f_seen" value="1"' in html:
            bad.append("previewed 가 처음부터 1 이다 — ②를 건너뛴다")
    else:
        bad.append("admin_collect.html 이 없다")
    _ = conn
    return result(C["V11-44"], rid, "미리보기 필수",
                  "관문 통과" if not bad else "관문 없음", not bad, bad)


def _browser_chunk_check(conn, rid):
    """V11-47 — 한 번에 상한을 넘기지 않는가 (개정 263).

    ★ 「나눠 보낸다」를 글로 두지 않는다.  config 와 실제 저장분을 함께 본다
    """
    import json as _j

    from contracts import ORIGIN_BROWSER

    with open(os.path.join(ROOT, "config", "web.json"),
              encoding="utf-8") as f:
        web = _j.load(f)
    cap = int(web["max_form_bytes"])
    bad = []
    if "browser_collect_rows" not in web:
        bad.append("config.web.browser_collect_rows 가 없다")
    tpl = os.path.join(ROOT, "web", "templates", "admin_collect.html")
    html = open(tpl, encoding="utf-8").read() if os.path.isfile(tpl) else ""
    if "url_template" not in html or "{offset}" not in html:
        bad.append("JS 가 쪽을 이어서 부르지 않는다")
    # ★ 건수로만 나누면 바이트가 안 묶인다.  한글은 글자당 3바이트다 (실측 413)
    if "new Blob(" not in html:
        bad.append("JS 가 바이트를 재지 않는다 — 건수로만 나눈다")
    if "{rows}" not in html:
        bad.append("건수를 줄여 다시 부를 수 없다")
    if "나눠서 보내" in html and "사람" not in html:
        bad.append("사람에게 나누라고 안내한다")
    # ★ 「한 번에」는 한 POST 다.  이어붙인 원문은 여러 POST 로 왔다 (개정 307).
    #   저장된 크기로 재면 조각 전송을 넣은 것이 도리어 실패로 나온다
    if "chunk_seq" not in html or "chunk_hash" not in html:
        bad.append("큰 원문을 조각으로 안 보낸다 (개정 307)")
    row = conn.execute(
        "SELECT MAX(LENGTH(body)) FROM raw_response WHERE origin=?"
        " AND COALESCE(response_meta,'') NOT LIKE '%chunked%'",
        (ORIGIN_BROWSER,)).fetchone()
    worst = row[0] or 0
    if worst > cap:
        bad.append(f"한 번에 보낸 것이 {worst}바이트 — 상한 {cap} 초과")
    return result(C["V11-47"], rid, f"<= {cap}", worst, not bad, bad)


def _status_screen_checks(rid):
    """V11-51 · V11-52 — 진행 화면 (STEP 136f · 개정 272)."""
    import json as _j

    tpl = os.path.join(ROOT, "web", "templates", "admin_status.html")
    bad51, bad52 = [], []
    if not os.path.isfile(tpl):
        bad51.append("admin_status.html 이 없다")
        bad52.append("admin_status.html 이 없다")
        html = ""
    else:
        html = open(tpl, encoding="utf-8").read()
    with open(os.path.join(ROOT, "config", "web.json"),
              encoding="utf-8") as f:
        web = _j.load(f)
    if "status_poll_sec" not in web:
        bad51.append("config.web.status_poll_sec 가 없다")
    src = open(os.path.join(ROOT, "web", "views.py"),
               encoding="utf-8").read()
    body = src.split("def admin_status", 1)[-1].split("\ndef ", 1)[0]
    if "refresh_sec" not in body:
        bad51.append("화면이 갱신 간격을 넘기지 않는다")
    if "마지막 확인" not in html:
        bad51.append("마지막 갱신 시각을 안 낸다")
    # ★ 지켜보는 화면에 실행 단추가 있으면 안 된다
    if "<form" in html or "type=\"submit\"" in html:
        bad52.append("진행 화면에 폼·단추가 있다")
    from web.routes import ROUTES

    for r in ROUTES:
        if r.path == "/admin/status" and "POST" in r.methods:
            bad52.append("/admin/status 가 POST 를 받는다")
    return [result(C["V11-51"], rid, "갱신",
                   "갱신" if not bad51 else "없음", not bad51, bad51),
            result(C["V11-52"], rid, "읽기 전용",
                   "읽기 전용" if not bad52 else "단추 있음", not bad52, bad52)]


def _status_liveness_check(conn, rid):
    """V11-53 — 진행 판정이 큐만 보는가 (개정 273).

    ★ 코드가 셋을 보는지, 그리고 지금 화면이 스스로 모순되지 않는지 함께 본다
    """
    from report.screens.admin import status_view

    src = open(os.path.join(ROOT, "report", "screens", "admin.py"),
               encoding="utf-8").read()
    body = src.split("def _live_progress", 1)[-1].split("\ndef ", 1)[0]
    bad = []
    if "audit_request" not in body:
        bad.append("최근 요청을 안 본다 — 큐만 본다")
    if "requested_at" not in body:
        bad.append("마지막 처리 시각을 안 본다")
    view = status_view(conn, ROOT)
    # ★ 「도는 것이 없다」와 「방금 처리했다」가 같이 나오면 모순이다
    last = view.get("last_item") or {}
    if view.get("idle") and last.get("minutes") == 0:
        bad.append("「할 일 없음」인데 마지막 처리가 0분 전이다")
    return result(C["V11-53"], rid, "실측 기준",
                  "도는 중" if view.get("live_running") else "조용함",
                  not bad, bad)


# 이 말 뒤의 숫자는 식별자다.  단위가 없는 것이 맞다 (V11-74)
ID_WORDS = ("매물", "계정", "run", "job", "id", "번호", "코드", "키")
# ★ 원값을 그대로 고치는 화면이다.  단위를 붙이면 「100만」을 저장하게 된다.
#   보는 화면이 아니라 고치는 화면이라 이 검사에서 뺀다 (V11-74)
RAW_VALUE_SCREENS = ("/admin/config", "/admin/query", "/admin/api")
# 단위 환산 (2장 상수표 · V4-13)
BYTES_PER_KB = 1_024
MENU_TABLE = os.path.join(ROOT, "docs", "chapters", "60-admin", "c-tools.md")
LISTINGS_TPL = os.path.join(TEMPLATES, "listings.html")
APP_CSS = os.path.join(ROOT, "web", "static", "app.css")
SIAN = os.path.join(ROOT, "ref", "screens")


def _menu_label_check(rid):
    """V11-54 — 메뉴에 경로가 그대로 나오는가 (개정 274).

    ★ 13장 STEP 138 메뉴표와 대조한다.  표에 있는데 이름이 없으면 결함이다
    """
    from web.app import LABELS

    bad = [p for p in LABELS.values() if p.startswith("/")]
    if os.path.isfile(MENU_TABLE):
        doc = open(MENU_TABLE, encoding="utf-8").read()
        for path in re.findall(r"\|\s*`(/admin[a-z/]*)`\s*\|", doc):
            if path not in LABELS:
                bad.append(f"{path} — 메뉴표에 있는데 이름이 없다")
    return result(C["V11-54"], rid, "이름", "이름" if not bad else "경로",
                  not bad, bad)


def _listing_paging_checks(conn, rid):
    """V11-55 · V11-58 — 전체 건수 · 쪽 · 쪽을 넘겨도 남는 조건.

    ★ 실제로 화면을 만들어 본다.  「구현했다」가 아니라 나온 글자를 본다
    """
    from report.screens.views import ListingFilter
    from store.core import current_versions
    from web.views import _paging

    ver = current_versions(conn)
    html = open(LISTINGS_TPL, encoding="utf-8").read()
    bad55 = []
    for want in ("paging.total", "paging.page", "paging.pages"):
        if want not in html:
            bad55.append(f"{want} 를 안 낸다")
    flt = ListingFilter(site="encar", calc_version=ver["calc_version"])
    pg = _paging(conn, flt, 0, ROOT)
    if pg["total"] and pg["pages"] < 1:
        bad55.append("쪽 수가 0 이다")

    # V11-58 — 조건을 걸고 쪽 링크에 그 조건이 남는가
    bad58 = []
    got = _paging(conn, ListingFilter(site="encar", grade="B",
                                      calc_version=ver["calc_version"]),
                  0, ROOT)
    for link in [got["next"], got["last"]] + [x["url"] for x in got["links"]]:
        if link and "grade=B" not in link:
            bad58.append(f"쪽 링크에 조건이 없다 — {link}")
            break
    return [result(C["V11-55"], rid, "건수 · 쪽",
                   f"{pg['total']}건 {pg['pages']}쪽" if not bad55 else "없음",
                   not bad55, bad55),
            result(C["V11-58"], rid, "조건 유지",
                   "유지" if not bad58 else "풀림", not bad58, bad58)]


def _photo_checks(conn, rid):
    """V11-56 · V11-57 — 대표 사진 (개정 274)."""
    from report.screens.build import photo_url

    bad56 = []
    n = conn.execute("SELECT COUNT(*) FROM core_listing WHERE status='active'"
                     ).fetchone()[0]
    got = conn.execute("SELECT COUNT(*) FROM core_listing"
                       " WHERE status='active' AND photo_list_json IS NOT NULL"
                       ).fetchone()[0]
    if n and not got:
        bad56.append("펼쳐 앉은 매물에 사진 원문이 하나도 없다")
    row = conn.execute("SELECT photo_list_json FROM core_listing"
                       " WHERE photo_list_json IS NOT NULL LIMIT 1").fetchone()
    if row and not photo_url(row[0], "https://ci.encar.com"):
        bad56.append("원문이 있는데 대표 사진을 못 고른다")

    # ★ 사진이 없어도 행이 살아 있는가 — 깨진 원문 4종을 실제로 넣어 본다
    bad57 = []
    for broken in (None, "", "[]", '[{"ordering":1.0}]', "{not json"):
        try:
            if photo_url(broken, "https://ci.encar.com") is not None:
                bad57.append(f"없는 사진에 주소를 만든다 — {broken!r}")
        except Exception as e:                       # noqa: BLE001
            bad57.append(f"사진이 없으면 터진다 — {broken!r} {e}")
    html = open(LISTINGS_TPL, encoding="utf-8").read()
    if "thumb-none" not in html:
        bad57.append("사진이 없을 때 자리를 안 채운다")
    if 'loading="lazy"' not in html:
        bad57.append("loading=\"lazy\" 가 없다 — 200행에 200장을 한 번에 받는다")
    return [result(C["V11-56"], rid, "사진 원문", f"{got}/{n}건",
                   not bad56, bad56),
            result(C["V11-57"], rid, "없어도 뜸",
                   "뜸" if not bad57 else "무너짐", not bad57, bad57)]


def _sian_css_checks(rid):
    """V11-59 · V11-60 — 시안 CSS 를 그대로 옮겼는가 (개정 275).

    ★ 화면이 쓰는 이름이 CSS 에 있는가 · 시안의 값과 같은가
    """
    css = open(APP_CSS, encoding="utf-8").read() if os.path.isfile(APP_CSS) else ""
    have = set(re.findall(r"\.([a-zA-Z][\w-]*)", css))
    used: set = set()
    for name in os.listdir(TEMPLATES):
        if not name.endswith(".html"):
            continue
        html = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        # ★ JS 가 만드는 class 문자열은 세지 않는다 — 따옴표 안이 코드다
        html = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
        for attr in re.findall(r'class="([^"{}]*)"', html):
            # ★ js- 는 JS 가 잡는 손잡이다.  꾸미지 않는다
            used |= {c for c in attr.split() if c and not c.startswith("js-")}
    bad59 = sorted(used - have)

    # V11-60 — 시안의 값과 우리 CSS 의 값이 같은가 (겹치는 이름 표본)
    bad60 = []
    if not os.path.isdir(SIAN):
        bad60.append("시안이 없다 — ref/screens/")
    else:
        for f in sorted(os.listdir(SIAN)):
            if not f.endswith(".html"):
                continue
            src = open(os.path.join(SIAN, f), encoding="utf-8").read()
            for sel, body in re.findall(r"\n(\.[\w-]+)\{([^{}]*)\}", src):
                want = re.sub(r"\s+", "", body)
                for got in re.findall(re.escape(sel) + r" \{ ([^{}]*)\}", css):
                    if re.sub(r"\s+", "", got) == want:
                        break
                else:
                    if sel[1:] in have:      # 이름은 있는데 값이 다르다
                        bad60.append(f"{f} {sel} 값이 시안과 다르다")
    # ★ 이름을 우리가 따로 쓰는 것(.mini 등)은 화면별로 가둬 뒀다 — 표본만 본다
    bad60 = bad60[:5]
    return [result(C["V11-59"], rid, "쓰는 이름",
                   f"{len(used)}종" if not bad59 else f"{len(bad59)}종 없음",
                   not bad59, bad59),
            result(C["V11-60"], rid, "시안과 같음",
                   "같음" if not bad60 else "다름", not bad60, bad60)]


V1_UI = os.path.join(ROOT, "ref", "v1-ui", "web", "templates")

# 이어질 수 있는 값 — 링크가 되어야 하는 것 (STEP 149p · 실측 08-16).
# ★ 「값을 누르면 그 조건으로」가 이 도구의 설계다 (STEP 149g)
LINKED_FIELDS = {
    "r.dealer_shop": "딜러 — 그 딜러 매물로",
    "r.year_month": "연식 — 그 연식으로",
    "r.mileage_km": "주행 — 구간으로",
    "r.price_won": "가격 — 가격대로",
    "r.monthly_won": "월납입 — 예산대로",
    "r.status_label": "상태 — 게시중만",
}
# 툴팁이 필요한 것 — 사람이 「이게 뭔가」를 물어볼 것 (STEP 149p)
TIPPED = ("r.grade", "r.ratio_pct", "r.denominator", "c.mark", "r.monthly_won")
ENCAR_DETAIL = "encar.com/dc/dc_cardetailview.do"


def _cell_of(html: str, expr: str) -> str:
    """그 값을 낸 <td> 한 칸을 통째로 잘라 온다.  ★ 링크·title 이
    그 칸 안에 있는지를 봐야 한다 — 화면 어딘가에 있는 것으로는 안 된다."""
    i = html.find("{{ " + expr)
    if i < 0:
        i = html.find(expr)
    if i < 0:
        return ""
    a = html.rfind("<td", 0, i)
    b = html.find("</td>", i)
    return html[a:b] if a >= 0 and b > a else ""


def _link_tip_checks(rid):
    """V11-61 · V11-62 — 링크와 툴팁 (STEP 149p · 개정 276)."""
    html = open(LISTINGS_TPL, encoding="utf-8").read()
    bad61 = [f"{e} — {why}" for e, why in LINKED_FIELDS.items()
             if "<a " not in _cell_of(html, e)]
    bad62 = [e for e in TIPPED if 'title="' not in _cell_of(html, e)]
    return [result(C["V11-61"], rid, "링크",
                   f"{len(LINKED_FIELDS) - len(bad61)}/{len(LINKED_FIELDS)}",
                   not bad61, bad61),
            result(C["V11-62"], rid, "툴팁",
                   f"{len(TIPPED) - len(bad62)}/{len(TIPPED)}",
                   not bad62, bad62)]


def _origin_link_check(rid):
    """V11-63 — 엔카 원문 링크 (STEP 149q).

    ★ 주소는 config 에 있고 화면은 encar_url 만 쓴다.
      글자를 찾지 말고 「주소가 규격대로 만들어지는가」를 본다
    """
    import json as _j

    bad = []
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        tpl = str(_j.load(f).get("encar_detail_url", ""))
    if ENCAR_DETAIL not in tpl:
        bad.append(f"config 의 주소가 규격과 다르다 — {tpl or '없음'}")
    if "{source_id}" not in tpl:
        bad.append("주소에 source_id 자리가 없다")
    for name in ("why.html", "listings.html"):
        html = open(os.path.join(TEMPLATES, name), encoding="utf-8").read()
        if "encar_url" not in html:
            bad.append(f"{name} 에 원문 링크가 없다")
            continue
        if 'target="_blank"' not in html or 'rel="noopener"' not in html:
            bad.append(f"{name} 새 탭으로 안 연다")
        if "엔카에서 보기" not in html:
            bad.append(f"{name} 「엔카에서 보기」라고 안 적었다")
    return result(C["V11-63"], rid, "원문 링크",
                  "있음" if not bad else "없음", not bad, bad)


def _choose_check(rid):
    """V11-64 — 고르는 칸은 고르게 (STEP 149r).

    ★ 차종 추가에서 target_key 를 손으로 치게 두지 않는다
    """
    path = os.path.join(TEMPLATES, "admin_targets.html")
    html = open(path, encoding="utf-8").read() if os.path.isfile(path) else ""
    bad = []
    if "<select" not in html:
        bad.append("고를 목록이 하나도 없다 — 전부 자유 입력이다")
    if "target_key" in html and "<select" not in html:
        bad.append("차종 키를 사람이 외워 치게 한다")
    return result(C["V11-64"], rid, "목록 제공",
                  f"select {html.count('<select')}개", not bad, bad)


def _order_filter_checks(rid):
    """V11-65 · V11-66 · V11-67 — 기본 순서 · 필터 위치 · 켜짐꺼짐."""
    from report.screens.build import ORDER_HEAD, ORDER_TAIL

    html = open(LISTINGS_TPL, encoding="utf-8").read()
    bad65 = []
    if "E','NOT_RATED'" not in ORDER_HEAD.replace('"', "'"):
        bad65.append("E · NOT_RATED 를 뒤로 보내지 않는다")
    if "earned" not in ORDER_TAIL:
        bad65.append("비율 높은 순이 아니다")
    from web.views import FILTER_BUTTONS

    if not any(f == "min_grade" and v == "A" for f, v, _lb, _t in FILTER_BUTTONS):
        bad65.append("「A 이상만」 단추가 없다")
    if "기본" not in html:
        bad65.append("기본으로 무엇이 걸렸는지 안 적는다")

    # V11-66 — 필터가 표보다 위에 있는가.  ★ 줄 번호로 본다
    bad66 = []
    i_bar = min([x for x in (html.find('class="bar"'), html.find('class="chips"'))
                 if x >= 0] or [-1])
    i_tab = html.find("<table")
    if i_bar < 0:
        bad66.append("필터 줄이 없다")
    elif i_tab >= 0 and i_bar > i_tab:
        bad66.append("필터가 표 아래에 있다")

    # V11-67 — 누르면 켜지고 다시 누르면 꺼지는가
    bad67 = []
    if 'class="btn' not in html:
        bad67.append("조건 단추가 없다")
    if "btn on" not in html and 'on"' not in html:
        bad67.append("켜진 단추를 구분하지 않는다")
    if ".btn.on" not in open(APP_CSS, encoding="utf-8").read():
        bad67.append("켜진 단추가 amber 로 안 보인다")
    return [result(C["V11-65"], rid, "기본 순서",
                   "규격대로" if not bad65 else "모자람", not bad65, bad65),
            result(C["V11-66"], rid, "필터 위치",
                   "위" if not bad66 else "아래", not bad66, bad66),
            result(C["V11-67"], rid, "켜짐·꺼짐",
                   "오감" if not bad67 else "없음", not bad67, bad67)]


def _checks_cfg() -> dict:
    """검사 임계값은 config 에 둔다 (V4-13 · V4-17)."""
    import json

    with open(os.path.join(ROOT, "config", "checks.json"),
              encoding="utf-8") as f:
        return json.load(f)


def _photo_size_by_screen_check(rid):
    """V11-107 — 화면별 사진 크기가 부록 G 와 같은가 (개정 332).

    ★ 부록 G 0절의 표에서 읽는다.  코드에 두 벌 두지 않는다
    """
    # ★ 정본 위치는 config/checks.json 이 안다 (개정 342).
    #   경로를 박아 두면 문서가 옮겨진 날 검사가 조용히 미실행이 된다
    text = canon_text("화면")
    if not text:
        return not_applicable(C["V11-107"], rid, "화면 정본을 못 찾았다")
    css = open(APP_CSS, encoding="utf-8").read()
    bad = []
    # 표의 「목록 | 96×72 | 88×66 | 80×60」 꼴을 읽는다
    for line in text.splitlines():
        got = re.match(r"\| *(목록|추천) *\|((?: *\d+×\d+ *\|)+)", line)
        if not got:
            continue
        for size in re.findall(r"(\d+)×(\d+)", got.group(2)):
            w, h = size
            if f"width:{w}px" not in css.replace(" ", ""):
                bad.append(f"{got.group(1)} {w}×{h} 가 CSS 에 없다")
    return result(C["V11-107"], rid, 0, len(bad), not bad, bad[:6])


def _template_leak_check(rid):
    """V11-104 — 템플릿 문법이 화면에 그대로 나오는가.

    ★ 엔진이 모르는 문법은 조용히 글자로 나온다.
      {# 주석 #} 과 {% if a == b %} 이 마스터 화면에 찍혀 있었다
    ★ 렌더 결과를 본다 — 템플릿만 보면 「엔진이 아는가」를 못 본다
    """
    base = os.path.join(ROOT, "outputs", "render")
    if not os.path.isdir(base):
        return not_applicable(C["V11-104"], rid, "렌더 결과가 없다")
    bad = []
    for name in sorted(os.listdir(base)):
        if not name.endswith(".html"):
            continue
        html = open(os.path.join(base, name), encoding="utf-8").read()
        got = re.search(r"\{[%{#][^}]{0,60}", html)
        if got:
            bad.append(f"{name} — {got.group(0)[:40]}")
    return result(C["V11-104"], rid, 0, len(bad), not bad, bad[:6])


# 값 칸 — 여기 줄표가 있으면 마스터가 못 읽는다 (부록 G · G-4)
RE_VALUE_CELL = re.compile(r"<(td|dd)\b[^>]*>(.*?)</\1>", re.S)
DASHES = ("\u2014", "\u2013")


def _em_dash_check(rid):
    """V11-106 — 값 자리에 「—」가 나오지 않는가 (부록 G · G-4).

    ★ 검사가 없으니 계속 늘어났다 — 21곳 → 41곳 (가이드 08-17).
    ★ 셀 전체가 줄표인 것만 잡는다.  문장 속 줄표는 글이지 값이 아니다
      («받은 원문은 origin='browser' 로 남습니다 — …»)
    ★ 렌더 결과를 본다.  템플릿만 보면 필터가 만드는 줄표를 못 본다
    """
    base = os.path.join(ROOT, "outputs", "render")
    if not os.path.isdir(base):
        return not_applicable(C["V11-106"], rid, "렌더 결과가 없다")
    bad = []
    for name in sorted(os.listdir(base)):
        if not name.endswith(".html"):
            continue
        html = open(os.path.join(base, name), encoding="utf-8").read()
        for got in RE_VALUE_CELL.finditer(html):
            text = re.sub(r"<[^>]+>", "", got.group(2)).strip()
            if text in DASHES:
                bad.append(f"{name} — {got.group(0)[:60]}")
    return result(C["V11-106"], rid, 0, len(bad), not bad, bad[:6])


# 화면 : (템플릿, 부록 G 줄 수 상한 표의 줄 이름).
# ★ 줄 수를 여기 적지 않는다 — 부록 G 「줄 수 상한」 표에서 읽는다
CARD_SHAPES = {
    "car-rows": (os.path.join(ROOT, "web", "templates", "listings.html"),
                 "목록 (좁음)"),
    "cand-rows": (os.path.join(ROOT, "web", "templates", "recommend.html"),
                  "추천 (좁음)"),
}
CARD_AXES = ("사고", "골격", "용도", "보증")
# 부록 G 「한 화면에 매물이 2개 이상 보인다」 — 그 「2개」다
CARDS_PER_SCREEN = 2


def _card_limits() -> dict:
    """부록 G 「줄 수 상한」 표.  ★ 6줄·8줄을 코드에 적지 않는다."""
    body = canon_text("화면")
    if not body:
        return {}
    head = body.find("## 줄 수 상한")
    if head < 0:
        return {}
    block = body[head:body.find("\n#", head + 1)]
    out = {}
    for line in block.splitlines():
        got = re.match(r"\| *([^|]+?) *\| *\*{0,2}(\d+)줄", line)
        if got:
            out[got.group(1)] = int(got.group(2))
    return out


def _cells_of(tpl: str, axes: int) -> list:
    """템플릿의 칸을 나오는 차례대로 낸다.  반환 [(클래스집합, 이름표)].

    ★ 축 칸은 반복문 하나로 적혀 있다 — 실제로 나오는 수만큼 편다.
      이걸 안 하면 5줄이 축 하나로 세어져 겹침을 못 본다 (실측 08-18)
    """
    from report.screens.build import axis_heads

    body = re.sub(r"<script>.*?</script>", "", tpl, flags=re.S)
    # ★ 첫 <tbody> 하나만 본다.  아래쪽 「후보에서 뺀 것」 표까지 세면
    #   빈 칸 넷이 더 세어져 카드가 12줄로 잡힌다 (실측 08-18)
    body = body[body.find("<tbody>"):body.find("</tbody>")]
    labels = [h["label"] for h in axis_heads(ROOT)][:axes]
    out = []
    for got in re.finditer(r"<td([^>]*)>", body):
        attrs = got.group(1)
        cls = set(re.findall(r'class="([^"]*)"', attrs)[0].split()) \
            if 'class="' in attrs else set()
        name = re.findall(r'data-label="([^"]*)"', attrs)
        label = name[0] if name else ""
        if "{{" in label:                       # 축 — 이름이 반복문 변수다
            for one in labels:
                out.append((cls, one))
            continue
        out.append((cls, label))
    return out


def _matches(sel: str, klass: str, cls: set, label: str) -> int:
    """선택자가 이 칸에 걸리는가.  걸리면 좁기(특정도)를 낸다 · 아니면 -1."""
    sel = sel.strip()
    if not sel.startswith(f".{klass}"):
        return -1
    rest = sel[len(klass) + 1:]
    score = 1
    for want in re.findall(r'\[data-label="([^"]*)"\]', rest):
        if want != label:
            return -1
        score += 1
    rest = re.sub(r'\[data-label="[^"]*"\]', "", rest)
    for want in re.findall(r"\.([a-zA-Z][\w-]*)", rest):
        if want not in cls:
            return -1
        score += 1
    return score


def _place_cards(css: str, tpl: str, klass: str, narrow_px: int,
                 card_px: int):
    """칸을 격자에 실제로 놓아 본다.

    반환   (놓인 칸, 격자 칸 수, 가장 큰 글자 크기, 넘친 것)
    ★ CSS 를 눈으로 읽어서는 겹침이 안 보인다 — 놓아 보고 센다
    """
    # ★ 주석을 먼저 뗀다.  주석 안의 중괄호·쉼표가 규칙 쪼개기를 깨뜨린다
    #   (실측 08-18 — 주석에 적은 예시 하나로 축 규칙 넷이 통째로 사라졌다)
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)
    # ★ 어림값을 두지 않는다.  CSS 에 없으면 그것이 결함이다 —
    #   기본값을 두면 「격자를 안 정했다」가 조용히 통과한다
    rules, cols, biggest, base = [], 0, 0.0, 0.0
    for width, body in _media_blocks(css):
        # ★ 그 폭에서 실제로 도는 블록만 본다.  min-width 를 안 보면
        #   중간 폭 규칙이 좁은 폭 검사에 섞인다 (실측 08-18)
        low = _media_blocks.low.get(body, 0)
        if width < narrow_px or low > narrow_px:
            continue
        if width > card_px and low == 0:
            continue
        # ★ 행(tr)의 격자만 읽는다.  블록 아무 데서나 repeat( 를 주우면
        #   .tiles 같은 다른 격자를 읽는다 — 실측 08-18: cols 가 2 로 잡혀
        #   「칸이 안 들어간다」가 무더기로 났다
        for one in re.finditer(r"([^{}]*\btr\b[^{}]*)\{([^{}]*)\}", body):
            hit = re.search(r"grid-template-columns:\s*repeat\((\d+)",
                            one.group(2))
            if hit:
                cols = int(hit.group(1))
            # 행이 정한 글자 크기 — 칸에 따로 안 적힌 것은 이것을 물려받는다
            hit = re.search(r"font-size:\s*([\d.]+)px", one.group(2))
            if hit:
                base = float(hit.group(1))
        if width > narrow_px:
            continue
        for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", body):
            sel = rule.group(1)
            decl = rule.group(2).replace(" ", "")
            for one in sel.split(","):
                rules.append((one, decl))
    cells = _cells_of(tpl, len(CARD_AXES))
    placed, spill = {}, []
    # 칸마다 글자 크기 — 「한 칸 폭 ÷ 글자 폭」을 재려면 칸별로 있어야 한다
    fonts: dict = {}
    hidden, area, rowspan, flow = set(), {}, {}, {}
    for idx, (cls, label) in enumerate(cells):
        best = {}
        for one, decl in rules:
            score = _matches(one, klass, cls, label)
            if score < 0:
                continue
            size = re.search(r"font-size:([\d.]+)px", decl)
            if size:
                biggest = max(biggest, float(size.group(1)))
                cur = fonts.get(idx)
                if cur is None or score >= cur[0]:
                    fonts[idx] = (score, float(size.group(1)))
            if "display:none" in decl:
                best[("hide", score)] = True
            got = re.search(r"grid-area:(\d+)/(\d+)/(\d+)/(\d+)", decl)
            if got:
                best[("area", score)] = tuple(int(x) for x in got.groups())
            row = re.search(r"grid-row:(\d+);", decl)
            span = re.search(r"grid-column:span(\d+)", decl)
            if row:
                best[("row", score)] = int(row.group(1))
            if span:
                best[("span", score)] = int(span.group(1))
        def pick(kind):
            got = [(sc, v) for (k, sc), v in best.items() if k == kind]
            return max(got)[1] if got else None
        if pick("hide"):
            hidden.add(idx)
            continue
        if pick("area"):
            area[idx] = pick("area")
        elif pick("row"):
            rowspan[idx] = (pick("row"), pick("span") or 1)
        else:
            flow[idx] = pick("span") or 1
    grid: dict = {}
    for idx, (r1, c1, r2, c2) in area.items():
        # ★ grid-area 는 줄 번호다.  끝이 시작보다 크지 않으면 폭이 0 이라
        #   브라우저가 칸을 하나 더 만든다 — 그 칸이 nowrap 폭을 먹어
        #   나머지가 쥐어짜인다 (실측 08-18: act 1/13/3/13)
        if c2 <= c1 or r2 <= r1:
            spill.append(f"{r1}줄 — grid-area {r1}/{c1}/{r2}/{c2} 의 폭이 0 이다")
            continue
        if cols and c2 > cols + 1:
            spill.append(f"{r1}줄 — grid-area 가 {c2 - 1}칸까지 간다 "
                         f"(격자는 {cols}칸)")
            continue
        for r in range(r1, r2):
            for c in range(c1, c2):
                if grid.get((r, c)) is not None:
                    spill.append(f"{r}줄 {c}칸 겹침")
                grid[(r, c)] = idx
        placed[idx] = (r1, r2)
    for idx, (row, span) in sorted(rowspan.items()):
        for c in range(1, cols - span + 2):
            if all(grid.get((row, c + k)) is None for k in range(span)):
                for k in range(span):
                    grid[(row, c + k)] = idx
                placed[idx] = (row, row + 1)
                break
        else:
            spill.append(f"{row}줄 — 칸 {span} 개가 안 들어간다 (남은 자리 없음)")
    used = max((r for r, _c in grid), default=0)
    for idx, span in sorted(flow.items()):
        used += 1
        placed[idx] = (used, used + 1)
    span = {i: (a[3] - a[1]) for i, a in area.items()}
    span.update({i: v[1] for i, v in rowspan.items()})
    span.update(dict(flow.items()))
    got = {i: v[1] for i, v in fonts.items()}
    # ★ 칸에 글자 크기가 안 적혔으면 행이 정한 것을 쓴다.
    #   가장 큰 것(가격 15px)을 물려주면 「관심」이 3.0자로 잘못 잡힌다
    for i in placed:
        got.setdefault(i, base or biggest)
    return (placed, cols, biggest, spill, hidden, len(cells), got, span)


def _card_shape_checks(rid):
    """V11-108 · V11-109 — 부록 G 줄 수 상한과 칸 겹침.

    ★ 「6줄로 묶었습니다」를 믿지 않는다.  템플릿의 칸을 하나하나
      격자에 놓아 보고 줄 번호를 센다.
    ★ 실측 08-18 — .rows td.ax[data-label="용도"] 하나가 span 6 이라
      5줄이 15칸이 되어 격자가 통째로 어긋났다.  스크린샷만 보고는
      「배치가 잘못됐다」로 여섯 번 헛짚었다.
      ★ 축은 반복문 하나로 적혀 있어 CSS 만 세면 한 칸으로 세어진다 —
        그래서 템플릿에서 실제 칸 수를 편다
    """
    import json as _j

    css = open(APP_CSS, encoding="utf-8").read()
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        # ★ 1099 가 아니라 639 다.  1099 는 표가 카드로 바뀌는 폭이고
        #   줄 수 상한은 부록 G 「좁음 (<640)」에서 잰다
        web = _j.load(f)
    narrow = int(web["card_narrow_max_px"])
    screen_px = float(web["card_screen_px"])
    line_factor = float(web["card_line_factor"])
    pad_px = float(web["card_pad_px"])
    limits = _card_limits()
    if not limits:
        return [not_applicable(C["V11-108"], rid, "부록 G 줄 수 상한을 못 읽었다"),
                not_applicable(C["V11-109"], rid, "부록 G 줄 수 상한을 못 읽었다")]
    bad109, bad108 = [], []
    # ★ 좁음만 보지 않는다.  중간 폭이 깨져 있었는데 검사가 안 봤다
    #   (실측 08-18 — 마스터 화면 약 1200px 에서 글자가 세로로 떨어졌다)
    wide_min = int(web["list_wide_min_px"])
    tiers = ((narrow, "좁음"), (wide_min - 1, "중간"))
    for klass, (tpl_path, row_name) in CARD_SHAPES.items():
        tpl = open(tpl_path, encoding="utf-8").read()
        for at, tier in tiers:
            key = row_name.replace("좁음", tier)
            limit = limits.get(key)
            if limit is None:
                continue                  # 부록 G 에 그 폭의 상한이 없다
            got = _place_cards(css, tpl, klass, at, wide_min - 1)
            placed, cols, biggest, spill, hidden, total, _f, _sp = got
            if not placed:
                bad109.append(f"{klass} {tier} — 카드 배치를 못 찾았다")
                continue
            if not cols:
                bad109.append(f"{klass} {tier} — grid-template-columns 가 없다")
                continue
            used = max(r2 - 1 for _r1, r2 in placed.values())
            if used > limit:
                bad109.append(f"{klass} {tier} {used}줄 — 부록 G 상한 {limit}줄")
            bad109 += [f"{klass} {tier} {x}" for x in spill[:3]]
            if len(placed) + len(hidden) != total:
                bad109.append(f"{klass} {tier} 칸 {total}개 중 "
                              f"{total - len(placed) - len(hidden)}개를 못 놓았다")
            if tier != "좁음":
                continue
            tall = used * biggest * line_factor + pad_px
            if tall * CARDS_PER_SCREEN > screen_px:
                bad108.append(f"{klass} 한 장 약 {tall:.0f}px — "
                              f"{CARDS_PER_SCREEN}장이 {screen_px:.0f}px 를 넘는다")
    return [result(C["V11-108"], rid, f"{CARDS_PER_SCREEN}장",
                   "들어간다" if not bad108 else "안 들어간다",
                   not bad108, bad108),
            result(C["V11-109"], rid, "상한 안", "넘음" if bad109 else "안 넘음",
                   not bad109, bad109[:8])]


# 부록 G 절 이름 ↔ 화면 제목.  ★ 순서는 부록 G 가 정한다 — 여기는 이름표뿐
WHY_SECTION_WORDS = {
    "머리말": ("판정 근거",),
    "값": ("감가 곡선", "값"),
    "왜 싼가": ("왜 싼가", "왜 비싼가"),
    "무엇을 조회했는가": ("무엇을 조회했는가",),
    "축별 판정": ("축별 판정",),
    "마이너스": ("마이너스",),
    "확인 못 한 것": ("확인 못 한 것",),
    "옵션": ("옵션",),
    "비용": ("비용",),
    "참고 자료": ("참고 자료",),
}
WHY_RENDER = "why_listing_id.html"


def _why_order_spec() -> list:
    """부록 G 3장 「절 순서」를 읽는다.  ★ 순서를 코드에 박지 않는다."""
    body = canon_text("화면")
    if not body:
        return []
    head = body.find("## 절 순서")
    if head < 0:
        return []
    block = body[head:body.find("```", body.find("```", head) + 3)]
    # ★ 「값 — ★ 가장 크게」처럼 뒤에 설명이 붙는다.  이름만 뗀다
    out = []
    for got in re.finditer(r"^[①-⑩]\s*(.+)$", block, re.M):
        name = re.split(r"\s+[—(]|\s*/\s*", got.group(1).strip())[0]
        out.append(name.strip())
    return out


def _why_order_check(rid):
    """V11-110 — 상세 절 순서가 부록 G 와 같은가.

    ★ 순서가 판단 순서다.  값을 먼저 보고 근거를 나중에 본다.
    ★ 렌더 결과의 제목을 차례대로 읽는다 — 템플릿 순서가 아니라
      실제로 나온 순서다 (절이 조건부로 빠질 수 있다)
    """
    want = _why_order_spec()
    path = os.path.join(ROOT, "outputs", "render", WHY_RENDER)
    if not want:
        return not_applicable(C["V11-110"], rid, "부록 G 에서 절 순서를 못 읽었다")
    if not os.path.isfile(path):
        return not_applicable(C["V11-110"], rid, "렌더 결과가 없다")
    html = open(path, encoding="utf-8").read()
    heads = [re.sub(r"<[^>]+>", "", x.group(1)).strip()
             for x in re.finditer(r"<h[12][^>]*>(.*?)</h[12]>", html, re.S)]
    # 부록 G 의 절이 화면 어디에 나왔는가
    at = []
    for name in want:
        words = WHY_SECTION_WORDS.get(name, (name,))
        found = [i for i, h in enumerate(heads)
                 if any(w in h for w in words)]
        at.append((name, found[0] if found else None))
    bad = [f"{n} 절이 없다" for n, i in at if i is None]
    seen = [(n, i) for n, i in at if i is not None]
    for (n1, i1), (n2, i2) in zip(seen, seen[1:], strict=False):
        if i1 > i2:
            bad.append(f"{n1} 이 {n2} 보다 뒤에 있다 "
                       f"— 부록 G 는 {n1} → {n2} 다")
    return result(C["V11-110"], rid, "부록 G 순서",
                  "같다" if not bad else "다르다", not bad, bad[:6])




def _width_policy() -> dict:
    import json as _j

    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        return _j.load(f)


def _width_checks(rid):
    """V11-113 · V11-114 · V11-115 — 폭 다섯 곳 (개정 337).

    ★ 「찍기만 하고 아무도 안 본다」를 없앤다.  찍힌 파일이 있는지 세고,
      CSS 경계가 정책과 같은지 보고, 폭마다 한 칸이 몇 자인지 잰다
    ★ 세로로 떨어지는 것은 눈으로만 보였다.  숫자로 본다 —
      한 칸 폭 ÷ 글자 폭 < 3 이면 실패
    """
    import json as _j

    web = _width_policy()
    # 한 칸이 이보다 좁으면 글자가 세로로 떨어진다 (개정 337 · V11-115)
    chars_min = float(web["cell_chars_min"])
    row_pad = float(web["row_pad_px"])
    gap = float(web["grid_gap_px"])
    widths = list(web.get("shot_widths") or ())
    card_max = int(web["list_card_max_px"])
    wide_min = int(web["list_wide_min_px"])
    css = re.sub(r"/\*.*?\*/", " ", open(APP_CSS, encoding="utf-8").read(),
                 flags=re.S)

    # V11-113 — 다섯 폭이 실제로 찍혔는가
    bad113 = []
    if not widths:
        bad113.append("config/web.json 에 shot_widths 가 없다")
    for one in widths:
        if not os.path.isfile(os.path.join(ROOT, "outputs", "shot",
                                           f"listings_{one}.png")):
            bad113.append(f"{one}px 스크린샷이 없다 — listings_{one}.png")

    # V11-114 — CSS 경계가 정책과 같은가
    bad114 = []
    for want, why in ((card_max, "좁음↔중간"), (wide_min, "중간↔넓음")):
        if f"max-width:{want}px" not in css.replace(" ", "") and \
                f"min-width:{want}px" not in css.replace(" ", ""):
            bad114.append(f"CSS 에 {why} 경계 {want}px 이 없다")
    for one in widths:
        tier = ("좁음" if one <= card_max
                else "넓음" if one >= wide_min else "중간")
        del tier

    # V11-115 — 폭마다 한 칸이 몇 자인가
    bad115 = []
    for klass, (tpl_path, _name) in CARD_SHAPES.items():
        tpl = open(tpl_path, encoding="utf-8").read()
        for one in widths:
            if one >= wide_min:
                continue                  # 넓음은 표다 — 격자가 아니다
            top = card_max if one <= card_max else wide_min - 1
            got = _place_cards(css, tpl, klass, top, wide_min - 1)
            placed, cols, biggest, _spill, _hid, _n, fonts, spans = got
            if not placed or not cols:
                continue
            track = (one - row_pad - (cols - 1) * gap) / cols
            for idx, span in spans.items():
                if idx not in placed:
                    continue
                room = track * span + gap * (span - 1)
                font = fonts.get(idx) or biggest
                if not font:
                    continue
                chars = room / font
                if chars < chars_min:
                    label = _cells_of(tpl, len(CARD_AXES))[idx][1] or "칸"
                    bad115.append(
                        f"{klass} {one}px 「{label}」 — {room:.0f}px ÷ "
                        f"{font:.0f}px = {chars:.1f}자")
    del _j
    return [
        result(C["V11-113"], rid, f"{len(widths)}폭",
               f"{len(widths) - len(bad113)}폭", not bad113, bad113[:6]),
        result(C["V11-114"], rid, 0, len(bad114), not bad114, bad114[:6]),
        result(C["V11-115"], rid, f"{chars_min:.0f}자 이상",
               "좁음" if bad115 else "넉넉함", not bad115, bad115[:6]),
    ]


# 화면 : (렌더 파일, 있어야 할 차트 표시, 없을 때 적어야 할 말)
# ★ 어느 화면에 어떤 차트인지는 부록 G 14장-7 이 정한다
CHART_SCREENS = {
    "home": ("class=\"hist\"", "분포를 낼 수 없습니다"),
    "market": ("svg class=\"line\"", "선을 낼 수 없습니다"),
    "why_listing_id": ("class=\"pos\"", "분포를 내지 않습니다"),
    "dealers": ("class=\"quad\"", "표본"),
    "watch": ("class=\"spark\"", "추이 없음"),
}


def _chart_check(rid):
    """V11-119 — 화면마다 차트가 있는가 (개정 340).

    ★ 마스터 지적 — 「차트가 안 보이잖아」
    ★ 차트가 없으면 「왜 없는지」가 있어야 한다.  자리를 비워 두지 않는다
    """
    base = os.path.join(ROOT, "outputs", "render")
    if not os.path.isdir(base):
        return not_applicable(C["V11-119"], rid, "렌더 결과가 없다")
    bad, seen = [], 0
    for name, (mark, why) in sorted(CHART_SCREENS.items()):
        path = os.path.join(base, f"{name}.html")
        if not os.path.isfile(path):
            continue
        seen += 1
        html = open(path, encoding="utf-8").read()
        if mark in html:
            continue
        if why in html:
            continue                  # 차트가 없는 까닭을 적었다
        bad.append(f"{name} — 차트({mark})도 없고 왜 없는지도 안 적었다")
    if not seen:
        return not_applicable(C["V11-119"], rid, "차트 화면 렌더가 없다")
    return result(C["V11-119"], rid, f"{seen}화면", f"{seen - len(bad)}화면",
                  not bad, bad[:6])


# 매물이 나오는 화면 — 행 전체가 링크여야 하고 터치로 미리보기가 떠야 한다
ROW_LINK_SCREENS = ("listings", "recommend", "watch")


def _row_link_checks(rid):
    """V11-116 · V11-117 — 행 전체 링크 · 터치 미리보기 (개정 337).

    ★ 렌더 결과를 본다.  템플릿에 있어도 값이 안 실리면 링크가 없다
    ★ 행 수와 data-href 수를 견준다 — 하나만 있으면 「있다」가 아니다
    """
    base = os.path.join(ROOT, "outputs", "render")
    if not os.path.isdir(base):
        return [not_applicable(C["V11-116"], rid, "렌더 결과가 없다"),
                not_applicable(C["V11-117"], rid, "렌더 결과가 없다")]
    bad116, bad117, seen = [], [], 0
    for name in ROW_LINK_SCREENS:
        path = os.path.join(base, f"{name}.html")
        if not os.path.isfile(path):
            continue
        html = open(path, encoding="utf-8").read()
        rows = len(re.findall(r"<tr[^>]*\bdata-peek=", html))
        if not rows:
            continue
        seen += 1
        links = len(re.findall(r"<tr[^>]*\bdata-href=", html))
        if links < rows:
            bad116.append(f"{name} — 행 {rows}개인데 data-href {links}개")
        if "touchstart" not in html:
            bad117.append(f"{name} — touchstart 를 안 듣는다")
        if 'id="peek"' not in html:
            bad117.append(f"{name} — 미리보기 상자가 없다")
    if not seen:
        return [not_applicable(C["V11-116"], rid, "매물 화면 렌더가 없다"),
                not_applicable(C["V11-117"], rid, "매물 화면 렌더가 없다")]
    return [result(C["V11-116"], rid, f"{seen}화면", f"{seen - len(bad116)}화면",
                   not bad116, bad116[:6]),
            result(C["V11-117"], rid, f"{seen}화면", f"{seen - len(bad117)}화면",
                   not bad117, bad117[:6])]


def _screen_contradiction_check(rid):
    """V11-105 — 화면 위아래가 어긋나지 않는가 (개정 325).

    ★ 마스터가 본 것 — 위에서 「미조회」, 아래에서 「확인율 100%」.
      표는 정확했고 그 아래 문장이 표를 배신했다
    """
    path = os.path.join(ROOT, "outputs", "render", "why_listing_id.html")
    if not os.path.isfile(path):
        return not_applicable(C["V11-105"], rid, "렌더 결과가 없다")
    html = open(path, encoding="utf-8").read()
    text = re.sub(r"<[^>]+>", " ", html)
    bad = []
    if "확인율 100%" in text and "미조회" in text:
        bad.append("「미조회」가 있는데 「확인율 100%」라 한다")
    # ★ 옛 규격 문구가 남아 있으면 화면이 옛말을 한다 (개정 289 · 298)
    if "분모에서 뺍니다" in text:
        bad.append("★ 「분모에서 뺍니다」 — 개정 289 로 폐기된 문구다")
    if "확인율" not in text:
        bad.append("확인율을 아예 안 낸다")
    return result(C["V11-105"], rid, 0, len(bad), not bad, bad)


def _chunk_check(rid):
    """V11-98 — 바이트 조각을 이어붙여 원문이 그대로 나오는가 (개정 307)."""
    from store import chunk

    bad = []
    # ★ 실측 facet 크기(19~21만)보다 크게 잡는다.  작으면 시험이 안 된다
    cfg = _checks_cfg()
    body = ("가나다" * int(cfg["chunk_probe_chars"])).encode("utf-8")
    room = int(cfg["chunk_probe_room"])
    parts = [body[i:i + room] for i in range(0, len(body), room)]
    key, sig = "probe", chunk.digest(body)
    for i, part in enumerate(parts):
        chunk.put(key, i, len(parts), part, 0.0)
    got = chunk.take(key, len(body), sig)
    if got != body:
        bad.append("이어붙인 것이 원문과 다르다")

    # ★ 하나라도 빠지면 저장하지 않는다 — 반쪽을 원문이라 부르지 않는다
    for i, part in enumerate(parts):
        if i == 1:
            continue
        chunk.put("half", i, len(parts), part, 0.0)
    try:
        chunk.take("half", len(body), sig)
        bad.append("★ 조각이 빠졌는데 저장했다")
    except ValueError as e:
        if "2/" not in str(e):
            bad.append(f"몇 번째가 빠졌는지 안 밝힌다 — {e}")

    # 화면이 조각을 보내는가
    tpl = open(os.path.join(TEMPLATES, "admin_collect.html"),
               encoding="utf-8").read()
    if "chunk_seq" not in tpl or "chunk_hash" not in tpl:
        bad.append("화면이 조각으로 안 보낸다")
    if "나눌 수 없습니다" in tpl:
        bad.append("★ 아직 「나눌 수 없습니다」로 포기한다")
    return result(C["V11-98"], rid, "원문 그대로",
                  "그대로" if not bad else bad, not bad, bad)


def _csrf_reuse_check(rid):
    """V11-99 — 한 세션에서 토큰이 몇 번이고 쓰이는가 (개정 308).

    ★ 브라우저 수집은 한 화면에서 수십 번 POST 한다 (전 차종 16묶음).
      1회용도, 서버 메모리 저장도 그것을 견디지 못한다
    """
    from web.session import csrf_for, csrf_ok

    bad = []
    try:
        from store.pii import load_key

        key = load_key(os.path.join(ROOT, "secrets", "plate_hmac.key"))
    except (FileNotFoundError, ValueError):
        return not_applicable(C["V11-99"], rid, "HMAC 키가 없다")
    a = csrf_for("session-a", key)
    if not all(csrf_ok(a, csrf_for("session-a", key))
               for _ in range(int(_checks_cfg()["csrf_repeat"]))):
        bad.append("같은 세션인데 토큰이 매번 다르다")
    if csrf_ok(a, csrf_for("session-b", key)):
        bad.append("★ 다른 세션의 토큰이 통과한다")
    # ★ 메모리 dict 에 쌓고 있으면 재시작에 무효가 된다 — 그 자리를 찾는다
    app = open(os.path.join(ROOT, "web", "app.py"), encoding="utf-8").read()
    if "csrf_for(" not in app:
        bad.append("토큰을 세션에서 만들지 않는다")
    return result(C["V11-99"], rid, "5번 다 통과",
                  "통과" if not bad else bad, not bad, bad)


def _origin_price_check(rid):
    """V11-92 — 신차가 = 등급기준 + 선택옵션 (개정 301).

    ★ 실측 — 엔카 신차가 6,547만은 등급기준 5,787 + 옵션 760 이다.
      우리는 등급기준만 냈다.  옵션 760만이 통째로 빠져 있었다
    """
    path = os.path.join(ROOT, "outputs", "render", "listings.html")
    if not os.path.isfile(path):
        return not_applicable(C["V11-92"], rid, "렌더 결과가 없다")
    html = open(path, encoding="utf-8").read()
    bad = []
    if "등급 " not in html or "+ 옵션 " not in html:
        bad.append("「등급 5,787만 + 옵션 760만」 형태로 안 낸다")
    if "판매자가 입력한" not in html:
        bad.append("「판매자가 입력한 것」임을 안 밝힌다")
    return result(C["V11-92"], rid, "셋을 다 낸다",
                  "낸다" if not bad else bad, not bad, bad)


# v1 이 낸 조작 → 그 조작을 v2 에서 찾는 무늬 (개정 303~305 · ORDER 08-17).
# ★ 손으로 적은 표가 아니다 — v1 템플릿에 그 무늬가 있을 때만 「v1 에 있다」로 센다
V1_OPS = {
    "관심 ♡": (("♡", "watch/add", "관심"), ("♡", "watch/add", "관심")),
    "미리보기": (("data-peek", "preview"), ("data-peek", "preview")),
    "엔카 링크": (('target="_blank"',), ('target="_blank"',)),
    "비교 담기": (("compare",), ("compare",)),
    "정렬 드롭다운": (("<select",), ("<select",)),
    "조건 단추": (("btn",), ("btn",)),
}
# ★ 매물이 나오는 화면 여섯만이다 (개정 306 §3).
#   base 는 껍데기고 run·market·dealers 는 매물 목록이 아니다 — 요구하지 않는다
V1_SCREENS = (("listings", "listings"), ("recommend", "recommend"),
              ("why", "why"), ("dashboard", "dashboard"),
              ("compare", "compare"), ("watch", "watch"))


def _v1_parity_checks(rid):
    """V11-68 · V11-69 — v1 전 화면과 대조한다 (개정 277 · 303~305).

    ★ 가이드 지적 — 「개정 277 에서 v1 목록만 봤다.  추천은 안 봤다」
      마스터가 화면을 볼 때마다 「v1 에 있던 것」이 하나씩 나온다.
      검사가 한 번에 다 찾아야 한다 (ORDER_v1_compare 08-17)
    ★ 「v1 이 낸 것」을 v1 템플릿에서 직접 읽는다.  손으로 적은 표를 안 쓴다
    """
    src = os.path.join(V1_UI, "listings.html")
    if not os.path.isfile(src):
        return [not_applicable(C["V11-68"], rid, "v1 원본이 없다"),
                not_applicable(C["V11-69"], rid, "v1 원본이 없다")]
    v1 = open(src, encoding="utf-8").read()
    ours = open(LISTINGS_TPL, encoding="utf-8").read()

    # ── V11-68 — 목록 열 ─────────────────────────────────────────────
    # ★ 개정 332(부록 G)가 개정 277(v1 22열)을 대신한다.
    #   부록 G 가 목록 열의 정본이다 — v1 은 그 앞의 판이다.
    #   부록 G 가 있으면 그것과 대조하고, 없으면 v1 과 대조한다
    want = []
    text = canon_text("화면")
    if text:
        block = text.split("## 넓음 (≥1100)", 1)[-1].split("## 중간", 1)[0]
        # ★ 표에 **굵게** 가 섞여 있다.  이름만 뽑는다
        want = [m.group(1).strip().strip("*").strip()
                for m in re.finditer(r"^\| *\d+ *\| *([^|]+?) *\|", block,
                                     re.M)]
    if not want:
        head = re.search(r"<thead>(.*?)</thead>", v1, re.S)
        want = [re.sub(r"<[^>]+>", "", t).strip()
                for t in re.findall(r"<th[^>]*>(.*?)</th>", head.group(1), re.S)]
    want = [w for w in want if w]
    # ★ 축 열의 머리말은 config 에서 온다 (axis_heads).  템플릿 글자만 보면
    #   화면에 있는 열을 「없다」고 한다 — 실제로 낼 이름을 합쳐서 본다
    from report.screens.build import axis_heads

    got = re.sub(r"<[^>]+>", " ", ours) + " " + " ".join(
        a["label"] for a in axis_heads(ROOT))
    bad68 = [w for w in want if w not in got]

    # ── V11-69 — 화면마다 조작 ───────────────────────────────────────
    # ★ 화면 하나만 보면 「listings 는 v1 수준인데 recommend 가 없다」를 못 본다
    bad69 = []
    for v1_name, v2_name in V1_SCREENS:
        a = os.path.join(V1_UI, f"{v1_name}.html")
        b = os.path.join(TEMPLATES, f"{v2_name}.html")
        if not (os.path.isfile(a) and os.path.isfile(b)):
            continue
        src_a = open(a, encoding="utf-8").read()
        src_b = open(b, encoding="utf-8").read()
        for op, (in_v1, in_v2) in V1_OPS.items():
            if not any(x in src_a for x in in_v1):
                continue          # v1 에 없던 것은 요구하지 않는다
            if not any(x in src_b for x in in_v2):
                bad69.append(f"{v2_name} — {op}")
    return [_photo_size_by_screen_check(rid), _template_leak_check(rid),
            _em_dash_check(rid), _chart_check(rid),
            *_row_link_checks(rid),
            *_card_shape_checks(rid),
            *_width_checks(rid),
            _why_order_check(rid),
            _screen_contradiction_check(rid),
            _chunk_check(rid),
            _csrf_reuse_check(rid),
            _origin_price_check(rid),
            result(C["V11-68"], rid, "열",
                   f"{len(want) - len(bad68)}/{len(want)}", not bad68, bad68),
            result(C["V11-69"], rid, "화면별 조작",
                   f"빠진 것 {len(bad69)}" if bad69 else "v1 과 같다",
                   not bad69, bad69[:12])]


# 확인할 폭 (마스터 지시 08-16).  ★ 360 이 기준이다 — 휴대폰으로 본다
WIDTHS = (360, 640, 900, 1100, 1400)



def _media_blocks(css: str):
    """@media (max-width:N) 블록을 중괄호를 세어 잘라 낸다.

    ★ 정규식으로 첫 } 까지 자르면 안쪽 규칙 하나만 잡는다 (실측)
    """
    for m in re.finditer(r"@media([^{]*max-width:\s*(\d+)px[^{]*)\{", css):
        width, i, depth = int(m.group(2)), m.end(), 1
        while i < len(css) and depth:
            if css[i] == "{":
                depth += 1
            elif css[i] == "}":
                depth -= 1
            i += 1
        low = re.search(r"min-width:\s*(\d+)px", m.group(1))
        _media_blocks.low[css[m.end():i - 1]] = int(low.group(1)) if low else 0
        yield width, css[m.end():i - 1]


_media_blocks.low = {}


def _responsive_checks(rid):
    """V11-70 · V11-71 — 반응형 (STEP 149o-2 · 개정 278).

    ★ 「반응형으로 했습니다」가 아니라 숫자로 본다.
      좁은 폭에서 display:none 으로 값을 지우는지 CSS 를 실제로 읽는다
    """
    import json as _j

    css = open(APP_CSS, encoding="utf-8").read()
    html = open(LISTINGS_TPL, encoding="utf-8").read()
    # 이 폭 아래는 카드다 (STEP 149o-2).  ★ 폭은 표시 정책이라 config 에 둔다
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        web = _j.load(f)
    narrow_max = int(web["narrow_max_px"])
    # ★ 부록 G 「좁음 (<640)」 도면에 없는 칸 (개정 332).
    #   지우는 것이 아니라 접는 것이다 — 640 이상과 /why 에는 그대로 있다.
    #   ★ 여기 적힌 것만 접을 수 있다.  적지 않고 지우면 아래에서 걸린다
    folded = set(web.get("narrow_folded_labels", []))
    # 칸 안의 조각 — 칸은 그대로 보이고 그 안의 원값만 상세로 간다
    folded_parts = tuple(web.get("narrow_folded_parts", []))
    from report.screens.build import CHIP_AXES

    # ★ 축 칸은 반복문 하나로 적혀 있다.  화면에 실제로 나오는 수로 센다 —
    #   템플릿 글자 수를 세어 보고하면 마스터가 보는 수와 다르다.
    #   JS 안의 문자열도 빼야 한다 — 실측: ' + label + ' 이 한 칸으로 세어졌다
    body = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    cells = [c for c in re.findall(r'data-label="([^"]*)"', body) if c]
    cells += [""] * (len(CHIP_AXES) - 1)
    bad70, bad71 = [], []
    if not cells:
        bad70.append("칸에 이름표(data-label)가 없다 — 카드로 못 바꾼다")

    card = False
    # ★ 「좁은 폭」은 카드 경계다 (개정 337).  narrow_max(1099)는 옛 값이라
    #   카드 변환 블록이 1749 로 넓어진 뒤 「카드로 안 바뀐다」로 헛짚었다
    card_at = int(web.get("list_card_max_px") or narrow_max)
    for width, body in _media_blocks(css):
        low = _media_blocks.low.get(body, 0)
        if width < card_at or low > card_at:
            continue
        if re.search(r"\.rows[^{}]*\{[^{}]*display:\s*block", body):
            card = True
        for rule in re.finditer(r"([^{}]+)\{([^{}]*)\}", body):
            sel, decl = rule.group(1), rule.group(2)
            if "display:none" not in decl.replace(" ", ""):
                continue
            if "thead" in sel or "#peek" in sel:
                # 머리말은 data-label 로 칸마다 붙고,
                # 미리보기는 값이 아니라 마우스용 덧창이다 (손가락에는 안 뜬다)
                continue
            # ★ 부록 G 도면이 좁은 폭에서 뺀 칸은 접어도 된다 (개정 332).
            #   config 에 적힌 것만이다 — 몰래 늘어나면 여기서 걸린다.
            #   한 규칙이 여러 칸을 지우면 전부 적혀 있어야 한다
            # ★ 주석 안의 쉼표가 선택자를 쪼갠다 — 먼저 뗀다
            #   («/* 원값(시세 5,290만)은 … */» 가 한 조각으로 세어졌다)
            sel = re.sub(r"/\*.*?\*/", " ", sel, flags=re.S)
            named = re.findall(r'data-label="([^"]*)"', sel)
            if named and all(x in folded for x in named):
                continue
            # 칸이 아니라 칸 안의 조각을 접는 것은 따로 못박아 둔다
            parts = [x.strip() for x in sel.split(",") if x.strip()]
            if folded_parts and parts and all(
                    x.endswith(folded_parts) for x in parts):
                continue
            bad70.append(f"{width}px 에서 값을 지운다 — {' '.join(sel.split())}")
    if not card:
        bad71.append("좁은 폭에서 표가 카드로 바뀌지 않는다")
    # ★ 목록을 가로 스크롤에 떠넘기지 않는다
    for m in re.finditer(r"([^{}]*)\{([^{}]*overflow-x[^{}]*)\}", css):
        if "rows" in m.group(1) and "auto" not in m.group(2):
            bad71.append(f"목록을 가로 스크롤에 떠넘긴다 — {m.group(1).strip()}")
    return [result(C["V11-70"], rid, "칸", f"{len(cells)}칸", not bad70, bad70),
            result(C["V11-71"], rid, "가로 스크롤",
                   "없음" if not bad71 else "있음", not bad71, bad71)]


# 주소가 될 수 없는 값.  ★ 화면에 이 글자가 찍히면 그것이 뿌리다
DEAD_URL = ("", "null", "None", "undefined", "#")
RE_URL_ATTR = re.compile(r'(href|src|action)="([^"]*)"')


def _dead_links(html: str) -> list:
    """렌더 결과에서 죽은 주소를 고른다.  ★ 템플릿이 아니라 결과를 본다."""
    body = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
    out = []
    for attr, val in RE_URL_ATTR.findall(body):
        v = val.strip()
        if v in DEAD_URL:
            out.append(f'{attr}="{val}"')
        elif re.search(r"[?&][\w_]+=(&|$)", v):
            # ?dealer= 처럼 값이 빈 조건 — 누르면 조건이 안 걸린 전건이 나온다
            out.append(f'{attr}="{v[:60]}" (빈 조건)')
    return out


def _null_link_check(conn, rid):
    """V11-72 — 빈 주소로 가는 링크 (개정 279 · 마스터 실측).

    ★ 전 화면을 실제로 렌더해 결과 HTML 을 본다.
      템플릿을 읽어 「{% if %} 로 막혀 있다」고 하는 것은 검사가 아니다
    """

    from contracts import ROLE_ADMIN, Account
    from errors import CarWatchError
    from web.routes import GET, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-72"], rid, "판정 결과가 없다")
    probe = _probe(conn)
    acc = Account(1, ROLE_ADMIN, "마스터")
    bad, seen = [], 0
    for route in ROUTES:
        if GET not in route.methods or guard(acc, route) is not None:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            continue
        pv = {}
        if "{" in route.path:
            k = route.path.split("{")[1].split("}")[0]
            pv = {k: str(row[0]) if k == "listing_id" else "1"}
        try:
            _st, _h, body = fn(probe, acc,
                               {"query": {}, "form": {}, "method": GET},
                               path_vars=pv, csrf="t")
        except (CarWatchError, KeyError, ValueError):
            continue          # 입력이 없어 못 그리는 화면은 이 검사 대상이 아니다
        except Exception:                                    # noqa: BLE001
            continue
        seen += 1
        for hit in _dead_links(body.decode("utf-8", "replace")):
            bad.append(f"{route.path} {hit}")
    return result(C["V11-72"], rid, f"{seen}화면",
                  "없음" if not bad else f"{len(bad)}곳", not bad, bad[:10])


# 화면마다 반드시 나와야 하는 시안의 시각 요소 (검토 14 · 개정 275).
# ★ 「그 화면이 무엇으로 보여 주는가」다.  표로 대신하면 시안이 아니다
# (그려야 할 class, 그릴 자료가 있다는 표시).
# ★ 자료가 없어 못 그린 것과 구조가 없는 것은 다르다 —
#   관심 0건이면 spark 를 그릴 수가 없다.  그것을 코드 결함으로 세지 않는다
# (그려야 할 class, 화면을 그릴 자료가 있다는 표시, 「그 자료가 없다」는 표시)
# ★ 셋째 칸 — 그 자리를 「없음」으로 그린 흔적이다.  씨앗 DB 는 사진이 없어
#   (StubEncar 가 "Photos": [] 를 준다) 목록이 전건 .thumb-none 으로 나온다.
#   그것을 「썸네일을 안 만들었다」로 세면 검사가 거짓말한다 (실측 08-18)
SIAN_VISUAL = {
    "/market": (("hist", "histx"), None, None),
    "/dealers": (("quad",), None, None),
    "/watch": (("spark",), "watch_id", None),
    "/recommend": (("pbar",), None, "thumb-none"),
    "/why/{listing_id}": (("curve",), None, None),
    "/listings": (("thumb", "peek"), None, "thumb-none"),
}


def _sian_visual_check(conn, rid):
    """V11-77 — 시안의 시각 요소가 렌더 결과에 실제로 나오는가.

    ★ CSS 도 템플릿도 보지 않는다.  나온 HTML 에서 class 를 센다
    """

    from contracts import ROLE_ADMIN, Account
    from errors import CarWatchError
    from web.routes import GET, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-77"], rid, "판정 결과가 없다")
    probe = _probe(conn)
    acc = Account(1, ROLE_ADMIN, "마스터")
    routes = {r.path: r for r in ROUTES}
    bad, ok, skipped = [], 0, []
    for path, (want, needs, none_mark) in SIAN_VISUAL.items():
        route = routes.get(path)
        if route is None or GET not in route.methods:
            bad.append(f"{path} — 그런 화면이 없다")
            continue
        if guard(acc, route) is not None:
            continue
        pv = {}
        if "{" in path:
            key = path.split("{")[1].split("}")[0]
            pv = {key: str(row[0])}
        try:
            _st, _h, body = HANDLERS[route.view](
                probe, acc, {"query": {}, "form": {}, "method": GET},
                path_vars=pv, csrf="t")
        except (CarWatchError, KeyError, ValueError) as e:
            bad.append(f"{path} — 못 그렸다: {type(e).__name__} {e}")
            continue
        html = body.decode("utf-8", "replace")
        if needs and needs not in html:
            skipped.append(f"{path} — 그릴 자료가 없다 ({needs})")
            continue
        used = set()
        for attr in re.findall(r'class="([^"{}]*)"', html):
            used |= set(attr.split())
        used |= set(re.findall(r'id="([\w-]+)"', html))
        for cls in want:
            if cls in used:
                ok += 1
            elif none_mark and none_mark in used:
                # ★ 자리는 만들었고 넣을 것이 없어 「없음」을 그린 것이다.
                #   구조가 없는 것과 다르다 — 코드 결함으로 세지 않는다
                skipped.append(f"{path} — .{cls} 를 그릴 자료가 없다 "
                               f"(.{none_mark} 로 나온다)")
            else:
                bad.append(f"{path} — .{cls} 가 화면에 없다 (표로 내고 있다)")
    total = sum(len(w) for w, _n, _m in SIAN_VISUAL.values())
    seen = ok + len(bad)
    note = f"{ok}/{seen}" + (f" · 자료 없어 못 본 것 {len(skipped)}"
                             if skipped else "")
    return result(C["V11-77"], rid, f"{total}종", note, not bad,
                  bad[:8] + skipped)


def _cell_squeeze_check(rid):
    """V11-78 — 좁은 폭에서 글자가 세로로 떨어지지 않는가.

    ★ 렌더 결과의 표를 세고, 그 표가 좁은 폭에서
      ① 카드로 바뀌거나 ② 안쪽 최소 폭을 갖고 가로로 넘기는지를 본다.
      둘 다 아니면 열 수만큼 쥐어짜여 한 글자가 한 줄이 된다
    """
    import json as _j

    # ★ 한 칸이 이 글자 수보다 좁아지면 세로로 떨어진다 (검토 17).
    #   폭을 브라우저 없이 재려면 「열 수 × 최소 칸 폭」이 화면 폭을 넘는지 본다.
    #   숫자는 표시 정책이라 config 에 둔다 (S14)
    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        cfg = _j.load(f)
    min_chars = int(cfg["min_cell_chars"])
    char_px = int(cfg["char_px"])
    narrow = int(cfg["narrow_px"])
    wide = int(cfg["narrow_max_px"])
    css = open(APP_CSS, encoding="utf-8").read()
    guarded = False
    for width, body in _media_blocks(css):
        if narrow <= width <= wide and "table" in body:
            # ★ 막는 방법은 둘이다 — 안쪽에 최소 폭을 주거나,
            #   칸을 안 접게 해서 표가 스스로 넓어지게 하거나.
            #   둘 다 바깥이 가로로 넘어가게 만든다
            if (re.search(r"min-width:\s*\d+px", body)
                    or re.search(r"white-space:\s*nowrap", body)):
                guarded = True
    bad = []
    if not guarded:
        bad.append("좁은 폭에서 표를 막는 것이 없다 — 열 수만큼 쥐어짜인다 "
                   "(안쪽 최소 폭이나 white-space:nowrap 이 필요하다)")
    render_dir = os.path.join(ROOT, "outputs", "render")
    worst = 0
    if os.path.isdir(render_dir):
        for name in sorted(os.listdir(render_dir)):
            if not name.endswith(".html"):
                continue
            html = open(os.path.join(render_dir, name), encoding="utf-8").read()
            for tbl in re.findall(r"<table.*?</table>", html, re.S):
                cols = max((len(re.findall(r"<t[dh]\b", tr))
                            for tr in re.findall(r"<tr.*?</tr>", tbl, re.S)),
                           default=0)
                worst = max(worst, cols)
                # ★ 카드로 바뀌는 표(.rows)는 열 수와 무관하다
                if 'class="rows"' in tbl:
                    continue
                if cols * min_chars * char_px > narrow and not guarded:
                    bad.append(f"{name} — {cols}열 표가 {narrow}px 에서 "
                               f"한 칸 {min_chars}글자 미만이 된다")
    return result(C["V11-78"], rid, f"최대 {worst}열",
                  "안 떨어짐" if not bad else f"{len(bad)}곳",
                  not bad, bad[:6])


def _static_version_check(rid):
    """V11-82 — 정적 파일에 버전이 붙는가 (개정 282).

    ★ run_id 로 붙이면 수집할 때마다 전부 다시 받는다.  내용 지문이어야 한다
    """
    from web.app import static_version

    html = open(os.path.join(TEMPLATES, "base.html"), encoding="utf-8").read()
    bad = []
    for m in re.finditer(r'(?:href|src)="(/static/[^"]*)"', html):
        if "?v=" not in m.group(1):
            bad.append(f"버전이 없다 — {m.group(1)}")
    got = static_version()
    if not got:
        bad.append("지문을 만들지 못했다 — web/static/app.css 를 못 읽는다")
    return result(C["V11-82"], rid, "버전", got or "없음", not bad, bad)


def _axis_state_check(conn, rid):
    """V11-79 — 축 칸에 맨 숫자가 나오지 않는가 (STEP 149n).

    ★ 렌더 결과의 축 칸을 실제로 읽는다.  템플릿을 읽지 않는다
    """

    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS

    route = {r.path: r for r in ROUTES}.get("/listings")
    if route is None or GET not in route.methods:
        return not_applicable(C["V11-79"], rid, "/listings 가 없다")
    probe = _probe(conn)
    try:
        _st, _h, body = HANDLERS[route.view](
            probe, Account(1, ROLE_ADMIN, "마스터"),
            {"query": {}, "form": {}, "method": GET}, path_vars={}, csrf="t")
    except Exception as e:                                   # noqa: BLE001
        return not_applicable(C["V11-79"], rid, f"못 그렸다: {e}")
    html = body.decode("utf-8", "replace")
    bad, seen = [], 0
    for cell in re.findall(r'<td class="c ax".*?</td>', html, re.S):
        seen += 1
        text = re.sub(r"<[^>]+>", "", cell).strip()
        # ★ 맨 숫자만 있는 칸이 결함이다.  「1회」 「111만」은 상태다
        if re.fullmatch(r"-?\d+(\.\d+)?", text):
            bad.append(f"축 칸이 숫자뿐이다 — {text}")
    return result(C["V11-79"], rid, f"{seen}칸",
                  "상태" if not bad else f"{len(bad)}칸 숫자",
                  not bad, bad[:6])


# ★ 부록 G 로 열 이름이 「시세 대비」 「신차가 대비」가 됐다 (개정 332).
#   값을 함께 내는 것은 그대로다 — 이름만 바뀌었다
THREE_VALUES = ("신차가 대비", "시세 대비", "가격")


def _three_values_check(conn, rid):
    """V11-81 — 신차가 · 시세 · 가격 셋이 함께 나오는가 (STEP 149n-3)."""

    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS

    route = {r.path: r for r in ROUTES}.get("/listings")
    if route is None:
        return not_applicable(C["V11-81"], rid, "/listings 가 없다")
    probe = _probe(conn)
    try:
        _st, _h, body = HANDLERS[route.view](
            probe, Account(1, ROLE_ADMIN, "마스터"),
            {"query": {}, "form": {}, "method": GET}, path_vars={}, csrf="t")
    except Exception as e:                                   # noqa: BLE001
        return not_applicable(C["V11-81"], rid, f"못 그렸다: {e}")
    html = body.decode("utf-8", "replace")
    row = re.search(r"<tr[^>]*>.*?</tr>", html.split("<tbody>", 1)[-1], re.S)
    got = row.group(0) if row else ""
    bad = [w for w in THREE_VALUES if f'data-label="{w}"' not in got]
    # ★ 값 자체도 나와야 한다 — 「대비 %」만 내고 원값을 숨기면 안 된다
    for word in ("시세", "신차가"):
        if word not in got:
            bad.append(f"{word} 원값이 없다")
    return result(C["V11-81"], rid, "셋",
                  f"{len(THREE_VALUES) - len(bad)}/{len(THREE_VALUES)}",
                  not bad, [f"{w} 칸이 없다" for w in bad])


def _photo_size_check(rid):
    """V11-80 — 사진이 최소 크기 이상인가 (R-206 · `[마스터]` 개정 281).

    ★ `.thumb` 규칙의 글자만 읽고 통과하고 있었다.  그 class 가 목록
      `<img>` 에 붙어 있지 않아 실제로는 아무 데도 안 먹는 죽은 규칙이었고,
      화면에는 `.rows td.photo img` 의 96px 이 그려지고 있었다.
      검사는 「128px 이다」라고 했고 화면은 96px 이었다 —
      이 프로젝트가 막으려는 바로 그 「선언과 실제의 괴리」다 (실측 08-18)
    ★ 지금은 정본 표(`61-web/a-common` 사진 크기)를 읽는다.
      CSS 가 그 표대로인지는 V11-107 이 본다.  두 검사가 이어져야
      「표대로 그렸고 그 표가 최소치를 넘는다」가 성립한다
    """
    import json as _j

    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        want = int(_j.load(f)["photo_min_px"])
    text = canon_text("화면")
    if not text:
        return not_applicable(C["V11-80"], rid, "화면 정본을 못 찾았다")
    # 표의 「| 목록 | 96×72 | 88×66 | 80×60 |」 꼴을 읽는다.
    # ★ 목록·관심이 R-206 이 말하는 「목록 사진」이다.  추천은 마스터가
    #   따로 「추천에는 이미지 너무 커」라고 해 작게 정한 화면이다
    seen: dict = {}
    for line in text.splitlines():
        got = re.match(r"\| *\**(목록|관심)\** *\|((?: *\d+×\d+ *\|)+)", line)
        if not got:
            continue
        for w, _h in re.findall(r"(\d+)×(\d+)", got.group(2)):
            seen.setdefault(got.group(1), []).append(int(w))
    if not seen:
        return not_applicable(C["V11-80"], rid, "정본에 사진 크기 표가 없다")
    bad = [f"{name} {min(px)}px < {want}px "
           f"(정본 {' · '.join(str(x) for x in px)})"
           for name, px in sorted(seen.items()) if min(px) < want]
    got = " · ".join(f"{k} {'/'.join(str(x) for x in v)}px"
                     for k, v in sorted(seen.items()))
    return result(C["V11-80"], rid, f">= {want}px", got, not bad, bad[:6])


def _render_metrics_checks(conn, rid):
    """V11-73~76 — 렌더 결과를 재서 화면이 쓸 만한지 본다 (방법 D안).

    ★ 「돌아가는가」가 아니라 「쓸 수 있는가」다 (개정 279)
    """
    import json as _j
    import time as _t

    from contracts import ROLE_ADMIN, Account
    from errors import CarWatchError
    from web.routes import GET, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    with open(os.path.join(ROOT, "config", "web.json"), encoding="utf-8") as f:
        cfg = _j.load(f)
    max_kb = int(cfg["screen_max_kb"])
    max_sec = float(cfg["screen_max_sec"])
    # 본문에 이만큼도 없으면 빈 화면이다 (V11-73).  표시 정책이라 config 에 둔다
    min_words = int(cfg["min_body_words"])
    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return [not_applicable(C[c], rid, "판정 결과가 없다")
                for c in ("V11-73", "V11-74", "V11-75", "V11-76")]
    probe = _probe(conn)
    acc = Account(1, ROLE_ADMIN, "마스터")
    empty, unitless, deadlink, heavy, seen = [], [], [], [], 0
    for route in ROUTES:
        if GET not in route.methods or guard(acc, route) is not None:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            continue
        pv = {}
        if "{" in route.path:
            key = route.path.split("{")[1].split("}")[0]
            if key != "listing_id":
                continue
            pv = {key: str(row[0])}
        st = _t.time()
        try:
            _s, _h, body = fn(probe, acc,
                              {"query": {}, "form": {}, "method": GET},
                              path_vars=pv, csrf="t")
        except (CarWatchError, KeyError, ValueError):
            continue
        except Exception:                                    # noqa: BLE001
            continue
        took = _t.time() - st
        seen += 1
        html = body.decode("utf-8", "replace")
        text = re.sub(r"<script>.*?</script>", "", html, flags=re.S)
        text = re.sub(r"<[^>]+>", " ", text)
        # V11-73 — 값이 있는가.  머리말·메뉴 말고 본문에 숫자나 글이 있는가
        if len(text.split()) < min_words:
            empty.append(f"{route.path} — 낱말 {len(text.split())}개")
        # V11-74 — 원 단위 숫자가 맨몸으로 나오는가.
        # ★ 매물번호·계정번호 같은 식별자는 단위가 없는 것이 맞다.
        #   앞뒤 낱말로 가른다 — 「매물 42548963」은 식별자다
        for m in re.finditer(r"(?<![\w,.])\d{7,}(?![\w,.%])", text):
            if route.path in RAW_VALUE_SCREENS:
                break
            near = text[max(0, m.start() - 24):m.start()]
            if any(w in near for w in ID_WORDS):
                continue
            unitless.append(f"{route.path} — 단위 없는 숫자 {m.group(0)}")
            break
        # V11-75 — 죽은 링크
        dead = _dead_links(html)
        if dead:
            deadlink.append(f"{route.path} — {dead[0]}")
        # V11-76 — 크기·시간
        kb = len(body) / BYTES_PER_KB
        if kb > max_kb or took > max_sec:
            heavy.append(f"{route.path} — {kb:.0f}KB · {took:.2f}초")
    return [
        result(C["V11-73"], rid, f"{seen}화면",
               "값 있음" if not empty else f"{len(empty)}빈 화면",
               not empty, empty[:6]),
        result(C["V11-74"], rid, 0, len(unitless), not unitless, unitless[:6]),
        result(C["V11-75"], rid, 0, len(deadlink), not deadlink, deadlink[:6]),
        result(C["V11-76"], rid, f"<= {max_kb}KB · {max_sec}초",
               f"{len(heavy)}곳", not heavy, heavy[:6]),
    ]


def _browser_scope_checks(rid):
    """V11-48 · V11-49 — 범위 확인과 실패 격리 (개정 264)."""
    tpl = os.path.join(ROOT, "web", "templates", "admin_collect.html")
    html = open(tpl, encoding="utf-8").read() if os.path.isfile(tpl) else ""
    bad48 = []
    if 'value="all"' not in html:
        bad48.append("전 차종 선택지가 없다")
    if "f_confirm" not in html or "!== 'all'" not in html:
        bad48.append("all 확인 문구를 받지 않는다")
    bad49 = []
    # ★ 묶음마다 catch 하고 이어서 도는가 — 한 번 터지면 전체가 멈추면 안 된다
    if ".catch(" not in html or "failed.push" not in html:
        bad49.append("한 묶음 실패를 잡아 두지 않는다")
    if "runJob(i + 1)" not in html:
        bad49.append("실패 뒤 다음 묶음으로 가지 않는다")
    return [result(C["V11-48"], rid, "확인 있음",
                   "확인 있음" if not bad48 else "없음", not bad48, bad48),
            result(C["V11-49"], rid, "이어서 함",
                   "이어서 함" if not bad49 else "멈춘다", not bad49, bad49)]


def _import_opened_steps_check(conn, rid):
    """V11-46 — 반입으로 연 단계가 그렇게 적혀 있는가 (개정 259).

    ★ 「반입이 대신했다」는 근거가 있어야 연다.  근거는 두 가지다 —
      원문이 raw_response·raw_facet 에 있고, actual 이 'import' 다
    """
    from contracts import IMPORT_SOURCE, IMPORT_STEP_CODES

    marks = ",".join("?" * len(IMPORT_STEP_CODES))
    rows = conn.execute(
        f"SELECT code, actual, passed FROM audit_validation "
        f"WHERE code IN ({marks})", IMPORT_STEP_CODES).fetchall()
    opened = [r for r in rows if r[1] == IMPORT_SOURCE]
    if not opened:
        return not_applicable(C["V11-46"], rid, "반입으로 연 단계가 없다")
    batches = conn.execute(
        "SELECT COUNT(*) FROM raw_response WHERE origin=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    bad = []
    for code, actual, passed in opened:
        if not passed:
            bad.append(f"{code}: passed=0 인데 actual={actual}")
    if not batches:
        bad.append("반입 원문이 0건인데 단계를 열었다")
    return result(C["V11-46"], rid, IMPORT_SOURCE,
                  " · ".join(f"{c}={a}" for c, a, _p in opened), not bad, bad)


def _import_resume_check(conn, rid):
    """V11-41 — 반입 뒤 S5~S10 이 이어서 도는가 (STEP 136b ④).

    ★ 「돌 수 있다」를 글로 두지 않는다.  precheck 를 실제로 물어본다
    """
    from collect.pipeline import completed_steps, precheck
    from contracts import IMPORT_SOURCE

    listings = conn.execute(
        "SELECT COUNT(*) FROM core_listing WHERE classify_source=?",
        (IMPORT_SOURCE,)).fetchone()[0]
    if not listings:
        return not_applicable(C["V11-41"], rid, "반입분이 없다")
    done = completed_steps(conn)
    ok, why = precheck(conn, "S5", done)
    return result(C["V11-41"], rid, "S5 가능", "가능" if ok else why, ok,
                  [] if ok else [why])


def _watch_invite_check(conn, rid):
    """비로그인 관심 POST 가 유도 화면인가 (E-9 · D-5).

    ★ 라우트 권한만 보면 403 도 「막았으니 통과」가 된다.
      담으려던 대상이 화면에 보이는지까지 본다
    """
    from contracts import ANONYMOUS
    from web.views import watch_add_post

    row = conn.execute("SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-23"], rid, "판정 결과가 없다")
    req = {"method": "POST", "query": {},
           "form": {"listing_id": str(row[0]), "csrf": "t"}}
    try:
        status, _h, body = watch_add_post(conn, ANONYMOUS, req, csrf="t")
    except Exception as e:                                   # noqa: BLE001
        return result(C["V11-23"], rid, "유도 화면",
                      f"{type(e).__name__}", False, [str(e)[:60]])
    html = body.decode("utf-8") if isinstance(body, bytes) else str(body)
    bad = []
    if int(status) != 200:
        bad.append(f"{int(status)} 를 냈다 — 유도 화면이 아니다")
    if "로그인" not in html:
        bad.append("로그인 안내가 없다")
    if str(row[0]) not in html:
        bad.append("담으려던 대상이 화면에 없다")
    return result(C["V11-23"], rid, "유도 화면",
                  "유도 화면" if not bad else "아님", not bad, bad)


# POST 를 눌러 볼 때 쓰는 표본 폼.  ★ 값 자체는 뜻이 없다 — 「눌린다」를 본다
# POST 가 내도 되는 상태.  ★ 500 은 「우리 결함」, 400 은 입력, 404 는 없는 것
POST_OK_STATUS = (HTTPStatus.OK, HTTPStatus.FOUND, HTTPStatus.SEE_OTHER,
                  HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND)

SMOKE_FORM = {
    "csrf": "t", "previewed": "1", "reason": "검사", "action": "remove",
    "sql": "SELECT 1", "name": "없는이름", "secret": "틀린비번",
    "usage": "display_only", "endpoint": "detail", "json_path": "a.b",
    "title": "검사", "body": "검사", "scope": "all",
}


def _post_smoke_check(conn, rid):
    """V11-37 — 전 POST 를 실제로 눌러 본다.

    ★ 화면이 뜨는 것만 보면 쓰기 경로가 통째로 검사 밖에 있다.
      실측 08-15: 로그인 실패가 403 「권한 부족」을 냈는데 아무 검사도 안 잡았다
    """

    from contracts import ANONYMOUS, ROLE_ADMIN, ROLE_USER, Account
    from errors import PolicyError, ValidationError, WiringError
    from web.routes import POST, ROUTES
    from web.server import guard
    from web.views import HANDLERS

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-37"], rid, "판정 결과가 없다")

    # ★ 사본에 대고 누른다.  검사가 실제 DB 를 고치면 안 된다
    # ★ 파일을 복사하지 않는다.  커밋 안 된 스키마가 사본에 안 따라온다
    probe = _probe(conn)

    accs = {"anonymous": ANONYMOUS, "user": Account(2, ROLE_USER, "사용자"),
            "admin": Account(1, ROLE_ADMIN, "마스터")}
    form = dict(SMOKE_FORM, listing_id=str(row[0]))
    bad = []
    for route in ROUTES:
        if POST not in route.methods:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            bad.append(f"{route.path}: 핸들러가 없다")
            continue
        pv = {}
        if "{" in route.path:
            k = route.path.split("{")[1].split("}")[0]
            pv = {k: str(row[0]) if k == "listing_id" else "1"}
        for who, acc in accs.items():
            if guard(acc, route) is not None:
                continue
            try:
                st, _h, _b = fn(probe, acc,
                                {"query": {}, "form": dict(form),
                                 "method": POST},
                                path_vars=pv, csrf="t")
                if int(st) not in [int(s) for s in POST_OK_STATUS]:
                    bad.append(f"{route.path}[{who}] -> {int(st)}")
            except WiringError:
                # ★ 검사 환경은 plan·fetch 를 주입하지 않는다.
                #   배선 누락은 500 이 맞고, 그 자체가 결함은 아니다 (C-2)
                pass
            except PolicyError as e:
                # ★ guard 가 통과시킨 요청을 핸들러가 「권한 부족」으로 막으면
                #   둘이 어긋난 것이다.  실측: 비밀번호를 틀리면 403 이 났다
                if "권한 부족" in str(e):
                    bad.append(f"{route.path}[{who}] "
                               f"guard 는 통과인데 핸들러가 막았다")
            except ValidationError:
                pass          # 입력이 규칙에 안 맞은 것이다
            except Exception as e:                           # noqa: BLE001
                bad.append(f"{route.path}[{who}] "
                           f"{type(e).__name__}: {str(e)[:50]}")
    return result(C["V11-37"], rid, 0, len(bad), not bad, bad[:8])


# 화면 뼈대가 늘 넘기는 값.  ★ 여기 없는 이름은 뷰가 넘겨야 한다
FRAME_VARS = frozenset({"page", "viewer", "nav", "flash", "versions", "ver",
                        "csrf", "error"})
RE_TPL_OUT = re.compile(r"\{\{\s*([\w.]+)")
RE_TPL_IF = re.compile(r"\{%\s*if\s+([\w.!]+)")
RE_TPL_FOR = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+([\w.]+)")


def _template_roots(body: str) -> set:
    """템플릿이 바깥에서 받아야 하는 이름.  ★ 반복 변수는 뺀다."""
    loop = {m.group(1) for m in RE_TPL_FOR.finditer(body)}
    out = {m.group(1).split(".")[0] for m in RE_TPL_OUT.finditer(body)}
    out |= {m.group(1).lstrip("!").split(".")[0]
            for m in RE_TPL_IF.finditer(body)}
    out |= {m.group(2).split(".")[0] for m in RE_TPL_FOR.finditer(body)}
    return out - loop - FRAME_VARS


def _loop_fields(body: str) -> list:
    """{% for X in A.B %} 안에서 X.<필드> 로 쓰는 것.

    ★ 「반복 변수는 뺀다」가 결함이 사는 자리였다 (B-1).
      화면이 비는 자리는 거의 다 표 안이다 — 루프 변수의 속성을 봐야 잡힌다
    반환   [(원본경로, 루프변수, {필드…})]
    """
    out = []
    for m in RE_TPL_FOR.finditer(body):
        var, source = m.group(1), m.group(2)
        end = body.find("{% endfor %}", m.end())
        chunk = body[m.end():end if end > 0 else len(body)]
        fields = {f.group(1) for f in
                  re.finditer(rf"\{{\{{\s*{re.escape(var)}\.(\w+)", chunk)}
        fields |= {f.group(1) for f in
                   re.finditer(rf"\{{%\s*if\s+!?{re.escape(var)}\.(\w+)",
                               chunk)}
        if fields:
            out.append((source, var, fields))
    return out


def _context_supplied_check(conn, rid):
    """V11-38 — 템플릿이 쓰는 값을 뷰가 넘기는가.

    ★ 절만 만들고 값을 안 넘기면 화면이 조용히 빈 채로 뜬다.
      템플릿 엔진이 없는 이름을 빈 값으로 내주기 때문에 아무도 모른다.
      실측 08-15: admin 화면 8개가 그렇게 껍데기였다
    """
    from contracts import ROLE_ADMIN, Account
    from web.routes import GET, ROUTES
    from web.views import HANDLERS
    import web.views as _views

    row = conn.execute(
        "SELECT listing_id FROM result_score LIMIT 1").fetchone()
    if row is None:
        return not_applicable(C["V11-38"], rid, "판정 결과가 없다")

    acc = Account(1, ROLE_ADMIN, "마스터")
    seen: dict = {}
    orig = _views.page

    def spy(conn_, account, title, template, ctx, **kw):
        seen[template] = dict(ctx)
        return orig(conn_, account, title, template, ctx, **kw)

    _views.page = spy
    try:
        for route in ROUTES:
            if GET not in route.methods or route.view == "serve_static":
                continue
            fn = HANDLERS.get(route.view)
            if fn is None:
                continue
            pv = {}
            if "{" in route.path:
                pv = {route.path.split("{")[1].split("}")[0]: str(row[0])}
            try:
                fn(conn, acc, {"query": {}, "form": {}, "method": GET},
                   path_vars=pv, csrf="t")
            except Exception:                                # noqa: BLE001
                pass
    finally:
        _views.page = orig

    bad = []
    for tpl, ctx in sorted(seen.items()):
        path = os.path.join(TEMPLATES, tpl)
        if not os.path.isfile(path):
            bad.append(f"{tpl}: 템플릿이 없다")
            continue
        body = open(path, encoding="utf-8").read()
        bad += [f"{tpl}: {name} 를 아무도 안 넘긴다"
                for name in sorted(_template_roots(body))
                if name not in ctx]
        # ★ 표 안의 필드까지 본다 (B-1).  화면이 비는 자리는 거의 다 표다
        for source, var, fields in _loop_fields(body):
            sample = _first_item(ctx, source)
            if sample is None:
                continue          # 목록이 비었다 — 필드를 확인할 수 없다
            for f in sorted(fields):
                if not _has_field(sample, f):
                    bad.append(f"{tpl}: {var}.{f} 가 {source} 에 없다")

    return result(C["V11-38"], rid, 0, len(bad), not bad, bad[:10])



def _first_item(ctx: dict, path: str):
    """{% for X in A.B %} 의 A.B 첫 항목."""
    cur = ctx
    for part in path.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else getattr(
            cur, part, None)
        if cur is None:
            return None
    try:
        return next(iter(cur)) if cur else None
    except TypeError:
        return None


def _has_field(item, name: str) -> bool:
    if isinstance(item, dict):
        return name in item
    return hasattr(item, name)


def _table_counts(conn) -> dict:
    return {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            for (t,) in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'")}


def _save_button_check(conn, rid):
    """V11-39 — 쓸 수 있는 저장 단추는 실제로 쓰는가.

    ★ 「저장」이라 적힌 단추가 아무것도 안 바꾸면 사람이 바뀐 줄 알고 넘어간다.
      실측 08-15: admin_config · admin_api · admin_targets · admin_tools 가
      저장 단추를 내놓고 DB 를 전혀 건드리지 않았다
    준비 중이면 disabled 로 두고 그렇게 적는다 — 그건 검사 대상이 아니다
    """
    import re as _re

    from contracts import ROLE_ADMIN, Account
    from errors import PolicyError, ValidationError
    from web.routes import GET, POST, ROUTES
    from web.views import HANDLERS

    _ = GET
    # ★ 파일을 복사하지 않는다.  커밋 안 된 스키마가 사본에 안 따라온다
    probe = _probe(conn)
    acc = Account(1, ROLE_ADMIN, "마스터")

    bad = []
    for route in ROUTES:
        if POST not in route.methods:
            continue
        fn = HANDLERS.get(route.view)
        if fn is None:
            continue
        # ★ 템플릿 이름을 추측하지 않는다.  GET 을 눌러 실제로 나온 화면을 본다
        #   (admin_simple 은 view 이름과 템플릿 이름이 다르다)
        try:
            _st, _h, page_body = fn(conn, acc,
                                    {"query": {}, "form": {}, "method": "GET"},
                                    path_vars={}, csrf="t")
        except Exception:                                    # noqa: BLE001
            continue
        body = (page_body.decode("utf-8")
                if isinstance(page_body, bytes) else str(page_body))
        # ★ 눌리는 저장 단추만 본다.  disabled 는 「준비 중」이라 밝힌 것이다
        buttons = _re.findall(r"<button[^>]*>[^<]*저장[^<]*</button>", body)
        if not any("disabled" not in b for b in buttons):
            continue
        before = _table_counts(probe)
        try:
            fn(probe, acc, {"query": {}, "form": dict(SMOKE_FORM),
                            "method": POST}, path_vars={}, csrf="t")
        except (PolicyError, ValidationError):
            continue          # 규칙대로 거절한 것이다 — 저장 안 하는 게 맞다
        except Exception:                                    # noqa: BLE001
            continue          # V11-37 이 잡는다
        if _table_counts(probe) == before:
            bad.append(f"{route.view}: 저장 단추가 아무것도 안 바꾼다")
    return result(C["V11-39"], rid, 0, len(bad), not bad, bad[:8])


_PROBE: dict = {}


def _probe(conn):
    """검사용 DB 사본.  ★ 한 번만 만든다.

    실측 08-17: 검사마다 conn.backup 을 하면 231MB × 검사 수가 되어
    /tmp(여유 0.8GB)가 차고 「database or disk is full」로 V11 전체가 죽었다.
    검사가 디스크를 채우면 검사가 아니다
    """
    import sqlite3 as _sq

    got = _PROBE.get("conn")
    if got is None:
        path = os.path.join(_scratch(), "probe.db")
        got = _sq.connect(path)
        conn.backup(got)
        _PROBE["conn"] = got
    return got


def _scratch() -> str:
    """검사용 임시 자리.  ★ 끝나면 지운다 — 검사가 디스크를 채우면 안 된다.

    실측 08-15: 사본 63MB 가 실행마다 쌓여 디스크가 100% 가 됐고
    그 뒤 전 시험이 한꺼번에 깨졌다
    ★ 실측 08-17: /tmp 는 921MB tmpfs 인데 DB 가 484MB 로 자랐다.
      수집이 도는 중에 사본을 뜨자 「database or disk is full」로 죽었다.
      메모리에 뜨지 않는다 — 여유가 있는 디스크에 둔다
    """
    import atexit
    import shutil
    import tempfile

    # ★ 프로젝트 옆에 둔다.  /tmp 는 tmpfs 라 DB 사본이 안 들어간다
    base = os.path.join(ROOT, "outputs", "check-tmp")
    os.makedirs(base, exist_ok=True)
    path = tempfile.mkdtemp(prefix="cw-check-", dir=base)
    atexit.register(shutil.rmtree, path, ignore_errors=True)
    return path
