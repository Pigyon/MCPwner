# Adding a new tool

A tool in MCPwner is a small HTTP microservice in its own container. The MCP server discovers it
by probing a health endpoint and, when healthy, exposes it through the category's
`run_<category>_scan` tool. Adding one is five wiring steps - a container, a Compose service, a
registry entry, a config URL, and a discovery-list entry.

This walkthrough uses a hypothetical SAST scanner called `newscanner` on port `12345`.

## 1. Build the tool container

Create `docker/sast/newscanner/` with three files.

**`main.py`** - scanners reuse the shared FastAPI app, which provides `/health`, `/version`,
`/scan`, and report endpoints for free. You only supply how to build the scan command:

```python
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest


def build_newscanner_cmd(request: ScanRequest, output_path: Path):
    scan_path = Path(request.workspace_path) / request.scan_path
    return ["newscanner", "--format", "sarif", "--output", str(output_path), str(scan_path)]


app = create_scanner_app(
    tool_name="newscanner",
    version_cmd=["newscanner", "--version"],
    scan_cmd_builder=build_newscanner_cmd,
    report_format="sarif",   # or "json"
    tool_category="sast",
)
```

**`requirements.txt`** - the Python deps needed to serve the app (at minimum `fastapi` and
`uvicorn`; copy a sibling tool's file).

**`Dockerfile`** - install the tool, copy `docker/common` and your `main.py`, and serve on the
port:

```dockerfile
FROM python:3.11-alpine AS builder
COPY docker/sast/newscanner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-alpine
COPY --from=builder /install /usr/local
# ... install the `newscanner` binary itself here ...
WORKDIR /service
COPY docker/common /service/common
COPY docker/sast/newscanner/main.py .
EXPOSE 12345
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "12345"]
```

The base app exposes `/scan` (POST) and `/health` (GET) - you don't write those.

## 2. Add a Compose service

In `docker-compose.yaml`, add the service. Mirror a sibling in the same category for the security
options, then set the **healthcheck**, **profiles**, and **network**:

```yaml
  newscanner:
    build:
      context: .
      dockerfile: docker/sast/newscanner/Dockerfile
    container_name: newscanner-scanner
    env_file:
      - docker/common/python.env
    read_only: false
    restart: unless-stopped
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    volumes:
      - workspaces:/workspaces
    tmpfs:
      - /tmp:noexec,nosuid,size=1g
    networks:
      - mcpwner-internal        # add mcpwner-recon ONLY if the tool needs internet
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen(\"http://localhost:12345/health\")"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 10s
    profiles:
      - newscanner              # own-name profile
      - sast                    # category profile
```

Then register it as an **optional** dependency of the server so a narrow profile that excludes it
still starts cleanly. In the `mcpwner` service's `depends_on`:

```yaml
      newscanner:
        condition: service_healthy
        required: false
```

> `required: false` is important - without it, the always-on server implicitly enables the tool's
> profile and it starts even for unrelated workflows. Static/dynamic utilities are gated exactly this way.

## 3. Register the tool

Add one `_spec(...)` line to `_SPECS` in `src/config/tools.py`. This single registry is where the
server derives its HTTP client, the category grouping, and the supported-tools list:

```python
_spec("newscanner", _SAST, ("newscanner",), "http://newscanner:12345"),
```

The tuple is the **config path** (where the server reads the tool's `service_url`), and the URL is
`http://<service-name>:<port>`. Add an alias in `TOOL_ALIASES` if users are likely to spell it
differently.

> CodeQL and Linguist are intentionally **not** in this registry - they have bespoke wiring in
> `deps.py`. A normal scanner should always go through `_SPECS`.

## 4. Add the config URL

Add the matching entry to `config/config.yaml.example` (and your local `config.yaml`), under the
category, using the **config-path key** from step 3:

```yaml
# SAST Services
newscanner:
  service_url: "http://newscanner:12345"
```

Remember the naming rule: config keys use underscores where the hostname uses a hyphen.

## 5. Add it to tool discovery

Add an entry to the category's discovery dict - for SAST, `SAST_TOOLS` in
`src/api/tools/sast/list_tools.py`:

```python
"newscanner": {
    "name": "NewScanner",
    "description": "One-line description of what it scans and finds.",
    "languages": NEWSCANNER_LANGUAGES,   # SAST tools filter by detected language
},
```

For SAST, define the language list in `src/config/languages.py` so the tool is only offered for
workspaces where it applies. Non-SAST categories omit `languages`.

## 6. Build, run, verify

```bash
docker compose build newscanner
COMPOSE_PROFILES=sast docker compose up -d
docker compose ps newscanner            # should become healthy
docker compose restart mcpwner          # re-probe so the new tool registers
```

From your client, `run_sast_scan` should now accept `tool="newscanner"`, and the tool should
appear in `sast_list_tools`. If it doesn't register, check the container is healthy and confirm
the `service_url` in `config.yaml` matches the Compose service name and port.

## Choosing a port and network

- Pick an unused port in the category's range (see the port map in
  [configuration.md](configuration.md)).
- Use `mcpwner-internal` only, **unless** the tool must reach the internet (recon/DAST/utilities),
  in which case also attach `mcpwner-recon`. Static analyzers that read cloned source should stay
  internal.
