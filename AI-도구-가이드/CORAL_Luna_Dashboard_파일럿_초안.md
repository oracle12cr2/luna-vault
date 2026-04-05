# CORAL Luna Dashboard 파일럿 초안

## 목표

CORAL을 OpenClaw/루나 환경의 **보조 실험 런타임**으로 사용해,
Luna Dashboard의 특정 UI/위젯 개선 작업을 멀티 에이전트 방식으로 자동 탐색한다.

## 왜 Dashboard부터 시작하나?

- 결과 확인이 빠름
- build 성공/실패가 명확함
- 시각적 개선 여부를 비교하기 쉬움
- Oracle 튜닝 실험보다 위험이 낮음
- 현재 실제로 자주 수정 중인 프로젝트임

## 파일럿 범위

### 범위 포함
- 홈 대시보드 위젯 레이아웃 개선
- 카드 간격 / 밀도 / 정렬 개선
- 위젯 정보 구조 개선
- 특정 위젯의 시각적 가독성 개선
- 불필요한 카드 제거/재배치 제안

### 범위 제외
- 인증 로직 변경
- WebSocket / Gateway 구조 변경
- 외부 API 인증 체계 변경
- 운영 DB 스키마 변경
- 서버/인프라 직접 조작

## 성공 기준

### 필수
1. `npm run build` 성공
2. 런타임 치명적 에러 없음
3. 기존 핵심 기능 유지
   - `/dashboard` 진입 가능
   - 주요 카드 렌더링 가능
4. 수정 diff가 이해 가능하고 과도하지 않을 것

### 추가 점수
- 레이아웃이 더 직관적임
- 시각적 밀도 개선
- 중복 정보 감소
- 유지보수성 개선

## 추천 에이전트 설정

### 기본
- runtime: `codex`
- count: `2~3`
- model: 현재 Codex 기본 모델 사용

### 이유
- 빠르고 반복 실험에 적합
- 현재 루나 환경과 잘 맞음
- 비용 통제가 비교적 쉬움

### 선택적 폴백
- `claude_code`
- 설명/구조 재정리/문서화에 강점

## 권장 실험 방식

### Round 1
주제:
- 홈 카드 배치 개선
- 비어 있거나 가치 낮은 카드 제거
- 카드 크기 균형 재조정

### Round 2
주제:
- 특정 카드 시각 디자인 개선
- typography / spacing / hierarchy 정리

### Round 3
주제:
- 정보 밀도 최적화
- 자주 보는 정보 우선 노출

## grader 아이디어

### 1. Build grader
- `npm run build` 성공 여부
- 실패 시 즉시 0점

### 2. Smoke test grader
- `/dashboard` 접근 가능
- HTML 기본 렌더 확인
- 특정 핵심 텍스트 존재 여부 확인

### 3. Diff sanity grader
- 변경 파일 수 제한
- 인증/API/인프라 파일 수정 시 감점
- `components/dashboard.tsx` / UI 컴포넌트 중심 수정 가점

### 4. Optional heuristic grader
- 카드 수 과도 감소 시 감점
- 치명적 import 오류/undefined 참조 감점

## task.yaml 초안 예시

```yaml
task:
  name: luna-dashboard-ui-pilot
  description: |
    Improve the Luna Dashboard homepage layout and widget composition.
    Keep the dashboard functional and buildable.
    Focus on layout clarity, spacing, hierarchy, and practical usefulness.
    Do not modify authentication, gateway, websocket, or infrastructure logic.

grader:
  type: function
  module: eval.grader

agents:
  count: 2
  runtime: codex
  model: gpt-5.4
  max_turns: 80

workspace:
  results_dir: ./results
  repo_path: ./seed
```

## grader.py 초안 방향

```python
from coral.grader import TaskGrader, ScoreBundle

class Grader(TaskGrader):
    def evaluate(self):
        build = self.run_program("build.sh")
        if build.returncode != 0:
            return self.fail("build failed")

        smoke = self.run_program("smoke.sh")
        if smoke.returncode != 0:
            return self.fail("smoke test failed")

        return 1.0
```

## smoke.sh 예시 아이디어

- build output 존재 확인
- `/dashboard` 렌더 확인
- 핵심 문자열 존재 확인
  - `LUNA & YUNA DASHBOARD`
  - `루나 시스템`
  - `DB 모니터`

## 운영 원칙

- OpenClaw가 메인 허브 역할 유지
- CORAL은 장기 실험 작업만 담당
- 운영 반영은 사람이 최종 승인
- 대시보드 본 서비스에 바로 적용하지 말고, 별도 seed/workspace에서 검증 후 반영

## 리스크

- UI는 정량 평가가 어려움
- grader가 너무 약하면 품질 낮은 결과 통과 가능
- 대시보드처럼 현재 진행 중인 프로젝트는 기준선이 자주 바뀔 수 있음

## 최종 추천

첫 파일럿은 **Luna Dashboard의 홈 레이아웃 개선**으로 제한한다.

이유:
- 위험 낮음
- 결과 비교 빠름
- CORAL이 실제로 유용한지 검증 가능
- 실패해도 복구 부담이 작음

이 파일럿이 괜찮으면 다음 단계로:
1. 위젯별 리팩토링
2. 블로그 프론트 UI 개선
3. Oracle SQL 튜닝 실험 자동화
순으로 확장하는 것이 적절하다.
