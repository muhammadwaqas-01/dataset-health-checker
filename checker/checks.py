from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
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

class OutlierCheck(Check):
    name = "outliers"

    def __init__(self, k: float = 1.5):
        if not np.isfinite(k) or k < 0:
            raise ValueError("k must be a finite, non-negative number")

        self.k = k

    def run(self, dataset: Dataset) -> list[Finding]:
        findings = []

        for column, raw_values in dataset.numeric_columns.items():
            # Convert values to a NumPy array.
            values = np.asarray(raw_values, dtype=float)

            # Ignore NaN and infinite values for this calculation.
            valid_mask = np.isfinite(values)
            valid_values = values[valid_mask]

            # IQR-based outlier detection needs at least 4 valid values.
            if len(valid_values) < 4:
                findings.append(
                    Finding(
                        check=self.name,
                        column=column,
                        severity=Severity.INFO,
                        message=(
                            f"Only {len(valid_values)} valid numeric values; "
                            "at least 4 are required to check for outliers"
                        ),
                    )
                )
                continue

            # Calculate Q1 and Q3, ignoring NaN values.
            q1, q3 = np.nanpercentile(valid_values, [25, 75])

            # Calculate IQR and the lower/upper fences.
            iqr = q3 - q1
            lower_fence = q1 - self.k * iqr
            upper_fence = q3 + self.k * iqr

            # Find outliers while preserving original row positions.
            outlier_mask = valid_mask & (
                (values < lower_fence)
                | (values > upper_fence)
            )
            outlier_indices = np.flatnonzero(outlier_mask)

            if len(outlier_indices) == 0:
                continue

            # CSV line 1 contains headers, so data starts at line 2.
            csv_lines = [
                int(index) + 2
                for index in outlier_indices
            ]
            line_text = ", ".join(map(str, csv_lines))

            findings.append(
                Finding(
                    check=self.name,
                    column=column,
                    severity=Severity.WARNING,
                    message=(
                        f"Found {len(outlier_indices)} potential outlier(s). "
                        f"CSV line numbers: {line_text}. "
                        f"Lower fence={lower_fence:g}, "
                        f"upper fence={upper_fence:g}"
                    ),
                )
            )

        return findings

class CorrelationCheck(Check):
    name = "correlation"

    def __init__(self, threshold: float = 0.95):
        if not np.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError("threshold must be between 0 and 1")
        self.threshold = threshold

    def run(self, dataset: Dataset) -> list[Finding]:
        findings = []

        # Generate each pair exactly once.
        columns = list(dataset.numeric_columns.items())

        for (column_a, raw_a), (column_b, raw_b) in combinations(
            columns, 2
        ):
            a = np.asarray(raw_a, dtype=float)
            b = np.asarray(raw_b, dtype=float)

            # Use rows where both values are finite.
            mask = np.isfinite(a) & np.isfinite(b)
            a_shared = a[mask]
            b_shared = b[mask]

            # Require at least 5 shared rows.
            if len(a_shared) < 5:
                continue

            # Correlation is undefined for constant data.
            if np.ptp(a_shared) == 0 or np.ptp(b_shared) == 0:
                continue

            correlation = np.corrcoef(a_shared, b_shared)[0, 1]

            if abs(correlation) >= self.threshold:
                findings.append(
                    Finding(
                        check=self.name,
                        column=f"{column_a}, {column_b}",
                        severity=Severity.WARNING,
                        message=(
                            f"Strong correlation between "
                            f"'{column_a}' and '{column_b}': "
                            f"{correlation:.4f} "
                            f"(threshold={self.threshold})"
                        ),
                    )
                )

        return findings
