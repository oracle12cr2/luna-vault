# D. Anti Semi 조인

> 📂 원본: `3장 조인 튜닝/실습 3-4/D. Anti Semi 조인.txt`

```sql
SELECT
/*+ LEADING(A) FULL(A) USE_NL(B) */
  A.CUST_ID,
  A.CUST_NM,
  B.CUST_ID,
  B.SEQ,
  B.CUST_INFO
FROM
  TB_CUST A, TB_CUST_DTL B
WHERE
  A.CUST_NM LIKE 'A%' AND
  A.CUST_ID = B.CUST_ID AND
  NOT EXISTS
    (   SELECT 
        /*+ UNNEST NL_SJ INDEX(C TB_ORD_IDX01) */
        '1'
     FROM TB_ORD C
     WHERE
       C.CUST_ID = B.CUST_ID AND
       C.ORD_DT LIKE '2015%'
       ) ;

```
