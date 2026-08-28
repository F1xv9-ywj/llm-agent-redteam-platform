from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolAdapter:
    name: str
    version: str
    executable: str | None = None
    module: str | None = None

    def detected(self) -> bool:
        return bool((self.executable and shutil.which(self.executable)) or (self.module and importlib.util.find_spec(self.module)))

    def safe_command(self, config: str) -> list[str]:
        if self.name == "promptfoo":
            return ["promptfoo", "eval", "-c", config, "--no-cache"]
        raise NotImplementedError(f"{self.name} execution requires an isolated, explicitly approved integration")

    def status(self) -> dict[str, Any]:
        return {"name": self.name, "version": self.version, "detected": self.detected(), "executed": False, "contract": "normalized-result/v1"}


ADAPTERS = (
    ToolAdapter("promptfoo", "0.121.15", "promptfoo"),
    ToolAdapter("garak", "0.15.1", "garak"),
    ToolAdapter("PyRIT", "1.0.1", module="pyrit"),
    ToolAdapter("Giskard", "v3 beta", module="giskard"),
)
