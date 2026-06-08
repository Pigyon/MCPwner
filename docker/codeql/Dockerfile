FROM mcr.microsoft.com/cstsectools/codeql-container@sha256:0fd52101e30652e0998be85f6e09ac59534c6f40cebb670acd77b78869c45bc2

# Run as root for installation
USER root

ENV GO_VERSION=1.23.2
ENV GO_SHA256=542d3c1705f1c6a1c5a80d5dc62e2e45171af291e755d591c5e6531ef63b454e
RUN apt-get update && \
    apt-get install -y python3 python3-pip curl gnupg && \
    # Install Node.js
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    curl -OL https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz && \
    echo "${GO_SHA256}  go${GO_VERSION}.linux-amd64.tar.gz" | sha256sum -c - && \
    tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz && \
    rm go${GO_VERSION}.linux-amd64.tar.gz && \
    # Cleanup
    rm -rf /var/lib/apt/lists/*

ENV PATH=$PATH:/usr/local/go/bin

# The vendor base ships CodeQL 2.15.5, which has no `--build-mode=none` and so
# can only build compiled languages (Java/C#) via an autobuilder that needs
# Maven + internet — impossible on the internal, network-less SAST network.
# Install the official CodeQL bundle (CLI + all query packs + extractors) which
# supports build-mode=none, and put it first on PATH. Downloaded at build time.
ARG CODEQL_BUNDLE_URL=https://github.com/github/codeql-action/releases/download/codeql-bundle-v2.20.3/codeql-bundle-linux64.tar.gz
RUN curl -fsSL "$CODEQL_BUNDLE_URL" -o /tmp/codeql-bundle.tar.gz && \
    mkdir -p /opt && tar -xzf /tmp/codeql-bundle.tar.gz -C /opt && \
    rm /tmp/codeql-bundle.tar.gz && \
    chmod -R a+rX /opt/codeql
ENV PATH=/opt/codeql:$PATH

# Ensure codeql binaries are world-executable so cap_drop:ALL (which removes
# DAC_OVERRIDE) doesn't cause "Permission denied" at runtime.
RUN chmod -R a+rX /usr/local/codeql-home/codeql/

WORKDIR /service

# Install Python service deps directly into the system interpreter.
# NOTE: the multi-stage --prefix=/install builder pattern used by the
# python:-image-based services does NOT work here: this base uses Debian's
# system python, which searches dist-packages (not the site-packages dir that
# pip --prefix produces), so a copied prefix is invisible at runtime.
# --no-cache-dir keeps pip's download cache out of the image layer.
COPY docker/codeql/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY docker/codeql/main.py .

# Expose service port
EXPOSE 8080

# Override the base image's entrypoint to avoid startup script issues
ENTRYPOINT []

# Run the FastAPI service with uvicorn
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
