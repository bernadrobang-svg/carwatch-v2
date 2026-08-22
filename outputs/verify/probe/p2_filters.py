import sys, json, urllib.parse

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get; from p1_census import parse_rows, head
    RES=[]
    def T(name, q, check=None, note=""):
        s,t,b = get("/listings?"+q)
        if s!=200:
            RES.append(dict(name=name,q=q,http=s,n=None,bad=None,verdict="HTTP%d"%s,note=note)); 
            print(f"{name:34s} {q:44s} HTTP{s}"); return None
        h=head(b); rows=parse_rows(b); n=h[0] if h else None
        bad=None
        if check:
            bad=[r for r in rows if not check(r)]
        v = "OK" if (check is None or not bad) else f"위반 {len(bad)}/{len(rows)}"
        RES.append(dict(name=name,q=q,http=s,n=n,shown=len(rows),bad=(len(bad) if bad is not None else None),verdict=v,note=note))
        print(f"{name:34s} {q:44s} 200  {str(n):>6}건 표시{len(rows):3d}  {v}")
        return rows

    BASE=3137
    print("== 기준 무필터 ==");T("무필터","", None)
    print("\n== 차종 10 ==")
    chips={'G80_25T':1962,'MODEL_Y':580,'G70_20T':280,'KOLEOS_HEV':262,'GRANDEUR_LPG':258,
           'SPORTAGE_LPI':200,'GV60':129,'G70_25T':102,'GV70_EV':77,'G80_EV':66}
    census=json.load(open('probe/census.json'))
    from collections import Counter
    actual=Counter(r['model'] for r in census)
    for m,chip in chips.items():
        rows=T(f"차종 {m}", f"model={m}", lambda r,m=m: r['model']==m, f"칩표기 {chip} · 전수 {actual[m]}")
    print("\n== 가격(칩 단위=만원) ==")
    T("가격 상한 3000","price_max=3000", lambda r: r['price']<=30000000)
    T("가격 하한 5000","price_min=5000", lambda r: r['price']>=50000000)
    T("가격 2000~3500","price_min=2000&price_max=3500", lambda r: 20000000<=r['price']<=35000000)
    print("\n== 행/현황 링크가 보내는 원 단위 ==")
    T("행 가격링크(원)","price_max=60000000", lambda r: r['price']<=60000000)
    T("현황 사분위(원)","price_max=25800000", lambda r: r['price']<=25800000)
    T("현황 사분위(만 환산)","price_max=2580", lambda r: r['price']<=25800000)
    print("\n== 주행 ==")
    for km in (30000,50000,70000,100000,150000):
        T(f"주행 {km}","km_max=%d"%km, lambda r,k=km: r['km'] is not None and r['km']<=k)
    T("행 주행링크","km_max=20000", lambda r: r['km'] is not None and r['km']<=20000)
    print("\n== 색 ==")
    T("외장 흰색","color_ext=%s"%urllib.parse.quote("흰색"), lambda r: r.get('cext')=="흰색")
    T("외장 검정색","color_ext=%s"%urllib.parse.quote("검정색"), lambda r: r.get('cext')=="검정색")
    T("내장 베이지","color_int=%s"%urllib.parse.quote("베이지색 계열"), lambda r: r.get('cint')=="베이지색 계열")
    print("\n== 등급 ==")
    order=['S','A','B','C','D','E','F','G']
    for g in order:
        ok=set(order[:order.index(g)+1])
        T(f"min_grade {g}","min_grade=%s"%g, lambda r,ok=ok: r['grade'] in ok)
    for g in ['S','A','B','EXCLUDED','NOT_RATED','NO_GRADE']:
        T(f"grade= {g}","grade=%s"%g, lambda r,g=g: r['grade']==g)
    print("\n== 그 밖의 칩 ==")
    T("연식 year=2024","year=2024", lambda r: r['year'] and r['year'][:4]>='2024')
    T("행 연식링크 year_from","year_from=2024-09", lambda r: r['year'] and r['year']>='2024-09')
    T("옵션종수 option_min=5","option_min=5", lambda r: r['opt_n'] is not None and r['opt_n']>=5)
    T("트림 터보","trim=%s"%urllib.parse.quote("터보"), lambda r: r['trim'] and "터보" in r['trim'])
    T("트림 캘리그래피","trim=%s"%urllib.parse.quote("캘리그래피"))
    T("연료 가솔린","fuel=%s"%urllib.parse.quote("가솔린"))
    T("연료 전기","fuel=%s"%urllib.parse.quote("전기"))
    T("사이트 encar","site=encar")
    T("정직도 70","honesty_min=70")
    T("경과 30일","days_max=30", lambda r: r['days'] is not None and r['days']<=30)
    T("가격내린것","price_dropped=1")
    T("보증잔여 12","warranty_month_min=12")
    T("지역 서울","region=%s"%urllib.parse.quote("서울"))
    T("리스포함","lease=1")
    T("관문제외 따로","excluded=1")
    T("월납 40만","monthly_max=400000", lambda r: r['monthly'] is not None and r['monthly']<=400000)
    T("월납 110만","monthly_max=1100000", lambda r: r['monthly'] is not None and r['monthly']<=1100000)
    print("\n== 점수 필터 ==")
    T("값>=150","score_value_min=150", lambda r: '값' in r['bar'] and r['bar']['값'][0]>=150)
    T("차량>=100","score_car_min=100", lambda r: '차량' in r['bar'] and r['bar']['차량'][0]>=100)
    T("보증>=100","score_warranty_min=100", lambda r: '보증' in r['bar'] and r['bar']['보증'][0]>=100)
    T("취향>=90","score_taste_min=90", lambda r: '취향' in r['bar'] and r['bar']['취향'][0]>=90)
    print("\n== 축 칩 ==")
    for ax in ['state.accident','state.frame','history.usage','warranty.power','history.damage','history.rental']:
        T(f"axis {ax}", f"axis={ax}&bucket=1")
    print("\n== target / status ==")
    T("target G80_25T","target=G80_25T", lambda r: r['model']=='G80_25T')
    T("status active","status=active")
    json.dump(RES, open('probe/filters.json','w'), ensure_ascii=False)
    print("\n총",len(RES),"건 시험")

