# -*- coding: utf-8 -*-
"""내보내기.

지시서   9장 STEP 92
근거     파일명은 ReportMeta 에서 나온다.  규격과 구조체가 어긋나지 않는다
필수     전 형식에 VersionStamp 포함.  csv 헤더에 배점을 표기한다
금지     화면 전용 문구를 csv·json 에 넣는 것.  값과 코드로 낸다
"""
from __future__ import annotations

import csv
import dataclasses
import io
import json
import os

from report.views import (
    ExportResult, HaltReport, RunReport, ScoreView, TargetReport,
)
from report.views import display_points, display_value

MD, CSV, JSON = "md", "csv", "json"
CONTENT_TYPE = {MD: "text/markdown", CSV: "text/csv", JSON: "application/json"}


def filename(meta, ext: str) -> str:
    """{run_id}_{layer}_{target_key|ALL}_{calc_version}.{ext}"""
    tk = meta.target_key or "ALL"
    return f"{meta.run_id}_{meta.layer}_{tk}_{meta.calc_version}.{ext}"


def _stamp_lines(v) -> list[str]:
    return [f"버전  parse={v.parse_version} dict={v.dict_version} "
            f"calc={v.calc_version} coefficient={v.coefficient}"
            f"(id={v.coefficient_id})"]


def listing_md(view: ScoreView, labels: dict) -> str:
    vl = labels.get("VALUE_LABELS", {})
    gl = labels.get("GRADE_LABELS", {})
    out = [f"# {view.listing_id}  [{view.target_key}]", ""]
    out.append(f"등급  {gl.get(view.grade, view.grade)}"
               f"  {view.score_total:g} / {view.denominator:g}")
    if view.absolute_fail:
        out.append(f"E등급 사유  {view.absolute_fail}")
    out += ["", "| 축 | 획득 | 값 | 근거 | prio |", "|---|---|---|---|---|"]
    for a in view.axes:
        out.append(f"| {a.label} | {display_points(a.points, a.excluded, a.max_points)}"
                   f" | {display_value(a.value, a.excluded, vl)}"
                   f" | {a.source} | {a.prio} |")
    if view.finance:
        f = view.finance
        out += ["", "## 비용 — 점수가 아니다", ""]
        # ★ 「실구매가」를 앞에 내지 않는다.  현금은 항상 선납금 고정이다.
        #   매물마다 다른 것은 월 납입이다
        if f.cash_only:
            out.append(f"{f.price_listed_won:,} (전액 현금 — 할부 없음)")
        else:
            out.append(f"{f.price_listed_won:,} "
                       f"(현금 {f.down_payment_won:,} · 월 {f.monthly_payment_won:,})")
        out.append(f"부대비용 {f.acquisition_cost_won:,} · "
                   f"차값 선납 {f.vehicle_down_won:,} · "
                   f"할부 원금 {f.loan_principal_won:,} · "
                   f"총이자 {f.total_interest_won:,}")
        if f.shortfall_won:
            out.append(f"★ 선납 부족 {f.shortfall_won:,} — 부대비용이 선납금을 넘는다")
        if f.estimated_items:
            out.append(f"추정 항목  {', '.join(f.estimated_items)}")
    if view.pending_items:
        # ★ 「무엇이 · 몇 점 · 왜」를 함께 낸다 (STEP 149h)
        out += ["", "미확정  " + " · ".join(
            f"{p['label']} {p['points']}점 ({p['reason']})"
            for p in view.pending_items)]
    out += [""] + _stamp_lines(view.versions)
    return "\n".join(out)


def listing_csv(views: list[ScoreView]) -> str:
    """헤더에 배점을 표기한다 — price(200) · spec.hud(20)."""
    axes = [a.axis for a in views[0].axes] if views else []
    mx = {a.axis: a.max_points for a in views[0].axes} if views else {}
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["listing_id", "target_key", "grade", "score_total",
                "denominator", "calc_version", "dict_version"]
               + [f"{a}({mx[a]})" for a in axes])
    for v in views:
        w.writerow([v.listing_id, v.target_key, v.grade, v.score_total,
                    v.denominator, v.versions.calc_version,
                    v.versions.dict_version]
                   + [("" if a.excluded else a.points) for a in v.axes])
    return buf.getvalue()


def halt_md(rep: HaltReport) -> str:
    """L0 — 빈 화면으로 끝내지 않는다."""
    out = [f"# 중단 — {rep.meta.run_id}", "",
           f"중단 단계  {rep.halted_step}", "", "## 사유", ""]
    for r in rep.failures:
        out.append(f"- **{r.check.code}** {r.check.title}")
        out.append(f"  - 기대 {r.expected} / 실제 {r.actual}")
        if r.samples:
            out.append(f"  - 표본 {', '.join(map(str, r.samples[:5]))}")
    out += ["", "## 조치", ""]
    for code, action in rep.actions.items():
        out.append(f"- {code} → {action}")
    out += ["", "## 진행분 — 처음부터 다시 돌지 않는다", ""]
    for s in rep.completed_steps:
        out.append(f"- {s.step}  요청 {s.requested} · ok {s.ok}")
    if rep.artifacts:
        out += ["", "## 생성물", ""] + [f"- {a}" for a in rep.artifacts]
    out += [""] + _stamp_lines(rep.versions)
    return "\n".join(out)


def target_md(rep: TargetReport) -> str:
    out = [f"# {rep.meta.target_key}  ({rep.meta.run_id})", "",
           f"매물 {rep.collect.listing_count}건", "",
           "| 엔드포인트 | 확보율 | ok | empty | not_found | error | not_requested |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for ep, c in rep.collect.status_counts.items():
        out.append(f"| {ep} | {rep.collect.endpoint_rates[ep]:.0%} | "
                   + " | ".join(str(c[k]) for k in
                                ("ok", "empty", "not_found", "error",
                                 "not_requested")) + " |")
    out += ["", f"분류  잠정 {rep.classify.provisional} · "
            f"확정 {rep.classify.confirmed} · 충돌 {rep.classify.conflict}", "",
            "| 축 | 평균/배점 | 값 종류 | 제외 비율 |", "|---|---|---:|---:|"]
    for a in rep.axes:
        out.append(f"| {a.axis} | {a.avg_points:.1f}/{a.max_points} | "
                   f"{a.distinct_values} | {a.excluded_ratio:.0%} |")
    out += ["", f"등급  {rep.grades}"]
    if rep.warnings:
        out += ["", "## 경고", ""] + [f"- {w}" for w in rep.warnings]
    return "\n".join(out)


def run_md(rep: RunReport) -> str:
    """L3 — 수집·검증이 정상인가 (STEP 90).

    ★ 「통과 몇 건」이 아니라 「무엇이 실패했나」를 먼저 낸다.
      통과 수만 보면 새로 생긴 실패가 묻힌다
    """
    out = [f"# 실행 {rep.meta.run_id}", "",
           f"사이트 {rep.meta.site} · calc {rep.meta.calc_version}", ""]

    fails = [c for c in rep.checks if not c[4]]
    fatal = [c for c in fails if c[5] == "fatal"]
    warn = [c for c in fails if c[5] != "fatal"]
    out.append(f"검증 {len(rep.checks)}건 · 실패 {len(fails)} "
               f"(fatal {len(fatal)} · warn {len(warn)})")
    out.append("")
    for title, rows in (("## fatal", fatal), ("## warn", warn)):
        if not rows:
            continue
        out.append(title)
        out.append("")
        out.append("| 코드 | 기대 | 실제 | 표본 |")
        out.append("|---|---|---|---|")
        for phase, code, expected, actual, _p, _s, samples in rows:
            out.append(f"| {code} | {expected} | {actual} | "
                       f"{str(samples or '')[:60]} |")
            _ = phase
        out.append("")

    if rep.steps:
        out.append("## 단계")
        out.append("")
        out.append("| 단계 | 요청 | 성공 | 없음 | 실패 |")
        out.append("|---|---:|---:|---:|---:|")
        for s in rep.steps:
            out.append(f"| {getattr(s, 'step', '-')} "
                       f"| {getattr(s, 'requested', 0)} "
                       f"| {getattr(s, 'ok', 0)} "
                       f"| {getattr(s, 'skipped', 0)} "
                       f"| {getattr(s, 'failed', 0)} |")
        out.append("")

    out.append(f"등록부 미분류 {rep.unclassified_count}건")
    if rep.coefficient_changes:
        out.append("")
        out.append("## 계수 변경")
        for c in rep.coefficient_changes:
            out.append(f"- {c}")
    return "\n".join(out) + "\n"


def _asdict(obj):
    if dataclasses.is_dataclass(obj):
        return {k: _asdict(v) for k, v in dataclasses.asdict(obj).items()}
    if isinstance(obj, (list, tuple)):
        return [_asdict(v) for v in obj]
    return obj


def export(report, fmt: str, labels: dict | None = None,
           meta=None) -> ExportResult:
    """ScoreView 에는 ReportMeta 가 없다 (9장 정의서).

    파일명은 ReportMeta 에서 나오므로 L1 은 meta 를 함께 받는다.
    DTO 에 필드를 추가하지 않는다 — 정의서가 정본이다.
    """
    labels = labels or {}
    if fmt == JSON:
        body = json.dumps(_asdict(report), ensure_ascii=False, indent=2,
                          default=str)
    elif fmt == CSV:
        body = listing_csv(report if isinstance(report, list) else [report])
    elif isinstance(report, HaltReport):
        body = halt_md(report)
    elif isinstance(report, TargetReport):
        body = target_md(report)
    elif isinstance(report, RunReport):
        body = run_md(report)
    else:
        body = listing_md(report, labels)
    if meta is None:
        first = report[0] if isinstance(report, list) and report else report
        meta = getattr(first, "meta", None)
    # ★ meta 없이 파일로 내지 않는다.  이름이 report.md 로 겹쳐 덮어쓴다 (V8-01).
    #   전 요소를 ReportMeta 에서 가져온다 — 손으로 조립하지 않는다 (STEP 91a)
    name = filename(meta, fmt) if meta else f"report.{fmt}"
    return ExportResult(name, body.encode("utf-8"), CONTENT_TYPE[fmt])


# ── STEP 91a 파일 출력 ───────────────────────────────────────────────
# ★ 경로는 config 가 아니라 고정이다.  임의 위치에 쓰지 않는다
OUTPUT_DIR = "outputs"
# 줄바꿈은 LF.  ★ Windows 에서도 LF 다 — CRLF 면 diff 가 전건 변경으로 보인다
NEWLINE = "\n"
# 인코딩은 UTF-8, BOM 없음.  ★ BOM 이 있으면 csv 첫 열 이름이 깨진다
ENCODING = "utf-8"


def output_path(res, root: str = ".") -> str:
    """outputs/{파일명}.  ★ 전 요소를 ReportMeta 에서 가져온다 (STEP 91a).

    손으로 조립하지 않는다 — 손으로 적으면 run_id 가 빠져 덮어쓴다
    """
    return os.path.join(root, OUTPUT_DIR, res.filename)


def write_export(res: ExportResult, root: str = ".") -> str:
    """리포트를 파일로 낸다.

    ★ 덮어쓰지 않는다.  같은 이름이면 FileExistsError 다 (V8-01).
      덮어쓰면 어제 것과 비교할 수 없다 — 재생성은 calc_version 이 올라간 뒤다
    ★ BOM 없는 UTF-8 · LF 다 (V8-02)
    """
    if res.filename.startswith("report."):
        raise ValueError(
            "ReportMeta 없이 파일로 낼 수 없다. 이름이 겹쳐 덮어쓴다 "
            "(STEP 91a · V8-01)")
    path = output_path(res, root)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        raise FileExistsError(
            f"{path} 가 이미 있다. 덮어쓰지 않는다 — "
            f"재생성은 calc_version 이 올라간 뒤다")
    body = res.content
    if isinstance(body, bytes):
        body = body.decode(ENCODING)
    # ★ BOM 을 떼고 CRLF 를 LF 로 낮춘다 (V8-02).
    #   BOM 이 있으면 csv 첫 열 이름이 깨지고, CRLF 면 diff 가 전건 변경이 된다
    body = body.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    # 원자적으로 쓴다.  ★ 중간에 죽으면 반쪽 파일이 남는다
    tmp = f"{path}.part"
    with open(tmp, "w", encoding=ENCODING, newline=NEWLINE) as f:
        f.write(body)
    os.replace(tmp, path)
    return path
