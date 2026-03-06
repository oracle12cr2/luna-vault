#!/bin/bash
# OpenClaw 언어 옵션에서 English만 남기고 제거하는 스크립트

ASSETS_DIR="/root/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/dist/control-ui/assets"
JS_FILE="$ASSETS_DIR/index-CJS46cAv.js"

if [ ! -f "$JS_FILE" ]; then
    echo "❌ 파일을 찾을 수 없습니다: $JS_FILE"
    exit 1
fi

echo "🔍 현재 언어 설정 확인 중..."
CURRENT=$(grep -o 'rd=\[[^]]*\]' "$JS_FILE" 2>/dev/null)
echo "현재: $CURRENT"

if [[ "$CURRENT" == 'rd=["en"]' ]]; then
    echo "✅ 이미 English만 설정되어 있습니다."
    exit 0
fi

echo "💾 백업 생성 중..."
cp "$JS_FILE" "$JS_FILE.backup.$(date +%Y%m%d_%H%M%S)"

echo "✏️  언어 목록 수정 중..."
sed -i 's/rd=\["en","zh-CN","zh-TW","pt-BR"\]/rd=["en"]/g' "$JS_FILE"

RESULT=$(grep -o 'rd=\[[^]]*\]' "$JS_FILE" 2>/dev/null)
echo "수정 후: $RESULT"

if [[ "$RESULT" == 'rd=["en"]' ]]; then
    echo "✅ 성공적으로 수정되었습니다!"
    echo "🌐 브라우저에서 Ctrl+F5로 새로고침 하세요."
else
    echo "❌ 수정에 실패했습니다."
    exit 1
fi
