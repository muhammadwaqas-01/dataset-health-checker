from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

import numpy as np

class Severity(Enum):
    INFO = 1
    WARNING = 2
    ERROR = 3


@dataclass(frozen=True)
class Finding:
    check: str
    column: str
    severity: Severity
    message: str

@dataclass
class Dataset:
    headers: list[str]
    rows: list[dict[str, str]]
    numeric_columns: dict[str, np.ndarray]
    text_columns: dict[str, np.ndarray]

    def row_count(self) -> int:
        return len(self.rows)

class Check(ABC):
    name: str

    @abstractmethod
    def run(self, dataset: Dataset) -> list[Finding]:
        pass

class MissingValuesCheck(Check):
    name = "missing_values"

    def __init__(self, warn_at: float = 0.05, error_at: float = 0.30,):
        if not 0 <= warn_at <= error_at <= 1:
            raise ValueError("Thresholds must satisfy 0 <= warn_at <= error_at <= 1")

        self.warn_at = warn_at
        self.error_at = error_at

    def run(self, dataset: Dataset) -> list[Finding]:
        findings = []
        total_rows = dataset.row_count()

        if total_rows == 0:
            return findings

        for column in dataset.headers:
            values = [ row.get(column, "") for row in dataset.rows]
            missing_count = sum(
                value is None
                or (
                    isinstance(value, str)
                    and value.strip() == ""
                )
                or (
                    isinstance(value, (int, float, np.number))
                    and np.isnan(value)
                )
                for value in values
            )

            missing_share = missing_count / total_rows

            if missing_count == 0:
                continue

            if missing_share >= self.error_at:
                severity = Severity.ERROR
            elif missing_share >= self.warn_at:
                severity = Severity.WARNING
            else:
                severity = Severity.INFO

            percentage = missing_share * 100

            findings.append(
                Finding(
                    check=self.name,
                    column=column,
                    severity=severity,
                    message=(
                        f"{missing_count}/{total_rows} values "
                        f"are missing ({percentage:.1f}%)"
                    ),
                )
            )

        return findings

class DuplicateRowsCheck(Check):
    name = "duplicate_rows"

    def __init__(self, max_lines: int = 5):
        if max_lines < 0:
            raise ValueError("max_lines cannot be negative")

        self.max_lines = max_lines

    def run(self, dataset: Dataset) -> list[Finding]:
        seen = set()
        duplicate_lines = []

        for index, row in enumerate(dataset.rows):
            row_tuple = tuple(
                row.get(header, "")
                for header in dataset.headers
            )

            if row_tuple in seen:
                # +2 because line 1 is the CSV header
                duplicate_lines.append(index + 2)
            else:
                seen.add(row_tuple)

        if not duplicate_lines:
            return []

        shown_lines = duplicate_lines[:self.max_lines]
        line_text = ", ".join(map(str, shown_lines))

        if len(duplicate_lines) > len(shown_lines):
            line_text += ", ..."

        return [
            Finding(
                check=self.name,
                column="*",
                severity=Severity.WARNING,
                message=(
                    f"Found {len(duplicate_lines)} duplicate rows. "
                    f"CSV line numbers: {line_text}"
                ),
            )
        ]
class ConstantColumnCheck(Check):
    name = "constant_column"

    def run(self, dataset: Dataset) -> list[Finding]:
        findings = []

        for column in dataset.headers:
            # Step 1: Column ki tamam values nikalo
            values = [
                row.get(column, "")
                for row in dataset.rows
            ]

            # Step 2: Blank aur whitespace values ignore karo
            present_values = [
                value
                for value in values
                if value is not None
                and str(value).strip() != ""
            ]

            # Step 3: Agar column mein koi present value nahi,
            # to aglay column par chale jao
            if not present_values:
                continue

            # Step 4: Unique values nikalo
            unique_values = set(present_values)

            # Step 5: Agar sirf ek unique value hai,
            # to column constant hai
            if len(unique_values) == 1:
                findings.append(
                    Finding(
                        check=self.name,
                        column=column,
                        severity=Severity.WARNING,
                        message=(
                            "Column contains only one "
                            "unique non-blank value"
                        ),
                    )
                )

        # Step 6: Findings return karo
        return findings


def run_all(
    checks: list[Check],
    dataset: Dataset,
) -> list[Finding]:
    findings = []

    for check in checks:
        results = check.run(dataset)
        findings.extend(results)

    findings.sort(
        key=lambda f: f.severity.value,
        reverse=True,
    )

    return findings