# D.추가 튜닝

> 📂 원본: `2장 인덱스 튜닝/실습 2-1/D.추가 튜닝.txt`

```sql
DROP INDEX TB_CUST_IDX01;
CREATE INDEX TB_CUST_IDX01 ON TB_CUST(CUST_NM, CUST_ID);
ANALYZE INDEX TB_CUST_IDX01 COMPUTE STATISTICS;


```
