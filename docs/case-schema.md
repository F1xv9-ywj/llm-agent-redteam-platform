# Case Schema

| Field | Meaning |
|---|---|
| `id` | Stable regression identifier |
| `family`, `title` | Human-readable risk classification |
| `payload` | Harmless synthetic instruction only |
| `owasp`, `atlas` | External taxonomy mappings |
| `severity` | critical / high / medium / low |
| `expected_policy` | allow or block |
| `markers` | Deterministic evidence markers |

Cases are immutable dataclasses. Additions must remain non-operational and include regression tests.
