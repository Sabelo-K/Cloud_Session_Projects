"""Settings (TOML) and secrets (environment) loading."""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SETTINGS_PATH = ROOT / "config" / "settings.toml"

Settings = dict[str, Any]


class ConfigError(Exception):
    pass


def load_dotenv(path: Path | None = None) -> None:
    """Minimal .env loader for local runs. Never overrides variables already set,
    and ignores empty values so an unfilled `.env.example` copy behaves as 'unset'."""
    path = path or ROOT / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        if value and key not in os.environ:
            os.environ[key] = value


def load_settings(path: Path | None = None) -> Settings:
    with open(path or DEFAULT_SETTINGS_PATH, "rb") as fh:
        return tomllib.load(fh)


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"Missing required environment variable {name} (see .env.example)")
    return value
