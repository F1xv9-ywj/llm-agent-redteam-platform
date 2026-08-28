import json
import xml.etree.ElementTree as ET

import pytest

from redsentinel.reports import write_reports
from redsentinel.scanner import scan
from redsentinel.targets import SafeMockTarget
from redsentinel.tools import ADAPTERS


def test_reports_are_real_and_parseable(tmp_path):
    run = scan(SafeMockTarget())
    paths = write_reports(run, tmp_path)
    assert {path.name for path in paths} == {"report.json", "report.html", "junit.xml"}
    assert json.loads((tmp_path / "report.json").read_text())["id"] == run["id"]
    assert "authorized synthetic scan" in (tmp_path / "report.html").read_text()
    assert ET.parse(tmp_path / "junit.xml").getroot().attrib["failures"] == "0"


def test_tool_contract_never_claims_execution():
    statuses = [adapter.status() for adapter in ADAPTERS]
    assert all(status["executed"] is False for status in statuses)
    assert all(status["contract"] == "normalized-result/v1" for status in statuses)
    assert ADAPTERS[0].safe_command("safe.yaml")[-1] == "--no-cache"
    with pytest.raises(NotImplementedError):
        ADAPTERS[1].safe_command("safe.yaml")
