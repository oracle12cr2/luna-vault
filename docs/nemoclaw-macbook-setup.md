# NemoClaw 맥북 설치 가이드 🍎

> 원본: [YouTube - NemoClaw VPS 셋업](https://www.youtube.com/watch?v=dEL9tKwvejo)
> 참고: [Mac Mini 셋업 가이드](https://github.com/bcharleson/nemoclaw-macmini-setup)
> 작성: 2026-03-27

## 개요

NemoClaw = OpenClaw + Nvidia OpenShell 샌드박스. 맥북에서 도커 없이(Colima 사용) AI 에이전트를 보안 격리 환경에서 24시간 운영.

### 아키텍처
```
브라우저/텔레그램 → macOS 방화벽 → Colima(Docker) → OpenShell 샌드박스 → OpenClaw
                                                      ├─ Landlock FS 격리
                                                      ├─ seccomp 시스콜 필터
                                                      └─ 네트워크 화이트리스트
```

### 2중 보안 레이어
- **Layer 1**: macOS 전용 유저 계정 (sudo 불가, 파일시스템 격리)
- **Layer 2**: OpenShell 컨테이너 (네트워크/파일/시스콜 제한)

---

## 사전 준비

- macOS 14 (Sonoma) 이상
- Apple Silicon (M1/M2/M4) 또는 **Intel Mac** (2020 이하)
- 16GB RAM 이상 (로컬 모델 돌리려면 32GB+)
- 40GB 이상 디스크 여유
- Nvidia API 키 (무료): https://build.nvidia.com → 프로필 → API Keys

### ⚠️ Intel Mac 참고사항
- Homebrew 경로: `/usr/local/bin` (Apple Silicon은 `/opt/homebrew/bin`)
- 가이드의 `/opt/homebrew/...` 경로를 `/usr/local/...`로 바꿔서 실행
- GPU 가속 없음 → **Ollama 로컬 모델 매우 느림**
- 추천: Ollama Cloud 또는 Claude/OpenAI API 사용
- RAM 16GB면 로컬 모델은 4B가 한계 (그마저도 느림)

---

## Part 1. 호스트 환경 설정 (관리자 계정)

### 1-1. Homebrew 설치 (없으면)
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

### 1-2. Colima + Docker 설치
> VPS에선 Docker를 직접 설치하지만, macOS에선 **Colima**가 경량 Docker 런타임 역할

```bash
brew install colima docker
```

### 1-3. Colima 시작
```bash
# Intel Mac 16GB
colima start --cpu 2 --memory 6 --disk 40

# Apple Silicon 16GB
colima start --cpu 4 --memory 8 --disk 40

# Apple Silicon 32GB+ (권장)
colima start --cpu 6 --memory 12 --disk 60
```

> ⚠️ Intel Mac은 CPU/메모리 여유가 적으니 보수적으로 잡기 (2코어/6GB)

### 1-4. Docker 동작 확인
```bash
docker ps
# 빈 목록이 나오면 정상. "Cannot connect to Docker daemon" → colima status 확인
```

### 1-5. 추론 백엔드 선택

| 옵션 | 장점 | 단점 |
|------|------|------|
| **A. Ollama Cloud** (추천) | 설치 간편, GPU 불필요, 무료 | 데이터가 외부 경유 |
| **B. Ollama 로컬** | 완전 프라이빗, 무제한 | RAM 많이 필요 |
| **C. Claude/OpenAI API** | 최고 품질 | API 비용 발생 |

#### 옵션 A: Ollama Cloud (가장 쉬움)
```bash
brew install ollama
brew services start ollama
# 모델 다운로드 불필요 — onboard 시 nemotron-3-super:cloud 선택
```

#### 옵션 B: Ollama 로컬
```bash
brew install ollama
brew services start ollama

# 32GB+ → 베스트 가성비
ollama pull nemotron-3-nano:30b    # 24GB 다운로드

# 16GB → 가벼운 모델
ollama pull nemotron-3-nano:4b     # 2.8GB 다운로드
```

#### 옵션 C: Claude/OpenAI API (영상에서 사용한 방식)
```bash
# Ollama는 기본으로 설치 (NemoClaw가 필요)
brew install ollama
brew services start ollama
# API 키는 Part 4에서 OpenShell provider로 등록
```

#### 추론 확인
```bash
curl -s http://localhost:11434/api/tags | head -c 200
# JSON 응답 나오면 OK
```

---

## Part 2. 에이전트 전용 macOS 유저 생성

> VPS에선 root로 다 하지만, macOS에선 **격리된 비관리자 계정**을 만들어서 보안 강화

### 2-1. 변수 설정
```bash
export AGENT_NAME="Luna"           # 에이전트 이름
export AGENT_USERNAME="luna"       # macOS 유저명 (소문자)
export UNIQUE_ID="502"             # 고유 UID (겹치지 않게)
export SANDBOX_NAME="luna-sandbox" # 샌드박스 이름
```

### 2-2. 유저 생성
```bash
# 사용 중인 UID 확인
dscl . -list /Users UniqueID | sort -n -k2

# 유저 생성
sudo dscl . -create /Users/$AGENT_USERNAME
sudo dscl . -create /Users/$AGENT_USERNAME UserShell /bin/zsh
sudo dscl . -create /Users/$AGENT_USERNAME RealName "$AGENT_NAME"
sudo dscl . -create /Users/$AGENT_USERNAME UniqueID $UNIQUE_ID
sudo dscl . -create /Users/$AGENT_USERNAME PrimaryGroupID 20
sudo dscl . -create /Users/$AGENT_USERNAME NFSHomeDirectory /Users/$AGENT_USERNAME

# 홈 디렉토리 생성
sudo createhomedir -c -u $AGENT_USERNAME

# 비밀번호 설정
sudo passwd $AGENT_USERNAME

# 작업 디렉토리 생성
sudo mkdir -p /Users/$AGENT_USERNAME/{Developer,Desktop,Documents,Downloads}
sudo chown -R $AGENT_USERNAME:staff /Users/$AGENT_USERNAME/{Developer,Desktop,Documents,Downloads}
```

> ⚠️ 이 유저는 staff 그룹이지만 **admin 그룹이 아님** → sudo 불가

---

## Part 3. NemoClaw 설치 (에이전트 유저)

### 3-1. 에이전트 유저로 전환
```bash
su - $AGENT_USERNAME
# 비밀번호 입력

# 변수 재설정 (세션 넘어가면 초기화됨)
export SANDBOX_NAME="luna-sandbox"
```

### 3-2. NemoClaw 설치
```bash
curl -fsSL https://nvidia.com/nemoclaw.sh | bash
```

설치 과정:
1. Node.js 없으면 nvm으로 자동 설치
2. npm 10+ 확인
3. GPU 감지 (Apple Silicon은 nvidia-smi 스킵 — 정상)
4. NemoClaw CLI 글로벌 설치

### 3-3. 온보딩 위저드
```bash
nemoclaw onboard
```

**Step 1 — 샌드박스 이름:**
```
Enter sandbox name: luna-sandbox
```

**Step 2 — 추론 설정:**

| 선택한 옵션 | 위저드 입력 |
|-------------|-------------|
| Ollama Cloud | `2` (Local Ollama) → 모델: `nemotron-3-super:cloud` |
| Ollama 로컬 | `2` (Local Ollama) → 모델: `nemotron-3-nano:30b` |
| Claude/OpenAI | `1` (NVIDIA Cloud) → 나중에 Part 4에서 변경 |

**Step 3 — 보안 정책:**
- 기본값 수락 (pypm, npm 허용)
- 필요한 서비스 추가: `telegram`, `slack` 등

> 빌드 5~15분 소요 (이미지 ~2.4GB 다운로드)

### 3-4. 설치 확인
```bash
nemoclaw status
# sandbox running + healthy 표시되면 성공
```

---

## Part 4. AI 모델 연결 (Claude/OpenAI 사용 시)

> 영상에서 Nemotron → OpenAI로 전환하는 부분. macOS에서도 동일.

### 4-1. 에이전트 유저 쉘에서 나오기
```bash
exit  # 관리자 계정으로 복귀
```

### 4-2. API 키 등록 (OpenShell provider)
```bash
# Claude 사용 시
export ANTHROPIC_API_KEY="sk-ant-xxxxx"
openshell provider create anthropic \
  --kind anthropic \
  --api-key "$ANTHROPIC_API_KEY"

# OpenAI 사용 시
export OPENAI_API_KEY="sk-xxxxx"
openshell provider create openai \
  --kind openai \
  --api-key "$OPENAI_API_KEY"
```

### 4-3. 추론 라우팅 설정
```bash
# Claude로 설정
openshell inference set --provider anthropic --model claude-sonnet-4-20250514

# 또는 OpenAI로 설정
openshell inference set --provider openai --model gpt-4.1

# 확인
openshell inference get
```

> 핵심: API 키는 **샌드박스 밖**(OpenShell provider)에 저장 → 샌드박스 안의 에이전트가 키에 직접 접근 불가

### 4-4. OpenClaw config에 모델 추가
```bash
# 샌드박스 진입
nemoclaw $SANDBOX_NAME connect

# config에 provider 추가 (샌드박스 안에서)
openclaw gateway config.patch --raw '{"models":{"anthropic":{"kind":"anthropic"}}}'

# 게이트웨이 재시작
openclaw gateway restart

# 나오기
exit
```

### 4-5. 게이트웨이 토큰 확인
```bash
nemoclaw $SANDBOX_NAME connect
openclaw gateway token
# 이 토큰으로 웹 UI 접속
exit
```

---

## Part 5. 접속 및 테스트

### 5-1. 웹 UI 접속
브라우저에서: `http://localhost:18789`
→ 게이트웨이 토큰 입력 → 연결

### 5-2. 외부 접속 (선택)

#### Caddy로 HTTPS (VPS 영상 방식의 macOS 버전)
```bash
brew install caddy

# Caddyfile 작성
cat > /opt/homebrew/etc/Caddyfile << 'EOF'
your-domain.com {
    reverse_proxy localhost:18789
}
EOF

brew services start caddy
```

#### 또는 Tailscale/Cloudflare Tunnel
```bash
# Tailscale (가장 간편)
brew install tailscale
# Tailscale 로그인 후 → tailscale ip 로 접속
```

---

## Part 6. 자동 시작 설정

### 6-1. Colima 자동 시작 (관리자 계정)
```bash
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.colima.autostart.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.colima.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <!-- Intel Mac: /usr/local/bin/colima, Apple Silicon: /opt/homebrew/bin/colima -->
        <string>/opt/homebrew/bin/colima</string>
        <string>start</string>
        <string>--cpu</string>
        <string>4</string>
        <string>--memory</string>
        <string>8</string>
        <string>--disk</string>
        <string>40</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.colima.autostart.plist
```

### 6-2. NemoClaw 자동 시작 (에이전트 유저)
```bash
sudo -u $AGENT_USERNAME mkdir -p /Users/$AGENT_USERNAME/Library/LaunchAgents

sudo -u $AGENT_USERNAME bash -c "cat > /Users/$AGENT_USERNAME/Library/LaunchAgents/com.nemoclaw.autostart.plist << 'PLIST'
<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>Label</key>
    <string>com.nemoclaw.autostart</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>source ~/.nvm/nvm.sh &amp;&amp; nemoclaw start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
PLIST"
```

---

## Part 7. 관리자 편의 설정

### 작업 디렉토리 심볼릭 링크
```bash
# 관리자 계정에서 에이전트 파일 쉽게 접근
ln -s /Users/$AGENT_USERNAME/Developer ~/Developer/${AGENT_USERNAME}-developer
ln -s /Users/$AGENT_USERNAME/Documents ~/Developer/${AGENT_USERNAME}-documents
```

### 유용한 명령어
```bash
# 상태 확인
sudo -u $AGENT_USERNAME -i bash -c 'nemoclaw status'

# 로그 보기
sudo -u $AGENT_USERNAME -i bash -c 'nemoclaw logs -f'

# 재시작
sudo -u $AGENT_USERNAME -i bash -c 'nemoclaw stop && nemoclaw start'

# 업데이트
sudo -u $AGENT_USERNAME -i bash -c 'source ~/.nvm/nvm.sh && npm update -g nemoclaw'
brew upgrade ollama colima
```

---

## VPS vs 맥북 차이점 요약

| 항목 | VPS (영상) | 맥북 |
|------|-----------|------|
| Docker | 직접 설치 | **Colima** 경유 |
| 유저 격리 | root으로 전부 실행 | **전용 비관리자 계정** (2중 보안) |
| 리버스 프록시 | Caddy + 서브도메인 | localhost 직접 / Tailscale |
| 방화벽 | Hostinger 패널 | macOS 기본 방화벽 (보통 불필요) |
| GPU | 없음 | Apple Silicon (Ollama 로컬 가능) / Intel (로컬 느림, API 추천) |
| 비용 | ~$10/월 (Hostinger) | **무료** (전기세만) |
| 외부 접속 | 서브도메인 자동 | Tailscale/Cloudflare 필요 |
| 자동 시작 | systemd | **launchd** (plist) |

---

## 트러블슈팅

| 문제 | 해결 |
|------|------|
| `Cannot connect to Docker daemon` | `colima start --cpu 4 --memory 8 --disk 40` |
| `nvidia-smi not found` | 정상 — Apple Silicon은 스킵 |
| Ollama 연결 안 됨 | `brew services start ollama` → `curl localhost:11434/api/tags` |
| 온보딩 중 Ollama 미감지 | 관리자 계정에서 Ollama 시작 후 에이전트 유저로 재시도 |
| UID 충돌 | `dscl . -list /Users UniqueID | sort -n -k2` → 다른 ID 사용 |
