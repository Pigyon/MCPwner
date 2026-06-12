# Utilities Tools Testing

## Linguist: Language Detection

**Goal:** Validate that `detect_languages` accurately identifies primary languages across diverse codebases and that the output would correctly drive SAST tool suggestions.

| Repository URL | Expected Primary Languages | SAST tools that should appear |
|---|---|---|
| [github.com/WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java, JavaScript, XML | Joern, PMD, Semgrep (Bandit should NOT appear) |
| [github.com/juice-shop/juice-shop](https://github.com/juice-shop/juice-shop) | TypeScript, JavaScript, HTML | NodeJsScan, Semgrep |
| [github.com/we45/Vulnerable-Flask-App](https://github.com/we45/Vulnerable-Flask-App) | Python | Bandit, Semgrep (Gosec should NOT appear) |
| [github.com/securego/gosec](https://github.com/securego/gosec) | Go | Gosec, Semgrep only |
| [github.com/OWASP/railsgoat](https://github.com/OWASP/railsgoat) | Ruby, JavaScript, CSS | Brakeman, Semgrep only |
| [github.com/bridgecrewio/terragoat](https://github.com/bridgecrewio/terragoat) | HCL, Python, Go | Semgrep (Terraform rules), Bandit, Gosec |

Run `detect_languages` on each workspace, then immediately run `sast_list_tools` with the same `workspace_id` and confirm the filtered tool list matches the expected column above.

---

## aiohttp Fuzzer: Async HTTP Fuzzing

> All targets below are intentionally vulnerable, publicly authorized test applications.

| Target URL | `param` | `method` | `concurrency` | Focus |
|---|---|---|---|---|
| `http://testphp.vulnweb.com/search.php` | `searchFor` | GET | 50 | SQLi and reflected XSS payloads |
| `http://testphp.vulnweb.com/userinfo.php` | `profileID` | GET | 50 | IDOR: numeric ID enumeration |
| `https://demo.testfire.net/search.aspx` | `txtSearch` | GET | 30 | XSS in .NET search field |
| `https://demo.testfire.net/bank/login.aspx` | `uid` | POST | 20 | Auth bypass, response-time anomaly on valid usernames |
| `http://webscantest.com/crosstraining/aboutyou.php` | `fn` | GET | 30 | Path traversal and LFI probes |
| `http://testphp.vulnweb.com/hpp/` | `pp` | GET | 50 | HTTP Parameter Pollution |

**Race condition test:** Set `concurrency: 100` against `https://demo.testfire.net/bank/transfer.aspx` to probe for TOCTOU in balance updates. Look for two simultaneous 200 responses that each report the full transfer succeeding.

**Anomaly baseline:** Run once with the default `payloads` list and note the baseline status code distribution. Any response with a different status code or content-length deviation greater than 30% of the median is a candidate for further investigation.

---

## Mitmproxy: Traffic Interception

> All targets are authorized test applications.

| Target URL | Interception Goal | `modify_request` headers |
|---|---|---|
| `http://testphp.vulnweb.com/listproducts.php?cat=1` | Capture SQL parameter in transit, observe raw response | `{"X-Forwarded-For": "127.0.0.1"}` |
| `https://demo.testfire.net/bank/login.aspx` | Observe session token issuance in Set-Cookie headers | `{"X-Original-URL": "/admin"}` |
| `http://testphp.vulnweb.com/AJAX/infoartist.php` | Capture raw AJAX JSON response structure for use in subsequent fuzzing | `{"Accept": "application/json"}` |
| `http://webscantest.com` | Baseline traffic map, observe only, no modification | _(none)_ |
| `http://testphp.vulnweb.com/hpp/?pp=12` | Intercept HPP request, note how server handles duplicate params | `{"X-HTTP-Method-Override": "DELETE"}` |

**Custom script test:** Supply an inline `script` that rewrites every captured `GET` request's method to `POST` (`flow.request.method = "POST"`), then confirm whether the server's response changes. A different response indicates the server uses the HTTP verb for access control.

**Multi-target test:** Pass three parameterized URLs in `extra_targets` from the same host to capture all three flows in a single mitmdump session and compare their request structures in one report.

---

## WireMock: API Response Mocking

WireMock tests require a **live running target application** that calls API endpoints. Clone the repo, start the app locally, and point `target` at `http://localhost:<port>`.

| Local App | Endpoint to Stub | Malicious Response Goal |
|---|---|---|
| Juice Shop (`localhost:3000`) | `GET /rest/products/search?q=*` | Return 10,000 products with `<script>alert(1)</script>` in `name` - probe for stored XSS via API trust |
| Juice Shop (`localhost:3000`) | `POST /api/BasketItems` | Return `{"price": -999, "quantity": 1}` - test whether the checkout flow accepts negative prices from the API |
| Juice Shop (`localhost:3000`) | `POST /rest/user/login` | Return `{"authentication": {"token": "admin-token"}}` for any credentials - test whether the frontend trusts the API response without server-side verification |
| WebGoat (`localhost:8080`) | `POST /WebGoat/login` | Return `{"success": true}` unconditionally - test whether the app re-validates login server-side |
| DVWA (`localhost:80`) | `POST /recaptcha/api/siteverify` | Return `{"success": true}` - bypass CAPTCHA by mocking the Google reCAPTCHA endpoint |
| Any app with a payment flow | `POST /payment/charge` | Return `{"charged": true, "amount": 0.00, "status": "paid"}` - test whether the app trusts the payment gateway response or verifies the amount independently |

**Stub template** for `config.stubs`:

```json
[
  {
    "request": { "method": "ANY", "urlPattern": "/api/.*" },
    "response": {
      "status": 200,
      "jsonBody": { "error": null, "data": "<img src=x onerror=alert(1)>" },
      "headers": { "Content-Type": "application/json" }
    }
  },
  {
    "request": { "method": "POST", "url": "/payment/charge" },
    "response": {
      "status": 200,
      "body": "{\"charged\": true, \"amount\": 0.00}",
      "headers": { "Content-Type": "application/json" },
      "fixedDelayMilliseconds": 5000
    }
  }
]
```

Use `config.test_requests` to list the paths the target app will call after stubs are registered. Inspect the report's `request_journal` to confirm each stub was actually triggered - an unstubbed endpoint means the test did not reach that code path.

---

## Headless Chromium: Client-Side Analysis

| Target URL | `check_xss` | `screenshot` | `wait_for` | Focus |
|---|---|---|---|---|
| `https://juice-shop.herokuapp.com` | `true` | `true` | `networkidle` | React SPA DOM rendering, JS errors, XSS probe in `/#/search?q=` |
| `http://testphp.vulnweb.com/artists.php?artist=1` | `true` | `false` | `domcontentloaded` | Reflected XSS in `artist` URL parameter |
| `https://xss-game.appspot.com/level1/frame` | `true` | `true` | `domcontentloaded` | Known DOM XSS - validates that `window.__xss` probe fires correctly (use as canary) |
| `http://testphp.vulnweb.com` | `false` | `true` | `networkidle` | Full-site screenshot + enumerate all JS errors on the landing page |
| `https://demo.testfire.net` | `false` | `false` | `networkidle` | Network request capture - map what API endpoints the SPA calls on initial load |
| `https://ginandjuice.shop` | `true` | `true` | `networkidle` | PortSwigger intentionally vulnerable shop: DOM XSS, open redirects, client-side logic flaws |

**Canary validation:** `xss-game.appspot.com/level1` is a known-vulnerable target. If `check_xss: true` does **not** return at least one `triggered: true` in `xss_findings`, the probe injection logic has a bug and must be fixed before trusting Chromium results on other targets.

**JS error baseline:** Run Chromium on `https://demo.testfire.net` with no XSS checking. A healthy modern app should return 0 uncaught JS exceptions in `js_errors`. Any exceptions indicate poor error handling and are worth manual investigation.

---

## Chaining Workflows

### Chain 1: Code Analysis to API Attack Surface

1. **Linguist** - `detect_languages` on a cloned target repo.
2. **SAST tool** (Semgrep or CodeQL) - scan for hardcoded third-party API base URLs or SDK import statements (`import stripe`, `from twilio.rest`, `axios.create({baseURL:`).
3. **WireMock** - register stubs at those discovered API endpoints and supply malicious responses. Replay the user flow that calls those APIs and observe whether the app blindly trusts the mocked response.

*Replicates: find that an app calls `api.stripe.com/v1/charges`, mock it, return `{"status": "succeeded"}` for a zero-amount charge, confirm whether the app releases the order.*

### Chain 2: Endpoint Discovery to Async Fuzzing to DOM Verification

1. **Katana** or **GAU** (Reconnaissance) - extract all parameterized URLs from the target.
2. **Fuzzer** - for each parameterized URL, fuzz the parameter with XSS and SQLi probes at `concurrency: 50`. Record all URLs where the response body or status deviates from the baseline.
3. **Chromium** with `check_xss: true` - for each anomalous URL from step 2, navigate headlessly and confirm whether the payload is reflected and executes as JavaScript in the rendered DOM.

*Converts a raw URL list into confirmed client-side vulnerabilities without any manual browser work.*

### Chain 3: Baseline Capture to Targeted Replay

1. **Mitmproxy** (no `modify_request`) - intercept a clean browse through the target app, capture the full request structure (parameter names, headers, cookie keys) into the report.
2. **Fuzzer** - using the exact parameter names from the mitmproxy report, fuzz those parameters at high concurrency (`concurrency: 100`).
3. **Mitmproxy** again with an inline `script` that replaces the session cookie with an invalid value on every intercepted request - re-run the same fuzz targets to isolate which endpoints fail open under unauthenticated load.

### Chain 4: SPA Fingerprint to Chromium Crawl to API Fuzzing

1. **httpx** (Reconnaissance) on a list of live subdomains - filter those returning large JS bundles (`Content-Type: text/html` with a JavaScript-heavy response). These are SPA candidates.
2. **Chromium** on each SPA URL (`screenshot: true`, `wait_for: networkidle`) - capture the full `network_requests` list from the page load. This reveals hidden internal API endpoints and CDN-hosted JS files invisible to static crawlers.
3. **Fuzzer** - target each API endpoint discovered in the Chromium network request log with `method: POST` and a payload list of auth bypass, mass assignment, and type confusion probes.
