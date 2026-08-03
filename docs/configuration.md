# Configuration

MCPwner has two configuration surfaces:

- **`.env`** - which tool containers start (`COMPOSE_PROFILES`), read by Docker Compose.
- **`config/config.yaml`** - where the MCP server finds each tool and how it logs.

Both have tracked `.example` files. Copy them before first run:

```bash
cp .env.example .env
cp config/config.yaml.example config/config.yaml
```

---

## `.env` - which containers start

The only variable you normally set is `COMPOSE_PROFILES`, a comma-separated list. You can enable
whole **categories** or **individual tools**:

```bash
# whole categories
COMPOSE_PROFILES=sast,fuzzing,dast,sca,secrets,reconnaissance,iac,poc

# or specific tools
COMPOSE_PROFILES=semgrep,bandit,codeql
```

**Categories:** `sast`, `sca`, `secrets`, `reconnaissance`, `dast`, `iac`, `fuzzing`, `poc`.

**Always on (no profile needed):** `mcpwner` (the server), `volume-init` (one-shot volume
ownership), and `linguist` (language detection + the code-facts index).

**Opt-in utilities:** Chromium, WireMock, mitmproxy, and the aiohttp fuzzer come up **only** under
the `dast` and `poc` profiles - a static-only fleet never starts a browser or DAST tooling. See
[quickstart.md](quickstart.md) for the profile table.

> The `poc` profile brings up `poc-sandbox`, the sandbox that runs scripted PoCs against a
> deterministic pass/fail oracle. Enable it when you intend to prove a bug with an exploit script.

---

## `config/config.yaml` - server-side wiring

The server reads one `service_url` per tool (the tool's address on the internal Docker network)
plus a logging block:

```yaml
codeql:
  service_url: "http://codeql:8080"
linguist:
  service_url: "http://linguist:8081"
semgrep:
  service_url: "http://semgrep:8082"
# ... scanners grouped by category (reconnaissance:, iac:, fuzzing:, dast:, poc:)

logging:
  level: "INFO"          # DEBUG | INFO | WARNING | ERROR | CRITICAL
  file: "/var/log/mcpwner/server.log"
```

You rarely need to edit these - the defaults match the service names and ports in
`docker-compose.yaml`. Change a `service_url` only if you relocate a tool or run it outside the
default network.

**Naming gotcha:** config keys use **underscores** where the Docker service/hostname uses a
**hyphen**. For example the service `detect-secrets` is configured under `detect_secrets:`, and
`hawk-scanner` under `hawk_scanner:`. The canonical mapping lives in `src/config/tools.py`.

---

## Port map

Each tool listens on a fixed port on the internal network. Ports are allocated by category:

| Category | Port range | Examples |
|---|---|---|
| Core | 8080-8082 | codeql `8080`, linguist `8081`, semgrep `8082` |
| SAST | 8083-8096 | bandit `8083`, gosec `8084`, joern `8089`, opengrep `8096` |
| Secrets | 8090-8094 | gitleaks `8090`, trufflehog `8091`, detect-secrets `8093` |
| SCA | 8100-8104 | osv-scanner `8100`, grype `8101`, syft `8102` |
| Reconnaissance | 8110-8121 | httpx `8112`, katana `8113`, ffuf `8114` |
| Utilities | 8130-8134 | wiremock `8130`, mitmproxy `8131`, fuzzer `8132`, chromium `8133`, poc-sandbox `8134` |
| IaC | 8140-8144 | checkov `8140`, tfsec `8143`, hadolint `8144` |
| Fuzzing | 8150-8153 | atheris `8150`, jazzer `8151`, php-fuzzer `8153` |
| DAST | 8160-8167 | sqlmap `8160`, dalfox `8163`, interactsh-client `8167` |

These ports are internal to the Docker network; the server reaches them by service name, so you
don't publish them on the host. Full authoritative list: the `_SPECS` table in
`src/config/tools.py`.

---

## Local source instead of a Git clone

To scan a checkout on your host, mount it read-only into the server and use a local workspace
(see the README's Installation section):

```yaml
services:
  mcpwner:
    volumes:
      - /path/to/your/projects:/mnt/projects:ro
```

Then `create_workspace(source_type="local", source="/mnt/projects/my-project")`.
