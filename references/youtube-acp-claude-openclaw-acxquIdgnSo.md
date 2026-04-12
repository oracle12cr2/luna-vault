# YouTube 메모 - Claude 차단 이후 OpenClaw / ACP 대안 정리

- 영상 링크: https://www.youtube.com/watch?v=acxquIdgnSo
- 확인일: 2026-04-12
- 제목 요지: Anthropic/Claude의 서드파티 경유 사용 제한 이후, OpenClaw와 ACP를 어떻게 활용할지 설명

## 한줄 요약

Claude를 OpenClaw 같은 서드파티 경유 방식으로 직접 붙여 쓰는 길이 점점 막히고 있기 때문에, 앞으로는 종량제 API 전환, 다른 모델 사용, 또는 ACP를 통해 로컬 Claude Code 세션에 작업을 보내는 방식이 현실적 대안이라는 내용이다.

## 영상 핵심 포인트

### 1. 서드파티 경유 Claude 사용 제한

영상에서는 2026-04-04부터 OpenClaw 같은 서드파티 도구를 통해 Claude 계정을 연결해서 쓰는 방식이 사실상 막혔다고 설명한다.

핵심 메시지:
- 기존처럼 Claude 계정을 외부 하네스에 붙여서 무제한/편법처럼 쓰는 방식은 점점 어려워짐
- API 과금 전환 또는 사용 제한이 걸릴 수 있음

## 2. 추천 대안

영상에서 제시하는 주요 대안은 다음과 같다.

1. 종량제 API로 전환
2. 다른 모델(OpenAI/Codex 등) 사용
3. ACP를 통해 로컬 Claude Code에 작업 위임

즉 "Claude를 서드파티가 직접 소유해서 쓰는 구조"보다, "내 로컬/내 세션에서 돌고 있는 Claude Code에 작업을 보내는 구조"가 더 현실적이라고 본다.

## 3. ACP(Agent Communication Protocol) 관점

영상 설명 기준 ACP는:
- AI 에이전트끼리 대화/작업 전달을 가능하게 하는 프로토콜
- OpenClaw 같은 오케스트레이터가
- 로컬 컴퓨터에서 실행 중인 Claude Code 세션에
- 일을 보내고 결과를 받는 구조

핵심 의미:
- Claude를 직접 우회 호출하는 게 아니라
- 사용자가 정상적으로 쓰고 있는 Claude Code 환경을 활용하는 방식

## 4. 비용/정책 리스크 인식

영상에서는 다음 맥락도 강조한다.

- Google/Anthropic 모두 이런 비공식/우회적 사용을 장려하지 않음
- 사용량이 크면 정책 변경이나 제한이 언제든 들어올 수 있음
- 따라서 특정 편법 경로에 운영을 전부 걸면 위험함

## 우리 환경과 직접 연결되는 포인트

이 영상은 우리 최근 상황과 거의 그대로 맞닿아 있다.

### 연결되는 실제 이슈
- Claude usage limit surface
- star-cliproxy 경유 Claude 사용 불안정
- OpenAI 우선 / Claude fallback 재조정
- ACP 런타임을 통한 Codex/Claude 세션 활용

즉 이 영상은 일반론이 아니라, 우리가 이미 겪고 있는 문제를 설명해 주는 레퍼런스에 가깝다.

## 우리 기준 실전 해석

### 1. 기본 경로는 OpenAI/Codex 쪽이 더 안정적
- 정책 리스크와 사용량 제한을 고려하면 OpenAI/Codex를 기본 경로로 두는 것이 운영상 편함
- 특히 자동화/대량 작업은 Claude보다 정책 충돌 가능성이 낮은 경로가 유리함

### 2. Claude는 직접 API보다 ACP/로컬 세션 활용이 현실적
- Claude를 꼭 써야 한다면
- 로컬에서 정상 로그인된 Claude Code 세션을 활용하는 방식이 더 현실적임
- 즉 "Claude를 원격 provider처럼 쓰기"보다 "Claude Code에 일 보내기"가 낫다는 뜻

### 3. fallback 설계가 중요
- 한 provider에 전부 걸지 말고
- OpenAI 우선, Claude 보조 같은 다중 경로를 유지해야 함
- 특히 usage limit, alias mismatch, 정책 차단에 대비해야 함

## 우리 운영 기준 권장 방향

1. **기본 모델 경로는 OpenAI/Codex 우선**
2. **Claude는 ACP/로컬 Claude Code 세션 활용 우선**
3. **서드파티 경유 Claude direct 연결은 보조/실험용으로만 취급**
4. **fallback을 항상 준비**
5. **특정 모델/정책에 종속되지 않도록 cross-harness 구조 유지**

## 결론

이 영상의 핵심은 단순한 우회 팁이 아니다.

본질은 이거다:
- Claude direct 경유는 점점 불안정해진다
- 안정적인 운영은 OpenAI/Codex + ACP + fallback 구조로 가야 한다

우리 환경에서도 같은 결론이 이미 여러 번 확인되고 있으므로, 참고 가치가 높은 영상이다.
