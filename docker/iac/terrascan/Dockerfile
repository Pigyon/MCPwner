# Stage 1: terrascan binary
FROM tenable/terrascan:1.19.9 AS terrascan

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/iac/terrascan/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM python:3.11-alpine

RUN apk add --no-cache gcompat

COPY --from=terrascan /go/bin/terrascan /usr/local/bin/terrascan
COPY --from=deps /install /usr/local

# Pre-fetch Terrascan's policy bundle at build time, since the runtime network is
# internal-only. `terrascan init` clones the policies into $HOME/.terrascan; bake
# them under a fixed HOME and make them readable by the runtime user.
ENV HOME=/home/scanner
RUN adduser -D -h /home/scanner scanner \
    && terrascan init \
    && chown -R scanner:scanner /home/scanner \
    && chmod -R a+rX /home/scanner/.terrascan

WORKDIR /service

COPY docker/common /service/common
COPY docker/iac/terrascan/main.py .

RUN chown -R scanner:scanner /service

USER scanner

EXPOSE 8142

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8142"]
