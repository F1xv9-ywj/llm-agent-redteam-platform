import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


def write_reports(run: dict[str, Any], out_dir: str | Path) -> list[Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    json_path = out / "report.json"
    json_path.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    row_template = "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>"
    rows = "".join(
        row_template.format(
            html.escape(f["case_id"]),
            html.escape(f["family"]),
            f["severity"],
            "PASS" if f["passed"] else "FAIL",
            html.escape(f["evidence"]),
        )
        for f in run["findings"]
    )
    html_path = out / "report.html"
    summary = run["summary"]
    gate = "PASS" if summary["policy_gate"]["passed"] else "FAIL"
    document = f"""<!doctype html><meta charset="utf-8"><title>RedSentinel Report</title>
<style>body{{font:15px system-ui;margin:40px;color:#172033}}table{{border-collapse:collapse;width:100%}}
th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left}}</style>
<h1>RedSentinel authorized synthetic scan</h1>
<p>Run {run["id"]} · ASR {summary["asr"]:.1%} · Block {summary["block_rate"]:.1%} · Gate {gate}</p>
<table><tr><th>Case</th><th>Family</th><th>Severity</th><th>Result</th><th>Evidence</th></tr>{rows}</table>"""
    html_path.write_text(document, encoding="utf-8")
    suite = ET.Element("testsuite", name="redsentinel", tests=str(run["summary"]["total"]), failures=str(run["summary"]["failed"]))
    for finding in run["findings"]:
        case = ET.SubElement(suite, "testcase", classname=finding["family"], name=finding["case_id"])
        if not finding["passed"]:
            ET.SubElement(case, "failure", message=finding["evidence"])
    junit_path = out / "junit.xml"
    ET.ElementTree(suite).write(junit_path, encoding="utf-8", xml_declaration=True)
    return [json_path, html_path, junit_path]
