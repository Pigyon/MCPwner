from clients.base import BaseSASTClient


class BaseSecretsClient(BaseSASTClient):
    """Base HTTP client for Secrets services."""

    report_tool = "get_secrets_report"
