# B.튜닝 전 상황

> 📂 원본: `5장 부분 범위 처리 튜닝/실습 5-2/B.튜닝 전 상황.txt`

```sql
SELECT * FROM
(
	SELECT
	ROWNUM RNUM, TRD_DTM, TRD_CNT, TRD_AMT,
	COUNT(*) OVER() CNT
	FROM
	(
		SELECT
		TRD_DTM, TRD_CNT, TRD_AMT
		FROM TB_STOCK_TRD A
		WHERE STOCK_CD = '000001'
		AND TRD_DTM >= TO_CHAR(SYSDATE-365, 'YYYYMMDDHH24MISS')
	  ORDER BY TRD_DTM
	)
)
WHERE RNUM BETWEEN 21 AND 30;

```
