# RedSentinel · LLM & Agent Red-Team Evaluation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/OWASP-LLM%20Top%2010%202025-000000" alt="OWASP LLM Top 10 2025">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
</p>

<p align="center"><a href="README.md">中文版</a></p>

## Overview

RedSentinel is a reproducible red-team evaluation and regression platform for **LLM, RAG, and agent applications**. It organizes Prompt Injection, Jailbreak, Sensitive Information Disclosure, Misinformation, and Excessive Agency into versioned cases, then combines target adapters, independent rule-based judges, and a policy gate to produce structured security evidence.

The default deterministic Safe Mock runs locally: no network access, real tool execution, or real secrets are required. A remote adapter is available for an owned OpenAI-compatible endpoint, but only through an explicit host allowlist and address validation.

> **Authorization boundary:** test only systems you own or have explicit written permission to assess. This project is an evaluation harness, not an exploitation framework or a guarantee of production protection.

![RedSentinel dashboard sample](docs/dashboard-sample.png)

## Features

- **Risk taxonomy:** OWASP Top 10 for LLM Applications 2025 coverage for Prompt Injection, Jailbreak, Sensitive Information Disclosure, Misinformation, and Excessive Agency.
- **Structured cases:** OWASP / MITRE ATLAS mapping, severity, harmless payloads, and expected policy per case.
- **Target adapters:** deterministic Safe Mock and OpenAI-compatible targets with timeout, error redaction, allowlist, and redirect controls.
- **Independent judges:** response judging is decoupled from target execution and records triggers, evidence, severity, and remediation hints.
- **Evidence and persistence:** SQLite runs/findings, JSON, HTML, JUnit XML, and a dashboard for latest runs.
- **Policy gate:** ASR, block rate, critical findings, coverage, and CI-friendly pass/fail decisions.

## Quick start

Downloading the repository does not start a server automatically. Run the following commands once to install dependencies, execute the authorized Safe Mock scan, and start the local service:

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
redsentinel scan --authorized --output reports/sample
uvicorn redsentinel.app:app --reload
```

Only after the last command is running, open <http://127.0.0.1:8000>. Generated [JSON](reports/sample/report.json), [HTML](reports/sample/report.html), and [JUnit](reports/sample/junit.xml) evidence is included for inspection. Exit code `0` means the policy gate passed; `2` means release-blocking findings were detected.

## API and authorization

The API exposes `/health`, `/api/cases`, `/api/tools`, `/api/runs`, `/api/runs/{id}`, and `POST /api/scans`. Every scan request must include `{"authorized": true}` so an authorization acknowledgement is explicit in both CLI and API workflows.

## Remote target security

```bash
export REDSENTINEL_REMOTE_ALLOWLIST=api.example.com
redsentinel scan --authorized --target remote \
  --base-url https://api.example.com/v1 \
  --model your-model \
  --output reports/remote
```

The adapter performs one DNS resolution and reuses the verified address set for a pinned-IP connection. The original hostname is preserved for the HTTP `Host` header, HTTPS SNI, and certificate validation. Redirects, URL credentials, loopback, private, link-local, and reserved addresses are rejected.

## Tool boundary, tests, and limitations

promptfoo, garak, PyRIT, and Giskard are represented through optional detection and a normalized contract; third-party tools are not executed by default and the UI reports `executed: false`. Enable them only after reviewing versions, payload provenance, network access, isolation, and credential handling.

```bash
ruff check .
mypy src
pytest
```

The current synthetic regression suite reports `23 passed` with `95.74%` coverage. The Safe Mock gate passes, while a vulnerable fixture returns the blocking exit code. These figures validate the pipeline, not the security of a real model.

Start with [Architecture](docs/architecture.md), [Threat model](docs/threat-model.md), [Metrics](docs/metrics.md), [Research basis](docs/research-basis.md), [Roadmap](docs/roadmap.md), and the [Authorized use](AUTHORIZED_USE.md) policy.

## License

[MIT](LICENSE)
