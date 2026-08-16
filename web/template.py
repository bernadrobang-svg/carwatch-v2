# -*- coding: utf-8 -*-
"""최소 템플릿 엔진 (14장 STEP 143).

지시서   STEP 143
근거     ★ Jinja2 의존을 넣지 않는다.  치환·반복·조건·상속 4개면 화면 11개가 된다.
         v1 이 Flask 였고 그것이 이식을 어렵게 했다 (0장 STEP 1)
금지     템플릿에서 DB 조회 · 점수 계산
         사용자 입력을 {{! }} 로 넣는 것
"""
from __future__ import annotations

import datetime
import html
import os
import re

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "templates")

RE_EXTENDS = re.compile(r"\{%\s*extends\s+([\w.]+)\s*%\}")
RE_BLOCK = re.compile(r"\{%\s*block\s+(\w+)\s*%\}(.*?)\{%\s*endblock\s*%\}",
                      re.S)
# 이름 경로.  ★ 대괄호 첨자를 여기서 받아야 _lookup 까지 간다.
#   안 받으면 {{ d.gc[g] }} 가 「값 없음」이 아니라 글자 그대로 찍힌다 (N-1)
PATH = r"[\w.\[\]'\"-]+"
RE_FOR_OPEN = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+(" + PATH + r")\s*%\}")
RE_FOR_ANY = re.compile(r"\{%\s*(for)\s+\w+\s+in\s+" + PATH + r"\s*%\}"
                        r"|\{%\s*(endfor)\s*%\}")
RE_IF_OPEN = re.compile(r"\{%\s*if\s+(!?" + PATH + r")\s*%\}")
RE_IF_ANY = re.compile(r"\{%\s*(if)\s+!?" + PATH + r"\s*%\}"
                       r"|\{%\s*(else)\s*%\}|\{%\s*(endif)\s*%\}")
RE_RAW = re.compile(r"\{\{!\s*([\w.]+)\s*\}\}")
RE_VAR = re.compile(r"\{\{\s*(" + PATH + r")\s*(?:\|\s*(\w+)\s*)?\}\}")

# ── 표시 필터 (STEP 152) ────────────────────────────────────────────
# ★ 필터는 표시만 한다.  반올림으로 값을 바꾸지 않는다.
#   값은 원 단위 정수로 온다 — 「48.5만」은 표기다
WON_PER_MANWON = 10000
WON_PER_EOKWON = 100000000


def f_won(v) -> str:
    """원 → 사람이 읽는 금액.  ★ 원본을 바꾸지 않는다."""
    if v in (None, ""):
        return "—"
    n = int(v)
    if abs(n) >= WON_PER_EOKWON:
        eok, rest = divmod(abs(n), WON_PER_EOKWON)
        man = rest // WON_PER_MANWON
        s = f"{eok}억" + (f" {man:,}만" if man else "")
    elif abs(n) >= WON_PER_MANWON:
        s = f"{abs(n) // WON_PER_MANWON:,}만"
    else:
        s = f"{abs(n):,}"
    return ("-" if n < 0 else "") + s


def f_km(v) -> str:
    return "—" if v in (None, "") else f"{int(v):,}km"


def f_pct(v) -> str:
    return "—" if v in (None, "") else f"{float(v) * 100:.1f}%"


def f_date(v) -> str:
    """ISO → YYYY-MM-DD.  ★ 표준 라이브러리가 형식을 안다 — 숫자를 안 적는다."""
    if not v:
        return "—"
    s = str(v).replace("Z", "+00:00")
    try:
        return datetime.date.fromisoformat(s.split("T")[0]).isoformat()
    except ValueError:
        return str(v)


def f_num(v) -> str:
    if v in (None, ""):
        return "—"
    n = float(v)
    return f"{int(n):,}" if n == int(n) else f"{n:,.1f}"


def f_gradecls(v) -> str:
    """등급 → CSS 클래스.  ★ 템플릿에서 문자열을 만들지 않는다 (STEP 152)."""
    s = str(v or "").strip().lower()
    return "grade-" + (s if s in ("s", "a", "b", "c", "d", "e") else "none")


def f_count(v) -> str:
    """건수.  ★ 화면에 수를 적지 않는다 — 세는 것은 여기서 한다."""
    try:
        return f"{len(v):,}"
    except TypeError:
        return "0"


FILTERS = {"won": f_won, "km": f_km, "pct": f_pct, "date": f_date,
           "num": f_num, "gradecls": f_gradecls, "count": f_count}

# ★ 원문 삽입을 허용하는 자리.  쓰는 곳을 센다 (V11-05)
RAW_ALLOW: frozenset[str] = frozenset({
    "page.body_html",      # 조립된 부분 템플릿
    "doc.body_html",       # 문서 뷰어 — 지시서 마크다운 (관리자 전용)
})


# 이름 조각 또는 [첨자].  ★ 점만 처리하면 {{ d.gc[g] }} 가 그대로 찍힌다
#   — 값이 없어서가 아니라 이름을 못 읽어서다 (N-1 · 실측 08-16)
_PATH_SEG = re.compile(r"([^.\[\]]+)|\[([^\]]*)\]")


def _index_key(ctx: dict, raw: str):
    """[ ] 안의 첨자를 값으로 바꾼다.

    'x' · "x"   글자 그대로
    3           정수 — 목록 첨자다
    g           문맥의 변수 (반복 변수를 첨자로 쓰는 자리다)
    """
    token = raw.strip()
    if len(token) >= 2 and token[0] == token[-1] and token[0] in "\"'":
        return token[1:-1]
    if token.lstrip("-").isdigit():
        return int(token)
    return _lookup(ctx, token)


def _step(cur, key):
    if key is None:
        return None
    if isinstance(cur, dict):
        return cur.get(key)
    if isinstance(cur, (list, tuple)):
        # ★ 범위를 벗어나면 None 이다.  터뜨리면 화면 하나가 통째로 500 이 된다
        return cur[key] if isinstance(key, int) and -len(cur) <= key < len(cur) \
            else None
    return getattr(cur, str(key), None)


def _lookup(ctx: dict, path: str):
    cur = ctx
    for name, sub in _PATH_SEG.findall(path):
        cur = _step(cur, name if name else _index_key(ctx, sub))
        if cur is None:
            return None
    return cur


def _truthy(value) -> bool:
    return bool(value) if not isinstance(value, str) else value != ""


def render_str(src: str, ctx: dict) -> str:
    """치환 · 반복 · 조건.  ★ 산술 연산이 없다 (V11-04)."""

    def expand_for(src: str) -> str:
        """★ 짝을 세어 닫는다.  정규식 non-greedy 는 중첩에서 깨진다.

        실측: for 안에 for 가 있으면 안쪽 endfor 를 바깥 것으로 잡아
              뒤 내용이 통째로 사라졌다
        """
        m = RE_FOR_OPEN.search(src)
        if not m:
            return src
        var, seq_path = m.group(1), m.group(2)
        depth, pos, end = 1, m.end(), None
        for mm in RE_FOR_ANY.finditer(src, m.end()):
            depth += 1 if mm.group(1) else -1
            if depth == 0:
                end, tail = mm.start(), mm.end()
                break
        if end is None:
            raise ValueError("{% for %} 에 짝이 되는 {% endfor %} 가 없다")
        body = src[pos:end]
        seq = _lookup(ctx, seq_path) or []
        made = "".join(render_str(body, {**ctx, var: item}) for item in seq)
        return src[:m.start()] + made + expand_for(src[tail:])

    def expand_if(src: str) -> str:
        """★ 짝을 세어 닫는다.  정규식 non-greedy 는 중첩에서 깨진다.

        실측: 'A{% if !c %}B{% if a %}C{% endif %}D{% endif %}E' 가
              ABDE 대신 ABE 로 나왔고, 거짓일 때 endif 가 화면에 찍혔다.
        for 는 고쳤는데 if 는 안 고쳐 가입 화면의 폼이 통째로 사라졌다 (B-3)
        """
        m = RE_IF_OPEN.search(src)
        if not m:
            return src
        cond = m.group(1)
        depth, else_at, end, tail = 1, None, None, None
        for mm in RE_IF_ANY.finditer(src, m.end()):
            if mm.group(1):
                depth += 1
            elif mm.group(2):
                if depth == 1:
                    else_at = mm.start(), mm.end()
            else:
                depth -= 1
                if depth == 0:
                    end, tail = mm.start(), mm.end()
                    break
        if end is None:
            raise ValueError("{% if %} 에 짝이 되는 {% endif %} 가 없다")
        if else_at:
            yes, no = src[m.end():else_at[0]], src[else_at[1]:end]
        else:
            yes, no = src[m.end():end], ""
        neg = cond.startswith("!")
        val = _truthy(_lookup(ctx, cond[1:] if neg else cond))
        made = render_str(yes if (val != neg) else no, ctx)
        return src[:m.start()] + made + expand_if(src[tail:])

    prev = None
    out = src
    while prev != out:                     # 중첩 for/if 를 안쪽부터 푼다
        prev = out
        out = expand_for(out)
        out = expand_if(out)

    def do_raw(m):
        path = m.group(1)
        if path not in RAW_ALLOW:
            raise ValueError(
                f"{{{{! {path} }}}} 는 허용 목록에 없다 (STEP 143 · V11-05). "
                f"사용자 입력을 원문으로 넣지 않는다")
        return str(_lookup(ctx, path) or "")

    out = RE_RAW.sub(do_raw, out)
    def do_var(m):
        raw = _lookup(ctx, m.group(1))
        name = m.group(2)
        if name:
            if name not in FILTERS:
                raise ValueError(f"없는 필터: {name} (STEP 152)")
            return html.escape(FILTERS[name](raw))
        return html.escape("" if raw is None else str(raw))

    return RE_VAR.sub(do_var, out)


def render(name: str, ctx: dict, root: str | None = None) -> str:
    """템플릿 파일 → HTML.  상속은 한 단계만 지원한다."""
    base_dir = root or TEMPLATE_DIR
    with open(os.path.join(base_dir, name), encoding="utf-8") as f:
        src = f.read()

    m = RE_EXTENDS.search(src)
    if not m:
        return render_str(src, ctx)

    blocks = {b: body for b, body in RE_BLOCK.findall(src)}
    with open(os.path.join(base_dir, m.group(1)), encoding="utf-8") as f:
        parent = f.read()
    filled = RE_BLOCK.sub(
        lambda mm: blocks.get(mm.group(1), mm.group(2)), parent)
    return render_str(filled, ctx)
