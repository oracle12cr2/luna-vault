#!/bin/bash

# Test script to verify us_market_report.py works in cron environment
echo "Testing US Market Report Script for Cron Compatibility"
echo "Date: $(date)"
echo "===================="

cd /root/.openclaw/workspace/stock
/root/.openclaw/workspace/stock/us_market_report.py > /tmp/market_test_output.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Script executed successfully"
    echo "📊 Report generated at: /root/.openclaw/workspace/stock/reports/us_market_$(date +%Y%m%d).txt"
    echo "💬 Chat summary:"
    echo "===================="
    tail -8 /tmp/market_test_output.log
else
    echo "❌ Script failed"
    cat /tmp/market_test_output.log
fi