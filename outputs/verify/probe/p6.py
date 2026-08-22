import sys,re,html

if __name__ == "__main__":
    sys.path.insert(0,'probe'); from p0 import get
    s,t,b=get("/why/7781")
    t2=re.sub(r'<script.*?</script>','',b,flags=re.S); t2=re.sub(r'<style.*?</style>','',t2,flags=re.S)
    t2=re.sub(r'<[^>]+>','\n',t2); t2=html.unescape(t2)
    L=[' '.join(x.split()) for x in t2.split('\n')]; L=[x for x in L if x]
    i=L.index('축')
    print('\n'.join(L[i:i+120]))

