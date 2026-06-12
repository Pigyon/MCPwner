import shlex
from pathlib import Path

from common.base_service import create_scanner_app
from common.models import ScanRequest

# Written when no Dockerfiles are found so the scan still yields a valid,
# zero-finding SARIF report instead of erroring out.
_EMPTY_SARIF = (
    '{"version":"2.1.0",'
    '"$schema":"https://json.schemastore.org/sarif-2.1.0-rtm.5.json",'
    '"runs":[{"tool":{"driver":{"name":"Hadolint"}},"results":[]}]}'
)


def build_hadolint_cmd(request: ScanRequest, output_path: Path):
    full_scan_path = Path(request.workspace_path) / request.scan_path

    config = request.config or {}
    # hadolint takes explicit file arguments (it does not recurse a directory), so
    # discover Dockerfiles here and pass them in.
    patterns = config.get("patterns") or [
        "Dockerfile",
        "Dockerfile.*",
        "*.dockerfile",
        "*.Dockerfile",
    ]

    dockerfiles = sorted(
        {str(p) for pat in patterns for p in full_scan_path.rglob(pat) if p.is_file()}
    )

    out_q = shlex.quote(str(output_path))

    if not dockerfiles:
        return ["sh", "-c", f"printf '%s' {shlex.quote(_EMPTY_SARIF)} > {out_q}"]

    # --no-fail keeps the exit code at 0 even when issues are found; hadolint prints
    # one merged SARIF document across all files to stdout.
    inner = ["hadolint", "--no-fail", "--format", "sarif", *dockerfiles]
    script = " ".join(shlex.quote(c) for c in inner) + f" > {out_q}"
    return ["sh", "-c", script]


app = create_scanner_app(
    tool_name="hadolint",
    version_cmd=["hadolint", "--version"],
    scan_cmd_builder=build_hadolint_cmd,
    report_format="sarif",
    tool_category="iac",
)
