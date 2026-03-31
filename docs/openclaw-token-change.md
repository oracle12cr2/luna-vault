# OpenClaw API 토큰 변경 방법

> 루나/유나 전환 시, 또는 토큰 재발급 시 참고

## 토큰 구조

OpenClaw는 여러 Anthropic 토큰 프로필을 관리한다:

| 프로필 이름 | 용도 |
|---|---|
| `anthropic:yuna` | 유나 (맥북 에어) 전용 토큰 |
| `anthropic:luna` | 루나 (서버) 전용 토큰 |
| `anthropic:default` | 기본 토큰 (현재 우선순위에 따라 사용) |

우선순위는 `~/.openclaw/openclaw.json`의 `auth.order.anthropic` 배열 순서대로 적용된다.

## 토큰 발급 위치

- Claude Code 앱 → 설정 → API 토큰 발급
- 토큰 형식: `sk-ant-oat01-...`

## 토큰 변경 절차

### 1. openclaw configure 실행

```bash
openclaw configure
```

- API 키 입력 프롬프트에서 새 토큰 붙여넣기
- Token name: 해당 프로필 이름 입력 (예: `Yuna` → `anthropic:yuna`)

### 2. 게이트웨이 재시작

```bash
openclaw gateway restart
```

### 3. 확인

우선순위 확인:
```bash
cat ~/.openclaw/openclaw.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['auth']['order'])"
```

현재 사용 토큰 확인 (OpenClaw 채팅에서):
```
/status
```
`🔑 token (anthropic:yuna)` 형식으로 표시됨

## 루나 → 유나 전환 시 (루나 사용 종료 후)

1. 유나 토큰(`sk-ant-oat01-...`) 발급
2. `openclaw configure` → Token name: `Yuna`
3. `openclaw gateway restart`
4. `auth.order` 확인: `anthropic:yuna`가 1순위인지 체크

## 주의사항

- `~/.openclaw/openclaw.json.backup-apikey` — 이전 설정 백업 파일
- 토큰 값 자체는 macOS Keychain에 저장됨 (json 파일에는 프로필 이름만)
- 게이트웨이 인증 토큰(`gateway.auth.token`)과 API 토큰은 **완전히 별개**
