# Troubleshooting

Most problems fall into three buckets: the Docker fleet, tool registration in your MCP client,
and image builds. Work top-down - `docker compose ps` first, then logs for the offending
service.

---

## A tool is missing from my client's tool list

The MCP server registers **only tools whose container is healthy at server startup**. If a tool
is missing:

1. **Is its container running?** `docker compose ps` - look for the service and a `healthy`
   status.
2. **Is its profile enabled?** Tools are grouped into `COMPOSE_PROFILES` categories. A tool in a
   profile you didn't enable never starts. See [configuration.md](configuration.md).
3. **Did you start it after the server?** The server probes health **once at startup**. If you
   bring a container up later, restart the server so it re-probes:
   ```bash
   docker compose restart mcpwner
   ```
   Then reconnect the client (or restart it) to pick up the new tool list.
4. **Is the container unhealthy?** Check its logs:
   ```bash
   docker compose logs --tail=50 <service>
   ```

`upsert_finding`, `list_findings`, `get_finding`, and `diff_discovery` are **always** registered
(local file/git operations, no container gate). If *those* are missing, the server itself failed
to load - check `docker compose logs mcpwner`.

---

## `detect_languages` / `index_code_facts` / `query_code_facts` are missing

These three depend on the **linguist** container. Linguist runs unconditionally (no profile), so
if they're absent the container is unhealthy:

```bash
docker compose ps linguist
docker compose logs --tail=50 linguist
```

Linguist runs as UID 1000 to match cloned-workspace ownership; a permissions error here usually
means the `workspaces` volume ownership is off - re-run `volume-init` with
`docker compose up -d volume-init`.

---

## The server starts but a DAST/browser tool is unavailable

Chromium, WireMock, mitmproxy, and the aiohttp fuzzer are **opt-in** utilities. They only start
under the `dast` or `poc` profiles. If `run_dast_scan` or `run_utilities_scan` reports the tool
as unavailable, add the profile and restart:

```bash
# .env
COMPOSE_PROFILES=sast,dast,poc
docker compose up -d
docker compose restart mcpwner
```

---

## Image build failures

### `ImportError: cannot import name 'McpError' from 'mcp.shared.exceptions'`

The `mcp` SDK published a 2.x release that FastMCP 2.14.0 is not compatible with. `requirements.txt`
pins a FastMCP version that constrains `mcp<2.0`; if you changed that pin, restore a FastMCP
release that carries the upper bound (2.14.7+) and rebuild:

```bash
docker compose build mcpwner
```

### `ERROR: unable to select packages: universal-ctags (no such package)`

The Linguist image is based on Alpine, which packages Universal Ctags as **`ctags`**, not
`universal-ctags`. `docker/linguist/Dockerfile` installs `ctags`; if you edited it, use that name.

### Registry timeouts (`context deadline exceeded`) during build

Usually a cold Docker daemon or flaky network pulling base images. Pre-pull and retry:

```bash
docker pull python:3.12-alpine
docker compose build
```

---

## The whole fleet is heavy / slow to start

You almost certainly don't need every category. Narrow `COMPOSE_PROFILES` to what the engagement
needs - a static-only audit is just `sast` (plus the always-on `linguist`, `mcpwner`, and
`volume-init`). Fewer containers means less memory, less disk, and a smaller local attack surface.

---

## `docker compose` can't connect to the daemon

`Cannot connect to the Docker daemon` / `dockerDesktopLinuxEngine ... system cannot find the
file` means the Docker engine isn't running. Start Docker Desktop (or `dockerd`) and wait for it
to report ready before `docker compose up`.

---

## `config.yaml` not found

Copy the example before first run:

```bash
cp config/config.yaml.example config/config.yaml
```

`config.yaml` is git-ignored so your local service URLs and log settings stay out of version
control.
