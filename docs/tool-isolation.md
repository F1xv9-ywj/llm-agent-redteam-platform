# Third-party Tool Isolation

Pinned reference versions for this project snapshot: promptfoo `0.121.15`, garak `0.15.1`, PyRIT `1.0.1`, Giskard `v3 beta`. Detection output always includes `executed: false`; no adapter claims a scan occurred.

Before enabling a tool: verify the version and license, inspect config, use a disposable non-root container, mount only synthetic inputs read-only, provide no production credentials, deny network by default, set CPU/memory/time limits, disable telemetry where supported, and normalize output into `normalized-result/v1`. CLI flags and telemetry behavior change across releases; never execute a generated command without reviewing installed-version documentation.

The promptfoo example uses an echo provider and contains no remote endpoint. garak, PyRIT and Giskard execution intentionally raise `NotImplementedError` until an isolated integration is explicitly designed.
