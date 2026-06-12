"""Generic source-fuzzing report retrieval tool."""

from typing import Any, Dict

from api.tools.common import get_report


def get_fuzzing_report(tool: str, workspace_id: str) -> Dict[str, Any]:
    """
    Get the latest crash report for a source-fuzzing engine.

    Args:
        tool: Name of the fuzzing engine (atheris, jazzer, jazzerjs, php-fuzzer)
        workspace_id: UUID of the workspace

    Returns:
        Report data. ``crash_found`` indicates whether a triggering input was
        discovered; ``results`` lists each crash artifact with its base64-encoded
        input and stack trace, and ``log_tail`` carries the tail of the engine's
        output for triage.
    """
    return get_report("fuzzing", tool, workspace_id)
