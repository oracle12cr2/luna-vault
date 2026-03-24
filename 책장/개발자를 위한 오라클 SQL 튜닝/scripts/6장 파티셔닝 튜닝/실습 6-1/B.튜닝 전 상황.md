# B.튜닝 전 상황

> 📂 원본: `6장 파티셔닝 튜닝/실습 6-1/B.튜닝 전 상황.txt`

```sql
SELECT *
FROM TB_TRD
WHERE TRD_DT 
BETWEEN TO_DATE(TO_CHAR(SYSDATE - 180, 'YYYYMMDD'), 'YYYYMMDD') 
AND TO_DATE(TO_CHAR(SYSDATE - 120, 'YYYYMMDD'), 'YYYYMMDD');

```
