# star-cliproxy 설정 로그 (2026-04-04)

## 배경
- Codex 한도 소진, Anthropic OAuth 4/5 새벽 4시 차단 예정
- star-cliproxy를 통해 Claude CLI를 OpenAI-compatible API로 프록시
- API 서버: http://192.168.50.56:8300 (루나 서버)

## 유나 적용 과정

### 1. openclaw.json에 provider 추가

`models.providers`에 star-cliproxy 등록:
```json
"star-cliproxy": {
  "baseUrl": "http://192.168.50.56:8300/v1",
  "apiKey": "sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a",
  "api": "openai-completions",
  "models": [
    {
      "id": "claude-sonnet",
      "name": "claude-sonnet (star-cliproxy)",
      "reasoning": false,
      "input": ["text"],
      "cost": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
      "contextWindow": 200000,
      "maxTokens": 8192
    }
  ]
}
```

### 2. model 설정 변경

`agents.defaults.model`:
```json
{
  "primary": "star-cliproxy/claude-sonnet",
  "fallbacks": ["anthropic/claude-sonnet-4-6"]
}
```

### 3. credentials 파일 생성

`~/.openclaw/credentials/openai-star-cliproxy-default.json`:
```json
{"apiKey": "sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a"}
```

### 4. 게이트웨이 재시작
```bash
export PATH=/opt/homebrew/bin:$PATH
openclaw gateway restart
```

## 삽질 기록 (주의사항!)

### ❌ auth.profiles에 baseUrl 넣으면 안 됨
```json
// 이렇게 하면 에러!
"star-cliproxy:default": {
  "provider": "openai",
  "mode": "api_key",
  "baseUrl": "http://..." // ← Unrecognized key
}
```

### ❌ api 값은 "openai" 안 됨
```
"api": "openai"  // ← Invalid option
```
허용 값: `openai-completions`, `openai-responses`, `openai-codex-responses`, `anthropic-messages`, `google-generative-ai`, `github-copilot`, `bedrock-converse-stream`, `ollama`, `azure-openai-responses`

### ❌ Claude CLI root 권한 + bypassPermissions 안 됨
```
--permission-mode bypassPermissions → root에서 보안상 거부
```
해결: `--permission-mode auto`로 변경 (star-cliproxy config.yaml)

## 검증 완료 (23:18 KST)
- star-cliproxy API 로그에서 유나 요청 확인
- 유나 디스코드에서 정상 응답 확인
- primary: star-cliproxy/claude-sonnet → Claude CLI → Anthropic

## 루나 적용
- 루나는 안정성 우선으로 기존 Anthropic 직접 연결 유지 중
- 같은 방식으로 적용 가능 (models.providers 방식)
- 기존에 auth.profiles 방식으로 시도했다가 게이트웨이가 model 설정을 리셋해버린 전적 있음
