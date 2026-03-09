#!/bin/bash
# ETF 자동매매 시스템을 기존 GitHub 저장소에 추가하는 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}📁 기존 저장소에 ETF 프로젝트 추가${NC}"
echo "============================================"

# 현재 프로젝트 경로
PROJECT_SOURCE="/root/.openclaw/workspace/etf_collector"

# 사용자 입력 받기
echo -e "${YELLOW}🔧 설정 정보를 입력해주세요:${NC}"
echo ""

# 기존 저장소 URL 입력
read -p "📍 기존 GitHub 저장소 URL: " REPO_URL
if [[ -z "$REPO_URL" ]]; then
    echo -e "${RED}❌ 저장소 URL이 필요합니다.${NC}"
    exit 1
fi

# 폴더명 입력 (기본값: etf-auto-trading)
read -p "📁 프로젝트 폴더명 (기본: etf-auto-trading): " FOLDER_NAME
FOLDER_NAME=${FOLDER_NAME:-etf-auto-trading}

# 작업 디렉토리 설정
WORK_DIR="/tmp/github_upload_$(date +%Y%m%d_%H%M%S)"
REPO_NAME=$(basename "$REPO_URL" .git)

echo ""
echo -e "${BLUE}📋 작업 정보:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "📍 저장소: ${GREEN}$REPO_URL${NC}"
echo -e "📁 폴더명: ${GREEN}$FOLDER_NAME${NC}"
echo -e "💼 작업 경로: ${GREEN}$WORK_DIR${NC}"
echo -e "📦 소스 경로: ${GREEN}$PROJECT_SOURCE${NC}"

echo ""
read -p "🚀 계속 진행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⏹️  작업을 취소했습니다.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}🔄 작업 시작...${NC}"

# 1. 작업 디렉토리 생성
echo -e "${YELLOW}📁 작업 디렉토리 생성 중...${NC}"
mkdir -p "$WORK_DIR"
cd "$WORK_DIR"

# 2. 기존 저장소 클론
echo -e "${YELLOW}📥 기존 저장소 클론 중...${NC}"
if ! git clone "$REPO_URL" "$REPO_NAME"; then
    echo -e "${RED}❌ 저장소 클론 실패. URL을 확인해주세요.${NC}"
    rm -rf "$WORK_DIR"
    exit 1
fi

cd "$REPO_NAME"

# 3. 프로젝트 폴더 생성
echo -e "${YELLOW}📂 프로젝트 폴더 생성: $FOLDER_NAME${NC}"
if [[ -d "$FOLDER_NAME" ]]; then
    echo -e "${YELLOW}⚠️  폴더가 이미 존재합니다. 기존 내용을 백업하고 교체합니다.${NC}"
    mv "$FOLDER_NAME" "${FOLDER_NAME}_backup_$(date +%Y%m%d_%H%M%S)" 2>/dev/null
fi

mkdir "$FOLDER_NAME"

# 4. 파일 복사
echo -e "${YELLOW}📄 ETF 프로젝트 파일 복사 중...${NC}"
if ! cp -r "$PROJECT_SOURCE/"* "$FOLDER_NAME/"; then
    echo -e "${RED}❌ 파일 복사 실패${NC}"
    cd /
    rm -rf "$WORK_DIR"
    exit 1
fi

# Git 히스토리 제거 (기존 저장소에 추가할 때)
rm -rf "$FOLDER_NAME/.git" 2>/dev/null

# 5. Git 상태 확인
echo -e "${YELLOW}📊 Git 상태 확인...${NC}"
git status

echo ""
echo -e "${BLUE}📁 추가된 파일들:${NC}"
find "$FOLDER_NAME" -type f | head -20
FILE_COUNT=$(find "$FOLDER_NAME" -type f | wc -l)
echo -e "${GREEN}📊 총 $FILE_COUNT개 파일이 추가됩니다.${NC}"

echo ""
read -p "🔍 파일 내용을 확인하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}📋 프로젝트 구조:${NC}"
    tree "$FOLDER_NAME" -L 2 2>/dev/null || find "$FOLDER_NAME" -type d | head -10
fi

# 6. Git에 추가
echo ""
echo -e "${YELLOW}📦 Git에 추가 중...${NC}"
git add "$FOLDER_NAME/"

# 7. 커밋 메시지 작성
echo -e "${YELLOW}💾 커밋 메시지 작성...${NC}"
COMMIT_MESSAGE="✨ Add ETF Auto-Trading System

🚀 Korean ETF Auto-Trading System v1.0

✨ Features:
- 10개 한국 ETF 자동 모니터링
- 기술적 지표 분석 (SMA, RSI, MACD, 볼린저밴드)
- AI 기반 매매 신호 생성 (BUY/SELL/HOLD)
- Oracle RAC 데이터베이스 연동
- 한국투자증권 OpenAPI 지원
- 완전 자동화 시스템 (Cron)

📊 Supported ETFs:
- KODEX 200, KOSDAQ150, 2차전지, 고배당
- TIGER 200IT, NASDAQ100, 건설, 원유선물
- KODEX US SP500, 삼성우선주

🛠️ Tech Stack:
- Python 3.9+ | Oracle RAC | TA-Lib
- RESTful API | 완전한 문서화

📁 Location: /$FOLDER_NAME/"

# 8. 커밋 실행
echo -e "${YELLOW}💾 커밋 실행 중...${NC}"
if git commit -m "$COMMIT_MESSAGE"; then
    echo -e "${GREEN}✅ 커밋 완료!${NC}"
else
    echo -e "${RED}❌ 커밋 실패${NC}"
    cd /
    rm -rf "$WORK_DIR"
    exit 1
fi

# 9. 푸시 확인
echo ""
echo -e "${PURPLE}🚀 GitHub에 푸시할 준비가 완료되었습니다!${NC}"
echo ""
read -p "📤 지금 푸시하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}📤 GitHub에 푸시 중...${NC}"
    if git push origin main; then
        echo ""
        echo -e "${GREEN}🎉 성공! ETF 프로젝트가 GitHub에 업로드되었습니다!${NC}"
        echo ""
        echo -e "${BLUE}📍 확인할 위치:${NC}"
        echo -e "   🌐 GitHub: $REPO_URL/tree/main/$FOLDER_NAME"
        echo -e "   📁 로컬: $(pwd)/$FOLDER_NAME"
        echo ""
        echo -e "${PURPLE}🎯 다음 단계:${NC}"
        echo -e "   1. GitHub에서 폴더 구조 확인"
        echo -e "   2. README.md 내용 점검"
        echo -e "   3. Issues/Wiki 탭 활성화"
        echo -e "   4. 저장소 설정에서 Topics 추가"
    else
        echo -e "${RED}❌ 푸시 실패. 권한을 확인해주세요.${NC}"
        echo -e "${YELLOW}💡 수동 푸시: cd $(pwd) && git push origin main${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}📋 수동 푸시 방법:${NC}"
    echo -e "   cd $(pwd)"
    echo -e "   git push origin main"
fi

# 10. 정리
echo ""
echo -e "${BLUE}🧹 정리 작업...${NC}"
echo -e "${YELLOW}📁 작업 디렉토리 위치: $WORK_DIR${NC}"
read -p "🗑️  작업 디렉토리를 삭제하시겠습니까? (Y/n): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    cd /
    rm -rf "$WORK_DIR"
    echo -e "${GREEN}✅ 정리 완료!${NC}"
else
    echo -e "${YELLOW}📁 작업 디렉토리 보존: $WORK_DIR${NC}"
fi

echo ""
echo -e "${GREEN}🎉 ETF 자동매매 시스템 업로드 완료!${NC}"
echo -e "${PURPLE}⭐ 저장소에 Star를 눌러주세요!${NC}"