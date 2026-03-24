# C.튜닝

> 📂 원본: `7장 병렬 처리 튜닝/실습 7-1/C.튜닝.txt`

```sql
SELECT /*+ FULL(TB_TRD) PARALLEL(TB_TRD 16) */ *
FROM TB_TRD
WHERE TRD_DT BETWEEN TO_CHAR(SYSDATE-365, 'YYYYMMDD') AND TO_CHAR(SYSDATE, 'YYYYMMDD')
AND CUST_ID = '0000000001';

```
