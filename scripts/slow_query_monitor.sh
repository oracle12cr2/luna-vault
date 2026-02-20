#!/bin/bash
# 슬로우 쿼리 모니터링 스크립트
# 매일 1회 실행, 최근 24시간 내 슬로우 쿼리 리포트

DB_USER="app_user"
DB_PASS="oracle"
DB_HOST="192.168.50.31"
DB_PORT="1521"
DB_SERVICE="PROD"
THRESHOLD_SEC=3
MAIL_TO="kto2004@naver.com"
MAIL_SUBJECT="[PROD DB] 슬로우 쿼리 리포트 - $(date '+%Y-%m-%d %H:%M')"

CONN_STR="${DB_USER}/${DB_PASS}@${DB_HOST}:${DB_PORT}/${DB_SERVICE}"

# Top 20 슬로우 쿼리 (누적 실행시간 기준)
TOP_SLOW=$(sqlplus -s "$CONN_STR" <<EOSQL
SET PAGESIZE 50
SET LINESIZE 200
SET FEEDBACK OFF
SET HEADING ON
COL SQL_ID FORMAT A15
COL ELAPSED_SEC FORMAT 999,999,999.99
COL AVG_SEC FORMAT 999,999.99
COL EXECUTIONS FORMAT 999,999,999
COL SQL_TEXT FORMAT A80

SELECT sql_id,
       ROUND(elapsed_time/1000000, 2) AS ELAPSED_SEC,
       executions,
       CASE WHEN executions > 0 THEN ROUND(elapsed_time/1000000/executions, 2) ELSE 0 END AS AVG_SEC,
       SUBSTR(sql_text, 1, 80) AS SQL_TEXT
FROM v\$sql
WHERE elapsed_time/1000000 > ${THRESHOLD_SEC}
  AND parsing_schema_name NOT IN ('SYS','SYSTEM','DBSNMP','SYSMAN')
  AND last_active_time > SYSDATE - 1
ORDER BY elapsed_time DESC
FETCH FIRST 20 ROWS ONLY;
EOSQL
)

# 현재 실행 중인 긴 쿼리 (10초 이상)
RUNNING=$(sqlplus -s "$CONN_STR" <<EOSQL2
SET PAGESIZE 50
SET LINESIZE 200
SET FEEDBACK OFF
SET HEADING ON
COL USERNAME FORMAT A15
COL SID FORMAT 99999
COL SQL_ID FORMAT A15
COL RUNTIME_SEC FORMAT 999,999
COL SQL_TEXT FORMAT A70

SELECT s.username,
       s.sid,
       s.sql_id,
       ROUND((SYSDATE - s.sql_exec_start) * 86400) AS RUNTIME_SEC,
       SUBSTR(q.sql_text, 1, 70) AS SQL_TEXT
FROM v\$session s
JOIN v\$sql q ON s.sql_id = q.sql_id AND s.sql_child_number = q.child_number
WHERE s.status = 'ACTIVE'
  AND s.username IS NOT NULL
  AND s.username NOT IN ('SYS','SYSTEM','DBSNMP')
  AND (SYSDATE - s.sql_exec_start) * 86400 > ${THRESHOLD_SEC}
ORDER BY RUNTIME_SEC DESC;
EOSQL2
)

SLOW_COUNT=$(echo "$TOP_SLOW" | grep -c "^[a-z0-9]")
RUNNING_COUNT=$(echo "$RUNNING" | grep -c "^[A-Z]")

# 메일 본문
MAIL_BODY="━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROD DB 슬로우 쿼리 리포트
일시: $(date '+%Y-%m-%d %H:%M:%S')
서버: ${DB_HOST}:${DB_PORT}/${DB_SERVICE}
기준: ${THRESHOLD_SEC}초 이상
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[현재 실행 중인 슬로우 쿼리]

${RUNNING:-없음}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[최근 24시간 Top 20 슬로우 쿼리 (누적)]

${TOP_SLOW:-없음}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
자동 생성 by 루나 🌙"

if [ "$RUNNING_COUNT" -gt 0 ]; then
    MAIL_SUBJECT="🔴 ${MAIL_SUBJECT} (실행중 ${RUNNING_COUNT}건)"
elif [ "$SLOW_COUNT" -gt 0 ]; then
    MAIL_SUBJECT="🟡 ${MAIL_SUBJECT} (${SLOW_COUNT}건)"
else
    MAIL_SUBJECT="✅ ${MAIL_SUBJECT} (없음)"
fi

TMPHTML=$(mktemp /tmp/slow_report.XXXXXX.html)
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

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 슬로우 쿼리 메일 발송 완료 (Top: ${SLOW_COUNT}건, Running: ${RUNNING_COUNT}건) -> ${MAIL_TO}"

# 카카오 알림
if [ "$RUNNING_COUNT" -gt 0 ]; then
    python3 /usr/local/bin/kakao_notify.py "PROD DB 슬로우 쿼리" "현재 실행 중인 슬로우 쿼리 ${RUNNING_COUNT}건 감지" "error"
elif [ "$SLOW_COUNT" -gt 0 ]; then
    python3 /usr/local/bin/kakao_notify.py "PROD DB 슬로우 쿼리" "최근 24시간 슬로우 쿼리 ${SLOW_COUNT}건 감지" "error"
fi
