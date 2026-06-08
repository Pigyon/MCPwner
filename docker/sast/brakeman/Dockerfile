# Stage 1: Install brakeman gem
FROM ruby:3.2-slim AS builder

RUN gem install brakeman --no-document

# Stage 2: Slim runtime
FROM ruby:3.2-slim

# Copy full gem environment from builder (gems + binstubs)
COPY --from=builder /usr/local/bundle /usr/local/bundle

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Install the Python deps into an isolated virtualenv instead of
# --break-system-packages (PEP 668). A venv is self-contained on its own
# sys.path, which also avoids Debian's site-packages/dist-packages split that
# breaks the bare --prefix=/install copy pattern on system-python bases.
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY docker/sast/brakeman/requirements.txt .
RUN python3 -m venv "$VIRTUAL_ENV" && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/brakeman/main.py .

EXPOSE 8085

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
