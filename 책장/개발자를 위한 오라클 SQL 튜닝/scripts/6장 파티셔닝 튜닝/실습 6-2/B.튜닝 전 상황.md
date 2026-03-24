# B.튜닝 전 상황

> 📂 원본: `6장 파티셔닝 튜닝/실습 6-2/B.튜닝 전 상황.txt`

```sql
SELECT *
FROM TB_TRD
WHERE CUST_ID = '0000000001'
AND TRD_DT BETWEEN TO_CHAR(SYSDATE - 365, 'YYYYMMDD') AND TO_CHAR(SYSDATE, 'YYYYMMDD');

```
