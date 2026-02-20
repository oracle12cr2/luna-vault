#!/bin/bash
# 테이블스페이스 모니터링 스크립트
# 매일 1회 실행, 80% 이상 사용 시 메일 알림

DB_USER="app_user"
DB_PASS="oracle"
DB_HOST="192.168.50.31"
DB_PORT="1521"
DB_SERVICE="PROD"
THRESHOLD=95
MAIL_TO="kto2004@naver.com"
MAIL_SUBJECT="[PROD DB] 테이블스페이스 모니터링 리포트 - $(date '+%Y-%m-%d %H:%M')"

CONN_STR="${DB_USER}/${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_SERVICE}"

# 전체 현황 조회
ALL_RESULT=$(sqlplus -s "$CONN_STR" <<'EOSQL'
SET PAGESIZE 100
SET LINESIZE 150
SET FEEDBACK OFF
SET HEADING ON
COL TABLESPACE_NAME FORMAT A20
COL TOTAL_MB FORMAT 999,999,999
COL USED_MB FORMAT 999,999,999
COL FREE_MB FORMAT 999,999,999
COL PCT_USED FORMAT 999.99

SELECT a.tablespace_name,
       ROUND(a.total_bytes/1024/1024) AS TOTAL_MB,
       ROUND((a.total_bytes - NVL(b.free_bytes,0))/1024/1024) AS USED_MB,
       ROUND(NVL(b.free_bytes,0)/1024/1024) AS FREE_MB,
       ROUND((a.total_bytes - NVL(b.free_bytes,0))/a.total_bytes * 100, 2) AS PCT_USED
FROM (SELECT tablespace_name, SUM(bytes) total_bytes FROM dba_data_files GROUP BY tablespace_name) a
LEFT JOIN (SELECT tablespace_name, SUM(bytes) free_bytes FROM dba_free_space GROUP BY tablespace_name) b
ON a.tablespace_name = b.tablespace_name
ORDER BY PCT_USED DESC;
EOSQL
)

# 80% 이상 경고 대상
WARN_RESULT=$(sqlplus -s "$CONN_STR" <<EOSQL2
SET PAGESIZE 100
SET LINESIZE 150
SET FEEDBACK OFF
SET HEADING OFF
COL TABLESPACE_NAME FORMAT A20

SELECT a.tablespace_name || ' : ' || ROUND((a.total_bytes - NVL(b.free_bytes,0))/a.total_bytes * 100, 2) || '%'
FROM (SELECT tablespace_name, SUM(bytes) total_bytes FROM dba_data_files GROUP BY tablespace_name) a
LEFT JOIN (SELECT tablespace_name, SUM(bytes) free_bytes FROM dba_free_space GROUP BY tablespace_name) b
ON a.tablespace_name = b.tablespace_name
WHERE ROUND((a.total_bytes - NVL(b.free_bytes,0))/a.total_bytes * 100, 2) >= ${THRESHOLD}
ORDER BY 1;
EOSQL2
)

WARN_COUNT=$(echo "$WARN_RESULT" | grep -c '%')

# 메일 본문 구성
MAIL_BODY="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROD DB 테이블스페이스 모니터링 리포트
일시: $(date '+%Y-%m-%d %H:%M:%S')
서버: ${DB_HOST}:${DB_PORT}/${DB_SERVICE}
임계치: ${THRESHOLD}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"

if [ "$WARN_COUNT" -gt 0 ]; then
    MAIL_BODY+="⚠️  경고! ${WARN_COUNT}개 테이블스페이스가 ${THRESHOLD}% 이상입니다:

${WARN_RESULT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"
    MAIL_SUBJECT="⚠️ ${MAIL_SUBJECT}"
else
    MAIL_BODY+="✅ 모든 테이블스페이스 정상 (${THRESHOLD}% 미만)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"
fi

MAIL_BODY+="[전체 현황]

${ALL_RESULT}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
자동 생성 by 루나 🌙"

TMPHTML=$(mktemp /tmp/tbs_report.XXXXXX.html)
cat > "$TMPHTML" <<EOHTML
<html>
<head><meta charset="UTF-8"></head>
<body>
<pre style="font-family:'Courier New',Courier,monospace;font-size:13px;">
$(echo "$MAIL_BODY")
</pre>
</body>
</html>
EOHTML

sendmail -t <<EOMAIL
To: ${MAIL_TO}
Subject: ${MAIL_SUBJECT}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8

$(cat "$TMPHTML")
EOMAIL

rm -f "$TMPHTML"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 메일 발송 완료 (경고: ${WARN_COUNT}건) -> ${MAIL_TO}"

# 카카오 알림
if [ "$WARN_COUNT" -gt 0 ]; then
    KAKAO_MSG="[TBS 경고] ${WARN_COUNT}개 테이블스페이스 ${THRESHOLD}% 초과
${WARN_RESULT}"
    python3 /usr/local/bin/kakao_notify.py "PROD DB 테이블스페이스 경고" "${KAKAO_MSG}" "error"
fi
