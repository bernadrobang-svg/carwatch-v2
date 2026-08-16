# -*- coding: utf-8 -*-
"""배점 조정 — 비율 재배분과 정수 보정.

지시서   13장 STEP 128 · 7장 STEP 68
근거     점수는 사람이 읽는 값이다.  47.5점은 비교를 어렵게 한다
금지     total_points 를 직접 입력하는 것.  성분 합으로만 정해진다
         0 이 되는 성분을 만드는 것 — 「0점」과 「스킵」은 다르다
"""
from __future__ import annotations

from contracts import total_of  # noqa: F401

from errors import PolicyError, ValidationError


def redistribute(components: dict[str, int], new_total: int) -> dict[str, int]:
    """축 총점 변경 시 성분을 비율로 재배분한다.

    1  각 성분 = round(기존 × 새 총점 ÷ 기존 총점)
    2  잔여 = 새 총점 − Σ(반올림 결과)
    3  잔여를 배점이 가장 큰 성분에 더한다.  같으면 이름 순 첫 번째
    4  Σ == new_total 을 저장 전에 검산한다
    """
    old_total = sum(components.values())
    if old_total <= 0:
        raise PolicyError("기존 총점이 0 이다", step="STEP 128")
    out = {k: round(v * new_total / old_total) for k, v in components.items()}

    zero = sorted(k for k, v in out.items() if v == 0)
    if zero:
        raise PolicyError(
            f"0 이 되는 성분: {zero}. 「점수 0」과 「스킵」은 다르다. "
            "skipped: true 를 쓴다",
            step="STEP 128")

    rest = new_total - sum(out.values())
    if rest:
        head = sorted(out, key=lambda k: (-out[k], k))[0]
        out[head] += rest
    if sum(out.values()) != new_total:
        raise PolicyError(
            f"재배분 합 {sum(out.values())} != {new_total}", step="STEP 128")
    return out


def apply_skip(components: dict, name: str, skipped: bool = True) -> dict:
    """components 에서 빼지 않는다.  skipped: true 로 표시한다.

    빼면 「있었는데 뺐다」가 기록되지 않는다 (STEP 128).
    """
    if name not in components:
        raise PolicyError(f"없는 성분: {name}", step="STEP 128")
    v = components[name]
    points = v["points"] if isinstance(v, dict) else int(v)
    out = dict(components)
    out[name] = {"points": points, "skipped": True} if skipped else points
    return out


# total_of 는 contracts.py 다 — store/admin 도 쓴다 (STEP 15a)

# ── STEP 128 배점 조정 ──────────────────────────────────────────────
# ★ 전부 정수다.  점수는 사람이 읽는 값이라 47.5점은 비교를 어렵게 한다


def _axis_of(component: str) -> str:
    return component.split(".")[0]


def _points_of(spec) -> int:
    return int(spec if isinstance(spec, int) else spec.get("points", 0))


def _skipped(spec) -> bool:
    return isinstance(spec, dict) and bool(spec.get("skipped"))


def _with_points(spec, points: int):
    """원래 형태를 지킨다.  ★ 스킵 표시를 지우면 「있었는데 뺐다」가 사라진다."""
    if isinstance(spec, dict):
        out = dict(spec)
        out["points"] = points
        return out
    return points


def redistribute_axis(components: dict, axis: str, new_total: int) -> dict:
    """축 총점 변경 — 그 축 성분만 골라 재배분한다 (STEP 128)."""
    members = {k: _points_of(v) for k, v in components.items()
               if _axis_of(k) == axis and not _skipped(v)}
    if not members:
        raise ValidationError(f"축에 성분이 없다: {axis}", step="STEP 128")
    scaled = redistribute(members, int(new_total))

    zeroed = sorted(k for k, v in scaled.items() if v <= 0)
    if zeroed:
        raise ValidationError(
            f"0 점이 되는 성분이 있다: {', '.join(zeroed)}. "
            f"빼려면 스킵을 쓴다 — 「0점」과 「스킵」은 다르다",
            step="STEP 128")
    out = dict(components)
    for k, v in scaled.items():
        out[k] = _with_points(components[k], v)
    return out


def set_component(components: dict, component: str, points: int) -> dict:
    """성분 점수 변경 — 그 성분만 바꾼다 (STEP 128)."""
    if component not in components:
        raise ValidationError(f"없는 성분: {component}", step="STEP 128")
    if points <= 0:
        raise ValidationError(
            "성분 점수는 1 이상이다. 빼려면 스킵을 쓴다", step="STEP 128")
    out = dict(components)
    out[component] = _with_points(components[component], points)
    return out


def set_skipped(components: dict, component: str, skipped: bool) -> dict:
    """성분 스킵 — components 에서 빼지 않는다 (STEP 128).

    ★ 빼면 「있었는데 뺐다」가 기록되지 않는다.  skipped: true 로 표시한다
    """
    if component not in components:
        raise ValidationError(f"없는 성분: {component}", step="STEP 128")
    out = dict(components)
    out[component] = {"points": _points_of(components[component]),
                      "skipped": bool(skipped)}
    return out


def next_components(components: dict, action: str, target: str,
                    value) -> dict:
    """조정 3종을 적용한 새 components 를 낸다 (STEP 128).

    ★ 저장은 하지 않는다.  파일 쓰기는 store 가 한다 — 층이 다르다
    """
    if action == "axis":
        return redistribute_axis(components, target, int(value))
    if action == "component":
        return set_component(components, target, int(value))
    if action == "skip":
        return set_skipped(components, target,
                           str(value).lower() in ("1", "true"))
    raise ValidationError(f"없는 조작: {action}", step="STEP 128")
