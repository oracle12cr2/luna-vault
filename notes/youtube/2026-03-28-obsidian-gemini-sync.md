# 옵시디언 Gemini Sync 플러그인 — 내 노트로 AI 대화

> 출처: https://www.youtube.com/watch?v=-mi6uplokrc

## 핵심 개념
- 옵시디언 노트를 Gemini API로 임베딩
- **내 노트만** 소스로 AI 대화 (웹 검색 X)
- 결과물에 원본 노트 링크 자동 첨부 → 출처 추적

## 워크플로우
1. 노트 폴더 선택 → Gemini Sync 임베딩
2. 프롬프트 입력 (예: "30분 강의안 작성해줘")
3. 내 노트 기반 초안 생성 (원본 링크 포함)
4. Claude Code로 웹서치 근거 보강
5. PDF 익스포트 → PPT/마인드맵 변환 가능

## 설치 방법
1. BRAT 플러그인 설치
2. Add Beta Plugin → `reallygood83/omg-search`
3. 설정에서 Gemini API 키 입력
4. 모델: Gemini 2.5 Flash / Flash Lite 권장
5. 싱크 설정: 전체 또는 특정 폴더 선택
6. Auto Sync 활성화 → 노트 편집 시 자동 재싱크

## 주요 기능
- 폴더별 선택 싱크
- Auto Sync (노트 추가/편집 시 자동)
- Force Full Sync / Clear
- Create New Note (결과물 → 새 노트 저장)
- 각 항목에 원본 노트 링크 자동 첨부

## 참고
- API 무료 정책 엄격해짐 → 유료 계정 권장
- 토큰 절약: 원본 전체 대신 초안만 전달
- luna-vault 노트에도 적용 가능 (유튜브 요약, lessons, 매매 분석 등)
