#!/bin/bash
# PostgreSQL 17 모니터링 스크립트
# 사용: ssh kto2005@192.168.50.16 'bash -s' < pg_monitor.sh

HOST="192.168.50.16"
PSQL="sudo -u postgres psql -X --no-align --tuples-only"

echo "========================================"
echo "🐘 PostgreSQL 모니터링 - $(date '+%Y-%m-%d %H:%M:%S')"
echo "========================================"

# 1. 기본 정보
echo ""
echo "📌 [기본 정보]"
$PSQL -c "SELECT version();"
echo "Uptime: $($PSQL -c "SELECT now() - pg_postmaster_start_time();")"
echo "DB Size: $($PSQL -c "SELECT pg_size_pretty(sum(pg_database_size(datname))) FROM pg_database;")"

# 2. 연결 상태
echo ""
echo "📌 [연결 상태]"
echo "활성 연결: $($PSQL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")"
echo "유휴 연결: $($PSQL -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';")"
echo "전체 연결: $($PSQL -c "SELECT count(*) FROM pg_stat_activity;")"
echo "최대 연결: $($PSQL -c "SHOW max_connections;")"

# 3. 데이터베이스별 크기
echo ""
echo "📌 [데이터베이스 크기]"
$PSQL -c "
SELECT datname AS db,
       pg_size_pretty(pg_database_size(datname)) AS size
FROM pg_database
WHERE datistemplate = false
ORDER BY pg_database_size(datname) DESC;
" | column -t -s'|'

# 4. 활성 쿼리 (1초 이상)
echo ""
echo "📌 [활성 쿼리 (1초+)]"
$PSQL -c "
SELECT pid, usename, state,
       now() - query_start AS duration,
       left(query, 80) AS query
FROM pg_stat_activity
WHERE state = 'active'
  AND query NOT LIKE '%pg_stat_activity%'
  AND now() - query_start > interval '1 second'
ORDER BY duration DESC
LIMIT 5;
" | column -t -s'|'

# 5. 잠금 대기
echo ""
echo "📌 [잠금 대기]"
LOCKS=$($PSQL -c "
SELECT count(*)
FROM pg_locks bl
JOIN pg_stat_activity a ON a.pid = bl.pid
WHERE NOT bl.granted;")
if [ "$LOCKS" = "0" ]; then
    echo "잠금 대기 없음 ✅"
else
    echo "⚠️ 잠금 대기: ${LOCKS}건"
    $PSQL -c "
    SELECT bl.pid, a.usename, a.query
    FROM pg_locks bl
    JOIN pg_stat_activity a ON a.pid = bl.pid
    WHERE NOT bl.granted
    LIMIT 5;"
fi

# 6. 캐시 히트율
echo ""
echo "📌 [캐시 히트율]"
$PSQL -c "
SELECT d.datname,
       round(s.blks_hit * 100.0 / NULLIF(s.blks_hit + s.blks_read, 0), 2) AS hit_ratio
FROM pg_stat_database s
JOIN pg_database d ON d.datname = s.datname
WHERE d.datistemplate = false AND s.blks_hit + s.blks_read > 0
ORDER BY d.datname;
" | while IFS='|' read db ratio; do
    if [ -n "$db" ]; then
        if (( $(echo "$ratio >= 99" | bc -l 2>/dev/null || echo 0) )); then
            echo "  $db: ${ratio}% ✅"
        elif (( $(echo "$ratio >= 90" | bc -l 2>/dev/null || echo 0) )); then
            echo "  $db: ${ratio}% ⚠️"
        else
            echo "  $db: ${ratio}% ❌"
        fi
    fi
done

# 7. 테이블 bloat (VACUUM 필요 여부)
echo ""
echo "📌 [VACUUM 필요 테이블 (dead tuple 많은 순)]"
$PSQL -c "
SELECT schemaname || '.' || relname AS table_name,
       n_dead_tup AS dead_tuples,
       n_live_tup AS live_tuples,
       last_autovacuum::text
FROM pg_stat_user_tables
WHERE n_dead_tup > 1000
ORDER BY n_dead_tup DESC
LIMIT 5;
" | column -t -s'|'
VACUUM_COUNT=$($PSQL -c "SELECT count(*) FROM pg_stat_user_tables WHERE n_dead_tup > 1000;")
if [ "$VACUUM_COUNT" = "0" ]; then
    echo "모두 깨끗 ✅"
fi

# 8. 디스크 사용량
echo ""
echo "📌 [디스크 사용량]"
PG_DATA=$($PSQL -c "SHOW data_directory;" | xargs)
df -h "$PG_DATA" 2>/dev/null | tail -1 | awk '{printf "  사용: %s / %s (%s)\n", $3, $2, $5}'
if [ -z "$(df -h "$PG_DATA" 2>/dev/null | tail -1)" ]; then
    df -h / | tail -1 | awk '{printf "  사용: %s / %s (%s)\n", $3, $2, $5}'
fi

# 9. 복제 상태
echo ""
echo "📌 [복제 상태]"
REP_COUNT=$($PSQL -c "SELECT count(*) FROM pg_stat_replication;")
if [ "$REP_COUNT" = "0" ]; then
    echo "복제 없음 (standalone)"
else
    $PSQL -c "
    SELECT client_addr, state, sent_lsn, replay_lsn,
           pg_wal_lsn_diff(sent_lsn, replay_lsn) AS lag_bytes
    FROM pg_stat_replication;"
fi

echo ""
echo "========================================"
echo "✅ 모니터링 완료"
echo "========================================"
