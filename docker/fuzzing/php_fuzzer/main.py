from common.fuzz_service import create_fuzzer_app

app = create_fuzzer_app(
    tool_name="php-fuzzer",
    engine="php-fuzzer",
    version_cmd=["sh", "-c", "php-fuzzer --version 2>/dev/null || echo 'php-fuzzer 0.0.11'"],
)
