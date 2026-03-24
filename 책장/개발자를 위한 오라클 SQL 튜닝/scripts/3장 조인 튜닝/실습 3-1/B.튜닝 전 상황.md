# B.튜닝 전 상황

> 📂 원본: `3장 조인 튜닝/실습 3-1/B.튜닝 전 상황.txt`

```sql
SELECT
/*+ LEADING(A) USE_NL(B) */
*
FROM TB_CUST A, TB_ORD B
WHERE A.CUST_NM LIKE 'L%'
AND A.CUST_ID = B.CUST_ID
AND B.ORD_DT BETWEEN 
TO_CHAR(SYSDATE-365, 'YYYYMMDD') 
AND TO_CHAR(SYSDATE, 'YYYYMMDD');

```
