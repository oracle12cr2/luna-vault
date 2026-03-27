---
globs: ["blog-front/**", "luna-dashboard/**", "**/*.tsx", "**/*.jsx"]
---

# Next.js 프론트엔드 규칙

## 블로그 (oracle23cr2.asuscomm.com)
- 프론트: Next.js, webserver01/02 이중화, PM2 관리, 포트 3001
- API: Fastify, 포트 3000
- DB: Oracle 19c (app_user@50.35:1521/PROD)
- 관리자: /admin (admin/admin1234)

## 스타일
- 다크테마 기본
- 모바일 반응형 필수
- Tailwind CSS 사용
- 컴포넌트: 함수형 + TypeScript

## 디자인 참고
- velog/dev.to 스타일
- 사이드바: 프로필 + 검색 + 카테고리 트리
- 코드블록, blockquote 강조

## 배포
- 빌드: npm run build
- 재시작: pm2 restart blog-front (webserver01, webserver02 양쪽)
