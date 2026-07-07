from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import yaml

from china_cars.db import connect
from china_cars.paths import OPS_DIR, PROJECT_ROOT
from china_cars.transform import (
    COMEX_UNIT_NUMBER_OF_ITEMS,
    COMEX_VEHICLE_PREFIXES,
    _load_chinese_brand_aliases,
    _norm_key,
    load_brand_classification,
)


@dataclass
class QualityCheck:
    name: str
    status: str
    observed: Any
    expected: Any
    details: str = ""


def _single_value(con: duckdb.DuckDBPyConnection, query: str) -> Any:
    return con.execute(query).fetchone()[0]


def _check_count(con: duckdb.DuckDBPyConnection, checks: list[QualityCheck], table: str) -> None:
    observed = _single_value(con, f"select count(*) from {table}")
    checks.append(
        QualityCheck(
            name=f"{table}.row_count",
            status="pass" if observed > 0 else "fail",
            observed=observed,
            expected="> 0",
        )
    )


def _check_period(
    con: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
    table: str,
    expected_min: str,
    expected_max: str,
) -> None:
    observed = con.execute(f"select min(ano_mes), max(ano_mes) from {table}").fetchone()
    checks.append(
        QualityCheck(
            name=f"{table}.period_coverage",
            status="pass" if observed == (expected_min, expected_max) else "fail",
            observed={"min": observed[0], "max": observed[1]},
            expected={"min": expected_min, "max": expected_max},
        )
    )


def _check_no_nulls(
    con: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
    table: str,
    columns: list[str],
) -> None:
    for column in columns:
        observed = _single_value(con, f"select count(*) from {table} where {column} is null")
        checks.append(
            QualityCheck(
                name=f"{table}.{column}.not_null",
                status="pass" if observed == 0 else "fail",
                observed=observed,
                expected=0,
            )
        )


def _check_non_negative(
    con: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
    table: str,
    columns: list[str],
) -> None:
    for column in columns:
        observed = _single_value(con, f"select count(*) from {table} where {column} < 0")
        checks.append(
            QualityCheck(
                name=f"{table}.{column}.non_negative",
                status="pass" if observed == 0 else "fail",
                observed=observed,
                expected=0,
            )
        )


def _check_unique_key(
    con: duckdb.DuckDBPyConnection,
    checks: list[QualityCheck],
    table: str,
    columns: list[str],
) -> None:
    column_list = ", ".join(columns)
    observed = _single_value(
        con,
        f"""
        select count(*)
        from (
            select {column_list}, count(*) as rows
            from {table}
            group by {column_list}
            having count(*) > 1
        )
        """,
    )
    checks.append(
        QualityCheck(
            name=f"{table}.unique_key",
            status="pass" if observed == 0 else "fail",
            observed=observed,
            expected=0,
            details=", ".join(columns),
        )
    )


def _check_brand_scope_coverage(
    con: duckdb.DuckDBPyConnection, checks: list[QualityCheck]
) -> None:
    """Toda marca marcada como chinesa deve aparecer ao menos uma vez nos dados
    extraidos. Teria detectado o desaparecimento do BYD (marca no escopo sem
    correspondencia nos arquivos brutos)."""
    aliases = _load_chinese_brand_aliases()
    canonical_in_data = {
        aliases[_norm_key(row[0])]
        for row in con.execute(
            "select distinct company_or_brand from gold_anfavea_chinese_registrations_by_brand_monthly"
        ).fetchall()
        if _norm_key(row[0]) in aliases
    }
    expected = {
        item["brand"]
        for item in load_brand_classification()
        if item.get("include_in_chinese_cars_scope")
    }
    missing = sorted(expected - canonical_in_data)
    checks.append(
        QualityCheck(
            name="brand_classification.scope_coverage",
            status="pass" if not missing else "fail",
            observed=len(missing),
            expected=0,
            details="Marcas no escopo sem dados: " + ", ".join(missing) if missing else "",
        )
    )


def _check_comex_vehicle_units(
    con: duckdb.DuckDBPyConnection, checks: list[QualityCheck]
) -> None:
    """quantidade_veiculos so pode vir de NCMs de veiculos completos medidos em
    numero de unidades (unidade estatistica 11), nunca de kg."""
    prefixes = ", ".join(f"'{p}'" for p in COMEX_VEHICLE_PREFIXES)
    observed = _single_value(
        con,
        f"""
        select count(*)
        from raw_comex_china_automotive_detail
        where quantidade_veiculos > 0
          and (
            codigo_unidade_estatistica <> '{COMEX_UNIT_NUMBER_OF_ITEMS}'
            or ncm_prefixo_consulta not in ({prefixes})
          )
        """,
    )
    checks.append(
        QualityCheck(
            name="gold_comex.vehicle_quantity_unit_integrity",
            status="pass" if observed == 0 else "fail",
            observed=observed,
            expected=0,
            details="Linhas com quantidade_veiculos fora de unidade 11 / prefixo de veiculo",
        )
    )


def _check_manifest_files(checks: list[QualityCheck]) -> None:
    manifest_path = OPS_DIR / "metadata" / "file_manifest.yml"
    if not manifest_path.exists():
        checks.append(
            QualityCheck("file_manifest.exists", "fail", observed=False, expected=True)
        )
        return

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8")) or {}
    missing: list[str] = []
    size_mismatch: list[str] = []
    for item in manifest.get("files", []):
        path = PROJECT_ROOT / item["path"]
        if not path.exists():
            missing.append(item["path"])
            continue
        if path.stat().st_size != item["size_bytes"]:
            size_mismatch.append(item["path"])

    checks.append(
        QualityCheck(
            "file_manifest.files_exist",
            "pass" if not missing else "fail",
            observed=len(missing),
            expected=0,
            details=", ".join(missing[:10]),
        )
    )
    checks.append(
        QualityCheck(
            "file_manifest.size_matches",
            "pass" if not size_mismatch else "fail",
            observed=len(size_mismatch),
            expected=0,
            details=", ".join(size_mismatch[:10]),
        )
    )


def run_quality_checks(include_manifest: bool = True) -> dict[str, Any]:
    checks: list[QualityCheck] = []
    with connect(read_only=True) as con:
        for table in [
            "gold_anfavea_chinese_registrations_monthly",
            "gold_anfavea_chinese_registrations_by_brand_monthly",
            "raw_anfavea_origin_brand_monthly",
            "gold_comex_china_automotive_monthly",
            "gold_comex_china_automotive_by_prefix_monthly",
            "gold_comex_china_automotive_by_ncm_monthly",
            "raw_cpca_article_metrics",
            "gold_cpca_article_metrics",
            "gold_cpca_passenger_market_monthly",
            "raw_caam_evidence_catalog",
            "gold_caam_evidence_catalog",
        ]:
            _check_count(con, checks, table)

        _check_period(
            con, checks, "gold_anfavea_chinese_registrations_monthly", "2021-01", "2026-06"
        )
        _check_period(con, checks, "gold_comex_china_automotive_monthly", "2021-01", "2026-06")
        _check_period(con, checks, "gold_cpca_passenger_market_monthly", "2021-02", "2026-06")

        _check_no_nulls(
            con, checks, "gold_anfavea_chinese_registrations_monthly", ["ano_mes", "emplacamentos"]
        )
        _check_no_nulls(
            con,
            checks,
            "gold_comex_china_automotive_by_ncm_monthly",
            ["ano_mes", "pais", "ncm_prefixo_consulta", "codigo_ncm"],
        )
        _check_no_nulls(
            con,
            checks,
            "raw_cpca_article_metrics",
            ["ano_mes", "metric_name", "source_file"],
        )
        _check_no_nulls(
            con,
            checks,
            "gold_cpca_article_metrics",
            ["ano_mes", "metric_name", "source_file"],
        )
        _check_no_nulls(
            con,
            checks,
            "raw_caam_evidence_catalog",
            ["title", "source_file", "evidence_role"],
        )
        _check_no_nulls(
            con,
            checks,
            "gold_caam_evidence_catalog",
            ["title", "source_file", "evidence_role"],
        )

        _check_non_negative(
            con,
            checks,
            "gold_anfavea_chinese_registrations_monthly",
            ["emplacamentos", "emplacamentos_total_anfavea"],
        )
        _check_non_negative(
            con,
            checks,
            "gold_comex_china_automotive_by_ncm_monthly",
            ["quantidade_veiculos", "quantidade_estatistica", "kg_liquido", "valor_fob_usd"],
        )
        _check_non_negative(
            con,
            checks,
            "raw_cpca_article_metrics",
            ["value_10k_vehicles"],
        )

        _check_unique_key(con, checks, "gold_anfavea_chinese_registrations_monthly", ["ano_mes"])
        _check_unique_key(
            con,
            checks,
            "gold_anfavea_chinese_registrations_by_brand_monthly",
            ["ano_mes", "vehicle_group", "company_or_brand"],
        )
        _check_unique_key(
            con, checks, "gold_comex_china_automotive_monthly", ["ano_mes", "fluxo", "pais"]
        )
        _check_unique_key(
            con,
            checks,
            "gold_comex_china_automotive_by_prefix_monthly",
            ["ano_mes", "fluxo", "pais", "ncm_prefixo_consulta"],
        )
        _check_unique_key(
            con,
            checks,
            "gold_comex_china_automotive_by_ncm_monthly",
            ["ano_mes", "fluxo", "pais", "codigo_ncm"],
        )
        _check_unique_key(
            con,
            checks,
            "gold_cpca_passenger_market_monthly",
            ["ano_mes"],
        )

        _check_brand_scope_coverage(con, checks)
        _check_comex_vehicle_units(con, checks)

    if include_manifest:
        _check_manifest_files(checks)
    failed = [check for check in checks if check.status != "pass"]
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "pass" if not failed else "fail",
        "summary": {"checks": len(checks), "passed": len(checks) - len(failed), "failed": len(failed)},
        "checks": [asdict(check) for check in checks],
    }


def write_quality_results(result: dict[str, Any] | None = None) -> Path:
    result = result or run_quality_checks()
    output_dir = OPS_DIR / "quality" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = yaml.safe_dump(result, allow_unicode=True, sort_keys=False)

    latest_path = output_dir / "latest.yml"
    timestamp = result["generated_at"].replace(":", "").replace("-", "").replace("T", "_")
    timestamp_path = output_dir / f"{timestamp}.yml"
    latest_path.write_text(payload, encoding="utf-8")
    timestamp_path.write_text(payload, encoding="utf-8")
    return latest_path
