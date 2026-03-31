# Stage 1: Build ffuf
FROM golang:1.21-alpine AS builder

RUN go install github.com/ffuf/ffuf/v2@v2.1.0

# Stage 2: Install Python deps
FROM python:3.11-alpine AS deps

COPY docker/reconnaissance/ffuf/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 3: Lean runtime
FROM alpine:3.19

RUN apk add --no-cache python3 ca-certificates wget

COPY --from=builder /go/bin/ffuf /usr/local/bin/ffuf
COPY --from=deps /install /usr

# Download wordlists (with fallbacks)
RUN mkdir -p /usr/share/wordlists && \
    (wget -q -T 10 http://ffuf.me/wordlist/common.txt -O /usr/share/wordlists/common.txt || \
     printf '%s\n' admin api test login index config backup data files images js css static uploads downloads docs help about contact search profile settings dashboard users accounts services products cart checkout payment orders reports logs status health metrics api/v1 api/v2 admin/login admin/dashboard .git .env .htaccess robots.txt sitemap.xml favicon.ico wp-admin wp-content wp-includes > /usr/share/wordlists/common.txt) && \
    (wget -q -T 10 http://ffuf.me/wordlist/parameters.txt -O /usr/share/wordlists/parameters.txt || \
     printf '%s\n' id user username password email token api_key session page limit offset sort order filter search query type category tag status action callback redirect url path file name value data json xml format method version > /usr/share/wordlists/parameters.txt) && \
    (wget -q -T 10 http://ffuf.me/wordlist/subdomains.txt -O /usr/share/wordlists/subdomains.txt || \
     printf '%s\n' www mail ftp admin api dev test staging prod production blog shop store app mobile static cdn images media assets docs help support portal dashboard status monitor metrics logs > /usr/share/wordlists/subdomains.txt) && \
    chmod 644 /usr/share/wordlists/*.txt

WORKDIR /app

COPY docker/common /app/common
COPY docker/reconnaissance/ffuf/main.py .

EXPOSE 8114

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8114"]
