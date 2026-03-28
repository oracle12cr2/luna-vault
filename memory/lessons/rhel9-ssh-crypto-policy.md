---
trigger: "RHEL9/OL9에서 SSH 접속 시 키 인증 실패"
domain: linux
confidence: ✅
created: 2026-03-11
updated: 2026-03-11
---

# RHEL9 crypto-policies가 ssh-rsa(SHA1) 차단

## 문제
기존 ssh-rsa 키로 RHEL9/OL9 서버 접속 시 인증 거부

## 원인
RHEL9의 crypto-policies가 SHA1 기반 알고리즘 기본 차단

## 해결
ed25519 키 생성 및 사용:
```bash
ssh-keygen -t ed25519
```

## 교훈
RHEL9 이상 서버에는 ed25519 키 사용. ssh-rsa는 더 이상 기본 지원 안 됨.
