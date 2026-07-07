from pathlib import Path

import pandas as pd

from china_cars.config import load_project_config
from china_cars.db import connect
from china_cars.paths import PROJECT_ROOT


def list_curated_tables() -> list[str]:
    query = """
        select table_name
        from information_schema.tables
        where table_schema = 'main'
          and table_name like 'gold_%'
        order by table_name
    """
    with connect(read_only=True) as con:
        return [row[0] for row in con.execute(query).fetchall()]


def export_workbook(path: str | Path | None = None) -> Path:
    config = load_project_config()
    export_path = (
        PROJECT_ROOT / config["exports"]["excel_dir"] / config["exports"]["default_workbook"]
        if path is None
        else Path(path)
    )
    export_path.parent.mkdir(parents=True, exist_ok=True)

    tables = list_curated_tables()
    with connect(read_only=True) as con, pd.ExcelWriter(export_path, engine="xlsxwriter") as writer:
        if not tables:
            pd.DataFrame(
                [{"message": "Nenhuma tabela gold_ encontrada para exportacao."}]
            ).to_excel(writer, sheet_name="metadata", index=False)
            return export_path

        for table in tables:
            sheet_name = table.removeprefix("gold_")[:31] or table[:31]
            con.execute(f"select * from {table}").df().to_excel(
                writer,
                sheet_name=sheet_name,
                index=False,
            )

    return export_path
