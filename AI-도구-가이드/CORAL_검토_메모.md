# CORAL 검토 메모

- 리포: https://github.com/Human-Agent-Society/CORAL
- 공식 설명: CORAL은 **멀티 에이전트 self-evolution / autoresearch 인프라**다.
- 핵심 개념:
  - 여러 에이전트가 각자 **git worktree**에서 분리 실행
  - `.coral/` 공유 상태(시도, 노트, 스킬)를 함께 사용
  - grader 점수 기반으로 반복 개선
  - CLI + 웹 UI 제공
  - Claude Code / Codex / OpenCode 지원

## 한 줄 요약

OpenClaw 같은 개인 비서/오케스트레이터를 대체하는 도구가 아니라,
**장기 실험형 멀티 에이전트 실행기**에 가깝다.

즉 추천 구조는:
- **OpenClaw = 허브 / 비서 / 운영 레이어**
- **CORAL = 장기 실험 / 자동 개선 런타임**

## 설치/실행 개요

```bash
git clone https://github.com/Human-Agent-Society/CORAL.git
cd CORAL
uv sync
uv run coral start -c task.yaml
uv run coral status
uv run coral log
uv run coral ui
uv run coral stop
```

## 요구사항

- `uv` 설치
- Claude Code / Codex / OpenCode 중 하나 이상 설치 및 인증 완료
- grader(평가 스크립트) 준비
- task.yaml 작성

## OpenClaw / 루나 환경에 붙일 수 있는가?

### 결론
가능하다. 다만 **직접 통합 대상**이라기보다, **보조 실험 런타임**으로 쓰는 것이 적절하다.

### 이유
- 이미 루나/유나는 Codex / Claude 계열을 활용 중
- 멀티 에이전트 실험, 점수 기반 반복 개선, 공유 지식 구조가 현재 워크플로우와 잘 맞음
- 단, OpenClaw처럼 생활형 비서/메시징 허브 역할은 하지 않음

## 우리 환경에서 쓸만한 적용처

### 1. Oracle 튜닝 실험 자동화
- SQL / 스크립트 / 파라미터 조정
- grader로 실행 시간 / 성공 여부 / plan 품질 점수화
- Part 18 / Part 19 학습 및 실무 튜닝 사례에 적합

### 2. Luna Dashboard 리디자인 / 리팩토링
- 여러 에이전트가 각각 다른 UI 개선안 시도
- Lighthouse / 테스트 / 스냅샷 기준으로 비교 가능

### 3. 투자 / 백테스트 전략 실험
- 전략 후보 여러 개 자동 생성
- 수익률 / 샤프 / MDD 등으로 점수화
- 단, 비용 및 실수 위험 때문에 제한적 사용 권장

### 4. 루나-유나 협업 실험실
- 지금의 대화형 협업을 점수 기반 자동 경쟁 구조로 바꾸는 실험 가능

## 장점
- 멀티 에이전트 실험 구조가 명확함
- Codex / Claude Code / OpenCode 지원
- shared knowledge 설계가 괜찮음
- autoresearch / self-improvement 철학이 분명함

## 주의점
- OpenClaw처럼 개인 비서형 도구는 아님
- grader 설계가 핵심이라 세팅 품질에 따라 결과 차이 큼
- 잘못 쓰면 토큰/시간/비용 많이 듦
- 바로 전면 도입보다 **작은 파일럿**이 적절함

## 추천 도입 방식

### 권장
전면 도입 X

### 추천 파일럿
1. `oracle-sql-tuning-compass`
2. `Luna Dashboard` 일부 위젯/레이아웃 리팩토링

### 이유
- 점수 기준 만들기 쉬움
- 결과 비교가 명확함
- 실패해도 손해가 작음

## 최종 판단

CORAL은 **OpenClaw를 대체할 도구가 아니라**, 루나가 관리하는 환경에서
특정 프로젝트를 대상으로 **멀티 에이전트 자동 개선 실험**을 맡기기 좋은 도구다.

지금 기준으로는:
- OpenClaw 유지
- 필요 시 CORAL을 프로젝트 단위 실험 런타임으로 추가

이 방향이 가장 현실적이다.
