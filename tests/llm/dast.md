# DAST Tools Testing

DAST tools scan **live running applications**, so tests run against intentionally
vulnerable Docker containers on the local network. Start the target containers
before running any DAST scans.

## Test targets

Start these vulnerable applications locally:

```bash
# DVWA — SQL injection, command injection, XSS, SSTI, file inclusion
docker run -d --name dvwa -p 8880:80 vulnerables/web-dvwa

# Juice Shop — XSS, SQLi, JWT flaws, SSRF, NoSQL injection
docker run -d --name juiceshop -p 3000:3000 bkimminich/juice-shop

# WebGoat — SQL injection, JWT, XXE, SSRF
docker run -d --name webgoat -p 8081:8080 webgoat/webgoat
```

| Local Target | Primary Tools |
|---|---|
| `http://host.docker.internal:8880/vulnerabilities/sqli/?id=1&Submit=Submit` | sqlmap, dalfox |
| `http://host.docker.internal:8880/vulnerabilities/exec/` | commix |
| `http://host.docker.internal:3000/rest/products/search?q=test` | nosqlmap, dalfox |
| `http://host.docker.internal:3000` | sstimap, ssrfmap |
| `http://host.docker.internal:8081/WebGoat` | sqlmap, jwt_tool |

> **Note:** DAST containers are on the `mcpwner-recon` network, so use
> `host.docker.internal` (Docker Desktop) or the host's Docker bridge IP
> (Linux) to reach targets running on the host.

## Suggested workflows

### SQL injection

1. Start DVWA: `docker run -d --name dvwa -p 8880:80 vulnerables/web-dvwa`
2. Login to DVWA (admin/password), set Security Level to Low.
3. Run sqlmap:
   ```
   run_dast_scan(
     tool="sqlmap",
     target="http://host.docker.internal:8880/vulnerabilities/sqli/?id=1&Submit=Submit",
     config={"cookie": "PHPSESSID=<session>; security=low"}
   )
   ```
4. `get_dast_report(tool="sqlmap", workspace_id="<id>")`

### XSS probing

1. Run **dalfox** against a reflected parameter:
   ```
   run_dast_scan(
     tool="dalfox",
     target="http://host.docker.internal:8880/vulnerabilities/xss_r/?name=test",
     config={"cookie": "PHPSESSID=<session>; security=low"}
   )
   ```
2. Dalfox emits native JSON findings.

### Command injection

1. Run **commix** against DVWA command injection page:
   ```
   run_dast_scan(
     tool="commix",
     target="http://host.docker.internal:8880/vulnerabilities/exec/",
     config={"data": "ip=127.0.0.1&Submit=Submit", "cookie": "PHPSESSID=<session>; security=low"}
   )
   ```

### NoSQL injection

1. Run **nosqlmap** against Juice Shop search:
   ```
   run_dast_scan(
     tool="nosqlmap",
     target="http://host.docker.internal:3000/rest/products/search?q=test"
   )
   ```

### SSTI

1. Run **sstimap** against any user-input endpoint:
   ```
   run_dast_scan(
     tool="sstimap",
     target="http://host.docker.internal:8880/vulnerabilities/xss_r/?name={{7*7}}"
   )
   ```

### JWT testing

1. Obtain a JWT token from Juice Shop or WebGoat login.
2. Run **jwt_tool** with the token:
   ```
   run_dast_scan(
     tool="jwt_tool",
     target="http://host.docker.internal:3000/rest/user/whoami",
     config={"token": "<JWT>"}
   )
   ```

### Blind OOB confirmation

1. Start **interactsh-client** to obtain an OOB domain:
   ```
   run_dast_scan(tool="interactsh-client")
   ```
2. Inject the returned `domain` into SSRF, blind SQLi, or XXE payloads
   against the local targets.
3. Re-run **interactsh-client** in the same workspace to collect interactions
   received since the last scan.

### SSRF

1. Capture a raw HTTP request from mitmproxy or browser devtools.
2. Run **ssrfmap** with the raw request:
   ```
   run_dast_scan(
     tool="ssrfmap",
     target="http://host.docker.internal:3000/profile/image/url",
     config={"raw_request": "<raw HTTP request>", "param": "imageUrl", "module": "readfiles"}
   )
   ```

## Chaining from reconnaissance

1. Run **httpx** or **katana** to discover live URLs on the local targets.
2. Pass discovered URLs into **dalfox**, **sqlmap**, **commix**, or **sstimap**.
3. For SSRF testing, capture a raw HTTP request and pass it to **ssrfmap**
   via `config.raw_request`.

## Expected MCP tools

- `dast_list_tools`
- `run_dast_scan`
- `get_dast_report`
