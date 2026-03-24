# B.튜닝 전 상황

> 📂 원본: `3장 조인 튜닝/실습 3-4/B.튜닝 전 상황.txt`

```sql
SELECT 
/*+ LEADING(A) FULL(A) USE_NL(B) USE_NL(C) */
  A.CUST_ID, 
  A.CUST_NM, 
  B.CUST_ID, 
  B.SEQ, 
  B.CUST_INFO
FROM 
  TB_CUST A, 
  TB_CUST_DTL B, 
  TB_ORD C
WHERE
  A.CUST_NM LIKE 'A%' AND
  A.CUST_ID = B.CUST_ID AND
  C.CUST_ID = B.CUST_ID AND
  C.ORD_DT LIKE '2015%' 
GROUP BY 
  A.CUST_ID, 
  A.CUST_NM, 
  B.CUST_ID, 
  B.SEQ, 
  B.CUST_INFO;

```
