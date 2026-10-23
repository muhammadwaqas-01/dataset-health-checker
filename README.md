# Dataset Health Checker

A lightweight Python command-line tool that checks CSV datasets for common data quality issues and generates readable text or JSON reports.

## Features

The tool currently runs five data quality checks:

- **Missing values:** Identifies columns containing missing values.
- **Duplicate rows:** Detects duplicate records and reports their CSV line numbers.
- **Constant columns:** Identifies columns containing only one unique non-blank value.
- **Outliers:** Uses the Interquartile Range (IQR) method to flag potential numerical outliers.
- **Correlation:** Identifies strongly correlated numerical column pairs using a configurable threshold.

## Example Report

Run the tool against the included sample dataset:

```powershell
python main.py data/sample.csv
```

Example output:

```text
Dataset Health Report
Rows: 20 | Columns: 6 | Total findings: 5
Findings by severity: INFO: 0, WARNING: 5, ERROR: 0

WARNING (5)
- [missing_values] Column: department | 2/20 values are missing (10.0%)
- [duplicate_rows] Column: * | Found 2 duplicate rows. CSV line numbers: 20, 21
- [constant_column] Column: source | Column contains only one unique non-blank value
- [outliers] Column: score | Found 1 potential outlier(s). CSV line numbers: 19. Lower fence=45.625, upper fence=94.625
- [correlation] Column: study_hours, practice_hours | Strong correlation between 'study_hours' and 'practice_hours': 1.0000 (threshold=0.95)
```

The output above comes from a run of the sample dataset.

## Usage

### Requirements

- Python 3.12 (or a compatible version)
- Dependencies listed in `requirements.txt`

### Setup

Clone the repository and navigate to the project directory:

```powershell
git clone <repository-url>
cd dataset-health-checker
```

Create and activate a virtual environment:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

### Run the checks

Generate a text report:

```powershell
python main.py data/sample.csv
```

Generate a JSON report:

```powershell
python main.py data/sample.csv --format json
```

Treat warnings as failures:

```powershell
python main.py data/sample.csv --fail-on warning
```

Treat only errors as failures:

```powershell
python main.py data/sample.csv --fail-on error
```

### Command-line options

| Option | Description |
|---|---|
| `path` | Path to the input CSV file |
| `--format text` | Generate a human-readable text report |
| `--format json` | Generate a JSON report |
| `--fail-on warning` | Exit with a failure status when warnings or errors are found |
| `--fail-on error` | Exit with a failure status only when errors are found |

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | No findings meet the selected failure threshold |
| `1` | Findings meet the selected failure threshold |
| `2` | Invalid command-line arguments |

Input-file errors are reported to standard error.

## Run Tests

Run the test suite from the project root:

```powershell
python -m pytest
```

## Limitations

- The tool currently supports CSV input.
- Outliers are flagged as potential issues; they are not automatically removed or corrected.
- Correlation indicates a statistical relationship, not causation.
- Results depend on the implemented checks and their thresholds.
- The tool reports data quality issues but does not automatically clean the dataset.

## Future Improvements

- Add configurable thresholds for additional checks.
- Support more input formats.
- Add richer summary statistics and report customization.
- Explore additional data quality checks.

## Project Status

This project is a learning-focused data quality checker built with Python, NumPy, and automated tests.
