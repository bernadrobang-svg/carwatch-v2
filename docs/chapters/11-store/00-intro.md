# 3장. 테이블 설계 (STEP 28–39)

```
version  SPEC-2026.08.29-r989
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


## 3장 정의서

**본 장에서 확정하는 테이블군 · 공통 규칙 · DTO. DDL 은 `sql/ddl/` 에 둔다.**

### 테이블군

```
admin_*    관리자 · 계정 · 변경 이력 (13장)
raw_*      원문.  무손실.  삭제 금지
core_*     정규.  사이트 무관 공통 스키마
dict_*     사전.  RAW 에서 생성
meta_*     메타.  필드 사용 구분 등록부 (8장 STEP 87)
result_*   판정·점수.  재계산으로 언제든 다시 만들 수 있다
audit_*    수집·검증 로그
```

**`result_*` 는 버려도 된다. `raw_*` 는 절대 버리지 않는다.**
이 구분이 재처리 구조의 전제다 (1장 STEP 10).

### DTO

```python
@dataclass(frozen=True)
class ListingSnapshot:
    """Analyzer 입력. core_* 조인 결과. Row 를 직접 넘기지 않는다."""
    listing_id: str
    site: str
    target_key: str
    price_current_won: int | None
    price_origin_won: int | None
    year_month: str | None
    mileage_km: int | None
    displacement_cc: int | None
    warranty_body_month: int | None
    warranty_body_km: int | None
    warranty_power_month: int | None
    warranty_power_km: int | None
    first_registration_date: date | None
    options_standard: list[str] | None
    options_choice: list[str] | None
    inspection_panels: list[dict] | None      # outers 원문 배열
    # ── E등급 절대조건 필드는 dict 에 숨기지 않고 명시한다 (STEP 82) ──
    flood_total_cnt: int | None
    flood_part_cnt: int | None
    total_loss_cnt: int | None
    airbag_deployed: int | None
    seizing_cnt: int | None
    pledge_cnt: int | None
    accident_my_cost: int | None
    accident_my_cnt: int | None
    accident_other_cnt: int | None
    inspection_waterlog: int | None
    sales_status: str | None
    lease_present: bool | None
    lease_type: str | None
    not_join_json: str | None
    owner_change_cnt: int | None
    record_plate_no: str | None
    plate_history_json: str | None
    color_ext_raw: str | None
    color_ext_hex: str | None
    sell_type: str | None
    plate_no: str | None
    ad_body_text: str | None
    site_flags: dict          # 사이트 고유값. Analyzer 는 어댑터 사전을 통해서만 읽는다

# ★ 판정에 쓰는 필드는 전부 명시한다.  dict 안에 숨기지 않는다
#   record_summary: dict 같은 통짜 필드는 352컬럼 Row 를 dict 하나로 바꾼 것에 불과하다
#   site_flags 는 사이트 고유 표시값 전용이며, 판정에 쓰려면 명시 필드로 승격한다

@dataclass(frozen=True)
class AxisResult:
    axis: str
    value: int | None
    source: str
    prio: int
    denominator_excluded: bool
```

**`ListingSnapshot` 에 없는 필드는 판정에 쓸 수 없다.** 축을 추가하려면 DTO 를 먼저 고친다.

### 함수

| 이름 | 입력 | 출력 | 목적 |
|---|---|---|---|
| `load_snapshot` | `listing_id` | `ListingSnapshot` | core → DTO |
| `upsert_core` | `parsed: dict` | `int` | 파싱 결과 적재 |
| `record_change` | `listing_id, field, old, new` | `None` | 변경 이력 적재 |
| `build_dict` | `endpoint, axis` | `int` | RAW → 사전 생성 |

---

