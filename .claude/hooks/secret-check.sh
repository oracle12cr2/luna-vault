#!/bin/bash
# PreToolUse Hook: 파일 쓰기 전 시크릿 유출 체크
# API키, 비밀번호 패턴 감지 시 경고

FILE="$1"
[ -z "$FILE" ] && exit 0
[ ! -f "$FILE" ] && exit 0

# .gitignore에 있는 파일은 스킵
EXT="${FILE##*.}"
[[ "$EXT" == "log" || "$EXT" == "json" ]] && exit 0

# 시크릿 패턴 체크
PATTERNS=(
  'sk-ant-[a-zA-Z0-9]'
  'sk-[a-zA-Z0-9]{20,}'
  'AKIA[0-9A-Z]{16}'
  'ghp_[a-zA-Z0-9]{36}'
  'password\s*=\s*["\x27][^"\x27]{8,}'
)

for PATTERN in "${PATTERNS[@]}"; do
  if grep -qP "$PATTERN" "$FILE" 2>/dev/null; then
    echo "⚠️ SECRET DETECTED in $FILE (pattern: $PATTERN)" >&2
    # 경고만 하고 차단은 안 함 (exit 1 하면 차단)
    exit 0
  fi
done

exit 0
