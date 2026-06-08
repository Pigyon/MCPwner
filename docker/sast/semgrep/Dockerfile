# Stage 1: Install semgrep and deps
FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY docker/sast/semgrep/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Slim runtime
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Keep semgrep fully offline: don't phone home for update checks (which otherwise
# hangs 'semgrep --version' past the health-check timeout) or metrics.
ENV SEMGREP_ENABLE_VERSION_CHECK=0 \
    SEMGREP_SEND_METRICS=off

# Bundle the official ruleset at build time (build has network access) so the
# scanner works fully offline at runtime — the SAST network is internal:true and
# 'semgrep --config auto' would otherwise need to reach semgrep.dev.
ARG SEMGREP_RULES_REF=develop
RUN git clone --depth 1 --branch "${SEMGREP_RULES_REF}" \
    https://github.com/semgrep/semgrep-rules /opt/semgrep-rules && \
    rm -rf /opt/semgrep-rules/.git
ENV SEMGREP_DEFAULT_CONFIG=/opt/semgrep-rules

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/semgrep/main.py .

EXPOSE 8082

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8082"]
