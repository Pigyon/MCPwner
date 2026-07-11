"""Unit tests for the findings ledger (FindingsService).

Container-free: stubs the workspace repository and writes to a temp dir, so it runs
anywhere (no /workspaces volume, no Docker). Runnable via pytest or directly:

    python tests/unit/test_findings_ledger.py
"""

import sys
import tempfile
from pathlib import Path

# Make `src` importable without installing the package.
SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from services.findings import FindingsService, _deep_merge  # noqa: E402


class _StubWorkspace:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir

    def get_reports_base_dir(self) -> str:
        return self._base_dir


class _StubWorkspaceRepository:
    """Minimal stand-in for WorkspaceRepository: only find_by_id is used."""

    def __init__(self, workspaces: dict):
        self._workspaces = workspaces

    def find_by_id(self, workspace_id: str):
        return self._workspaces.get(workspace_id)


def _service(tmp: str) -> FindingsService:
    repo = _StubWorkspaceRepository({"ws-1": _StubWorkspace(tmp)})
    return FindingsService(repo)


def test_upsert_creates_and_get_returns():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        stored = svc.upsert_finding("ws-1", {"id": "F-001", "title": "SQLi", "status": "hypothesis"})
        assert stored["id"] == "F-001"
        assert (Path(tmp) / "findings" / "F-001.json").exists()
        got = svc.get_finding("ws-1", "F-001")
        assert got["title"] == "SQLi"
        assert svc.get_finding("ws-1", "F-404") is None


def test_deep_merge_preserves_peer_agent_fields():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        svc.upsert_finding(
            "ws-1",
            {
                "id": "F-002",
                "status": "hypothesis",
                "poc": {"verdict": None},
                "review": {"verdict": None},
            },
        )
        svc.upsert_finding(
            "ws-1",
            {
                "id": "F-002",
                "status": "poc-confirmed",
                "poc": {"verdict": "confirmed", "oracle": {"kind": "differential", "passed": True}},
            },
        )
        svc.upsert_finding("ws-1", {"id": "F-002", "review": {"verdict": "approved"}})
        f = svc.get_finding("ws-1", "F-002")
        assert f["status"] == "poc-confirmed"
        assert f["poc"]["verdict"] == "confirmed"
        assert f["poc"]["oracle"]["passed"] is True  # nested field survived
        assert f["review"]["verdict"] == "approved"  # peer field not clobbered


def test_merge_false_replaces():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        svc.upsert_finding("ws-1", {"id": "F-003", "a": 1, "b": 2})
        svc.upsert_finding("ws-1", {"id": "F-003", "a": 9}, merge=False)
        f = svc.get_finding("ws-1", "F-003")
        assert f == {"id": "F-003", "a": 9}


def test_list_and_status_filter():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        svc.upsert_finding("ws-1", {"id": "F-010", "status": "hypothesis"})
        svc.upsert_finding("ws-1", {"id": "F-011", "status": "poc-confirmed"})
        svc.upsert_finding("ws-1", {"id": "F-012", "status": "poc-confirmed"})
        assert svc.list_findings("ws-1")["count"] == 3
        confirmed = svc.list_findings("ws-1", status="poc-confirmed")
        assert confirmed["count"] == 2
        assert {f["id"] for f in confirmed["findings"]} == {"F-011", "F-012"}


def test_invalid_and_missing_id_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        for bad in ["../evil", "a/b", "", "with space"]:
            try:
                svc.upsert_finding("ws-1", {"id": bad})
                raise AssertionError(f"expected ValueError for id={bad!r}")
            except ValueError:
                pass
        try:
            svc.upsert_finding("ws-1", {"title": "no id"})
            raise AssertionError("expected ValueError for missing id")
        except ValueError:
            pass


def test_unknown_workspace_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        svc = _service(tmp)
        try:
            svc.upsert_finding("nope", {"id": "F-001"})
            raise AssertionError("expected ValueError for unknown workspace")
        except ValueError:
            pass


def test_deep_merge_helper():
    assert _deep_merge({"a": {"x": 1, "y": 2}}, {"a": {"y": 9, "z": 3}}) == {
        "a": {"x": 1, "y": 9, "z": 3}
    }
    assert _deep_merge({"a": [1, 2]}, {"a": [3]}) == {"a": [3]}  # lists replace


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
    print(f"\nAll {len(fns)} findings-ledger tests passed.")
