# Security Considerations

> **Note:** This project is under construction and in beta.

MCPwner executes security tools that perform intrusive operations. Only use on systems you own or have explicit permission to test. The PoC sandbox runs arbitrary agent-authored code inside a resource-capped, unprivileged container - but it is connected to the target network by design.

Restrict MCP server access to authorized users. Review tool configurations before running scans. Follow responsible disclosure practices. Never commit credentials to configuration files - use environment variables.

## Reporting Vulnerabilities

Currently, security vulnerabilities should be reported as an issue or a pull request in this repository. The project is stil in Beta development.

<div align="center">
  <img src="https://private-user-images.githubusercontent.com/66902031/626540097-4cec23dd-259b-4173-8d80-1c399aa87b28.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3ODQ5MjkyMTksIm5iZiI6MTc4NDkyODkxOSwicGF0aCI6Ii82NjkwMjAzMS82MjY1NDAwOTctNGNlYzIzZGQtMjU5Yi00MTczLThkODAtMWMzOTlhYTg3YjI4LnBuZz9YLUFtei1BbGdvcml0aG09QVdTNC1ITUFDLVNIQTI1NiZYLUFtei1DcmVkZW50aWFsPUFLSUFWQ09EWUxTQTUzUFFLNFpBJTJGMjAyNjA3MjQlMkZ1cy1lYXN0LTElMkZzMyUyRmF3czRfcmVxdWVzdCZYLUFtei1EYXRlPTIwMjYwNzI0VDIxMzUxOVomWC1BbXotRXhwaXJlcz0zMDAmWC1BbXotU2lnbmF0dXJlPTEzMmMyOTc1NjI3NzMyNTRiMDU4ODA2OTU1ZDIwMTVjOGQ3MGY5ZGVjZTVkODRkYzljMmU1MWQ1ZmEwN2ZmNjAmWC1BbXotU2lnbmVkSGVhZGVycz1ob3N0JnJlc3BvbnNlLWNvbnRlbnQtdHlwZT1pbWFnZSUyRnBuZyJ9.qL2hJVlO14yQKX825H3n5EDBiz428pzfrfnEDqCGPk8" alt="nothing to see here">
</div>
