from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

Severity = Literal["critical", "high", "medium", "low"]


@dataclass(frozen=True)
class TestCase:
    id: str
    family: str
    title: str
    payload: str
    owasp: str
    atlas: str
    severity: Severity
    expected_policy: Literal["allow", "block"]
    markers: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["markers"] = list(self.markers)
        return data


@dataclass
class TargetResponse:
    text: str
    blocked: bool
    tool_actions: list[str] = field(default_factory=list)
    latency_ms: float = 0.0
    error: str | None = None


@dataclass
class Finding:
    case_id: str
    title: str
    family: str
    owasp: str
    atlas: str
    severity: Severity
    expected_policy: str
    passed: bool
    blocked: bool
    evidence: str
    tool_actions: list[str]
    latency_ms: float
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
