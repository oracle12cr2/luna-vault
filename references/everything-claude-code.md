# Everything Claude Code 참고 메모

- 원문: https://github.com/affaan-m/everything-claude-code
- 확인일: 2026-04-11
- 라이선스: MIT
- 홈페이지: https://ecc.tools

## 한줄 요약

Claude Code를 중심으로 Codex, Cursor, OpenCode 등 여러 AI 코딩 하네스를 더 체계적으로 운영하기 위한 대형 agent harness 최적화 시스템이다.

## 저장소 성격

- 단순 프롬프트 모음이 아님
- agents, skills, hooks, rules, memory persistence, security, eval, model routing까지 포함한 운영 프레임워크에 가까움
- 매우 opinionated 한 구조를 가짐
- 대규모 커뮤니티 검증이 어느 정도 된 상태

## 규모 메모

- 스타: 15만+
- 포크: 2.3만+
- 기여자: 170+
- 언어 생태계: 12+
- 주 언어: JavaScript

## 핵심 구성

- agents: 역할별 서브에이전트
- skills: 작업 흐름과 도메인 지식
- hooks: 세션 시작/종료/편집/검증 자동화
- rules: 언어/도구별 규칙 세트
- memory persistence: 세션 간 맥락 유지
- verification loops: checkpoint, continuous eval, grader
- security scanning: AgentShield 포함
- cross-harness support: Claude Code, Codex, Cursor, OpenCode, Gemini 등

## 우리 환경에서 배울 만한 포인트

### 1. Memory persistence 패턴

- 세션 시작/종료 훅으로 문맥을 자동 저장/복원하는 접근은 참고 가치가 큼
- 다만 우리 쪽은 이미 `MEMORY.md`, daily memory, AGENTS.md 구조가 있으므로 통째 도입보다는 훅 설계 아이디어만 참고하는 편이 적절함

### 2. Hook 설계 방식

- inline one-liner 대신 script 기반 hook으로 안정성을 높인 점이 좋음
- OpenClaw에서도 장기적으로는 복잡한 hook 로직을 스크립트화하는 방식이 유지보수에 유리할 수 있음

### 3. Verification / review loop

- 단순 생성보다 중간 checkpoint, review, grading 루프를 넣는 구조가 인상적임
- 우리도 중요 작업에서 `review → validate → commit` 흐름을 더 명확히 만들 때 참고 가능

### 4. Cross-harness 관점

- Claude Code 전용이 아니라 Codex, Cursor, OpenCode까지 고려하는 구조가 강점
- 루나/유나 환경처럼 여러 도구를 혼용할 때 패턴 재사용 아이디어를 얻기 좋음

### 5. Security / cost awareness

- agentic security, 비용 통제, sandboxing을 같이 다루는 건 실무적으로 중요함
- 특히 자동화 훅이 많아질수록 보안/비용 규칙을 함께 설계해야 한다는 점을 다시 확인시켜줌

## 우리 환경에 바로 도입할 것은 아님

이 repo는 크고 무겁고 규칙이 강하다. 현재 OpenClaw + 루나 운영 구조에 통째로 넣는 것은 과하다.

추천 방향:
- 전체 설치/전면 적용 X
- 필요한 패턴만 추출 O
- 특히 memory, hook, review/eval, security 부분만 선택적으로 참고

## 우리 기준 추천 액션

1. `hooks` 구조 읽고 안정적인 패턴만 벤치마킹
2. `memory persistence` 구조와 우리 memory 체계 비교
3. `review / validation` 루프를 우리 coding workflow에 부분 적용
4. Codex/Cursor 공용으로 재사용 가능한 운영 규칙이 있는지 선별

## 결론

이건 “Claude Code 잘 쓰는 법 모음”보다는 “AI 코딩 에이전트 운영체계 전체 패키지”에 가깝다.

우리에게 유용한 건 전체 도입이 아니라, 이미 가진 OpenClaw 운영 방식에 맞는 패턴만 추출해 흡수하는 것이다.
