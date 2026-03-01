<div align="center">
  <h1>MCPwner</h1>
  <img src="readme/avatar.png" width="180" alt="MCPwner Badger Avatar"><br>
  <strong>Beware of the Badger</strong><br>
  <em>MCP for autonomous security research workflow</em>
</div>

## What is this?

MCPwner is a Swiss-army knife Model Context Protocol built for security researchers, designed specifically for LLM-driven workflows. It unifies secret discovery, infrastructure scanning, SAST, DAST, poc generation, and exploitation inside a structured machine-readable context layer.

Instead of manually chaining tools and pasting outputs into your LLM, MCPwner standardizes and streams results directly into the model's working context. This allows reasoning, correlation and attack path discovery to happen continuously instead of isolated steps.

MCPwner is built to shine in multi-agent setups where specialized agents collaborate across the security research phases under a shared persistent context.

This project is still work in progress.

## What tools are included?

<div align="center">

## SAST (Static Application Security Testing) Scanning Tools

|   <img src="readme/codeql.png" width="100">    |  <img src="readme/psalm.png" width="100">   |    <img src="readme/gosec.png" width="100">    |   <img src="readme/bandit.png" width="100">   |    <img src="readme/semgrep.jpg" width="100">     |
| :--------------------------------------------: | :-----------------------------------------: | :--------------------------------------------: | :-------------------------------------------: | :-----------------------------------------------: |
| [**CodeQL**](https://github.com/github/codeql) | [**Psalm**](https://github.com/vimeo/psalm) | [**Gosec**](https://github.com/securego/gosec) | [**Bandit**](https://github.com/PyCQA/bandit) | [**Semgrep**](https://github.com/semgrep/semgrep) |

<br>

|        <img src="readme/brakeman.png" width="100">        | <img src="readme/pmd.png" width="100"> |
| :-------------------------------------------------------: | :------------------------------------: |
| [**Brakeman**](https://github.com/presidentbeef/brakeman) | [**PMD**](https://github.com/pmd/pmd)  |

</div>

<div align="center">

## Secrets Scanning Tools

|   <img src="readme/gitleaks.png" width="100">    |  <img src="readme/trufflehog.png" width="100">   | <img src="readme/detect-secrets.png" width="100"> | <img src="readme/whispers.png" width="100"> | <img src="readme/hawk-eye.jpeg" width="100"> |
| :----------------------------------------------: | :----------------------------------------------: | :----------------------------------------------: | :------------------------------------------: | :------------------------------------------: |
| [**Gitleaks**](https://github.com/zricethezav/gitleaks) | [**TruffleHog**](https://github.com/trufflesecurity/trufflehog) | [**detect-secrets**](https://github.com/Yelp/detect-secrets) | [**Whispers**](https://github.com/Skyscanner/whispers) | [**Hawk-Eye**](https://github.com/rohitcoder/hawk-eye) |

</div>

## Future Tools (Planned)

### DAST, API & Recon

- **OWASP ZAP**
- **Nikto**
- **SQLmap**
- **Nuclei**
- **Akto**
- **Wapiti**
- **Nmap**
- **Amass**
- **FFUF**

### SCA

- **Trivy**
- **Grype**
- **OSV-Scanner**

### Infrastructure & IaC

- **Prowler**
- **Checkov**
- **KICS**
- **Terrascan**
- **TFSec**
- **Hadolint**

### PoC & Exploitation

- **Metasploit**
- **SearchSploit**
- **Interactsh**


## How to use it?

1. **Setup config**:
   ```bash
   cp config/config.yaml.example config/config.yaml
   ```

2. **Run Services**:
   ```bash
   docker-compose up -d --build
   ```

3. **Configure your IDE/LLM**:
   Add the following to your MCP configuration file (e.g., `mcp.json` for Cursor/Kiro/Claude Desktop or similar settings for other IDEs). This connects directly to the running Docker container.

   ```json
   {
     "mcpServers": {
       "mcpwner": {
         "command": "docker",
         "args": [
           "exec",
           "-i",
           "mcpwner-server",
           "python",
           "src/server.py"
         ],
         "env": {}
       }
     }
   }
   ```

4. **Scanning Local Projects**:
   To scan projects on your host machine, mount them into the container via `docker-compose.yaml`:
   ```yaml
   services:
     mcpwner:
       volumes:
         - /path/to/your/projects:/mnt/projects:ro
   ```
   Then use the `create_workspace` tool with `source_type="local"` and `source="/mnt/projects/my-project"`.

## Contributing

Contributions are welcome!

MCPwner is expected to grow significantly. Therefore, there is a need for more extensive testing infrastructure, e2e and maybe some unit testing for cruicial functions, better error handling, and timeouts. Among many other things to consider.

You can read full contribution guidelines [here](CONTRIBUTING.md).

Will also consider a better management of containers since many of them are needed ad hoc and not to be ran all the time, this might be configured or maybe managed like kubernetes does with KEDA

Also, adding all the tools and testing that them with LLM to verify they work as efficiently and as expected will take some time as well.

If you want to contribute, please submit a single purpose pull request with a manageable number of changes and reasonable lines of code to review.

## Future plans

This project was built with supporting future deployments to remote servers in mind, but for the moment it mainly supports local usage. However, with a few modifications, it could be deployed and used. That's why communication between containers is HTTP and not using the docker-cli.
