# Lessons Learned — 패턴 & 교훈 저장소

> ECC의 Instinct 개념을 우리 환경에 맞게 적용한 학습 시스템

## 구조

각 교훈은 개별 마크다운 파일로 저장:

```
memory/lessons/
├── README.md (이 파일)
├── oracle-rac-patch.md
├── cron-python-path.md
└── ...
```

## 파일 포맷

```markdown
---
trigger: "어떤 상황에서 이 교훈이 적용되는지"
domain: "oracle | python | infra | git | linux | web | stock"
confidence: ✅ 확실 | ⚠️ 조건부 | ❌ 폐기
created: YYYY-MM-DD
updated: YYYY-MM-DD
---

# 제목

## 문제
구체적으로 무슨 문제가 발생했는지

## 원인
왜 그런 일이 일어났는지

## 해결
어떻게 고쳤는지 (명령어, 코드 포함)

## 교훈
다음에 같은 상황이면 이렇게 하라
```

## 규칙

- **사소한 건 기록하지 않기** (오타, 일회성 이슈)
- **재현 가능한 패턴만** — 다음에도 만날 가능성이 있는 것
- **하나의 교훈 = 하나의 파일** — 검색 용이
- **주간 리뷰** — MEMORY.md에 반영할 것 선별
