from pathlib import Path

import duckdb

from china_cars.config import load_project_config
from china_cars.paths import PROJECT_ROOT


def database_path() -> Path:
    config = load_project_config()
    return PROJECT_ROOT / config["project"]["database_path"]


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path), read_only=read_only)

