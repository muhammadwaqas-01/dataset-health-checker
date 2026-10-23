
import json

from main import main


def make_csv(tmp_path, content):
    path = tmp_path / "sample.csv"
    path.write_text(content, encoding="utf-8")
    return str(path)


def test_cli_success_returns_zero(tmp_path, capsys):
    path = make_csv(
        tmp_path,
        "x,y\n"
        "1,2\n"
        "2,1\n"
        "3,4\n"
        "4,3\n"
        "5,6\n"
        "6,5\n",
    )

    exit_code = main([path])

    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Dataset Health Report" in captured.out
    assert captured.err == ""


def test_cli_warning_returns_one_when_fail_on_warning(
    tmp_path, capsys
):
    path = make_csv(
        tmp_path,
        "score\n"
        "50\n"
        "50\n"
        "50\n"
        "50\n"
        "50\n"
        "50\n",
    )

    exit_code = main([path, "--fail-on", "warning"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "WARNING" in captured.out


def test_cli_missing_file_returns_one_and_uses_stderr(
    tmp_path, capsys
):
    missing_path = str(tmp_path / "missing.csv")

    exit_code = main([missing_path])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Error:" in captured.err
    assert captured.out == ""


def test_cli_json_output(tmp_path, capsys):
    path = make_csv(
        tmp_path,
        "x,y\n"
        "1,2\n"
        "2,1\n"
        "3,4\n"
        "4,3\n"
        "5,6\n"
        "6,5\n",
    )

    exit_code = main([path, "--format", "json"])

    captured = capsys.readouterr()
    data = json.loads(captured.out)

    assert exit_code == 0
    assert data["summary"]["rows"] == 6
    assert data["summary"]["columns"] == 2
    assert data["findings"] == []
