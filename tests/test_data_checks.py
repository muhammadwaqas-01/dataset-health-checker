
import pytest

from checker.checks import (
    Dataset,
    Severity,
    MissingValuesCheck,
    DuplicateRowsCheck,
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
