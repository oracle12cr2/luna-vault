#!/bin/bash
# 코스피 ETF 리포트 생성 및 발송

REPORT_FILE="/tmp/etf_report_$(date +%Y%m%d).txt"
DATE=$(date +"%Y년 %m월 %d일 %H:%M")

# ETF 5종 코드
ETFS="069500 102110 091160 305720 226490"

cat > "$REPORT_FILE" << EOF
========================================
  코스피 ETF 일간 분석 리포트
  ${DATE}
========================================

■ 선정 기준: 거래량·규모 상위, 섹터 다양성

EOF

for code in $ETFS; do
  data=$(curl -s "https://polling.finance.naver.com/api/realtime/domestic/stock/$code" 2>/dev/null)
  name=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['stockName'])" 2>/dev/null)
  price=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['closePrice'])" 2>/dev/null)
  change=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['compareToPreviousClosePrice'])" 2>/dev/null)
  rate=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['fluctuationsRatio'])" 2>/dev/null)
  vol=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['accumulatedTradingVolume'])" 2>/dev/null)
  high=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['highPrice'])" 2>/dev/null)
  low=$(echo "$data" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['datas'][0]['lowPrice'])" 2>/dev/null)

  if [ "$rate" != "" ]; then
    sign=""
    echo "$rate" | grep -q "^-" || sign="+"
  fi

  cat >> "$REPORT_FILE" << EOF
──────────────────────────────────
  ${name} (${code})
──────────────────────────────────
  현재가: ${price}원 (${sign}${rate}%)
  전일비: ${change}원
  고가/저가: ${high} / ${low}
  거래량: ${vol}주
EOF

  case $code in
    069500) cat >> "$REPORT_FILE" << 'EOF'
  특징: 코스피200 대표 ETF, 시장 전체 흐름 파악
  용도: 시장 방향성 베팅, 적립식 장기투자
EOF
    ;;
    102110) cat >> "$REPORT_FILE" << 'EOF'
  특징: TIGER 운용사의 코스피200 추종
  용도: KODEX 200 대비 보수 비교 후 선택
EOF
    ;;
    091160) cat >> "$REPORT_FILE" << 'EOF'
  특징: 반도체 섹터 집중 (삼성전자, SK하이닉스)
  용도: 반도체 업황 회복기 집중 투자
EOF
    ;;
    305720) cat >> "$REPORT_FILE" << 'EOF'
  특징: 2차전지 관련주 (LG에너지솔루션, 삼성SDI 등)
  용도: 전기차·배터리 성장 테마 투자
EOF
    ;;
    226490) cat >> "$REPORT_FILE" << 'EOF'
  특징: 코스피 전체 시장 추종 (200보다 넓은 범위)
  용도: 보수적 시장 전체 투자
EOF
    ;;
  esac

  echo "" >> "$REPORT_FILE"
done

cat >> "$REPORT_FILE" << EOF
========================================
  ※ 본 리포트는 참고용이며 투자 판단의
    책임은 본인에게 있습니다.
  ※ 데이터 출처: 네이버 금융
  ※ 생성: 루나 🌙
========================================
EOF

# 메일 발송 (python3 + naver SMTP)
python3 << PYEOF
import smtplib
from email.mime.text import MIMEText

with open("$REPORT_FILE", "r") as f:
    body = f.read()

msg = MIMEText(body, "plain", "utf-8")
msg["Subject"] = "[ETF 리포트] 코스피 ETF 일간 분석 - $(date +%Y.%m.%d)"
msg["From"] = "kto2004@naver.com"
msg["To"] = "kto2004@naver.com"

try:
    server = smtplib.SMTP("smtp.naver.com", 587)
    server.starttls()
    server.login("kto2004", "rlaxodhks")
    server.send_message(msg)
    server.quit()
    print("메일 발송 성공!")
except Exception as e:
    print(f"메일 발송 실패: {e}")
PYEOF

echo "리포트: $REPORT_FILE"
