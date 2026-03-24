# B.튜닝 전 상황

> 📂 원본: `2장 인덱스 튜닝/실습 2-2/B.튜닝 전 상황.txt`

```sql
SELECT
  ORD_DT,
  SALE_GB,
  PAY_GB,
  COUNT(*) AS 주문건수,
  SUM(ORD_AMT) AS 총주문금액,
  ROUND(AVG(ORD_AMT), 2) AS 평균주문금액
FROM TB_ORD
WHERE
  ORD_DT BETWEEN '20150101' AND '20151231'AND
  ORD_NM LIKE 'A%'AND
  ORD_AMT >= 1000
GROUP BY
  ORD_DT, SALE_GB, PAY_GB
ORDER BY
  ORD_DT, SALE_GB, PAY_GB;

```
