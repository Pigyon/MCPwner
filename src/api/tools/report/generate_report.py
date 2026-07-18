"""Render a Markdown assessment report from the findings ledger."""

from api.tools.common import handle_tool_error
from deps import get_report_service


@handle_tool_error
def generate_report(workspace_id: str, fmt: str = "markdown") -> dict:
    """Render an assessment report from the findings ledger.

    Only review-approved (or poc-confirmed) findings appear in the Verified body;
    poc-likely / disputed findings get their own follow-up section, and rejected
    or still-unverified findings go to an audit trail. Each verified/likely finding
    embeds its confirmed PoC script inline (read back from the sandbox artifact).

    A "Tool Coverage" section reports exactly which tools ran (proven by an
    artifact on disk), which were available but never invoked, and which
    categories were absent this run (e.g. IaC not deployed) — a missing tool
    never blocks report generation, it is recorded as "not used".

    Writes report.md under the workspace reports dir and returns its path plus
    coverage summary.

    Args:
        workspace_id: UUID of the workspace.
        fmt: Output format (currently only "markdown").
    """
    return get_report_service().render_report(workspace_id, fmt)
