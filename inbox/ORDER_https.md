# HTTPS 로 바꾼다 — 마스터 지시

**2026-08-16**

---

# 1. 규격은 이미 있습니다

```
14장 1584줄
3  HTTPS 는 앞단(리버스 프록시)에 맡긴다.  자체 TLS 를 두지 않는다
```

**앱은 그대로 두고 앞에 Caddy 를 세웁니다.**

---

# 2. ★ 도메인이 필요합니다

```
Let's Encrypt 는 IP 에 인증서를 주지 않습니다
43.201.16.78 로는 못 받습니다
```

## 무료로 되는 길 — `sslip.io`

```
43.201.16.78.sslip.io   →  자동으로 43.201.16.78 로 해석됩니다
```

```
★ 실제 도메인이라 Let's Encrypt 인증서를 받습니다
★ 가입 없음 · 무료 · 바로 됨
★ 나중에 진짜 도메인을 사면 Caddyfile 한 줄만 바꾸면 됩니다
```

---

# 3. 할 일

## ① 보안 그룹에 443 열기

**★ 이건 마스터가 콘솔에서 하십니다.**

```
carwatch-sg → 인바운드 규칙 편집 → 규칙 추가
  유형   HTTPS
  포트   443
  소스   Anywhere-IPv4
```

**80 도 열어야 합니다 (인증서 발급에 씁니다).**

## ② Caddy 설치

```bash
sudo dnf install -y 'dnf-command(copr)'
sudo dnf copr enable -y @caddy/caddy
sudo dnf install -y caddy
```

**안 되면 바이너리로.**

```bash
curl -fsSL -o /tmp/caddy.tar.gz \
  "https://github.com/caddyserver/caddy/releases/latest/download/caddy_linux_arm64.tar.gz"
```

**★ 실제 파일명은 릴리스에서 확인하십시오.**

## ③ Caddyfile

```
43.201.16.78.sslip.io {
    reverse_proxy 127.0.0.1:8765
    encode gzip
}
```

```
필수   앱은 127.0.0.1 만 듣게 바꾼다
       지금 0.0.0.0:8765 로 밖에 열려 있다
       Caddy 를 세운 뒤에는 밖에서 직접 못 들어오게 한다
필수   carwatch.service 의 --host 를 127.0.0.1 로
필수   보안 그룹에서 8765 를 닫는다
```

## ④ 앱 설정

```
필수   config/web.json 의 base_url 을 https 로
필수   쿠키에 Secure 를 붙인다 (882줄 — HTTPS 일 때)
       ★ 지금 HTTP 라 안 붙어 있을 것입니다
확인   HTTPS 인지 어떻게 아는가
      Caddy 가 X-Forwarded-Proto: https 를 보냅니다
      그것을 읽어 Secure 를 결정하십시오
```

## ⑤ 확인

```bash
curl -sI https://43.201.16.78.sslip.io/ | head -3
curl -sI http://43.201.16.78:8765/ 2>&1 | head -2   # 밖에서 막혔는지
```

---

# 4. 순서

```
1  마스터가 보안 그룹에 80 · 443 을 엽니다
2  Caddy 설치 · Caddyfile
3  앱을 127.0.0.1 로
4  쿠키 Secure
5  8765 를 보안 그룹에서 닫습니다  ← 마스터
6  확인
```

**★ 3번을 먼저 하면 화면이 안 열립니다. 순서를 지키십시오.**

---

# 5. 그리고

```
필수   엔카 이미지가 https 인지 확인하십시오
       https://ci.encar.com — 이미 https 면 됩니다
       http 면 브라우저가 「혼합 콘텐츠」로 막습니다
필수   엔카 원문 링크는 http 여도 됩니다.  새 탭이라 상관없습니다
       다만 https 로 열리면 그게 낫습니다
```

**★ 이게 실제 문제가 될 수 있습니다. 먼저 확인하십시오.**
