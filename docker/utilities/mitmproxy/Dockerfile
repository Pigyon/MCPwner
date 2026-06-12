FROM mitmproxy/mitmproxy:12

# mitmproxy:12 ships Python 3.14. pydantic-core <2.27 has no Python 3.14 wheel and
# requires Rust to build from source, which is not present in this image. Pin fastapi
# and pydantic loosely so pip resolves a version with pre-built 3.14 wheels.
RUN pip install --no-cache-dir \
    "fastapi>=0.115.0,<1.0" \
    "uvicorn==0.32.0" \
    "pydantic>=2.10.0,<3.0" \
    "requests==2.32.3"

WORKDIR /service

COPY docker/utilities/mitmproxy/main.py .

EXPOSE 8131

# The base image entrypoint does usermod/su-exec to set up the mitmproxy user.
# That conflicts with cap_drop: ALL (needs CAP_SETUID) and our /service workdir.
# Clear it so Docker runs our CMD directly.
ENTRYPOINT []
CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8131"]
