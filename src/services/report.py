"""Render a Markdown assessment report from the findings ledger.

Workspace-scoped local file I/O, mirroring the ledger's storage model. Only
review-approved (or poc-confirmed) findings reach the body; everything rejected
or still-unverified goes to an audit trail, so the deliverable reflects the
"only verified findings ship" rule as a mechanism, not just a maxim.

The report is self-describing about its own coverage: a missing tool category
(e.g. no IaC container deployed) never blocks the run, it is recorded in the
Tool Coverage section as "not used" so a reader can see exactly which engines
did and did not touch the target. Confirmed PoCs are embedded inline so the
proof travels with the finding.
"""

import json
import logging
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import config.tools as tools_module
from repositories.workspace import WorkspaceRepository
from services.findings import FindingsService

logger = logging.getLogger(__name__)

_SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}

# CodeQL and Linguist are not in the scan registry; surface them as their own
# coverage lanes so "did CodeQL run?" is answerable from the report.
_STANDALONE_LANES = ("codeql", "linguist")


class ReportService:
    """Turns the findings ledger into a Markdown report."""

    def __init__(self, workspace_repository: WorkspaceRepository, findings_service: FindingsService):
        self.workspace_repository = workspace_repository
        self.findings_service = findings_service

    def render_report(self, workspace_id: str, fmt: str = "markdown") -> Dict[str, Any]:
        if fmt != "markdown":
            return {"status": "error", "error": f"Unsupported format '{fmt}' (only 'markdown')."}

        workspace = self.workspace_repository.find_by_id(workspace_id)
        if not workspace:
            return {"status": "error", "error": f"Workspace not found: {workspace_id}"}

        findings = self.findings_service.list_findings(workspace_id).get("findings", [])
        approved, likely, dismissed = self._triage_findings(findings)

        approved.sort(key=self._severity_key, reverse=True)
        likely.sort(key=self._severity_key, reverse=True)

        reports_base = Path(workspace.get_reports_base_dir())
        coverage = self._tool_coverage(reports_base, findings)
        md = self._build_markdown(workspace_id, findings, approved, likely, dismissed, coverage)

        report_path = reports_base / "report.md"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = report_path.with_suffix(".md.tmp")
        tmp.write_text(md, encoding="utf-8")
        tmp.replace(report_path)
        logger.info(f"Rendered report ({len(approved)} verified) → {report_path}")

        return {
            "status": "success",
            "report_path": str(report_path),
            "verified_count": len(approved),
            "likely_count": len(likely),
            "audit_trail_count": len(dismissed),
            "tools_used": coverage["used_flat"],
            "tools_not_used": coverage["unavailable_categories"] + coverage["available_unused_flat"],
        }

    @staticmethod
    def _severity_key(f: Dict[str, Any]) -> int:
        return _SEVERITY_ORDER.get((f.get("severity") or "").lower(), 0)

    @staticmethod
    def _triage_findings(
        findings: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Split the ledger into shipped / likely-or-disputed / dismissed buckets."""
        approved, likely, dismissed = [], [], []
        for f in findings:
            verdict = (f.get("review") or {}).get("verdict")
            status = f.get("status", "")
            if verdict == "rejected" or status in ("review-rejected", "poc-fp", "dismissed"):
                dismissed.append(f)
            elif verdict == "approved" or status in ("review-approved", "poc-confirmed"):
                approved.append(f)
            elif status in ("poc-likely", "review-disputed"):
                likely.append(f)
            else:
                dismissed.append(f)  # still a hypothesis - neither shipped nor buried
        return approved, likely, dismissed

    # ------------------------------------------------------------------ coverage

    def _tool_coverage(self, reports_base: Path, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Classify every tool category as used / available-but-unused / unavailable.

        "Used" is proven by an artifact on disk (or a finding that cites the tool),
        never by mere availability — so the report states what actually ran, not
        what could have.
        """
        used = self._used_tools_from_disk(reports_base)
        for f in findings:
            for tool in (f.get("evidence") or {}).get("tools", []) or []:
                cat = self._category_of(tool)
                if cat:
                    used[cat].add(tool)

        categories = self._category_tool_map()
        healthy = set(tools_module.HEALTHY_TOOLS)

        used_grouped: Dict[str, List[str]] = {}
        available_unused: Dict[str, List[str]] = {}
        unavailable: List[str] = []
        for category, tools in categories.items():
            healthy_here = [t for t in tools if t in healthy]
            used_here = sorted(used.get(category, set()))
            if used_here:
                used_grouped[category] = used_here
            unused_here = sorted(set(healthy_here) - set(used_here))
            if unused_here:
                available_unused[category] = unused_here
            if not healthy_here and not used_here:
                unavailable.append(category)

        used_flat = sorted({t for tools in used_grouped.values() for t in tools})
        available_unused_flat = sorted({t for tools in available_unused.values() for t in tools})
        return {
            "used_grouped": used_grouped,
            "available_unused": available_unused,
            "unavailable_categories": sorted(unavailable),
            "used_flat": used_flat,
            "available_unused_flat": available_unused_flat,
        }

    @staticmethod
    def _used_tools_from_disk(reports_base: Path) -> Dict[str, Set[str]]:
        """A (category, tool) counts as used iff its report dir holds a real artifact."""
        used: Dict[str, Set[str]] = defaultdict(set)

        reports_root = reports_base / "reports"
        if reports_root.exists():
            for cat_dir in reports_root.iterdir():
                if not cat_dir.is_dir() or cat_dir.name.startswith("."):
                    continue
                for tool_dir in cat_dir.iterdir():
                    if tool_dir.is_dir() and any(
                        p.is_file() and not p.name.startswith(".") for p in tool_dir.iterdir()
                    ):
                        used[cat_dir.name].add(tool_dir.name)

        # CodeQL writes SARIF at the reports_base root; Linguist leaves a facts index.
        if any(reports_base.glob("*.sarif")):
            used["codeql"].add("codeql")
        if (reports_base / "code_facts" / "index.json").exists():
            used["linguist"].add("linguist")
        return used

    @staticmethod
    def _category_tool_map() -> Dict[str, List[str]]:
        """category -> registry tool names, plus the standalone CodeQL/Linguist lanes."""
        mapping: Dict[str, List[str]] = defaultdict(list)
        for spec in tools_module._SPECS:
            mapping[spec.category].append(spec.name)
        for lane in _STANDALONE_LANES:
            mapping[lane].append(lane)
        return dict(mapping)

    @staticmethod
    def _category_of(tool: str) -> Optional[str]:
        if tool in _STANDALONE_LANES:
            return tool
        spec = tools_module.TOOL_REGISTRY.get(tool)
        return spec.category if spec else None

    # ------------------------------------------------------------------ markdown

    def _build_markdown(
        self,
        workspace_id: str,
        findings: List[Dict[str, Any]],
        approved: List[Dict[str, Any]],
        likely: List[Dict[str, Any]],
        dismissed: List[Dict[str, Any]],
        coverage: Dict[str, Any],
    ) -> str:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        mode = self._engagement_mode(findings)
        lines = [
            "# Security Assessment Report",
            "",
            f"- **Workspace:** `{workspace_id}`",
            f"- **Generated:** {now}",
            f"- **Engagement mode:** {mode}",
            f"- **Verified findings:** {len(approved)}"
            f"  ·  **Likely / disputed:** {len(likely)}"
            f"  ·  **Dismissed / unverified:** {len(dismissed)}",
            "",
            "---",
            "",
        ]

        lines += self._render_coverage(coverage)

        lines += ["## Verified Findings", ""]
        if not approved:
            lines += ["_No findings passed verification._", ""]
        for f in approved:
            lines += self._render_finding(f, embed_poc=True)

        if likely:
            lines += ["---", "", "## Likely / Disputed (human follow-up)", ""]
            for f in likely:
                lines += self._render_finding(f, embed_poc=True)

        chains = [f for f in approved + likely if f.get("chain_of")]
        if chains:
            lines += ["---", "", "## Attack Paths", ""]
            for f in chains:
                links = ", ".join(f.get("chain_of", []))
                lines.append(f"- **{f.get('id', '?')}** {f.get('title', '')} — chain of {links}")
            lines.append("")

        if dismissed:
            lines += ["---", "", "## Audit Trail (unverified / dismissed)", ""]
            for f in dismissed:
                reason = (
                    f.get("dismissal_reason")
                    or (f.get("review") or {}).get("notes")
                    or f.get("status")
                    or "unverified"
                )
                lines.append(f"- **{f.get('id', '?')}** {f.get('title', '(untitled)')} — _{reason}_")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _engagement_mode(findings: List[Dict[str, Any]]) -> str:
        for f in findings:
            if f.get("engagement_mode"):
                return str(f["engagement_mode"])
        return "unspecified"

    @staticmethod
    def _render_coverage(coverage: Dict[str, Any]) -> List[str]:
        """Make tool coverage explicit - what ran, what was skipped, what was absent."""
        out = ["## Tool Coverage", ""]

        used = coverage["used_grouped"]
        if used:
            out.append("**Tools used** (produced an artifact this run):")
            out += [f"- **{cat}:** {', '.join(tools)}" for cat, tools in sorted(used.items())]
        else:
            out.append("**Tools used:** _none recorded_")
        out.append("")

        avail = coverage["available_unused"]
        if avail:
            out.append("**Available but not used** (deployed and healthy, never invoked):")
            out += [f"- **{cat}:** {', '.join(tools)}" for cat, tools in sorted(avail.items())]
            out.append("")

        unavailable = coverage["unavailable_categories"]
        if unavailable:
            out.append(
                "**Not exercised** (no tool deployed/healthy for this category this run — "
                "the assessment continued without it):"
            )
            out.append(f"- {', '.join(unavailable)}")
            out.append("")

        out += ["---", ""]
        return out

    def _render_finding(self, f: Dict[str, Any], embed_poc: bool = False) -> List[str]:
        meta = f"**Severity:** {f.get('severity', 'unknown')}"
        if f.get("cwe"):
            meta += f" · **{f['cwe']}**"
        if (f.get("novelty") or {}).get("class"):
            meta += f" · **novelty:** {f['novelty']['class']}"
        if f.get("discovery_lane"):
            meta += f" · **lane:** {f['discovery_lane']}"

        out = [f"### {f.get('id', '?')}: {f.get('title', '(untitled)')}", "", meta, ""]

        endpoint = f.get("endpoint") or {}
        if endpoint:
            param = endpoint.get("param", "")
            out.append(
                f"- **Endpoint:** `{endpoint.get('method', '')} {endpoint.get('path', '')}`"
                + (f" (param `{param}`)" if param else "")
            )

        sink = f.get("sink_loc") or {}
        if sink.get("file"):
            out.append(f"- **Location:** `{sink['file']}:{sink.get('line', '?')}`")

        reach = f.get("reachability") or {}
        if reach.get("kind"):
            note = f" — {reach['notes']}" if reach.get("notes") else ""
            out.append(f"- **Reachability:** {reach['kind']}{note}")

        if f.get("hypothesis"):
            out.append(f"- **Hypothesis:** {f['hypothesis']}")
        if f.get("invariant_violated"):
            out.append(f"- **Invariant violated:** {f['invariant_violated']}")
        if f.get("impact"):
            out.append(f"- **Impact:** {f['impact']}")

        out += self._render_poc(f, embed_poc)
        out += self._render_review(f)

        if f.get("remediation"):
            out += ["", "**Remediation:**", "", f["remediation"]]

        out.append("")
        return out

    def _render_poc(self, f: Dict[str, Any], embed_poc: bool) -> List[str]:
        poc = f.get("poc") or {}
        oracle = poc.get("oracle") or {}
        out: List[str] = []

        if oracle.get("kind") or oracle.get("passed") is not None:
            verdict = "PASSED" if oracle.get("passed") else "did not pass"
            decided = f" (decided by {oracle['decided_by']})" if oracle.get("decided_by") else ""
            out.append(f"- **Oracle:** `{oracle.get('kind', 'unknown')}` {verdict}{decided}")
            if oracle.get("evidence"):
                out += ["", "```json", json.dumps(oracle["evidence"], indent=2), "```"]

        if poc.get("rerun_command"):
            out += ["", "**Reproduction:**", "", "```", poc["rerun_command"], "```"]

        if embed_poc:
            script, interpreter = self._load_poc_script(poc)
            if script:
                out += ["", "**Confirmed PoC:**", "", f"```{interpreter}", script, "```"]

        if poc.get("notes"):
            out += ["", poc["notes"]]
        return out

    @staticmethod
    def _load_poc_script(poc: Dict[str, Any]) -> Tuple[Optional[str], str]:
        """Pull the confirmed exploit script inline: prefer the ledger's own copy,
        else read it back from the sandbox artifact JSON it points at."""
        interpreter = str(poc.get("interpreter") or "").lower()
        if interpreter not in ("python", "bash"):
            interpreter = ""

        script = poc.get("script")
        if not script:
            artifact = poc.get("artifact")
            if artifact and str(artifact).endswith(".json"):
                try:
                    data = json.loads(Path(artifact).read_text(encoding="utf-8"))
                    script = data.get("script")
                    interpreter = interpreter or str(data.get("interpreter") or "")
                except Exception as e:  # noqa: BLE001 - a missing/garbled artifact must not break the report
                    logger.warning(f"Could not read PoC artifact {artifact}: {e}")
        return script, interpreter

    @staticmethod
    def _render_review(f: Dict[str, Any]) -> List[str]:
        review = f.get("review") or {}
        if not (review.get("verdict") or review.get("notes")):
            return []
        out = [f"- **Review:** {review.get('verdict', 'pending')}"]
        if review.get("reason_code"):
            out[-1] += f" ({review['reason_code']})"
        if review.get("notes"):
            out[-1] += f" — {review['notes']}"
        if review.get("self_review") or review.get("reduced_independence"):
            out.append("- _Self-review: gate ran with reduced independence (same agent)._")
        return out
