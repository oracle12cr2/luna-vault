# Codex plugin for Claude Code 참고 메모

- 원문: https://github.com/openai/codex-plugin-cc
- 확인일: 2026-04-11
- 저장 방식: 원문 미러 대신 요약/참고 메모만 보관
- 라이선스: Apache License 2.0

## 한줄 요약

Claude Code 안에서 Codex를 직접 불러서 코드 리뷰하거나 작업을 위임할 수 있게 해주는 공식 플러그인이다.

## 무엇을 해주나

- `/codex:review` : 일반 읽기 전용 코드 리뷰
- `/codex:adversarial-review` : 더 공격적으로 가정/설계를 의심하는 리뷰
- `/codex:rescue` : Codex에게 조사/수정 작업 위임
- `/codex:status` : 백그라운드 작업 상태 확인
- `/codex:result` : 완료 결과 확인
- `/codex:cancel` : 작업 취소
- `/codex:setup` : 설치/로그인/리뷰 게이트 상태 확인

## 설치 흐름

1. Claude Code에 plugin marketplace 추가
2. `codex@openai-codex` 플러그인 설치
3. 플러그인 reload
4. `/codex:setup` 실행
5. 필요 시 `codex login`으로 인증

## 핵심 개념

- Claude Code에서 작업하다가 일부 검토/수정/실험 작업을 Codex에 넘길 수 있음
- 백그라운드 작업 관리용 명령이 별도로 있어 긴 작업에도 맞음
- 로컬에 설치된 Codex CLI와 인증 상태를 그대로 사용함
- Codex 설정 파일(`~/.codex/config.toml`, `.codex/config.toml`)을 그대로 따름

## 대표 사용 예

- 현재 변경분을 Codex로 한 번 더 리뷰
- `main` 대비 브랜치 리뷰
- 실패 원인 조사 같은 탐색 작업을 Codex에 위임
- 작은 모델로 빠른 조사, 큰 모델로 정밀 검토 같은 분리 운영

## 주의할 점

- ChatGPT 구독 또는 OpenAI API 키가 필요할 수 있음
- 사용량은 Codex usage limits에 반영됨
- review gate는 유용하지만 Claude/Codex 루프가 길어져 사용량을 빨리 소모할 수 있음
- 실제 실행은 로컬 Codex CLI 기반이라, 로컬 환경과 인증 상태가 중요함

## 저장소 상태 메모

- 공개 저장소
- 생성: 2026-03-30
- 언어: JavaScript
- 라이선스: Apache-2.0
- 스타 수가 높고 반응이 커서 실사용 관심도가 높아 보임

## 우리 관점 메모

- Claude Code를 계속 쓰면서 Codex를 보조 reviewer/worker로 붙이는 용도로 꽤 실용적임
- 특히 리뷰 전용과 작업 위임 명령이 분리된 점이 좋음
- 다만 사용량/한도 관리가 중요해서 무조건 상시 활성화보다는 필요한 상황에만 쓰는 편이 안전함
