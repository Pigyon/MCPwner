FROM mcr.microsoft.com/cstsectools/codeql-container@sha256:0fd52101e30652e0998be85f6e09ac59534c6f40cebb670acd77b78869c45bc2

USER root

ENV GO_VERSION=1.23.2
ENV GO_SHA256=542d3c1705f1c6a1c5a80d5dc62e2e45171af291e755d591c5e6531ef63b454e
RUN apt-get update && \
    apt-get install -y python3 python3-pip curl gnupg && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    echo "${GO_SHA256}  go${GO_VERSION}.linux-amd64.tar.gz" | sha256sum -c - && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=$PATH:/usr/local/go/bin

# Vendor CodeQL 2.15.5 lacks --build-mode=none; bundle v2.20.3 supports offline SAST builds.
ARG CODEQL_BUNDLE_URL=https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.20.3/codeql-bundle-linux64.tar.gz
RUN curl -fsSL "$CODEQL_BUNDLE_URL" -o /tmp/codeql-bundle.tar.gz && \
    mkdir -p /opt && tar -xzf /tmp/codeql-bundle.tar.gz -C /opt && \
    rm /tmp/codeql-bundle.tar.gz && \
    chmod -R a+rX /opt/codeql
ENV PATH=/opt/codeql:$PATH

# World-executable bits so cap_drop:ALL (no DAC_OVERRIDE) does not deny runtime access.
RUN chmod -R a+rX /usr/local/codeql-home/codeql/

WORKDIR /service

# Debian system python reads dist-packages, not pip --prefix site-packages; install deps in-place.
COPY docker/codeql/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY docker/codeql/main.py .

EXPOSE 8080

ENTRYPOINT []

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
