import urllib.request, ssl, time, re, json
ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
B="https://43.201.16.78.sslip.io"
def get(path, timeout=90):
    t=time.time()
    try:
        r=urllib.request.urlopen(B+path, context=ctx, timeout=timeout)
        b=r.read().decode('utf-8','replace'); return r.status, time.time()-t, b
    except urllib.error.HTTPError as e:
        return e.code, time.time()-t, e.read().decode('utf-8','replace')
    except Exception as e:
        return -1, time.time()-t, str(e)
if __name__=="__main__":
    for p in ["/","/listings","/detail/7781","/recommend","/why/7781","/notready","/watch","/login","/dealers?q=%EB%B9%84%EC%97%A0%EC%9E%90%EB%8F%99%EC%B0%A8","/compare?ids=7781","/market","/dashboard"]:
        s,t,b=get(p)
        f=re.search(r'<footer class="ver">(.*?)</footer>', b, re.S)
        ver=' '.join(re.sub(r'<[^>]+>',' ',f.group(1)).split()) if f else '-'
        print(f"{p:55s} {s:5d} {t:6.2f}s {len(b)//1024:5d}KB  {ver}")
