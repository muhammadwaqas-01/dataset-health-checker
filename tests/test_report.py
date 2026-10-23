
import json

import numpy as np

from checker.checks import Dataset, Finding, Severity
from checker.report import format_text, format_json


def make_dataset():
    rows = [
        {"study_hours": "2", "score": "50"},
        {"study_hours": "4", "score": "70"},
        {"study_hours": "6", "score": "90"},
    ]

    return Dataset(
        headers=["study_hours", "score"],
        rows=rows,
        numeric_columns={
            "study_hours": np.array([2.0, 4.0, 6.0]),
            "score": np.array([50.0, 70.0, 90.0]),
        },
        text_columns={},
    )


def make_findings():
    return [
        Finding(
            check="correlation",
            column="study_hours, score",
            severity=Severity.WARNING,
            message="Strong correlation found",
        ),
        Finding(
            check="missing_values",
            column="score",
            severity=Severity.INFO,
            message="Some values are missing",
        ),
    ]


def test_format_text_contains_summary_and_grouped_findings():
    report = format_text(make_findings(), make_dataset())

    assert "Dataset Health Report" in report
    assert "Rows: 3" in report
    assert "Columns: 2" in report
    assert "Total findings: 2" in report
    assert "WARNING (1)" in report
    assert "INFO (1)" in report
    assert "Strong correlation found" in report
    assert "Some values are missing" in report


def test_format_json_can_be_loaded_back():
    report = format_json(make_findings(), make_dataset())
    data = json.loads(report)

    assert data["summary"]["rows"] == 3
    assert data["summary"]["columns"] == 2
    assert data["summary"]["total_findings"] == 2
    assert data["summary"]["findings_by_severity"]["WARNING"] == 1
    assert data["summary"]["findings_by_severity"]["INFO"] == 1
    assert data["findings"][0]["severity"] == "WARNING"
    assert data["findings"][0]["message"] == "Strong correlation found"


def test_no_findings_is_handled():
    dataset = make_dataset()

    text_report = format_text([], dataset)
    json_report = json.loads(format_json([], dataset))

    assert "No findings found" in text_report
    assert json_report["findings"] == []
    assert json_report["summary"]["total_findings"] == 0
    assert "No findings found" in json_report["message"]
