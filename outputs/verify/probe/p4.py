import sys,json,re

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get; from p1_census import parse_rows, head
    C=json.load(open('probe/census.json'))
    def n(u):
        s,t,b=get(u); h=head(b); return (h[0] if h else None), parse_rows(b)
    print("=== 현황 사분위 25% 링크 — target 과 함께 오는 것 ===")
    for t_,p in [("G70_20T",25800000),("G80_25T",30990000),("KOLEOS_HEV",31900000),("MODEL_Y",39700000)]:
        a,_=n(f"/listings?target={t_}")
        b_,rows=n(f"/listings?target={t_}&price_max={p}")
        c,_=n(f"/listings?target={t_}&price_max={p//10000}")
        viol=sum(1 for r in rows if r['price']>p)
        print(f"  {t_:14s} 전체{a:5d} · 원단위{b_:5d}(위반{viol}/50) · 만원환산{c:5d}")
    print("\n=== 월납 필터 vs 화면 표기 불일치 ===")
    srv,_=n("/listings?monthly_max=400000")
    mine=[r for r in C if r['monthly'] is not None and r['monthly']<=400000]
    print(f"  서버 monthly_max=400000 → {srv}건 · 화면표기 월40만 이하 → {len(mine)}건 · 차 {len(mine)-srv}")
    s,t,b=get("/listings?monthly_max=400000&page=1")
    got={r['id'] for r in b and parse_rows(b)}
    ids_srv=set()
    for pg in range(1,16):
        s,t,b=get(f"/listings?monthly_max=400000&page={pg}")
        rs=parse_rows(b)
        if not rs: break
        ids_srv|={r['id'] for r in rs}
    mineids={r['id'] for r in mine}
    print(f"  서버집합 {len(ids_srv)} · 화면집합 {len(mineids)}")
    only=mineids-ids_srv
    print(f"  화면엔 월40만 이하인데 필터에서 빠진 것 {len(only)}건")
    for i in list(only)[:8]:
        r=next(x for x in C if x['id']==i)
        print(f"    id{i} {r['price']/1e4:5.0f}만 화면월 {r['monthly']/1e4:4.1f}만 링크값 {r['monthly_link']} {r['model']}")
    print("\n=== 3,000만 이하 691건과 월40만 691건이 같은 집합인가 ===")
    p30=set()
    for pg in range(1,16):
        s,t,b=get(f"/listings?price_max=3000&page={pg}")
        rs=parse_rows(b)
        if not rs: break
        p30|={r['id'] for r in rs}
    print(f"  가격3000이하 {len(p30)} · 월40이하 {len(ids_srv)} · 교집합 {len(p30&ids_srv)} · 가격만 {len(p30-ids_srv)} · 월납만 {len(ids_srv-p30)}")

