FROM wiremock/wiremock:3x-alpine

USER root

# Add Python 3 and pip, then install FastAPI + requests for the adapter service
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir --break-system-packages \
        fastapi==0.135.0 \
        uvicorn==0.32.0 \
        requests==2.32.3 \
        pydantic==2.9.0

RUN mkdir -p /service/wiremock-data/mappings /service/wiremock-data/__files

WORKDIR /service

COPY docker/utilities/wiremock/main.py .
COPY docker/utilities/wiremock/start.sh .
RUN chmod +x /service/start.sh

# 8130 — MCPwner adapter (FastAPI)
# 8080 — WireMock admin + mock traffic (internal only)
EXPOSE 8130

ENTRYPOINT []
CMD ["/service/start.sh"]
