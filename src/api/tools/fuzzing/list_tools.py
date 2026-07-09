"""Source-fuzzing tool discovery MCP tool."""

import logging
from typing import Optional

from api.tools.common import filter_tools_by_language, handle_tool_error
from config.languages import (
    ATHERIS_LANGUAGES,
    JAZZER_LANGUAGES,
    JAZZERJS_LANGUAGES,
    PHP_FUZZER_LANGUAGES,
)

logger = logging.getLogger(__name__)


FUZZING_TOOLS = {
    "atheris": {
        "name": "Atheris",
        "description": (
            "Coverage-guided Python fuzzer (libFuzzer-based). Harness is a Python "
            "script that calls atheris.Setup([...], TestOneInput) and atheris.Fuzz(), "
            "where TestOneInput feeds fuzzer bytes into the suspect function. "
            "Config: harness (required, relative path), max_total_time (s, default 60), "
            "runs, corpus, engine_args."
        ),
        "languages": ATHERIS_LANGUAGES,
    },
    "jazzer": {
        "name": "Jazzer",
        "description": (
            "Coverage-guided JVM fuzzer for Java/Kotlin (libFuzzer-based). The fuzz "
            "target is a compiled class exposing "
            "public static void fuzzerTestOneInput(FuzzedDataProvider data). "
            "Config: target_class (required, fully-qualified), classpath (required, "
            "relative path(s) to compiled classes/jars), max_total_time (s, default 60), "
            "runs, corpus, engine_args. Compile the target into the workspace first."
        ),
        "languages": JAZZER_LANGUAGES,
    },
    "jazzerjs": {
        "name": "Jazzer.js",
        "description": (
            "Coverage-guided JavaScript/Node.js fuzzer (libFuzzer-based). Harness is "
            "a CommonJS module exporting function fuzz(data: Buffer) that drives the "
            "suspect function. Config: harness (required, relative path), "
            "max_total_time (s, default 60), runs, corpus, engine_args. Install the "
            "target project's node_modules in the workspace first."
        ),
        "languages": JAZZERJS_LANGUAGES,
    },
    "php-fuzzer": {
        "name": "PHP-Fuzzer",
        "description": (
            "Coverage-guided PHP fuzzer (nikic/php-fuzzer). Harness is a PHP file "
            "that calls $fuzzer->setTarget(function (string $input) { ... }) to feed "
            "fuzzer bytes into the suspect function. Config: harness (required, "
            "relative path), max_total_time (s, default 60), corpus, engine_args."
        ),
        "languages": PHP_FUZZER_LANGUAGES,
    },
}


@handle_tool_error
def fuzzing_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available source-fuzzing engines with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter engines by detected languages
        show_all: If True, show all engines regardless of workspace languages

    Returns:
        Dictionary with available engines and their metadata
    """
    return filter_tools_by_language("fuzzing", FUZZING_TOOLS, workspace_id, show_all)
