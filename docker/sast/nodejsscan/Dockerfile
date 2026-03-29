FROM opensecurity/nodejsscan:v4.8

USER root

# Install Python deps for FastAPI wrapper
COPY docker/sast/nodejsscan/requirements.txt .
RUN pip install --break-system-packages --no-cache-dir -r requirements.txt

WORKDIR /service

COPY docker/common /service/common
COPY docker/sast/nodejsscan/main.py .

EXPOSE 8088

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8088"]
