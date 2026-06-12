# SAST Tools Testing

## Test repositories

| Repository URL | Primary Tools | Language Focus |
|---|---|---|
| [github.com/WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | CodeQL, Joern, PMD, Opengrep, Semgrep | Java |
| [github.com/juice-shop/juice-shop](https://github.com/juice-shop/juice-shop) | Semgrep, CodeQL | JavaScript / TypeScript |
| [github.com/appsecco/dvna](https://github.com/appsecco/dvna) | CodeQL, NodeJsScan | Node.js |
| [github.com/we45/Vulnerable-Flask-App](https://github.com/we45/Vulnerable-Flask-App) | CodeQL, Bandit, Semgrep | Python |
| [github.com/securego/gosec](https://github.com/securego/gosec) | CodeQL, Gosec | Go |
| [github.com/digininja/DVWA](https://github.com/digininja/DVWA) | Psalm | PHP |
| [github.com/OWASP/railsgoat](https://github.com/OWASP/railsgoat) | Brakeman | Ruby on Rails |

## Suggested workflow

1. Create a workspace for each repo (`create_workspace` with the GitHub URL).
2. Run `detect_languages` to confirm Linguist correctly identifies the primary language before selecting tools.
3. Run the primary tools listed per repo.
4. For Java repos, follow up Semgrep/PMD findings with a targeted CodeQL query (e.g., `java/sql-injection`) on the same database.
