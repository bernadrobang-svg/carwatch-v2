import sys,json,re,urllib.parse

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get; from p1_census import parse_rows, head
    C=json.load(open('probe/census.json'))
    print("=== 무필터 3,137건 안에 조건 위반이 실제로 있는가 (필터가 '무시'인지 '해당없음'인지 가르기) ===")
    print("경과 30일 초과 행 수:", sum(1 for r in C if r['days'] and r['days']>30), "· 최대 경과", max(r['days'] for r in C if r['days']))
    print("옵션 5종 미만 행 수:", sum(1 for r in C if r['opt_n'] is not None and r['opt_n']<5))
    print("2024-09 이전 연식 행 수:", sum(1 for r in C if r['year'] and r['year']<'2024-09'))
    print("사이트 값 종류:", set(r['site'] for r in C))
    def q(u):
        s,t,b=get(u); h=head(b); return h[0] if h else None
    print("\n=== 무시 여부 재판정 ===")
    for name,u in [("days_max=30","/listings?days_max=30"),("days_max=1","/listings?days_max=1"),
                   ("days_max=0","/listings?days_max=0"),("option_min=1","/listings?option_min=1"),
                   ("option_min=99","/listings?option_min=99"),("year_from=2026-01","/listings?year_from=2026-01"),
                   ("status=sold","/listings?status=sold"),("status=xxx","/listings?status=xxx"),
                   ("site=xxx","/listings?site=xxx"),("warranty_month_min=999","/listings?warranty_month_min=999"),
                   ("price_max=1","/listings?price_max=1"),("price_max=100000000","/listings?price_max=100000000")]:
        print(f"  {name:26s} → {q(u)}")
    print("\n=== 월납 40만 위반 행 찾기 ===")
    s,t,b=get("/listings?monthly_max=400000")
    for r in parse_rows(b):
        if r['monthly'] and r['monthly']>400000:
            print("  위반",r['id'],r['price']/1e4,"만 · 월",r['monthly']/1e4,"만 ·",r['model'])
    print("\n=== 월납 계산식 역산 (현금 1,500만 고정?) ===")
    for r in C[:6]:
        if r['monthly'] and r['buy']:
            print(f"  가격{r['price']/1e4:6.0f} 총{r['buy']/1e4:6.0f} 월{r['monthly']/1e4:5.1f}  (총-1500)/48={(r['buy']-15000000)/48/1e4:6.1f}  (가격-1500)/48={(r['price']-15000000)/48/1e4:6.1f}")
    print("\n=== 현황 화면 링크 전수 ===")
    s,t,root=get("/")
    links=sorted(set(re.findall(r'href="(/listings\?[^"]+)"', root)))
    print("현황 → 목록 링크",len(links),"개")
    dead=[]
    for L in links:
        n=q(L.replace('&amp;','&'))
        if n in (0,None) or n==3137: dead.append((L,n))
    for L,n in dead: print(f"  ★ {L:60s} → {n}")
    print(f"  (정상 {len(links)-len(dead)} · 문제 {len(dead)})")

