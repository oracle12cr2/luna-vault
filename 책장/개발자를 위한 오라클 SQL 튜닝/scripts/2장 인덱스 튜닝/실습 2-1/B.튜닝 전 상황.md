# B.튜닝 전 상황

> 📂 원본: `2장 인덱스 튜닝/실습 2-1/B.튜닝 전 상황.txt`

```sql
SELECT /*+ FULL(A) */
   COUNT(*)
FROM TB_CUST A
WHERE
  A.CUST_NM LIKE 'AB%' AND
  EXISTS
    (
        SELECT '1'
         FROM TB_ORD C
         WHERE
       C.CUST_ID = A.CUST_ID AND
       C.PRDT_CD LIKE 'AB%'
     ) ;


```
