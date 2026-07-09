# pcntl extension required because php-fuzzer forks per input; service runs in Python venv.
FROM php:8.2-cli-bookworm

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

RUN docker-php-ext-install pcntl > /dev/null

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-venv git unzip \
    && rm -rf /var/lib/apt/lists/*

ENV COMPOSER_HOME=/opt/composer
RUN composer global require nikic/php-fuzzer:0.0.11 --no-interaction \
    && ln -s /opt/composer/vendor/bin/php-fuzzer /usr/local/bin/php-fuzzer

COPY docker/fuzzing/php_fuzzer/requirements.txt /tmp/requirements.txt
RUN python3 -m venv /opt/svc \
    && /opt/svc/bin/pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm -f /tmp/requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/fuzzing/php_fuzzer/main.py .

EXPOSE 8153

CMD ["/opt/svc/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8153"]
