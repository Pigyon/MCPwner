"""Extract code context tool."""

from deps import get_context_service, get_workspace_service


def extract_code_context(
    workspace_id: str, database_id: str, extract_call_graph_flag: bool = True
) -> dict:
    """
    Extract code context from CodeQL database into SQLite context database.

    Args:
        workspace_id: UUID of the workspace
        database_id: ID of the CodeQL database (format: workspace_id-language)
        extract_call_graph_flag: Whether to extract call graph (default: True)

    Returns:
        Dictionary with extraction results and statistics
    """
    try:
        # Validate workspace
        workspace_service = get_workspace_service()
        workspace = workspace_service.get_workspace(workspace_id)

        # Extract language from database_id (format: workspace_id-language)
        language = database_id.split("-")[-1] if "-" in database_id else None
        if not language:
            return {
                "status": "error",
                "error": "Invalid database_id format. Expected: workspace_id-language",
            }

        # Use context service
        context_service = get_context_service()
        result = context_service.extract_context(
            workspace_id=workspace_id,
            database_id=database_id,
        )

        return result

    except Exception as e:
        return {"status": "error", "error": str(e)}
