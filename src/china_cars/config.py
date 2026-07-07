from pathlib import Path
from typing import Any

import yaml

from china_cars.paths import CONFIG_DIR


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_project_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "project.yml")


def load_sources_config() -> dict[str, Any]:
    return load_yaml(CONFIG_DIR / "sources.yml")

