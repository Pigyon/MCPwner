# Jazzer.js runs on Node; the MCPwner HTTP service runs in an isolated Python
# venv and shells out to the global `jazzer` CLI provided by @jazzer.js/core.
#
# @jazzer.js/core@4.0.0's prebuilt native addon (fuzzer-linux-x64.node) requires
# GLIBC >= 2.38. Debian Bookworm ships 2.36, so we switch to Ubuntu 24.04 Noble
# (glibc 2.39) and install Node.js 20 via the NodeSource repository.
FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg python3 python3-venv \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Jazzer.js fuzzing CLI pinned to the requested version (provides the `jazzer` bin).
# @jazzer.js/bug-detectors must be installed as a top-level sibling of core —
# if it lands only as a nested dependency of core, the CLI path lookup fails.
# NODE_PATH lets require() resolve globally installed packages like @babel/core
# without needing them in a local node_modules directory.
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
