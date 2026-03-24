# C.튜닝

> 📂 원본: `3장 조인 튜닝/실습 3-2/C.튜닝.txt`

```sql
SELECT /*+ LEADING(B) FULL(B) USE_HASH(A)  */
A.ORD_NO, A.ORD_DT, B.PRDT_CD, B.PRDT_NM
FROM TB_ORD A,
    TB_PRDT B
WHERE A.ORD_DT > TO_CHAR(SYSDATE-365, 'YYYYMMDD')
AND A.PRDT_CD = B.PRDT_CD;

```
