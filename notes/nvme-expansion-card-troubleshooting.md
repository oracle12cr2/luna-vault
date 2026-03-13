# NVMe 확장카드 인식 문제 트러블슈팅

> 작성일: 2026-02-15 | 정리일: 2026-03-14

## 환경
- **메인보드:** X99 (중국산)
- **확장카드:** NVMe 4개 장착용 PCIe 확장카드
- **장착 슬롯:** PCIe x16
- **NVMe 수:** 4개
- **증상:** 이전에 인식됐었는데 현재 BIOS에서도 안 보임

## 원인 분석 (우선순위순)

### 1. PCIe Bifurcation 설정 (가장 유력)
- NVMe 4개 카드는 내부적으로 **x4×4 = 16레인** 사용
- BIOS 기본값은 x16 슬롯을 단일 장치(x16)로 인식
- **해결:** BIOS에서 해당 슬롯을 `x4x4x4x4`로 분기 설정

**BIOS 메뉴 위치 (중국산 X99 기준):**
- `Advanced` → `PCIe/PCI Configuration`
- `Chipset` → `PCH Configuration` 또는 `CPU Configuration`
- `Advanced` → `Onboard Device Configuration`
- 항목명: "Bifurcation", "PCIe Bifurcation", "Lane Bifurcation" 등

> ⚠️ **Bifurcation 미지원 보드:** 일부 저가형 X99는 이 옵션이 없음 → PLX 칩셋 내장 확장카드로 교체 필요 (자동 레인 분기)

### 2. CSM 비활성화
- NVMe는 UEFI 모드에서만 인식되는 경우 많음
- **해결:** BIOS → `CSM` → **Disabled**

### 3. Above 4G Decoding
- 멀티 NVMe 확장카드는 이 옵션이 필요한 경우 있음
- **해결:** BIOS → `Advanced` → `PCIe 설정` → `Above 4G Decoding` → **Enabled**

### 4. PCIe 슬롯 대역폭 공유
- M.2 슬롯과 특정 PCIe 슬롯이 CPU/칩셋 레인 공유
- M.2에 다른 SSD가 있으면 PCIe 슬롯 자동 비활성화 가능
- **해결:** 메인보드 매뉴얼에서 슬롯 공유 관계 확인

### 5. 물리적 접촉 불량
- PCIe 금속 단자를 지우개로 닦고 재장착
- NVMe 고정 나사 풀림 확인
- 콜드 부팅 (전원 완전 차단 후 10초 대기 → 재시작)

## 체크리스트
- [ ] CSM Disabled 설정
- [ ] PCIe Bifurcation → x4x4x4x4 설정
- [ ] Above 4G Decoding Enabled
- [ ] M.2 슬롯 공유 충돌 확인
- [ ] 확장카드 물리적 재장착
- [ ] 콜드 부팅 시도
