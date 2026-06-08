# Stage 1: Build PHP extensions and install Composer
# Pin by digest for byte-for-byte reproducibility (tag 6.9.1 as of 2026-06-06)
FROM ghcr.io/danog/psalm:6.9.1@sha256:99992b00695c29ceebf152d705a26e512ba24f4fd968908d5add8c25c05aeef3 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

ADD https://github.com/mlocati/docker-php-extension-installer/releases/latest/download/install-php-extensions /usr/local/bin/
RUN chmod +x /usr/local/bin/install-php-extensions && \
    install-php-extensions zip

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Stage 2: Runtime
FROM ghcr.io/danog/psalm:6.9.1@sha256:99992b00695c29ceebf152d705a26e512ba24f4fd968908d5add8c25c05aeef3

# Copy built PHP extensions from builder
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /usr/bin/composer /usr/bin/composer

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps into an isolated virtualenv instead of
# --break-system-packages (PEP 668).
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:/composer/vendor/bin:${PATH}"
COPY docker/sast/psalm/requirements.txt .
RUN python3 -m venv "$VIRTUAL_ENV" && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/psalm/main.py .
COPY docker/sast/psalm/psalm.xml /service/psalm.xml

EXPOSE 8087

ENTRYPOINT []
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8087"]
