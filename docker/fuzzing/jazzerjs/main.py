from common.fuzz_service import create_fuzzer_app

app = create_fuzzer_app(
    tool_name="jazzerjs",
    engine="jazzerjs",
    version_cmd=["sh", "-c", "jazzer --version 2>/dev/null || echo 'jazzer.js 4.0.0'"],
)
