#!/bin/bash
# Kafka/Debezium CDC 모니터링 스크립트
# 체크 대상: Docker 컨테이너 + Debezium 커넥터 상태

MAIL_TO="kto2004@naver.com"
MAIL_FROM="kto2004@naver.com"
HOSTNAME=$(hostname)
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
ALERT=""

# 1. Docker 컨테이너 상태 체크
for container in zookeeper kafka connect; do
    STATUS=$(docker inspect -f '{{.State.Running}}' $container 2>/dev/null)
    if [ "$STATUS" != "true" ]; then
        ALERT="${ALERT}<tr><td style='color:red;font-weight:bold;'>❌ DOWN</td><td>${container}</td><td>컨테이너가 실행 중이 아닙니다</td></tr>"
    fi
done

# 2. Debezium 커넥터 상태 체크
for connector in oracle-cdc pg-sink-all; do
    RESULT=$(curl -s --max-time 5 http://localhost:8083/connectors/${connector}/status 2>/dev/null)
    if [ -z "$RESULT" ]; then
        ALERT="${ALERT}<tr><td style='color:red;font-weight:bold;'>❌ NO RESPONSE</td><td>${connector}</td><td>Connect API 응답 없음</td></tr>"
        continue
    fi

    CONN_STATE=$(echo "$RESULT" | python3 -c "import sys,json; print(json.loads(sys.stdin.read())['connector']['state'])" 2>/dev/null)
    TASK_STATE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.loads(sys.stdin.read()); print(d['tasks'][0]['state'] if d.get('tasks') else 'NO_TASK')" 2>/dev/null)

    if [ "$CONN_STATE" != "RUNNING" ]; then
        ALERT="${ALERT}<tr><td style='color:red;font-weight:bold;'>❌ ${CONN_STATE}</td><td>${connector} (connector)</td><td>커넥터 상태 비정상</td></tr>"
    fi
    if [ "$TASK_STATE" != "RUNNING" ]; then
        TRACE=$(echo "$RESULT" | python3 -c "
import sys,json
d=json.loads(sys.stdin.read())
t=d.get('tasks',[{}])[0]
trace=t.get('trace','')
for l in trace.split(chr(10)):
    if 'Caused by' in l:
        print(l.strip()[:150])
        break
" 2>/dev/null)
        ALERT="${ALERT}<tr><td style='color:red;font-weight:bold;'>❌ ${TASK_STATE}</td><td>${connector} (task-0)</td><td>${TRACE:-Task 상태 비정상}</td></tr>"
    fi
done

# 3. Kafka 브로커 체크
BROKER_CHECK=$(docker exec kafka /kafka/bin/kafka-topics.sh --list --bootstrap-server localhost:9092 2>&1 | head -1)
if echo "$BROKER_CHECK" | grep -qi "error\|exception\|refused"; then
    ALERT="${ALERT}<tr><td style='color:red;font-weight:bold;'>❌ ERROR</td><td>Kafka Broker</td><td>브로커 연결 실패</td></tr>"
fi

# 알림 있을 때만 메일 발송
if [ -n "$ALERT" ]; then
    HTML="<!DOCTYPE html><html><head><meta charset='utf-8'></head>
<body style='font-family: sans-serif; padding: 20px;'>
<h2 style='color: #e74c3c;'>🚨 CDC 파이프라인 장애 알림</h2>
<p>서버: ${HOSTNAME} | 시간: ${TIMESTAMP}</p>
<table border='1' cellpadding='8' cellspacing='0' style='border-collapse: collapse; width: 100%;'>
<tr style='background: #e74c3c; color: white;'><th>상태</th><th>대상</th><th>상세</th></tr>
${ALERT}
</table>
<hr>
<p style='color: #999;'>확인: <code>docker ps</code> / <code>curl http://localhost:8083/connectors</code></p>
<p style='color: #999;'>복구: <code>docker compose -f ~/debezium/docker-compose.yml up -d</code></p>
</body></html>"

    (
    echo "From: ${MAIL_FROM}"
    echo "To: ${MAIL_TO}"
    echo "Subject: =?UTF-8?B?$(echo -n "[CDC 장애] ${HOSTNAME} - Kafka/Debezium 이상 감지" | base64 -w0)?="
    echo "MIME-Version: 1.0"
    echo "Content-Type: text/html; charset=UTF-8"
    echo "Content-Transfer-Encoding: base64"
    echo ""
    echo "$HTML" | base64 -w76
    ) | /usr/sbin/sendmail -t

    echo "[${TIMESTAMP}] ALERT SENT: ${ALERT}" >> /var/log/kafka_monitor.log
else
    echo "[${TIMESTAMP}] OK - All services running" >> /var/log/kafka_monitor.log
fi
