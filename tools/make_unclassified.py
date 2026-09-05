"""미분류(out_of_scope) 를 갈래로 묶어 마스터께 여쭐 표를 만든다 (09-05).

마스터 지시 — 「내가 아는 상품 코드지만 마스터가 허용하지 않은 것과,
허용한 것 이외에 공백이 있는 것들을 분류해서 「이거 어떻게 할까요」 물어라」

낸 것: outputs/UNCLASSIFIED.md — 갈래마다 건수·사이트·본보기 이름.
마스터는 각 줄에 「받는다 / 안 받는다」만 적으시면 된다.
"""
import html
import json
import os
import re
import ssl
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "UNCLASSIFIED.md")


def build(base_url: str, name: str = "admin", secret: str = "12345678") -> str:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx),
                                     urllib.request.HTTPCookieProcessor(CookieJar()))

    def get(p):
        with op.open(base_url + p, timeout=60) as r:
            return r.read().decode("utf-8", "replace")

    def csrf(t):
        m = re.search(r'name="csrf" value="([^"]+)"', t)
        return m.group(1) if m else ""

    op.open(base_url + "/login", timeout=60)
    op.open(urllib.request.Request(
        base_url + "/login",
        data=urllib.parse.urlencode({"name": name, "secret": secret,
                                     "csrf": csrf(get("/login"))}).encode()),
        timeout=60)

    def rows(sql):
        tok = csrf(get("/admin/query"))
        with op.open(urllib.request.Request(
                base_url + "/admin/query",
                data=urllib.parse.urlencode({"sql": sql, "csrf": tok}).encode()),
                timeout=180) as r:
            body = r.read().decode("utf-8", "replace")
        t = html.unescape(re.sub(r"<[^>]+>", "\n", body))
        out = [x.strip() for x in t.split("\n") if x.strip()]
        if "탭 구분 — 표에 그대로 붙습니다" not in out:
            return []
        j = out.index("탭 구분 — 표에 그대로 붙습니다")
        got = []
        for ln in out[j + 1:]:
            if "\t" not in ln:
                break
            got.append(ln.split("\t"))
        return got[1:] if got else []

    got = rows(
        "SELECT site_model_group, site, COUNT(*) AS n FROM core_listing "
        "WHERE status='out_of_scope' AND site_model_group IS NOT NULL "
        "GROUP BY site_model_group, site ORDER BY 3 DESC LIMIT 80")
    lines = [
        "# 미분류 — 마스터께 여쭐 것",
        "",
        "`python3 -c \"from tools.make_unclassified import build; build('배포주소')\"` 가 만든다.",
        "",
        "받고 있는데 우리 차종에 안 들어간 것들이다.",
        "각 줄에 **받는다 / 안 받는다** 만 적어 주시면 `config/targets.json` 에 반영한다.",
        "",
        "| 갈래 | 사이트 | 건수 | 받는다 / 안 받는다 |",
        "|---|---|--:|---|",
    ]
    for r in got:
        if len(r) < 3:
            continue
        lines.append(f"| {r[0][:40]} | {r[1]} | {r[2]} | |")
    text = "\n".join(lines) + "\n"
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"미분류 {len(got)}갈래 → {OUT}")
    return OUT
