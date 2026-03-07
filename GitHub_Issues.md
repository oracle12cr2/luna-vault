# GitHub 이슈 목록

## 2026-03-07 발견된 문제

### luna-vault 리포지토리의 클릭 안되는 항목들

**문제**: GitHub에서 다음 두 항목이 파란색으로 표시되지만 클릭해도 반응 없음
- `oracle-sql-tuning-compass`
- `oracle-to-postgresql`

**위치**: https://github.com/oracle12cr2/luna-vault (파일 트리)

**추정 원인**:
1. 빈 파일 (생성만 하고 내용 없음)
2. Git submodule 설정 오류  
3. 깨진 심볼릭 링크
4. 권한 문제

**해결 방법 (내일 검토)**:
- 로컬에서 해당 파일들 상태 확인
- 필요 없으면 삭제, 필요하면 올바르게 설정
- Git 상태 및 .gitmodules 파일 점검

**상태**: 🔍 조사 필요
**우선순위**: 낮음 (기능에 영향 없음)

---
**작성**: 2026-03-07 23:16 KST