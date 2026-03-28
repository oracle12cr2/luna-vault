---
trigger: "Windows SSH에서 GitHub 접속 시 Permission denied (publickey)"
domain: git
confidence: ✅
created: 2026-03-28
---

# Windows SSH — GitHub 키 경로와 USERPROFILE 불일치

## 문제
Windows PC에서 `ssh -T git@github.com` 시 `Permission denied (publickey)`. 키 파일은 `C:\Users\kto\.ssh\id_ed25519`에 있는데 인식 안 됨.

## 원인
SSH 접속 시 `%USERPROFILE%`이 `C:\Users\Administrator`로 잡힘 (kto 계정이지만 Administrator 프로필 사용). SSH는 `C:\Users\Administrator\.ssh\`에서 키를 찾음.

## 해결
```cmd
mkdir C:\Users\Administrator\.ssh
copy C:\Users\kto\.ssh\id_ed25519 C:\Users\Administrator\.ssh\id_ed25519
copy C:\Users\kto\.ssh\id_ed25519.pub C:\Users\Administrator\.ssh\id_ed25519.pub

echo Host github.com > C:\Users\Administrator\.ssh\config
echo   HostName github.com >> C:\Users\Administrator\.ssh\config
echo   User git >> C:\Users\Administrator\.ssh\config
echo   IdentityFile C:\Users\Administrator\.ssh\id_ed25519 >> C:\Users\Administrator\.ssh\config
```

## 교훈
- Windows에서 `whoami`와 `%USERPROFILE%`이 다를 수 있음 (특히 Administrators 그룹 계정)
- SSH config 파일은 **실제 USERPROFILE 경로** 아래 `.ssh/`에 있어야 함
- `gh ssh-key add`로 GitHub에 공개키 등록, `ssh -T git@github.com`으로 검증
