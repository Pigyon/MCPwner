#!/bin/sh
set -e

# Start WireMock in the background on its standard admin port (8080)
java -jar /var/wiremock/lib/wiremock-standalone.jar \
    --port 8080 \
    --root-dir /service/wiremock-data \
    --no-request-journal=false &

WIREMOCK_PID=$!

# Wait for WireMock to become ready (up to 20 seconds)
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

# Start FastAPI adapter in foreground on port 8130
exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8130
