---
globs: ["**/*.test.*", "**/*.spec.*", "**/*_test.*", "**/test_*.*"]
---

# 테스트 규칙

## 원칙
- 테스트 파일은 대상 파일과 같은 디렉토리에 배치
- 테스트 함수명: test_기능_설명 (Python) / describe+it (JS/TS)
- 엣지 케이스 포함 (빈 값, 초과값, 권한 없음)

## Python 테스트
- pytest 사용
- fixture 활용, 하드코딩 금지
- DB 테스트: 별도 테스트 스키마 사용

## JS/TS 테스트
- Jest 또는 Vitest
- 컴포넌트 테스트: React Testing Library
- E2E: Playwright (MCP 연동 가능)
