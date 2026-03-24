# B.튜닝 전 상황

> 📂 원본: `3장 조인 튜닝/실습 3-3/B.튜닝 전 상황.txt`

```sql
SELECT 
  B.PRDT_CD, 
MIN(B.PRDT_NM),
SUM(A.SALE_CNT), 
SUM(A.SALE_AMT)
FROM
  TB_PRDT_SALE_DAY A, TB_PRDT B
WHERE
  A.SALE_DT BETWEEN '20120101' AND '20131231' AND
  A.PRDT_CD = B.PRDT_CD
GROUP BY B.PRDT_CD;

```
