# Reused from Week 1 project: csv-analyzer/analyzer/loader.py
import csv
import math
import numpy as np
from collections import Counter


def load_csv(path: str) -> tuple[list[str], list[dict[str, str]]]:
    """
    Load a CSV file and return its headers and rows.

    Args:
        path: Path of the CSV file.

    Returns:
        A tuple containing the headers and rows.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is empty, has no data rows,
            contains duplicate column names, or is not valid UTF-8.
    """
    try:
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)

            if reader.fieldnames is None:
                raise ValueError("The CSV file is empty!")

            headers = [header.strip() for header in reader.fieldnames]

            duplicates = [
                header
                for header, count in Counter(headers).items()
                if count > 1
            ]

            if duplicates:
                raise ValueError(
                    f"Duplicate column name: {duplicates[0]}"
                )

            rows = []

            for row in reader:
                if None in row:
                    raise ValueError(
                        f"Line {reader.line_num}: "
                        "row has more values than headers"
                    )

                clean_row = {}

                for key, value in row.items():
                    clean_key = key.strip()
                    clean_value = "" if value is None else value.strip()
                    clean_row[clean_key] = clean_value

                rows.append(clean_row)

        if not rows:
            raise ValueError(
                "The CSV file has a header but no data rows"
            )

        return headers, rows

    except UnicodeDecodeError as e:
        raise ValueError(
            "The file is not valid UTF-8 text"
        ) from e
def is_number(value: str) -> bool:
    """
    Check whether a string represents a finite number.

    Args:
        value: String value to check.

    Returns:
        True if the value is a finite number, otherwise False.
    """
    try:
        number = float(value)
        return math.isfinite(number)
    except ValueError:
        return False

def numeric_columns(headers, rows):
    numeric = {}

    for header in (headers):
        values = [row[header] for row in rows]
        non_empty = [value for value in values if value.strip() != ""]

        # Skip columns that contain only empty values
        if not non_empty:
            continue

        # Skip columns containing non-numeric or non-finite values
        if not all(is_number(value) for value in non_empty):
            continue

        # Convert blank values to NaN and all values to floats
        numeric[header] = np.array(
            [float(value) if value.strip() != "" else np.nan for value in values],
            dtype=float
        )

    return numeric

def text_columns(headers, rows):
    text = {}

    for header in (headers):
        values = [row[header] for row in rows]
        non_empty = [value for value in values if value.strip() != ""]

        # Skip columns that contain only empty values
        if not non_empty:
            continue

        # Skip columns containing only numeric values
        if all(is_number(value) for value in non_empty):
            continue

        # Store text column values
        text[header] = np.array(values, dtype=str)

    return text