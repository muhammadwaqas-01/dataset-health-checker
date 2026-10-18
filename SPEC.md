# Dataset Health Checker — Specification

## 1. Project Overview

Dataset Health Checker is a command-line tool that reads a CSV dataset and identifies common data quality problems.

It reports findings with severity levels so users can understand which problems need attention first.

The tool analyzes data and reports problems. It does not automatically modify or clean the original dataset.

## 2. Input

- The input must be a CSV file.
- The CSV file must contain a header row with column names.
- Each subsequent row represents one record.
- Blank cells are treated as missing values.
- Numeric columns are converted to NumPy arrays of floating-point values.
- Blank values in numeric columns are represented by `numpy.nan`.
- A column is considered numeric only when all its present values are finite numbers.
- Columns containing non-numeric values are treated as text columns.

## 3. Data Quality Checks

The tool performs the following five checks.

### 3.1 Missing Values

Identifies columns containing blank or missing values.

For each affected column, the report includes the number or proportion of missing values.

Severity rules:

- **INFO:** Some values are missing, but the missing-value proportion is below 5%.
- **WARNING:** At least 5% but less than 30% of the column's values are missing.
- **ERROR:** At least 30% of the column's values are missing.
- No finding is generated for a column with no missing values.

The check uses configurable thresholds with default values of `warn_at=0.05` and `error_at=0.30`.

### 3.2 Duplicate Rows

Identifies rows that are identical across all columns.

When duplicates are found, the report includes the number of duplicate occurrences and the first few relevant row numbers.

Severity: **WARNING** when duplicate rows are found.

### 3.3 Constant Columns

Identifies columns whose present values are all the same.

Constant columns may provide little or no useful information for analysis.

Severity: **WARNING** when a constant column is found.

Missing values are ignored when determining whether a column is constant.

### 3.4 Outliers

Identifies unusually high or low values in numeric columns using the Interquartile Range (IQR) method.

The default multiplier is `k=1.5`.

The check calculates:

- First quartile (Q1)
- Third quartile (Q3)
- Interquartile range (IQR)
- Lower and upper outlier bounds

Values outside the calculated bounds are considered potential outliers.

Requirements:

- Use NumPy's `nanpercentile` so missing values do not affect the quartile calculations.
- Skip columns with fewer than four present numeric values and report an INFO finding.
- When outliers are found, report their count and relevant row numbers.
- Handle an IQR of zero safely so that a constant column is not incorrectly reported as containing many outliers.

Severity: **WARNING** when outliers are detected.

Outlier detection identifies potential anomalies; it does not prove that a value is incorrect.

### 3.5 Highly Correlated Columns

Identifies pairs of numeric columns with a strong linear correlation.

The default absolute correlation threshold is `0.95`.

Requirements:

- Calculate Pearson correlation using NumPy.
- Use only rows where both columns have present numeric values.
- Skip pairs with fewer than five shared valid observations.
- Skip constant columns to avoid invalid correlation calculations.
- Report each column pair only once.
- Report the names of both columns and their correlation value.

Severity: **WARNING** when the absolute correlation is greater than or equal to `0.95`.

Correlation does not imply causation.

## 4. Severity Levels

The tool supports three severity levels:

| Severity | Meaning |
|---|---|
| `ERROR` | A serious data quality issue |
| `WARNING` | A potential issue that may need attention |
| `INFO` | Informational result or limitation of a check |

Findings are ordered from highest to lowest severity:

1. ERROR
2. WARNING
3. INFO

Each finding contains the check name, an optional column reference, its severity, and a human-readable message.

## 5. Reports

The tool supports two output formats: text and JSON.

### 5.1 Text Report

The text report includes:

- Dataset row count
- Dataset column count
- Number of findings at each severity level
- Findings grouped by severity, from ERROR to INFO
- A clear message when no findings are present

### 5.2 JSON Report

The JSON report contains the same summary information and findings as the text report in a machine-readable format.

Severity values are represented as strings, such as `"ERROR"`, `"WARNING"`, and `"INFO"`.

The report-formatting functions return strings instead of printing directly to the terminal.

## 6. Command-Line Interface

The tool is launched using `main.py`.

Basic usage:

`python main.py data/sample.csv`

Available arguments:

- `path`: Required path to the input CSV file.
- `--format`: Output format, either `text` or `json`. Defaults to `text`.
- `--fail-on`: Minimum severity that causes a non-zero result. Accepts `warning` or `error`. Defaults to `error`.

Examples:

`python main.py data/sample.csv --format text`

`python main.py data/sample.csv --format json`

`python main.py data/sample.csv --fail-on warning`

The command-line runner loads the dataset, executes all five checks, formats the report, and returns the appropriate exit code.

## 7. Error Handling and Exit Codes

The tool handles input-file errors by displaying a clear error message on standard error.

Exit codes:

- **0:** The tool ran successfully and no finding reached the configured `--fail-on` severity.
- **1:** At least one finding reached the configured `--fail-on` severity, or the input file could not be processed.
- **2:** Invalid command-line usage, handled by `argparse`.

For example, with the default `--fail-on error`, WARNING and INFO findings alone do not cause exit code 1.

## 8. Testing

The project uses `pytest`.

Tests cover:

- CSV loading and file errors
- Numeric and text column detection
- Missing-value handling
- Finding immutability and severity ordering
- Abstract check behavior
- Missing values and duplicate rows
- Constant columns
- Outlier detection and IQR edge cases
- Correlation detection and skipped cases
- Text and JSON report formatting
- CLI arguments, output, and exit codes

Temporary files should be used where appropriate so tests do not depend on the user's actual files.

## 9. Project Structure

```text
dataset-health-checker/
├── checker/
│   ├── __init__.py
│   ├── loader.py
│   ├── checks.py
│   └── report.py
├── tests/
├── data/
│   └── sample.csv
├── main.py
├── README.md
├── SPEC.md
├── requirements.txt
└── .gitignore
```

## 10. Out of Scope

The project will not:

- Automatically clean or modify the original CSV.
- Replace missing values automatically.
- Train machine-learning models.
- Provide a graphical user interface.
- Guarantee that every detected outlier is an error.
- Infer causal relationships from correlated columns.

The purpose is to identify and report potential data quality issues, not to make automatic decisions about how the dataset should be changed.
