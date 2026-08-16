#!/usr/bin/env bash
# CarWatch v2 launcher (mac / Linux).
# 문구는 tools/menu.py 한 곳에 있다 — 셸과 배치가 갈리지 않게 한다.
set -u
cd "$(dirname "$0")"
exec "${PY:-python3}" tools/menu.py "$@"
