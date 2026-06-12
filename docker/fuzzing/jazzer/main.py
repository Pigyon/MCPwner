from common.fuzz_service import create_fuzzer_app

app = create_fuzzer_app(
    tool_name="jazzer",
    engine="jazzer",
    version_cmd=["sh", "-c", "jazzer --version 2>/dev/null || echo 'jazzer 0.30.0'"],
)
