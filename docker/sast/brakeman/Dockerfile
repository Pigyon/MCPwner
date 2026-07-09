FROM ruby:3.2-slim AS builder

# Brakeman 7+ needs prism compiled via build-essential; Ruby 3.2 does not bundle it.
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    gem install brakeman prism --no-document && \
    rm -rf /var/lib/apt/lists/*

FROM ruby:3.2-slim

COPY --from=builder /usr/local/bundle /usr/local/bundle

RUN apt-get update && \
    apt-get install -y --no-install-recommends python3 python3-venv && \
    rm -rf /var/lib/apt/lists/*

# Venv avoids PEP 668 and Debian's site-packages/dist-packages split on system python.
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
