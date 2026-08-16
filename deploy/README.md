# 배포 — 앞단 HTTPS (14장 1584줄)

**2026-08-16 세움.  실제로 도는 것이 여기 있다.**

```
브라우저 ──https──▶ Caddy :443 ──http──▶ CarWatch 127.0.0.1:8765
                    :80 은 308 로 https 로 보낸다
```

```
주소   https://43.201.16.78.sslip.io
근거   Let's Encrypt 는 IP 에 인증서를 주지 않는다.
      sslip.io 는 43.201.16.78.sslip.io → 43.201.16.78 로 해석되는 실제 도메인이다.
      진짜 도메인을 사면 Caddyfile 의 첫 줄만 바꾸면 된다
```

## 파일

| 여기 | 놓는 곳 |
|---|---|
| `Caddyfile` | `/etc/caddy/Caddyfile` |
| `caddy.service` | `/etc/systemd/system/caddy.service` |
| `carwatch.service` | `/etc/systemd/system/carwatch.service` |

Caddy 는 copr 에 aarch64 패키지가 없어 **공식 바이너리**를 넣었다.

```bash
curl -fsSL -o /tmp/caddy.tar.gz \
  https://github.com/caddyserver/caddy/releases/download/v2.11.4/caddy_2.11.4_linux_arm64.tar.gz
tar xzf /tmp/caddy.tar.gz caddy && sudo install -m 0755 caddy /usr/local/bin/caddy
sudo useradd --system --home /var/lib/caddy --create-home --shell /usr/sbin/nologin caddy
```

## ★ 앱은 127.0.0.1 만 듣는다

```
ExecStart=/usr/bin/python3.11 run.py web --host 127.0.0.1 --port 8765
```

밖에서 `http://43.201.16.78:8765` 는 **연결되지 않는다.**
보안 그룹을 건드리지 않고도 닫힌 것과 같다 — 앱이 아예 그 주소로 안 듣는다.

```
금지   --host 0.0.0.0 으로 되돌리는 것.  TLS 를 우회해 평문으로 들어올 수 있다
금지   run.py web 을 8765 로 따로 띄우는 것.  서비스가 포트를 못 잡는다
시험   포트를 따로 쓴다 — run.py web --port 8799
```

## 쿠키 Secure

앱은 평문으로 듣기 때문에 **「지금 HTTPS 인가」를 스스로 모른다.**
Caddy 가 붙이는 `X-Forwarded-Proto` 로만 안다 (`web/session.py is_https`).

```
실측 2026-08-16
  https 로 들어옴  →  X-Forwarded-Proto='https'  →  쿠키에 Secure
  머리글이 없으면   →  안 붙인다 (평문인데 붙이면 쿠키가 아예 안 간다)
```

## 확인

```bash
systemctl is-active carwatch caddy
ss -tln | grep -E ':(80|443|8765)\b'      # 8765 는 127.0.0.1 이어야 한다
curl -sI https://43.201.16.78.sslip.io/listings | head -3
curl -so /dev/null -w '%{http_code}\n' http://43.201.16.78:8765/listings   # 000 이어야 한다
```

## 인증서

Caddy 가 자동으로 받고 갱신한다. 손댈 것이 없다.

```
발급   2026-08-16 · Let's Encrypt · 43.201.16.78.sslip.io
갱신   Caddy 가 만료 전에 스스로 한다 (80 이 열려 있어야 한다)
★     보안 그룹에서 80 을 닫으면 갱신이 실패한다.  80 은 열어 둔다
```
