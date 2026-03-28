---
trigger: "10053 트레이스 파싱 시 Scan IO Cost, NL Join Cost 누락"
domain: oracle
confidence: ✅
created: 2026-03-28
---

# 10053 트레이스 파싱 — 누락되기 쉬운 패턴들

## 문제
optimizer_trace.py로 대형 SQL (4테이블 조인, 서브쿼리) 10053 파싱 시 여러 항목 누락:
- Scan IO Cost 128줄 미파싱
- NL Join Cost 101개 미파싱
- Cardinality `rsel` 붙은 패턴 매칭 실패
- ix_sel 과학표기법 (1.6129e-08) 매칭 실패

## 원인
1. `Card: Original: 31000000.000000rsel = 0.000020   Rounded: 619` — `rsel`이 숫자에 바로 붙어있음
2. `Scan IO  Cost (Disk) = 34681.000000` — 기존 파서에 해당 패턴 없음
3. `NL Join : Cost: 150204.738212` — `NL Join :` 접두어 때문에 Cost 정규식 미매칭
4. `ix_sel: 1.6129e-08` — `[\d.]+`가 과학표기법 미지원

## 해결
```python
# 1. Cardinality — rsel 옵셔널 그룹 추가
r'Card: Original:\s+([\d.]+)(?:rsel\s*=\s*[\d.eE+-]+\s+)?\s*Rounded:\s+(\d+)'

# 2. Scan IO Cost 패턴 4종 추가
r'\s*Scan IO\s+Cost\s+\(Disk\)\s*=\s+([\d.]+)'
r'\s*Scan CPU Cost\s+\(Disk\)\s*=\s+([\d.]+)'
r'\s*Total Scan IO\s+Cost\s*=\s+([\d.]+)'
r'\s*Total Scan CPU\s+Cost\s*=\s+([\d.]+)'

# 3. NL Join Cost 별도 매칭
r'\s*NL Join\s*:\s*Cost:\s+([\d.]+)\s+Resp:\s+([\d.]+)\s+Degree:\s+(\d+)'

# 4. ix_sel 과학표기법
r'\s*ix_sel:\s+([\d.eE+-]+)\s+ix_sel_with_filters:\s+([\d.eE+-]+)'
```

## 교훈
- 10053 트레이스는 **단일 테이블 vs 다중 조인**에서 출력 패턴이 크게 다름
- 단순 SQL로만 테스트하면 NL Join, 과학표기법 ix_sel 등을 놓침
- **대형 SQL (4+ 테이블, 서브쿼리)로 반드시 테스트** 해야 함
