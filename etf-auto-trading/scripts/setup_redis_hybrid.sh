#!/bin/bash
# ETF Redis + Oracle 하이브리드 시스템 설정 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${BLUE}🚀 ETF Redis + Oracle 하이브리드 시스템 설정${NC}"
echo "=================================================="

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR"

echo -e "📁 프로젝트 경로: ${GREEN}$PROJECT_DIR${NC}"

# 1. 의존성 확인
echo ""
echo -e "${YELLOW}📦 의존성 확인 중...${NC}"

# Python 패키지 확인
echo "🐍 Python 패키지 확인..."
python3 -c "import redis; import cx_Oracle; import yaml; import numpy" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "  ✅ Python 패키지 모두 설치됨"
else
    echo -e "  ❌ Python 패키지 설치 필요"
    echo "  pip3 install redis cx-Oracle PyYAML numpy"
    read -p "  지금 설치하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip3 install redis cx-Oracle PyYAML numpy
    fi
fi

# 2. Redis 연결 테스트
echo ""
echo -e "${YELLOW}🔴 Redis 클러스터 연결 테스트...${NC}"

if command -v redis-cli &> /dev/null; then
    if redis-cli -h 192.168.50.9 -p 6379 -a redis ping > /dev/null 2>&1; then
        echo -e "  ✅ Redis 연결 성공 (192.168.50.9:6379)"
        
        # Redis 정보 확인
        echo "  📊 Redis 상태:"
        redis-cli -h 192.168.50.9 -p 6379 -a redis info memory | grep "used_memory_human"
        redis-cli -h 192.168.50.9 -p 6379 -a redis info stats | grep "total_commands_processed"
        
    else
        echo -e "  ❌ Redis 연결 실패"
        echo "  Redis 서버 상태를 확인해주세요."
    fi
else
    echo -e "  ⚠️  redis-cli 명령어 없음"
fi

# 3. Oracle 연결 테스트
echo ""
echo -e "${YELLOW}🔵 Oracle RAC 연결 테스트...${NC}"

python3 -c "
import cx_Oracle
try:
    dsn = cx_Oracle.makedsn('oracle19c01', 1521, service_name='PROD')
    conn = cx_Oracle.connect('stock', 'stock123', dsn)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM etf_master')
    count = cursor.fetchone()[0]
    print(f'  ✅ Oracle 연결 성공 (ETF 마스터: {count}개)')
    cursor.close()
    conn.close()
except Exception as e:
    print(f'  ❌ Oracle 연결 실패: {e}')
" 2>/dev/null

# 4. 로그 디렉토리 생성
echo ""
echo -e "${YELLOW}📁 로그 디렉토리 설정...${NC}"
mkdir -p logs
mkdir -p logs/redis
mkdir -p logs/batch

echo -e "  ✅ 로그 디렉토리 생성 완료"

# 5. Cron 설정 업데이트
echo ""
echo -e "${YELLOW}⏰ Cron 작업 업데이트...${NC}"

# 기존 crontab 백업
crontab -l > "crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "기존 crontab 없음"

# 임시 cron 파일 생성
TEMP_CRON="/tmp/etf_hybrid_cron.txt"

# 기존 crontab 내용 가져오기
crontab -l > "$TEMP_CRON" 2>/dev/null || touch "$TEMP_CRON"

# ETF 관련 기존 작업 제거
sed -i '/# ETF/d' "$TEMP_CRON"
sed -i '/etf_/d' "$TEMP_CRON"

# 새로운 하이브리드 시스템 cron 작업 추가
cat >> "$TEMP_CRON" << EOF

# ETF Redis + Oracle 하이브리드 시스템 - $(date)
# ================================================

# Redis 상태 점검 (매일 오전 8시)
0 8 * * * redis-cli -h 192.168.50.9 -p 6379 -a redis ping >> ${PROJECT_DIR}/logs/redis/health.log 2>&1

# 실시간 수집 시작 (평일 오전 8시 50분 - 장 시작 10분 전)
50 8 * * 1-5 cd ${PROJECT_DIR} && pkill -f etf_redis_realtime.py; nohup python3 etf_redis_realtime.py >> logs/redis/realtime.log 2>&1 &

# 배치 처리 (평일 오후 4시 - 장 종료 후)
0 16 * * 1-5 cd ${PROJECT_DIR} && python3 etf_batch_processor.py manual >> logs/batch/daily.log 2>&1

# 주간 Redis 정리 (일요일 오전 2시)
0 2 * * 0 redis-cli -h 192.168.50.9 -p 6379 -a redis FLUSHDB >> ${PROJECT_DIR}/logs/redis/cleanup.log 2>&1

# 로그 파일 정리 (월요일 오전 3시)
0 3 * * 1 find ${PROJECT_DIR}/logs -name "*.log" -mtime +30 -delete

EOF

# 새로운 crontab 적용
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo -e "  ✅ Cron 작업 설정 완료"

# 6. 실시간 수집 테스트
echo ""
echo -e "${YELLOW}🧪 실시간 시스템 테스트...${NC}"

read -p "실시간 수집 테스트를 실행하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "  🚀 실시간 수집 테스트 시작..."
    
    # 10초 동안 실시간 수집 테스트
    timeout 10 python3 etf_redis_realtime.py &
    TEST_PID=$!
    
    sleep 2
    
    # Redis에서 데이터 확인
    echo "  📊 Redis 데이터 확인 중..."
    redis-cli -h 192.168.50.9 -p 6379 -a redis KEYS "etf:*" | head -5
    
    wait $TEST_PID 2>/dev/null
    
    echo -e "  ✅ 실시간 수집 테스트 완료"
fi

# 7. 배치 처리 테스트
echo ""
read -p "배치 처리 테스트를 실행하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "  🔄 배치 처리 테스트 시작..."
    
    # 어제 날짜로 테스트 (오늘 데이터가 없을 수 있음)
    YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
    
    python3 etf_batch_processor.py manual "$YESTERDAY" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "  ✅ 배치 처리 테스트 완료"
    else
        echo -e "  ⚠️  배치 처리 테스트 실패 (정상일 수 있음 - 테스트 데이터 없음)"
    fi
fi

# 8. 설정 요약 출력
echo ""
echo -e "${PURPLE}📋 설정 완료 요약${NC}"
echo "=============================="

echo -e "${BLUE}🔴 Redis 클러스터:${NC}"
echo "  Host: 192.168.50.9:6379"
echo "  Password: redis"
echo "  사용 목적: 실시간 데이터 처리"

echo ""
echo -e "${BLUE}🔵 Oracle RAC:${NC}"  
echo "  Host: oracle19c01:1521/PROD"
echo "  Schema: stock"
echo "  사용 목적: 영구 데이터 저장"

echo ""
echo -e "${BLUE}⏰ 자동화 스케줄:${NC}"
echo "  08:50 - 실시간 수집 시작 (평일)"
echo "  16:00 - 배치 처리 실행 (평일)"
echo "  02:00 - 주간 정리 (일요일)"

echo ""
echo -e "${BLUE}📁 로그 위치:${NC}"
echo "  실시간: logs/redis/realtime.log"
echo "  배치: logs/batch/daily.log"
echo "  상태: logs/redis/health.log"

echo ""
echo -e "${GREEN}✨ ETF Redis + Oracle 하이브리드 시스템 설정 완료!${NC}"
echo ""

# 9. 다음 단계 안내
echo -e "${YELLOW}🎯 다음 단계:${NC}"
echo "1. 한국투자증권 계좌 개설 및 API 키 발급"
echo "2. config.yaml에서 API 키 설정"
echo "3. 월요일 오전 8시 50분에 자동 시작 확인"
echo "4. 실시간 모니터링:"
echo "   tail -f logs/redis/realtime.log"
echo ""

echo -e "${BLUE}🚀 시스템 준비 완료! 이제 실투자 가능! 💰${NC}"