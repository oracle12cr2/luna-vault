# Claude Pro 사용량 제한 논란 + Mythos 유출 + Claude Code 팁

> 출처: https://www.youtube.com/watch?v=E9W17CTE1PA

## 1. Claude Pro 사용량 제한 논란
- Pro($20): 피크 시간(한국 21시~03시)에 프롬프트 2개로 100% 소진
- Max($200): 같은 작업 40개 해도 7%
- 토큰 한도/피크 시간 미공개 → 투명성 부재 비판
- Anthropic: "전체 7%만 영향" (핵심 유료 사용자가 그 7%)

## 2. 비밀 모델 "Claude Mythos" 유출
- Anthropic 공개 캐시에서 미발표 문서 ~3,000건 발견
- Opus 4.6보다 강력한 새 모델 (코드명 "카피바라" 등급)
- 사이버보안: 방어자 수준 초월하는 취약점 탐지/공격 능력
- 출시 전 보안 전문가 우선 접근 계획
- Anthropic: "인적 실수" (의도적 마케팅 의혹도)

## 3. CLAUDE.md 베스트 프랙티스
- **200줄 넘으면** 지시 안 따르기 시작 ⚠️
- **300줄 이상** 효과 급감
- 핵심만 CLAUDE.md, 세부는 `rules/` 폴더로 분리
- `skills/` 폴더에 작업 정의 → 자동 실행

## 4. Claude Code 스케줄 작업 (공식 출시)
- 예약 작업: 매일 PR 요약, 매주 보안 감사, PR 머지 시 문서 동기화
- 주기: 매시간/매일/평일/매주
- 외부 연동: Slack, Linear
- 대상: Pro, Max, Teams, Enterprise

## 참고 사항
- 피크 시간(21시~03시) API 제한 가능성 주의
- CLAUDE.md 200줄 제한 → 우리 설정 파일 점검 필요
- Mythos 출시되면 자동매매 분석 고도화 가능
