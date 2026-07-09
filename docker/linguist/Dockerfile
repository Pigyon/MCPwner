FROM python:3.12-alpine AS deps

COPY docker/linguist/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /tmp/requirements.txt

FROM crazymax/linguist:9.2.0

USER root

# Alpine sys.path includes /usr site-packages; prefix copy works without venv or --break-system-packages.
RUN apk add --no-cache python3 curl
COPY --from=deps /install /usr

WORKDIR /service

COPY docker/linguist/main.py .
COPY src/utils/git_utils.py .

EXPOSE 8081

ENTRYPOINT []

CMD ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]
