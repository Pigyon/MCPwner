FROM golang:1.21-alpine AS builder

# Install ffuf
RUN go install github.com/ffuf/ffuf/v2@v2.1.0

FROM alpine:3.19

# Install Python and runtime dependencies
RUN apk add --no-cache python3 py3-pip ca-certificates wget

# Copy ffuf binary from builder
COPY --from=builder /go/bin/ffuf /usr/local/bin/ffuf

# Create wordlists directory and download common wordlists
# If downloads fail, create basic fallback wordlists
RUN mkdir -p /usr/share/wordlists && \
    (wget -q -T 10 http://ffuf.me/wordlist/common.txt -O /usr/share/wordlists/common.txt || \
     echo -e "admin\napi\ntest\nlogin\nindex\nconfig\nbackup\ndata\nfiles\nimages\njs\ncss\nstatic\nuploads\ndownloads\ndocs\nhelp\nabout\ncontact\nsearch\nprofile\nsettings\ndashboard\nusers\naccounts\nservices\nproducts\ncart\ncheckout\npayment\norders\nreports\nlogs\nstatus\nhealth\nmetrics\napi/v1\napi/v2\nadmin/login\nadmin/dashboard\n.git\n.env\n.htaccess\nrobots.txt\nsitemap.xml\nfavicon.ico\nwp-admin\nwp-content\nwp-includes" > /usr/share/wordlists/common.txt) && \
    (wget -q -T 10 http://ffuf.me/wordlist/parameters.txt -O /usr/share/wordlists/parameters.txt || \
     echo -e "id\nuser\nusername\npassword\nemail\ntoken\napi_key\nsession\npage\nlimit\noffset\nsort\norder\nfilter\nsearch\nquery\ntype\ncategory\ntag\nstatus\naction\ncallback\nredirect\nurl\npath\nfile\nname\nvalue\ndata\njson\nxml\nformat\nmethod\nversion" > /usr/share/wordlists/parameters.txt) && \
    (wget -q -T 10 http://ffuf.me/wordlist/subdomains.txt -O /usr/share/wordlists/subdomains.txt || \
     echo -e "www\nmail\nftp\nadmin\napi\ndev\ntest\nstaging\nprod\nproduction\nblog\nshop\nstore\napp\nmobile\nstatic\ncdn\nimages\nmedia\nassets\ndocs\nhelp\nsupport\nportal\ndashboard\nstatus\nmonitor\nmetrics\nlogs" > /usr/share/wordlists/subdomains.txt) && \
    chmod 644 /usr/share/wordlists/*.txt && \
    ls -lh /usr/share/wordlists/ && \
    echo "Wordlist setup complete. File sizes:" && \
    wc -l /usr/share/wordlists/*.txt

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY docker/reconnaissance/ffuf/requirements.txt .
RUN pip install --no-cache-dir --break-system-packages -r requirements.txt

# Copy common modules
COPY docker/common /app/common

# Copy service code
COPY docker/reconnaissance/ffuf/main.py .

# Expose port
EXPOSE 8114

# Run the service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8114"]
