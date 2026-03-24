# B.튜닝 전 상황

> 📂 원본: `5장 부분 범위 처리 튜닝/실습 5-1/B.튜닝 전 상황.txt`

```sql
SELECT
 MAX(ORD_NO) MAX_ORD_NO, 
 MIN(ORD_NO) MIN_ORD_NO
FROM TB_ORD_DAY
WHERE ORD_DT = TO_CHAR(SYSDATE - 30, 'YYYYMMDD')

```
