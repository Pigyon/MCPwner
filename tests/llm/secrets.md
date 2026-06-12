# Secrets / Credential Scanning Tools Testing

## Test repositories

| Repository URL | Primary Tools |
|---|---|
| [github.com/GitGuardian/sample_secrets](https://github.com/GitGuardian/sample_secrets) | Gitleaks, TruffleHog, detect-secrets |
| [github.com/OWASP/wrongsecrets](https://github.com/OWASP/wrongsecrets) | TruffleHog, Gitleaks, Hawk-Eye |
| [github.com/trufflesecurity/test_keys](https://github.com/trufflesecurity/test_keys) | TruffleHog, Gitleaks, Whispers |
| [github.com/digininja/leakyrepo](https://github.com/digininja/leakyrepo) | detect-secrets, Hawk-Eye, Gitleaks |
| [github.com/Plazmaz/leaky-repo](https://github.com/Plazmaz/leaky-repo) | Whispers, detect-secrets, Gitleaks |
| [github.com/bridgecrewio/terragoat](https://github.com/bridgecrewio/terragoat) | Whispers, detect-secrets, TruffleHog |

## Suggested workflow

1. Create a workspace for each repo.
2. Run all three primary tools listed per repo independently to compare finding overlap and false-positive rates.
3. Cross-reference: a credential flagged by two or more tools is a high-confidence finding.
