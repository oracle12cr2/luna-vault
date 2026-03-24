# AI싱크클럽 — 클로드 코드 관련 가이드 요점 정리

> 📖 출처: [AI싱크클럽 Notion](https://neighborly-wolfberry-308.notion.site/aisyncsource)
> 📝 정리: 유나 (2026-03-24)
> 🎬 유튜브: [AI싱크클럽](https://www.youtube.com/@AISyncClub)

---

## 목차

1. [클로드+MCP 설치 가이드](#1-클로드mcp-설치-가이드)
2. [클로드 코드 자동화 모드 (Autorun) 권한 세팅](#2-클로드-코드-자동화-모드-autorun-권한-세팅)
3. [15분 안에 Claude Skill 설정법](#3-15분-안에-claude-skill-설정법)
4. [Claude 개인 선호사항 설정](#4-claude-개인-선호사항-설정)
5. [클로드 AI 스킬 바이브코딩 가이드북](#5-클로드-ai-스킬-바이브코딩-가이드북)
6. [Claude Cowork 영상 자료](#6-claude-cowork-영상-자료)

---

## 1. 클로드+MCP 설치 가이드

> 🎬 [유튜브 영상](https://www.youtube.com/watch?v=CY00_dNfL8o)

### 사전 설치

| 항목 | 링크 |
|------|------|
| Claude 데스크톱 앱 | https://claude.ai/download |
| VSCode | https://code.visualstudio.com/ |
| Node.js | https://nodejs.org/ko |

### MCP 서버 설정 (config.json)

#### Perplexity MCP

```json
{
  "mcpServers": {
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": {
        "PERPLEXITY_API_KEY": "YOUR_API_KEY_HERE"
      }
    }
  }
}
```

- API 키 발급: https://www.perplexity.ai/account/api
- Pro 버전 사용자는 $5 보너스 제공

#### Notion MCP

```json
{
  "mcpServers": {
    "notionApi": {
      "command": "npx",
      "args": ["-y", "@notionhq/notion-mcp-server"],
      "env": {
        "OPENAPI_MCP_HEADERS": "{\"Authorization\": \"Bearer ntn_****\", \"Notion-Version\": \"2022-06-28\"}"
      }
    }
  }
}
```

- Integration 생성: https://www.notion.so/profile/integrations
- Integration 생성 후 API 토큰 발급
- 접근할 Notion 페이지/DB에 해당 Integration 연결 필요
- `ntn_****` 부분에 발급받은 토큰 입력

#### GitHub MCP 서버 목록

- 공식 MCP 서버 모음: https://github.com/modelcontextprotocol/servers

---

## 2. 클로드 코드 자동화 모드 (Autorun) 권한 세팅

### 권한 모드 (`settings.json`의 `defaultMode`)

| 모드 | 설명 | 사용 시기 |
|------|------|----------|
| `default` | 각 도구의 첫 사용 시 권한 요청 | 일반 사용 |
| `acceptEdits` | 세션 동안 파일 편집 자동 승인 | 신뢰할 수 있는 프로젝트 |
| `plan` | 분석만 가능, 파일 수정/명령 실행 불가 | 코드 리뷰, 계획 수립 |
| `bypassPermissions` | 모든 권한 프롬프트 건너뜀 | 안전한 격리 환경에서만 |

### Safe YOLO 모드 (완전 자동 실행)

```bash
claude --dangerously-skip-permissions
```

- 모든 권한 검사 우회
- Claude가 완료까지 중단 없이 작업
- **적합한 용도**: 린트 오류 수정, 보일러플레이트 코드 생성
- ⚠️ **주의**: 안전한 환경(Docker, VM 등)에서만 사용 권장

---

## 3. 15분 안에 Claude Skill 설정법

> 원본: Reddit u/chasing_next

### 9단계 가이드

1. **스킬 활성화 확인** — 설정 > 기능 > 스킬 이동, 활성화 확인
2. **"skill-creator" 스킬 켜기** — 다른 스킬을 자동으로 만들어주는 메타 스킬
3. **새 채팅에서 스킬 생성 요청** — "skill-creator 사용해서 새 스킬 만들어줘"
4. **원하는 스킬 구체적으로 설명** — 결과물, 형식, 규칙 등 상세 기술
5. **클로드가 스킬 파일 자동 생성** — 몇 가지 질문 후 완전한 파일 + 문서 생성
6. **사용법 문서 읽고 다운로드** — read-me 확인 후 스킬 파일 다운로드
7. **스킬 업로드 및 활성화** — 설정 > 기능 > 스킬 > 스킬 업로드, 토글 ON
8. **새 채팅에서 테스트** — 스킬 이름 언급하며 사용 요청
9. **필요시 수정/업데이트** — 원래 대화에서 수정 요청 → 재업로드

> 💡 **팁**: 이미 정기적으로 하는 간단한 반복 작업부터 시작하세요!

---

## 4. Claude 개인 선호사항 설정

### 설정 위치

**클로드 > 설정 > 프로필**

Claude가 응답할 때 기본적으로 고려하는 사항을 세팅하는 곳.

### 자기 점검 체크리스트

- [ ] 반복적으로 하는 작업인가?
- [ ] 특정한 형식이나 절차가 있는가?
- [ ] 매번 같은 설명을 반복하고 있는가?
- [ ] 일관된 결과물이 필요한가?

→ 하나라도 해당되면 스킬이나 선호사항으로 설정 권장

---

## 5. 클로드 AI 스킬 바이브코딩 가이드북

### 스킬이란?

- Claude의 기능을 확장하는 **모듈식 역량**
- 지시사항, 메타데이터, 선택적 리소스(스크립트, 템플릿)를 패키지로 묶음
- Claude가 관련 작업에 **자동으로** 사용

### 스킬의 핵심 장점

- 반복 설명 불필요 — 한 번 설정하면 자동 적용
- 일관된 결과물 보장
- 컨텍스트 효율적 사용 (점진적 공개 시스템)

### 3단계 점진적 공개 시스템

| 단계 | 동작 | 설명 |
|------|------|------|
| **1단계** | 시작 시 | 모든 스킬의 기본 정보(이름, 설명)를 미리 로드 |
| **2단계** | 필요 시 | 해당 스킬의 SKILL.md 본문(절차적 지식) 로드 |
| **3단계** | 복잡한 작업 시 | 번들된 파일들을 bash로 실행 (컨텍스트 부담 없음) |

### 스킬 파일 구조 (SKILL.md)

```yaml
---
name: "스킬 이름"        # 64자 최대
description: "스킬 설명"  # 1024자 최대
---
# 스킬 본문
(절차적 지식, 규칙, 템플릿 등)
```

- `name`과 `description`만 YAML frontmatter에서 지원
- 이 두 필드로 Claude가 어떤 스킬을 활성화할지 결정

### 스킬 작성 황금 법칙

1. **간결함이 핵심** — 컨텍스트 윈도우는 공공재, 다른 것들과 공유
2. **Claude가 이미 아는 건 쓰지 마라** — 모르는 컨텍스트만 추가
3. **description 최적화** — 어떤 작업에, 어떤 결과를, 어떤 형식으로

### 내장 스킬 4가지

| 스킬 | 기능 |
|------|------|
| **PowerPoint** | 프레젠테이션 생성, 슬라이드 편집, 콘텐츠 분석 |
| **Excel** | 스프레드시트 생성, 데이터 분석, 차트 보고서 |
| **Word** | 문서 생성, 콘텐츠 편집, 텍스트 형식 지정 |
| **PDF** | 형식화된 PDF 문서와 보고서 생성 |

### 실전 비즈니스 스킬 예시 5가지

1. **데이터 인사이트 자동화** — 데이터 분석 결과 자동 리포트
2. **수익 예측 (Revenue Forecasting)** — 매출 데이터 기반 예측
3. **회의록 문서 생성** — 일관된 형식의 회의록 자동화
4. **파이프라인 분석기 (Pipeline Doctor)** — 영업 파이프라인 분석
5. **피치 덱 생성기 (Pitch Wizard)** — 투자 발표 자료 자동 생성

### 문제 해결 팁

- **스킬이 활성화 안 될 때** → description 확인, 키워드 매칭
- **결과물 품질 낮을 때** → 본문에 구체적인 예시/규칙 추가
- **컨텍스트 부족** → 번들 파일로 분리, 점진적 로드 활용
- **모든 모델에서 테스트** → Sonnet/Opus 등 다른 모델 호환성 확인

### Skills vs MCP 비교

| 항목 | Skills | MCP |
|------|--------|-----|
| **역할** | Claude의 행동 방식 정의 | 외부 도구/데이터 연결 |
| **비유** | 직원의 업무 매뉴얼 | 직원이 쓰는 도구 |
| **설정** | SKILL.md 파일 업로드 | config.json 서버 설정 |
| **실행** | Claude 내부에서 자동 | 외부 서버 호출 |
| **조합** | Skills + MCP = 최강 조합 | |

---

## 6. Claude Cowork 영상 자료

| 자료 | 내용 |
|------|------|
| **검증된 프롬프트 15선** | 실전에서 검증된 Claude 협업 프롬프트 모음 |
| **회의록 완벽 템플릿** | Claude를 활용한 회의록 작성 템플릿 |
| **실패 사례 & 해결법** | 흔한 실수와 해결 방법 정리 |
| **시작 전 체크리스트** | Claude Cowork 세팅 전 확인사항 |

---

## 부록: PRD 생성 프롬프트

- **PRD 샘플 템플릿** 제공 (한국어/영어 버전)
- Claude에게 PRD(Product Requirements Document) 자동 생성 요청 가능
- [상세 페이지](https://neighborly-wolfberry-308.notion.site/PRD-2649fdd0a7e280c6bc46dc8a5e4cbdb6)

---

## 참고 링크

- [Claude 공식 Skills 문서](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview)
- [Claude Skills 모범 사례](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices)
- [MCP 서버 공식 목록](https://github.com/modelcontextprotocol/servers)
- [Cursor Rules 모음](https://cursor.directory/)
