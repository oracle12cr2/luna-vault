#!/bin/bash
# PostToolUse Hook: 파일 저장 후 자동 포매팅
# AI가 로직에만 집중하고, 포매팅은 훅이 처리
# 크로스 플랫폼 (루나 서버 + 유나 맥북)

FILE="$1"
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

EXT="${FILE##*.}"

# 포매터 찾기 (절대경로 우선, 없으면 PATH에서 탐색)
find_cmd() {
  for p in "$@"; do
    [ -x "$p" ] && echo "$p" && return
  done
  which "$1" 2>/dev/null
}

case "$EXT" in
  py)
    BLACK=$(find_cmd /home/anaconda3/bin/black python3)
    if [ -n "$BLACK" ] && [[ "$BLACK" == *black* ]]; then
      "$BLACK" --quiet --line-length 120 "$FILE" 2>/dev/null
    else
      python3 -m black --quiet --line-length 120 "$FILE" 2>/dev/null
    fi
    ;;
  js|jsx|ts|tsx|json|css|md|html|yaml|yml)
    PRETTIER=$(find_cmd /root/.nvm/versions/node/v22.22.0/bin/prettier)
    [ -z "$PRETTIER" ] && PRETTIER=$(which prettier 2>/dev/null)
    [ -n "$PRETTIER" ] && "$PRETTIER" --write --log-level silent "$FILE" 2>/dev/null
    ;;
  sh|bash)
    SHFMT=$(find_cmd /root/go/bin/shfmt /opt/homebrew/bin/shfmt /usr/local/bin/shfmt)
    [ -z "$SHFMT" ] && SHFMT=$(which shfmt 2>/dev/null)
    [ -n "$SHFMT" ] && "$SHFMT" -w -i 2 "$FILE" 2>/dev/null
    ;;
esac

exit 0
