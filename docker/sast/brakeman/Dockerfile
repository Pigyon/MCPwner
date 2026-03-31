# Stage 1: Install brakeman gem
FROM ruby:3.2-slim AS builder

RUN gem install brakeman --no-document

# Stage 2: Slim runtime
FROM ruby:3.2-slim

# Copy full gem environment from builder (gems + binstubs)
COPY --from=builder /usr/local/bundle /usr/local/bundle

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-pip && \
    rm -rf /var/lib/apt/lists/*

COPY docker/sast/brakeman/requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/brakeman/main.py .

EXPOSE 8085

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8085"]
