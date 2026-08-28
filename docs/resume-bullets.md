# Resume Bullets

- 构建 Python 3.11 / FastAPI 的 LLM security regression platform，以独立规则判定、SQLite 审计与 JSON/HTML/JUnit 输出覆盖 6 个无害合成安全用例。
- 实现 remote target SSRF 防护基线（scheme 校验、精确 allowlist、私网/loopback 拒绝、timeout、secret redaction）及 unauthorized tool / secret leakage release hard gates。
- 使用 pytest 验证 taxonomy registry、scoring、policy gate、storage、API contract 与 remote failure handling，并通过响应式 dashboard 展示可追溯 findings。
