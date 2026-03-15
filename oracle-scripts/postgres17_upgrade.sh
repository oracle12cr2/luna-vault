#!/bin/bash
# ============================================================
# PostgreSQL 16 → 17 업그레이드 스크립트
# OS: Oracle Linux 9.7
# 방법: pg_upgrade (데이터 보존, 빠른 업그레이드)
# 실행: sudo bash postgres17_upgrade.sh
# ============================================================

set -e  # 오류 시 즉시 중단

OLD_VER=16
NEW_VER=17
OLD_DATA=/var/lib/pgsql/data
NEW_DATA=/var/lib/pgsql/17/data
OLD_BIN=/usr/bin
NEW_BIN=/usr/pgsql-17/bin
BACKUP_DIR=/var/lib/pgsql/backups/pg16_backup_$(date +%Y%m%d_%H%M%S)

echo "============================================================"
echo "PostgreSQL ${OLD_VER} → ${NEW_VER} 업그레이드 시작"
echo "============================================================"

# ============================================================
# STEP 1. PostgreSQL 17 설치
# ============================================================
echo ""
echo "STEP 1. PostgreSQL 17 설치..."

# PostgreSQL 공식 저장소 추가
dnf install -y https://download.postgresql.org/pub/repos/yum/reporpms/EL-9-x86_64/pgdg-redhat-repo-latest.noarch.rpm 2>/dev/null || true

# 기본 PostgreSQL 모듈 비활성화 (OL9)
dnf -qy module disable postgresql 2>/dev/null || true

# PostgreSQL 17 설치
dnf install -y postgresql17 postgresql17-server postgresql17-contrib

echo "PostgreSQL 17 설치 완료"
echo "버전 확인: $($NEW_BIN/postgres --version)"

# ============================================================
# STEP 2. 기존 데이터 백업
# ============================================================
echo ""
echo "STEP 2. 기존 데이터 백업..."
mkdir -p $BACKUP_DIR

# pg_dumpall로 논리 백업 (PostgreSQL 16이 실행 중인 경우)
# 현재 중지 상태이므로 디렉토리 복사로 백업
cp -a $OLD_DATA $BACKUP_DIR/data_backup
echo "백업 완료: $BACKUP_DIR"

# ============================================================
# STEP 3. PostgreSQL 17 초기화
# ============================================================
echo ""
echo "STEP 3. PostgreSQL 17 데이터 디렉토리 초기화..."

mkdir -p /var/lib/pgsql/17
chown postgres:postgres /var/lib/pgsql/17

su - postgres -c "$NEW_BIN/initdb \
    --pgdata=$NEW_DATA \
    --encoding=UTF8 \
    --locale=ko_KR.UTF-8 \
    --auth-local=peer \
    --auth-host=md5"

echo "초기화 완료"

# ============================================================
# STEP 4. pg_upgrade 호환성 검사
# ============================================================
echo ""
echo "STEP 4. pg_upgrade 호환성 검사 (--check)..."

su - postgres -c "$NEW_BIN/pg_upgrade \
    --old-datadir=$OLD_DATA \
    --new-datadir=$NEW_DATA \
    --old-bindir=$OLD_BIN \
    --new-bindir=$NEW_BIN \
    --check"

echo "호환성 검사 통과!"

# ============================================================
# STEP 5. PostgreSQL 16 중지 확인
# ============================================================
echo ""
echo "STEP 5. PostgreSQL 16 중지 확인..."
systemctl stop postgresql 2>/dev/null || true
su - postgres -c "$OLD_BIN/pg_ctl stop -D $OLD_DATA -m fast" 2>/dev/null || true
echo "PostgreSQL 16 중지됨"

# ============================================================
# STEP 6. pg_upgrade 실행 (실제 업그레이드)
# ============================================================
echo ""
echo "STEP 6. pg_upgrade 실행 중... (수분 소요)"

su - postgres -c "$NEW_BIN/pg_upgrade \
    --old-datadir=$OLD_DATA \
    --new-datadir=$NEW_DATA \
    --old-bindir=$OLD_BIN \
    --new-bindir=$NEW_BIN \
    --jobs=4"

echo "pg_upgrade 완료!"

# ============================================================
# STEP 7. postgresql.conf 설정 복사
# ============================================================
echo ""
echo "STEP 7. 설정 파일 마이그레이션..."

# 기존 설정에서 주요 파라미터 복사
OLD_CONF=$OLD_DATA/postgresql.conf
NEW_CONF=$NEW_DATA/postgresql.conf

# listen_addresses
OLD_LISTEN=$(grep "^listen_addresses" $OLD_CONF 2>/dev/null | head -1)
[ -n "$OLD_LISTEN" ] && sed -i "s/^#listen_addresses.*/$OLD_LISTEN/" $NEW_CONF

# max_connections
OLD_MAXCONN=$(grep "^max_connections" $OLD_CONF 2>/dev/null | head -1)
[ -n "$OLD_MAXCONN" ] && sed -i "s/^max_connections.*/$OLD_MAXCONN/" $NEW_CONF

# shared_buffers
OLD_SHM=$(grep "^shared_buffers" $OLD_CONF 2>/dev/null | head -1)
[ -n "$OLD_SHM" ] && sed -i "s/^shared_buffers.*/$OLD_SHM/" $NEW_CONF

# pg_hba.conf 복사
cp $OLD_DATA/pg_hba.conf $NEW_DATA/pg_hba.conf
echo "설정 복사 완료"

# ============================================================
# STEP 8. systemd 서비스 설정 변경
# ============================================================
echo ""
echo "STEP 8. systemd 서비스 설정..."

# postgresql-17 서비스 활성화
systemctl enable postgresql-17
systemctl start postgresql-17

sleep 3
systemctl status postgresql-17 | grep -E "Active|running"

# ============================================================
# STEP 9. 검증
# ============================================================
echo ""
echo "STEP 9. 업그레이드 검증..."

su - postgres -c "psql -c \"SELECT version();\""
su - postgres -c "psql -l"
su - postgres -c "psql -c \"SELECT count(*) FROM pg_database;\""

echo ""
echo "============================================================"
echo "✅ PostgreSQL 17 업그레이드 완료!"
echo "============================================================"
echo ""
echo "다음 작업:"
echo "  1. 통계정보 수집: su - postgres -c '$NEW_BIN/vacuumdb --all --analyze-in-stages'"
echo "  2. 구버전 제거: ./delete_old_cluster.sh (pg_upgrade가 생성)"
echo "  3. 구버전 패키지 제거: dnf remove postgresql16*"
echo ""
echo "롤백 방법:"
echo "  systemctl stop postgresql-17"
echo "  systemctl start postgresql  # PostgreSQL 16 재시작"
