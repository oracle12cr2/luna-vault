#!/bin/bash
export ORACLE_HOME=/usr/lib/oracle/23/client64
export LD_LIBRARY_PATH=$ORACLE_HOME/lib
cd /root/.openclaw/workspace/ora2pg

echo "=== 1. TABLE DDL 변환 ==="
ora2pg -c ora2pg.conf -t TABLE -o table.sql 2>&1
echo ""

echo "=== 2. INDEX 변환 ==="
ora2pg -c ora2pg.conf -t INDEX -o index.sql 2>&1
echo ""

echo "=== 3. FUNCTION 변환 ==="
ora2pg -c ora2pg.conf -t FUNCTION -o function.sql 2>&1
echo ""

echo "=== 4. SEQUENCE 변환 ==="
ora2pg -c ora2pg.conf -t SEQUENCE -o sequence.sql 2>&1
echo ""

echo "=== 완료! ==="
ls -la output/
