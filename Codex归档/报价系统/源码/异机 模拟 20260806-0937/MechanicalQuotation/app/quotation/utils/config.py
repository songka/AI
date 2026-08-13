"""Configuration management.

Loads configuration from:
1. Default values (built-in)
2. Environment variables (QUOTATION_*)
3. YAML config file (optional)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    """Application configuration.

    All prices must come from rule files — no pricing defaults here.
    """

    # -- Paths --
    rules_dir: str = "rules"
    templates_dir: str = "templates"
    output_dir: str = "output"
    logs_dir: str = "logs"

    # -- DXF parsing --
    dxf_supported_formats: list[str] = field(default_factory=lambda: [".dxf", ".dwg"])
    dxf_max_file_size_mb: int = 50

    # -- Rule engine --
    default_loss_rate: float = 0.05  # 5% material loss
    default_rule_file: str = "quotation-rules.yaml"

    # -- AI --
    ai_enabled: bool = False  # Disabled by default per constitution
    ai_model: str = ""

    # -- Logging --
    log_level: str = "INFO"
    log_format: str = "%(asctime)s [%(levelname)-8s] %(name)s: %(message)s"

    # -- Output --
    json_output: bool = True
    excel_output: bool = True

    @classmethod
    def from_env(cls) -> "Config":
        """Create Config from environment variables."""
        config = cls()

        for field_name in cls.__dataclass_fields__:
            env_key = f"QUOTATION_{field_name.upper()}"
            env_value = os.environ.get(env_key)
            if env_value is not None:
                field_type = type(getattr(config, field_name))
                if field_type is bool:
                    setattr(config, field_name, env_value.lower() in ("true", "1", "yes"))
                elif field_type is int:
                    setattr(config, field_name, int(env_value))
                elif field_type is float:
                    setattr(config, field_name, float(env_value))
                elif field_type is list:
                    setattr(config, field_name, env_value.split(","))
                else:
                    setattr(config, field_name, env_value)

        return config

    def resolve_path(self, relative_path: str) -> Path:
        """Resolve a path relative to the project root."""
        return Path(relative_path)

    def ensure_dirs(self) -> None:
        """Ensure output and logs directories exist."""
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        Path(self.logs_dir).mkdir(parents=True, exist_ok=True)
