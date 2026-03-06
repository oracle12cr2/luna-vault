# Claude Code 풀 가이드 요약

> 출처: 유튜브 라이브 (https://www.youtube.com/watch?v=JCMMWZBuYjA)

## 1. 설치 & 결제

### 결제 플랜
- **Pro ($20/월)**: 웹/데스크탑에서 리서치용으로는 OK, 코딩하기엔 부족
- **Max ($100/월)**: 코딩하려면 최소 이거. 추천
- **Max 20x ($200/월)**: 헤비 유저용. 주간 사용량 많으면 업그레이드
- 5시간 단위 세션 사용량 + 주간 한도가 있음

### 설치 방법
- **Mac**: `brew install claude-code` (Homebrew)
- **Windows**: WSL2 권장, 또는 VS Code 내장 터미널
- **공통**: `curl` 방식으로도 설치 가능

### 로그인
- `claude` 실행 후 `/login`
- 3가지 옵션:
  1. **Account Subscription** (구독형) ← 일반 사용자 추천
  2. **Console Account** (API 키, 종량제) — 서비스 환경용
  3. **Third-party** (AWS Bedrock, Azure, Vertex AI)

## 2. 초기 세팅

### `/init` — 프로젝트 초기화
- 프로젝트 폴더에서 `claude` 실행 후 `/init`
- 프로젝트 구조를 분석해서 `CLAUDE.md` 자동 생성
- CLAUDE.md = 프로젝트 맥락 파일 (AI가 참고하는 설명서)

### Superpowers 스킬 설치 (핵심!)
- GitHub에서 Superpowers 주소 복사
- Claude Code에게 "이 스킬을 전역으로 설치해줘" 라고 요청
- **전역(Global)**: 모든 프로젝트에서 사용 가능 (내 PC 전체)
- **프로젝트**: 해당 프로젝트에서만 사용 (git으로 공유 가능)
- Superpowers Brainstorming → 기획/설계를 AI가 도와줌

## 3. 핵심 워크플로우

### 기본 흐름
1. 프로젝트 폴더에서 `claude` 실행
2. `/init`으로 CLAUDE.md 생성
3. Superpowers Brainstorming으로 기획
4. AI와 대화하며 설계 문서 생성 (PRD)
5. 구현 → 테스트 → 피드백 반복

### 권한 모드
- **기본**: 파일 생성/실행마다 승인 필요 (Yes/Allow)
- **Bypass 모드**: `claude --dangerously-skip-permissions` → 자동 승인
- ESC로 취소 가능

### 터미널 팁
- `!` 치면 bash 모드 → 터미널 명령어 직접 실행
- Cmd+클릭으로 파일 열기
- Ctrl+C 두 번 → 종료

## 4. 주요 기능

### 모델 선택
- **Opus**: 최고 성능, 복잡한 작업용
- **Sonnet**: 가성비 좋음, 버그 수정/코드 작성
- **Haiku**: 간단한 작업, 파일 시스템 조작

### Sub-agent (서브 에이전트)
- `spawn`으로 병렬 작업 분배
- 예: 업로드 페이지 + 프로필 페이지 동시 개발
- 토큰 사용량 많아짐

### Agent Team (에이전트 팀) — 신기능
- 서브 에이전트를 팀으로 구성
- 에이전트별로 다른 모델 선택 가능 (Opus/Sonnet 혼용)
- 에이전트끼리 대화/합의 가능

### Worktree (워크트리) — 신기능
- Git worktree 기반 병렬 개발
- 브랜치별로 격리된 작업 → 코드 충돌 방지
- `claude worktree`로 실행
- 서브 에이전트와 조합하면 병렬 개발 시 충돌 없음

### 1M Context (100만 토큰 컨텍스트)
- 긴 대화/복잡한 작업 시 컨텍스트 유지
- 컨텍스트 초과 시 자동 compact → 맥락 압축 후 새 세션

### 기타 슬래시 명령어
- `/chrome` — 크롬 확장으로 웹페이지 읽기/스크린샷
- `/compact` — 컨텍스트 압축
- `/config` — 설정
- `/copy` — 대화 내용 클립보드 복사
- `/cost` — 사용량 확인
- `/hooks` — 자동화 훅 설정
- `/memory` — 메모리 관리 (스킬과 유사)
- `/model` — 모델 변경

## 5. 학습 팁

### AI로 공부하기
- 문서/GitHub 링크를 Claude에게 먹이기
- "이 링크 확인하고 [주제]에 대해 설명해줘"
- 모르는 건 직접 읽지 말고 AI에게 물어보기

### 핵심 포인트
1. **기획이 중요** — AI 코딩의 성패는 기획 품질
2. **두려워하지 말고 물어보기** — LLM에게 질문
3. **오픈소스/문서 먹이기** — GitHub, 공식 문서 등
4. **스킬 활용** — Superpowers 같은 스킬로 워크플로우 강화
5. **병렬 작업** — 서브 에이전트 + 워크트리로 효율화

## 6. 사용량 관리

- 설정 → 사용량에서 확인
- **세션 사용량**: 5시간마다 초기화
- **주간 한도**: 매주 결제 시점 기준 초기화
- 토큰 절약: Sonnet 활용, 불필요한 작업 줄이기
