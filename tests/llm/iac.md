# Infrastructure and IaC Security Tools Testing

## Test repositories

| Repository URL | Primary Tools | IaC Focus |
|---|---|---|
| [github.com/bridgecrewio/terragoat](https://github.com/bridgecrewio/terragoat) | Checkov, KICS, Terrascan, TFSec | Terraform (HCL) |
| [github.com/bridgecrewio/cfngoat](https://github.com/bridgecrewio/cfngoat) | Checkov, KICS | AWS CloudFormation |
| [github.com/bridgecrewio/kustomizegoat](https://github.com/bridgecrewio/kustomizegoat) | Checkov, KICS, Terrascan | Kubernetes / Kustomize |
| [github.com/madhuakula/kubernetes-goat](https://github.com/madhuakula/kubernetes-goat) | KICS, Checkov, Terrascan, Hadolint | Kubernetes manifests + Dockerfiles |
| [github.com/bridgecrewio/cdkgoat](https://github.com/bridgecrewio/cdkgoat) | Checkov | AWS CDK |

## Suggested workflow

1. Create a workspace for each repo (`create_workspace` with the GitHub URL).
2. Run `iac_list_tools` to confirm the available scanners, then run the primary tools listed per repo with `run_iac_scan`.
3. Cross-reference: a misconfiguration flagged by two or more tools (e.g. a public S3 bucket caught by both Checkov and TFSec) is a high-confidence finding.
4. For any repo containing Dockerfiles, run **Hadolint** - it auto-discovers `Dockerfile*` under the scan path and reports best-practice and security issues. `terragoat` and `kubernetes-goat` both ship Dockerfiles to exercise it.
