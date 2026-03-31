# Stage 1: Build PHP extensions and install Composer
FROM ghcr.io/danog/psalm:6.9.1 AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

ADD https://github.com/mlocati/docker-php-extension-installer/releases/latest/download/install-php-extensions /usr/local/bin/
RUN chmod +x /usr/local/bin/install-php-extensions && \
    install-php-extensions zip

COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Stage 2: Runtime
FROM ghcr.io/danog/psalm:6.9.1

# Copy built PHP extensions from builder
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /usr/bin/composer /usr/bin/composer

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

COPY docker/sast/psalm/requirements.txt .
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt

ENV PATH="/composer/vendor/bin:${PATH}"

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/psalm/main.py .
COPY docker/sast/psalm/psalm.xml /service/psalm.xml

EXPOSE 8087

ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8087"]
