# 검사 색인 — 규격 ↔ 코드

**`python3.11 tools/build_index.py` 가 만든다. 손으로 고치지 않는다.**

검사 **496개**

| 갈래 | 몇 개 | 누가 |
|---|--:|---|
| ② 죽은 검사 — 통과도 실패도 한 적 없다 | **496** | 개발측 |
| ④ 규격에 근거가 없는 검사 | **18** | 가이드가 판단 |
| ⑤ ★ 규격에 있는데 코드에 없는 검사 | **34** | 개발측 |

★ ① 중복 · ③ 못 잡는 검사는 기계가 못 가릅니다 — 가이드·테스터 몫입니다 (개정 344).

| 코드 | 무엇 | 등급 | 소스 | 마지막 통과 | 마지막 실패 | 규격 |
|---|---|---|---|---|---|---|
| `S1` | 디렉터리 (STEP 15) | fatal | `tools/check_src.py:171` | **★ 없음** | 없음 | trace/13-pipeline.md:38 · trace/RULES.md:223 · ref/E-attach.md:62 |
| `S2` | 구조체 정의 | fatal | `tools/check_src.py:193` | **★ 없음** | 없음 | trace/13-pipeline.md:38 · trace/13-pipeline.md:41 · trace/RULES.md:223 |
| `S3` | 함수 정의 | fatal | `tools/check_src.py:214` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:11 · HEYDEALER_API.md:203 · MULTISITE_MAPPING.md:335 |
| `S4` | 테이블 DDL (STEP 28) | fatal | `tools/check_src.py:236` | **★ 없음** | 없음 | trace/13-pipeline.md:57 · trace/60-admin.md:91 · trace/60-admin.md:92 |
| `S5` | config 키 (V4-15) | fatal | `tools/check_src.py:313` | **★ 없음** | 없음 | trace/02-collect.md:22 · trace/02-collect.md:64 · trace/60-admin.md:35 |
| `S6` | 배점 검산 (불변식 ⑤) | fatal | `tools/check_src.py:348` | **★ 없음** | 없음 | ref/E-attach.md:66 · guide/03_이력.md:289 · guide/03_이력.md:855 |
| `S7` | 매직 넘버 (V4-13) | fatal | `tools/check_src.py:403` | **★ 없음** | 없음 | ref/E-attach.md:67 · guide/03_이력.md:734 · chapters/13-pipeline.md:114 |
| `S8` | 접미사 규칙 (STEP 4) | fatal | `tools/check_src.py:410` | **★ 없음** | 없음 | ref/E-attach.md:68 · guide/03_이력.md:92 · guide/03_이력.md:734 |
| `S9` | 금지 근거 (STEP 14) | fatal | `tools/check_src.py:426` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:240 · CROSS_SITE_COMPARE.md:243 · CROSS_SITE_COMPARE.md:246 |
| `S10` | 도메인 예외 (STEP 3) | fatal | `tools/check_src.py:432` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:243 · trace/02-collect.md:22 · trace/02-collect.md:64 |
| `S11` | 분석 계층 순수성 (STEP 2) | fatal | `tools/check_src.py:451` | **★ 없음** | 없음 | UI_REVIEW.md:1272 · ref/E-attach.md:71 · guide/01_시작.md:71 |
| `S12` | 축 파일 STEP 주석 | fatal | `tools/check_src.py:466` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:244 · ref/E-attach.md:72 · guide/01_시작.md:235 |
| `S13` | 본문 config 예시 대조 | fatal | `tools/check_src.py:533` | **★ 없음** | 없음 | ref/B-config.md:298 · ref/D-update.md:31 · ref/E-attach.md:73 |
| `S14` | 상수 등록·성격 (V4-17) | fatal | `tools/check_src.py:582` | **★ 없음** | 없음 | ref/E-attach.md:74 · chapters/20-verify/c-v3v4.md:208 · chapters/20-verify/c-v3v4.md:214 |
| `S14-1` | 화면에 배점을 박지 않음 (V4-17) | fatal | `tools/check_src.py:615` | **★ 없음** | 없음 | — |
| `S15` | 계층 의존 (STEP 15) | fatal | `tools/check_src.py:493` | **★ 없음** | 없음 | ref/E-attach.md:75 · guide/03_이력.md:120 · chapters/10-collect/00-intro.md:226 |
| `S16` | 검증 코드 대조 | fatal | `tools/check_src.py:667` | **★ 없음** | 없음 | ref/E-attach.md:76 · ref/E-attach.md:217 · guide/03_이력.md:157 |
| `S23` | 실행 환경 (Python 3.11+) | fatal | `tools/check_src.py:674` | **★ 없음** | 없음 | trace/00-standard.md:21 · trace/00-standard.md:22 · trace/RULES.md:81 |
| `S24` | 시험 격리 (운영 DB 미사용) | fatal | `tools/check_src.py:693` | **★ 없음** | 없음 | trace/00-standard.md:29 · trace/00-standard.md:30 · trace/00-standard.md:31 |
| `S25` | 형상 관리 (미커밋 없음) | fatal | `tools/check_src.py:713` | **★ 없음** | 없음 | trace/RULES.md:87 · trace/RULES.md:88 · trace/RULES.md:89 |
| `S26` | 작업 기록 (6절 · 이름 규칙) | fatal | `tools/check_src.py:741` | **★ 없음** | 없음 | trace/00-standard.md:53 · trace/00-standard.md:54 · trace/00-standard.md:55 |
| `S27` | 기능마다 화면 (CLI 는 완성이 아니다) | fatal | `tools/check_src.py:777` | **★ 없음** | 없음 | trace/00-standard.md:34 · trace/00-standard.md:38 · trace/RULES.md:85 |
| `S28` | 검사 색인 (규격 ↔ 코드) | fatal | `tools/check_src.py:800` | **★ 없음** | 없음 | INDEX.md:14 · SCHEMA.md:7 · trace/00-standard.md:78 |
| `S29-0` | 가벼운 점검 (4시간 · 실제로 돎) | fatal | `tools/check_src.py:831` | **★ 없음** | 없음 | trace/00-standard.md:110 · trace/00-standard.md:111 · trace/00-standard.md:112 |
| `S29-4` | 점검이 찾은 fatal 을 고침 | fatal | `tools/check_src.py:854` | **★ 없음** | 없음 | trace/00-standard.md:109 · trace/00-standard.md:110 · trace/00-standard.md:111 |
| `S34-1` | 표의 규격이 실재 | fatal | `tools/check_src.py:936` | **★ 없음** | 없음 | trace/00-standard.md:231 · trace/00-standard.md:232 · trace/00-standard.md:234 |
| `S34-2` | 표의 소스·검사가 실재 | fatal | `tools/check_src.py:937` | **★ 없음** | 없음 | trace/00-standard.md:231 · trace/00-standard.md:232 · trace/00-standard.md:234 |
| `S34-3` | 추적표 빈 칸을 센다 | fatal | `tools/check_src.py:888` | **★ 없음** | 없음 | guide/03_이력.md:427 · chapters/00-standard.md:1540 · chapters/00-standard.md:1830 |
| `S34-4` | 규격이 표에 있음 | fatal | `tools/check_src.py:1027` | **★ 없음** | 없음 | guide/03_이력.md:368 · guide/03_이력.md:423 · chapters/00-standard.md:1541 |
| `S35-1` | 자기 칸만 고침 | fatal | `tools/check_src.py:1112` | **★ 없음** | 없음 | trace/00-standard.md:235 · trace/00-standard.md:236 · trace/00-standard.md:237 |
| `S36-1` | 「정식 서비스 착수」 목록이 있음 | fatal | `tools/check_src.py:1129` | **★ 없음** | 없음 | trace/00-standard.md:250 · trace/00-standard.md:251 · trace/00-standard.md:252 |
| `S37-1` | 파는 쪽 개념이 안 남아 있음 | fatal | `tools/check_src.py:1147` | **★ 없음** | 없음 | trace/00-standard.md:260 · trace/RULES.md:123 · trace/RULES.md:124 |
| `S38-4` | 상태가 세 칸에서 유도한 값과 같음 | fatal | `tools/check_src.py:972` | **★ 없음** | 없음 | guide/03_이력.md:425 · chapters/00-standard.md:1817 |
| `S38-5` | 「!」·「?」 가 도구 실행 뒤에도 남음 | fatal | `tools/check_src.py:974` | **★ 없음** | 없음 | guide/03_이력.md:425 · chapters/00-standard.md:1818 |
| `S39-1` | R 마다 층이 적혀 있음 | fatal | `tools/check_src.py:1014` | **★ 없음** | 없음 | guide/03_이력.md:389 · guide/03_이력.md:417 · chapters/00-standard.md:2107 |
| `S39-2` | 화면 층이 아닌데 「화면 없음」이 아님 | fatal | `tools/check_src.py:1016` | **★ 없음** | 없음 | guide/03_이력.md:389 · chapters/00-standard.md:2108 |
| `S43-2` | 규격의 축 id 가 config 에 있는가 | fatal | `validate/v0_guide.py:32` | **★ 없음** | 없음 | guide/03_이력.md:510 · guide/03_이력.md:512 · guide/03_이력.md:517 |
| `S43-2b` | config 축 id 가 규격 이름인가 | fatal | `validate/v0_guide.py:228` | **★ 없음** | 없음 | guide/00_버전.md:116 · guide/03_이력.md:519 · guide/03_이력.md:522 |
| `S43-2c` | HDA 가 저장소에 없는가 | fatal | `validate/v0_guide.py:254` | **★ 없음** | 없음 | guide/00_버전.md:115 · guide/01_요구사항.md:50 · guide/03_이력.md:520 |
| `S43-3` | 버전이 이력 마지막과 같은가 | fatal | `validate/v0_guide.py:490` | **★ 없음** | 없음 | guide/03_이력.md:510 · guide/03_이력.md:518 · guide/03_이력.md:553 |
| `S44-1` | 가리키는 명령서가 실제로 있는가 | fatal | `validate/v0_guide.py:171` | **★ 없음** | 없음 | guide/00_버전.md:118 · guide/03_이력.md:456 · guide/03_이력.md:463 |
| `S44-2` | 명령서가 하나뿐인가 | fatal | `validate/v0_guide.py:213` | **★ 없음** | 없음 | guide/03_이력.md:456 · guide/03_이력.md:463 · guide/03_이력.md:510 |
| `S44-3` | 규격을 명령서가 가리키는가 | fatal | `validate/v0_guide.py:452` | **★ 없음** | 없음 | guide/03_이력.md:555 · guide/03_이력.md:556 · guide/03_이력.md:566 |
| `S44-4` | 명령서에 수집 범위가 있는가 | fatal | `validate/v0_guide.py:70` | **★ 없음** | 없음 | guide/03_이력.md:557 · guide/03_이력.md:558 · guide/03_이력.md:891 |
| `S44-5` | 명령서이 사이트를 한 가지로 적는가 | fatal | `validate/v0_guide.py:102` | **★ 없음** | 없음 | KCAR_API.md:436 · guide/03_이력.md:557 · guide/03_이력.md:803 |
| `S45-1` | f-table 절 제목과 표가 같은가 | fatal | `validate/v0_guide.py:135` | **★ 없음** | 없음 | guide/03_이력.md:460 · guide/03_이력.md:501 · guide/03_이력.md:510 |
| `S45-2` | 시안에 옛 배점·분모가 없는가 | fatal | `validate/v0_guide.py:431` | **★ 없음** | 없음 | guide/00_버전.md:113 · guide/00_버전.md:114 · guide/03_이력.md:521 |
| `S45-3` | 규격에 옛 총점이 없는가 | fatal | `validate/v0_guide.py:361` | **★ 없음** | 없음 | guide/00_버전.md:110 · guide/00_버전.md:112 · guide/03_이력.md:523 |
| `S45-4` | 배점표가 config 에서 생성한 것과 같은가 | fatal | `validate/v0_guide.py:346` | **★ 없음** | 없음 | guide/00_버전.md:108 · guide/03_이력.md:527 |
| `S45-5` | 규격이 배점을 손으로 적지 않는가 | fatal | `validate/v0_guide.py:308` | **★ 없음** | 없음 | guide/00_버전.md:107 · guide/03_이력.md:528 · guide/03_이력.md:553 |
| `S46-21` | 시안 한 파일에 화면이 하나인가 | fatal | `validate/v0_guide.py:546` | **★ 없음** | 없음 | UI_REVIEW.md:421 · guide/01_요구사항.md:61 · guide/03_이력.md:644 |
| `S46-22` | 시안 절 차례가 화면과 같은가 | fatal | `validate/v0_guide.py:571` | **★ 없음** | 없음 | UI_REVIEW.md:423 · UI_REVIEW.md:731 · UI_REVIEW.md:836 |
| `S46-23` | 빈 site_query 가 없는가 | fatal | `validate/v0_guide.py:646` | **★ 없음** | 없음 | guide/01_요구사항.md:58 · guide/01_요구사항.md:88 · guide/01_요구사항.md:119 |
| `S46-24` | facet 미확인 차종이 없는가 | warn | `validate/v0_guide.py:661` | **★ 없음** | 없음 | guide/03_이력.md:647 · guide/03_이력.md:669 · guide/03_이력.md:678 |
| `S46-30` | INDEX 가 docs 를 다 가리키는가 | warn | `validate/v0_guide.py:678` | **★ 없음** | 없음 | guide/03_이력.md:661 |
| `S46-31` | 규격이 있는 사이트가 config 에 있는가 | fatal | `validate/v0_guide.py:717` | **★ 없음** | 없음 | BMW_BPS_API.md:7 · BOBAEDREAM_API.md:7 · ENCAR_API.md:7 |
| `S46-32` | 생성물이 최신인가 | fatal | `validate/v0_guide.py:738` | **★ 없음** | 없음 | guide/01_요구사항.md:65 · guide/03_이력.md:672 · guide/03_이력.md:677 |
| `S46-36` | 폐기된 요구가 규격에 안 살아 있는가 | fatal | `validate/v0_guide.py:819` | **★ 없음** | 없음 | HYUNDAI_CERTIFIED_API.md:209 · trace/00_공통머리.md:44 · guide/01_요구사항.md:25 |
| `S46-40` | 「진행」인 요구의 문서가 바뀌었는가 | warn | `validate/v0_guide.py:847` | **★ 없음** | 없음 | guide/01_요구사항.md:69 · guide/03_이력.md:682 · guide/06_오판대장.md:181 |
| `S46-41` | 사이트 status 가 규격의 셋 안인가 | fatal | `validate/v0_guide.py:878` | **★ 없음** | 없음 | guide/06_오판대장.md:182 |
| `S46-45` | 제원이 목록에 안 나오는가 | fatal | `validate/v0_guide.py:925` | **★ 없음** | 없음 | UI_REVIEW.md:517 · guide/01_요구사항.md:77 · guide/03_이력.md:691 |
| `S46-46` | 금지 제원 열 항목이 화면에 없는가 | fatal | `validate/v0_guide.py:945` | **★ 없음** | 없음 | UI_REVIEW.md:518 · guide/01_요구사항.md:77 · guide/03_이력.md:691 |
| `S46-54` | 짝 중 등급이 두 칸 갈린 것 | warn | `validate/v0_guide.py:2053` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:7 · CROSS_SITE_COMPARE.md:254 · CROSS_SITE_COMPARE.md:422 |
| `S46-55` | 짝 중 값이 30% 갈린 것 | warn | `validate/v0_guide.py:2078` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:7 · CROSS_SITE_COMPARE.md:255 |
| `S46-56` | 짝 중 사고 판정이 갈린 것 | warn | `validate/v0_guide.py:2104` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:7 · CROSS_SITE_COMPARE.md:256 |
| `S46-65` | 판본이 하루 넘게 오래되지 않았는가 | fatal | `validate/v0_guide.py:1010` | **★ 없음** | 없음 | guide/01_요구사항.md:107 · guide/03_이력.md:745 · guide/03_이력.md:746 |
| `S46-66` | 화면이 낸 링크가 인코딩돼 있는가 | fatal | `validate/v0_guide.py:971` | **★ 없음** | 없음 | UI_REVIEW.md:896 · guide/01_요구사항.md:108 · guide/03_이력.md:747 |
| `S46-67` | 시안 이름이 app.css 와 안 겹치는가 | fatal | `validate/v0_guide.py:1057` | **★ 없음** | 없음 | UI_REVIEW.md:1307 · UI_REVIEW.md:1605 · guide/03_이력.md:749 |
| `S46-68` | 관심이 모바일 기준 카드인가 | fatal | `validate/v0_guide.py:1120` | **★ 없음** | 없음 | UI_REVIEW.md:999 · guide/01_요구사항.md:111 · guide/03_이력.md:754 |
| `S46-74` | 한 쪽 장 수가 규격과 같은가 | fatal | `validate/v0_guide.py:1174` | **★ 없음** | 없음 | UI_REVIEW.md:1033 · guide/01_요구사항.md:114 · guide/03_이력.md:761 |
| `S46-75` | v4m 여덟 장 공통 규칙 | fatal | `validate/v0_guide.py:1220` | **★ 없음** | 없음 | guide/01_요구사항.md:116 · guide/03_이력.md:766 · guide/06_오판대장.md:218 |
| `S46-76` | 수집기가 원문을 남기는가 | fatal | `validate/v0_guide.py:1260` | **★ 없음** | 없음 | guide/01_요구사항.md:118 · guide/03_이력.md:770 · guide/03_이력.md:771 |
| `S46-77` | KB 는 우리 20종만 받는가 | fatal | `validate/v0_guide.py:1770` | **★ 없음** | 없음 | — |
| `S46-78` | 엔카 전용 경로가 좁혀 있는가 | fatal | `validate/v0_guide.py:1825` | **★ 없음** | 없음 | guide/03_이력.md:771 |
| `S46-87` | 부른 주소가 그 매물의 사이트인가 | fatal | `validate/v0_guide.py:1867` | **★ 없음** | 없음 | guide/03_이력.md:772 · guide/03_이력.md:773 · guide/03_이력.md:855 |
| `S46-88` | 엔카가 막히면 화면이 까닭을 말하는가 | fatal | `validate/v0_guide.py:1936` | **★ 없음** | 없음 | guide/03_이력.md:773 |
| `S46-90` | 근거가 절반도 없는데 등급을 매기지 않는가 | fatal | `validate/v0_guide.py:2144` | **★ 없음** | 없음 | UI_REVIEW.md:1082 · guide/03_이력.md:780 |
| `S46-91` | 받은 원문이 저장까지 갔는가 | fatal | `validate/v0_guide.py:2251` | **★ 없음** | 없음 | guide/03_이력.md:781 · guide/06_오판대장.md:225 |
| `S46-92` | 브라우저 수집이 0건을 받았는가 | warn | `validate/v0_guide.py:2990` | **★ 없음** | 없음 | guide/03_이력.md:783 · guide/03_이력.md:784 |
| `S46-94` | 원문 문이 그 매물의 사이트로 가는가 | fatal | `validate/v0_guide.py:2207` | **★ 없음** | 없음 | guide/03_이력.md:787 · guide/06_오판대장.md:228 |
| `S46-95` | 배포된 화면이 다 열리는가 | fatal | `validate/v0_guide.py:2894` | **★ 없음** | 없음 | guide/03_이력.md:788 · guide/03_이력.md:789 · guide/03_이력.md:792 |
| `S46-96` | 사이트가 파는 차종인데 코드가 없는가 | warn | `validate/v0_guide.py:2950` | **★ 없음** | 없음 | guide/03_이력.md:791 · guide/03_이력.md:860 · guide/04_질의.md:718 |
| `S46-97` | 원문이 source_id 로 매물에 이어지는가 | fatal | `validate/v0_guide.py:2323` | **★ 없음** | 없음 | guide/03_이력.md:792 · guide/03_이력.md:879 · guide/06_오판대장.md:263 |
| `S46-98` | 시안의 낱말이 화면에 있는가 | fatal | `validate/v0_guide.py:2788` | **★ 없음** | 없음 | UI_REVIEW.md:1880 · guide/03_이력.md:793 · guide/03_이력.md:794 |
| `S46-99` | 로그인하면 관심·관리가 열리는가 | fatal | `validate/v0_guide.py:2391` | **★ 없음** | 없음 | guide/03_이력.md:794 · guide/03_이력.md:879 · guide/03_이력.md:1009 |
| `S46-100` | 시안의 낱말 차례가 화면과 같은가 | fatal | `validate/v0_guide.py:2558` | **★ 없음** | 없음 | guide/03_이력.md:804 · guide/03_이력.md:879 · guide/03_이력.md:1009 |
| `S46-102` | 「전기만」에 전기 아닌 것이 없는가 | fatal | `validate/v0_guide.py:2695` | **★ 없음** | 없음 | UI_REVIEW.md:1133 · guide/03_이력.md:814 · guide/06_오판대장.md:239 |
| `S46-103` | 시안의 크기·자리 값을 담았는가 | fatal | `validate/v0_guide.py:2747` | **★ 없음** | 없음 | guide/03_이력.md:819 · guide/03_이력.md:847 · guide/06_오판대장.md:241 |
| `S46-115` | 시키는 화면이 스스로 안 바뀌는가 | fatal | `validate/v0_guide.py:1288` | **★ 없음** | 없음 | UI_REVIEW.md:1338 · guide/03_이력.md:850 |
| `S46-116` | 사유에 쉬운 말이 있는가 | fatal | `validate/v0_guide.py:1410` | **★ 없음** | 없음 | UI_REVIEW.md:1374 · guide/03_이력.md:850 |
| `S46-117` | 목록을 받는 수집기가 팔린 차를 거르는가 | fatal | `validate/v0_guide.py:1721` | **★ 없음** | 없음 | KCAR_API.md:151 · guide/03_이력.md:851 · guide/03_이력.md:855 |
| `S46-118` | 하트가 자기 카드 안에 앉는가 | fatal | `validate/v0_guide.py:1348` | **★ 없음** | 없음 | UI_REVIEW.md:1429 · guide/03_이력.md:852 |
| `S46-120` | 등록부의 감사 열쇠가 목록 열쇠와 같은가 | fatal | `validate/v0_guide.py:1437` | **★ 없음** | 없음 | guide/03_이력.md:854 |
| `S46-121` | 머리띠 규칙이 한 곳에만 있는가 | fatal | `validate/v0_guide.py:1388` | **★ 없음** | 없음 | UI_REVIEW.md:1510 · guide/03_이력.md:862 · guide/09_설계뒤에할것_20260829.md:102 |
| `S46-122` | 머리·발이 한 곳에만 있는가 | fatal | `validate/v0_guide.py:1515` | **★ 없음** | 없음 | UI_REVIEW.md:1545 · guide/03_이력.md:863 · guide/09_설계뒤에할것_20260829.md:101 |
| `S46-123` | 토스 표에 없는 색이 없는가 | fatal | `validate/v0_guide.py:1473` | **★ 없음** | 없음 | UI_REVIEW.md:1609 · guide/03_이력.md:863 |
| `S46-124` | DB 를 PRAGMA 없이 열지 않는가 | fatal | `validate/v0_guide.py:1651` | **★ 없음** | 없음 | VOLVO_SELEKT_API.md:513 · guide/03_이력.md:866 |
| `S46-125` | 고른 정렬 축이 정말 먹는가 | fatal | `validate/v0_guide.py:1317` | **★ 없음** | 없음 | guide/03_이력.md:868 |
| `S46-126` | 수집기가 통신·sleep 을 트랜잭션 밖에서 하는가 | fatal | `validate/v0_guide.py:1687` | **★ 없음** | 없음 | guide/03_이력.md:870 · guide/03_이력.md:935 · guide/06_오판대장.md:282 |
| `S46-127` | 수집기마다 화면이나 타이머가 있는가 | fatal | `validate/v0_guide.py:1603` | **★ 없음** | 없음 | guide/06_오판대장.md:258 · guide/07_밀린일대장.md:74 |
| `S46-128` | 묶어 쓰는 단계가 다른 쓰기에 창을 주는가 | fatal | `validate/v0_guide.py:1559` | **★ 없음** | 없음 | guide/06_오판대장.md:259 |
| `S46-129` | 표의 합이 맞는가 | fatal | `validate/v0_guide.py:3240` | **★ 없음** | 없음 | guide/03_이력.md:977 · guide/03_이력.md:987 · guide/06_오판대장.md:260 |
| `S46-130` | 합계표가 문서마다 하나인가 | fatal | `validate/v0_guide.py:3496` | **★ 없음** | 없음 | guide/03_이력.md:1001 · guide/06_오판대장.md:261 |
| `S46-131` | 「쪽넘김이 없다」에 실측이 있는가 | fatal | `validate/v0_guide.py:3380` | **★ 없음** | 없음 | guide/06_오판대장.md:262 · guide/07_밀린일대장.md:39 |
| `S46-132` | 인계문이 다시 재라고 적는가 | fatal | `validate/v0_guide.py:3272` | **★ 없음** | 없음 | guide/06_오판대장.md:263 |
| `S46-133` | 검사 구멍이 밀린일에 있는가 | fatal | `validate/v0_guide.py:3635` | **★ 없음** | 없음 | guide/06_오판대장.md:264 |
| `S46-134` | 질의와 규격이 어긋나지 않는가 | fatal | `validate/v0_guide.py:3513` | **★ 없음** | 없음 | guide/06_오판대장.md:265 |
| `S46-135` | 일반화에 표본이 있는가 | fatal | `validate/v0_guide.py:3402` | **★ 없음** | 없음 | guide/06_오판대장.md:266 |
| `S46-136` | 규격의 warn 수가 지금 값과 같은가 | fatal | `validate/v0_guide.py:3653` | **★ 없음** | 없음 | guide/06_오판대장.md:267 · guide/07_밀린일대장.md:40 |
| `S46-137` | 질의 열쇠를 읽는 코드가 있는가 | fatal | `validate/v0_guide.py:3675` | **★ 없음** | 없음 | guide/06_오판대장.md:268 |
| `S46-138` | 「전량」에 세는 법이 있는가 | fatal | `validate/v0_guide.py:3419` | **★ 없음** | 없음 | guide/03_이력.md:999 · guide/06_오판대장.md:269 |
| `S46-139` | 「칸이 비었다」에 전수가 있는가 | fatal | `validate/v0_guide.py:3704` | **★ 없음** | 없음 | guide/06_오판대장.md:270 |
| `S46-140` | 쓰는 호스트가 robots 문서에 있는가 | fatal | `validate/v0_guide.py:3286` | **★ 없음** | 없음 | guide/06_오판대장.md:271 · guide/07_밀린일대장.md:39 |
| `S46-141` | 거르개 판정에 실측이 있는가 | fatal | `validate/v0_guide.py:3539` | **★ 없음** | 없음 | guide/06_오판대장.md:272 |
| `S46-142` | 「N 사이트」가 config 와 같은가 | fatal | `validate/v0_guide.py:3305` | **★ 없음** | 없음 | guide/06_오판대장.md:273 · guide/07_밀린일대장.md:40 |
| `S46-143` | 마스터께 올릴 것이 세어졌는가 | fatal | `validate/v0_guide.py:3556` | **★ 없음** | 없음 | guide/03_이력.md:1001 · guide/06_오판대장.md:274 |
| `S46-144` | 「비었다」가 ⑤·⑥·⑦ 로 갈렸는가 | fatal | `validate/v0_guide.py:3785` | **★ 없음** | 없음 | guide/03_이력.md:983 · guide/06_오판대장.md:275 · guide/12_남은것_20260829.md:15 |
| `S46-145` | 마스터께 드리는 표에 수의 뜻이 있는가 | fatal | `validate/v0_guide.py:3138` | **★ 없음** | 없음 | guide/03_이력.md:985 · guide/06_오판대장.md:276 |
| `S46-146` | 「안 준다」를 쓰며 파서를 봤는가 | fatal | `validate/v0_guide.py:3336` | **★ 없음** | 없음 | guide/03_이력.md:997 · guide/06_오판대장.md:277 |
| `S46-147` | 「안 준다」의 표본이 열 건인가 | fatal | `validate/v0_guide.py:3591` | **★ 없음** | 없음 | guide/05_가이드역할.md:1500 · guide/06_오판대장.md:278 · evidence/absence_20260829.md:6 |
| `S46-148` | 「축이 빈다」가 칼럼·파서를 짚는가 | fatal | `validate/v0_guide.py:3721` | **★ 없음** | 없음 | guide/03_이력.md:1001 · guide/06_오판대장.md:279 |
| `S46-149` | 자백이 닫혔는가 | fatal | `validate/v0_guide.py:3443` | **★ 없음** | 없음 | guide/06_오판대장.md:280 · guide/07_밀린일대장.md:40 |
| `S46-150` | 규격의 칼럼이 DDL 에 있는가 | fatal | `validate/v0_guide.py:3613` | **★ 없음** | 없음 | guide/06_오판대장.md:281 |
| `S46-152` | 마지막 개발 회차를 읽었는가 | fatal | `validate/v0_guide.py:3739` | **★ 없음** | 없음 | guide/03_이력.md:991 · guide/03_이력.md:1007 · guide/03_이력.md:1009 |
| `S46-153` | 「마스터 몫」이 진짜 마스터 몫인가 | fatal | `validate/v0_guide.py:3802` | **★ 없음** | 없음 | guide/03_이력.md:1007 · guide/03_이력.md:1009 · guide/06_오판대장.md:284 |
| `S46-154` | 마스터 말씀이 요구 추적표에 있는가 | fatal | `validate/v0_guide.py:3358` | **★ 없음** | 없음 | guide/01_요구사항.md:49 · guide/03_이력.md:1005 · guide/06_오판대장.md:285 |
| `S46-155` | 화면 규격마다 시안이 있는가 | fatal | `validate/v0_guide.py:3167` | **★ 없음** | 없음 | guide/03_이력.md:985 · guide/03_이력.md:1003 · guide/06_오판대장.md:286 |
| `S46-156` | 개발측 물음의 답이 규격에 있는가 | fatal | `validate/v0_guide.py:3470` | **★ 없음** | 없음 | guide/06_오판대장.md:287 |
| `S46-157` | 성능 판정에 시간이 있는가 | fatal | `validate/v0_guide.py:3834` | **★ 없음** | 없음 | guide/06_오판대장.md:288 |
| `S46-158` | 용량 판정에 수가 있는가 | fatal | `validate/v0_guide.py:3852` | **★ 없음** | 없음 | guide/06_오판대장.md:289 |
| `S46-159` | 설계도가 할 수 있는 것만 시키는가 | fatal | `validate/v0_guide.py:3766` | **★ 없음** | 없음 | guide/06_오판대장.md:290 · guide/07_밀린일대장.md:40 |
| `S46-160` | 전기차 누유가 만점·분모 910 인가 | fatal | `validate/v0_guide.py:3870` | **★ 없음** | 없음 | guide/03_이력.md:971 · guide/06_오판대장.md:291 · guide/06_오판대장.md:292 |
| `S46-161` | 「사이트가 안 준다」에 증거가 있는가 | fatal | `validate/v0_guide.py:3059` | **★ 없음** | 없음 | guide/03_이력.md:975 · guide/03_이력.md:977 · guide/03_이력.md:979 |
| `S46-162` | 오판이 약속한 검사가 실제로 있는가 | fatal | `validate/v0_guide.py:3108` | **★ 없음** | 없음 | guide/03_이력.md:977 · guide/03_이력.md:979 · guide/03_이력.md:985 |
| `S46-163` | 시안마다 라우팅 표에 주소가 있는가 | fatal | `validate/v0_guide.py:3200` | **★ 없음** | 없음 | guide/03_이력.md:985 · guide/03_이력.md:1003 · guide/06_오판대장.md:294 |
| `S46-164` | 개발 회차의 「마스터 몫」에 답을 냈는가 | fatal | `validate/v0_guide.py:3887` | **★ 없음** | 없음 | guide/03_이력.md:991 · guide/06_오판대장.md:295 · guide/14_누가할것_20260829.md:39 |
| `S46-165` | 「못 잰다」가 진짜인가 | fatal | `validate/v0_guide.py:3915` | **★ 없음** | 없음 | guide/03_이력.md:1011 · guide/06_오판대장.md:296 · guide/06_오판대장.md:297 |
| `S46-166` | 마스터 확정이 장 규격에 닿았는가 | fatal | `validate/v0_guide.py:3953` | **★ 없음** | 없음 | ARCHITECTURE_20260830.md:8 · guide/03_이력.md:1017 · guide/06_오판대장.md:298 |
| `S46-168` | 검사가 예외를 수로 내는가 | fatal | `validate/v0_guide.py:3983` | **★ 없음** | 없음 | guide/03_이력.md:1037 · guide/06_오판대장.md:299 |
| `V0-01` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:26 · guide/03_이력.md:349 · guide/03_이력.md:413 |
| `V0-02` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:56 · guide/03_이력.md:666 |
| `V0-03` | — | — | **★ 코드에 없다** | — | — | guide/00_버전.md:78 · guide/03_이력.md:349 · guide/03_이력.md:413 |
| `V1-01` | expected == requested + not_requested | run | `validate/v1_collect.py:34` | **★ 없음** | 없음 | trace/02-collect.md:21 · chapters/00-standard.md:362 · chapters/13-pipeline.md:651 |
| `V1-02` | not_requested == 0 | run | `validate/v1_collect.py:37` | **★ 없음** | 없음 | trace/02-collect.md:37 · chapters/20-verify/b-v1v2.md:14 |
| `V1-03` | requested == ok+empty+not_found+error | run | `validate/v1_collect.py:40` | **★ 없음** | 없음 | chapters/20-verify/00-intro.md:22 · chapters/20-verify/b-v1v2.md:15 · chapters/20-verify/d-v5.md:221 |
| `V1-04` | 형식 검증 거부 0 | run | `validate/v1_collect.py:43` | **★ 없음** | 없음 | chapters/60-admin/b-ops.md:215 · chapters/20-verify/b-v1v2.md:16 · chapters/20-verify/b-v1v2.md:95 |
| `V1-05` | raw_response 신규 == 응답 합 | run | `validate/v1_collect.py:46` | **★ 없음** | 없음 | trace/02-collect.md:61 · guide/03_이력.md:59 · chapters/20-verify/b-v1v2.md:17 |
| `V1-06` | 차종별 ok > 0 | target | `validate/v1_collect.py:49` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:23 |
| `V1-07` | 매물별 엔드포인트 4종 상태 존재 | listing | `validate/v1_collect.py:52` | **★ 없음** | 없음 | chapters/20-verify/00-intro.md:125 · chapters/20-verify/b-v1v2.md:24 · chapters/10-collect/d-record.md:551 |
| `V1-08` | 동일 코드 실패율 100% 인 엔드포인트 없음 | run | `validate/v1_collect.py:55` | **★ 없음** | 없음 | guide/03_이력.md:60 · chapters/13-pipeline.md:544 · chapters/20-verify/00-intro.md:126 |
| `V1-08b` | 엔드포인트별 전량 404 없음 | run | `validate/v1_collect.py:58` | **★ 없음** | 없음 | guide/03_이력.md:134 · chapters/20-verify/b-v1v2.md:92 · chapters/10-collect/d-record.md:533 |
| `V1-09` | 시간대별 실패율 상승 없음 | run | `validate/v1_collect.py:162` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:40 |
| `V1-10` | site_query 키가 전부 q 에 반영됨 | run | `validate/v1_collect.py:159` | **★ 없음** | 없음 | guide/03_이력.md:124 · chapters/20-verify/b-v1v2.md:41 · chapters/10-collect/a-endpoint.md:177 |
| `V1-11` | 예외로 종료된 실행이 없음 | run | `validate/v1_collect.py:62` | **★ 없음** | 없음 | trace/60-admin.md:59 · guide/03_이력.md:129 · chapters/60-admin/b-ops.md:165 |
| `V1-12` | 연속 실패 중단 시 ResumePoint 가 남음 | run | `validate/v1_collect.py:155` | **★ 없음** | 없음 | guide/03_이력.md:127 · chapters/20-verify/b-v1v2.md:43 |
| `V1-13` | 껍데기를 거친 실행과 직접 실행의 인자가 같음 | run | `validate/v1_collect.py:133` | **★ 없음** | 없음 | trace/13-pipeline.md:23 · trace/13-pipeline.md:24 · guide/01_시작.md:124 |
| `V1-14` | diagnosis 호출 대상이 encarDiagnosis == 0 으로 좁혀짐 | run | `validate/v1_collect.py:65` | **★ 없음** | 없음 | trace/13-pipeline.md:31 · trace/RULES.md:222 · guide/03_이력.md:182 |
| `V1-15` | expected == 요청 대상 수 (skipped 제외) | run | `validate/v1_collect.py:150` | **★ 없음** | 없음 | trace/13-pipeline.md:31 · trace/13-pipeline.md:32 · trace/RULES.md:222 |
| `V1-16` | 이번 run_id 밖의 행을 보지 않음 | run | `validate/v1_collect.py:145` | **★ 없음** | 없음 | trace/20-verify.md:21 · trace/20-verify.md:22 · trace/20-verify.md:23 |
| `V1-17` | diagnosis 가 detail 뒤에 있음 | run | `validate/v1_collect.py:138` | **★ 없음** | 없음 | guide/03_이력.md:224 · chapters/20-verify/b-v1v2.md:48 · chapters/10-collect/a-endpoint.md:160 |
| `V1-18` | 빈 DB 에서도 검사가 돈다 | run | `validate/v1_collect.py:142` | **★ 없음** | 없음 | trace/13-pipeline.md:23 · guide/03_이력.md:222 · chapters/13-pipeline.md:141 |
| `V1-19` | 이번 실행이 저장한 원문에 run_id 가 있음 | run | `validate/v1_collect.py:128` | **★ 없음** | 없음 | — |
| `V1-20` | 카탈로그를 모델당 1회만 받음 | run | `validate/v1_collect.py:123` | **★ 없음** | 없음 | — |
| `V1-21` | 받아 두고 안 펼쳐진 원문이 없음 | run | `validate/v1_collect.py:113` | **★ 없음** | 없음 | trace/02-collect.md:62 · trace/13-pipeline.md:40 · trace/13-pipeline.md:41 |
| `V1-22` | — | — | **★ 코드에 없다** | — | — | trace/05-score.md:47 · guide/01_요구사항.md:159 · guide/01_요구사항.md:275 |
| `V1-23` | 필요한 조합 대비 받은 카탈로그 비율 | run | `validate/v1_collect.py:81` | **★ 없음** | 없음 | trace/02-collect.md:44 · guide/02_결함대장.md:235 · guide/02_결함대장.md:245 |
| `V1-24` | 받은 카탈로그가 매물과 이어짐 | run | `validate/v1_collect.py:108` | **★ 없음** | 없음 | guide/02_결함대장.md:235 · guide/02_결함대장.md:245 · guide/03_이력.md:346 |
| `V1-25` | ok 로 저장된 원문이 온전한가 | run | `validate/v1_collect.py:72` | **★ 없음** | 없음 | — |
| `V1-26` | 판정 축이 통째로 비지 않음 | run | `validate/v1_collect.py:101` | **★ 없음** | 없음 | guide/03_이력.md:437 |
| `V1-27` | 확인 안 됨을 ①②③④ 로 가른 표가 있음 | run | `validate/v1_collect.py:88` | **★ 없음** | 없음 | guide/03_이력.md:454 · chapters/30-score/f-table.md:504 |
| `V1-28` | ② ③ 건수가 지난번보다 안 늘었음 | run | `validate/v1_collect.py:95` | **★ 없음** | 없음 | guide/03_이력.md:454 · chapters/30-score/f-table.md:505 |
| `V2-01` | ok 원문 수 == CORE 행 수 | run | `validate/v2_load.py:26` | **★ 없음** | 없음 | ARCHITECTURE_20260830.md:8 · ARCHITECTURE_20260830.md:12 · ARCHITECTURE_20260830.md:45 |
| `V2-02` | 필수 컬럼 NOT NULL 위반 없음 | run | `validate/v2_load.py:29` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:106 |
| `V2-03` | — | — | **★ 코드에 없다** | — | — | trace/RULES.md:186 · chapters/11-store/a-key.md:377 · chapters/20-verify/b-v1v2.md:107 |
| `V2-04` | status 열거값 위반 없음 | run | `validate/v2_load.py:32` | **★ 없음** | 없음 | trace/RULES.md:189 · chapters/20-verify/b-v1v2.md:108 |
| `V2-05` | 단위 — 가격이 만원 단위로 남아 있지 않은가 | run | `validate/v2_load.py:35` | **★ 없음** | 없음 | trace/60-admin.md:52 · trace/RULES.md:149 · trace/RULES.md:190 |
| `V2-06` | 빈 컨테이너가 NULL 로 저장되지 않았는가 | run | `validate/v2_load.py:38` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:110 · chapters/20-verify/b-v1v2.md:148 · chapters/20-verify/b-v1v2.md:151 |
| `V2-07` | 전건 NULL 컬럼 | run | `validate/v2_load.py:41` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:111 · chapters/20-verify/b-v1v2.md:148 · chapters/20-verify/b-v1v2.md:152 |
| `V2-08` | 값 종류 1인 컬럼 | run | `validate/v2_load.py:121` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:112 · chapters/20-verify/b-v1v2.md:148 · chapters/20-verify/b-v1v2.md:153 |
| `V2-09` | core_pii 를 직접 조회하는 코드 없음 | run | `validate/v2_load.py:44` | **★ 없음** | 없음 | SCHEMA.md:37 · guide/03_이력.md:96 · chapters/11-store/b-core.md:488 |
| `V2-10` | core_listing 에 plate_no · dealer_name · phone · address 없음 | run | `validate/v2_load.py:47` | **★ 없음** | 없음 | guide/03_이력.md:96 · chapters/20-verify/b-v1v2.md:128 |
| `V2-10b` | core_* 에 마스킹 컬럼 없음 | run | `validate/v2_load.py:57` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:129 |
| `V2-11` | plate_hash 가 전건 16자 hex | run | `validate/v2_load.py:118` | **★ 없음** | 없음 | DEDUP_CROSS_SITE.md:26 · trace/11-store.md:50 · chapters/11-store/b-core.md:446 |
| `V2-12` | secrets/plate_hmac.key 가 버전 관리 밖 | run | `validate/v2_load.py:53` | **★ 없음** | 없음 | chapters/60-admin/00-intro.md:181 · chapters/20-verify/b-v1v2.md:131 |
| `V2-13` | core_record 에 record_plate_no 원본 없음 | run | `validate/v2_load.py:80` | **★ 없음** | 없음 | chapters/11-store/b-core.md:643 · chapters/20-verify/b-v1v2.md:132 |
| `V2-14` | 참조되는 5종 PK 가 단일 INTEGER | run | `validate/v2_load.py:109` | **★ 없음** | 없음 | chapters/11-store/a-key.md:189 · chapters/11-store/a-key.md:529 · chapters/60-admin/00-intro.md:147 |
| `V2-15` | 자연키가 UNIQUE 로 걸려 있음 | run | `validate/v2_load.py:112` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:134 |
| `V2-16` | PK·FK 컬럼에 개인정보 없음 | run | `validate/v2_load.py:115` | **★ 없음** | 없음 | chapters/60-admin/00-intro.md:147 · chapters/20-verify/b-v1v2.md:135 |
| `V2-17` | PII 고아 행 없음 | run | `validate/v2_load.py:60` | **★ 없음** | 없음 | guide/03_이력.md:110 · chapters/11-store/b-core.md:474 · chapters/20-verify/b-v1v2.md:136 |
| `V2-18` | parse_rule 재처리 후 전 봉투가 현재 parse_version | run | `validate/v2_load.py:105` | **★ 없음** | 없음 | trace/RULES.md:226 · guide/03_이력.md:136 · chapters/13-pipeline.md:380 |
| `V2-19` | 원문 유래 컬럼에 NOT NULL 없음 | run | `validate/v2_load.py:102` | **★ 없음** | 없음 | guide/01_요구사항.md:910 · guide/01_요구사항.md:919 · guide/01_요구사항.md:920 |
| `V2-20` | 파싱 실패 필드가 있는 행도 CORE 에 있음 | run | `validate/v2_load.py:64` | **★ 없음** | 없음 | guide/01_요구사항.md:923 · guide/01_요구사항.md:932 · guide/01_요구사항.md:933 |
| `V2-21` | parse_error · type_mismatch 건수 | run | `validate/v2_load.py:68` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:115 |
| `V2-22` | 현재 DB 스키마가 sql/ddl 과 일치 | run | `validate/v2_load.py:84` | **★ 없음** | 없음 | trace/20-verify.md:27 · trace/RULES.md:139 · guide/03_이력.md:145 |
| `V2-23` | 중간 노드 None 인 매물도 CORE 에 있음 | run | `validate/v2_load.py:87` | **★ 없음** | 없음 | guide/03_이력.md:149 · chapters/20-verify/b-v1v2.md:117 · chapters/10-collect/d-record.md:97 |
| `V2-24` | 배열 기대 필드가 전건 list 로 정규화됨 | run | `validate/v2_load.py:91` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:118 |
| `V2-25` | 스칼라 null 이 0 으로 저장된 컬럼 없음 | run | `validate/v2_load.py:95` | **★ 없음** | 없음 | chapters/20-verify/b-v1v2.md:119 |
| `V2-27` | parse/ 에 원문 연쇄 첨자가 없음 | run | `validate/v2_load.py:98` | **★ 없음** | 없음 | guide/03_이력.md:152 · chapters/20-verify/00-intro.md:151 · chapters/20-verify/b-v1v2.md:120 |
| `V2-28` | 파싱 실패해도 남은 필드가 저장됨 | run | `validate/v2_load.py:72` | **★ 없음** | 없음 | guide/03_이력.md:240 · chapters/00-standard.md:706 · chapters/20-verify/b-v1v2.md:122 |
| `V2-29` | upsert 가 버린 키를 기록함 | run | `validate/v2_load.py:77` | **★ 없음** | 없음 | guide/03_이력.md:241 · chapters/20-verify/b-v1v2.md:123 · chapters/10-collect/b-parse.md:75 |
| `V2-30` | 전 파서가 row_status 를 냄 | run | `validate/v2_load.py:134` | **★ 없음** | 없음 | guide/03_이력.md:289 · chapters/20-verify/b-v1v2.md:124 · chapters/10-collect/b-parse.md:96 |
| `V2-31` | target_key NULL 이 판정에 들어가지 않음 | run | `validate/v2_load.py:124` | **★ 없음** | 없음 | trace/11-store.md:70 · trace/11-store.md:71 · trace/RULES.md:197 |
| `V2-32` | NULL 매물의 모델명이 화면에서 보임 | run | `validate/v2_load.py:129` | **★ 없음** | 없음 | trace/11-store.md:71 · trace/11-store.md:72 · trace/RULES.md:197 |
| `V3-01` | result_axis.source 전건 NOT NULL | axis | `validate/v3_logic.py:41` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:45 · chapters/20-verify/c-v3v4.md:125 |
| `V3-02` | result_axis.prio 전건 NOT NULL | axis | `validate/v3_logic.py:44` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:46 |
| `V3-03` | 축별 source 값 종류 >= 2 | axis | `validate/v3_logic.py:47` | **★ 없음** | 없음 | chapters/00-standard.md:664 · chapters/30-score/c-spec.md:66 · chapters/20-verify/c-v3v4.md:47 |
| `V3-04` | 축별 값 종류 >= 2 | axis | `validate/v3_logic.py:50` | **★ 없음** | 없음 | chapters/40-report.md:116 · chapters/40-report.md:331 · chapters/30-score/c-spec.md:17 |
| `V3-05` | 금지 근거가 source 에 없음 | axis | `validate/v3_logic.py:53` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:49 |
| `V3-06` | put() 충돌 기록 검토 | run | `validate/v3_logic.py:68` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:50 |
| `V3-07` | 축별 -1 비율 | axis | `validate/v3_logic.py:56` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:51 |
| `V3-08` | 사전 pending 이 판정에 쓰이지 않음 | run | `validate/v3_logic.py:59` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:52 |
| `V3-09` | 축별 excluded 비율 | axis | `validate/v3_logic.py:62` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:53 |
| `V3-10` | 재판정 결과가 이전과 동일 | run | `validate/v3_logic.py:71` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:137 |
| `V3-11` | put() 순서 셔플 후에도 동일 | run | `validate/v3_logic.py:65` | **★ 없음** | 없음 | chapters/00-standard.md:663 · chapters/30-score/a-frame.md:190 · chapters/20-verify/c-v3v4.md:138 |
| `V3-20` | trust_score 가 555 에 합산되지 않음 | run | `validate/v3_logic.py:363` | **★ 없음** | 없음 | chapters/20-verify/00-intro.md:150 · chapters/20-verify/c-v3v4.md:88 · chapters/20-verify/c-v3v4.md:125 |
| `V3-21` | 경고가 555 에 합산되지 않음 | run | `validate/v3_logic.py:366` | **★ 없음** | 없음 | MULTISITE_MAPPING.md:231 · MULTISITE_MAPPING.md:283 · MULTISITE_MAPPING.md:598 |
| `V3-22` | 경고로 매물이 목록에서 제외되지 않음 | run | `validate/v3_logic.py:369` | **★ 없음** | 없음 | guide/03_이력.md:427 · chapters/00-standard.md:1960 · chapters/20-verify/c-v3v4.md:90 |
| `V3-23` | 경고로 등급·추천 순위가 바뀌지 않음 | run | `validate/v3_logic.py:74` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:91 |
| `V3-24` | acknowledged 가 신호 감지를 멈추지 않음 | run | `validate/v3_logic.py:78` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:92 |
| `V3-25` | 소멸한 경고가 삭제되지 않고 남음 | run | `validate/v3_logic.py:81` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:93 |
| `V3-27` | 모든 경고에 evidence 존재 | run | `validate/v3_logic.py:372` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:95 |
| `V3-28` | PeerGroup 이 확장 단계를 표시 | run | `validate/v3_logic.py:84` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:96 |
| `V3-29` | 배점 변경 시 calc_version 이 증가 | run | `validate/v3_logic.py:88` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:97 |
| `V3-30` | halt 축의 사전이 비어 있지 않음 | run | `validate/v3_logic.py:102` | **★ 없음** | 없음 | trace/RULES.md:212 · guide/03_이력.md:128 · chapters/00-standard.md:210 |
| `V3-31` | 딜러 NULL 매물에 dealer_untrusted 없음 | run | `validate/v3_logic.py:358` | **★ 없음** | 없음 | guide/01_요구사항.md:949 · guide/01_요구사항.md:958 · guide/01_요구사항.md:959 |
| `V3-32` | seizing null 매물이 「저당 없음」으로 판정되지 않음 | run | `validate/v3_logic.py:125` | **★ 없음** | 없음 | guide/01_요구사항.md:949 · guide/01_요구사항.md:958 · guide/01_요구사항.md:959 |
| `V3-34` | 판정 항목 수 == resultCode IS NOT NULL 인 items 수 | run | `validate/v3_logic.py:115` | **★ 없음** | 없음 | trace/11-store.md:62 · guide/03_이력.md:184 · chapters/11-store/b-core.md:232 |
| `V3-35` | conflicts 가 있는 매물이 기록됨 | run | `validate/v3_logic.py:107` | **★ 없음** | 없음 | guide/03_이력.md:225 · chapters/30-score/a-frame.md:162 · chapters/11-store/c-result.md:219 |
| `V3-36` | conflicts 건수가 임계 미만 | run | `validate/v3_logic.py:112` | **★ 없음** | 없음 | guide/03_이력.md:225 · chapters/00-standard.md:707 · chapters/30-score/a-frame.md:163 |
| `V3-37` | 목록 관측분의 source 가 'list' 임 | run | `validate/v3_logic.py:131` | **★ 없음** | 없음 | trace/12-dict.md:29 · trace/12-dict.md:32 · trace/RULES.md:206 |
| `V3-38` | facet 수신 후 목록 관측분과 대조함 | run | `validate/v3_logic.py:136` | **★ 없음** | 없음 | trace/12-dict.md:31 · guide/03_이력.md:285 · guide/03_이력.md:418 |
| `V3-39` | 이론가와 실제 중앙값의 차가 상한 안 | run | `validate/v3_logic.py:294` | **★ 없음** | 없음 | guide/01_요구사항.md:191 · guide/01_요구사항.md:201 · guide/01_요구사항.md:202 |
| `V3-40` | 핵심 축이 excluded 인데 등급을 매기지 않음 | run | `validate/v3_logic.py:284` | **★ 없음** | 없음 | guide/02_결함대장.md:57 · guide/02_결함대장.md:67 · guide/03_이력.md:306 |
| `V3-41` | 전 매물의 분모가 만점과 같음 | run | `validate/v3_logic.py:278` | **★ 없음** | 없음 | trace/05-score.md:23 · guide/02_결함대장.md:71 · guide/02_결함대장.md:81 |
| `V3-42` | — | — | **★ 코드에 없다** | — | — | trace/14-web.md:55 · guide/01_요구사항.md:157 · guide/01_요구사항.md:233 |
| `V3-44` | — | — | **★ 코드에 없다** | — | — | guide/02_결함대장.md:85 · guide/02_결함대장.md:95 · guide/03_이력.md:310 |
| `V3-45` | 배점 합이 만점과 같음 | run | `validate/v3_logic.py:355` | **★ 없음** | 없음 | guide/03_이력.md:311 · chapters/20-verify/c-v3v4.md:105 |
| `V3-47` | 축별 차종 간 결측률 편차가 상한 안 | run | `validate/v3_logic.py:289` | **★ 없음** | 없음 | trace/05-score.md:92 · trace/RULES.md:248 · guide/01_요구사항.md:247 |
| `V3-49` | — | — | **★ 코드에 없다** | — | — | ENCAR_API.md:184 · trace/05-score.md:57 · guide/01_요구사항.md:158 |
| `V3-50` | 성능부와 보험이력이 어긋난 건을 셈 | run | `validate/v3_logic.py:155` | **★ 없음** | 없음 | trace/05-score.md:93 · guide/03_이력.md:314 · guide/03_이력.md:434 |
| `V3-52` | 「싸다」에 이유가 붙어 있음 | run | `validate/v3_logic.py:341` | **★ 없음** | 없음 | trace/05-score.md:90 · trace/14-web.md:86 · guide/01_요구사항.md:301 |
| `V3-53` | 점검 출처가 판정에 반영됨 | run | `validate/v3_logic.py:346` | **★ 없음** | 없음 | trace/05-score.md:76 · guide/03_이력.md:319 · chapters/30-score/a-frame.md:623 |
| `V3-54` | 렌트 이력을 세 곳에서 대조 | run | `validate/v3_logic.py:350` | **★ 없음** | 없음 | trace/05-score.md:56 · guide/03_이력.md:321 · chapters/30-score/a-frame.md:667 |
| `V3-55` | 사이트 보증 축이 config 규칙을 읽는가 | run | `validate/v3_logic.py:312` | **★ 없음** | 없음 | trace/05-score.md:75 · trace/05-score.md:102 · trace/05-score.md:103 |
| `V3-56` | 배점 합이 605 | run | `validate/v3_logic.py:317` | **★ 없음** | 없음 | trace/05-score.md:21 · trace/60-admin.md:49 · chapters/00-standard.md:1329 |
| `V3-57` | 등급 기준이 grade_base_points 와 같음 | run | `validate/v3_logic.py:320` | **★ 없음** | 없음 | trace/05-score.md:22 · guide/03_이력.md:325 |
| `V3-58` | 배터리 SOH 가 축이 아니라 가점임 | run | `validate/v3_logic.py:141` | **★ 없음** | 없음 | trace/05-score.md:37 · trace/05-score.md:114 · guide/03_이력.md:337 |
| `V3-59` | 가점이 분모를 늘리지 않음 | run | `validate/v3_logic.py:147` | **★ 없음** | 없음 | guide/03_이력.md:337 · guide/03_이력.md:399 · guide/03_이력.md:430 |
| `V3-62` | 원문이 없는데 값을 만든 축이 없음 | run | `validate/v3_logic.py:299` | **★ 없음** | 없음 | trace/05-score.md:91 · trace/RULES.md:177 · trace/RULES.md:196 |
| `V3-64` | 등급 경계가 절대 기준 | run | `validate/v3_logic.py:304` | **★ 없음** | 없음 | trace/05-score.md:26 · guide/01_요구사항.md:355 · guide/01_요구사항.md:365 |
| `V3-65` | 확인율이 근거 있는 축만 셈 | run | `validate/v3_logic.py:308` | **★ 없음** | 없음 | trace/05-score.md:24 · trace/14-web.md:89 · guide/03_이력.md:344 |
| `V3-66` | 각 축의 계산이 f-table 과 같음 | run | `validate/v3_logic.py:161` | **★ 없음** | 없음 | trace/05-score.md:27 · guide/02_결함대장.md:141 · guide/02_결함대장.md:151 |
| `V3-67` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:160 · guide/01_요구사항.md:369 · guide/01_요구사항.md:379 |
| `V3-68` | 부록 F 전 24축이 구현돼 있음 | run | `validate/v3_logic.py:335` | **★ 없음** | 없음 | guide/01_요구사항.md:383 · guide/01_요구사항.md:393 · guide/01_요구사항.md:394 |
| `V3-69` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:350 · chapters/30-score/a-frame.md:764 |
| `V3-70` | 일반·동력계 보증을 따로 냄 | run | `validate/v3_logic.py:325` | **★ 없음** | 없음 | trace/05-score.md:111 · trace/05-score.md:112 · trace/05-score.md:115 |
| `V3-71` | 보증 잔여가 기간·거리 중 낮은 쪽임 | run | `validate/v3_logic.py:330` | **★ 없음** | 없음 | trace/05-score.md:113 · trace/05-score.md:115 · guide/03_이력.md:384 |
| `V3-72` | SOH 가점이 곡선대로 붙음 | run | `validate/v3_logic.py:151` | **★ 없음** | 없음 | guide/03_이력.md:399 · chapters/30-score/f-table.md:933 |
| `V3-73` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:400 · chapters/30-score/f-table.md:1607 |
| `V3-75` | 트림 점수를 신차가로 잼 | run | `validate/v3_logic.py:273` | **★ 없음** | 없음 | guide/03_이력.md:401 · guide/03_이력.md:1025 · guide/03_이력.md:1027 |
| `V3-76` | ⑤ 의 하위 축 합이 갈래 표기와 같음 | run | `validate/v3_logic.py:256` | **★ 없음** | 없음 | guide/03_이력.md:412 · chapters/30-score/f-table.md:1326 |
| `V3-77` | 갈래마다 하위 축 합 = 갈래 표기 (전 갈래) | run | `validate/v3_logic.py:262` | **★ 없음** | 없음 | guide/03_이력.md:412 · guide/03_이력.md:431 · guide/03_이력.md:452 |
| `V3-78` | 「그 밖」으로 옮긴 값이 축을 덮지 않음 | run | `validate/v3_logic.py:267` | **★ 없음** | 없음 | guide/03_이력.md:418 |
| `V3-79` | 어긋난 매물에 ②-2·②-3 만점이 없음 | run | `validate/v3_logic.py:216` | **★ 없음** | 없음 | guide/03_이력.md:434 · chapters/30-score/f-table.md:993 |
| `V3-80` | ②-1 회수가 max(보험, 성능부) 임 | run | `validate/v3_logic.py:222` | **★ 없음** | 없음 | guide/03_이력.md:434 · chapters/30-score/f-table.md:994 |
| `V3-81` | 셋 중 하나만 null 인데 확인 안 됨이 아님 | run | `validate/v3_logic.py:228` | **★ 없음** | 없음 | guide/03_이력.md:435 · chapters/30-score/f-table.md:1064 |
| `V3-82` | 시세 점수가 계단값만 나오지 않음 | run | `validate/v3_logic.py:234` | **★ 없음** | 없음 | guide/03_이력.md:439 · chapters/30-score/f-table.md:759 |
| `V3-83` | 시세보다 비싼 매물에 음수 점수가 붙음 | run | `validate/v3_logic.py:240` | **★ 없음** | 없음 | chapters/30-score/f-table.md:760 |
| `V3-84` | 신차가 곡선이 규격의 앵커와 같음 | run | `validate/v3_logic.py:246` | **★ 없음** | 없음 | guide/03_이력.md:439 · chapters/30-score/f-table.md:803 |
| `V3-85` | 옵션 보정 없이 원 중앙값으로 견준 매물 | run | `validate/v3_logic.py:251` | **★ 없음** | 없음 | guide/03_이력.md:441 |
| `V3-86` | 축 점수가 배점을 넘지 않음 | run | `validate/v3_logic.py:205` | **★ 없음** | 없음 | guide/03_이력.md:448 · chapters/30-score/f-table.md:544 |
| `V3-87` | 사이트 검증이 단계임 (더하지 않음) | run | `validate/v3_logic.py:211` | **★ 없음** | 없음 | guide/03_이력.md:448 · chapters/30-score/f-table.md:545 · chapters/30-score/f-table.md:1411 |
| `V3-88` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:450 · chapters/30-score/f-table.md:702 |
| `V3-90` | 등급 분모가 총점으로 고정 | run | `validate/v3_logic.py:194` | **★ 없음** | 없음 | guide/03_이력.md:451 · guide/03_이력.md:501 · guide/03_이력.md:503 |
| `V3-91` | 가이드 검산 일곱 줄이 표대로 나옴 | run | `validate/v3_logic.py:199` | **★ 없음** | 없음 | guide/03_이력.md:451 · chapters/30-score/f-table.md:526 · chapters/30-score/f-table.md:1411 |
| `V3-92` | 트림 만점이 개별 취향 축보다 큼 | run | `validate/v3_logic.py:178` | **★ 없음** | 없음 | guide/03_이력.md:452 · chapters/30-score/f-table.md:375 |
| `V3-93` | 제외 매물에 등급 문자가 안 붙음 | run | `validate/v3_logic.py:184` | **★ 없음** | 없음 | guide/03_이력.md:453 · chapters/30-score/f-table.md:336 |
| `V3-94` | 등급 컷이 규격의 8단계임 | run | `validate/v3_logic.py:189` | **★ 없음** | 없음 | guide/03_이력.md:453 · chapters/30-score/f-table.md:322 · chapters/30-score/f-table.md:337 |
| `V3-95` | 화면이 source='missing' 을 「없음」으로 안 냄 | run | `validate/v3_logic.py:166` | **★ 없음** | 없음 | guide/03_이력.md:455 · guide/07_밀린일대장.md:352 · chapters/30-score/f-table.md:424 |
| `V3-96` | value IS NULL 과 source 모름 건수 차 | run | `validate/v3_logic.py:172` | **★ 없음** | 없음 | guide/03_이력.md:455 · guide/07_밀린일대장.md:352 · chapters/30-score/f-table.md:425 |
| `V4-01` | 매핑 일치율 (A 100% · B 99% · C 80%) | run | `validate/v4_mapping.py:28` | **★ 없음** | 없음 | chapters/00-standard.md:661 · chapters/60-admin/c-tools.md:152 · chapters/20-verify/c-v3v4.md:176 |
| `V4-02` | 미매핑 경로 목록 | run | `validate/v4_mapping.py:103` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:177 |
| `V4-03` | 오매핑 탐지 — 다른 경로와 더 높은 일치율 | run | `validate/v4_mapping.py:31` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:178 · chapters/20-verify/c-v3v4.md:294 |
| `V4-04` | 매핑표에 없는 CORE 컬럼 | run | `validate/v4_mapping.py:106` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:179 |
| `V4-05` | 원문 경로 수 변동 | run | `validate/v4_mapping.py:108` | **★ 없음** | 없음 | trace/12-dict.md:21 · chapters/31-registry.md:303 · chapters/20-verify/c-v3v4.md:180 |
| `V4-06` | RAW 경로가 등록부에 있는가 | run | `validate/v4_mapping.py:34` | **★ 없음** | 없음 | trace/31-registry.md:21 · trace/31-registry.md:39 · trace/60-admin.md:53 |
| `V4-06b` | 등록부에 있는데 RAW 에 없는 유령 경로 | run | `validate/v4_mapping.py:37` | **★ 없음** | 없음 | trace/31-registry.md:40 · trace/RULES.md:246 · trace/RULES.md:247 |
| `V4-07` | in_use 인데 core_column NULL | run | `validate/v4_mapping.py:40` | **★ 없음** | 없음 | chapters/31-registry.md:294 · chapters/60-admin/b-ops.md:129 · chapters/20-verify/c-v3v4.md:183 |
| `V4-08` | blocked 인데 unblock_condition NULL | run | `validate/v4_mapping.py:43` | **★ 없음** | 없음 | trace/RULES.md:209 · chapters/31-registry.md:295 · chapters/20-verify/c-v3v4.md:184 |
| `V4-09` | deferred 인데 use_when NULL | run | `validate/v4_mapping.py:46` | **★ 없음** | 없음 | chapters/31-registry.md:296 · chapters/20-verify/c-v3v4.md:185 |
| `V4-10` | display_only 인데 core_column NULL | run | `validate/v4_mapping.py:49` | **★ 없음** | 없음 | chapters/31-registry.md:297 · chapters/20-verify/c-v3v4.md:186 |
| `V4-11` | unclassified 존재 | run | `validate/v4_mapping.py:52` | **★ 없음** | 없음 | trace/12-dict.md:65 · guide/01_시작.md:225 · guide/01_시작.md:235 |
| `V4-11b` | 판정에 안 쓰는 미분류 경로 | run | `validate/v4_mapping.py:55` | **★ 없음** | 없음 | trace/RULES.md:243 · guide/01_요구사항.md:178 · guide/01_요구사항.md:187 |
| `V4-12` | facet 필수 축 집합 존재 | run | `validate/v4_mapping.py:87` | **★ 없음** | 없음 | chapters/20-verify/c-v3v4.md:189 |
| `V4-13` | 매직 넘버 없음 (tools/check_src.py S7) | run | `validate/v4_mapping.py:90` | **★ 없음** | 없음 | trace/RULES.md:147 · trace/RULES.md:261 · trace/RULES.md:318 |
| `V4-19` | 성격(kind)이 없는 Check 가 없음 | run | `validate/v4_mapping.py:111` | **★ 없음** | 없음 | trace/20-verify.md:33 · trace/20-verify.md:34 · trace/RULES.md:140 |
| `V4-20` | dict_option_code 에 문장(공백·한글)이 없음 | run | `validate/v4_mapping.py:126` | **★ 없음** | 없음 | guide/03_이력.md:150 · chapters/20-verify/c-v3v4.md:197 · chapters/10-collect/e-catalog.md:182 |
| `V4-21` | 같은 이름의 공개 함수가 두 모듈에 없음 | run | `validate/v4_mapping.py:122` | **★ 없음** | 없음 | guide/03_이력.md:156 · chapters/30-score/h-verdict.md:70 · chapters/20-verify/c-v3v4.md:198 |
| `V4-22` | 역방향 · 순환 import 없음 | run | `validate/v4_mapping.py:114` | **★ 없음** | 없음 | MAPPING.md:62 · MAPPING.md:96 · trace/RULES.md:160 |
| `V4-23` | 모듈 최상위에 I/O · 부작용 없음 | run | `validate/v4_mapping.py:117` | **★ 없음** | 없음 | MAPPING.md:97 · trace/41-view.md:22 · trace/RULES.md:164 |
| `V4-24` | 축 함수가 target_config 에서 매물 값을 읽지 않음 | run | `validate/v4_mapping.py:92` | **★ 없음** | 없음 | guide/03_이력.md:226 · chapters/01-arch.md:223 · chapters/20-verify/c-v3v4.md:201 |
| `V4-25` | 판정에 쓰는 축의 사전이 비어 있지 않음 | run | `validate/v4_mapping.py:98` | **★ 없음** | 없음 | trace/12-dict.md:49 · trace/60-admin.md:90 · guide/03_이력.md:242 |
| `V4-26` | 미분류가 원인별로 갈려 있음 | run | `validate/v4_mapping.py:58` | **★ 없음** | 없음 | trace/12-dict.md:62 · guide/01_요구사항.md:800 · guide/01_요구사항.md:810 |
| `V4-27` | 판정을 막는 것만 막음 | run | `validate/v4_mapping.py:64` | **★ 없음** | 없음 | trace/12-dict.md:63 · guide/01_요구사항.md:800 · guide/01_요구사항.md:810 |
| `V4-28` | 미분류 항목에 값 분포와 선택지가 있음 | run | `validate/v4_mapping.py:76` | **★ 없음** | 없음 | guide/03_이력.md:386 · chapters/31-registry.md:660 |
| `V4-29` | 기본 화면이 판정 막는 것만 냄 | run | `validate/v4_mapping.py:82` | **★ 없음** | 없음 | guide/03_이력.md:386 · chapters/31-registry.md:672 |
| `V4-30` | 판정을 막는 것의 목록 파일이 있음 | run | `validate/v4_mapping.py:70` | **★ 없음** | 없음 | guide/03_이력.md:410 |
| `V5-01` | 배점 합계 == config 총점 | run | `validate/v5_value.py:16` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:15 |
| `V5-02` | 표시용 등급 점수가 비율과 일치 | run | `validate/v5_value.py:19` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:16 |
| `V5-03` | 분모 시험 A·D·E·G·H·I 통과 | run | `validate/v5_value.py:22` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:17 · chapters/20-verify/d-v5.md:28 |
| `V5-04` | 점수 범위 위반 없음 | run | `validate/v5_value.py:25` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:18 |
| `V5-05` | 등급 분포가 극단적이지 않음 | run | `validate/v5_value.py:28` | **★ 없음** | 없음 | chapters/00-standard.md:662 · chapters/30-score/h-verdict.md:17 · chapters/60-admin/c-tools.md:154 |
| `V5-06` | 기준값 대비 실측 이탈 | run | `validate/v5_value.py:31` | **★ 없음** | 없음 | chapters/30-score/b-price.md:90 · chapters/20-verify/d-v5.md:20 · chapters/20-verify/d-v5.md:53 |
| `V5-07` | 계수 보정 타당성 | run | `validate/v5_value.py:34` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:21 |
| `V5-08` | 계수 산출 입력에 result_* 없음 | run | `validate/v5_value.py:51` | **★ 없음** | 없음 | trace/RULES.md:153 · chapters/20-verify/d-v5.md:22 · chapters/20-verify/d-v5.md:123 |
| `V5-09` | 등급이 earned / denominator 로 산출됨 | run | `validate/v5_value.py:41` | **★ 없음** | 없음 | guide/03_이력.md:147 · chapters/20-verify/d-v5.md:23 |
| `V5-10` | 같은 비율 · 다른 분모가 같은 등급 | run | `validate/v5_value.py:46` | **★ 없음** | 없음 | chapters/20-verify/d-v5.md:24 |
| `V5-11` | 분모 최대값으로도 S 가 불가능한 매물 없음 | run | `validate/v5_value.py:48` | **★ 없음** | 없음 | guide/03_이력.md:147 · chapters/20-verify/d-v5.md:25 |
| `V5-12` | NOT_RATED 인데 not_rated_reason 이 NULL 인 행 없음 | run | `validate/v5_value.py:37` | **★ 없음** | 없음 | trace/11-store.md:78 · guide/03_이력.md:239 · chapters/11-store/c-result.md:123 |
| `V6-01` | — | — | **★ 코드에 없다** | — | — | chapters/41-view.md:877 · chapters/61-web.md:370 |
| `V6-07` | ORDER BY 에 4단이 전부 있음 | run | `validate/v3_logic.py:121` | **★ 없음** | 없음 | trace/41-view.md:61 · trace/41-view.md:62 · trace/RULES.md:170 |
| `V7-01` | watch_track 에 버전 4종 전건 있음 | run | `validate/v7_watch.py:30` | **★ 없음** | 없음 | guide/03_이력.md:159 · chapters/42-watch.md:618 |
| `V7-02` | cause != 'listing' 인 이벤트가 알림되지 않음 | run | `validate/v7_watch.py:34` | **★ 없음** | 없음 | chapters/42-watch.md:624 |
| `V7-04` | 같은 이벤트 중복 발송 0건 | run | `validate/v7_watch.py:38` | **★ 없음** | 없음 | trace/50-multisite.md:26 · chapters/42-watch.md:626 · chapters/50-multisite.md:126 |
| `V7-05` | gone 매물이 목록에서 삭제되지 않음 | run | `validate/v7_watch.py:40` | **★ 없음** | 없음 | chapters/42-watch.md:627 |
| `V7-06` | 검증 실패 실행에서 알림이 나가지 않음 | run | `validate/v7_watch.py:43` | **★ 없음** | 없음 | trace/50-multisite.md:23 · trace/RULES.md:293 · chapters/42-watch.md:628 |
| `V7-07` | relist 결합에 identity_kind 기록 | run | `validate/v7_watch.py:47` | **★ 없음** | 없음 | chapters/42-watch.md:629 |
| `V7-08` | 구매 체크리스트가 점수·등급에 반영되지 않음 | run | `validate/v7_watch.py:62` | **★ 없음** | 없음 | chapters/42-watch.md:630 |
| `V7-09` | 실구매가·총소유비용이 점수에 반영되지 않음 | run | `validate/v7_watch.py:78` | **★ 없음** | 없음 | chapters/42-watch.md:631 |
| `V7-10` | 발송 시도 대비 성공률 | run | `validate/v7_watch.py:50` | **★ 없음** | 없음 | trace/50-multisite.md:24 · trace/RULES.md:291 · trace/RULES.md:292 |
| `V7-11` | closed_reason 이 CHECK 안의 값 | run | `validate/v7_watch.py:58` | **★ 없음** | 없음 | trace/42-watch.md:37 · trace/42-watch.md:46 · trace/42-watch.md:47 |
| `V7-12` | 남의 관심 항목을 고치지 못함 | run | `validate/v7_watch.py:54` | **★ 없음** | 없음 | trace/14-web.md:113 · trace/42-watch.md:38 · trace/42-watch.md:39 |
| `V7-14` | 재등록 횟수가 화면에 나옴 | run | `validate/v7_watch.py:66` | **★ 없음** | 없음 | trace/42-watch.md:30 · guide/03_이력.md:374 · guide/03_이력.md:430 |
| `V7-15` | 진행 메모를 자유롭게 적을 수 있음 | run | `validate/v7_watch.py:71` | **★ 없음** | 없음 | trace/42-watch.md:68 · trace/42-watch.md:69 · trace/42-watch.md:70 |
| `V8-01` | 같은 파일명이 두 번 생성되지 않음 | run | `validate/v3_logic.py:92` | **★ 없음** | 없음 | trace/RULES.md:266 · trace/RULES.md:267 · guide/03_이력.md:163 |
| `V8-02` | 출력 파일에 BOM · CRLF 가 없음 | run | `validate/v3_logic.py:97` | **★ 없음** | 없음 | trace/40-report.md:42 · trace/40-report.md:43 · trace/40-report.md:45 |
| `V9-01` | 축 × 사이트 표가 있음 | run | `validate/v9_multisite.py:45` | **★ 없음** | 없음 | trace/02-collect.md:75 · trace/05-score.md:104 · trace/50-multisite.md:41 |
| `V9-02` | site_unavailable 이 화면에 나옴 | run | `validate/v9_multisite.py:49` | **★ 없음** | 없음 | trace/50-multisite.md:39 · trace/50-multisite.md:40 · chapters/50-multisite.md:223 |
| `V9-03` | — | — | **★ 코드에 없다** | — | — | trace/50-multisite.md:42 · trace/50-multisite.md:43 · trace/50-multisite.md:44 |
| `V9-04` | — | — | **★ 코드에 없다** | — | — | trace/31-registry.md:53 · trace/50-multisite.md:51 · trace/50-multisite.md:52 |
| `V9-05` | — | — | **★ 코드에 없다** | — | — | trace/02-collect.md:73 · trace/50-multisite.md:52 · trace/50-multisite.md:53 |
| `V9-06` | 매물마다 사이트 배지가 있음 | run | `validate/v9_multisite.py:33` | **★ 없음** | 없음 | trace/02-collect.md:76 · trace/14-web.md:63 · trace/50-multisite.md:61 |
| `V9-07` | 합친 값에 출처가 붙어 있음 | run | `validate/v9_multisite.py:61` | **★ 없음** | 없음 | trace/50-multisite.md:45 · trace/50-multisite.md:63 · trace/50-multisite.md:64 |
| `V9-08` | — | — | **★ 코드에 없다** | — | — | trace/02-collect.md:77 · trace/05-score.md:101 · trace/50-multisite.md:70 |
| `V9-09` | 같은 점수에서 사이트 보증이 높은 쪽이 앞 | run | `validate/v9_multisite.py:55` | **★ 없음** | 없음 | trace/50-multisite.md:72 · trace/RULES.md:299 · guide/01_요구사항.md:328 |
| `V9-10` | 사이트 보증 항목의 합이 만점과 같음 | run | `validate/v9_multisite.py:39` | **★ 없음** | 없음 | trace/05-score.md:100 · trace/05-score.md:102 · trace/05-score.md:103 |
| `V10-01` | admin 전용을 user 로 호출 시 PolicyError | run | `validate/v10_admin.py:28` | **★ 없음** | 없음 | trace/13-pipeline.md:22 · chapters/60-admin/c-tools.md:790 |
| `V10-02` | 서버 권한 검증 존재 (화면 숨김 아님) | run | `validate/v10_admin.py:31` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:791 |
| `V10-03` | run_query 가 SELECT 외를 전건 거부 | run | `validate/v10_admin.py:34` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:792 |
| `V10-04` | run_query 판정이 AST 기반 (정규식 아님) | run | `validate/v10_admin.py:37` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:793 |
| `V10-05` | config 변경이 ConfigChange 없이 안 일어남 | run | `validate/v10_admin.py:40` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:794 · chapters/20-verify/c-v3v4.md:208 · chapters/20-verify/c-v3v4.md:213 |
| `V10-06` | 배점 저장 시 Σ == total_points | run | `validate/v10_admin.py:43` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:795 |
| `V10-07` | 성분 추가가 선택 가능 목록 안에서만 | run | `validate/v10_admin.py:46` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:796 |
| `V10-08` | 관리 도구가 core_* 를 UPDATE 하지 않음 | run | `validate/v10_admin.py:49` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:797 |
| `V10-09` | DevRequest 가 삭제되지 않음 | run | `validate/v10_admin.py:52` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:798 |
| `V10-10` | 문서 뷰어에 편집 경로 없음 | run | `validate/v10_admin.py:55` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:799 |
| `V10-11` | 실행 중 config 변경이 잠김 | run | `validate/v10_admin.py:58` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:800 |
| `V10-12` | 배점 조정 후 0점 성분 없음 | run | `validate/v10_admin.py:61` | **★ 없음** | 없음 | chapters/60-admin/c-tools.md:801 |
| `V10-13` | 웹에서 전면 재수집이 큐에 안 들어감 | run | `validate/v10_admin.py:64` | **★ 없음** | 없음 | trace/60-admin.md:60 · trace/RULES.md:45 · guide/03_이력.md:109 |
| `V10-14` | components.{axis}.{component} 경로 읽기·쓰기 | run | `validate/v10_admin.py:67` | **★ 없음** | 없음 | trace/13-pipeline.md:21 · trace/RULES.md:37 · guide/03_이력.md:115 |
| `V10-15` | 저장 전 배점 합 검사 | run | `validate/v10_admin.py:70` | **★ 없음** | 없음 | guide/03_이력.md:115 · chapters/60-admin/c-tools.md:804 |
| `V10-16` | must_change_secret 계정이 다른 화면에 접근 못 함 | run | `validate/v10_admin.py:73` | **★ 없음** | 없음 | trace/RULES.md:29 · trace/RULES.md:30 · trace/RULES.md:31 |
| `V10-17` | admin 수가 0 이 되는 변경이 거부됨 | run | `validate/v10_admin.py:78` | **★ 없음** | 없음 | guide/03_이력.md:178 · guide/03_이력.md:215 · chapters/61-web.md:1992 |
| `V10-18` | core_pii · core_dealer_pii 조회가 거부됨 | run | `validate/v10_admin.py:83` | **★ 없음** | 없음 | trace/60-admin.md:74 · trace/60-admin.md:75 · trace/60-admin.md:76 |
| `V10-19` | 중지·비밀번호 변경 후 옛 세션이 anonymous | run | `validate/v10_admin.py:88` | **★ 없음** | 없음 | trace/60-admin.md:32 · trace/60-admin.md:33 · trace/RULES.md:32 |
| `V10-20` | 로그인 실패 상한이 config 대로 돎 | run | `validate/v10_admin.py:180` | **★ 없음** | 없음 | trace/11-store.md:63 · trace/60-admin.md:34 · trace/60-admin.md:36 |
| `V10-22` | queued 를 소비하는 코드가 있음 | run | `validate/v10_admin.py:94` | **★ 없음** | 없음 | trace/60-admin.md:64 · trace/60-admin.md:65 · trace/60-admin.md:67 |
| `V10-23` | 오래된 queued 가 화면에 표시됨 | run | `validate/v10_admin.py:99` | **★ 없음** | 없음 | trace/60-admin.md:64 · trace/60-admin.md:65 · trace/60-admin.md:67 |
| `V10-24` | 사전 확정에 사유가 남음 | run | `validate/v10_admin.py:104` | **★ 없음** | 없음 | trace/60-admin.md:137 · trace/60-admin.md:139 · trace/60-admin.md:140 |
| `V10-25` | 'list' 출처가 화면에 표시됨 | run | `validate/v10_admin.py:176` | **★ 없음** | 없음 | trace/12-dict.md:30 · trace/60-admin.md:137 · trace/60-admin.md:138 |
| `V10-26` | 목록 저장 후 큐에 작업이 들어감 | run | `validate/v10_admin.py:152` | **★ 없음** | 없음 | trace/02-collect.md:51 · trace/60-admin.md:180 · trace/RULES.md:72 |
| `V10-27` | 중간 실패에서 다음 단계로 안 넘어감 | run | `validate/v10_admin.py:157` | **★ 없음** | 없음 | trace/60-admin.md:110 · trace/60-admin.md:185 · trace/RULES.md:72 |
| `V10-28` | 타이머가 겹쳐 돌지 않음 | run | `validate/v10_admin.py:161` | **★ 없음** | 없음 | trace/02-collect.md:52 · trace/60-admin.md:189 · trace/60-admin.md:190 |
| `V10-29` | 목록 저장이 전건 재수집을 안 부름 | run | `validate/v10_admin.py:166` | **★ 없음** | 없음 | trace/02-collect.md:54 · trace/13-pipeline.md:50 · trace/60-admin.md:186 |
| `V10-30` | 재판정이 수집 없이 돎 | run | `validate/v10_admin.py:171` | **★ 없음** | 없음 | trace/60-admin.md:186 · trace/60-admin.md:188 · trace/RULES.md:73 |
| `V10-31` | 자동 수집이 13:00 인가 | run | `validate/v10_admin.py:129` | **★ 없음** | 없음 | guide/03_이력.md:407 · chapters/60-admin/c-tools.md:1082 |
| `V10-32` | 사람 손이 필요한 작업이 낮 시간대인가 | run | `validate/v10_admin.py:134` | **★ 없음** | 없음 | guide/03_이력.md:407 · chapters/60-admin/c-tools.md:1083 |
| `V10-33` | 컴파일 실패가 PolicyError 로 안 감 | run | `validate/v10_admin.py:108` | **★ 없음** | 없음 | guide/03_이력.md:411 |
| `V10-34` | 거부 응답에 고칠 재료가 있음 | run | `validate/v10_admin.py:115` | **★ 없음** | 없음 | — |
| `V10-35` | query_log 가 compile · policy 로 갈림 | run | `validate/v10_admin.py:120` | **★ 없음** | 없음 | — |
| `V10-36` | 표를 누르면 컬럼이 보임 | run | `validate/v10_admin.py:125` | **★ 없음** | 없음 | guide/03_이력.md:411 |
| `V10-37` | 결과 표 위에 복사 단추가 있음 | run | `validate/v10_admin.py:146` | **★ 없음** | 없음 | guide/03_이력.md:421 |
| `V10-38` | 끊긴 실행이 큐를 막고 있지 않음 | run | `validate/v10_admin.py:139` | **★ 없음** | 없음 | — |
| `V11-01` | web/ 에 SQL 문자열이 없음 | run | `validate/v11_web.py:40` | **★ 없음** | 없음 | guide/03_이력.md:161 · chapters/61-web.md:36 · chapters/61-web.md:1558 |
| `V11-02` | 기본 바인딩이 127.0.0.1 | run | `validate/v11_web.py:43` | **★ 없음** | 없음 | chapters/61-web.md:107 · chapters/61-web.md:2059 · chapters/61-web.md:2128 |
| `V11-03` | 전 Route 에 role 이 지정됨 | run | `validate/v11_web.py:47` | **★ 없음** | 없음 | chapters/61-web.md:175 · chapters/61-web.md:2129 |
| `V11-04` | 템플릿에 산술 연산이 없음 | run | `validate/v11_web.py:49` | **★ 없음** | 없음 | trace/RULES.md:163 · chapters/61-web.md:288 · chapters/61-web.md:2104 |
| `V11-05` | {{! }} 사용처가 화이트리스트에 있음 | run | `validate/v11_web.py:52` | **★ 없음** | 없음 | trace/RULES.md:163 · chapters/61-web.md:305 · chapters/61-web.md:2131 |
| `V11-06` | 정적 경로 탈출이 거부됨 | run | `validate/v11_web.py:57` | **★ 없음** | 없음 | trace/RULES.md:165 · trace/RULES.md:278 · chapters/61-web.md:410 |
| `V11-07` | 쿠키에 role 문자열이 없음 | run | `validate/v11_web.py:59` | **★ 없음** | 없음 | chapters/61-web.md:1357 · chapters/61-web.md:2133 |
| `V11-08` | 상태 변경이 GET 경로에 없음 | run | `validate/v11_web.py:61` | **★ 없음** | 없음 | chapters/61-web.md:1393 · chapters/61-web.md:2134 |
| `V11-09` | 미리보기 없이 저장이 안 됨 | run | `validate/v11_web.py:64` | **★ 없음** | 없음 | trace/RULES.md:68 · chapters/61-web.md:1421 · chapters/61-web.md:1912 |
| `V11-10` | 오류 화면에 스택 트레이스가 없음 | run | `validate/v11_web.py:66` | **★ 없음** | 없음 | chapters/61-web.md:1455 · chapters/61-web.md:2136 |
| `V11-11` | result_* 가 비었을 때 안내가 나옴 | run | `validate/v11_web.py:70` | **★ 없음** | 없음 | chapters/61-web.md:1484 · chapters/61-web.md:2137 |
| `V11-12` | 라우팅 표의 view 가 10·13장에 실재함 | run | `validate/v11_web.py:168` | **★ 없음** | 없음 | guide/03_이력.md:191 · guide/03_이력.md:272 · guide/03_이력.md:277 |
| `V11-13` | app.css 에 토큰 밖의 색값이 없음 | run | `validate/v11_web.py:93` | **★ 없음** | 없음 | guide/03_이력.md:214 · guide/03_이력.md:230 · guide/03_이력.md:842 |
| `V11-14` | 숫자 셀에 mono 가 걸려 있음 | run | `validate/v11_web.py:96` | **★ 없음** | 없음 | chapters/61-web.md:485 · chapters/61-web.md:2140 |
| `V11-15` | 화면이 빌드 산출물에 의존하지 않음 | run | `validate/v11_web.py:99` | **★ 없음** | 없음 | chapters/61-web.md:1300 · chapters/61-web.md:2141 |
| `V11-16` | /why 가 전 Component 를 냄 | run | `validate/v11_web.py:102` | **★ 없음** | 없음 | chapters/61-web.md:1506 · chapters/61-web.md:1581 · chapters/61-web.md:2142 |
| `V11-17` | /why 가 조회 상태 절을 냄 | run | `validate/v11_web.py:105` | **★ 없음** | 없음 | chapters/61-web.md:1581 · chapters/61-web.md:1635 · chapters/61-web.md:2143 |
| `V11-18` | 축 태그가 전건 필터 링크임 | run | `validate/v11_web.py:108` | **★ 없음** | 없음 | chapters/61-web.md:1679 · chapters/61-web.md:2144 |
| `V11-19` | 폴링 실패 시 화면이 안 깨짐 | run | `validate/v11_web.py:111` | **★ 없음** | 없음 | chapters/61-web.md:1699 · chapters/61-web.md:2145 |
| `V11-20` | 분모 표시가 있음 | run | `validate/v11_web.py:114` | **★ 없음** | 없음 | guide/03_이력.md:237 · chapters/61-web.md:1725 · chapters/61-web.md:2146 |
| `V11-21` | 행동 요청 파라미터가 현재 필터와 일치 | run | `validate/v11_web.py:117` | **★ 없음** | 없음 | chapters/61-web.md:1779 · chapters/61-web.md:2147 |
| `V11-22` | excluded 축이 「—/N」 으로 표시됨 | run | `validate/v11_web.py:120` | **★ 없음** | 없음 | chapters/61-web.md:1821 · chapters/61-web.md:2148 |
| `V11-23` | 비로그인 관심 POST 가 유도 화면을 냄 | run | `validate/v11_web.py:123` | **★ 없음** | 없음 | guide/03_이력.md:238 · chapters/61-web.md:1851 · chapters/61-web.md:2149 |
| `V11-24` | 메뉴 분류가 잠금 단위와 일치 | run | `validate/v11_web.py:126` | **★ 없음** | 없음 | chapters/61-web.md:1885 · chapters/61-web.md:2150 |
| `V11-25` | 사유 없이 설정이 저장되지 않음 | run | `validate/v11_web.py:130` | **★ 없음** | 없음 | chapters/61-web.md:1912 · chapters/61-web.md:2151 |
| `V11-26` | 되돌릴 수 없는 행동에 확인이 있음 | run | `validate/v11_web.py:133` | **★ 없음** | 없음 | chapters/61-web.md:1956 · chapters/61-web.md:2152 |
| `V11-27` | 가입 정책에 따라 화면이 바뀜 | run | `validate/v11_web.py:136` | **★ 없음** | 없음 | chapters/61-web.md:2013 · chapters/61-web.md:2153 |
| `V11-28` | 응답 헤더에 비 ASCII 없음 | run | `validate/v11_web.py:73` | **★ 없음** | 없음 | guide/03_이력.md:188 · chapters/61-web.md:1434 · chapters/61-web.md:2154 |
| `V11-29` | 렌더된 폼의 csrf_token 이 비어 있지 않음 | run | `validate/v11_web.py:77` | **★ 없음** | 없음 | guide/03_이력.md:189 · chapters/61-web.md:395 · chapters/61-web.md:2155 |
| `V11-30` | 시안 ↔ 템플릿 대조 통과 | run | `validate/v11_web.py:81` | **★ 없음** | 없음 | guide/03_이력.md:190 · chapters/61-web.md:350 · chapters/61-web.md:1534 |
| `V11-31` | must_change_secret=1 에서 /password 가 200 | run | `validate/v11_web.py:84` | **★ 없음** | 없음 | chapters/61-web.md:1378 · chapters/61-web.md:2157 |
| `V11-32` | known_issues 의 키가 전부 targets 에 있음 | run | `validate/v11_web.py:89` | **★ 없음** | 없음 | ref/B-config.md:377 · guide/03_이력.md:196 · chapters/61-web.md:2158 |
| `V11-33` | POST 가 저장 없이 성공 메시지를 내지 않음 | run | `validate/v11_web.py:139` | **★ 없음** | 없음 | guide/03_이력.md:220 · chapters/61-web.md:2037 · chapters/61-web.md:2159 |
| `V11-34` | 화면이 요청당 쿼리 상한을 넘지 않음 | run | `validate/v11_web.py:145` | **★ 없음** | 없음 | trace/41-view.md:22 · trace/41-view.md:70 · trace/RULES.md:164 |
| `V11-35` | 중첩 if 가 안쪽부터 닫힘 | run | `validate/v11_web.py:142` | **★ 없음** | 없음 | guide/03_이력.md:233 · chapters/61-web.md:1333 · chapters/61-web.md:2161 |
| `V11-36` | 잘못된 쿼리 파라미터가 500 을 내지 않음 | run | `validate/v11_web.py:149` | **★ 없음** | 없음 | guide/03_이력.md:235 · chapters/61-web.md:1342 · chapters/61-web.md:2162 |
| `V11-37` | POST 가 예상 밖 500 을 내지 않음 | run | `validate/v11_web.py:153` | **★ 없음** | 없음 | — |
| `V11-38` | 템플릿이 쓰는 값을 뷰가 넘김 | run | `validate/v11_web.py:158` | **★ 없음** | 없음 | — |
| `V11-39` | 저장 단추가 실제로 저장함 | run | `validate/v11_web.py:163` | **★ 없음** | 없음 | — |
| `V11-40` | 반입분의 origin 이 'import' 임 | run | `validate/v11_web.py:171` | **★ 없음** | 없음 | trace/11-store.md:36 · guide/03_이력.md:263 · guide/03_이력.md:271 |
| `V11-41` | 반입 뒤 S5~S10 이 이어서 돎 | run | `validate/v11_web.py:176` | **★ 없음** | 없음 | guide/03_이력.md:263 · chapters/61-web.md:2164 · chapters/60-admin/c-tools.md:213 |
| `V11-42` | S4 완료 행의 actual 이 'import' 임 | run | `validate/v11_web.py:627` | **★ 없음** | 없음 | guide/03_이력.md:264 · chapters/61-web.md:2165 · chapters/60-admin/c-tools.md:295 |
| `V11-43` | 브라우저 수집분의 origin 이 'browser' 임 | run | `validate/v11_web.py:181` | **★ 없음** | 없음 | trace/02-collect.md:63 · trace/60-admin.md:99 · trace/60-admin.md:100 |
| `V11-44` | 사람 확인 없이 저장되지 않음 | run | `validate/v11_web.py:186` | **★ 없음** | 없음 | trace/60-admin.md:99 · trace/60-admin.md:100 · trace/60-admin.md:102 |
| `V11-45` | CLI 로만 되는 기능이 없음 | run | `validate/v11_web.py:403` | **★ 없음** | 없음 | trace/00-standard.md:38 · trace/60-admin.md:28 · trace/60-admin.md:29 |
| `V11-46` | 반입으로 연 단계의 actual 이 'import' 임 | run | `validate/v11_web.py:622` | **★ 없음** | 없음 | trace/13-pipeline.md:39 · trace/RULES.md:223 · guide/03_이력.md:278 |
| `V11-47` | 브라우저 수집이 한 번에 max_form_bytes 를 넘기지 않음 | run | `validate/v11_web.py:608` | **★ 없음** | 없음 | trace/02-collect.md:23 · trace/02-collect.md:24 · trace/60-admin.md:107 |
| `V11-48` | 전 차종 수집에 확인 절차가 있음 | run | `validate/v11_web.py:614` | **★ 없음** | 없음 | trace/02-collect.md:26 · trace/60-admin.md:114 · trace/60-admin.md:116 |
| `V11-49` | 한 차종 실패가 나머지를 멈추지 않음 | run | `validate/v11_web.py:618` | **★ 없음** | 없음 | trace/60-admin.md:114 · trace/60-admin.md:115 · trace/60-admin.md:116 |
| `V11-51` | 진행 화면이 스스로 갱신됨 | run | `validate/v11_web.py:600` | **★ 없음** | 없음 | trace/14-web.md:127 · trace/60-admin.md:147 · trace/60-admin.md:152 |
| `V11-52` | 진행 화면에 실행 단추가 없음 | run | `validate/v11_web.py:604` | **★ 없음** | 없음 | trace/60-admin.md:147 · trace/60-admin.md:152 · trace/60-admin.md:154 |
| `V11-53` | 진행 판정이 큐만 보지 않음 | run | `validate/v11_web.py:191` | **★ 없음** | 없음 | trace/14-web.md:128 · trace/60-admin.md:150 · guide/01_요구사항.md:759 |
| `V11-54` | 메뉴에 경로가 그대로 나오지 않음 | run | `validate/v11_web.py:197` | **★ 없음** | 없음 | trace/14-web.md:122 · guide/03_이력.md:293 · guide/03_이력.md:416 |
| `V11-55` | 목록에 전체 건수와 쪽이 표시됨 | run | `validate/v11_web.py:202` | **★ 없음** | 없음 | trace/14-web.md:62 · trace/41-view.md:63 · chapters/61-web.md:2177 |
| `V11-56` | 대표 사진 경로가 저장됨 | run | `validate/v11_web.py:207` | **★ 없음** | 없음 | chapters/61-web.md:546 · chapters/61-web.md:2178 |
| `V11-57` | 사진 없는 매물이 화면을 무너뜨리지 않음 | run | `validate/v11_web.py:211` | **★ 없음** | 없음 | guide/03_이력.md:293 · chapters/61-web.md:547 · chapters/61-web.md:2179 |
| `V11-58` | 쪽을 넘겨도 조건이 남음 | run | `validate/v11_web.py:216` | **★ 없음** | 없음 | — |
| `V11-59` | 시안의 클래스가 CSS 에 있음 | run | `validate/v11_web.py:220` | **★ 없음** | 없음 | trace/00-standard.md:207 · trace/00-standard.md:208 · trace/00-standard.md:209 |
| `V11-60` | 시안 CSS 를 다시 만들지 않음 | run | `validate/v11_web.py:224` | **★ 없음** | 없음 | trace/00-standard.md:207 · trace/00-standard.md:208 · trace/00-standard.md:209 |
| `V11-61` | 이어질 수 있는 값이 링크임 | run | `validate/v11_web.py:228` | **★ 없음** | 없음 | trace/14-web.md:57 · guide/03_이력.md:295 · chapters/61-web.md:1201 |
| `V11-62` | 코드·줄임말에 title 이 있음 | run | `validate/v11_web.py:232` | **★ 없음** | 없음 | trace/14-web.md:58 · trace/14-web.md:126 · chapters/61-web.md:1202 |
| `V11-63` | 매물 화면에 원문 링크가 있음 | run | `validate/v11_web.py:236` | **★ 없음** | 없음 | trace/14-web.md:59 · guide/03_이력.md:481 · guide/03_이력.md:847 |
| `V11-64` | 고를 수 있는 값이 목록으로 제공됨 | run | `validate/v11_web.py:240` | **★ 없음** | 없음 | trace/14-web.md:123 · chapters/61-web.md:1240 · chapters/61-web.md:2185 |
| `V11-65` | 기본 정렬이 규격대로임 | run | `validate/v11_web.py:245` | **★ 없음** | 없음 | trace/14-web.md:61 · chapters/61-web.md:1261 · chapters/61-web.md:2186 |
| `V11-66` | 필터가 목록 위에 있음 | run | `validate/v11_web.py:249` | **★ 없음** | 없음 | trace/14-web.md:60 · chapters/61-web.md:1282 · chapters/61-web.md:2187 |
| `V11-67` | 단추가 켜짐·꺼짐을 오감 | run | `validate/v11_web.py:252` | **★ 없음** | 없음 | guide/03_이력.md:295 · chapters/61-web.md:1283 · chapters/61-web.md:2188 |
| `V11-68` | v1 이 낸 열이 v2 에도 있음 | run | `validate/v11_web.py:256` | **★ 없음** | 없음 | trace/14-web.md:39 · trace/14-web.md:40 · guide/01_요구사항.md:511 |
| `V11-69` | v1 이 가진 조작이 v2 에도 있음 | run | `validate/v11_web.py:261` | **★ 없음** | 없음 | trace/14-web.md:41 · guide/01_요구사항.md:511 · guide/01_요구사항.md:521 |
| `V11-70` | 좁은 폭에서 값이 사라지지 않음 | run | `validate/v11_web.py:266` | **★ 없음** | 없음 | trace/14-web.md:21 · guide/01_요구사항.md:525 · guide/01_요구사항.md:535 |
| `V11-71` | 가로 스크롤로 떠넘기지 않음 | run | `validate/v11_web.py:274` | **★ 없음** | 없음 | guide/01_요구사항.md:525 · guide/01_요구사항.md:535 · guide/01_요구사항.md:536 |
| `V11-72` | 빈 주소로 가는 링크가 없음 | run | `validate/v11_web.py:278` | **★ 없음** | 없음 | — |
| `V11-73` | 화면마다 값이 나옴 | run | `validate/v11_web.py:588` | **★ 없음** | 없음 | — |
| `V11-74` | 숫자가 단위와 함께 나옴 | run | `validate/v11_web.py:591` | **★ 없음** | 없음 | — |
| `V11-75` | 링크가 유효함 | run | `validate/v11_web.py:594` | **★ 없음** | 없음 | — |
| `V11-76` | 화면 크기·시간이 상한 안 | run | `validate/v11_web.py:597` | **★ 없음** | 없음 | UI_REVIEW.md:1032 · guide/03_이력.md:759 · guide/03_이력.md:761 |
| `V11-77` | 시안의 시각 요소가 렌더 결과에 나옴 | run | `validate/v11_web.py:283` | **★ 없음** | 없음 | trace/14-web.md:98 · trace/14-web.md:101 · trace/14-web.md:102 |
| `V11-78` | 좁은 폭에서 글자가 세로로 안 떨어짐 | run | `validate/v11_web.py:289` | **★ 없음** | 없음 | trace/14-web.md:124 · guide/03_이력.md:393 · chapters/00-standard.md:1265 |
| `V11-79` | 축 칸에 맨 숫자가 나오지 않음 | run | `validate/v11_web.py:574` | **★ 없음** | 없음 | trace/14-web.md:53 · guide/02_결함대장.md:29 · guide/02_결함대장.md:39 |
| `V11-80` | 사진이 최소 크기 이상 | run | `validate/v11_web.py:579` | **★ 없음** | 없음 | trace/14-web.md:27 · guide/01_요구사항.md:539 · guide/01_요구사항.md:549 |
| `V11-81` | 신차가 · 시세 · 가격 셋이 함께 나옴 | run | `validate/v11_web.py:583` | **★ 없음** | 없음 | trace/41-view.md:45 · guide/01_요구사항.md:205 · guide/01_요구사항.md:215 |
| `V11-82` | 정적 파일에 버전이 붙음 | run | `validate/v11_web.py:569` | **★ 없음** | 없음 | trace/14-web.md:31 |
| `V11-85` | 트림에 세부등급이 포함됨 | run | `validate/v11_web.py:413` | **★ 없음** | 없음 | trace/05-score.md:65 · trace/05-score.md:66 · trace/14-web.md:52 |
| `V11-87` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:156 · guide/01_요구사항.md:219 · guide/01_요구사항.md:229 |
| `V11-88` | — | — | **★ 코드에 없다** | — | — | guide/01_요구사항.md:161 · guide/01_요구사항.md:567 · guide/01_요구사항.md:577 |
| `V11-92` | 신차가가 등급기준 + 옵션 합 | run | `validate/v11_web.py:565` | **★ 없음** | 없음 | trace/05-score.md:35 · guide/03_이력.md:320 · chapters/30-score/a-frame.md:646 |
| `V11-93` | — | — | **★ 코드에 없다** | — | — | trace/14-web.md:47 · guide/01_요구사항.md:162 · guide/01_요구사항.md:581 |
| `V11-94` | 추천 조건이 화면에 적혀 있음 | run | `validate/v11_web.py:427` | **★ 없음** | 없음 | trace/14-web.md:74 · guide/01_요구사항.md:595 · guide/01_요구사항.md:605 |
| `V11-96` | ♡ 가 제목 줄에 있음 | run | `validate/v11_web.py:423` | **★ 없음** | 없음 | trace/14-web.md:56 · guide/03_이력.md:324 · chapters/61-web.md:807 |
| `V11-98` | 큰 원문을 조각으로 보내고 이어붙이는가 | run | `validate/v11_web.py:554` | **★ 없음** | 없음 | trace/02-collect.md:25 · trace/60-admin.md:167 · trace/60-admin.md:168 |
| `V11-99` | 같은 화면에서 여러 번 POST 가 되는가 | run | `validate/v11_web.py:559` | **★ 없음** | 없음 | trace/60-admin.md:170 · trace/60-admin.md:171 · guide/03_이력.md:327 |
| `V11-100` | 목록에 옵션 개수와 합계가 나옴 | run | `validate/v11_web.py:418` | **★ 없음** | 없음 | trace/05-score.md:67 · trace/14-web.md:51 · guide/03_이력.md:332 |
| `V11-102` | 비교가 옵션 차이만 냄 | run | `validate/v11_web.py:386` | **★ 없음** | 없음 | trace/14-web.md:115 · guide/03_이력.md:332 · chapters/61-web.md:719 |
| `V11-103` | 목록이 오래되면 화면에 나옴 | run | `validate/v11_web.py:408` | **★ 없음** | 없음 | trace/02-collect.md:53 · trace/41-view.md:31 · trace/60-admin.md:195 |
| `V11-104` | 템플릿 문법이 화면에 새지 않음 | run | `validate/v11_web.py:294` | **★ 없음** | 없음 | guide/01_요구사항.md:637 · guide/01_요구사항.md:646 · guide/01_요구사항.md:647 |
| `V11-105` | 화면 위아래가 어긋나지 않음 | run | `validate/v11_web.py:549` | **★ 없음** | 없음 | guide/03_이력.md:344 · chapters/30-score/g-absolute.md:148 |
| `V11-106` | 값 자리에 「—」가 없음 | run | `validate/v11_web.py:299` | **★ 없음** | 없음 | trace/14-web.md:67 · trace/RULES.md:166 · trace/RULES.md:265 |
| `V11-107` | 화면별 사진 크기가 부록 G 와 같음 | run | `validate/v11_web.py:544` | **★ 없음** | 없음 | trace/14-web.md:26 · trace/14-web.md:77 · guide/03_이력.md:351 |
| `V11-108` | 좁은 폭에서 한 화면에 매물 2개 이상 | run | `validate/v11_web.py:346` | **★ 없음** | 없음 | trace/14-web.md:28 · chapters/61-web/a-common.md:64 |
| `V11-109` | 카드가 부록 G 줄 수 상한을 안 넘음 | run | `validate/v11_web.py:352` | **★ 없음** | 없음 | trace/14-web.md:75 · trace/14-web.md:78 · chapters/00-standard.md:1265 |
| `V11-110` | 상세 절 순서가 부록 G 와 같음 | run | `validate/v11_web.py:341` | **★ 없음** | 없음 | trace/14-web.md:84 · chapters/61-web/d-detail.md:73 |
| `V11-111` | — | — | **★ 코드에 없다** | — | — | chapters/61-web/e-compare.md:38 |
| `V11-113` | 다섯 폭 스크린샷이 있음 | run | `validate/v11_web.py:306` | **★ 없음** | 없음 | trace/14-web.md:23 · guide/03_이력.md:356 · guide/03_이력.md:843 |
| `V11-114` | 폭마다 부록 G 의 배치임 | run | `validate/v11_web.py:312` | **★ 없음** | 없음 | trace/14-web.md:22 · chapters/61-web/f-width.md:33 |
| `V11-115` | 어느 폭에서도 글자가 세로로 안 떨어짐 | run | `validate/v11_web.py:318` | **★ 없음** | 없음 | trace/14-web.md:24 · guide/03_이력.md:356 · chapters/61-web/f-width.md:34 |
| `V11-116` | 카드 전체가 상세 링크임 | run | `validate/v11_web.py:324` | **★ 없음** | 없음 | trace/14-web.md:64 · guide/03_이력.md:357 · guide/03_이력.md:395 |
| `V11-117` | 터치로 미리보기가 뜸 | run | `validate/v11_web.py:330` | **★ 없음** | 없음 | trace/14-web.md:65 · chapters/61-web/f-width.md:60 |
| `V11-118` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:357 · chapters/61-web/d-detail.md:120 · chapters/61-web/f-width.md:78 |
| `V11-119` | 화면마다 부록 G 가 정한 차트가 있음 | run | `validate/v11_web.py:335` | **★ 없음** | 없음 | trace/14-web.md:91 · trace/14-web.md:92 · trace/14-web.md:99 |
| `V11-120` | 매물마다 사이트별 구매 총액이 나옴 | run | `validate/v11_web.py:358` | **★ 없음** | 없음 | trace/40-report.md:67 · trace/40-report.md:71 · trace/40-report.md:72 |
| `V11-121` | 여러 사이트에 있는 차는 총액을 나란히 냄 | run | `validate/v11_web.py:364` | **★ 없음** | 없음 | trace/40-report.md:69 · trace/40-report.md:70 · trace/40-report.md:71 |
| `V11-122` | 리포트를 화면에서 읽을 수 있음 | run | `validate/v11_web.py:538` | **★ 없음** | 없음 | trace/40-report.md:74 · trace/40-report.md:75 · trace/40-report.md:76 |
| `V11-123` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:388 · chapters/61-web/h-admin.md:29 · chapters/61-web/h-admin.md:272 |
| `V11-124` | — | — | **★ 코드에 없다** | — | — | chapters/61-web/h-admin.md:85 · chapters/61-web/h-admin.md:273 |
| `V11-128` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:390 · chapters/00-standard.md:2136 · chapters/61-web/i-admin-mock.md:389 |
| `V11-129` | — | — | **★ 코드에 없다** | — | — | chapters/00-standard.md:2037 · chapters/61-web/i-admin-mock.md:390 · chapters/61-web/j-admin-mock2.md:491 |
| `V11-131` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:392 · chapters/00-standard.md:2213 |
| `V11-132` | 상세에 큰 사진과 썸네일이 있음 | run | `validate/v11_web.py:532` | **★ 없음** | 없음 | guide/03_이력.md:394 · chapters/61-web/d-detail.md:106 |
| `V11-133` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:396 · chapters/61-web/d-detail.md:159 |
| `V11-134` | 상세에 「받은 원문」 절이 있음 | run | `validate/v11_web.py:369` | **★ 없음** | 없음 | guide/03_이력.md:397 · guide/03_이력.md:427 · chapters/00-standard.md:1962 |
| `V11-135` | 파서가 없어도 원문을 그대로 냄 | run | `validate/v11_web.py:375` | **★ 없음** | 없음 | chapters/61-web/d-detail.md:193 |
| `V11-136` | 받은 것 중 묻혀 있는 것이 없음 | run | `validate/v11_web.py:380` | **★ 없음** | 없음 | guide/03_이력.md:397 · chapters/61-web/d-detail.md:211 |
| `V11-137` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:402 · chapters/61-web/d-detail.md:258 |
| `V11-138` | — | — | **★ 코드에 없다** | — | — | chapters/61-web/d-detail.md:259 · chapters/61-web/d-detail.md:270 |
| `V11-141` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:404 · chapters/61-web/j-admin-mock2.md:215 |
| `V11-143` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:405 · chapters/61-web/i-admin-mock.md:209 |
| `V11-144` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:405 · chapters/61-web/i-admin-mock.md:248 |
| `V11-147` | 조각 절단면이 글자 경계임 | run | `validate/v11_web.py:391` | **★ 없음** | 없음 | guide/03_이력.md:409 |
| `V11-148` | 조각마다 길이·해시를 대조함 | run | `validate/v11_web.py:398` | **★ 없음** | 없음 | guide/03_이력.md:409 |
| `V11-149` | 조각 실패 문구에 서버 message 가 있음 | run | `validate/v11_web.py:526` | **★ 없음** | 없음 | guide/03_이력.md:414 |
| `V11-150` | 메뉴 라벨이 경로가 아님 | run | `validate/v11_web.py:521` | **★ 없음** | 없음 | guide/03_이력.md:416 · chapters/61-web.md:266 |
| `V11-151` | 부족액 문구가 화면에 없음 | run | `validate/v11_web.py:510` | **★ 없음** | 없음 | guide/03_이력.md:420 · chapters/41-view.md:454 |
| `V11-152` | cash_limit 을 한 곳에서만 읽음 | run | `validate/v11_web.py:515` | **★ 없음** | 없음 | guide/03_이력.md:420 · chapters/41-view.md:455 |
| `V11-153` | 기본 목록에 리스·렌트가 없음 | run | `validate/v11_web.py:432` | **★ 없음** | 없음 | guide/03_이력.md:440 |
| `V11-154` | 뺀 건수가 화면에 있음 | run | `validate/v11_web.py:437` | **★ 없음** | 없음 | — |
| `V11-155` | 차종·가격대 필터가 있음 | run | `validate/v11_web.py:441` | **★ 없음** | 없음 | — |
| `V11-156` | 필터 조건이 그대로 넘어감 | run | `validate/v11_web.py:505` | **★ 없음** | 없음 | guide/03_이력.md:440 |
| `V11-157` | 상단 메뉴가 다섯을 넘지 않음 | run | `validate/v11_web.py:493` | **★ 없음** | 없음 | guide/03_이력.md:447 · guide/03_이력.md:458 · guide/03_이력.md:463 |
| `V11-158` | 내린 화면이 열리고 ★ 들어가는 문이 있음 | run | `validate/v11_web.py:499` | **★ 없음** | 없음 | UI_REVIEW.md:562 · UI_REVIEW.md:855 · guide/03_이력.md:565 |
| `V11-159` | 상세 11개 절이 규격 순서로 있음 | run | `validate/v11_web.py:452` | **★ 없음** | 없음 | CROSS_SITE_COMPARE.md:161 · UI_REVIEW.md:88 · UI_REVIEW.md:328 |
| `V11-160` | 1 절에 「왜 그 등급인가」 문장이 있음 | run | `validate/v11_web.py:457` | **★ 없음** | 없음 | guide/03_이력.md:511 · chapters/41-view.md:98 |
| `V11-161` | 3 절에 총 구매비용 표가 있음 | run | `validate/v11_web.py:463` | **★ 없음** | 없음 | chapters/41-view.md:99 |
| `V11-162` | 목록 한 행의 칸이 8을 넘지 않음 | run | `validate/v11_web.py:481` | **★ 없음** | 없음 | chapters/41-view.md:390 |
| `V11-163` | 네 묶음 막대가 목록에 있음 | run | `validate/v11_web.py:487` | **★ 없음** | 없음 | chapters/41-view.md:391 |
| `V11-164` | 점수 필터가 SQL 로 걸림 | run | `validate/v11_web.py:469` | **★ 없음** | 없음 | chapters/41-view.md:424 |
| `V11-165` | 고른 조건이 문장으로 나옴 | run | `validate/v11_web.py:475` | **★ 없음** | 없음 | KCAR_API.md:354 · guide/03_이력.md:447 · guide/03_이력.md:466 |
| `V11-166` | 비교에 막대 넷·총 구매비용·결론이 있음 | run | `validate/v11_web.py:446` | **★ 없음** | 없음 | guide/03_이력.md:449 · chapters/41-view.md:495 |
| `V13-08` | — | — | **★ 코드에 없다** | — | — | guide/03_이력.md:446 · chapters/13-pipeline.md:346 |

## ② 죽은 검사 — 한 번도 안 돌았다

★ 「있다」와 「돈다」는 다릅니다. 안 도는 검사는 지키는 척만 합니다.

- `S1` 디렉터리 (STEP 15) — `tools/check_src.py`
- `S10` 도메인 예외 (STEP 3) — `tools/check_src.py`
- `S11` 분석 계층 순수성 (STEP 2) — `tools/check_src.py`
- `S12` 축 파일 STEP 주석 — `tools/check_src.py`
- `S13` 본문 config 예시 대조 — `tools/check_src.py`
- `S14` 상수 등록·성격 (V4-17) — `tools/check_src.py`
- `S14-1` 화면에 배점을 박지 않음 (V4-17) — `tools/check_src.py`
- `S15` 계층 의존 (STEP 15) — `tools/check_src.py`
- `S16` 검증 코드 대조 — `tools/check_src.py`
- `S2` 구조체 정의 — `tools/check_src.py`
- `S23` 실행 환경 (Python 3.11+) — `tools/check_src.py`
- `S24` 시험 격리 (운영 DB 미사용) — `tools/check_src.py`
- `S25` 형상 관리 (미커밋 없음) — `tools/check_src.py`
- `S26` 작업 기록 (6절 · 이름 규칙) — `tools/check_src.py`
- `S27` 기능마다 화면 (CLI 는 완성이 아니다) — `tools/check_src.py`
- `S28` 검사 색인 (규격 ↔ 코드) — `tools/check_src.py`
- `S29-0` 가벼운 점검 (4시간 · 실제로 돎) — `tools/check_src.py`
- `S29-4` 점검이 찾은 fatal 을 고침 — `tools/check_src.py`
- `S3` 함수 정의 — `tools/check_src.py`
- `S34-1` 표의 규격이 실재 — `tools/check_src.py`
- `S34-2` 표의 소스·검사가 실재 — `tools/check_src.py`
- `S34-3` 추적표 빈 칸을 센다 — `tools/check_src.py`
- `S34-4` 규격이 표에 있음 — `tools/check_src.py`
- `S35-1` 자기 칸만 고침 — `tools/check_src.py`
- `S36-1` 「정식 서비스 착수」 목록이 있음 — `tools/check_src.py`
- `S37-1` 파는 쪽 개념이 안 남아 있음 — `tools/check_src.py`
- `S38-4` 상태가 세 칸에서 유도한 값과 같음 — `tools/check_src.py`
- `S38-5` 「!」·「?」 가 도구 실행 뒤에도 남음 — `tools/check_src.py`
- `S39-1` R 마다 층이 적혀 있음 — `tools/check_src.py`
- `S39-2` 화면 층이 아닌데 「화면 없음」이 아님 — `tools/check_src.py`
- `S4` 테이블 DDL (STEP 28) — `tools/check_src.py`
- `S43-2` 규격의 축 id 가 config 에 있는가 — `validate/v0_guide.py`
- `S43-2b` config 축 id 가 규격 이름인가 — `validate/v0_guide.py`
- `S43-2c` HDA 가 저장소에 없는가 — `validate/v0_guide.py`
- `S43-3` 버전이 이력 마지막과 같은가 — `validate/v0_guide.py`
- `S44-1` 가리키는 명령서가 실제로 있는가 — `validate/v0_guide.py`
- `S44-2` 명령서가 하나뿐인가 — `validate/v0_guide.py`
- `S44-3` 규격을 명령서가 가리키는가 — `validate/v0_guide.py`
- `S44-4` 명령서에 수집 범위가 있는가 — `validate/v0_guide.py`
- `S44-5` 명령서이 사이트를 한 가지로 적는가 — `validate/v0_guide.py`
- `S45-1` f-table 절 제목과 표가 같은가 — `validate/v0_guide.py`
- `S45-2` 시안에 옛 배점·분모가 없는가 — `validate/v0_guide.py`
- `S45-3` 규격에 옛 총점이 없는가 — `validate/v0_guide.py`
- `S45-4` 배점표가 config 에서 생성한 것과 같은가 — `validate/v0_guide.py`
- `S45-5` 규격이 배점을 손으로 적지 않는가 — `validate/v0_guide.py`
- `S46-100` 시안의 낱말 차례가 화면과 같은가 — `validate/v0_guide.py`
- `S46-102` 「전기만」에 전기 아닌 것이 없는가 — `validate/v0_guide.py`
- `S46-103` 시안의 크기·자리 값을 담았는가 — `validate/v0_guide.py`
- `S46-115` 시키는 화면이 스스로 안 바뀌는가 — `validate/v0_guide.py`
- `S46-116` 사유에 쉬운 말이 있는가 — `validate/v0_guide.py`
- `S46-117` 목록을 받는 수집기가 팔린 차를 거르는가 — `validate/v0_guide.py`
- `S46-118` 하트가 자기 카드 안에 앉는가 — `validate/v0_guide.py`
- `S46-120` 등록부의 감사 열쇠가 목록 열쇠와 같은가 — `validate/v0_guide.py`
- `S46-121` 머리띠 규칙이 한 곳에만 있는가 — `validate/v0_guide.py`
- `S46-122` 머리·발이 한 곳에만 있는가 — `validate/v0_guide.py`
- `S46-123` 토스 표에 없는 색이 없는가 — `validate/v0_guide.py`
- `S46-124` DB 를 PRAGMA 없이 열지 않는가 — `validate/v0_guide.py`
- `S46-125` 고른 정렬 축이 정말 먹는가 — `validate/v0_guide.py`
- `S46-126` 수집기가 통신·sleep 을 트랜잭션 밖에서 하는가 — `validate/v0_guide.py`
- `S46-127` 수집기마다 화면이나 타이머가 있는가 — `validate/v0_guide.py`
- `S46-128` 묶어 쓰는 단계가 다른 쓰기에 창을 주는가 — `validate/v0_guide.py`
- `S46-129` 표의 합이 맞는가 — `validate/v0_guide.py`
- `S46-130` 합계표가 문서마다 하나인가 — `validate/v0_guide.py`
- `S46-131` 「쪽넘김이 없다」에 실측이 있는가 — `validate/v0_guide.py`
- `S46-132` 인계문이 다시 재라고 적는가 — `validate/v0_guide.py`
- `S46-133` 검사 구멍이 밀린일에 있는가 — `validate/v0_guide.py`
- `S46-134` 질의와 규격이 어긋나지 않는가 — `validate/v0_guide.py`
- `S46-135` 일반화에 표본이 있는가 — `validate/v0_guide.py`
- `S46-136` 규격의 warn 수가 지금 값과 같은가 — `validate/v0_guide.py`
- `S46-137` 질의 열쇠를 읽는 코드가 있는가 — `validate/v0_guide.py`
- `S46-138` 「전량」에 세는 법이 있는가 — `validate/v0_guide.py`
- `S46-139` 「칸이 비었다」에 전수가 있는가 — `validate/v0_guide.py`
- `S46-140` 쓰는 호스트가 robots 문서에 있는가 — `validate/v0_guide.py`
- `S46-141` 거르개 판정에 실측이 있는가 — `validate/v0_guide.py`
- `S46-142` 「N 사이트」가 config 와 같은가 — `validate/v0_guide.py`
- `S46-143` 마스터께 올릴 것이 세어졌는가 — `validate/v0_guide.py`
- `S46-144` 「비었다」가 ⑤·⑥·⑦ 로 갈렸는가 — `validate/v0_guide.py`
- `S46-145` 마스터께 드리는 표에 수의 뜻이 있는가 — `validate/v0_guide.py`
- `S46-146` 「안 준다」를 쓰며 파서를 봤는가 — `validate/v0_guide.py`
- `S46-147` 「안 준다」의 표본이 열 건인가 — `validate/v0_guide.py`
- `S46-148` 「축이 빈다」가 칼럼·파서를 짚는가 — `validate/v0_guide.py`
- `S46-149` 자백이 닫혔는가 — `validate/v0_guide.py`
- `S46-150` 규격의 칼럼이 DDL 에 있는가 — `validate/v0_guide.py`
- `S46-152` 마지막 개발 회차를 읽었는가 — `validate/v0_guide.py`
- `S46-153` 「마스터 몫」이 진짜 마스터 몫인가 — `validate/v0_guide.py`
- `S46-154` 마스터 말씀이 요구 추적표에 있는가 — `validate/v0_guide.py`
- `S46-155` 화면 규격마다 시안이 있는가 — `validate/v0_guide.py`
- `S46-156` 개발측 물음의 답이 규격에 있는가 — `validate/v0_guide.py`
- `S46-157` 성능 판정에 시간이 있는가 — `validate/v0_guide.py`
- `S46-158` 용량 판정에 수가 있는가 — `validate/v0_guide.py`
- `S46-159` 설계도가 할 수 있는 것만 시키는가 — `validate/v0_guide.py`
- `S46-160` 전기차 누유가 만점·분모 910 인가 — `validate/v0_guide.py`
- `S46-161` 「사이트가 안 준다」에 증거가 있는가 — `validate/v0_guide.py`
- `S46-162` 오판이 약속한 검사가 실제로 있는가 — `validate/v0_guide.py`
- `S46-163` 시안마다 라우팅 표에 주소가 있는가 — `validate/v0_guide.py`
- `S46-164` 개발 회차의 「마스터 몫」에 답을 냈는가 — `validate/v0_guide.py`
- `S46-165` 「못 잰다」가 진짜인가 — `validate/v0_guide.py`
- `S46-166` 마스터 확정이 장 규격에 닿았는가 — `validate/v0_guide.py`
- `S46-168` 검사가 예외를 수로 내는가 — `validate/v0_guide.py`
- `S46-21` 시안 한 파일에 화면이 하나인가 — `validate/v0_guide.py`
- `S46-22` 시안 절 차례가 화면과 같은가 — `validate/v0_guide.py`
- `S46-23` 빈 site_query 가 없는가 — `validate/v0_guide.py`
- `S46-24` facet 미확인 차종이 없는가 — `validate/v0_guide.py`
- `S46-30` INDEX 가 docs 를 다 가리키는가 — `validate/v0_guide.py`
- `S46-31` 규격이 있는 사이트가 config 에 있는가 — `validate/v0_guide.py`
- `S46-32` 생성물이 최신인가 — `validate/v0_guide.py`
- `S46-36` 폐기된 요구가 규격에 안 살아 있는가 — `validate/v0_guide.py`
- `S46-40` 「진행」인 요구의 문서가 바뀌었는가 — `validate/v0_guide.py`
- `S46-41` 사이트 status 가 규격의 셋 안인가 — `validate/v0_guide.py`
- `S46-45` 제원이 목록에 안 나오는가 — `validate/v0_guide.py`
- `S46-46` 금지 제원 열 항목이 화면에 없는가 — `validate/v0_guide.py`
- `S46-54` 짝 중 등급이 두 칸 갈린 것 — `validate/v0_guide.py`
- `S46-55` 짝 중 값이 30% 갈린 것 — `validate/v0_guide.py`
- `S46-56` 짝 중 사고 판정이 갈린 것 — `validate/v0_guide.py`
- `S46-65` 판본이 하루 넘게 오래되지 않았는가 — `validate/v0_guide.py`
- `S46-66` 화면이 낸 링크가 인코딩돼 있는가 — `validate/v0_guide.py`
- `S46-67` 시안 이름이 app.css 와 안 겹치는가 — `validate/v0_guide.py`
- `S46-68` 관심이 모바일 기준 카드인가 — `validate/v0_guide.py`
- `S46-74` 한 쪽 장 수가 규격과 같은가 — `validate/v0_guide.py`
- `S46-75` v4m 여덟 장 공통 규칙 — `validate/v0_guide.py`
- `S46-76` 수집기가 원문을 남기는가 — `validate/v0_guide.py`
- `S46-77` KB 는 우리 20종만 받는가 — `validate/v0_guide.py`
- `S46-78` 엔카 전용 경로가 좁혀 있는가 — `validate/v0_guide.py`
- `S46-87` 부른 주소가 그 매물의 사이트인가 — `validate/v0_guide.py`
- `S46-88` 엔카가 막히면 화면이 까닭을 말하는가 — `validate/v0_guide.py`
- `S46-90` 근거가 절반도 없는데 등급을 매기지 않는가 — `validate/v0_guide.py`
- `S46-91` 받은 원문이 저장까지 갔는가 — `validate/v0_guide.py`
- `S46-92` 브라우저 수집이 0건을 받았는가 — `validate/v0_guide.py`
- `S46-94` 원문 문이 그 매물의 사이트로 가는가 — `validate/v0_guide.py`
- `S46-95` 배포된 화면이 다 열리는가 — `validate/v0_guide.py`
- `S46-96` 사이트가 파는 차종인데 코드가 없는가 — `validate/v0_guide.py`
- `S46-97` 원문이 source_id 로 매물에 이어지는가 — `validate/v0_guide.py`
- `S46-98` 시안의 낱말이 화면에 있는가 — `validate/v0_guide.py`
- `S46-99` 로그인하면 관심·관리가 열리는가 — `validate/v0_guide.py`
- `S5` config 키 (V4-15) — `tools/check_src.py`
- `S6` 배점 검산 (불변식 ⑤) — `tools/check_src.py`
- `S7` 매직 넘버 (V4-13) — `tools/check_src.py`
- `S8` 접미사 규칙 (STEP 4) — `tools/check_src.py`
- `S9` 금지 근거 (STEP 14) — `tools/check_src.py`
- `V1-01` expected == requested + not_requested — `validate/v1_collect.py`
- `V1-02` not_requested == 0 — `validate/v1_collect.py`
- `V1-03` requested == ok+empty+not_found+error — `validate/v1_collect.py`
- `V1-04` 형식 검증 거부 0 — `validate/v1_collect.py`
- `V1-05` raw_response 신규 == 응답 합 — `validate/v1_collect.py`
- `V1-06` 차종별 ok > 0 — `validate/v1_collect.py`
- `V1-07` 매물별 엔드포인트 4종 상태 존재 — `validate/v1_collect.py`
- `V1-08` 동일 코드 실패율 100% 인 엔드포인트 없음 — `validate/v1_collect.py`
- `V1-08b` 엔드포인트별 전량 404 없음 — `validate/v1_collect.py`
- `V1-09` 시간대별 실패율 상승 없음 — `validate/v1_collect.py`
- `V1-10` site_query 키가 전부 q 에 반영됨 — `validate/v1_collect.py`
- `V1-11` 예외로 종료된 실행이 없음 — `validate/v1_collect.py`
- `V1-12` 연속 실패 중단 시 ResumePoint 가 남음 — `validate/v1_collect.py`
- `V1-13` 껍데기를 거친 실행과 직접 실행의 인자가 같음 — `validate/v1_collect.py`
- `V1-14` diagnosis 호출 대상이 encarDiagnosis == 0 으로 좁혀짐 — `validate/v1_collect.py`
- `V1-15` expected == 요청 대상 수 (skipped 제외) — `validate/v1_collect.py`
- `V1-16` 이번 run_id 밖의 행을 보지 않음 — `validate/v1_collect.py`
- `V1-17` diagnosis 가 detail 뒤에 있음 — `validate/v1_collect.py`
- `V1-18` 빈 DB 에서도 검사가 돈다 — `validate/v1_collect.py`
- `V1-19` 이번 실행이 저장한 원문에 run_id 가 있음 — `validate/v1_collect.py`
- `V1-20` 카탈로그를 모델당 1회만 받음 — `validate/v1_collect.py`
- `V1-21` 받아 두고 안 펼쳐진 원문이 없음 — `validate/v1_collect.py`
- `V1-23` 필요한 조합 대비 받은 카탈로그 비율 — `validate/v1_collect.py`
- `V1-24` 받은 카탈로그가 매물과 이어짐 — `validate/v1_collect.py`
- `V1-25` ok 로 저장된 원문이 온전한가 — `validate/v1_collect.py`
- `V1-26` 판정 축이 통째로 비지 않음 — `validate/v1_collect.py`
- `V1-27` 확인 안 됨을 ①②③④ 로 가른 표가 있음 — `validate/v1_collect.py`
- `V1-28` ② ③ 건수가 지난번보다 안 늘었음 — `validate/v1_collect.py`
- `V10-01` admin 전용을 user 로 호출 시 PolicyError — `validate/v10_admin.py`
- `V10-02` 서버 권한 검증 존재 (화면 숨김 아님) — `validate/v10_admin.py`
- `V10-03` run_query 가 SELECT 외를 전건 거부 — `validate/v10_admin.py`
- `V10-04` run_query 판정이 AST 기반 (정규식 아님) — `validate/v10_admin.py`
- `V10-05` config 변경이 ConfigChange 없이 안 일어남 — `validate/v10_admin.py`
- `V10-06` 배점 저장 시 Σ == total_points — `validate/v10_admin.py`
- `V10-07` 성분 추가가 선택 가능 목록 안에서만 — `validate/v10_admin.py`
- `V10-08` 관리 도구가 core_* 를 UPDATE 하지 않음 — `validate/v10_admin.py`
- `V10-09` DevRequest 가 삭제되지 않음 — `validate/v10_admin.py`
- `V10-10` 문서 뷰어에 편집 경로 없음 — `validate/v10_admin.py`
- `V10-11` 실행 중 config 변경이 잠김 — `validate/v10_admin.py`
- `V10-12` 배점 조정 후 0점 성분 없음 — `validate/v10_admin.py`
- `V10-13` 웹에서 전면 재수집이 큐에 안 들어감 — `validate/v10_admin.py`
- `V10-14` components.{axis}.{component} 경로 읽기·쓰기 — `validate/v10_admin.py`
- `V10-15` 저장 전 배점 합 검사 — `validate/v10_admin.py`
- `V10-16` must_change_secret 계정이 다른 화면에 접근 못 함 — `validate/v10_admin.py`
- `V10-17` admin 수가 0 이 되는 변경이 거부됨 — `validate/v10_admin.py`
- `V10-18` core_pii · core_dealer_pii 조회가 거부됨 — `validate/v10_admin.py`
- `V10-19` 중지·비밀번호 변경 후 옛 세션이 anonymous — `validate/v10_admin.py`
- `V10-20` 로그인 실패 상한이 config 대로 돎 — `validate/v10_admin.py`
- `V10-22` queued 를 소비하는 코드가 있음 — `validate/v10_admin.py`
- `V10-23` 오래된 queued 가 화면에 표시됨 — `validate/v10_admin.py`
- `V10-24` 사전 확정에 사유가 남음 — `validate/v10_admin.py`
- `V10-25` 'list' 출처가 화면에 표시됨 — `validate/v10_admin.py`
- `V10-26` 목록 저장 후 큐에 작업이 들어감 — `validate/v10_admin.py`
- `V10-27` 중간 실패에서 다음 단계로 안 넘어감 — `validate/v10_admin.py`
- `V10-28` 타이머가 겹쳐 돌지 않음 — `validate/v10_admin.py`
- `V10-29` 목록 저장이 전건 재수집을 안 부름 — `validate/v10_admin.py`
- `V10-30` 재판정이 수집 없이 돎 — `validate/v10_admin.py`
- `V10-31` 자동 수집이 13:00 인가 — `validate/v10_admin.py`
- `V10-32` 사람 손이 필요한 작업이 낮 시간대인가 — `validate/v10_admin.py`
- `V10-33` 컴파일 실패가 PolicyError 로 안 감 — `validate/v10_admin.py`
- `V10-34` 거부 응답에 고칠 재료가 있음 — `validate/v10_admin.py`
- `V10-35` query_log 가 compile · policy 로 갈림 — `validate/v10_admin.py`
- `V10-36` 표를 누르면 컬럼이 보임 — `validate/v10_admin.py`
- `V10-37` 결과 표 위에 복사 단추가 있음 — `validate/v10_admin.py`
- `V10-38` 끊긴 실행이 큐를 막고 있지 않음 — `validate/v10_admin.py`
- `V11-01` web/ 에 SQL 문자열이 없음 — `validate/v11_web.py`
- `V11-02` 기본 바인딩이 127.0.0.1 — `validate/v11_web.py`
- `V11-03` 전 Route 에 role 이 지정됨 — `validate/v11_web.py`
- `V11-04` 템플릿에 산술 연산이 없음 — `validate/v11_web.py`
- `V11-05` {{! }} 사용처가 화이트리스트에 있음 — `validate/v11_web.py`
- `V11-06` 정적 경로 탈출이 거부됨 — `validate/v11_web.py`
- `V11-07` 쿠키에 role 문자열이 없음 — `validate/v11_web.py`
- `V11-08` 상태 변경이 GET 경로에 없음 — `validate/v11_web.py`
- `V11-09` 미리보기 없이 저장이 안 됨 — `validate/v11_web.py`
- `V11-10` 오류 화면에 스택 트레이스가 없음 — `validate/v11_web.py`
- `V11-100` 목록에 옵션 개수와 합계가 나옴 — `validate/v11_web.py`
- `V11-102` 비교가 옵션 차이만 냄 — `validate/v11_web.py`
- `V11-103` 목록이 오래되면 화면에 나옴 — `validate/v11_web.py`
- `V11-104` 템플릿 문법이 화면에 새지 않음 — `validate/v11_web.py`
- `V11-105` 화면 위아래가 어긋나지 않음 — `validate/v11_web.py`
- `V11-106` 값 자리에 「—」가 없음 — `validate/v11_web.py`
- `V11-107` 화면별 사진 크기가 부록 G 와 같음 — `validate/v11_web.py`
- `V11-108` 좁은 폭에서 한 화면에 매물 2개 이상 — `validate/v11_web.py`
- `V11-109` 카드가 부록 G 줄 수 상한을 안 넘음 — `validate/v11_web.py`
- `V11-11` result_* 가 비었을 때 안내가 나옴 — `validate/v11_web.py`
- `V11-110` 상세 절 순서가 부록 G 와 같음 — `validate/v11_web.py`
- `V11-113` 다섯 폭 스크린샷이 있음 — `validate/v11_web.py`
- `V11-114` 폭마다 부록 G 의 배치임 — `validate/v11_web.py`
- `V11-115` 어느 폭에서도 글자가 세로로 안 떨어짐 — `validate/v11_web.py`
- `V11-116` 카드 전체가 상세 링크임 — `validate/v11_web.py`
- `V11-117` 터치로 미리보기가 뜸 — `validate/v11_web.py`
- `V11-119` 화면마다 부록 G 가 정한 차트가 있음 — `validate/v11_web.py`
- `V11-12` 라우팅 표의 view 가 10·13장에 실재함 — `validate/v11_web.py`
- `V11-120` 매물마다 사이트별 구매 총액이 나옴 — `validate/v11_web.py`
- `V11-121` 여러 사이트에 있는 차는 총액을 나란히 냄 — `validate/v11_web.py`
- `V11-122` 리포트를 화면에서 읽을 수 있음 — `validate/v11_web.py`
- `V11-13` app.css 에 토큰 밖의 색값이 없음 — `validate/v11_web.py`
- `V11-132` 상세에 큰 사진과 썸네일이 있음 — `validate/v11_web.py`
- `V11-134` 상세에 「받은 원문」 절이 있음 — `validate/v11_web.py`
- `V11-135` 파서가 없어도 원문을 그대로 냄 — `validate/v11_web.py`
- `V11-136` 받은 것 중 묻혀 있는 것이 없음 — `validate/v11_web.py`
- `V11-14` 숫자 셀에 mono 가 걸려 있음 — `validate/v11_web.py`
- `V11-147` 조각 절단면이 글자 경계임 — `validate/v11_web.py`
- `V11-148` 조각마다 길이·해시를 대조함 — `validate/v11_web.py`
- `V11-149` 조각 실패 문구에 서버 message 가 있음 — `validate/v11_web.py`
- `V11-15` 화면이 빌드 산출물에 의존하지 않음 — `validate/v11_web.py`
- `V11-150` 메뉴 라벨이 경로가 아님 — `validate/v11_web.py`
- `V11-151` 부족액 문구가 화면에 없음 — `validate/v11_web.py`
- `V11-152` cash_limit 을 한 곳에서만 읽음 — `validate/v11_web.py`
- `V11-153` 기본 목록에 리스·렌트가 없음 — `validate/v11_web.py`
- `V11-154` 뺀 건수가 화면에 있음 — `validate/v11_web.py`
- `V11-155` 차종·가격대 필터가 있음 — `validate/v11_web.py`
- `V11-156` 필터 조건이 그대로 넘어감 — `validate/v11_web.py`
- `V11-157` 상단 메뉴가 다섯을 넘지 않음 — `validate/v11_web.py`
- `V11-158` 내린 화면이 열리고 ★ 들어가는 문이 있음 — `validate/v11_web.py`
- `V11-159` 상세 11개 절이 규격 순서로 있음 — `validate/v11_web.py`
- `V11-16` /why 가 전 Component 를 냄 — `validate/v11_web.py`
- `V11-160` 1 절에 「왜 그 등급인가」 문장이 있음 — `validate/v11_web.py`
- `V11-161` 3 절에 총 구매비용 표가 있음 — `validate/v11_web.py`
- `V11-162` 목록 한 행의 칸이 8을 넘지 않음 — `validate/v11_web.py`
- `V11-163` 네 묶음 막대가 목록에 있음 — `validate/v11_web.py`
- `V11-164` 점수 필터가 SQL 로 걸림 — `validate/v11_web.py`
- `V11-165` 고른 조건이 문장으로 나옴 — `validate/v11_web.py`
- `V11-166` 비교에 막대 넷·총 구매비용·결론이 있음 — `validate/v11_web.py`
- `V11-17` /why 가 조회 상태 절을 냄 — `validate/v11_web.py`
- `V11-18` 축 태그가 전건 필터 링크임 — `validate/v11_web.py`
- `V11-19` 폴링 실패 시 화면이 안 깨짐 — `validate/v11_web.py`
- `V11-20` 분모 표시가 있음 — `validate/v11_web.py`
- `V11-21` 행동 요청 파라미터가 현재 필터와 일치 — `validate/v11_web.py`
- `V11-22` excluded 축이 「—/N」 으로 표시됨 — `validate/v11_web.py`
- `V11-23` 비로그인 관심 POST 가 유도 화면을 냄 — `validate/v11_web.py`
- `V11-24` 메뉴 분류가 잠금 단위와 일치 — `validate/v11_web.py`
- `V11-25` 사유 없이 설정이 저장되지 않음 — `validate/v11_web.py`
- `V11-26` 되돌릴 수 없는 행동에 확인이 있음 — `validate/v11_web.py`
- `V11-27` 가입 정책에 따라 화면이 바뀜 — `validate/v11_web.py`
- `V11-28` 응답 헤더에 비 ASCII 없음 — `validate/v11_web.py`
- `V11-29` 렌더된 폼의 csrf_token 이 비어 있지 않음 — `validate/v11_web.py`
- `V11-30` 시안 ↔ 템플릿 대조 통과 — `validate/v11_web.py`
- `V11-31` must_change_secret=1 에서 /password 가 200 — `validate/v11_web.py`
- `V11-32` known_issues 의 키가 전부 targets 에 있음 — `validate/v11_web.py`
- `V11-33` POST 가 저장 없이 성공 메시지를 내지 않음 — `validate/v11_web.py`
- `V11-34` 화면이 요청당 쿼리 상한을 넘지 않음 — `validate/v11_web.py`
- `V11-35` 중첩 if 가 안쪽부터 닫힘 — `validate/v11_web.py`
- `V11-36` 잘못된 쿼리 파라미터가 500 을 내지 않음 — `validate/v11_web.py`
- `V11-37` POST 가 예상 밖 500 을 내지 않음 — `validate/v11_web.py`
- `V11-38` 템플릿이 쓰는 값을 뷰가 넘김 — `validate/v11_web.py`
- `V11-39` 저장 단추가 실제로 저장함 — `validate/v11_web.py`
- `V11-40` 반입분의 origin 이 'import' 임 — `validate/v11_web.py`
- `V11-41` 반입 뒤 S5~S10 이 이어서 돎 — `validate/v11_web.py`
- `V11-42` S4 완료 행의 actual 이 'import' 임 — `validate/v11_web.py`
- `V11-43` 브라우저 수집분의 origin 이 'browser' 임 — `validate/v11_web.py`
- `V11-44` 사람 확인 없이 저장되지 않음 — `validate/v11_web.py`
- `V11-45` CLI 로만 되는 기능이 없음 — `validate/v11_web.py`
- `V11-46` 반입으로 연 단계의 actual 이 'import' 임 — `validate/v11_web.py`
- `V11-47` 브라우저 수집이 한 번에 max_form_bytes 를 넘기지 않음 — `validate/v11_web.py`
- `V11-48` 전 차종 수집에 확인 절차가 있음 — `validate/v11_web.py`
- `V11-49` 한 차종 실패가 나머지를 멈추지 않음 — `validate/v11_web.py`
- `V11-51` 진행 화면이 스스로 갱신됨 — `validate/v11_web.py`
- `V11-52` 진행 화면에 실행 단추가 없음 — `validate/v11_web.py`
- `V11-53` 진행 판정이 큐만 보지 않음 — `validate/v11_web.py`
- `V11-54` 메뉴에 경로가 그대로 나오지 않음 — `validate/v11_web.py`
- `V11-55` 목록에 전체 건수와 쪽이 표시됨 — `validate/v11_web.py`
- `V11-56` 대표 사진 경로가 저장됨 — `validate/v11_web.py`
- `V11-57` 사진 없는 매물이 화면을 무너뜨리지 않음 — `validate/v11_web.py`
- `V11-58` 쪽을 넘겨도 조건이 남음 — `validate/v11_web.py`
- `V11-59` 시안의 클래스가 CSS 에 있음 — `validate/v11_web.py`
- `V11-60` 시안 CSS 를 다시 만들지 않음 — `validate/v11_web.py`
- `V11-61` 이어질 수 있는 값이 링크임 — `validate/v11_web.py`
- `V11-62` 코드·줄임말에 title 이 있음 — `validate/v11_web.py`
- `V11-63` 매물 화면에 원문 링크가 있음 — `validate/v11_web.py`
- `V11-64` 고를 수 있는 값이 목록으로 제공됨 — `validate/v11_web.py`
- `V11-65` 기본 정렬이 규격대로임 — `validate/v11_web.py`
- `V11-66` 필터가 목록 위에 있음 — `validate/v11_web.py`
- `V11-67` 단추가 켜짐·꺼짐을 오감 — `validate/v11_web.py`
- `V11-68` v1 이 낸 열이 v2 에도 있음 — `validate/v11_web.py`
- `V11-69` v1 이 가진 조작이 v2 에도 있음 — `validate/v11_web.py`
- `V11-70` 좁은 폭에서 값이 사라지지 않음 — `validate/v11_web.py`
- `V11-71` 가로 스크롤로 떠넘기지 않음 — `validate/v11_web.py`
- `V11-72` 빈 주소로 가는 링크가 없음 — `validate/v11_web.py`
- `V11-73` 화면마다 값이 나옴 — `validate/v11_web.py`
- `V11-74` 숫자가 단위와 함께 나옴 — `validate/v11_web.py`
- `V11-75` 링크가 유효함 — `validate/v11_web.py`
- `V11-76` 화면 크기·시간이 상한 안 — `validate/v11_web.py`
- `V11-77` 시안의 시각 요소가 렌더 결과에 나옴 — `validate/v11_web.py`
- `V11-78` 좁은 폭에서 글자가 세로로 안 떨어짐 — `validate/v11_web.py`
- `V11-79` 축 칸에 맨 숫자가 나오지 않음 — `validate/v11_web.py`
- `V11-80` 사진이 최소 크기 이상 — `validate/v11_web.py`
- `V11-81` 신차가 · 시세 · 가격 셋이 함께 나옴 — `validate/v11_web.py`
- `V11-82` 정적 파일에 버전이 붙음 — `validate/v11_web.py`
- `V11-85` 트림에 세부등급이 포함됨 — `validate/v11_web.py`
- `V11-92` 신차가가 등급기준 + 옵션 합 — `validate/v11_web.py`
- `V11-94` 추천 조건이 화면에 적혀 있음 — `validate/v11_web.py`
- `V11-96` ♡ 가 제목 줄에 있음 — `validate/v11_web.py`
- `V11-98` 큰 원문을 조각으로 보내고 이어붙이는가 — `validate/v11_web.py`
- `V11-99` 같은 화면에서 여러 번 POST 가 되는가 — `validate/v11_web.py`
- `V2-01` ok 원문 수 == CORE 행 수 — `validate/v2_load.py`
- `V2-02` 필수 컬럼 NOT NULL 위반 없음 — `validate/v2_load.py`
- `V2-04` status 열거값 위반 없음 — `validate/v2_load.py`
- `V2-05` 단위 — 가격이 만원 단위로 남아 있지 않은가 — `validate/v2_load.py`
- `V2-06` 빈 컨테이너가 NULL 로 저장되지 않았는가 — `validate/v2_load.py`
- `V2-07` 전건 NULL 컬럼 — `validate/v2_load.py`
- `V2-08` 값 종류 1인 컬럼 — `validate/v2_load.py`
- `V2-09` core_pii 를 직접 조회하는 코드 없음 — `validate/v2_load.py`
- `V2-10` core_listing 에 plate_no · dealer_name · phone · address 없음 — `validate/v2_load.py`
- `V2-10b` core_* 에 마스킹 컬럼 없음 — `validate/v2_load.py`
- `V2-11` plate_hash 가 전건 16자 hex — `validate/v2_load.py`
- `V2-12` secrets/plate_hmac.key 가 버전 관리 밖 — `validate/v2_load.py`
- `V2-13` core_record 에 record_plate_no 원본 없음 — `validate/v2_load.py`
- `V2-14` 참조되는 5종 PK 가 단일 INTEGER — `validate/v2_load.py`
- `V2-15` 자연키가 UNIQUE 로 걸려 있음 — `validate/v2_load.py`
- `V2-16` PK·FK 컬럼에 개인정보 없음 — `validate/v2_load.py`
- `V2-17` PII 고아 행 없음 — `validate/v2_load.py`
- `V2-18` parse_rule 재처리 후 전 봉투가 현재 parse_version — `validate/v2_load.py`
- `V2-19` 원문 유래 컬럼에 NOT NULL 없음 — `validate/v2_load.py`
- `V2-20` 파싱 실패 필드가 있는 행도 CORE 에 있음 — `validate/v2_load.py`
- `V2-21` parse_error · type_mismatch 건수 — `validate/v2_load.py`
- `V2-22` 현재 DB 스키마가 sql/ddl 과 일치 — `validate/v2_load.py`
- `V2-23` 중간 노드 None 인 매물도 CORE 에 있음 — `validate/v2_load.py`
- `V2-24` 배열 기대 필드가 전건 list 로 정규화됨 — `validate/v2_load.py`
- `V2-25` 스칼라 null 이 0 으로 저장된 컬럼 없음 — `validate/v2_load.py`
- `V2-27` parse/ 에 원문 연쇄 첨자가 없음 — `validate/v2_load.py`
- `V2-28` 파싱 실패해도 남은 필드가 저장됨 — `validate/v2_load.py`
- `V2-29` upsert 가 버린 키를 기록함 — `validate/v2_load.py`
- `V2-30` 전 파서가 row_status 를 냄 — `validate/v2_load.py`
- `V2-31` target_key NULL 이 판정에 들어가지 않음 — `validate/v2_load.py`
- `V2-32` NULL 매물의 모델명이 화면에서 보임 — `validate/v2_load.py`
- `V3-01` result_axis.source 전건 NOT NULL — `validate/v3_logic.py`
- `V3-02` result_axis.prio 전건 NOT NULL — `validate/v3_logic.py`
- `V3-03` 축별 source 값 종류 >= 2 — `validate/v3_logic.py`
- `V3-04` 축별 값 종류 >= 2 — `validate/v3_logic.py`
- `V3-05` 금지 근거가 source 에 없음 — `validate/v3_logic.py`
- `V3-06` put() 충돌 기록 검토 — `validate/v3_logic.py`
- `V3-07` 축별 -1 비율 — `validate/v3_logic.py`
- `V3-08` 사전 pending 이 판정에 쓰이지 않음 — `validate/v3_logic.py`
- `V3-09` 축별 excluded 비율 — `validate/v3_logic.py`
- `V3-10` 재판정 결과가 이전과 동일 — `validate/v3_logic.py`
- `V3-11` put() 순서 셔플 후에도 동일 — `validate/v3_logic.py`
- `V3-20` trust_score 가 555 에 합산되지 않음 — `validate/v3_logic.py`
- `V3-21` 경고가 555 에 합산되지 않음 — `validate/v3_logic.py`
- `V3-22` 경고로 매물이 목록에서 제외되지 않음 — `validate/v3_logic.py`
- `V3-23` 경고로 등급·추천 순위가 바뀌지 않음 — `validate/v3_logic.py`
- `V3-24` acknowledged 가 신호 감지를 멈추지 않음 — `validate/v3_logic.py`
- `V3-25` 소멸한 경고가 삭제되지 않고 남음 — `validate/v3_logic.py`
- `V3-27` 모든 경고에 evidence 존재 — `validate/v3_logic.py`
- `V3-28` PeerGroup 이 확장 단계를 표시 — `validate/v3_logic.py`
- `V3-29` 배점 변경 시 calc_version 이 증가 — `validate/v3_logic.py`
- `V3-30` halt 축의 사전이 비어 있지 않음 — `validate/v3_logic.py`
- `V3-31` 딜러 NULL 매물에 dealer_untrusted 없음 — `validate/v3_logic.py`
- `V3-32` seizing null 매물이 「저당 없음」으로 판정되지 않음 — `validate/v3_logic.py`
- `V3-34` 판정 항목 수 == resultCode IS NOT NULL 인 items 수 — `validate/v3_logic.py`
- `V3-35` conflicts 가 있는 매물이 기록됨 — `validate/v3_logic.py`
- `V3-36` conflicts 건수가 임계 미만 — `validate/v3_logic.py`
- `V3-37` 목록 관측분의 source 가 'list' 임 — `validate/v3_logic.py`
- `V3-38` facet 수신 후 목록 관측분과 대조함 — `validate/v3_logic.py`
- `V3-39` 이론가와 실제 중앙값의 차가 상한 안 — `validate/v3_logic.py`
- `V3-40` 핵심 축이 excluded 인데 등급을 매기지 않음 — `validate/v3_logic.py`
- `V3-41` 전 매물의 분모가 만점과 같음 — `validate/v3_logic.py`
- `V3-45` 배점 합이 만점과 같음 — `validate/v3_logic.py`
- `V3-47` 축별 차종 간 결측률 편차가 상한 안 — `validate/v3_logic.py`
- `V3-50` 성능부와 보험이력이 어긋난 건을 셈 — `validate/v3_logic.py`
- `V3-52` 「싸다」에 이유가 붙어 있음 — `validate/v3_logic.py`
- `V3-53` 점검 출처가 판정에 반영됨 — `validate/v3_logic.py`
- `V3-54` 렌트 이력을 세 곳에서 대조 — `validate/v3_logic.py`
- `V3-55` 사이트 보증 축이 config 규칙을 읽는가 — `validate/v3_logic.py`
- `V3-56` 배점 합이 605 — `validate/v3_logic.py`
- `V3-57` 등급 기준이 grade_base_points 와 같음 — `validate/v3_logic.py`
- `V3-58` 배터리 SOH 가 축이 아니라 가점임 — `validate/v3_logic.py`
- `V3-59` 가점이 분모를 늘리지 않음 — `validate/v3_logic.py`
- `V3-62` 원문이 없는데 값을 만든 축이 없음 — `validate/v3_logic.py`
- `V3-64` 등급 경계가 절대 기준 — `validate/v3_logic.py`
- `V3-65` 확인율이 근거 있는 축만 셈 — `validate/v3_logic.py`
- `V3-66` 각 축의 계산이 f-table 과 같음 — `validate/v3_logic.py`
- `V3-68` 부록 F 전 24축이 구현돼 있음 — `validate/v3_logic.py`
- `V3-70` 일반·동력계 보증을 따로 냄 — `validate/v3_logic.py`
- `V3-71` 보증 잔여가 기간·거리 중 낮은 쪽임 — `validate/v3_logic.py`
- `V3-72` SOH 가점이 곡선대로 붙음 — `validate/v3_logic.py`
- `V3-75` 트림 점수를 신차가로 잼 — `validate/v3_logic.py`
- `V3-76` ⑤ 의 하위 축 합이 갈래 표기와 같음 — `validate/v3_logic.py`
- `V3-77` 갈래마다 하위 축 합 = 갈래 표기 (전 갈래) — `validate/v3_logic.py`
- `V3-78` 「그 밖」으로 옮긴 값이 축을 덮지 않음 — `validate/v3_logic.py`
- `V3-79` 어긋난 매물에 ②-2·②-3 만점이 없음 — `validate/v3_logic.py`
- `V3-80` ②-1 회수가 max(보험, 성능부) 임 — `validate/v3_logic.py`
- `V3-81` 셋 중 하나만 null 인데 확인 안 됨이 아님 — `validate/v3_logic.py`
- `V3-82` 시세 점수가 계단값만 나오지 않음 — `validate/v3_logic.py`
- `V3-83` 시세보다 비싼 매물에 음수 점수가 붙음 — `validate/v3_logic.py`
- `V3-84` 신차가 곡선이 규격의 앵커와 같음 — `validate/v3_logic.py`
- `V3-85` 옵션 보정 없이 원 중앙값으로 견준 매물 — `validate/v3_logic.py`
- `V3-86` 축 점수가 배점을 넘지 않음 — `validate/v3_logic.py`
- `V3-87` 사이트 검증이 단계임 (더하지 않음) — `validate/v3_logic.py`
- `V3-90` 등급 분모가 총점으로 고정 — `validate/v3_logic.py`
- `V3-91` 가이드 검산 일곱 줄이 표대로 나옴 — `validate/v3_logic.py`
- `V3-92` 트림 만점이 개별 취향 축보다 큼 — `validate/v3_logic.py`
- `V3-93` 제외 매물에 등급 문자가 안 붙음 — `validate/v3_logic.py`
- `V3-94` 등급 컷이 규격의 8단계임 — `validate/v3_logic.py`
- `V3-95` 화면이 source='missing' 을 「없음」으로 안 냄 — `validate/v3_logic.py`
- `V3-96` value IS NULL 과 source 모름 건수 차 — `validate/v3_logic.py`
- `V4-01` 매핑 일치율 (A 100% · B 99% · C 80%) — `validate/v4_mapping.py`
- `V4-02` 미매핑 경로 목록 — `validate/v4_mapping.py`
- `V4-03` 오매핑 탐지 — 다른 경로와 더 높은 일치율 — `validate/v4_mapping.py`
- `V4-04` 매핑표에 없는 CORE 컬럼 — `validate/v4_mapping.py`
- `V4-05` 원문 경로 수 변동 — `validate/v4_mapping.py`
- `V4-06` RAW 경로가 등록부에 있는가 — `validate/v4_mapping.py`
- `V4-06b` 등록부에 있는데 RAW 에 없는 유령 경로 — `validate/v4_mapping.py`
- `V4-07` in_use 인데 core_column NULL — `validate/v4_mapping.py`
- `V4-08` blocked 인데 unblock_condition NULL — `validate/v4_mapping.py`
- `V4-09` deferred 인데 use_when NULL — `validate/v4_mapping.py`
- `V4-10` display_only 인데 core_column NULL — `validate/v4_mapping.py`
- `V4-11` unclassified 존재 — `validate/v4_mapping.py`
- `V4-11b` 판정에 안 쓰는 미분류 경로 — `validate/v4_mapping.py`
- `V4-12` facet 필수 축 집합 존재 — `validate/v4_mapping.py`
- `V4-13` 매직 넘버 없음 (tools/check_src.py S7) — `validate/v4_mapping.py`
- `V4-19` 성격(kind)이 없는 Check 가 없음 — `validate/v4_mapping.py`
- `V4-20` dict_option_code 에 문장(공백·한글)이 없음 — `validate/v4_mapping.py`
- `V4-21` 같은 이름의 공개 함수가 두 모듈에 없음 — `validate/v4_mapping.py`
- `V4-22` 역방향 · 순환 import 없음 — `validate/v4_mapping.py`
- `V4-23` 모듈 최상위에 I/O · 부작용 없음 — `validate/v4_mapping.py`
- `V4-24` 축 함수가 target_config 에서 매물 값을 읽지 않음 — `validate/v4_mapping.py`
- `V4-25` 판정에 쓰는 축의 사전이 비어 있지 않음 — `validate/v4_mapping.py`
- `V4-26` 미분류가 원인별로 갈려 있음 — `validate/v4_mapping.py`
- `V4-27` 판정을 막는 것만 막음 — `validate/v4_mapping.py`
- `V4-28` 미분류 항목에 값 분포와 선택지가 있음 — `validate/v4_mapping.py`
- `V4-29` 기본 화면이 판정 막는 것만 냄 — `validate/v4_mapping.py`
- `V4-30` 판정을 막는 것의 목록 파일이 있음 — `validate/v4_mapping.py`
- `V5-01` 배점 합계 == config 총점 — `validate/v5_value.py`
- `V5-02` 표시용 등급 점수가 비율과 일치 — `validate/v5_value.py`
- `V5-03` 분모 시험 A·D·E·G·H·I 통과 — `validate/v5_value.py`
- `V5-04` 점수 범위 위반 없음 — `validate/v5_value.py`
- `V5-05` 등급 분포가 극단적이지 않음 — `validate/v5_value.py`
- `V5-06` 기준값 대비 실측 이탈 — `validate/v5_value.py`
- `V5-07` 계수 보정 타당성 — `validate/v5_value.py`
- `V5-08` 계수 산출 입력에 result_* 없음 — `validate/v5_value.py`
- `V5-09` 등급이 earned / denominator 로 산출됨 — `validate/v5_value.py`
- `V5-10` 같은 비율 · 다른 분모가 같은 등급 — `validate/v5_value.py`
- `V5-11` 분모 최대값으로도 S 가 불가능한 매물 없음 — `validate/v5_value.py`
- `V5-12` NOT_RATED 인데 not_rated_reason 이 NULL 인 행 없음 — `validate/v5_value.py`
- `V6-07` ORDER BY 에 4단이 전부 있음 — `validate/v3_logic.py`
- `V7-01` watch_track 에 버전 4종 전건 있음 — `validate/v7_watch.py`
- `V7-02` cause != 'listing' 인 이벤트가 알림되지 않음 — `validate/v7_watch.py`
- `V7-04` 같은 이벤트 중복 발송 0건 — `validate/v7_watch.py`
- `V7-05` gone 매물이 목록에서 삭제되지 않음 — `validate/v7_watch.py`
- `V7-06` 검증 실패 실행에서 알림이 나가지 않음 — `validate/v7_watch.py`
- `V7-07` relist 결합에 identity_kind 기록 — `validate/v7_watch.py`
- `V7-08` 구매 체크리스트가 점수·등급에 반영되지 않음 — `validate/v7_watch.py`
- `V7-09` 실구매가·총소유비용이 점수에 반영되지 않음 — `validate/v7_watch.py`
- `V7-10` 발송 시도 대비 성공률 — `validate/v7_watch.py`
- `V7-11` closed_reason 이 CHECK 안의 값 — `validate/v7_watch.py`
- `V7-12` 남의 관심 항목을 고치지 못함 — `validate/v7_watch.py`
- `V7-14` 재등록 횟수가 화면에 나옴 — `validate/v7_watch.py`
- `V7-15` 진행 메모를 자유롭게 적을 수 있음 — `validate/v7_watch.py`
- `V8-01` 같은 파일명이 두 번 생성되지 않음 — `validate/v3_logic.py`
- `V8-02` 출력 파일에 BOM · CRLF 가 없음 — `validate/v3_logic.py`
- `V9-01` 축 × 사이트 표가 있음 — `validate/v9_multisite.py`
- `V9-02` site_unavailable 이 화면에 나옴 — `validate/v9_multisite.py`
- `V9-06` 매물마다 사이트 배지가 있음 — `validate/v9_multisite.py`
- `V9-07` 합친 값에 출처가 붙어 있음 — `validate/v9_multisite.py`
- `V9-09` 같은 점수에서 사이트 보증이 높은 쪽이 앞 — `validate/v9_multisite.py`
- `V9-10` 사이트 보증 항목의 합이 만점과 같음 — `validate/v9_multisite.py`

## ⑤ ★ 규격이 요구했는데 코드에 없는 검사

- `V0-01` — guide/00_버전.md:26 · guide/03_이력.md:349 · guide/03_이력.md:413
- `V0-02` — guide/00_버전.md:56 · guide/03_이력.md:666
- `V0-03` — guide/00_버전.md:78 · guide/03_이력.md:349 · guide/03_이력.md:413
- `V1-22` — trace/05-score.md:47 · guide/01_요구사항.md:159 · guide/01_요구사항.md:275
- `V11-111` — chapters/61-web/e-compare.md:38
- `V11-118` — guide/03_이력.md:357 · chapters/61-web/d-detail.md:120 · chapters/61-web/f-width.md:78
- `V11-123` — guide/03_이력.md:388 · chapters/61-web/h-admin.md:29 · chapters/61-web/h-admin.md:272
- `V11-124` — chapters/61-web/h-admin.md:85 · chapters/61-web/h-admin.md:273
- `V11-128` — guide/03_이력.md:390 · chapters/00-standard.md:2136 · chapters/61-web/i-admin-mock.md:389
- `V11-129` — chapters/00-standard.md:2037 · chapters/61-web/i-admin-mock.md:390 · chapters/61-web/j-admin-mock2.md:491
- `V11-131` — guide/03_이력.md:392 · chapters/00-standard.md:2213
- `V11-133` — guide/03_이력.md:396 · chapters/61-web/d-detail.md:159
- `V11-137` — guide/03_이력.md:402 · chapters/61-web/d-detail.md:258
- `V11-138` — chapters/61-web/d-detail.md:259 · chapters/61-web/d-detail.md:270
- `V11-141` — guide/03_이력.md:404 · chapters/61-web/j-admin-mock2.md:215
- `V11-143` — guide/03_이력.md:405 · chapters/61-web/i-admin-mock.md:209
- `V11-144` — guide/03_이력.md:405 · chapters/61-web/i-admin-mock.md:248
- `V11-87` — guide/01_요구사항.md:156 · guide/01_요구사항.md:219 · guide/01_요구사항.md:229
- `V11-88` — guide/01_요구사항.md:161 · guide/01_요구사항.md:567 · guide/01_요구사항.md:577
- `V11-93` — trace/14-web.md:47 · guide/01_요구사항.md:162 · guide/01_요구사항.md:581
- `V13-08` — guide/03_이력.md:446 · chapters/13-pipeline.md:346
- `V2-03` — trace/RULES.md:186 · chapters/11-store/a-key.md:377 · chapters/20-verify/b-v1v2.md:107
- `V3-42` — trace/14-web.md:55 · guide/01_요구사항.md:157 · guide/01_요구사항.md:233
- `V3-44` — guide/02_결함대장.md:85 · guide/02_결함대장.md:95 · guide/03_이력.md:310
- `V3-49` — ENCAR_API.md:184 · trace/05-score.md:57 · guide/01_요구사항.md:158
- `V3-67` — guide/01_요구사항.md:160 · guide/01_요구사항.md:369 · guide/01_요구사항.md:379
- `V3-69` — guide/03_이력.md:350 · chapters/30-score/a-frame.md:764
- `V3-73` — guide/03_이력.md:400 · chapters/30-score/f-table.md:1607
- `V3-88` — guide/03_이력.md:450 · chapters/30-score/f-table.md:702
- `V6-01` — chapters/41-view.md:877 · chapters/61-web.md:370
- `V9-03` — trace/50-multisite.md:42 · trace/50-multisite.md:43 · trace/50-multisite.md:44
- `V9-04` — trace/31-registry.md:53 · trace/50-multisite.md:51 · trace/50-multisite.md:52
- `V9-05` — trace/02-collect.md:73 · trace/50-multisite.md:52 · trace/50-multisite.md:53
- `V9-08` — trace/02-collect.md:77 · trace/05-score.md:101 · trace/50-multisite.md:70

## ④ 코드에 있는데 규격에 안 적힌 검사

- `S14-1` 화면에 배점을 박지 않음 (V4-17) — `tools/check_src.py`
- `S46-77` KB 는 우리 20종만 받는가 — `validate/v0_guide.py`
- `V1-19` 이번 실행이 저장한 원문에 run_id 가 있음 — `validate/v1_collect.py`
- `V1-20` 카탈로그를 모델당 1회만 받음 — `validate/v1_collect.py`
- `V1-25` ok 로 저장된 원문이 온전한가 — `validate/v1_collect.py`
- `V10-34` 거부 응답에 고칠 재료가 있음 — `validate/v10_admin.py`
- `V10-35` query_log 가 compile · policy 로 갈림 — `validate/v10_admin.py`
- `V10-38` 끊긴 실행이 큐를 막고 있지 않음 — `validate/v10_admin.py`
- `V11-154` 뺀 건수가 화면에 있음 — `validate/v11_web.py`
- `V11-155` 차종·가격대 필터가 있음 — `validate/v11_web.py`
- `V11-37` POST 가 예상 밖 500 을 내지 않음 — `validate/v11_web.py`
- `V11-38` 템플릿이 쓰는 값을 뷰가 넘김 — `validate/v11_web.py`
- `V11-39` 저장 단추가 실제로 저장함 — `validate/v11_web.py`
- `V11-58` 쪽을 넘겨도 조건이 남음 — `validate/v11_web.py`
- `V11-72` 빈 주소로 가는 링크가 없음 — `validate/v11_web.py`
- `V11-73` 화면마다 값이 나옴 — `validate/v11_web.py`
- `V11-74` 숫자가 단위와 함께 나옴 — `validate/v11_web.py`
- `V11-75` 링크가 유효함 — `validate/v11_web.py`
