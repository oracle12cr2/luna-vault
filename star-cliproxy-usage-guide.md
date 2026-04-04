# star-cliproxy 사용 가이드

## 설치 정보
- **API 서버**: http://192.168.50.56:8300
- **대시보드**: http://192.168.50.56:5300 (현재 장애)
- **상태**: star-cliproxy-api.service 정상, dashboard 오류

## 인증
- **API Key**: `sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a`
- **Admin Token**: `ccb8d9f454c352d167f03a8ba52aae780c3aa84cb074a80dba5acb57cb3943c7`

## 사용 가능 모델

### 정상 동작
- **claude-sonnet**: claude-sonnet-4-6 (✅ 테스트 완료)

### 문제 있음
- **gpt-5.4**: Codex CLI 오류 (한도 차서 실패)
- **gpt-5.3-codex**: 동일하게 오류 예상
- **gpt-5.4-mini**: 동일하게 오류 예상

## API 사용법

### cURL 예제
```bash
curl -X POST \
  -H "Authorization: Bearer sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "claude-sonnet",
    "messages": [
      {"role": "user", "content": "안녕하세요!"}
    ],
    "max_tokens": 1000
  }' \
  http://192.168.50.56:8300/v1/chat/completions
```

### Python 예제
```python
import requests

headers = {
    "Authorization": "Bearer sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a",
    "Content-Type": "application/json"
}

data = {
    "model": "claude-sonnet",
    "messages": [
        {"role": "user", "content": "안녕하세요!"}
    ],
    "max_tokens": 1000
}

response = requests.post(
    "http://192.168.50.56:8300/v1/chat/completions", 
    headers=headers, 
    json=data
)
print(response.json())
```

### OpenAI SDK 호환
```python
from openai import OpenAI

client = OpenAI(
    api_key="sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a",
    base_url="http://192.168.50.56:8300/v1"
)

response = client.chat.completions.create(
    model="claude-sonnet",
    messages=[
        {"role": "user", "content": "안녕하세요!"}
    ],
    max_tokens=1000
)
print(response.choices[0].message.content)
```

## OpenClaw 연동 방법

### ✅ 설정 완료 (2026-04-04 22:50)
루나에 star-cliproxy provider 설정 완료:
- Provider: `star-cliproxy:default`
- 모델: `claude-sonnet`
- API Key: 등록 완료
- baseUrl: `http://192.168.50.56:8300/v1`

### 설정 예시 (openclaw.json)
```json
{
  "auth": {
    "profiles": {
      "star-cliproxy:default": {
        "provider": "openai",
        "mode": "api_key",
        "baseUrl": "http://192.168.50.56:8300/v1"
      }
    },
    "order": {
      "openai": [
        "star-cliproxy:default",
        "default"
      ]
    }
  },
  "agents": {
    "defaults": {
      "models": {
        "claude-sonnet": {
          "provider": "star-cliproxy:default"
        }
      },
      "model": {
        "primary": "claude-sonnet",
        "provider": "star-cliproxy:default",
        "fallbacks": ["anthropic/claude-sonnet-4-20250514"]
      }
    }
  }
}
```

## 문제 해결

### Claude 권한 문제
- 기존: `--permission-mode bypassPermissions` → root 권한으로 거부됨
- 해결: `--permission-mode auto` 로 변경

### Codex 한도 문제
- 현상: CLI exited with code 1
- 대기: 내일(4/5) 오전 9시 한도 초기화 예상
- 대안: 당분간 Claude만 사용

### 대시보드 장애
- 서비스: star-cliproxy-dashboard.service 재시작 실패
- 임시: API 직접 사용하거나 별도 디버깅 필요

## 주요 명령어
```bash
# 서비스 상태 확인
systemctl status star-cliproxy-api
systemctl status star-cliproxy-dashboard

# 서비스 재시작
systemctl restart star-cliproxy-api
systemctl restart star-cliproxy-dashboard

# 로그 확인
journalctl -u star-cliproxy-api -f
journalctl -u star-cliproxy-dashboard -f

# 모델 목록 확인
curl -H "Authorization: Bearer sk-proxy-25d58e2017ebf59251bed15be6d03f7a302c35864cc0af0a" \
  http://192.168.50.56:8300/v1/models
```

## 현재 상황 요약 (2026-04-04 22:40)
- **Claude**: ✅ star-cliproxy 통해 사용 가능
- **Codex**: ❌ 한도 차서 대기 중
- **Anthropic OAuth**: ⚠️ 4/5 새벽 4시 차단 예정
- **대안**: 오늘 밤 Anthropic API Key 전환 + star-cliproxy Claude 활용