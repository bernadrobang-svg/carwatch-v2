# -*- coding: utf-8 -*-
"""파서가 읽는 원문 경로 — 코드에서 뽑는다 (2장 STEP 20).

지시서   8장 STEP 87 (등록부) · 2장 STEP 20 (매핑표)
근거     ★ 표를 손으로 옮기지 않는다.  파서가 읽는 경로가 정본이다
        ★ 이 지식은 parse 계층의 것이다 — store · validate · tools 가 읽는다.
          store 가 tools 를 부르면 역방향이다 (V4-22 · 실측 08-19)
금지     경로 목록을 두 벌 두는 것.  갈리면 「32건」과 화면의 수가 어긋난다
"""
from __future__ import annotations

import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
MAPPING = os.path.join(ROOT, "parse", "encar", "mapping.py")

# 통째로 읽는 컨테이너.  ★ 파서가 안을 돌기 때문에 잎 이름으로는 안 잡힌다
WHOLE_CONTAINERS: tuple[str, ...] = (
    "outers", "inners", "etcs", "images", "carInfoChanges", "accidents",
    "options.standard", "options.choice", "usageChangeTypes",
    "recallFullFillTypes",
)

_CACHE: dict | None = None


def _read() -> dict:
    """경로 → 그것을 읽는 파일·줄.  ★ 한 번만 훑는다."""
    global _CACHE
    if _CACHE is None:
        rel = os.path.relpath(MAPPING, ROOT)
        got: dict = {}
        tree = ast.parse(open(MAPPING, encoding="utf-8").read())
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if fn not in ("_get", "get"):
                continue
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    got.setdefault(arg.value, f"{rel}:{node.lineno}")
        _CACHE = got
    return _CACHE


def parser_paths() -> set:
    """파서가 실제로 읽는 원문 경로."""
    return set(_read())


def parser_lines() -> dict:
    """그 경로를 읽는 파일·줄.  ★ 손으로 안 적는다."""
    return dict(_read())
