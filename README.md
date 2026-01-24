# MCPwner

## What is this?

MCPwner is a swiss knife Model Context Protocol for security researchers consolidating all secrets finding, infrastructure scanning, SAST, DAST, POC, and exploitation in a single place.

## What tools are included?

<div align="center">

### SAST tools

|   <img src="readme/codeql.png" width="100">    |  <img src="readme/psalm.png" width="100">   |    <img src="readme/gosec.png" width="100">    |   <img src="readme/bandit.png" width="100">   |    <img src="readme/semgrep.jpg" width="100">     |        <img src="readme/brakeman.png" width="100">        | <img src="readme/pmd.png" width="100"> |
| :--------------------------------------------: | :-----------------------------------------: | :--------------------------------------------: | :-------------------------------------------: | :-----------------------------------------------: | :-------------------------------------------------------: | :------------------------------------: |
| [**CodeQL**](https://github.com/github/codeql) | [**Psalm**](https://github.com/vimeo/psalm) | [**Gosec**](https://github.com/securego/gosec) | [**Bandit**](https://github.com/PyCQA/bandit) | [**Semgrep**](https://github.com/semgrep/semgrep) | [**Brakeman**](https://github.com/presidentbeef/brakeman) | [**PMD**](https://github.com/pmd/pmd)  |

</div>

## Future tools (to be added soon!):

### DAST, API & RECON

- **OWASP ZAP**: [owasp/zap2docker-stable:latest](https://hub.docker.com/r/owasp/zap2docker-stable)
- **Nikto**: [sullo/nikto:latest](https://hub.docker.com/r/sullo/nikto)
- **SQLmap**: [paoloo/sqlmap:latest](https://hub.docker.com/r/paoloo/sqlmap)
- **Nuclei**: [projectdiscovery/nuclei:latest](https://hub.docker.com/r/projectdiscovery/nuclei)
- **Akto**: [akto/akto-api-security:latest](https://hub.docker.com/r/akto/akto-api-security)
- **Wapiti**: [vasilyev/wapiti:latest](https://hub.docker.com/r/vasilyev/wapiti)
- **Nmap**: [instrumentisto/nmap:latest](https://hub.docker.com/r/instrumentisto/nmap)
- **Amass**: [caffix/amass:latest](https://hub.docker.com/r/caffix/amass)
- **FFUF**: [ffuf/ffuf:latest](https://hub.docker.com/r/ffuf/ffuf)

### SECRETS & SCA

- **Gitleaks**: [zricethezav/gitleaks:latest](https://hub.docker.com/r/zricethezav/gitleaks)
- **TruffleHog**: [trufflesecurity/trufflehog:latest](https://hub.docker.com/r/trufflesecurity/trufflehog)
- **Whispers**: [skyscanner/whispers:latest](https://hub.docker.com/r/skyscanner/whispers)
- **Trivy**: [aquasec/trivy:latest](https://hub.docker.com/r/aquasec/trivy)
- **Grype**: [anchore/grype:latest](https://hub.docker.com/r/anchore/grype)
- **OSV-Scanner**: [ghcr.io/google/osv-scanner:latest](https://github.com/google/osv-scanner)

### INFRASTRUCTURE & IAC

- **Checkov**: [bridgecrew/checkov:latest](https://hub.docker.com/r/bridgecrew/checkov)
- **KICS**: [checkmarx/kics:latest](https://hub.docker.com/r/checkmarx/kics)
- **Terrascan**: [tenable/terrascan:latest](https://hub.docker.com/r/tenable/terrascan)
- **TFSec**: [aquasec/tfsec:latest](https://hub.docker.com/r/aquasec/tfsec)
- **Hadolint**: [hadolint/hadolint:latest](https://hub.docker.com/r/hadolint/hadolint)

### POC & EXPLOITATION

- **Metasploit**: [metasploitframework/metasploit-framework:latest](https://hub.docker.com/r/metasploitframework/metasploit-framework)
- **SearchSploit**: [offensive-security/exploitdb:latest](https://hub.docker.com/r/offensive-security/exploitdb)
- **Interactsh**: [projectdiscovery/interactsh-client:latest](https://hub.docker.com/r/projectdiscovery/interactsh-client)

## How to use it?

1. Setup config:

```bash
cp config/config.yaml.example config/config.yaml
```

2. run:

```bash
sudo docker compose up
```

3. Add `mcp.json` or configure your LLM to communicate with MCPwner or any other set up you use to connect MCP servers to your agent/s.

```json
{
  "mcpServers": {
    "mcpwner": {
      "command": "docker",
      "args": ["exec", "-i", "mcpwner-server", "python", "/app/src/server.py"],
      "env": {
        "MCP_TRANSPORT": "stdio"
      }
    }
  }
}
```

4. profit.

## Contributing

Contributions are welcome!

MCPwner is expected to grow significantly. Therefore, there is a need for more extensive testing infrastructure, e2e and maybe some unit testing for cruicial functions, better error handling, and timeouts. Among many other things to consider.

You can read full contribution guidelines [here](CONTRIBUTING.md).

Will also consider a better management of containers since many of them are needed ad hoc and not to be ran all the time, this might be configured or maybe managed like kubernetes does with KEDA

Also, adding all the tools and testing that them with LLM to verify they work as efficiently and as expected will take some time as well.

If you want to contribute, please submit a single purpose pull request with a manageable number of changes and reasonable lines of code to review.

## Future plans

This project was built with supporting future deployments to remote servers in mind, but for the moment it mainly supports local usage. However, with a few modifications, it could be deployed and used. That's why communication between containers is HTTP and not using the docker-cli.
