from unittest.mock import patch

import pytest

from redsentinel import cli


def test_cli_scan_success_writes_reports(tmp_path):
    args = [
        "redsentinel",
        "scan",
        "--authorized",
        "--db",
        str(tmp_path / "runs.db"),
        "--output",
        str(tmp_path / "reports"),
    ]
    with patch("sys.argv", args):
        assert cli.main() == 0
    assert (tmp_path / "reports" / "report.json").exists()


def test_cli_returns_two_when_policy_gate_fails(tmp_path):
    args = [
        "redsentinel",
        "scan",
        "--authorized",
        "--mock-mode",
        "vulnerable",
        "--db",
        str(tmp_path / "runs.db"),
        "--output",
        str(tmp_path / "reports"),
    ]
    with patch("sys.argv", args):
        assert cli.main() == 2


def test_cli_requires_authorization():
    with patch("sys.argv", ["redsentinel", "scan"]), pytest.raises(SystemExit) as exc:
        cli.main()
    assert exc.value.code == 2
