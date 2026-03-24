# B.튜닝 전 상황

> 📂 원본: `4장 함수 튜닝/실습 4-1/B.튜닝 전 상황.txt`

```sql
SELECT
Y.*
FROM
(
    SELECT /*+ NO_MERGE*/ORD_DT, MAX(ORD_AMT) 
AS ORD_AMT
    FROM TB_ORD
    WHERE ORD_DT BETWEEN TO_CHAR(SYSDATE-30, 'YYYYMMDD') AND TO_CHAR(SYSDATE, 'YYYYMMDD')
    GROUP BY ORD_DT
) X,
TB_ORD Y
WHERE Y.ORD_DT = X.ORD_DT
AND Y.ORD_AMT = X.ORD_AMT
ORDER BY Y.ORD_DT;

```
