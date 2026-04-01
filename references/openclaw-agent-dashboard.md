# OpenClaw 에이전트 대시보드 & 시각화 프로젝트

> 출처: [코딩 없이 오픈클로 에이전트 직원 5명 굴리는 200% 활용법](https://www.youtube.com/watch?v=vPzM2ix4ApM) (2026-04-01)

## 📺 영상 요약

마케팅 업무를 4개 서브에이전트(카피라이터, 전략가, 리서처, 소셜미디어)로 분리하고 메인 에이전트가 오케스트레이션하는 구조.
바이브 코딩(Cursor + Composer 2)으로 에이전트 대시보드를 처음부터 구축하는 라이브 데모.

### 핵심 포인트
- 구축/스캐폴딩은 **싼 모델(Composer 2)로 충분** — 복잡한 로직만 GPT 5.4/Claude
- OpenClaw 폴더를 워크스페이스에 추가 → 참조용으로 활용
- **게이트웨이 Web RPC**로 실제 에이전트 연결 (토큰/인증 자동화)
- 이미지 레퍼런스 + 프롬프트만으로 프론트엔드 생성 가능 (비개발자 OK)

## 🔗 GitHub 레포지토리

### 1. Star Office UI (⭐6.4k) — 픽셀아트 에이전트 오피스
- **URL:** https://github.com/ringhyacinth/Star-Office-UI
- **설명:** A pixel office for your OpenClaw — 에이전트 상태를 픽셀 사무실로 시각화
- **스택:** HTML
- **특징:** 캐릭터, 대기실, 일일 노트, 게스트 에이전트

### 2. Claw3D (⭐1,035) — 3D 에이전트 오피스
- **URL:** https://github.com/iamlukethedev/Claw3D
- **설명:** 3D workspace for AI agents — React + Three.js
- **제작자:** LukeTheDev (@iamlukethedev)
- **특징:** 실시간 에이전트 모니터링, 스탠드업, PR 리뷰, QA 파이프라인, 스킬 트레이닝
- **구조:** OpenClaw = 인텔리전스 레이어, Claw3D = 시각화 레이어

### 3. OpenClaw Office — WW-AI-Lab (⭐480)
- **URL:** https://github.com/WW-AI-Lab/openclaw-office
- **설명:** OpenClaw 멀티에이전트 시스템 모니터링/관리 프론트엔드
- **스택:** TypeScript, WebSocket
- **특징:** 게이트웨이 WebSocket 연결, 에이전트 협업 시각화, 콘솔 관리

### 4. Cube Pets Office (⭐51)
- **URL:** https://github.com/opencroc/cube-pets-office
- **설명:** 큐브 펫 스타일 픽셀 오피스 — CEO/매니저/워커 동적 조립
- **스택:** TypeScript

### 5. Claw3D Skill (⭐61)
- **URL:** https://github.com/makermate/claw3d-skill
- **설명:** Claw3D를 OpenClaw 스킬로 설치 가능한 패키지

## 🎯 우리 프로젝트 적용

### Luna Dashboard (HEARTBEAT.md 대기열)
- Star Office UI 또는 Claw3D를 베이스로 커스텀 가능
- OpenClaw 게이트웨이 Web RPC 연결은 이미 지원됨
- 인프라 미니맵 (완료) + 에이전트 회의실 (재설계 완료) 와 통합 검토

### 참고 사항
- 영상에서 사용한 모델: Cursor Composer 2 (가성비 모델)
- 프론트엔드 기본 구조: Next.js + 네비게이션(에이전트/상태 메뉴)
- 백엔드 연결: OpenClaw Office 레포 참조 → Web RPC 인증 자동화
