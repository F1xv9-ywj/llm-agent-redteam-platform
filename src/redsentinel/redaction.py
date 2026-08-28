import re

PATTERNS = (
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)[^\s]+"),
    re.compile(r"(?i)(api[_-]?key[=:]\s*)[^\s,;]+"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{8,}\b"),
)


def redact(value: str) -> str:
    result = value
    for pattern in PATTERNS:
        result = pattern.sub(lambda m: (m.group(1) if m.lastindex else "") + "[REDACTED]", result)
    return result
