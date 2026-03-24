# B.튜닝 전 상황

> 📂 원본: `2장 인덱스 튜닝/실습 2-4/B.튜닝 전 상황.txt`

```sql
SELECT
/*+ INDEX(TB_ORD TB_ORD_IDX01) */
*
FROM TB_ORD
WHERE SALE_GB IN ('01', '02');

```
