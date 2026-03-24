# C.튜닝

> 📂 원본: `6장 파티셔닝 튜닝/실습 6-1/C.튜닝.txt`

```sql
SELECT *
FROM TB_TRD
WHERE TRD_DT 
BETWEEN TO_CHAR(SYSDATE - 180, 'YYYYMMDD')
AND TO_CHAR(SYSDATE - 120, 'YYYYMMDD');

```
