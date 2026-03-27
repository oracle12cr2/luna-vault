# CLAUDE.md — 프로젝트 공통 규칙

## 환경
- 서버: Rocky Linux 9, 192.168.50.56
- Python: /home/anaconda3/bin/python3
- Node: v22 (nvm)
- DB: Oracle 19c RAC (app_user@50.35:1521/PROD)

## 코딩 규칙
- 한국어 주석 사용
- 파일 상단에 목적 설명 docstring 필수
- cron 스크립트는 절대경로 shebang (#!/home/anaconda3/bin/python3)
- 에러 처리: try/except로 감싸고 로깅 필수
- 민감 정보(API 키, 비밀번호)는 환경변수 또는 별도 config 파일

## Git
- 커밋 메시지: 한국어, 변경 내용 요약
- 시크릿 포함 파일 커밋 금지 (.gitignore 확인)

## 기타
- 상세 규칙은 .claude/rules/ 에서 작업 유형별 자동 로드
