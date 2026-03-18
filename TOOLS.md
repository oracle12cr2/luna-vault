# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

### iCloud CalDAV
- Apple ID: ktokko@nate.com
- App Password: vlqr-yval-ljoa-nwpt
- Principal: /1316396648/
- 캘린더:
  - 가족 일정 → /1316396648/calendars/405E81D5-4424-4347-9801-2E5A8EF2BDEA/
  - 출금 일정 → /1316396648/calendars/AE107934-5CEA-4F28-90A7-18396FFA5787/
  - 작업 일정 → /1316396648/calendars/F9CB3AAD-E81E-460D-9A23-4D50EB349BB9/
  - 미리 알림 ⚠️ → /1316396648/calendars/feca1acc-9e0f-4c8d-b33b-3301b2ccae5a/

### KIS 모의투자 API
- App Key: PSn3EK6GBUcrb5pcAatX6qXr1Pa07laVUYUe
- App Secret: d3o9g5OfF55qwbM9CizR/nUDuNNgWhjOtnCn5fzOHCS5B9VM7mWFB2HsNFK5rJlHiQuts5vB4kxQiZS0w0+mAP9hP4L4OGW+aG8wW0PfI6HvU2JSqd7AHghIisAKuYxjzWMXjM5ctpXErzf/gpL/Y16BTQqzGogIYuIJ7gCGVB33VoHELhQ=
- Base URL: https://openapivts.koreainvestment.com:29443
- 발급일: 2026-03-11

### Windows PC
- 호스트명: 1260P (windows)
- IP: 192.168.50.30
- SSH: kto@192.168.50.30 (ed25519 키 인증)
- 접속: `ssh -i ~/.ssh/id_ed25519 kto@192.168.50.30`
- 유저: kto (관리자)
- 용도: 리니지M(Purple) 24시간 가동, Claude 데스크톱, Chrome
- 리니지M 리소스 제한: BelowNormal + CPU 4코어(0-3), 로그온 시 자동 적용
- 프로세스 모니터링: C:\Scripts\check_lineagem.ps1 (Purple+LineageM 종료 시 네이버 메일 알림)
- 네이버 SMTP: kto2004@naver.com / YM512KB4JEB8

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.
