#!/usr/bin/env bash
# OAuth 등록→PKCE 로그인→refresh→재시작 후 유지→revoke 전체 흐름을 로컬에서 검증한다.
# 실행 전: ./mcp/install.sh 로 venv를 만들어 두거나, PYTHON=/path/to/python 으로 지정한다.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PY="${PYTHON:-$REPO_DIR/venv/bin/python}"
[ -x "$PY" ] || PY="python3"

WORK="$(mktemp -d)"
DATA_DIR="$WORK/data"
PORT=8123
BASE="http://localhost:$PORT"
trap 'kill "$(cat "$WORK/pid" 2>/dev/null)" 2>/dev/null || true; rm -rf "$WORK"' EXIT
mkdir -p "$DATA_DIR"

start_server() {
  DATA_DIR="$DATA_DIR" PORT="$PORT" MCP_HOST=localhost MCP_USERNAME=admin MCP_PASSWORD=test \
    "$PY" "$SCRIPT_DIR/server.py" > "$WORK/server.log" 2>&1 &
  echo $! > "$WORK/pid"
  for _ in $(seq 1 30); do
    curl -sf "$BASE/.well-known/oauth-authorization-server" >/dev/null 2>&1 && return 0
    sleep 0.3
  done
  echo "FAIL: 서버가 기동하지 않음"; cat "$WORK/server.log"; exit 1
}
stop_server() {
  kill "$(cat "$WORK/pid")" 2>/dev/null || true
  wait "$(cat "$WORK/pid")" 2>/dev/null || true
}

echo "== 1) 서버 기동 =="
start_server

echo "== 2) dynamic client registration =="
REG=$(curl -s -X POST "$BASE/register" -H 'content-type: application/json' -d '{
  "client_name":"verify-client",
  "redirect_uris":["http://localhost:9999/cb"],
  "grant_types":["authorization_code","refresh_token"],
  "response_types":["code"],
  "token_endpoint_auth_method":"none"
}')
CLIENT_ID=$(echo "$REG" | python3 -c "import json,sys;print(json.load(sys.stdin)['client_id'])")

echo "== 3) PKCE code_verifier/challenge 생성 및 /authorize -> /login 리다이렉트 확인 =="
VERIFIER=$(openssl rand -base64 48 | tr -d '=+/\n' | cut -c1-64)
CHALLENGE=$(printf '%s' "$VERIFIER" | openssl dgst -sha256 -binary | openssl base64 -A | tr '+/' '-_' | tr -d '=')
STATE=$(openssl rand -hex 8)
AUTH_URL="$BASE/authorize?client_id=$CLIENT_ID&redirect_uri=http://localhost:9999/cb&response_type=code&code_challenge=$CHALLENGE&code_challenge_method=S256&state=$STATE&scope=mcp"
LOGIN_LOC=$(curl -s -o /dev/null -D - "$AUTH_URL" | grep -i '^location:' | tr -d '\r' | awk '{print $2}')
LOGIN_STATE=$(echo "$LOGIN_LOC" | sed -n 's/.*state=\([^&]*\).*/\1/p')

echo "== 4) /login/callback (username/password) → authorization code =="
CB_LOC=$(curl -s -o /dev/null -D - -X POST "$BASE/login/callback" \
  --data-urlencode "username=admin" --data-urlencode "password=test" --data-urlencode "state=$LOGIN_STATE" \
  | grep -i '^location:' | tr -d '\r' | awk '{print $2}')
CODE=$(echo "$CB_LOC" | sed -n 's/.*[?&]code=\([^&]*\).*/\1/p')

echo "== 5) authorization_code -> access_token + refresh_token =="
TOK=$(curl -s -X POST "$BASE/token" \
  --data-urlencode "grant_type=authorization_code" \
  --data-urlencode "code=$CODE" \
  --data-urlencode "redirect_uri=http://localhost:9999/cb" \
  --data-urlencode "client_id=$CLIENT_ID" \
  --data-urlencode "code_verifier=$VERIFIER")
ACCESS1=$(echo "$TOK" | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
REFRESH1=$(echo "$TOK" | python3 -c "import json,sys;print(json.load(sys.stdin)['refresh_token'])")

echo "== 6) refresh_token 으로 access_token 갱신 (재로그인 없이) =="
TOK2=$(curl -s -X POST "$BASE/token" \
  --data-urlencode "grant_type=refresh_token" \
  --data-urlencode "refresh_token=$REFRESH1" \
  --data-urlencode "client_id=$CLIENT_ID")
ACCESS2=$(echo "$TOK2" | python3 -c "import json,sys;print(json.load(sys.stdin)['access_token'])")
[ "$ACCESS1" != "$ACCESS2" ] || { echo "FAIL: refresh가 새 access_token을 발급하지 않음"; exit 1; }
echo "PASS: refresh_token으로 새 access_token 발급됨"

echo "== 7) oauth-state.json 영속화 확인 =="
python3 -c "
import json
d = json.load(open('$DATA_DIR/oauth-state.json'))
assert len(d['clients']) == 1 and len(d['refresh_tokens']) == 1
print('PASS: clients/refresh_tokens 저장됨')
"

echo "== 8) 서버 강제 종료 후 재기동, 재로그인 없이 refresh 가능한지 확인 =="
stop_server
start_server
TOK3=$(curl -s -X POST "$BASE/token" \
  --data-urlencode "grant_type=refresh_token" \
  --data-urlencode "refresh_token=$REFRESH1" \
  --data-urlencode "client_id=$CLIENT_ID")
ACCESS3=$(echo "$TOK3" | python3 -c "import json,sys;print(json.load(sys.stdin).get('access_token',''))")
[ -n "$ACCESS3" ] || { echo "FAIL: 재시작 후 refresh 실패: $TOK3"; exit 1; }
echo "PASS: 재시작 후에도 재로그인 없이 access_token 갱신됨"

echo "== 9) /revoke 로 refresh_token 무효화 확인 =="
curl -s -X POST "$BASE/revoke" \
  --data-urlencode "token=$REFRESH1" --data-urlencode "client_id=$CLIENT_ID" --data-urlencode "client_secret=" \
  >/dev/null
TOK4=$(curl -s -X POST "$BASE/token" \
  --data-urlencode "grant_type=refresh_token" \
  --data-urlencode "refresh_token=$REFRESH1" \
  --data-urlencode "client_id=$CLIENT_ID")
echo "$TOK4" | grep -q '"error"' || { echo "FAIL: revoke 후에도 refresh_token이 동작함: $TOK4"; exit 1; }
echo "PASS: revoke 후 refresh_token 거부됨"

stop_server
echo "== 모든 검증 통과 =="
