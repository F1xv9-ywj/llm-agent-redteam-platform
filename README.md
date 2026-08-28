# RedSentinel · LLM & Agent Red-Team Evaluation Platform

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/OWASP-LLM%20Top%2010%202025-000000" alt="OWASP LLM Top 10 2025">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
</p>

<p align="center">
  <a href="README.md">中文</a> · <a href="README_EN.md">English</a>
</p>

## 中文

### 项目简介

RedSentinel 是一个面向 **LLM、RAG 与 Agent 应用** 的可复现红队评测与回归平台。它把 Prompt Injection、Jailbreak、Sensitive Information Disclosure、Misinformation 与 Excessive Agency 等风险组织成 versioned cases，通过 target adapter、rule-based judges 和 policy gate 生成结构化安全证据。

平台默认运行在 deterministic Safe Mock 上：不联网、不执行真实工具、不读取真实秘密，适合本地演示、CI 回归和安全测试工程作品集。Remote adapter 只允许连接到显式 allowlist 中的、经过地址校验的 OpenAI-compatible endpoint。

> **授权边界：仅测试你拥有或获得明确书面授权的系统。** 本项目不是攻击框架，也不承诺生产防护效果。

![RedSentinel dashboard sample](docs/dashboard-sample.png)

上图是 Safe Mock scan 的真实运行截图；Dashboard 设计参考稿见 [`docs/dashboard-concept.png`](docs/dashboard-concept.png)。

### 为什么做这个项目

LLM security 不应只是一组散落的 payload。一个可以进入工程流程的安全评测需要同时回答：

- 测试 case 属于哪一种风险 taxonomy，严重性和预期 policy 是什么？
- payload 是否真的触发了风险，还是只是模型拒答或普通错误？
- 失败样例能否被 JSON、HTML、JUnit 和 SQLite 追踪？
- CI 是否能在 critical finding 或 policy violation 出现时阻断发布？

RedSentinel 将这些问题落到可审计的 case registry、judge contract、finding schema 和 gate decision 上。

### 核心能力

| 能力 | 实现内容 |
| --- | --- |
| Risk taxonomy | OWASP Top 10 for LLM Applications 2025；覆盖 Prompt Injection、Jailbreak、Sensitive Information Disclosure、Misinformation、Excessive Agency |
| Structured cases | 每个 case 包含 OWASP / MITRE ATLAS mapping、severity、harmless payload 与 expected policy |
| Target adapters | Safe Mock 与 OpenAI-compatible target；统一 timeout、错误 redaction、allowlist 和 redirect policy |
| Independent judging | rule-based judge 与 target response 解耦，输出 trigger、evidence、severity 和 remediation hint |
| Evidence & persistence | SQLite runs/findings persistence；JSON、HTML、JUnit reports；Dashboard 查询 latest runs |
| Policy gate | ASR、block rate、critical findings、coverage 与 pass/fail gate，可用于 CI 回归 |

### 30 秒开始

```bash
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS / Linux
# source .venv/bin/activate

python -m pip install -e ".[dev]"
redsentinel scan --authorized --output reports/sample
uvicorn redsentinel.app:app --reload
```

从 GitHub 下载项目不会自动启动服务。只有当最后一条命令保持运行时，下面的本地地址才可访问：<http://127.0.0.1:8000>。示例结果位于：

- JSON：[`reports/sample/report.json`](reports/sample/report.json)
- HTML：[`reports/sample/report.html`](reports/sample/report.html)
- JUnit：[`reports/sample/junit.xml`](reports/sample/junit.xml)

CLI 退出码约定：`0` 表示 policy gate 通过，`2` 表示发现阻断发布的问题。

### API

```text
GET  /health
GET  /api/cases
GET  /api/tools
GET  /api/runs
GET  /api/runs/{id}
POST /api/scans
```

创建 scan 必须显式提交 `{"authorized": true}`，以避免误测未授权目标。

### Remote target 安全策略

Remote adapter 需要环境变量配置，例如：

```powershell
$env:REDSENTINEL_REMOTE_ALLOWLIST = "api.example.com"
redsentinel scan --authorized --target remote `
  --base-url https://api.example.com/v1 `
  --model your-model `
  --output reports/remote
```

连接前只进行一次 DNS resolution，并复用已验证的地址集合建立 pinned-IP connection；HTTPS 保留原 hostname 用于 Host header、SNI 和证书校验。Redirect、embedded credentials、本机、私网、link-local 和 reserved address 均会被拒绝。

### 第三方工具集成边界

promptfoo、garak、PyRIT、Giskard 仅作为 optional import/command detection 与 normalized contract 设计参考；默认不执行第三方工具，UI 会明确显示 `executed: false`。真正启用前，应单独复核版本、payload 来源、网络访问和隔离权限。

### 测试与质量门禁

```bash
ruff check .
mypy src
pytest
```

本地验证记录：`23 passed`，coverage `95.74%`；secure Safe Mock scan 的 policy gate 通过，vulnerable fixture 会返回阻断退出码。上述数字属于当前 synthetic regression suite，不代表真实模型的安全率。

### 架构

```text
OWASP cases ──┐
              ├── Target adapter ── Rule judges ── Findings
Safe Mock ────┘                              │
Remote API ─────────────────────────────────┴── Policy gate
                                                   │
                              SQLite / JSON / HTML / JUnit / Dashboard
```

```text
src/redsentinel/    API、targets、case registry、judges、policy、reporters、CLI
cases/              versioned synthetic risk cases
tests/              unit / API / CLI / security regression tests
reports/sample/     reproducible sample evidence
docs/                architecture、threat model、metrics、roadmap
```

### 文档导航

- [Architecture](docs/architecture.md)
- [Threat model](docs/threat-model.md)
- [Metrics](docs/metrics.md)
- [Research basis](docs/research-basis.md)
- [Roadmap](docs/roadmap.md)
- [Authorized use](AUTHORIZED_USE.md)
- [Security policy](SECURITY.md)

### 限制

- Rule-based judges 适合确定性回归，不替代人工安全评审、model-specific testing 或生产监控。
- Safe Mock 的 ASR / block rate 只用于验证 pipeline，不应外推为真实模型结论。
- Remote adapter 是最小 OpenAI-compatible chat-completions client，不处理 streaming response 或厂商私有字段。
- 第三方 red-team tools 默认不执行；启用时必须配置独立环境、网络策略和凭据管理。

### License

[MIT](LICENSE)

---

英文版见 [`README_EN.md`](README_EN.md)。
