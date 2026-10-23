
import pytest
from dataclasses import FrozenInstanceError
from checker.checks import Finding, Severity, Check,run_all


# Test A — Finding immutable hai
def test_finding_is_immutable():
    finding = Finding(
        check="MissingValuesCheck",
        column="age",
        severity=Severity.WARNING,
        message="Missing values found",
    )

    with pytest.raises(FrozenInstanceError):
        finding.message = "Updated message"


# Test B — Severity ordering
def test_severity_ordering():
    severities = [
        Severity.ERROR,
        Severity.INFO,
        Severity.WARNING,
    ]

    sorted_severities = sorted(
        severities,
        key=lambda severity: severity.value,
    )

    assert sorted_severities == [
        Severity.INFO,
        Severity.WARNING,
        Severity.ERROR,
    ]


# Test C — Check abstract hai
def test_check_is_abstract():
    with pytest.raises(TypeError):
        Check()
from checker.checks import (
    ConstantColumnCheck,
    Dataset,
    Severity,
)


def test_constant_column_detects_constant_values():
    dataset = Dataset(
        headers=["department", "score"],
        rows=[
            {"department": "CS", "score": "80"},
            {"department": "CS", "score": "90"},
            {"department": "CS", "score": "75"},
        ],
        numeric_columns={},
        text_columns={},
    )

    check = ConstantColumnCheck()
    findings = check.run(dataset)

    assert len(findings) == 1
    assert findings[0].column == "department"
    assert findings[0].severity == Severity.WARNING


def test_constant_column_ignores_all_blank_values():
    dataset = Dataset(
        headers=["remarks"],
        rows=[
            {"remarks": ""},
            {"remarks": "   "},
            {"remarks": ""},
        ],
        numeric_columns={},
        text_columns={},
    )

    check = ConstantColumnCheck()
    findings = check.run(dataset)

    assert findings == []

def test_run_all_sorts_findings_by_severity():
    class FakeCheck(Check):
        name = "fake"

        def __init__(self, finding):
            self.finding = finding

        def run(self, dataset):
            return [self.finding]

    info = Finding(
        check="fake",
        column="a",
        severity=Severity.INFO,
        message="Info finding",
    )
    error = Finding(
        check="fake",
        column="b",
        severity=Severity.ERROR,
        message="Error finding",
    )
    warning = Finding(
        check="fake",
        column="c",
        severity=Severity.WARNING,
        message="Warning finding",
    )

    checks = [
        FakeCheck(info),
        FakeCheck(error),
        FakeCheck(warning),
    ]

    dataset = Dataset(
        headers=["a", "b", "c"],
        rows=[{"a": "1", "b": "2", "c": "3"}],
        numeric_columns={},
        text_columns={},
    )

    findings = run_all(checks, dataset)

    assert [
        finding.severity
        for finding in findings
    ] == [
        Severity.ERROR,
        Severity.WARNING,
        Severity.INFO,
    ]