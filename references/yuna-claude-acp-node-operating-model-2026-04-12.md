# Yuna 운영안 - 기본 main 챗봇이 아닌 Claude ACP 작업 노드로 사용

- 작성일: 2026-04-12
- 대상: Yuna (192.168.50.192)

## 배경

Yuna는 OpenClaw main 기본 챗봇 경로로는 불안정했다.

확인된 사실:
- OpenAI/Codex 쪽은 ChatGPT Plus usage limit에 자주 걸림
- OpenClaw main 라우팅과 fallback 구조는 여러 번 조정했지만 체감 안정성이 낮았음
- 반면 Yuna 로컬 Claude Code 자체는 정상 동작했고, Claude Max / `claude-opus-4-6` 런타임도 확인됨

즉 문제는 "Yuna의 Claude가 죽었다"가 아니라, "OpenClaw 기본 main 챗봇 구조와 Yuna 환경의 궁합이 나쁘다"에 가깝다.

## 결론

Yuna는 기본 main 챗봇으로 억지로 쓰지 말고, **Claude ACP 작업 노드**로 운영하는 것이 맞다.

## 역할 분리

### Luna
- 메인 비서
- 메인 채널 응답 담당
- 일반 대화, 관리, 라우팅 담당
- OpenClaw 기본 main 역할 유지

### Yuna
- Claude ACP 작업 노드
- 로컬 Claude Code 세션 기반 작업 처리
- 필요할 때 호출하는 보조 작업자 역할

## Yuna에 맡길 작업 유형

- 코드 작성/수정
- 코드 리뷰
- 문서 정리
- 긴 조사/리서치
- 병렬 보조 작업
- 로컬 Claude Code가 유리한 작업

## 운영 방식

### 기본 원칙
- 평소 대화는 Luna에서 처리
- "이건 Claude Code로 해봐", "유나에게 맡겨" 같은 요청은 Yuna로 위임
- Yuna는 상시 메인 채팅창보다, 필요할 때 부르는 전용 작업 노드처럼 사용

### 기대 효과
- OpenAI usage limit 영향 감소
- Yuna의 Claude Max 환경을 직접 활용 가능
- OpenClaw main 라우팅 불안정성 회피
- 역할이 명확해져 운영이 쉬워짐

## 장점

1. 로컬 Claude Code 강점을 그대로 사용 가능
2. 메인 챗봇 불안정 문제와 분리 가능
3. 병렬 작업 구조에 잘 맞음
4. Luna/Yuna 역할 분담이 명확함

## 주의점

- Yuna를 메인 챗봇으로 다시 억지 연결하려고 하면 같은 문제가 반복될 수 있음
- main/fallback/provider 튜닝보다, 역할 분리 자체가 더 중요함
- Yuna는 "대화 상시 응답자"보다 "전문 작업 노드"라는 관점으로 봐야 함

## 운영 원칙 한줄 요약

- **Luna = 메인 비서 / 메인 응답자**
- **Yuna = Claude ACP 작업 노드**

## 추천 사용 예

- "이 PR 리뷰 유나에게 맡겨"
- "이 문서 초안 Claude Code로 정리해줘"
- "이 기능 구현은 유나 Claude로 병렬 작업 돌리자"
- "메인 대화는 루나가 하고, 무거운 일은 유나가 받자"

## 최종 판단

현재 기준으로 Yuna를 살리는 가장 현실적인 방법은, main 챗봇 복구에 집착하는 것이 아니라 **Claude ACP 작업 노드라는 역할로 재정의하는 것**이다.
