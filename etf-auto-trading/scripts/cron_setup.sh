#!/bin/bash
# ETF 자동매매 시스템 Cron 작업 설정 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 프로젝트 루트 디렉토리
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 ETF 자동매매 시스템 Cron 설정${NC}"
echo "========================================"

# 현재 crontab 백업
echo -e "${YELLOW}📁 현재 crontab 백업 중...${NC}"
crontab -l > "${PROJECT_DIR}/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "기존 crontab 없음"

# Python 경로 확인
PYTHON_PATH=$(which python3)
echo -e "${BLUE}🐍 Python 경로: ${PYTHON_PATH}${NC}"

# 프로젝트 경로 확인
echo -e "${BLUE}📁 프로젝트 경로: ${PROJECT_DIR}${NC}"

# 로그 디렉토리 생성
mkdir -p "${PROJECT_DIR}/logs"
mkdir -p "${PROJECT_DIR}/logs/cron"

# Cron 작업 정의
echo -e "${YELLOW}⏰ Cron 작업 추가 중...${NC}"

# 임시 cron 파일 생성
TEMP_CRON="${PROJECT_DIR}/temp_crontab.txt"

# 기존 crontab 내용 가져오기
crontab -l > "${TEMP_CRON}" 2>/dev/null || touch "${TEMP_CRON}"

# ETF 시스템 관련 기존 작업 제거 (중복 방지)
sed -i '/# ETF Auto-Trading System/d' "${TEMP_CRON}"
sed -i '/etf_collector/d' "${TEMP_CRON}"

# 새로운 cron 작업 추가
cat >> "${TEMP_CRON}" << EOF

# ETF Auto-Trading System - 자동 생성됨 $(date)
# =================================================

# 실시간 데이터 수집 (평일 장중 10분마다)
*/10 9-15 * * 1-5 cd "${PROJECT_DIR}" && ${PYTHON_PATH} kis_real_collector.py >> logs/cron/realtime.log 2>&1

# 기술적 지표 계산 (평일 30분마다)  
*/30 * * * 1-5 cd "${PROJECT_DIR}" && ${PYTHON_PATH} technical_analyzer.py >> logs/cron/technical.log 2>&1

# 매매 신호 생성 (평일 1시간마다)
0 * * * 1-5 cd "${PROJECT_DIR}" && ${PYTHON_PATH} trading_signals.py >> logs/cron/signals.log 2>&1

# 일일 분석 리포트 (평일 오후 6시)
0 18 * * 1-5 cd "${PROJECT_DIR}" && ${PYTHON_PATH} etf_analysis.py >> logs/cron/analysis.log 2>&1

# 주간 데이터 백업 (일요일 오전 2시)
0 2 * * 0 cd "${PROJECT_DIR}" && bash scripts/backup_data.sh >> logs/cron/backup.log 2>&1

# 월간 성과 리포트 (매월 1일 오전 9시)
0 9 1 * * cd "${PROJECT_DIR}" && ${PYTHON_PATH} monthly_report.py >> logs/cron/monthly.log 2>&1

EOF

# 새로운 crontab 적용
crontab "${TEMP_CRON}"
rm "${TEMP_CRON}"

echo -e "${GREEN}✅ Cron 작업 설정 완료!${NC}"
echo ""

# 설정된 cron 작업 확인
echo -e "${BLUE}📋 설정된 Cron 작업:${NC}"
echo "----------------------------------------"
crontab -l | grep -A 15 "ETF Auto-Trading System"

echo ""
echo -e "${YELLOW}⚠️  중요 사항:${NC}"
echo "1. 실시간 데이터 수집은 한투 API 키가 필요합니다"
echo "2. 환경변수를 ~/.bashrc 또는 cron 환경에 설정하세요:"
echo "   export KIS_APP_KEY='your_key'"
echo "   export KIS_APP_SECRET='your_secret'"
echo "   export KIS_ACCOUNT_NO='your_account'"
echo ""
echo "3. 로그 파일 위치: ${PROJECT_DIR}/logs/cron/"
echo "4. 백업 해제: crontab -r (주의!)"
echo "5. 수동 실행 테스트:"
echo "   cd ${PROJECT_DIR} && python3 trading_signals.py"

echo ""
echo -e "${GREEN}🎯 자동화 설정 완료! 이제 시스템이 자동으로 동작합니다.${NC}"

# 환경변수 확인
echo ""
echo -e "${BLUE}🔍 환경변수 확인:${NC}"
if [[ -n "$KIS_APP_KEY" ]]; then
    echo -e "  KIS_APP_KEY: ${GREEN}설정됨${NC}"
else
    echo -e "  KIS_APP_KEY: ${RED}미설정${NC} (실시간 데이터 수집 불가)"
fi

if [[ -n "$KIS_APP_SECRET" ]]; then
    echo -e "  KIS_APP_SECRET: ${GREEN}설정됨${NC}"
else
    echo -e "  KIS_APP_SECRET: ${RED}미설정${NC} (실시간 데이터 수집 불가)"
fi

# 디스크 용량 확인
echo ""
echo -e "${BLUE}💽 디스크 용량 확인:${NC}"
df -h "${PROJECT_DIR}" | tail -1

# 네트워크 연결 테스트 (선택사항)
echo ""
echo -e "${BLUE}🌐 네트워크 연결 테스트:${NC}"
if ping -c 1 openapi.koreainvestment.com > /dev/null 2>&1; then
    echo -e "  한투 API 서버: ${GREEN}연결 가능${NC}"
else
    echo -e "  한투 API 서버: ${YELLOW}연결 확인 필요${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✨ ETF 자동매매 시스템이 준비되었습니다!${NC}"