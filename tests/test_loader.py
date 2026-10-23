
import numpy as np
import pytest

from checker.loader import load_csv, numeric_columns, text_columns


def test_load_csv_normal_file(tmp_path):
    file = tmp_path / "data.csv"
    file.write_text("age,name\n20,Ali\n25,Sara\n", encoding="utf-8")

    headers, rows = load_csv(file)

    assert headers == ["age", "name"]
    assert rows == [
        {"age": "20", "name": "Ali"},
        {"age": "25", "name": "Sara"},
    ]


def test_numeric_columns_converts_values_and_blanks_to_nan():
    headers = ["age", "score"]
    rows = [
        {"age": "20", "score": "85.5"},
        {"age": "", "score": "90"},
        {"age": "25", "score": ""},
    ]

    result = numeric_columns(headers, rows)

    np.testing.assert_allclose(
        result["age"], [20.0, np.nan, 25.0], equal_nan=True
    )
    np.testing.assert_allclose(
        result["score"], [85.5, 90.0, np.nan], equal_nan=True
    )


def test_numeric_columns_skips_text_and_all_blank_columns():
    headers = ["age", "name", "empty"]
    rows = [
        {"age": "20", "name": "Ali", "empty": ""},
        {"age": "25", "name": "Sara", "empty": ""},
    ]

    result = numeric_columns(headers, rows)

    assert list(result) == ["age"]


def test_text_columns_returns_text_columns():
    headers = ["age", "name", "empty"]
    rows = [
        {"age": "20", "name": "Ali", "empty": ""},
        {"age": "25", "name": "Sara", "empty": ""},
    ]

    result = text_columns(headers, rows)

    assert list(result) == ["name"]
    assert result["name"].tolist() == ["Ali", "Sara"]


def test_load_csv_file_not_found():
    with pytest.raises(FileNotFoundError):
        load_csv("file_that_does_not_exist.csv")


def test_load_csv_rejects_duplicate_headers(tmp_path):
    file = tmp_path / "duplicate.csv"
    file.write_text("name,name\nAli,Sara\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Duplicate column name"):
        load_csv(file)


def test_load_csv_rejects_header_without_data(tmp_path):
    file = tmp_path / "empty_rows.csv"
    file.write_text("age,name\n", encoding="utf-8")

    with pytest.raises(ValueError, match="no data rows"):
        load_csv(file)