import logging
from typing import Optional

from config.languages import (
    ATHERIS_LANGUAGES,
    JAZZER_LANGUAGES,
    JAZZERJS_LANGUAGES,
    PHP_FUZZER_LANGUAGES,
)
from config.tools import tools_for_category
from deps import get_linguist_service

"""Source-fuzzing tool discovery MCP tool."""


logger = logging.getLogger(__name__)


# Tool metadata with language support and config options, mirroring the shape
# returned by sast_list_tools. Source fuzzers are language-specific (one per
# language already covered by SAST), so the list is filtered by detected
# language when a workspace_id is supplied.
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
        "category": "fuzzing",
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
        "category": "fuzzing",
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
        "category": "fuzzing",
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
        "category": "fuzzing",
    },
}


def fuzzing_list_tools(workspace_id: Optional[str] = None, show_all: bool = False) -> dict:
    """
    List available source-fuzzing engines with language compatibility.

    Args:
        workspace_id: Optional workspace ID to filter engines by detected languages
        show_all: If True, show all engines regardless of workspace languages

    Returns:
        Dictionary with available engines and their metadata
    """
    try:
        healthy = set(tools_for_category("fuzzing"))
        available_tools = {k: v for k, v in FUZZING_TOOLS.items() if k in healthy}

        # If show_all or no workspace_id, return all engines
        if show_all or not workspace_id:
            return {"tools": available_tools, "filtered": False}

        # Detect languages in workspace
        try:
            linguist_service = get_linguist_service()
            detected_languages = linguist_service.detect_languages(workspace_id, filter_codeql=False)

            # Filter engines by language compatibility
            compatible_tools = {}
            for tool_id, tool_info in available_tools.items():
                tool_languages = set(tool_info["languages"])
                if tool_languages.intersection(detected_languages):
                    compatible_tools[tool_id] = tool_info

            return {
                "workspace_id": workspace_id,
                "detected_languages": detected_languages,
                "tools": compatible_tools,
                "filtered": True,
            }
        except Exception as e:
            logger.warning(
                f"Linguist language detection failed: {e}. "
                "Gracefully returning all healthy fuzzing tools."
            )
            return {
                "tools": available_tools,
                "filtered": False,
                "note": f"Language detection unavailable: {e}",
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}
