# -*- coding: utf-8 -*-
"""등록부 분류 초안 — 파서가 쓰는 경로를 근거로 자동 분류한다.

지시서   8장 STEP 87 (등록부) · 2장 STEP 20 (매핑표)
근거     ★ 302건을 손으로 분류하지 않는다.  파서가 읽는 경로는 in_use 다.
         suggested.json 의 후보는 매핑표를 못 봐서 핵심 필드까지 unclassified 였다
금지     자동 분류를 그대로 정본에 넣는 것.  사람이 확인한다 (STEP 87)
사용     python tools/classify_fields.py <suggested.json> [> draft.json]
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPING = os.path.join(ROOT, "parse", "encar", "mapping.py")

# 규칙 — 근거가 있는 것만.  애매하면 손대지 않는다
RULES: tuple[tuple[str, str, str], ...] = (
    (r"Photos?(\[\])?\.|Photo$|DealerPhoto|photo", "display_only",
     "사진. 화면 표시"),
    (r"AdWords|Hotmark|ServiceMark|preVerified|encarCheck|Advertisement$",
     "unused_by_policy", "엔카 마케팅 표시. 차량 품질이 아니다"),
    (r"BuyType|Separation|meetGo|homeService|HomeService",
     "unused_by_policy", "거래 방식. 차량 품질이 아니다"),
    # ★ LeaseType 은 판정 축이다 (E등급 · STEP 82).  금융 조건과 가른다
    (r"LeaseType$|leaseType$", "in_use", "리스·렌트 구분.  E등급 판정 (STEP 82)"),
    (r"Advances|Deposit|MonthLease|leaseRentInfo|lease(?!Type)|Lease(?!Type)",
     "unused_by_policy", "리스 금융 조건.  구매 대상이 아니다"),
    (r"viewCount|subscribeCount|ViewCount", "display_only", "인기도. 화면 표시"),
    (r"^Trust$|Trust\.", "unused_by_policy",
     "facet Trust 는 금지 근거다 (7장 STEP 79)"),
)


# ★ 파서가 통째로 저장하는 컨테이너 (STEP 32).
#   하위 경로를 개별로 읽지 않으므로 AST 로는 안 잡힌다.
#   그래도 in_use 다 — 원문이 그대로 CORE 에 들어간다
WHOLE_CONTAINERS: tuple[str, ...] = (
    "outers", "inners", "etcs", "images", "carInfoChanges", "accidents",
    "options.standard", "options.choice", "usageChangeTypes",
    "recallFullFillTypes",
)


def parser_paths() -> set[str]:
    """파서가 실제로 읽는 원문 경로.  코드에서 뽑는다 — 표를 손으로 옮기지 않는다."""
    src = open(MAPPING, encoding="utf-8").read()
    tree = ast.parse(src)
    out: set[str] = set()
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "attr", getattr(n.func, "id", ""))
        if fn not in ("_get", "get"):
            continue
        for a in n.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.add(a.value)
    return out


def decide(path: str, cand: dict, used: set[str]) -> tuple[str, str] | None:
    """반환   (usage, reason) · None 이면 사람이 판단한다."""
    leaf = path.split(":", 1)[1] if ":" in path else path
    bare = leaf.replace("[]", "")

    if bare in used or bare.split(".")[-1] in used:
        return "in_use", "파서가 읽는 경로 (2장 STEP 20 매핑표)"
    head = leaf.split("[]")[0]
    if head in WHOLE_CONTAINERS or head.split(".")[-1] in WHOLE_CONTAINERS:
        return "in_use", "컨테이너를 통째로 저장한다 (STEP 32). 원문 그대로 CORE 에"
    for pattern, usage, why in RULES:
        if re.search(pattern, leaf):
            return usage, why
    if cand["suggested_usage"] == "not_provided":
        return "not_provided", f"관측 {cand['observed']}건 전건 null·false"
    return None


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    with open(sys.argv[1], encoding="utf-8") as f:
        cands = json.load(f)["candidates"]
    used = parser_paths()

    seed: dict = {}
    residual: list[tuple[str, dict]] = []
    for path, cand in sorted(cands.items()):
        got = decide(path, cand, used)
        if got is None:
            residual.append((path, cand))
            continue
        usage, reason = got
        entry = {"usage": usage, "reason": reason}
        if usage in ("in_use", "display_only"):
            entry["core_column"] = "(확인 필요)"
        seed[path] = entry

    print(json.dumps({"_note": "자동 초안. 사람이 확인한 뒤 field_usage.json 의 "
                               "seed 로 옮긴다 (STEP 87)",
                      "_residual": len(residual),
                      "seed": seed}, ensure_ascii=False, indent=2))
    print(f"\n// 자동 {len(seed)}건 · 사람 판단 {len(residual)}건",
          file=sys.stderr)
    for path, cand in residual:
        print(f"//   {path:52} 관측 {cand['observed']:4} "
              f"{str(cand['samples'])[:44]}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())


def parser_lines() -> dict:
    """파서가 그 경로를 읽는 파일·줄.  ★ 코드에서 뽑는다 — 손으로 안 적는다.

    ★ store 가 이것을 못 부른다 (V4-22 — store 는 contracts·errors 만).
      부르는 쪽이 store 에 넘긴다
    """
    rel = os.path.relpath(MAPPING, ROOT)
    out: dict = {}
    tree = ast.parse(open(MAPPING, encoding="utf-8").read())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = getattr(node.func, "attr", getattr(node.func, "id", ""))
        if fn not in ("_get", "get"):
            continue
        for arg in node.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                out.setdefault(arg.value, f"{rel}:{node.lineno}")
    return out
