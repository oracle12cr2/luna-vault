# B.튜닝 전 상황

> 📂 원본: `3장 조인 튜닝/실습 3-2/B.튜닝 전 상황.txt`

```sql
SELECT /*+ LEADING(A) INDEX(A TB_ORD_IDX01) USE_NL(B) */
A.ORD_NO, A.ORD_DT, B.PRDT_CD, B.PRDT_NM
FROM TB_ORD A,
    TB_PRDT B
WHERE A.ORD_DT > TO_CHAR(SYSDATE-365, 'YYYYMMDD')
AND A.PRDT_CD = B.PRDT_CD;

```
