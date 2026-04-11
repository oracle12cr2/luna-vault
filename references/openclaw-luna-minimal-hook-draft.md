# OpenClaw / Luna 최소 Hook 초안

- 작성일: 2026-04-12
- 목적: ECC의 hook 설계 철학을 참고하되, 루나/OpenClaw 운영에 과하지 않은 최소 세트만 정의

## 원칙

- hook은 적을수록 좋다
- 차단은 정말 위험한 경우에만 쓴다
- 나머지는 경고/기록 위주로 간다
- 복잡한 로직은 inline 대신 script로 분리한다
- 매 edit마다 무거운 검증을 돌리지 않고, 가능한 것은 작업 단위 종료 시점에 모아 실행한다

## 최소 hook 3개

---

## 1. Session Summary Hook

### 목적

세션이 끝나거나 작업이 마무리될 때, 이번 세션에서 남길 가치가 있는 결과만 짧게 기록한다.

### 기대 효과

- daily memory 정리 보조
- 중요한 결정/교훈 누락 방지
- 다음 세션에서 빠르게 이어받기 쉬움

### 실행 시점

- 세션 종료 직전
- 또는 작업 완료 후 수동/자동 트리거

### 동작 방식

- 오늘 작업에서 의미 있는 항목만 추출
- 아래 중 하나에 기록 후보 생성
  - `memory/YYYY-MM-DD.md`
  - `WORKING.md` 정리용 메모
  - 필요 시 `MEMORY.md` 반영 후보

### 정책

- **차단 없음**
- 기본은 기록 후보만 생성하거나 요약문만 제안
- 자동 기록을 하더라도 짧고 보수적으로만

### 우리 환경 적용 메모

가장 먼저 도입하기 쉬운 hook이다.
실제 구현은 완전 자동보다 "요약 초안 생성 → 필요 시 저장" 흐름이 안전하다.

---

## 2. Stop-Time Validation Hook

### 목적

코드/문서 수정 후 응답 종료 시점에만 가벼운 검증을 모아서 실행한다.

### 기대 효과

- 수정 직후 기본 오류를 빨리 발견
- edit마다 검증하지 않아 체감 부담 감소
- 작업 완료 전 품질 체크 습관화

### 실행 시점

- assistant 응답 종료 시점
- 또는 코드 변경이 발생한 턴 종료 시점

### 검사 후보

우선은 아주 가볍게 시작:

- git diff 존재 여부 확인
- 수정 파일 수집
- 언어별 빠른 lint/format/typecheck 후보 탐지
- 문서 파일이면 markdown lint 대신 경고 수준 검사만

예시:
- JS/TS → prettier/biome/tsc 후보 탐지
- Python → ruff/pytest 후보 탐지
- 쉘 → shellcheck 후보 탐지
- 문서 → 링크/형식은 나중에

### 정책

- 1단계: **경고만**
- 2단계: 명백한 실패(예: syntax error)만 경고 강화
- 차단형은 도입하지 않음

### 우리 환경 적용 메모

지금 루나 운영에는 "무조건 모든 변경 후 전체 lint"는 무겁다.
대신 "이번 턴에서 바뀐 파일 기준으로 가능한 검사 후보를 제안하거나 실행"이 현실적이다.

---

## 3. Config Protection Hook

### 목적

agent가 문제를 해결한다고 하면서 lint/formatter/security/config를 약화하는 것을 막는다.

### 왜 중요하나

AI가 막힐 때 가장 나쁜 우회 중 하나가 설정을 느슨하게 만드는 것이다.
예:
- lint rule 끄기
- typecheck 끄기
- test skip 추가
- 보안 검증 비활성화

### 감시 대상 예시

- `.eslintrc*`
- `eslint.config.*`
- `biome.json`
- `tsconfig.json`
- `pyproject.toml`
- `ruff.toml`
- `pytest.ini`
- `package.json` 내 scripts/test/lint 관련 완화
- `.github/workflows/*` 테스트 우회
- OpenClaw/Claude/Codex 관련 핵심 설정 파일

### 정책

- 기본은 **강한 경고**
- 특정 파일/패턴은 **차단 후보**
- 차단 메시지는 "설정을 약화하지 말고 코드/원인을 수정하라" 방향으로 유도

### 우리 환경 적용 메모

이건 최소 세트 중 가장 가치가 크다.
특히 장기적으로 codex/claude/openclaw 혼합 사용 시 안전장치가 된다.

---

## 적용 우선순위

### 1순위
- Config Protection Hook
- Session Summary Hook

### 2순위
- Stop-Time Validation Hook

이유:
- config protection은 사고 예방 효과가 큼
- session summary는 기억 품질 개선에 바로 도움
- stop validation은 유용하지만 구현 범위를 잘못 잡으면 금방 무거워질 수 있음

## 구현 방식 제안

### Phase 1 - 문서화만

- 정책 문서만 먼저 정리
- 어떤 상황에서 경고/차단할지 기준 합의

### Phase 2 - 경고형부터

- session summary 초안 생성
- config 변경 감지 시 경고
- stop 시점 검증 후보 출력

### Phase 3 - 제한적 자동화

- 정말 안전한 항목만 자동 실행
- 예: changed files 기준 빠른 lint
- config 약화 시도 일부 차단

## 하지 말아야 할 것

- 초반부터 hook를 많이 붙이는 것
- 모든 수정에 무조건 full lint/typecheck 돌리는 것
- 메모리 자동 기록을 과하게 해서 daily log를 오염시키는 것
- 설정 파일 변경을 전부 무조건 차단하는 것

## 결론

루나/OpenClaw용 최소 hook 세트는 "운영을 돕는 얇은 안전망"이어야 한다.

핵심은 세 가지다:
- 세션 끝나면 중요한 것만 남기기
- 응답 끝나면 가벼운 검증하기
- 설정 약화는 강하게 막기

이 정도만 해도 과하지 않으면서 실질적인 품질 향상 효과를 기대할 수 있다.
