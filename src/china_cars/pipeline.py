from pathlib import Path

from china_cars.db import connect
from china_cars.paths import SQL_DIR
from china_cars.transform import build_all_tables, write_duckdb


def run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    if not sql.strip():
        return

    with connect() as con:
        con.execute(sql)


def run_layer(layer: str) -> None:
    layer_dir = SQL_DIR / layer
    for path in sorted(layer_dir.glob("*.sql")):
        run_sql_file(path)


def run_pipeline() -> None:
    write_duckdb(build_all_tables())
    for layer in ("bronze", "silver", "gold"):
        run_layer(layer)
