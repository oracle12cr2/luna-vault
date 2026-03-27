# AI 도구 리서치 정리 (2026-03-27)

## 1. Playwright MCP — Claude Code 브라우저 자동화

### 개요
Claude Code에서 Playwright MCP를 연결하면 브라우저 자동화(페이지 탐색, 스크린샷, 클릭, 폼 입력, E2E 테스트) 가능.

### 설치
```bash
npm install -g @playwright/mcp@latest
npx playwright install chromium

# 시스템 의존성 (RHEL/Rocky)
dnf install -y nss atk at-spi2-atk cups-libs libdrm libXcomposite libXdamage libXrandr mesa-libgbm pango alsa-lib libxkbcommon
```

### Claude Code 설정 (`~/.claude/settings.json`)
```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["@playwright/mcp", "--headless"]
    }
  }
}
```

### 활용
- 웹 UI 테스트 자동화
- 웹 스크래핑 (JS 렌더링 필요한 사이트)
- E2E 테스트 코드 생성

### 참고
- 원본: [바이브코딩파티 Day 17](https://vibecoding-newsletter.netlify.app/newsletters/day-17/email)
- Playwright MCP 공식: [@playwright/mcp](https://www.npmjs.com/package/@playwright/mcp)

---

## 2. NemoClaw — OpenClaw + Nvidia OpenShell 샌드박스

### 개요
OpenClaw을 Nvidia OpenShell 컨테이너 안에서 실행. API 키 격리, 정책 기반 접근 제어, 네트워크 화이트리스트 방식 보안.

### 아키텍처
```
브라우저/텔레그램 → 방화벽 → Caddy(HTTPS) → OpenShell 샌드박스 → OpenClaw
                                                ├─ Landlock FS 격리
                                                ├─ seccomp 시스콜 필터
                                                └─ 네트워크 화이트리스트
```

### 맥북 설치 (Intel/Apple Silicon)
상세 가이드: [`docs/nemoclaw-macbook-setup.md`](./nemoclaw-macbook-setup.md)

핵심 차이 (VPS vs 맥북):
| 항목 | VPS | 맥북 |
|------|-----|------|
| Docker | 직접 설치 | Colima 경유 |
| 유저 격리 | root | 전용 비관리자 계정 (2중 보안) |
| 리버스 프록시 | Caddy + 서브도메인 | localhost / Tailscale |
| 자동 시작 | systemd | launchd (plist) |
| 비용 | ~$10/월 | 무료 |

### 참고 링크
- 공식 문서: https://docs.nvidia.com/nemoclaw/latest/
- GitHub: https://github.com/NVIDIA/NemoClaw
- Mac Mini 가이드: https://github.com/bcharleson/nemoclaw-macmini-setup
- 영상: https://www.youtube.com/watch?v=dEL9tKwvejo

---

## 3. Agent Salad — OpenClaw GUI 래퍼

### 개요
설정 파일 없이 드래그 앤 드롭으로 AI 에이전트를 만들어서 텔레그램/디스코드/슬랙에 연결하는 데스크톱 앱.

### 구조
**에이전트 + 채널 + 타겟** 3개 조합 = "샐러드🥗"
- 에이전트: LLM 선택 (Claude, GPT, Gemini) + 역할 정의
- 채널: 텔레그램/디스코드/슬랙 봇 토큰
- 타겟: 개인 DM 또는 그룹

### 내장 스킬 10개
파일 R/W, 웹 Fetch, Playwright 브라우저, Bash, Gmail, Google Calendar/Drive, 크론

### 평가
비개발자/입문자용. 파워유저에게는 OpenClaw 직접 운영이 더 자유도 높음.

### 링크
- https://terry-uu.github.io/agentsalad/

---

## 4. Claude Desktop Computer Use

### 개요
클로드가 스크린샷을 찍고 → 분석 → 마우스/키보드로 직접 컴퓨터 조작. 모르는 앱도 화면 보고 알아서 사용.

### 4가지 도구 우선순위
| 순위 | 도구 | 방식 | 속도 | 용도 |
|------|------|------|------|------|
| 1 | API 커넥터 | 서비스 직접 연결 | ⚡ 최고 | Slack, Calendar, Notion |
| 2 | 터미널 | 명령어 실행 | ⚡ 빠름 | 파일, 코드, 시스템 |
| 3 | 크롬 MCP | HTML 구조 읽기 | 🔵 보통 | 웹사이트 조작 |
| 4 | Computer Use | 스크린샷→판단 | 🐌 느림 | GUI 전용 앱 (만능) |

### 크롬 MCP vs Computer Use
- 크롬: HTML 설계도를 **읽어서** 버튼 위치를 안다 → 빠르고 정확
- Computer Use: 화면을 **찍어서** 버튼 위치를 본다 → 느리지만 범위 무제한

### 활성화
```
Claude Desktop → Settings → Desktop app → General → Computer Use → ON
```
⚠️ 현재 Mac만 지원, Windows 미지원 (2026-03-27 기준)

### 참고
- https://www.youtube.com/watch?v=9_W05UyYXZI
- https://www.youtube.com/watch?v=7iTAkIPZzIw

---

## 5. Claude Code 에이전트 영상 제작 자동화

### 개요
Claude Code 스킬로 `/create-video 주제` 입력 → 7개 에이전트 순차 실행 → 영상 1편 완성 (9시간→30분)

### 파이프라인
| # | 에이전트 | 역할 | 모델 | 승인 |
|---|---------|------|------|------|
| 1 | 리서처 | 유튜브/뉴스/블로그 병렬 검색 → 소스.md | - | 자동 |
| 2 | 스크립트라이터 | 소스 + 캐릭터 가이드 → 씬별 대본 | Opus | ✅ |
| 3 | 서브타이틀 엔지니어 | 대본 → SRT 자막 | - | 자동 |
| 4 | 보이스 엔지니어 | 대본 → TTS 음성 (목소리 클론) | - | ✅ |
| 5 | 씬 디자이너 | 씬 → React 컴포넌트 (Remotion) | Opus | ✅ |
| 6 | 렌더러 | React + 보이스 → 최종 영상 | - | 자동 |
| 7 | QA 리뷰어 | 26개 체크리스트 검수 | Opus | ✅ |

### 핵심 개념: 하네스(Harness)
에이전트가 엉뚱하게 안 가도록 방향 잡아주는 장치:
- 역할 정의 + 입출력 형식
- Do/Don't 규칙
- 캐릭터 가이드 (채널 톤앤매너)
- 스타일.json (색상, 폰트, 모션)
- 승인 게이트

### 기술 스택
- **Remotion** — React 컴포넌트로 영상 생성 (코드 = 영상)
- **TTS Studio** — 로컬 TTS (목소리 클론)
- **Claude Code 스킬** — 오케스트레이터

### 참고
- https://www.youtube.com/watch?v=vLbzl5u5iwM
- Remotion: https://www.remotion.dev/
