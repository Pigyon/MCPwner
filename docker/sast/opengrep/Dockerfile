FROM python:3.11-alpine AS deps

COPY docker/sast/opengrep/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM ipvsix/opengrep:1.16.4

RUN apk add --no-cache curl git

COPY --from=deps /install /usr/local

# Bundle rules at build time; --config auto would fetch the registry on the internal network.
ARG SEMGREP_RULES_REF=develop
RUN git clone --depth 1 --branch "${SEMGREP_RULES_REF}" \
    https://github.com/semgrep/semgrep-rules /opt/semgrep-rules && \
    rm -rf /opt/semgrep-rules/.git
ENV OPENGREP_DEFAULT_CONFIG=/opt/semgrep-rules

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/opengrep/main.py .

EXPOSE 8096

ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8096"]
