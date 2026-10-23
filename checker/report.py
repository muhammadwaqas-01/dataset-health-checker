
import json
from dataclasses import asdict

from checker.checks import Severity


def _summary(findings, dataset):
    """Build the shared summary information for both report formats."""
    severity_counts = {
        severity.name: sum(
            finding.severity == severity for finding in findings
        )
        for severity in Severity
    }

    return {
        "rows": dataset.row_count(),
        "columns": len(dataset.headers),
        "total_findings": len(findings),
        "findings_by_severity": severity_counts,
    }


def _finding_to_dict(finding):
    """Convert a Finding dataclass into JSON-compatible values."""
    return {
        **asdict(finding),
        "severity": finding.severity.name,
    }


def format_text(findings, dataset):
    """Return a readable text report without printing it."""
    summary = _summary(findings, dataset)

    severity_summary = ", ".join(
        f"{severity}: {count}"
        for severity, count
        in summary["findings_by_severity"].items()
    )

    lines = [
        "Dataset Health Report",
        (
            f"Rows: {summary['rows']} | "
            f"Columns: {summary['columns']} | "
            f"Total findings: {summary['total_findings']}"
        ),
        f"Findings by severity: {severity_summary}",
        "",
    ]

    if not findings:
        lines.append("No findings found. Dataset passed all available checks.")
        return "\n".join(lines)

    for severity in Severity:
        grouped_findings = [
            finding
            for finding in findings
            if finding.severity == severity
        ]

        if not grouped_findings:
            continue

        lines.append(f"{severity.name} ({len(grouped_findings)})")

        for finding in grouped_findings:
            lines.append(
                f"- [{finding.check}] "
                f"Column: {finding.column} | "
                f"{finding.message}"
            )

        lines.append("")

    return "\n".join(lines).rstrip()


def format_json(findings, dataset):
    """Return the report as a JSON string."""
    report = {
        "summary": _summary(findings, dataset),
        "findings": [
            _finding_to_dict(finding)
            for finding in findings
        ],
    }

    if not findings:
        report["message"] = (
            "No findings found. Dataset passed all available checks."
        )

    return json.dumps(report, indent=2)
