## STEP 20 — `detail` 응답 → 필드

```
version  SPEC-2026.08.29-r952
follows  `docs/chapters/30-score/f-table.md`
sources  실측 08-22
checks   S46-38 · S46-39
```


**원문 123~144경로. 아래는 판정에 쓰는 것만. 나머지는 8장에서 다룬다.**

| 원문 | 변환 | CORE 필드 |
|---|---|---|
| `category.originPrice` | `×10000` | `price_origin_won` |
| `category.warranty.bodyMonth` / `bodyMileage` | — | `warranty_body_month` / `_km` |
| `category.warranty.transmissionMonth` / `Mileage` | — | `warranty_power_month` / `_km` |
| `category.jatoVehicleId` | str | `model_catalog_key` |
| `category.gradeName` | — | `trim_grade_name` | 트림 2순위 |
| `spec.displacement` | — | `displacement_cc` | **분류 2단 확정용** |
| `spec.mileage` | — | `mileage_detail_km` | 목록값과 교차검증 |
| `spec.colorName` | — | `color_ext_detail` | **상세가 원천 (P2)** |
| `spec.fuelName` | — | `fuel_detail` | |
| `spec.tradeType` | — | `trade_type` |
| `options.standard` | json | `options_standard_json` | 3자리 |
| `options.choice` | json | `options_choice_json` | 4자리. **`[]` 와 NULL 구분** |
| `options.etc` · `options.tuning` | json | `options_etc_json` · `options_tuning_json` |
| `condition.seizing.seizingCount` / `pledgeCount` | — | `seizing_cnt` / `pledge_cnt` |
| `condition.accident.recordView` / `resumeView` | — | `has_record` / `has_resume` | **요청 조건 아님** |
| `condition.inspection.formats` | json | `inspection_formats_json` | 동일 |
| `advertisement.price` | `×10000` | `price_detail_won` |
| `advertisement.advertisementType` | — | `advertisement_type` | **E등급 근거** (STEP 82) |
| `advertisement.leaseRentInfo` | json | `lease_rent_info_json` | **E등급 근거** (STEP 82) |
| `advertisement.diagnosisCar` | bool | `diagnosis_car` |
| `advertisement.encarPassType` / `encarPassCategoryType` | — | `site_pass_type` / `site_pass_grade` |
| `advertisement.extendWarranty` / `deemedExtendWarranty` | — | `warranty_extend` / `warranty_deemed` | **표시 전용** |
| `advertisement.underBodyPhotos[]` | json | `photo_underbody_json` | 표시 전용 |
| `view.encarDiagnosis` | — | `site_diagnosis_grade` | ★ v1 전건 NULL |
| `manage.registDateTime` · `firstAdvertisedDateTime` · `modifyDateTime` | date | `reg_at` · `first_ad_at` · `modify_at` |
| `manage.dummy` · `dummyVehicleId` | — | `is_dummy` · `paired_source_id` | 중복 매물 |
| `manage.viewCount` · `subscribeCount` | — | `view_cnt` · `subscribe_cnt` |
| `partnership.dealer.name` / `.firm.name` / `.firm.code` | — | `dealer_name` / **`dealer_shop`** / `dealer_shop_code` |
| `contact.no` · `address` | — | `dealer_phone` · `dealer_address` |
| `contents.text` | — | `ad_body_text` | **틴팅 판정 근거** |
| `vin` · `vehicleNo` | — | `vin` · `plate_no` |

```
단위     originPrice · price 는 만원 단위다.  ×10,000 후 저장
금지     값 크기로 단위를 추정해 되돌리는 보정
        (100만 미만이면 ×10,000 같은 규칙 — v1 임시방편)
필수     price_unit 컬럼에 'manwon' 을 명시.  원값도 함께 보존
```

---

