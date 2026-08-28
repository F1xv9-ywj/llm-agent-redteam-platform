# Architecture

```mermaid
flowchart LR
  UI[Dashboard / CLI] --> API[FastAPI]
  API --> O[Scanner Orchestrator]
  O --> C[Safe Case Registry]
  O --> T{Target Protocol}
  T --> M[Deterministic Mock]
  T --> R[Allowlisted OpenAI-compatible HTTP]
  O --> J[Independent Rule Judges]
  J --> G[Policy Gate]
  O --> S[(SQLite)]
  S --> P[JSON / HTML / JUnit]
```

Target execution and judging are deliberately separated. A provider cannot declare its own success. The hard gate fails on unauthorized tool actions, synthetic secret leakage, unresolved critical/high findings, or missing required coverage.
