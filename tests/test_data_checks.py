
import pytest
import numpy as np

from checker.checks import (
    Dataset,
    Severity,
    MissingValuesCheck,
    DuplicateRowsCheck,
    OutlierCheck,
    CorrelationCheck,
)



def make_dataset(headers, rows):
    return Dataset(
        headers=headers,
        rows=rows,
        numeric_columns={},
        text_columns={},
    )


# Test 1 — 10% missing values should produce WARNING
def test_missing_values_warning():
    rows = [
        {"name": "Ali"},
        {"name": "Sara"},
        {"name": ""},
        {"name": "Ahmed"},
        {"name": "Zara"},
        {"name": "Usman"},
        {"name": "Ayesha"},
        {"name": "Hamza"},
        {"name": "Noor"},
        {"name": "Bilal"},
    ]

    dataset = make_dataset(["name"], rows)
    findings = MissingValuesCheck().run(dataset)

    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "10.0%" in findings[0].message


# Test 2 — Less than 5% should produce INFO
def test_missing_values_info():
    rows = [
        {"name": ""},
        *[{"name": f"Person{i}"} for i in range(99)],
    ]

    dataset = make_dataset(["name"], rows)
    findings = MissingValuesCheck().run(dataset)

    assert findings[0].severity == Severity.INFO
    assert "1.0%" in findings[0].message


# Test 3 — 30% missing values should produce ERROR
def test_missing_values_error():
    rows = [
        {"name": ""},
        {"name": ""},
        {"name": ""},
        {"name": "Ali"},
        {"name": "Sara"},
        {"name": "Ahmed"},
        {"name": "Zara"},
        {"name": "Usman"},
        {"name": "Noor"},
        {"name": "Bilal"},
    ]

    dataset = make_dataset(["name"], rows)
    findings = MissingValuesCheck().run(dataset)

    assert findings[0].severity == Severity.ERROR
    assert "30.0%" in findings[0].message


# Test 4 — No missing values should produce no findings
def test_no_missing_values():
    dataset = make_dataset(
        ["name"],
        [{"name": "Ali"}, {"name": "Sara"}],
    )

    assert MissingValuesCheck().run(dataset) == []


# Test 5 — Find exactly two duplicate rows
def test_duplicate_rows():
    dataset = make_dataset(
        ["name", "age"],
        [
            {"name": "Ali", "age": "20"},
            {"name": "Sara", "age": "22"},
            {"name": "Ali", "age": "20"},
            {"name": "Ahmed", "age": "25"},
            {"name": "Sara", "age": "22"},
        ],
    )

    findings = DuplicateRowsCheck().run(dataset)

    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "Found 2 duplicate rows" in findings[0].message
    assert "4, 6" in findings[0].message


# Test 6 — No duplicate rows should produce no findings
def test_no_duplicate_rows():
    dataset = make_dataset(
        ["name", "age"],
        [
            {"name": "Ali", "age": "20"},
            {"name": "Sara", "age": "22"},
            {"name": "Ahmed", "age": "25"},
        ],
    )

    assert DuplicateRowsCheck().run(dataset) == []
def make_outlier_dataset(values):
    return Dataset(
        headers=["score"],
        rows=[{"score": str(value)} for value in values],
        numeric_columns={
            "score": np.asarray(values, dtype=float)
        },
        text_columns={},
    )


def test_outlier_check_detects_known_outlier():
    dataset = make_outlier_dataset([10, 11, 12, 13, 100])

    findings = OutlierCheck().run(dataset)

    assert len(findings) == 1
    assert findings[0].column == "score"
    assert findings[0].severity == Severity.WARNING
    assert "Found 1 potential outlier(s)" in findings[0].message
    assert "CSV line numbers: 6" in findings[0].message


def test_outlier_check_returns_no_finding_without_outliers():
    dataset = make_outlier_dataset([10, 11, 12, 13])

    findings = OutlierCheck().run(dataset)

    assert findings == []


def test_outlier_check_reports_info_for_fewer_than_four_values():
    dataset = make_outlier_dataset([10, 20, 30])

    findings = OutlierCheck().run(dataset)

    assert len(findings) == 1
    assert findings[0].severity == Severity.INFO
    assert "Only 3 valid numeric values" in findings[0].message


def test_outlier_check_ignores_nan_values():
    dataset = make_outlier_dataset([10, 11, 12, 13, 100, np.nan])

    findings = OutlierCheck().run(dataset)

    assert len(findings) == 1
    assert "CSV line numbers: 6" in findings[0].message


def test_correlation_check_detects_perfect_correlation():
    dataset = Dataset(
        headers=["a", "b"],
        rows=[],
        numeric_columns={
            "a": np.array([1, 2, 3, 4, 5], dtype=float),
            "b": np.array([2, 4, 6, 8, 10], dtype=float),
        },
        text_columns={},
    )

    findings = CorrelationCheck().run(dataset)

    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "a" in findings[0].column
    assert "b" in findings[0].column
    assert "1.0000" in findings[0].message


def test_correlation_check_ignores_uncorrelated_columns():
    dataset = Dataset(
        headers=["a", "b"],
        rows=[],
        numeric_columns={
            "a": np.array([1, 2, 3, 4, 5], dtype=float),
            "b": np.array([5, 3, 1, 3, 5], dtype=float),
        },
        text_columns={},
    )

    findings = CorrelationCheck().run(dataset)

    assert findings == []


def test_correlation_check_skips_constant_column():
    dataset = Dataset(
        headers=["a", "b"],
        rows=[],
        numeric_columns={
            "a": np.array([7, 7, 7, 7, 7], dtype=float),
            "b": np.array([1, 2, 3, 4, 5], dtype=float),
        },
        text_columns={},
    )

    findings = CorrelationCheck().run(dataset)

    assert findings == []
