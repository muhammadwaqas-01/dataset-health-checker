
import argparse
import sys
import csv
from checker.loader import load_csv, numeric_columns, text_columns
from checker.checks import (
    Dataset,
    Severity,
    MissingValuesCheck,
    DuplicateRowsCheck,
    ConstantColumnCheck,
    OutlierCheck,
    CorrelationCheck,
)
from checker.report import format_text, format_json


def main(argv=None):
    # Step 1: Build the command-line parser
    parser = argparse.ArgumentParser(
        description="Check a CSV dataset for common data-quality issues."
    )

    parser.add_argument(
        "path",
        help="Path to the CSV file",
    )

    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Report format (default: text)",
    )

    parser.add_argument(
        "--fail-on",
        choices=["warning", "error"],
        default="error",
        help="Exit with code 1 at this severity or higher (default: error)",
    )

    args = parser.parse_args(argv)

    # Step 2: Load the CSV and build the dataset
    try:
        headers, rows = load_csv(args.path)

        numbers = numeric_columns(headers, rows)
        texts = text_columns(headers, rows)

        dataset = Dataset(
            headers=headers,
            rows=rows,
            numeric_columns=numbers,
            text_columns=texts,
        )

    except (OSError, UnicodeError, csv.Error) as exc:
        print(f"Error: Could not read CSV file '{args.path}': {exc}",
              file=sys.stderr)
        return 1

    # Step 3: Run all five checks
    checks = [
        MissingValuesCheck(),
        DuplicateRowsCheck(),
        ConstantColumnCheck(),
        OutlierCheck(),
        CorrelationCheck(),
    ]

    all_findings = []

    for check in checks:
        all_findings.extend(check.run(dataset))

    # Step 4: Print the selected report
    if args.format == "json":
        print(format_json(all_findings, dataset))
    else:
        print(format_text(all_findings, dataset))

    # Step 5: Determine the exit code
    fail_level = {
        "warning": Severity.WARNING.value,
        "error": Severity.ERROR.value,
    }[args.fail_on]

    if any(f.severity.value >= fail_level for f in all_findings):
        return 1

    return 0


if __name__ == "__main__":


    sys.exit(main())
