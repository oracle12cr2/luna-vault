# Codex plugin for Claude Code 설치/테스트 로그 (2026-04-11)

- 대상 환경: 루나 서버
- 작업일: 2026-04-11
- 관련 저장소: https://github.com/openai/codex-plugin-cc

## 목적

Claude Code 안에서 Codex 플러그인이 실제로 설치되고, 리뷰/위임 명령이 정상 동작하는지 확인한다.

## 설치 결과

- Claude Code 설치 확인: `2.1.98`
- Codex CLI 설치 확인: `0.118.0`
- Node.js: `v22.22.0`
- npm: `10.9.4`
- 플러그인 설치 완료: `codex@openai-codex`
- 설치 버전: `1.0.3`
- 상태: `enabled`

## Claude 내부 확인 결과

`/reload-plugins` 후 `/codex:setup` 실행 결과:

- Node.js 정상
- npm 정상
- Codex CLI 정상
- Auth: `API key configured`
- Runtime: `Direct mode (starts on demand)`
- Review gate: `Disabled`
- 결론: Codex is installed and authenticated

## 테스트 1 - 잘못된 위치에서 review 실행

위치: `/root`

결과:
- `/codex:review --background` 실패
- 원인: 현재 디렉토리가 Git repository가 아니어서 diff 대상이 없음

교훈:
- `/codex:review` 는 반드시 `.git` 이 있는 repo 디렉토리에서 실행해야 함

## 테스트 2 - repo 안에서 review 실행

위치: `/root/.openclaw/workspace/luna-vault`

결과:
- `/codex:review --background` 정상 실행
- 다만 워킹 트리가 clean 상태여서 `There are no code changes relative to the provided merge base commit` 메시지 반환

교훈:
- 변경사항이 없으면 Codex review는 정상 동작해도 actionable issue 없이 종료됨

## 테스트 3 - 문서 1줄 변경 후 review 실행

테스트 파일:
- `references/codex-plugin-cc.md`

방법:
- 문서에 테스트 메모 1줄 추가
- `git diff`로 변경분 확인
- Claude 안에서 `/codex:review --wait` 실행
- 이후 `git checkout -- references/codex-plugin-cc.md` 로 원복

결과:
- Target: `working tree diff`
- Codex 판단: 문서 1줄 추가만 존재하며 기능/보안/유지보수 이슈 없음
- 결론: 실제 변경분 기준 review 정상 확인

## 테스트 4 - rescue 명령 실행

예시 명령:
- `/codex:rescue investigate this repository structure and suggest the safest first improvement`

결과:
- rescue subagent 정상 동작
- 첫 제안: workspace 루트 `.gitignore` 정리
- 제안 요지: transient/untracked artifact 노이즈를 줄여 accidental commit 위험 감소

## 최종 결론

Codex plugin for Claude Code는 루나 서버에서 정상 설치 및 사용 가능하다.

확인된 항목:
- 플러그인 설치 정상
- Codex CLI 연동 정상
- 인증 정상
- review 명령 정상
- rescue 명령 정상
- 실제 변경분 review 정상

## 실사용 메모

- review는 repo 안에서만 실행
- 테스트 시에는 먼저 `git diff`가 실제로 존재하는지 확인
- 작은 변경은 `/codex:review --wait` 가 헷갈림이 적음
- 긴 작업이나 탐색 작업은 `/codex:rescue --background` 계열이 적합
- review gate는 사용량 소모가 클 수 있으므로 평소에는 비활성 유지 권장
