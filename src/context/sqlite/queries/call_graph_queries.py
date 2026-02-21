"""SQL query builders for call graph operations."""



def build_insert_relationship_query() -> str:
    """Build INSERT query for call relationship."""
    return "INSERT INTO call_graph (caller_id, callee_id, call_site_line) VALUES (?, ?, ?)"


def build_get_callers_query() -> str:
    """Build query to get all callers of an element."""
    return """
        SELECT DISTINCT ce.* FROM code_elements ce
        JOIN call_graph cg ON ce.id = cg.caller_id
        WHERE cg.callee_id = ?
    """


def build_get_callees_query() -> str:
    """Build query to get all callees of an element."""
    return """
        SELECT DISTINCT ce.* FROM code_elements ce
        JOIN call_graph cg ON ce.id = cg.callee_id
        WHERE cg.caller_id = ?
    """


def build_count_relationships_query() -> str:
    """Build query to count total call relationships."""
    return "SELECT COUNT(*) FROM call_graph"
