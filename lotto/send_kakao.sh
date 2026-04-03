#!/bin/bash
# 카카오톡으로 메시지 전송 (유나 맥북 경유)
# 사용법: ./send_kakao.sh "채팅방이름" "메시지"

RECIPIENT="${1:-김태완(메인)}"
MESSAGE="$2"

if [ -z "$MESSAGE" ]; then
  echo "Usage: $0 <recipient> <message>"
  exit 1
fi

ssh -i ~/.ssh/id_ed25519 -o ConnectTimeout=10 taeoankim@192.168.50.192 \
  "export PATH=\$HOME/.local/bin:\$PATH; kmsg send \"$RECIPIENT\" \"$MESSAGE\"" 2>&1
