import re, json, sys, html


def _get(path):
    sys.path.insert(0, 'probe')
    from p0 import get as g
    return g(path)

ROW = re.compile(r'<div class="row" data-peek(.*?)\n</div>\n\n', re.S)
def parse_rows(b):
    out=[]
    # split on row starts
    parts = b.split('<div class="row"')[1:]
    for p in parts:
        d={}
        m=re.search(r'data-href="/detail/(\d+)"', p);  d['id']=int(m.group(1)) if m else None
        m=re.search(r'data-buy="([\d,]+)만"', p);      d['buy']=int(m.group(1).replace(',',''))*10000 if m else None
        m=re.search(r'class="gr ([A-Z_]+) grade', p);  d['grade']=m.group(1) if m else None
        if not d['grade']:
            m=re.search(r'class="gr ([A-Z_]+)"', p);   d['grade']=m.group(1) if m else None
        m=re.search(r'이 매물은 ([\d.]+) / ([\d.]+) 점 \(([\d.]+)%\)', p)
        if m: d['pt'],d['den'],d['pct']=float(m.group(1)),float(m.group(2)),float(m.group(3))
        else: d['pt']=d['den']=d['pct']=None
        m=re.search(r'<small>(\d+)위</small>', p);     d['rank']=int(m.group(1)) if m else None
        bars=re.findall(r'title="(차량|값|보증|취향) ([\d.]+) / ([\d.]+)점"', p)
        d['bar']={k:(float(a),float(bq)) for k,a,bq in bars}
        m=re.search(r'title="판정 근거와 상세를 봅니다">([^<]+)</a>', p); d['model']=m.group(1).strip() if m else None
        m=re.search(r'<div class="trim"[^>]*>([^<]*)</div>', p); d['trim']=' '.join(html.unescape(m.group(1)).split()) if m else None
        m=re.search(r'year_from=([\d-]+)"', p);        d['year']=m.group(1) if m else None
        m=re.search(r'km_max=\d+"[^>]*>([\d,]+)km</a>', p); d['km']=int(m.group(1).replace(',','')) if m else None
        m=re.search(r'price_max=(\d+)"[^>]*title="이 가격대 이하만 봅니다">([\d,]+)만</a>', p)
        d['price']=int(m.group(2).replace(',',''))*10000 if m else None
        d['price_link']=int(m.group(1)) if m else None
        m=re.search(r'monthly_max=(\d+)"[^>]*>([\d,]+)만</a>', p)
        d['monthly']=int(m.group(2).replace(',',''))*10000 if m else None
        d['monthly_link']=int(m.group(1)) if m else None
        m=re.search(r'<span class="swatch"[^>]*></span>([^/<]*)/\s*([^·<]*)', p)
        if m: d['cext'],d['cint']=m.group(1).strip(), m.group(2).strip()
        m=re.search(r'/dealers\?q=([^"]+)"', p); d['dealer']=html.unescape(m.group(1)) if m else None
        m=re.search(r'carid=(\d+)', p); d['carid']=m.group(1) if m else None
        m=re.search(r'<u>옵션가</u>\s*<b><a[^>]*>\s*(\d+)종\s*([\d,]*)만?', p)
        d['opt_n']=int(m.group(1)) if m else None
        d['opt_won']=int(m.group(2).replace(',',''))*10000 if (m and m.group(2)) else None
        m=re.search(r'<u>경과</u>\s*<b>(\d+)일</b>', p); d['days']=int(m.group(1)) if m else None
        m=re.search(r'<u>시세차</u>\s*<b class="[^"]*"[^>]*>\s*([-\d.]+)%', p, re.S); d['gap']=float(m.group(1)) if m else None
        m=re.search(r'시세 ([\d,]+)만', p); d['mkt']=int(m.group(1).replace(',',''))*10000 if m else None
        d['axes']=dict(re.findall(r'>(사고|골격|용도|보증)<b>([O\-?])</b>', p))
        d['site']=('엔카' if '>엔카</span>' in p else None)
        out.append(d)
    return out

def head(b):
    m=re.search(r'<h1>매물\s*<small>([\d,]+)건 중 ([\d,]+)건 ·\s*([\d,]+)쪽 중 ([\d,]+)쪽', b)
    return tuple(int(x.replace(',','')) for x in m.groups()) if m else None

if __name__=="__main__":
    allrows=[]; meta=None
    for pg in range(1,64):
        s,t,b=_get(f"/listings?page={pg}")
        if s!=200: print("FAIL",pg,s); continue
        h=head(b); rows=parse_rows(b)
        if pg==1: meta=h
        allrows+=rows
        if pg%10==0 or pg==1: print(pg, h, len(rows), f"{t:.1f}s", flush=True)
    json.dump(allrows, open('probe/census.json','w'))
    print("TOTAL rows", len(allrows), "meta", meta)
