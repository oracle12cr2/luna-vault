# C.튜닝

> 📂 원본: `2장 인덱스 튜닝/실습 2-4/C.튜닝.txt`

```sql
SELECT /*+ FULL(TB_ORD) */
*
FROM TB_ORD
WHERE SALE_GB IN ('01', '02');

```
