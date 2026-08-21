import sys,re,html,json
sys.path.insert(0,'probe'); from p0 import get; from p1_census import parse_rows, head
print("=== 정렬 8종 — 앞 5건 ===")
for o in ['rank','grade','price','price_desc','mileage','year','new','dom']:
    s,t,b=get(f"/listings?order={o}")
    R=parse_rows(b)
    print(f"  {o:10s} " + " | ".join(f"{r['grade']}·{r['price']//10000}만" for r in R[:5]))
print("\n=== 예산 걸고 정렬했을 때 첫 5건 ===")
for o in ['rank','grade','price']:
    s,t,b=get(f"/listings?price_max=3000&order={o}")
    R=parse_rows(b)
    print(f"  price_max=3000&order={o:6s} " + " | ".join(f"{r['grade']}·{r['price']//10000}만·{r['model']}" for r in R[:5]))
print("\n=== 현황 수집·확인필요 절 ===")
s,t,b=get("/")
t2=re.sub(r'<script.*?</script>','',b,flags=re.S); t2=re.sub(r'<style.*?</style>','',t2,flags=re.S)
t2=re.sub(r'<[^>]+>','\n',t2); t2=html.unescape(t2)
L=[' '.join(x.split()) for x in t2.split('\n')]; L=[x for x in L if x]
i=[k for k,x in enumerate(L) if '확인 필요' in x][0]
print('\n'.join(L[i:i+6]))
j=[k for k,x in enumerate(L) if x.startswith('수집')][0]
print('\n'.join(L[j:j+45]))
