# Use the official optimized Psalm image
FROM ghcr.io/danog/psalm:6.9.1

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extension installer to easily install zip extension
ADD https://github.com/mlocati/docker-php-extension-installer/releases/latest/download/install-php-extensions /usr/local/bin/
RUN chmod +x /usr/local/bin/install-php-extensions && \
    install-php-extensions zip

# Install Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy requirements and install Python packages
COPY docker/sast/psalm/requirements.txt .
RUN python3 -m pip install --break-system-packages --no-cache-dir -r requirements.txt

# Ensure psalm is in PATH
ENV PATH="/composer/vendor/bin:${PATH}"

WORKDIR /service

# Copy service files
COPY docker/common /service/common
COPY docker/sast/psalm/main.py .
COPY docker/sast/psalm/psalm.xml /service/psalm.xml

# Expose service port
EXPOSE 8087

# Run the FastAPI service with uvicorn
ENTRYPOINT ["/usr/bin/python3"]
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8087"]
