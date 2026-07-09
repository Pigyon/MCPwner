ARG TERRASCAN_VERSION=1.19.9
FROM tenable/terrascan:${TERRASCAN_VERSION} AS terrascan

FROM python:3.11-alpine AS deps

COPY docker/iac/terrascan/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine

RUN apk add --no-cache gcompat

COPY --from=terrascan /go/bin/terrascan /usr/local/bin/terrascan
COPY --from=deps /install /usr/local

# Pre-fetch policies at build time; terrascan init/go-git is flaky in Docker.
ARG TERRASCAN_VERSION=1.19.9
ENV HOME=/home/scanner
ENV TERRASCAN_VERSION=${TERRASCAN_VERSION}
RUN apk add --no-cache curl ca-certificates \
    && adduser -D -h /home/scanner scanner \
    && for attempt in 1 2 3 4 5; do \
         curl -fsSL \
           "https://github.com/tenable/terrascan/archive/refs/tags/v${TERRASCAN_VERSION}.tar.gz" \
           | tar -xz -C /home/scanner \
         && mv "/home/scanner/terrascan-${TERRASCAN_VERSION}" /home/scanner/.terrascan \
         && break; \
         echo "Policy download failed (attempt ${attempt}/5); retrying in 10s..."; \
         sleep 10; \
       done \
    && test -d /home/scanner/.terrascan/pkg/policies/opa/rego \
    && chown -R scanner:scanner /home/scanner \
    && chmod -R a+rX /home/scanner/.terrascan

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/terrascan/main.py .
COPY docker/iac/terrascan/start.sh .

RUN chmod +x /service/start.sh \
    && chown -R scanner:scanner /service

USER scanner

EXPOSE 8142

CMD ["/service/start.sh"]
