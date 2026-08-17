# -*- coding: utf-8 -*-
"""CarWatch v2 지시서 자체 점검 — 7종
사용:  python3 check_spec.py <문서.md>
종료:  0 통과 · 1 실패"""
import io,re,sys

PATH = sys.argv[1] if len(sys.argv)>1 else "docs"
# ★ 지시서가 여러 파일이면 합쳐 읽는다 (v3 T-002).
#   단일 파일 전제를 두면 장이 나뉜 뒤 검사가 옛 판을 본다 — 실측으로 겪었다
def _read_spec(path: str) -> str:
    import glob as _g
    import os as _o

    if _o.path.isdir(path):
        files = sorted(_g.glob(_o.path.join(path, "**", "*.md"),
                               recursive=True))
        # ★ 파일 사이에 경계를 둔다.  안 두면 앞 파일의 절이
        #   뒤 파일의 코드블록을 삼킨다 (실측: checks.json ← web.json)
        return "\n\n# ---\n\n".join(io.open(f, encoding="utf-8").read()
                                     for f in files)
    return io.open(path, encoding="utf-8").read()


S = _read_spec(PATH)
L = S.split("\n")
fail = []

# ① 코드 펜스 짝수
n=0; stack=[]
for i,l in enumerate(L,1):
    if l.strip().startswith("`"*3) or l.strip().startswith("~"*3):
        n+=1
        if n%2==1: stack.append(i)
        else: stack.pop()
print(f"① 펜스 {n}개 · 미닫힘 {stack}")
if stack: fail.append(f"펜스 미닫힘 {stack}")

# ② [판정] 스텝 6항목 — 헤더 블록 줄첫머리 라벨
marks=[(m.start(),m.group(1),m.group(0)) for m in re.finditer(r"^## (STEP [\w.]+)([^\n]*)",S,re.M)]
marks.append((len(S),None,None))
TYPE_LABELS={
  "[판정]": ["목적","원천","값규칙","근거","금지","검산"],
  "[규격]": ["목적","원천","입력","출력","값규칙","근거","금지","검산"],
  "[수집]": ["목적","원천","값규칙","근거","금지","검산"],
  "[검증]": [],          # 검사 표 자체가 규격이다
  "[목록]": [],          # 목록은 항목이 내용이다
}
bad=[]; njudge=0
for i in range(len(marks)-1):
    a,name,head=marks[i]; b=marks[i+1][0]
    tag=next((t for t in TYPE_LABELS if t in head), None)
    if tag is None: continue
    LABELS=TYPE_LABELS[tag]
    if not LABELS: continue
    njudge+=1
    m=re.search(r"```\n(.*?)```",S[a:b],re.S)
    blk=m.group(1) if m else ""
    miss=[k for k in LABELS if not re.search(r"^%s"%k,blk,re.M)]
    if miss: bad.append((name,miss))
print(f"② 유형 표기 STEP {njudge}개 · 누락 {len(bad)}")
for x,y in bad: print(f"   {x:12} {' · '.join(y)}")
if bad: fail.append(f"판정 항목 누락 {len(bad)}")

# ③ 참조 무결성
# ★ 이력은 「그때 그랬다」이지 현재 참조가 아니다.
#   개정 230 행의 「STEP 205」는 그날의 수치 기록이고, 지금 가리키는 곳이 아니다
# 참조 무결성은 규격 본문(chapters · ref) 안에서 본다.
# ★ 색인과 이력은 「그때 그랬다」·「몇 개다」이지 현재 참조가 아니다 —
#   INDEX 의 「STEP 205」는 총수 표기이고 가리키는 곳이 아니다
_REF_DIRS = ("chapters", "ref")


def _refs_source() -> str:
    import glob as _g
    import os as _o

    if not _o.path.isdir(PATH):
        return S
    files = []
    for d in _REF_DIRS:
        files += sorted(_g.glob(_o.path.join(PATH, d, "**", "*.md"),
                                recursive=True))
    return "\n\n# ---\n\n".join(io.open(f, encoding="utf-8").read()
                                 for f in sorted(files))


_R = _refs_source()
heads={m.group(1) for m in re.finditer(r"^## (STEP [\w.]+)",_R,re.M)}
refs={m.group(1) for m in re.finditer(r"(STEP [\w.]+)",_R)}
miss=sorted(r for r in refs-heads if re.match(r"STEP \d+[a-z]?$",r))
print(f"③ 참조 {len(refs)} · 깨진 링크 {len(miss)} {miss[:6]}")
if miss: fail.append(f"깨진 참조 {miss[:6]}")

# ④ 구조체 — 필드 타입 · 반환 화살표 · 함수표 「출력」 열
defined = set(re.findall(r"^class (\w+)",S,re.M)) | set(re.findall(r"class (\w+)\(",S))
toks  = {t for o in re.findall(r"^\|\s*`[a-z_]+`\s*\|[^|]*\|\s*`?([^|`]*)`?\s*\|",S,re.M)
           for t in re.findall(r"[A-Z]\w{3,}",o)}
toks |= {t for t in re.findall(r"->\s*`?([A-Z]\w{3,})",S)}
toks |= {t for t in re.findall(r":\s*([A-Z]\w{3,})\b",S)}
KNOWN={"KOLEOS_HEV","TEXT","INTEGER","REAL","HomeServiceVerification","SearchResults","GRANDEUR","GV60","GV70","KOLEOS","SPORTAGE","G80","G70","MODEL_Y","CarType","Manufacturer","ModelGroup","Year","Price","Hidden","MultiViewHidden","None","Component","RAW","CORE","STEP","API","URL","JSON","SQL","DTO",
       "Badge","Options","Aspect","Protocol","Response","Analyzer","Scorer","Reporter","NULL",
       "Validator","Collector","Parser","SiteAdapter","MODEL_Y","G80_25T","GV70_EV"}
und=sorted(toks-defined-KNOWN)
print(f"④ 구조체 미정의 {len(und)} {und[:8]}")
if und: fail.append(f"구조체 미정의 {und[:8]}")

# ⑤ config 대조
files=set(m.group(1) for m in re.finditer(r"config/([a-z_]+(?:\.[a-z_]+)*\.json|dictionaries/)",S))
tbl  =set(re.findall(r"\| `([a-z_.]+\.json|dictionaries/)`",S))
gap=sorted(f for f in files if f.rstrip("/") not in {t.rstrip("/") for t in tbl})
ex=set(re.findall(r"#### `config/([a-z_.]+(?:\.json)?/?)`",S))
GEN={"field_usage.suggested.json"}   # 생성물.  예시가 없는 것이 정상
noex=sorted(f for f in files if f not in ex and f not in GEN)
noex=[f for f in noex if f"#### `config/{f}`" not in S]
print(f"⑤ config 파일 {len(files)} · 표 누락 {len(gap)} {gap} · 부록 예시 없음 {len(noex)} {noex}")
if noex: fail.append(f"부록 B 예시 없음 {noex}")
if gap: fail.append(f"config 표 누락 {gap}")

# ⑥ 접미사 — _cnt(원문) vs _count(산출)
raw_cols={m.group(1) for m in re.finditer(r"\| `[\w.\[\]]+` \| [^|]* \| `(\w+)`",S)}
viol=sorted(c for c in raw_cols if c.endswith("_count"))
print(f"⑥ 접미사 위반 {len(viol)} {viol}   (매핑표에 원천이 있는데 _count)")
if viol: fail.append(f"접미사 위반 {viol}")

# ⑦ 산술 검산
m=re.search(r"\| 축 \(Axis\) \| 배점.*?\n\|[-: |]+\n((?:\|.*\n)+)",S)
if m:
    pts=[];comp=0
    for r in [x for x in m.group(1).split("\n") if x.startswith("|")]:
        c=[x.strip() for x in r.split("|")[1:-1]]
        if len(c)<4 or "합" in c[0]: continue
        p=re.search(r"\d+",c[1]); pts.append(int(p.group()) if p else 0)
        sub=c[3]
        if sub in ("—",""): comp += 1
        else:
            items=re.findall(r"`([a-z_.]+)`\s*(\d+)(\s*\(스킵\))?",sub)
            comp += sum(1 for _,_,sk in items if not sk)
            pts[-1]=sum(int(v) for _,v,sk in items if not sk) or pts[-1]
    claim=sorted(set(re.findall(r"(\d+) Component",S))|set(re.findall(r"총 (\d+)행",S)))
    print(f"⑦ 배점합 {sum(pts)} · Component {comp} · 본문 주장 {claim}")
    if claim and any(x!=str(comp) for x in claim):
        fail.append(f"Component 수 불일치 {comp} vs {claim}")
    tot=re.search(r"\| \*\*합\*\* \| \*\*(\d+)\*\*",m.group(1))
    if tot and int(tot.group(1))!=sum(pts):
        fail.append(f"배점합 불일치 {sum(pts)} vs {tot.group(1)}")
else:
    print("⑦ 배점 표를 찾지 못함"); fail.append("배점 표 없음")

# ⑧ 테이블.컬럼 참조 무결성
ddl=dict(re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);",S,re.S))
cols={t:set(re.findall(r"^\s{2}(\w+)\s+(?:TEXT|INTEGER|REAL)",b,re.M)) for t,b in ddl.items()}
badref=sorted({f"{m.group(1)}.{m.group(2)}"
               for m in re.finditer(r"`?(\w+)\.(\w+)`?",S)
               if m.group(1) in cols and m.group(2) not in cols[m.group(1)]
               and not m.group(2)[0].isupper()})
print(f"⑧ 테이블 {len(cols)}개 · DDL에 없는 컬럼 참조 {len(badref)} {badref[:6]}")
if badref: fail.append(f"컬럼 참조 오류 {badref[:6]}")

# ⑨ 본문 config 예시 자체 검산
mc=re.search(r'"components": \{(.*?)\n  \}',S,re.S)
mt=re.search(r'"total_points": (\d+)',S)
if mc and mt:
    # 두 형태를 지원한다 — "k": N  ·  "k": {"points": N, "skipped": bool}
    vals=[]
    for km in re.finditer(r'"([a-z_.]+)"\s*:\s*(\{[^}]*\}|\d+)', mc.group(1)):
        key, raw = km.group(1), km.group(2)
        if key.startswith("_"): continue
        if raw.startswith("{"):
            if re.search(r'"skipped"\s*:\s*true', raw): continue   # 스킵은 총점에서 뺀다
            pm = re.search(r'"points"\s*:\s*(\d+)', raw)
            if pm: vals.append(int(pm.group(1)))
        else:
            vals.append(int(raw))
    ok=sum(vals)==int(mt.group(1))
    print(f"⑨ config 예시 components {len(vals)}개 · 합 {sum(vals)} vs total_points {mt.group(1)}")
    if not ok: fail.append(f"config 예시 배점합 {sum(vals)} != {mt.group(1)}")
    if str(len(vals)) not in claim: fail.append(f"config 예시 components {len(vals)} != 본문 {claim}")
else:
    print("⑨ config 예시를 찾지 못함")

# ⑩ 영향표 반영 — STEP 125a 표의 각 행이 해당 장에 실제로 있는가
rows_all=""
for _h in ("### 실제로 고쳐야 하는 것", "### 13장 외 — 같은 시점에 반영할 것"):
    _m=re.search(re.escape(_h)+r"[^|]*\n\|[^\n]*\n\|[-: |]+\n((?:\|.*\n)+)",S)
    if _m: rows_all+=_m.group(1)
mi=re.match(r"((?:\|.*\n)+)",rows_all) if rows_all else None
if mi:
    chap={}
    for m in re.finditer(r"^# (\d+)장\.",S,re.M): chap[m.group(1)]=m.start()
    ends=sorted(chap.values())+[len(S)]
    span={c:(p,ends[ends.index(p)+1]) for c,p in chap.items()}
    miss=[]
    for row in mi.group(1).strip().split("\n"):
        c=[x.strip() for x in row.split("|")[1:-1]]
        if len(c)<3: continue
        ch=c[0].strip("*")
        toks=re.findall(r"`([A-Za-z_][A-Za-z0-9_.]{2,})`",c[2])
        if ch not in span or not toks: continue
        a,b=span[ch]; body=S[a:b]
        for t in toks:
            if t not in body: miss.append(f"{ch}장:{t}")
    print(f"⑩ 영향표 반영 미확인 {len(miss)} {miss[:6]}")
    if miss: fail.append(f"영향표 미반영 {miss[:6]}")
else:
    print("⑩ 영향표를 찾지 못함")

# ⑪ 부록 E ↔ 실제 파일 동기화
import os
E_MAP={"tests/fixtures/EXPECTED.json":"E-2","tests/fixtures/NOTES.json":"E-3"}
desync=[]
for path,sec in E_MAP.items():
    if not os.path.exists(path):
        base=os.path.basename(path)
        cand=[base, f"fixtures/{base}"]
        path=next((c for c in cand if os.path.exists(c)), None)
        if path is None: continue
    body=io.open(path,encoding="utf-8").read().strip()
    FEN="`"*3+"|"+"~"*3
    m=re.search(r"## %s\..*?(?:%s)(?:python|json)\n(.*?)(?:%s)" % (sec,FEN,FEN), S, re.S)
    if not m: desync.append(f"{sec} 블록 없음"); continue
    if m.group(1).strip()!=body: desync.append(f"{sec} 내용 불일치")
print(f"⑪ 부록 E 동기화 {len(desync)} {desync}")
if desync: fail.append(f"부록 E 불일치 {desync}")

# ⑫ V4-14 · V4-16 — 본문 config 참조가 STEP 6 표에 있는가
#    ★ 표에 없는 키를 본문이 쓰면 개발측이 없는 키를 구현한다
import json as _json
step6 = set()
for m in re.finditer(r"^\| `([\w.]+\.json)` \| (.+?) \|", S, re.M):
    f = m.group(1)
    for k in re.findall(r"`([\w.\[\]]+)`", m.group(2)):
        step6.add(f"{f}.{k}")
        step6.add(k)
refs = set(re.findall(r"config\.([\w]+\.json)\.([\w.]+)", S))
badref = sorted({f"{f}.{k}" for f, k in refs
                 if f"{f}.{k}" not in step6 and k.split(".")[0] not in step6})
print(f"⑫ 본문 config 참조가 STEP 6 표에 있음 {len(badref)} {badref[:6]}")
if badref: fail.append(f"STEP 6 표에 없는 키 {len(badref)}")

# ⑬ V4-18 — 상수표 이름과 config 키가 같은 뜻으로 겹치지 않는가
# ★ 개정 이력 행은 제외한다.  「제거했다」는 기록이 「지금 있다」로 잡힌다
consts = {n for row in re.findall(r"^\|.*\|$", S, re.M)
          if not re.match(r"^\| \d+ \| \d{2}-\d{2} \|", row)
          for n in re.findall(r"`([A-Z][A-Z0-9_]*)`", row)}
cfgkeys = {k.split(".")[-1] for k in step6}
dup = sorted({c for c in consts if c.lower() in cfgkeys})
print(f"⑬ 상수표 ↔ config 키 중복 {len(dup)} {dup[:6]}")
if dup: fail.append(f"상수와 config 키 중복 {dup}")

# S17 — 검사 대상 대조 (부록 E · 08-14 신설)
# ★ 장 파일이 늘었는데 CW_CHAPTERS 를 안 늘리면 그 장이 조용히 안 검사된다.
#   실측: 14장을 빼먹어 구조체 4 · 함수 5 가 미착수로 잡혔다
import glob as _glob
import os as _os

_cfg_path = _os.path.join(_os.path.dirname(_os.path.dirname(
    _os.path.abspath(__file__))), "config", "checks.json")
if _os.path.isfile(_cfg_path):
    _cfg = _json.load(io.open(_cfg_path, encoding="utf-8"))
    _root = _os.path.dirname(_cfg_path).replace("config", "")
    _files = _glob.glob(_os.path.join(_root, _cfg["spec_glob"]),
                        recursive=True)
    _chapters = {int(_os.path.basename(f)[:2]) // 10 if
                 _os.path.basename(f)[:2].isdigit() else -1
                 for f in _files}
    _want = set(_cfg["chapters"])
    _env = _os.environ.get("CW_CHAPTERS", "")
    _declared = {int(x) for x in _env.split(",") if x.strip().isdigit()}
    _bad = []
    if not _files:
        _bad.append(f"spec_glob 이 파일을 못 찾는다: {_cfg['spec_glob']}")
    if _declared and _declared != _want:
        _bad.append(f"CW_CHAPTERS {sorted(_declared)} != "
                    f"checks.json {sorted(_want)}")
    if not _os.path.isdir(_os.path.join(_root, _cfg["screens_dir"])):
        _bad.append(f"screens_dir 가 없다: {_cfg['screens_dir']}")
    print(f"S17 검사 대상 대조 {len(_bad)} {_bad}")
    if _bad:
        fail.append(f"검사 대상 {_bad}")
else:
    print("S17 검사 대상 대조 — config/checks.json 이 없다")
    fail.append("checks.json 없음")

def _spec_files() -> list:
    """검사 대상 파일 목록.  ★ 합쳐 읽지 않는다 — 파일별로 본다."""
    import glob as _g

    if _os.path.isdir(PATH):
        return sorted(_g.glob(_os.path.join(PATH, "**", "*.md"),
                              recursive=True))
    return [PATH]


# ── S18 config 예시 유일성 ──────────────────────────────────────────
# ★ 같은 파일의 JSON 예시가 두 곳에 있으면 반드시 갈린다.
#   실측: 같은 값이 두 파일에 있어 화면마다 갈렸다 (E-5)
_seen: dict = {}
for _f in _spec_files():
    _body = io.open(_f, encoding="utf-8").read()
    for _m in re.finditer(r"```json\s+//\s*(config/[\w.]+)", _body):
        _seen.setdefault(_m.group(1), []).append(_os.path.basename(_f))
_dup = [f"{k}: {v}" for k, v in _seen.items() if len(v) > 1]
print(f"S18 config 예시 유일성 {len(_dup)} {_dup[:4]}")
if _dup:
    fail.append(f"config 예시 중복 {_dup[:3]}")

# ── S19 검증 코드 정규식 범위 ───────────────────────────────────────
# ★ 차수를 손으로 나열하면 새 차수가 조용히 검사 밖으로 나간다.
#   실측: V11 15건이 검사 밖에 있었다 (D-1)
_src = io.open(_os.path.join(_root, "tools", "check_src.py"),
               encoding="utf-8").read()
_phases = {m.group(1) for m in re.finditer(r"\b(V\d{1,2})-\d+", S)}
_hand = re.search(r"V\(\?:[\d|]+\)-", _src)
_bad19 = []
if _hand:
    _bad19.append(f"차수를 손으로 나열한다: {_hand.group(0)}")
if r"V\d{1,2}-" not in _src:
    _bad19.append("전 차수 정규식이 없다")
print(f"S19 검증 코드 정규식 범위 {len(_bad19)} {_bad19} · 차수 {len(_phases)}")
if _bad19:
    fail.append(f"정규식 범위 {_bad19}")

# ── S20 유형 표기 필수 ──────────────────────────────────────────────
# ★ 태그 없는 STEP 은 검사가 통째로 건너뛴다 — 없는 것과 같다
_untagged = []
for _f in _spec_files():
    for _m in re.finditer(r"^## (STEP [\w.]+)(.*)$",
                          io.open(_f, encoding="utf-8").read(), re.M):
        if "[" not in _m.group(2):
            _untagged.append(f"{_os.path.basename(_f)}:{_m.group(1)}")
print(f"S20 유형 표기 필수 {len(_untagged)} {_untagged[:4]}")
if _untagged:
    fail.append(f"태그 없는 STEP {len(_untagged)}")

# ── S21 불변식 전건 ─────────────────────────────────────────────────
# ★ 「나중에」로 두면 시험이 「전부 통과」로 나오는데 절반만 본다
_inv = io.open(_os.path.join(_root, "tests", "test_invariants.py"),
               encoding="utf-8").read()
_miss21 = [n for n in "①②③④⑤⑥" if f"불변식{n}" not in _inv]
print(f"S21 불변식 전건 {len(_miss21)} {_miss21}")
if _miss21:
    fail.append(f"불변식 누락 {_miss21}")

# ── S22 정적 검사 ───────────────────────────────────────────────────
# ★ ruff 가 훅에 없으면 아무도 돌리지 않는다
_run = io.open(_os.path.join(_root, "tools", "run_tests.py"),
               encoding="utf-8").read()
_bad22 = [] if "ruff" in _run else ["run_tests 가 ruff 를 부르지 않는다"]
print(f"S22 정적 검사 등재 {len(_bad22)} {_bad22}")
if _bad22:
    fail.append(f"정적 검사 {_bad22}")

# ── S28 가이드 작업 규칙 (개정 333) ─────────────────────────────────
# ★ 가이드가 자기를 검사하면 같은 맹점을 넘긴다.
#   「고치는 쪽」과 「검사하는 쪽」이 갈린다 — 그것이 검사의 뜻이다
#   ★ 개발측은 지시서를 고치지 않는다 (규칙 2).  잡아서 넘긴다
# ★ 정본 위치는 config/checks.json 이 안다 (개정 342).
#   여기 박아 두면 문서가 옮겨진 날 S28 이 빈 파일을 검사한다
CANON_ALL = (_cfg.get("canon") or {}) if "_cfg" in dir() else {}
CANON = {k: (v[0] if isinstance(v, list) else v)
         for k, v in CANON_ALL.items()}
# 정본 밖에 나오면 안 되는 숫자.  ★ 배점의 총합과 등급 기준이다
CANON_NUMBERS = ("605", "555")
# 폐기 표시 문구 — 이것이 있으면 그 절은 건너뛴다
RETIRED_MARK = "폐기"


def _guide_files() -> list:
    return [f for f in _spec_files()
            if "/ref/" not in f.replace("\\", "/")]


def _sections(body: str) -> list:
    """머리말 단위로 자른다.  ★ 「폐기」가 붙은 절을 건너뛰기 위해서다."""
    out, cur = [], []
    for line in body.splitlines():
        if line.startswith("#") and cur:
            out.append("\n".join(cur))
            cur = []
        cur.append(line)
    if cur:
        out.append("\n".join(cur))
    return out


# S28-1 · S28-2 — 정본 밖 숫자
_bad28_1, _bad28_2 = [], []
for _f in _guide_files():
    _rel = _f.split("docs/", 1)[-1]
    for _sec in _sections(io.open(_f, encoding="utf-8").read()):
        head = _sec.splitlines()[0] if _sec else ""
        if RETIRED_MARK in head or RETIRED_MARK in _sec[:400]:
            continue                    # 폐기 표시가 있으면 건너뛴다
        for _n in CANON_NUMBERS:
            if re.search(rf"\b{_n}\b *점", _sec):
                _bad28_1.append(f"{_rel} — 배점 {_n} 이 정본 밖에 있다")
                break
        # ★ 화면 정본이 일곱 파일로 쪼개졌다 (개정 342).  전부 정본이다 —
        #   첫 파일만 정본으로 보면 나머지 여섯이 「정본 밖」이 된다
        if re.search(r"\d+×\d+", _sec) and not any(
                _rel.replace("\\", "/").endswith(w)
                for w in (CANON_ALL.get("화면") or ())):
            _bad28_2.append(f"{_rel} — 화면 크기가 정본 밖에 있다")

# S28-4 — 이력 마지막 개정 = 00_버전.md
_hist = next((io.open(f, encoding="utf-8").read() for f in _spec_files()
              if f.endswith("03_이력.md")), "")
_ver = next((io.open(f, encoding="utf-8").read() for f in _spec_files()
             if f.endswith("00_버전.md")), "")
_nums = sorted(int(x) for x in re.findall(r"^\| *(\d{2,3}) *\|", _hist, re.M))
_bad28_4 = []
_declared = re.search(r"SPEC-[\d.\-]+-r(\d+)", _ver)
if _nums and _declared and int(_declared.group(1)) != _nums[-1]:
    _bad28_4.append(f"버전 r{_declared.group(1)} != 이력 마지막 {_nums[-1]}")

# S28-5 — 본문이 참조하는 개정 번호가 이력에 실재하는가
_have = set(_nums)
_bad28_5 = []
for _f in _guide_files() + [f for f in _spec_files() if "/ref/" in f]:
    _rel = _f.split("docs/", 1)[-1]
    for _m in re.finditer(r"개정 (\d{2,3})", io.open(_f, encoding="utf-8").read()):
        if int(_m.group(1)) not in _have:
            _bad28_5.append(f"{_rel} — 개정 {_m.group(1)} 이 이력에 없다")
            break

# S28-6 — 개정 번호가 건너뛰거나 겹치지 않는가
_bad28_6 = []
if _nums:
    _dup = {n for n in _nums if _nums.count(n) > 1}
    if _dup:
        _bad28_6.append(f"겹친 개정 {sorted(_dup)}")
    _gap = [n for n in range(_nums[0], _nums[-1] + 1) if n not in _have]
    if _gap:
        _bad28_6.append(f"빠진 개정 {_gap[:8]}")

# S28-3 — 폐기 표시와 00_버전.md 폐기 표가 일치하는가
_bad28_3 = []
# ★ 이력은 「| 306 | 08-17 | …」 꼴이다.  「개정 306」 문자열이 아니다
_retired_tbl = {int(x) for x in re.findall(r"^\| *개정 (\d{2,3})", _ver, re.M)}
for _n in sorted(_retired_tbl):
    if _n not in _have:
        _bad28_3.append(f"폐기 표의 개정 {_n} 이 이력에 없다")

# S28-7 — 정본끼리 모순되지 않는가 (부록 F 축 ↔ CHECKS.md)
_bad28_7 = []
_want_f = tuple(CANON_ALL.get("배점") or ())
_f_scoring = next((io.open(f, encoding="utf-8").read() for f in _spec_files()
                   if any(f.replace("\\", "/").endswith(w)
                          for w in _want_f)), "")
if _f_scoring:
    _sums = re.findall(r"\| \*\*합\*\* \| \*\*(\d+)\*\*", _f_scoring)
    _axes = re.findall(r"^\| *\d+ *\| *[가-힣]+ *\|", _f_scoring, re.M)
    if _sums and _axes:
        _rows = re.findall(r"^\| *\d+ *\| *[가-힣]+ *\| *[^|]+\| *(\d+) *\|",
                           _f_scoring, re.M)
        if _rows and sum(int(x) for x in _rows) != int(_sums[-1]):
            _bad28_7.append(
                f"부록 F 축 합 {sum(int(x) for x in _rows)} != 표기 {_sums[-1]}")

for _code, _title, _bad in (
    ("S28-1", "배점이 정본 밖에", _bad28_1),
    ("S28-2", "화면 크기가 정본 밖에", _bad28_2),
    ("S28-3", "폐기 표 ↔ 이력", _bad28_3),
    ("S28-4", "버전 ↔ 이력 마지막", _bad28_4),
    ("S28-5", "참조한 개정이 실재", _bad28_5),
    ("S28-6", "개정 번호 연속", _bad28_6),
    ("S28-7", "정본끼리 모순 없음", _bad28_7),
):
    print(f"{_code} {_title} {len(_bad)} {_bad[:4]}")
    if _bad:
        # ★ 개발측이 고치지 않는다.  기록에 남겨 가이드에게 넘긴다 (규칙 2)
        fail.append(f"{_code} {_bad[:2]}")

print("\n결과:", "통과" if not fail else "실패 — " + " / ".join(fail))
sys.exit(1 if fail else 0)
