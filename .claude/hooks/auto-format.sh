#!/bin/bash
# PostToolUse Hook: 파일 저장 후 자동 포매팅
# AI가 로직에만 집중하고, 포매팅은 훅이 처리

FILE="$1"
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

EXT="${FILE##*.}"

case "$EXT" in
  py)
    /home/anaconda3/bin/black --quiet --line-length 120 "$FILE" 2>/dev/null
    ;;
  js|jsx|ts|tsx|json|css|md|html|yaml|yml)
    /root/.nvm/versions/node/v22.22.0/bin/prettier --write --log-level silent "$FILE" 2>/dev/null
    ;;
  sh|bash)
    /root/go/bin/shfmt -w -i 2 "$FILE" 2>/dev/null
    ;;
esac

exit 0
