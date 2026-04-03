# SCRATCHPAD.md — 임시 메모 & 중간 결과 (Hot Layer)

> Subagent 결과 요약, 리서치 중간 메모, 아이디어 등
> 정리되면 daily log나 MEMORY.md로 승격, 또는 삭제

---

## 메모

### LLM 비용절감 메모리 전략 (2026-03-24)
- 출처: @0xvinsohn (Threads)
- 핵심: Subagent + /compact + 3-tier 메모리(Hot/Warm/Cold) + ROOT 인덱싱
- 우리 워크스페이스에 적용 완료 (WORKING.md, SCRATCHPAD.md, ROOT.md 추가)

### OEL9 Python 3.12 전환 메모 (2026-04-04)
- 대상: 192.168.50.3, .4, .5, .6, .7, .9, .11, .12, .14, .16
- 결과: 전 서버 `python3` → `Python 3.12.12`, `python3.9` / `python3.12` 병행 유지
- 적용 방식:
  - `sudo dnf install -y python3.12`
  - `alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 10`
  - `alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 20`
  - `alternatives --set python3 /usr/bin/python3.12`
- 검증:
  - `python3 --version`
  - `alternatives --display python3`
  - `sudo dnf repolist` 정상
- 롤백:
  - `sudo alternatives --set python3 /usr/bin/python3.9`

### VM RPM 비교 결과 (2026-03-24)

**비교 결과:**
- WAS1(.6) vs WAS2(.7): **완벽 동일** (1,408개)
- WEB1(.11) vs WEB2(.12): **완벽 동일** (1,432개)
- Redis1(.3) vs Redis2(.4) vs Redis3(.5): **완벽 동일** (1,290개)

**불필요 RPM (7대 모두 동일, ~60개):**
- ModemManager, NetworkManager-wifi, wpa_supplicant
- cockpit (7개), cups (9개), avahi (3개)
- bluez (3개), colord (3개), gnome-user-docs
- firewalld (2개), sssd (12개)
- plymouth (8개), totem (3개), yelp (4개), alsa (2개)

**→ 남궁건 승인 후 제거 예정**
