#!/bin/sh
set -e

java -jar /var/wiremock/lib/wiremock-standalone.jar \
    --port 8080 \
    --root-dir /service/wiremock-data \
    --no-request-journal=false &

WIREMOCK_PID=$!

echo "Waiting for WireMock to start..."
i=0
while [ $i -lt 20 ]; do
    if wget -q -O /dev/null http://localhost:8080/__admin/health 2>/dev/null; then
        echo "WireMock is ready"
        break
    fi
    sleep 1
    i=$((i + 1))
done

exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8130
