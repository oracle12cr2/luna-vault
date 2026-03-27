---
globs: ["**/*.sql", "oracle-scripts/**", "oracle-sql-tuning-compass/**"]
---

# Oracle SQL 규칙

## 접속 정보
- RAC: app_user/oracle@192.168.50.35:1521/PROD (OGG RAC)
- 단독: system/oracle@192.168.50.27:1521/PROD (19c RAC)

## SQL 스타일
- 키워드 대문자 (SELECT, FROM, WHERE)
- 테이블 별칭 사용, 의미 있는 이름 (e.g., emp, dept)
- 힌트 사용 시 주석으로 이유 설명
- DML은 반드시 WHERE 조건 포함 (전체 삭제/갱신 금지)
- DDL 실행 전 확인 요청

## 튜닝
- 실행계획 확인: EXPLAIN PLAN 또는 DBMS_XPLAN.DISPLAY_CURSOR
- 인덱스 생성 시 기존 인덱스 확인 먼저
- 바인드 변수 사용 권장 (리터럴 지양)
