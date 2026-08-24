# 배포 — 앞단 HTTPS (14장 1584줄)

> ★ 배포 주소는 ★ `config/deploy.json` 이 정본이다 (★ 개정 684).  ★ 문서에 박지 않는다
> ★ `{base_url}` · `{public_ip}` 는 ★ 그 파일의 값이다


**2026-08-16 세움.  실제로 도는 것이 여기 있다.**

```
브라우저 ──https──▶ Caddy :443 ──http──▶ CarWatch 127.0.0.1:8765
                    :80 은 308 로 https 로 보낸다
```

```
주소   {base_url}
근거   Let's Encrypt 는 IP 에 인증서를 주지 않는다.
      sslip.io 는 ★ `{public_ip}.sslip.io` → `{public_ip}` 로 해석되는 실제 도메인이다.
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

밖에서 `http://{public_ip}:8765` 는 **연결되지 않는다.**
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
curl -sI {base_url}/listings | head -3
curl -so /dev/null -w '%{http_code}\n' http://{public_ip}:8765/listings   # 000 이어야 한다
```

## 인증서

Caddy 가 자동으로 받고 갱신한다. 손댈 것이 없다.

```
발급   2026-08-16 · Let's Encrypt · 43.201.16.78.sslip.io
갱신   Caddy 가 만료 전에 스스로 한다 (80 이 열려 있어야 한다)
★     보안 그룹에서 80 을 닫으면 갱신이 실패한다.  80 은 열어 둔다
```

---

# ★★★ 주소가 바뀌면 — ★ 되살리는 법 (마스터 결정 08-24 「나중에」 · 개정 683)

```
★★ 마스터 결정 — ★ **탄력적 IP · 감시 · SSM 셋은 ★ 「나중에」**
★ ★ 그러므로 ★ **지금 위험을 안고 간다.**  ★ 되살리는 법을 ★ 여기 적어 둔다
```

## ★ 지금 위험

```
★ 인스턴스를 ★ 껐다 켜면 ★ `{public_ip}` 이 ★ **바뀐다**
★ ★ 그 주소가 ★ 저장소 ★ **69곳**에 박혀 있다 (★ 실측 08-24)
   `deploy/README.md` · `CLAUDE.md` · 작업기록 여럿 · 검사
★ ★ 그러면 ★ 배포 확인 · 검사 · 인수인계가 ★ 한꺼번에 죽는다
★ ★ 그리고 ★ **감시가 없어** ★ 죽은 줄도 모른다 — ★ 마스터가 화면을 여셔야 안다
```

## ★★ 바뀌었을 때 — ★ 이 순서로 되살린다

```
① ★ AWS 콘솔에서 ★ 새 공인 IP 를 확인한다 (인스턴스 `i-0aa4fe11f2d668103`)
② ★ 새 주소로 ★ 두드려 본다 — `curl -sk -o /dev/null -w '%{http_code}' https://{새IP}.sslip.io/`
   ★ ★ 200 이 아니면 ★ 서비스가 안 뜬 것이다 — ★ 개발측에 알린다
③ ★ 저장소에서 ★ 옛 주소를 ★ **한 번에 바꾼다** —
   `grep -rl '{public_ip}' --include='*.md' --include='*.json' --include='*.py' .`
   ★ ★ **작업기록(`outputs/`)은 ★ 바꾸지 않는다** — ★ 그때 그 주소가 맞다
   ★ ★ 바꾸는 곳 — `deploy/README.md` · `CLAUDE.md` · 검사 · 규격
④ ★ `docs/guide/08_인수인계.md` 와 ★ 명령서 0장의 ★ 확인 명령을 고친다
⑤ ★ 검사를 돌려 ★ 다 통과하는지 본다
```

## ★ 되살리는 값을 ★ 한 곳에 둔다

| 무엇 | 값 |
|---|---|
| 지역 | `ap-northeast-2` (서울) |
| 인스턴스 | `i-0aa4fe11f2d668103` |
| 지금 주소 | `{public_ip}` (★ 실측 08-24) |
| 접속 | `{base_url}` |
| 앞단 | Caddy → ★ 안쪽 `8765` |
| 사용자 | `ec2-user` · 작업 폴더 `/home/ec2-user/v2` |
| 서비스 | `carwatch.service` · `carwatch-daily.timer` (13:00) |
| 계정 | `master` |

```
★★ ★ 이 표를 ★ **주소가 바뀌면 ★ 여기부터 고친다**
필수  ★ 마스터께서 ★ 「나중에」를 ★ **지금**으로 바꾸시면 ★ 탄력적 IP 를 먼저 붙인다
      ★ ★ 그러면 ★ 이 절이 ★ 필요 없어진다
★ 밀린일 ★ 94(감시) · 95(SSM) · 96(탄력적 IP) 는 ★ 「대」로 살려 둔다
```
