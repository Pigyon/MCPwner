from clients.base import BaseScanClient


class BaseSecretsClient(BaseScanClient):
    """Base HTTP client for Secrets services."""

    report_tool = "get_secrets_report"
