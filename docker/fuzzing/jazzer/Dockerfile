# Full JDK for in-image harness builds; MCPwner service runs in Python venv, shells out to jazzer.
FROM eclipse-temurin:17-jdk-jammy

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Jazzer standalone tarball extracts flat; /opt/jazzer is on PATH.
ARG JAZZER_VERSION=0.30.0
RUN mkdir -p /opt/jazzer \
    && curl -fsSL "https://github.com/CodeIntelligenceTesting/jazzer/releases/download/v${JAZZER_VERSION}/jazzer-linux-x86-64.tar.gz" \
       | tar -xz -C /opt/jazzer
ENV PATH="/opt/jazzer:${PATH}" \
    JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=/var/tmp"

COPY docker/fuzzing/jazzer/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/svc \
    && /opt/svc/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/fuzzing/jazzer/main.py .

EXPOSE 8151

CMD ["/opt/svc/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8151"]
