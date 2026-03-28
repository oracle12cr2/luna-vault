---
trigger: "cron에서 Python 스크립트 실행 시 PATH 문제"
domain: python
confidence: ✅
created: 2026-03-12
updated: 2026-03-12
---

# cron 환경 Python 절대경로 필수

## 문제
crontab에 등록한 Python 스크립트가 실행 안 됨

## 원인
`#!/usr/bin/env python3`은 사용자 PATH에 의존하는데, cron은 최소 PATH만 가짐
→ anaconda/venv의 python3을 찾지 못함

## 해결
shebang을 절대경로로 변경:
```bash
#!/home/anaconda3/bin/python3
```

## 교훈
cron용 스크립트는 **항상 절대경로 shebang** 사용. `env python3` 쓰지 말 것.
