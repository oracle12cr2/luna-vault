# Everything Claude Code hooks 분석 메모

- 원문 저장소: https://github.com/affaan-m/everything-claude-code
- 확인일: 2026-04-11
- 분석 범위: `hooks/README.md`, `hooks/hooks.json`

## 한줄 요약

ECC의 hooks는 단순 자동화가 아니라, 에이전트 작업 흐름 전체에 품질/안전/메모리/관측을 얹는 운영 레이어다.

## 구조 요약

ECC는 다음 이벤트 단위로 hook을 둔다.

- `PreToolUse`
- `PostToolUse`
- `PostToolUseFailure`
- `SessionStart`
- `PreCompact`
- `Stop`
- `SessionEnd`

즉, 단순히 "명령 전/후"만 보는 게 아니라 세션 시작, 응답 종료, 컨텍스트 압축 전까지 전부 관리한다.

## 눈에 띄는 설계 포인트

### 1. inline one-liner보다 script 기반 hook 선호

README와 hooks.json을 보면 복잡한 로직을 별도 script로 뽑고, hook에서는 runner만 호출한다.

예:
- `run-with-flags.js`
- `session-start-bootstrap.js`
- `quality-gate.js`
- `session-end.js`

의미:
- 유지보수 쉬움
- 플랫폼 호환성 향상
- hook별 기능 분리 명확

우리도 복잡한 검증/기록 로직은 장기적으로 스크립트화하는 편이 좋다.

### 2. Hook profile 개념이 좋음

환경변수로 hook 강도를 바꾼다.

- `ECC_HOOK_PROFILE=minimal|standard|strict`
- `ECC_DISABLED_HOOKS=...`

이건 꽤 좋은 패턴이다.

장점:
- 같은 hook 세트를 유지하면서도 상황별 강도 조절 가능
- 디버깅/긴급 우회가 쉬움
- 설정 파일 직접 수정 없이 런타임 제어 가능

우리 환경에도 적용 아이디어가 있다:
- `strict`: 안전/검증 많이
- `standard`: 평시 기본
- `minimal`: 성능 우선, 최소 체크만

### 3. Stop 시점 배치 검증이 실용적

ECC는 매 edit마다 무겁게 돌리지 않고, 일부는 `Stop` 시점에 모아서 실행한다.

예:
- batch format
- typecheck
- console.log audit
- session summary
- pattern extraction
- cost tracking

이 방식이 좋은 이유:
- edit마다 과도한 비용/지연 방지
- 한 응답 단위로 검증 가능
- 사용자 체감이 덜 거슬림

우리도 "매 수정마다 전체 검증"보다, 응답 종료 시점 또는 작업 단위 종료 시점 검증이 더 현실적일 수 있다.

### 4. 차단형 hook과 경고형 hook을 분리함

ECC는 pre-hook에서:
- `exit code 2` → 차단
- stderr 경고 → 경고만

예:
- 위험한 commit/push 습관 차단/경고
- config 약화 시도 차단
- 문서 파일 생성은 경고만

이 구분이 중요하다.

우리도 기준을 이렇게 나누는 게 좋다:
- 차단: 보안, config 약화, 위험한 destructive 작업
- 경고: 문서 위치, tmux 권장, compact 권장, console.log 주의

### 5. 관측성과 거버넌스를 hook에 심음

ECC hook에는 단순 품질검사 외에도 이런 것이 있음:
- bash command audit log
- cost tracker
- governance capture
- session activity tracker
- MCP health check

즉 hooks를 "자동 검증"뿐 아니라 "운영 telemetry" 레이어로도 쓴다.

이건 우리에게도 참고 가치가 크다.
특히 OpenClaw 쪽에서는:
- 실패 패턴 기록
- 어떤 유형 작업에서 비용이 큰지 기록
- 특정 도구/플로우 장애 감지
같은 데 응용 가능하다.

## 우리 환경에 가져올 만한 것

### 우선순위 높음

1. **SessionStart / Stop 기반 상태 기록 패턴**
- 이미 memory 구조가 있으니, hook은 그 보조 수단으로만 사용
- 세션 종료 시 요약/작업 흔적을 남기는 방식 참고 가능

2. **Stop 시점 배치 검증 패턴**
- 편집마다 무거운 검사 대신, 응답 종료 시 lint/typecheck 모아 실행
- 실제 체감 품질이 좋아질 수 있음

3. **profile 기반 hook 강도 제어**
- 환경별, 작업별로 검증 강도 바꾸기 쉬움

4. **config-protection 같은 차단형 패턴**
- linter/formatter/security config를 agent가 함부로 약화하지 못하게 막는 건 유용함

### 우선순위 중간

5. **tmux / long-running command guard**
- Claude Code 같은 환경에는 좋지만 OpenClaw 전체에 그대로 넣을 필요는 없음
- 특정 coding workflow에만 선택 적용 가능

6. **governance / cost / activity tracker**
- 좋긴 한데 지금 당장 넣기엔 다소 무거움
- 나중에 운영 가시성이 필요할 때 참고

### 우선순위 낮음

7. **continuous learning observer hooks**
- 재미있지만 잘못 설계하면 컨텍스트/로그 노이즈가 커질 수 있음
- 현재 루나 운영 구조에서는 신중해야 함

## 우리 기준 결론

ECC hooks에서 가장 배울 점은 "훅을 많이 쓴다"가 아니다.
핵심은 이거다:

- hook은 작고 역할이 분명해야 함
- 복잡한 로직은 script로 분리
- 차단과 경고를 명확히 구분
- 매 edit마다 무겁게 돌리지 말고 Stop 시점 배치 검증 활용
- 세션 lifecycle(SessionStart/Stop/PreCompact)을 적극 활용
- 강도 조절(profile) 가능한 구조가 운영에 유리함

## 추천 다음 단계

1. 우리 workflow에 맞는 최소 hook 패턴 3개만 설계
   - session summary
   - stop 시점 validation
   - config protection

2. OpenClaw/루나용으로 과하지 않은 hook policy 초안 작성

3. 실제 적용은 전체 도입이 아니라 작은 실험부터 시작

## 한줄 결론

ECC hooks는 "많이 붙인 자동화"가 아니라, 에이전트 운영 품질을 관리하는 작은 정책 엔진 모음에 가깝다. 우리도 통째로 베끼기보다 이 설계 철학만 가져오는 게 맞다.
