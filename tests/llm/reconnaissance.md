# Reconnaissance Tools Testing

## Test targets

| Target | Primary Tools |
|---|---|
| `inlanefreight.com` | Subfinder, Amass, BBOT, httpx, ffuf, Wafw00f |
| `scanme.nmap.org` | Nmap, Masscan, Katana, GAU, Arjun |
| `example.com` | Subfinder, Amass, BBOT, Kiterunner |

> All three domains are explicitly authorized for security testing.

## Chaining workflows

### Chain 1: Subdomain architecture to web mapping

1. **Subfinder / Amass / BBOT** (`preset: subdomain-enum`) - dump the initial subdomain list.
2. Pipe findings into **httpx** (`source_tool: subfinder`) - filter dead hosts, capture titles and tech stacks.
3. Pass live web targets into **Wafw00f** (`source_tool: httpx`) - identify which targets have WAFs before starting aggressive scans.

### Chain 2: Active infrastructure to port discovery

1. **Masscan** on a wide port range (e.g., `ports: 1-10000, rate: 500`) - rapidly locate open ports.
2. Feed Masscan results into **Nmap** (`source_tool: masscan`) - precise service fingerprinting and vulnerability scripting on confirmed open ports only.

### Chain 3: Web content and attack surface expansion

1. Take live web apps (from **httpx**) and run **Katana** (`source_tool: httpx`) and **GAU** (`source_tool: httpx`) simultaneously to extract crawled URLs, JS files, and historical paths.
2. Feed discovered URLs into **Arjun** (`source_tool: katana`) to look for hidden query parameters (`?debug=true`, `?admin=1`).
3. For endpoints that look like modern APIs, run **Kiterunner** (`source_tool: httpx`) with API-aware wordlists, or **ffuf** (`source_tool: katana`) for traditional directory brute-forcing.
