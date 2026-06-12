"""Shared FastAPI factory for source-fuzzing engine containers.

Every fuzzing engine (Atheris, Jazzer, Jazzer.js, PHP-Fuzzer) exposes the same
HTTP surface as the static scanners — ``/scan``, ``/health``, ``/version``,
``/reports`` — so it reuses :func:`common.base_service.create_scanner_app`
unchanged. The only difference is the scan command: instead of invoking the tool
directly (which would leave no machine-readable report), it invokes the shared
:mod:`common.fuzz_harness` runner, which drives the engine, collects crash
artifacts, and writes a JSON report to the factory's output path.

Each engine's ``main.py`` is therefore a one-liner: call :func:`create_fuzzer_app`
with the engine id and a version command.
"""

import json
from pathlib import Path
from typing import List

from common.base_service import create_scanner_app
from common.models import ScanRequest

# Absolute path to the runner inside the image (docker/common is copied here).
_RUNNER = "/service/common/fuzz_harness.py"


def create_fuzzer_app(tool_name: str, engine: str, version_cmd: List[str]):
    """Create a FastAPI app for a source-fuzzing engine.

    Args:
        tool_name: Registry/report name of the engine (e.g. ``"atheris"``).
        engine: Engine id understood by ``fuzz_harness`` (atheris, jazzer,
            jazzerjs, php-fuzzer).
        version_cmd: Command used by ``/version`` to report the engine version.
    """

    def build_cmd(request: ScanRequest, output_path: Path) -> List[str]:
        config = request.config or {}

        # Validate required config up-front so the factory returns a clean 400
        # instead of letting the engine fail cryptically.
        if engine == "jazzer":
            if not config.get("target_class"):
                raise ValueError("config.target_class is required for jazzer")
            if not config.get("classpath"):
                raise ValueError(
                    "config.classpath is required for jazzer (compiled classes/jars)"
                )
        elif not config.get("harness"):
            raise ValueError(f"config.harness is required for {tool_name}")

        return [
            "python3",
            _RUNNER,
            "--engine",
            engine,
            "--workspace",
            request.workspace_path,
            "--scan-path",
            request.scan_path or ".",
            "--out",
            str(output_path),
            "--config",
            json.dumps(config),
        ]

    return create_scanner_app(
        tool_name=tool_name,
        version_cmd=version_cmd,
        scan_cmd_builder=build_cmd,
        report_format="json",
        tool_category="fuzzing",
    )
