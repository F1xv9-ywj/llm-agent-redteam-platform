import argparse
import json
from pathlib import Path

from .reports import write_reports
from .scanner import scan
from .storage import RunStore
from .targets import OpenAICompatibleTarget, SafeMockTarget


def main() -> int:
    parser = argparse.ArgumentParser(prog="redsentinel", description="Authorized synthetic LLM security scanner")
    sub = parser.add_subparsers(dest="command", required=True)
    scan_cmd = sub.add_parser("scan")
    scan_cmd.add_argument("--provider", choices=["mock", "openai-compatible"], default="mock")
    scan_cmd.add_argument("--mock-mode", choices=["secure", "vulnerable"], default="secure")
    scan_cmd.add_argument("--authorized", action="store_true", help="Confirm you are authorized to test the target")
    scan_cmd.add_argument("--db", default="redsentinel.db")
    scan_cmd.add_argument("--output", default="reports/latest")
    args = parser.parse_args()
    if not args.authorized:
        parser.error("--authorized is required; test only systems you own or are authorized to assess")
    target = SafeMockTarget(args.mock_mode) if args.provider == "mock" else OpenAICompatibleTarget()
    run = scan(target)
    RunStore(args.db).save(run)
    write_reports(run, Path(args.output))
    print(json.dumps(run["summary"], indent=2))
    return 0 if run["summary"]["policy_gate"]["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
