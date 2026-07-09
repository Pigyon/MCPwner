FROM mitmproxy/mitmproxy:12

# Python 3.14 needs pydantic>=2.10 with pre-built wheels; older pydantic-core requires Rust.
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0,<1.0" \
    "uvicorn==0.32.0" \
    "pydantic>=2.10.0,<3.0" \
    "requests==2.32.3"

WORKDIR /service

COPY docker/utilities/mitmproxy/main.py .

EXPOSE 8131

# Base entrypoint needs CAP_SETUID; clear it for cap_drop:ALL and /service workdir.
ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8131"]
