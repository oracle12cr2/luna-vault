# PostgreSQL 16 → 17 업그레이드 가이드

**서버:** postgres01 (192.168.50.16)  
**OS:** Oracle Linux 9.7  
**방법:** pg_upgrade (데이터 보존)  
**접속:** `ssh kto2005@192.168.50.16`

---

## 사전 확인

```bash
# 현재 버전 확인
psql --version

# 데이터 디렉토리 확인
sudo ls /var/lib/pgsql/data/

# 디스크 여유공간 확인 (현재 데이터의 2배 필요)
df -h /var/lib/pgsql

# 데이터베이스 목록 확인
sudo su - postgres -c "psql -l"
```

---

## STEP 1. PostgreSQL 17 설치

```bash
# PostgreSQL 공식 저장소 추가
sudo dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm

# 기본 PostgreSQL 모듈 비활성화
sudo dnf -qy module disable postgresql

# PostgreSQL 17 설치
sudo dnf install -y postgresql17 postgresql17-server postgresql17-contrib

# 설치 확인
/usr/pgsql-17/bin/postgres --version
```

---

## STEP 2. 기존 데이터 백업

```bash
# 백업 디렉토리 생성
sudo mkdir -p /var/lib/pgsql/backups

# 데이터 디렉토리 복사 백업
sudo cp -a /var/lib/pgsql/data /var/lib/pgsql/backups/pg16_backup_$(date +%Y%m%d)

echo "백업 완료"
```

---

## STEP 3. PostgreSQL 17 데이터 디렉토리 초기화

```bash
# 디렉토리 생성 및 권한 설정
sudo mkdir -p /var/lib/pgsql/17
sudo chown postgres:postgres /var/lib/pgsql/17

# initdb 실행
sudo su - postgres -c "/usr/pgsql-17/bin/initdb \
    --pgdata=/var/lib/pgsql/17/data \
    --encoding=UTF8 \
    --locale=ko_KR.UTF-8 \
    --auth-local=peer \
    --auth-host=md5"
```

---

## STEP 4. 호환성 검사 (--check)

> 실제 업그레이드 전 문제 없는지 확인 (데이터 변경 없음)

```bash
sudo su - postgres -c "/usr/pgsql-17/bin/pg_upgrade \
    --old-datadir=/var/lib/pgsql/data \
    --new-datadir=/var/lib/pgsql/17/data \
    --old-bindir=/usr/bin \
    --new-bindir=/usr/pgsql-17/bin \
    --check"
```

✅ `Clusters are compatible` 메시지 확인 후 다음 단계

---

## STEP 5. PostgreSQL 16 중지

```bash
sudo systemctl stop postgresql
# 또는
sudo su - postgres -c "pg_ctl stop -D /var/lib/pgsql/data -m fast"

# 중지 확인
sudo systemctl status postgresql
```

---

## STEP 6. pg_upgrade 실행 (실제 업그레이드)

```bash
# 수분 소요
sudo su - postgres -c "/usr/pgsql-17/bin/pg_upgrade \
    --old-datadir=/var/lib/pgsql/data \
    --new-datadir=/var/lib/pgsql/17/data \
    --old-bindir=/usr/bin \
    --new-bindir=/usr/pgsql-17/bin \
    --jobs=4"
```

---

## STEP 7. 설정 파일 마이그레이션

```bash
# pg_hba.conf 복사 (접속 권한 설정)
sudo cp /var/lib/pgsql/data/pg_hba.conf /var/lib/pgsql/17/data/pg_hba.conf

# postgresql.conf 주요 설정 확인 후 수동 반영
sudo diff /var/lib/pgsql/data/postgresql.conf /var/lib/pgsql/17/data/postgresql.conf
# listen_addresses, max_connections, shared_buffers 등 기존 값으로 변경
sudo vi /var/lib/pgsql/17/data/postgresql.conf
```

---

## STEP 8. PostgreSQL 17 서비스 시작

```bash
# PostgreSQL 17 서비스 등록 및 시작
sudo systemctl enable postgresql-17
sudo systemctl start postgresql-17

# 상태 확인
sudo systemctl status postgresql-17
```

---

## STEP 9. 검증

```bash
# 버전 확인
sudo su - postgres -c "psql -c 'SELECT version();'"

# DB 목록 확인
sudo su - postgres -c "psql -l"

# 통계정보 재수집 (업그레이드 후 필수)
sudo su - postgres -c "/usr/pgsql-17/bin/vacuumdb --all --analyze-in-stages"
```

---

## STEP 10. 정리 (안정화 후 1주일 뒤)

```bash
# pg_upgrade가 생성한 구버전 삭제 스크립트 실행
sudo su - postgres -c "bash /var/lib/pgsql/delete_old_cluster.sh"

# PostgreSQL 16 패키지 제거
sudo dnf remove postgresql16*
```

---

## 롤백 방법 (문제 발생 시)

```bash
# PostgreSQL 17 중지
sudo systemctl stop postgresql-17

# PostgreSQL 16 재시작
sudo systemctl start postgresql

# 데이터 복구 (필요시)
sudo cp -a /var/lib/pgsql/backups/pg16_backup_YYYYMMDD /var/lib/pgsql/data
```

---

## 참고

| 항목 | 경로 |
|------|------|
| PG16 데이터 | `/var/lib/pgsql/data` |
| PG17 데이터 | `/var/lib/pgsql/17/data` |
| PG16 바이너리 | `/usr/bin/postgres` |
| PG17 바이너리 | `/usr/pgsql-17/bin/postgres` |
| 백업 위치 | `/var/lib/pgsql/backups/` |
