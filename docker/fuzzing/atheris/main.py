from common.fuzz_service import create_fuzzer_app

app = create_fuzzer_app(
    tool_name="atheris",
    engine="atheris",
    version_cmd=[
        "sh",
        "-c",
        "python3 -c \"import importlib.metadata as m; print(m.version('atheris'))\" "
        "2>/dev/null || echo 1.0.3",
    ],
)
