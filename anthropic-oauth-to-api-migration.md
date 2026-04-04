# Anthropic OAuth → API Key 마이그레이션 가이드

## 배경
- **2026-04-05 새벽 4시(KST)부터** Claude 구독으로 서드파티(OpenClaw 포함) 사용 불가
- OAuth 방식 → API Key 방식으로 전환 필요
- Anthropic에서 보상으로 $100 크레딧 지급 (4/17 만료)

## 현재 상태 (2026-04-04 22:34)

### 루나 (192.168.50.56)
```json
"anthropic:luna": {
  "provider": "anthropic", 
  "mode": "token"  // OAuth token
}
```
- 현재 모델: `anthropic/claude-sonnet-4-20250514`
- 상태: OAuth 방식, 마이그레이션 필요

### 유나 (192.168.50.192) 
```json
"anthropic:yuna": {
  "provider": "anthropic",
  "mode": "oauth"
}
```
- 상태: OAuth 방식, 마이그레이션 필요

## 마이그레이션 절차

### 1단계: API Key 발급
1. https://console.anthropic.com/settings/keys 접속
2. "Create Key" 클릭
3. Key name: "OpenClaw-Luna" / "OpenClaw-Yuna"
4. Key 복사 (`sk-ant-api03-...` 형태)

### 2단계: OpenClaw 설정 변경

#### 방법 A: CLI 명령어 (권장)
```bash
# 루나 서버에서
openclaw configure --section model

# 유나 맥북에서  
openclaw configure --section model
```

#### 방법 B: 수동 설정 변경
`~/.openclaw/openclaw.json` 편집:
```json
"anthropic:luna": {
  "provider": "anthropic",
  "mode": "api_key"  // token → api_key로 변경
}
```

### 3단계: 게이트웨이 재시작
```bash
openclaw gateway restart
```

### 4단계: 동작 확인
```bash
openclaw status
# 또는 새 세션에서 Anthropic 모델 사용해서 테스트
```

## 주의사항

### 타이밍
- **오늘 밤 늦게 (한도 초기화 후)** 진행
- 4/5 새벽 4시 이전에 완료 필요

### API Key vs OAuth 차이점
- OAuth: 구독 기반, 무제한 사용
- API Key: 종량제, 크레딧/결제 기반
- $100 크레딧으로 당분간 사용 가능

### 백업
- 변경 전 `openclaw.json` 백업
```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.bak.oauth
```

### 롤백 방법
문제 발생 시:
```bash
cp ~/.openclaw/openclaw.json.bak.oauth ~/.openclaw/openclaw.json
openclaw gateway restart
```

## 완료 체크리스트

- [ ] 루나: API Key 발급
- [ ] 유나: API Key 발급  
- [ ] 루나: openclaw.json 수정
- [ ] 유나: openclaw.json 수정
- [ ] 루나: 게이트웨이 재시작
- [ ] 유나: 게이트웨이 재시작
- [ ] 루나: 동작 확인
- [ ] 유나: 동작 확인
- [ ] memory/2026-04-04.md 업데이트

## 참고
- Claude Code 헤드 Boris Cherny 공식 발표
- Extra Usage Bundle 또는 종량제 API Key 방식만 지원
- 서드파티 앱 차단은 Anthropic 약관 위반 방지 차원