from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

from .cases import all_cases
from .judges import judge
from .policy import evaluate_policy
from .targets import Target


def scan(target: Target, selected: list[str] | None = None) -> dict[str, Any]:
    cases = [c for c in all_cases() if not selected or c.id in selected]
    findings = [judge(case, target.invoke(case)) for case in cases]
    failed = [f for f in findings if not f.passed]
    blocked_expected = [f for f in findings if f.expected_policy == "block"]
    policy = evaluate_policy(findings, min(5, len({c.family for c in cases})))
    return {
        "id": str(uuid.uuid4()),
        "created_at": dt.datetime.now(dt.UTC).isoformat(),
        "status": "completed",
        "summary": {
            "total": len(findings),
            "passed": len(findings) - len(failed),
            "failed": len(failed),
            "asr": round(len(failed) / len(findings), 4) if findings else 0,
            "block_rate": round(sum(f.blocked for f in blocked_expected) / len(blocked_expected), 4) if blocked_expected else 0,
            "critical_findings": sum(not f.passed and f.severity == "critical" for f in findings),
            "coverage": sorted({f.owasp.split()[0] for f in findings}),
            "policy_gate": policy.to_dict(),
        },
        "findings": [f.to_dict() for f in findings],
    }
