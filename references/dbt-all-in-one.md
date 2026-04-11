# DBT All In One 참고 메모

- 원문: https://github.com/praster1/DBT_all_in_one
- 확인일: 2026-04-11
- 저장 방식: 원문 미러 대신 요약/참고 메모만 보관
- 주의: 원본 저장소는 GitHub 기준 라이선스 표시가 없어 원문 전체 복제는 보류

## 한줄 요약

dbt 학습용 원고와 실습용 Companion Pack을 한 저장소에 모아둔 자료다.

## 무엇이 들어 있나

- 책 본문 Markdown
- 예제 케이스북
- 플랫폼별 playbook
- 부록 레퍼런스
- 실행 가능한 코드와 초기 데이터 셋업 파일

## 읽는 순서

1. `chapters/00-introduction-and-reading-guide.md`
2. `01_outline/master_toc.md`
3. `chapters/01-*` 순서대로
4. 실습 시 `codes/README.md` 및 `codes/01_duckdb_runnable_project/`
5. 필요 시 Appendix B, C, D 참고

## 본문 구성 요약

- Chapter 01~08: 핵심 개념, 모델링, 품질, 디버깅, 운영, 거버넌스, semantic layer
- Chapter 09~11: 연속 예제 casebook
- Chapter 12~20: 데이터 플랫폼별 playbook
- Appendix A~D: bootstrap, 명령어, Jinja/macro, 트러블슈팅/지원 매트릭스

## 예제 트랙

- Retail Orders
- Event Stream
- Subscription & Billing

## 플랫폼 범위

- DuckDB
- MySQL
- PostgreSQL
- BigQuery
- ClickHouse
- Snowflake
- Trino
- NoSQL + SQL Layer
- Databricks

## 활용 포인트

- dbt 전체 학습 로드맵 파악용
- 입문자용 교재 후보 검토용
- 플랫폼별 dbt 운영 방식 비교 참고용
- DuckDB 기반 로컬 실습 시작점 참고용

## 메모

- 원문 README에 따르면 ChatGPT를 적극 활용해 작성되었고, 오류 가능성을 직접 언급함
- 따라서 실무 적용 전에는 예제/설정 검증이 필요함
- 필요하면 다음 단계로 챕터 구조나 코드 품질을 별도 리뷰할 수 있음
