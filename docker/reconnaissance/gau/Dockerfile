FROM golang:1.21-alpine AS builder

RUN go install github.com/lc/gau/v2/cmd/gau@v2.2.4

FROM alpine:3.19

# Install Python and runtime dependencies
RUN apk add --no-cache python3 py3-pip curl

# Copy gau binary from builder
COPY --from=builder /go/bin/gau /usr/local/bin/gau

WORKDIR /app

# Copy requirements and install dependencies
COPY docker/reconnaissance/gau/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/gau/main.py .

EXPOSE 8115

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8115"]
