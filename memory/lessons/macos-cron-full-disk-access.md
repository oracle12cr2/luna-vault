---
trigger: "macOS cron에서 chat.db 등 보호된 파일 접근 시 PermissionError"
domain: infra
confidence: ✅
created: 2026-03-28
---

# macOS cron — Full Disk Access 권한

## 문제
cron에서 `/Users/xxx/Library/Messages/chat.db` 접근 시 `PermissionError: [Errno 1] Operation not permitted` 발생. LaunchAgent에서 cron으로 전환 후 권한이 안 따라옴.

## 원인
macOS는 프로세스별로 Full Disk Access (FDA) 권한을 관리함. LaunchAgent → cron 전환 시 `/usr/sbin/cron`에 별도로 FDA 부여 필요.

## 해결
1. 시스템 설정 → 개인정보 보호 및 보안 → Full Disk Access
2. `+` 버튼 → Finder에서 `/usr/sbin/cron` 선택 (경로 직접 입력: `Cmd+Shift+G`)
3. 토글 켜기

**팁**: Finder 대화상자에서 경로 입력이 안 보이면 `ln -s /usr/sbin/cron ~/Desktop/cron`으로 바로가기 만들어서 추가 후 삭제.

## 교훈
- macOS에서 보호된 파일(Messages, Photos, Mail 등)에 접근하는 스크립트는 **실행 주체에 FDA 필요**
- `/usr/sbin/cron`에 FDA 주면 cron 하위 모든 스크립트가 접근 가능
- python3 개별로 FDA 줘도 되지만, cron에 주는 게 더 간편
