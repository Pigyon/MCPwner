FROM python:3.12-slim

COPY docker/utilities/chromium/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# playwright install --with-deps fails on Debian Trixie: it falls back to an Ubuntu
# package list that includes ttf-unifont and ttf-ubuntu-font-family, which don't exist
# here. Install the Chromium runtime deps manually then fetch the browser binary only.
RUN apt-get update && apt-get install -y --no-install-recommends \
    fonts-liberation \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libpango-1.0-0 \
    libx11-6 \
    libxcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*
RUN playwright install chromium

WORKDIR /service

COPY docker/utilities/chromium/main.py .

EXPOSE 8133

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8133"]
