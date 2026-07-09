#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Python 가상환경 생성"
python3.11 -m venv "$REPO_DIR/venv-wiki"

echo "==> Python 패키지 설치"
"$REPO_DIR/venv-wiki/bin/pip" install -r "$SCRIPT_DIR/requirements.txt"

echo ""
echo "==> 데이터 디렉터리 생성"
mkdir -p "$SCRIPT_DIR/data"
echo "  $SCRIPT_DIR/data"

echo ""
echo "==> 환경변수 파일 설정"
ENV_FILE="$SCRIPT_DIR/jamong-wiki.env"
if [ ! -f "$ENV_FILE" ]; then
    cp "$SCRIPT_DIR/jamong-wiki.env.example" "$ENV_FILE"
    chmod 600 "$ENV_FILE"
    echo "  jamong-wiki.env 생성 완료. 실제 값으로 수정하세요:"
    echo "    nano $ENV_FILE"
else
    echo "  jamong-wiki.env 이미 존재, 건너뜀"
fi

echo ""
echo "==> systemd 서비스 등록"
SERVICE_SRC="$SCRIPT_DIR/jamong-wiki.service"
SERVICE_DST="/etc/systemd/system/jamong-wiki.service"

# 실제 경로로 치환 후 복사
sed "s|__REPO_DIR__|$REPO_DIR|g" "$SERVICE_SRC" > /tmp/jamong-wiki.service
sed -i "s|__VENV_DIR__|$REPO_DIR/venv-wiki|g" /tmp/jamong-wiki.service
sed -i "s|__ENV_FILE__|$ENV_FILE|g" /tmp/jamong-wiki.service

echo "  아래 명령을 root로 실행하세요:"
echo ""
echo "    cp /tmp/jamong-wiki.service $SERVICE_DST"
echo "    systemctl daemon-reload"
echo "    systemctl enable --now jamong-wiki"
echo ""
echo "Done."
