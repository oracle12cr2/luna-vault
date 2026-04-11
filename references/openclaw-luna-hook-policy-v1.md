# OpenClaw / Luna Hook Policy v1

- 작성일: 2026-04-12
- 상태: 초안이 아닌 실행 준비용 정책 문서
- 기반 문서:
  - `references/everything-claude-code-hooks.md`
  - `references/openclaw-luna-minimal-hook-draft.md`

## 목적

루나/OpenClaw 운영에서 과하지 않은 최소 hook 세트를 정의하고, 실제 감시 대상과 경고/차단 기준을 명확히 한다.

## 정책 철학

- hook은 적고 명확해야 한다
- 차단은 드물게, 경고는 실용적으로
- 메인 목표는 생산성 방해가 아니라 사고 예방
- 자동화보다 운영 일관성이 우선
- 복잡한 로직은 script로 분리한다

---

# Hook 1. Session Summary Policy

## 목표

세션 종료 또는 작업 완료 시, 다음 세션에 필요한 최소 요약만 남긴다.

## 기록 후보

다음 중 하나라도 만족하면 기록 후보로 본다.

- 파일 생성/수정/배포/설치 완료
- 설정 변경 완료
- 에러 원인 및 해결책 확보
- 다음 액션이 분명한 TODO 생성
- 반복될 가능성이 높은 교훈 확보

## 기록 위치 우선순위

1. `memory/YYYY-MM-DD.md`
2. `WORKING.md`
3. 장기 가치가 높을 때만 `MEMORY.md`

## 기록 금지

다음은 기록하지 않는다.

- 사소한 탐색 흔적
- 실패한 가설의 상세 로그
- 이미 다른 문서에 충분히 있는 중복 설명
- 토큰만 잡아먹는 장황한 회고

## 정책

- 기본 동작: **요약 초안 생성 또는 짧은 기록만**
- 차단 없음
- 자동 기록 시 최대 3~7줄 내로 제한

---

# Hook 2. Stop-Time Validation Policy

## 목표

편집이 발생한 턴 종료 시점에만 가벼운 검증을 수행해, 기본 오류를 빨리 드러낸다.

## 실행 조건

다음 조건일 때만 실행 후보로 본다.

- `Edit`, `Write`, `MultiEdit` 발생
- 실제 파일 변경이 존재
- 변경 파일 수가 과도하지 않음

## 우선 적용 대상

### JavaScript / TypeScript
- 파일 패턴:
  - `*.js`
  - `*.jsx`
  - `*.ts`
  - `*.tsx`
- 검사 후보:
  - prettier 또는 biome format check
  - `tsc --noEmit` 가능 여부 확인
  - eslint/biome lint 가능 여부 확인

### Python
- 파일 패턴:
  - `*.py`
- 검사 후보:
  - `ruff check`
  - `ruff format --check` 또는 format 안내
  - 필요 시 `pytest -q` 후보 제안

### Shell
- 파일 패턴:
  - `*.sh`
  - shebang이 bash/sh인 파일
- 검사 후보:
  - `shellcheck`

### Markdown / Docs
- 파일 패턴:
  - `*.md`
  - `docs/**`
  - `references/**`
- 검사 후보:
  - 길이/형식 경고만
  - 깨진 링크나 markdown lint는 후순위

## Validation 동작 규칙

- 1단계: 실행 가능한 검사 후보만 안내 또는 실행
- 2단계: 빠르고 안전한 검사만 자동 실행
- 3단계: 무거운 테스트는 권고만

## 차단 기준

기본적으로 차단 없음.
다만 장기적으로 고려 가능한 예외:
- syntax error 명백
- 포맷/구문 오류가 즉시 확인된 경우 강한 경고

## 제외 대상

다음은 기본적으로 stop validation 대상에서 제외한다.

- `memory/**`
- `daily-logs/**`
- `.archive-*`
- 대용량 데이터/리포트 파일
- 외부 벤더 코드

---

# Hook 3. Config Protection Policy

## 목표

문제를 해결한다는 이유로 lint/format/test/security/config를 약화시키는 변경을 감지하고 강하게 방지한다.

## 최우선 감시 파일

### JS/TS tooling
- `eslint.config.js`
- `eslint.config.cjs`
- `.eslintrc`
- `.eslintrc.json`
- `.eslintrc.js`
- `biome.json`
- `package.json`
- `tsconfig.json`
- `tsconfig.*.json`

### Python tooling
- `pyproject.toml`
- `ruff.toml`
- `.ruff.toml`
- `pytest.ini`
- `tox.ini`

### CI / workflow
- `.github/workflows/*.yml`
- `.github/workflows/*.yaml`

### OpenClaw / agent config
- `AGENTS.md`
- `SOUL.md`
- `MEMORY.md`
- `HEARTBEAT.md`
- `.claude/**`
- `.codex/**`
- `openclaw` 관련 설정 파일

## 위험 패턴

다음 패턴은 강한 경고 또는 차단 후보다.

### lint / format 약화
- rule disable 추가
- ignore 범위 과도 확대
- lint script 제거
- formatter 비활성화

예시 문자열:
- `eslint-disable`
- `rules: { ... off }`
- `ignorePatterns`
- `biome` 검사 비활성화

### type / test 약화
- `skipLibCheck: true` 를 문제 회피용으로 추가
- `noEmitOnError` 해제
- test script 제거 또는 `exit 0`
- workflow에서 test step 삭제

### security 약화
- secret scan 비활성화
- auth 관련 보호 로직 제거
- 보안 검사를 무시하는 설정 추가

### approval / safety 우회
- 위험 플래그 추가
- 검증 우회용 command/script 추가

## 차단 기준

다음은 **차단 후보**

- 테스트/검증을 우회하기 위한 CI step 제거
- lint/type/security 설정을 명백히 완화하는 변경
- agent 운영 핵심 설정을 파괴적으로 변경
- 안전장치 비활성화 목적이 명백한 경우

## 경고 기준

다음은 **강한 경고**

- 설정 파일 수정 자체
- package scripts 변경
- ignore 범위 확대
- type/lint/test 옵션 완화 가능성

## 허용 예외

다음은 차단하지 않는다.

- 명확한 근거와 함께 설정을 정교화하는 변경
- 성능/호환성 대응을 위한 제한적 조정
- 사용자가 직접 요청한 설정 변경

단, 이 경우도 변경 이유를 남기는 것이 좋다.

---

# 운영 우선순위

## 바로 도입 가능

1. Config Protection 경고형
2. Session Summary 초안형

## 제한적으로 도입 가능

3. Stop-Time Validation 경고형

## 나중에 검토

- config protection 일부 차단형
- session summary 자동 저장 강화
- validation 자동 실행 범위 확대

---

# 구현 메모

## 구현 방식

- hook 본체는 작게 유지
- 실제 로직은 별도 script
- 변경 파일 목록 수집 후 경량 판단
- 차단은 exit code 기반, 경고는 stderr/메시지 기반

## 추천 스크립트 분리

- `scripts/hooks/session-summary.*`
- `scripts/hooks/stop-validation.*`
- `scripts/hooks/config-protection.*`

## 로그/기록 원칙

- 너무 많이 남기지 말 것
- 실패 이유는 짧고 명확하게
- 메모리 오염 방지

---

# 최종 결론

루나/OpenClaw에서 hook는 "강한 통제 장치"보다 "가벼운 운영 안전망"이 맞다.

v1 정책의 핵심은 이 세 가지다.

1. 중요한 것만 남긴다
2. 종료 시점에 가볍게 검증한다
3. 설정 약화는 강하게 경계한다

이 정도면 과도한 자동화 없이도 실질적인 품질 향상과 사고 예방 효과를 기대할 수 있다.
