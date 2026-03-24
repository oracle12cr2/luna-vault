# C.튜닝

> 📂 원본: `3장 조인 튜닝/실습 3-3/C.튜닝.txt`

```sql
SELECT  /*+ NO_MERGE(A) */
  B.PRDT_CD,
  B.PRDT_NM,
  A.SALE_CNT_SUM,
  A.SALE_AMT_SUM
FROM
  (
	  	SELECT 
	     A.PRDT_CD,
	     SUM(A.SALE_CNT) SALE_CNT_SUM,
	     SUM(A.SALE_AMT) SALE_AMT_SUM
	   FROM TB_PRDT_SALE_DAY A
	   WHERE
	     A.SALE_DT BETWEEN '20120101' AND '20131231'
	   GROUP BY A.PRDT_CD
   ) A,
   TB_PRDT B
WHERE
  A.PRDT_CD = B.PRDT_CD;

```
