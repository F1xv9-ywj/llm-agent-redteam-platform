# Threat Model

## Assets

Remote API keys, scan evidence, allowlist configuration, SQLite reports, and evaluator integrity.

## Trust boundaries and controls

- Browser → API: explicit `authorized` acknowledgment; typed request model.
- API → remote target: only HTTP(S), exact host allowlist, no URL credentials, all DNS answers must be globally routable, re-resolution before each request, redirect rejection, timeout.
- Target → judge: untrusted text; deterministic string/policy checks; no model-as-judge dependency.
- Third-party tools: detection is not execution; isolate filesystem/network/secrets before explicit enablement.

## Non-goals / residual risk

DNS is re-resolved immediately before each request, but application validation alone cannot eliminate every DNS time-of-check/time-of-use race; production use still requires an egress proxy/firewall. This demo does not sandbox arbitrary third-party plugins, provide multi-tenant authentication, or prove absence of model vulnerabilities.
