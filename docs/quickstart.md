# Quickstart

MCPwner is two layers: an **MCP server** (`src/`, tool routing) that speaks the Model Context
Protocol, and a fleet of **Docker tool containers** (`docker/`) wrapping security tools - SAST,
SCA, secrets, reconnaissance, DAST, fuzzing, IaC, and runtime utilities. Point any MCP-capable
client at the server and the tools become callable MCP tools. This guide takes you from a clean
checkout to a working fleet wired into your client.

---

## 1. Start the tool fleet (with graceful degradation)

Which containers come online is controlled by `COMPOSE_PROFILES` in `.env`. The MCP server
probes running containers at startup and registers **only the healthy ones**, so a partial
fleet is fully supported - if you only run `sast`, you only get SAST tools, and the rest of the
tool list simply doesn't appear.

```bash
cp .env.example .env                          # then edit COMPOSE_PROFILES
cp config/config.yaml.example config/config.yaml
# .env - pick the categories you actually want:
#   COMPOSE_PROFILES=sast,sca,secrets,dast,fuzzing,poc
docker compose up -d --build
docker compose ps          # confirm health
```

**Profiles:**

| Profile | Brings up | When you need it |
|---|---|---|
| `sast`, `sca`, `secrets` | static analyzers | code audit / white-box |
| `reconnaissance`, `dast` | recon + dynamic web tools | black/grey-box web |
| `fuzzing` | Atheris / Jazzer / Jazzer.js / PHP-Fuzzer | coverage-guided bug hunting |
| `poc` | `poc-sandbox` | run scripted PoCs against a deterministic pass/fail oracle |
| `iac` | Checkov / KICS / Terrascan / tfsec / hadolint | infrastructure-as-code |

Linguist runs **unconditionally** - it is a core cross-tool dependency (language detection and
the code-facts index) and is not listed in `COMPOSE_PROFILES`. The dynamic-testing utilities
(Chromium, WireMock, mitmproxy, aiohttp fuzzer) are **opt-in**: they come up under the `dast`
and `poc` profiles, so a static-only fleet (e.g. `sast`) never starts a browser or DAST
tooling. Enable a profile only when you need it - a narrower fleet is lighter and has a smaller
local attack surface.

---

## 2. Register the MCP server

Add MCPwner to your client's MCP config (the README has one-click install buttons):

```json
{
  "mcpServers": {
    "mcpwner": {
      "command": "docker",
      "args": ["exec", "-i", "mcpwner-server", "python", "src/server.py"],
      "env": {}
    }
  }
}
```

Restart the client. Tools appear namespaced by category (`run_sast_scan`, `run_sca_scan`,
`run_dast_scan`, `run_poc_scan`, `detect_languages`, `index_code_facts`, `diff_discovery`,
`upsert_finding`, …). Only healthy categories register, so the tool list reflects your running
fleet. Any MCP-capable client works (Claude Code, Cursor, Windsurf, and others).

---

## 3. Quick sanity check

From your client, call:

```
health_check                      # server up; which tools are healthy
create_workspace(source_type=..., source=...)
detect_languages(workspace_id)    # requires the linguist container to be healthy
index_code_facts(workspace_id)    # builds the code-facts index used for triage
```

If `index_code_facts` / `query_code_facts` are missing from the tool list, the `linguist`
container isn't healthy - check `docker compose ps` and `docker compose logs linguist`. The
findings-ledger tools (`upsert_finding`, `list_findings`, `get_finding`) and `diff_discovery`
are always registered (local file/git operations, no container gate), so their absence points
to a server-load problem rather than a container.
