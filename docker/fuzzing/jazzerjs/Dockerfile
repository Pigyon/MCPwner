# @jazzer.js/core@4.0.0 needs glibc>=2.38; use Ubuntu 24.04 + Node 20 from NodeSource.
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg python3 python3-venv \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# bug-detectors must be a top-level sibling of core; NODE_PATH resolves global @babel/core.
ENV NODE_PATH=/usr/lib/node_modules

RUN npm install -g @jazzer.js/core@4.0.0 @jazzer.js/bug-detectors@4.0.0 @babel/core@7.29.7

COPY docker/fuzzing/jazzerjs/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/svc \
    && /opt/svc/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/fuzzing/jazzerjs/main.py .

EXPOSE 8152

CMD ["/opt/svc/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8152"]
