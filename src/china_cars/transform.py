from __future__ import annotations

import csv
import html
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import duckdb
import pandas as pd
import yaml
from openpyxl import load_workbook

from china_cars.db import database_path
from china_cars.paths import OPS_DIR, RAW_DIR


MONTHS = {
    "Jan": "01",
    "Fev": "02",
    "Mar": "03",
    "Abr": "04",
    "Mai": "05",
    "Jun": "06",
    "Jul": "07",
    "Ago": "08",
    "Set": "09",
    "Out": "10",
    "Nov": "11",
    "Dez": "12",
}
COMEX_NCM_PREFIXES = ("8702", "8703", "8704", "8706", "8707", "8708", "87011")
# Prefixos que representam veiculos completos: a quantidade estatistica destes
# NCMs (unidade 11 = numero de unidades) pode ser lida como "veiculos".
# 8707 (carrocerias) e 8708 (autopecas, misto de kg e unidades) ficam de fora.
COMEX_VEHICLE_PREFIXES = ("8702", "8703", "8704", "8706", "87011")
COMEX_UNIT_NUMBER_OF_ITEMS = "11"
COMEX_CHINA_CODE = "160"


def _sign_value(direction: str, value: str) -> float:
    number = float(value)
    return -number if direction in {"下降", "下跌", "减少"} else number


def _clean_html_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="ignore")
    text = html.unescape(text)
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<.*?>", " ", text)
    return " ".join(text.split())


def _extract_title(text: str) -> str:
    match = re.search(r"([〖【][^】〗]+[】〗][^发布时间]+)", text)
    return match.group(1).strip() if match else ""


def _extract_article_period(text: str) -> tuple[int | None, int | None]:
    title = _extract_title(text)
    source = title or text
    match = re.search(r"(20\d{2})年(\d{1,2})月", source)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _metric_record(
    *,
    source: str,
    article_type: str,
    path: Path,
    title: str,
    year: int,
    month: int,
    metric_name: str,
    value_10k: float,
    yoy_pct: float | None = None,
    mom_pct: float | None = None,
    ytd_value_10k: float | None = None,
    ytd_yoy_pct: float | None = None,
    notes: str = "",
    unit: str = "vehicles",
) -> dict[str, object]:
    value_vehicles = value_10k * 10_000 if unit == "vehicles" else None
    return {
        "source": source,
        "article_type": article_type,
        "ano": year,
        "mes": month,
        "ano_mes": f"{year}-{month:02d}",
        "metric_name": metric_name,
        "value_10k_vehicles": value_10k,
        "value_vehicles": value_vehicles,
        "yoy_pct": yoy_pct,
        "mom_pct": mom_pct,
        "ytd_value_10k_vehicles": ytd_value_10k,
        "ytd_value_vehicles": ytd_value_10k * 10_000 if ytd_value_10k is not None else None,
        "ytd_yoy_pct": ytd_yoy_pct,
        "title": title,
        "unit": unit,
        "source_file": str(path),
        "notes": notes,
        "extracted_at": datetime.now().isoformat(timespec="seconds"),
    }


def extract_cpca_article_metrics() -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base_dir = RAW_DIR / "cpca" / "articles"
    if not base_dir.exists():
        return pd.DataFrame()

    for path in sorted(base_dir.glob("*/*.html")):
        article_type = path.parent.name
        text = _clean_html_text(path)
        title = _extract_title(text)
        year, month = _extract_article_period(text)
        if not year or not month or year < 2021 or year > 2026:
            continue

        def add_from_match(metric_name: str, pattern: str) -> None:
            match = re.search(pattern, text)
            if not match:
                return
            records.append(
                _metric_record(
                    source="CPCA",
                    article_type=article_type,
                    path=path,
                    title=title,
                    year=year,
                    month=month,
                    metric_name=metric_name,
                    value_10k=float(match.group("value")),
                    yoy_pct=_sign_value(match.group("yoy_dir"), match.group("yoy")),
                    mom_pct=_sign_value(match.group("mom_dir"), match.group("mom"))
                    if "mom_dir" in match.groupdict() and match.group("mom_dir")
                    else None,
                    ytd_value_10k=float(match.group("ytd")) if match.groupdict().get("ytd") else None,
                    ytd_yoy_pct=_sign_value(match.group("ytd_dir"), match.group("ytd_yoy"))
                    if match.groupdict().get("ytd_yoy")
                    else None,
                )
            )

        add_from_match(
            "narrow_passenger_retail",
            r"狭义乘用车市场\s*零售\s*销量达(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%[；;]1[-－—]\d+月份累计销量(?P<ytd>[0-9.]+)万辆，同比(?P<ytd_dir>增长|下降)(?P<ytd_yoy>[0-9.]+)%",
        )
        add_from_match(
            "sedan_retail",
            r"轿车销量(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%[；;]累计销量(?P<ytd>[0-9.]+)万辆，同比(?P<ytd_dir>增长|下降)(?P<ytd_yoy>[0-9.]+)%",
        )
        add_from_match(
            "mpv_retail",
            r"MPV销量(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%[；;]累计销量(?P<ytd>[0-9.]+)万辆，同比(?P<ytd_dir>增长|下降)(?P<ytd_yoy>[0-9.]+)%",
        )
        add_from_match(
            "suv_retail",
            r"SUV销量(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%[；;]累计销量(?P<ytd>[0-9.]+)万辆，同比(?P<ytd_dir>增长|下降)(?P<ytd_yoy>[0-9.]+)%",
        )
        add_from_match(
            "nev_narrow_passenger_retail",
            r"新能源狭义乘用车销量(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%[；;]累计销量(?P<ytd>[0-9.]+)万辆，同比(?P<ytd_dir>增长|下降)(?P<ytd_yoy>[0-9.]+)%",
        )
        add_from_match(
            "nev_passenger_wholesale_estimate",
            r"新能源乘用车厂商批发销量预估达到(?P<value>[0-9.]+)万辆，同比(?P<yoy_dir>增长|下降)(?P<yoy>[0-9.]+)%，环比(?P<mom_dir>增长|下降)(?P<mom>[0-9.]+)%",
        )
        penetration = re.search(r"新能源渗透率达(?P<value>[0-9.]+)%", text)
        if penetration:
            records.append(
                _metric_record(
                    source="CPCA",
                    article_type=article_type,
                    path=path,
                    title=title,
                    year=year,
                    month=month,
                    metric_name="nev_retail_penetration",
                    value_10k=float(penetration.group("value")),
                    notes="Percentual, nao veiculos em 10 mil unidades.",
                    unit="percent",
                )
            )

    if not records:
        return pd.DataFrame()
    return pd.DataFrame.from_records(records).drop_duplicates(
        subset=["source", "article_type", "ano_mes", "metric_name", "source_file"]
    )


def build_cpca_outputs(metrics: pd.DataFrame) -> dict[str, pd.DataFrame]:
    if metrics.empty:
        return {
            "raw_cpca_article_metrics": metrics,
            "gold_cpca_passenger_market_monthly": metrics,
        }

    latest_by_metric = metrics.sort_values("source_file").drop_duplicates(
        ["ano", "mes", "ano_mes", "metric_name"], keep="last"
    )
    monthly = latest_by_metric.pivot_table(
        index=["ano", "mes", "ano_mes"],
        columns="metric_name",
        values="value_vehicles",
        aggfunc="first",
    ).reset_index()
    monthly.columns.name = None

    pct = latest_by_metric[latest_by_metric["metric_name"].eq("nev_retail_penetration")][
        ["ano", "mes", "ano_mes", "value_10k_vehicles"]
    ].rename(columns={"value_10k_vehicles": "nev_retail_penetration_pct"})
    if not pct.empty and "nev_retail_penetration" in monthly.columns:
        monthly = monthly.drop(columns=["nev_retail_penetration"])
    if not pct.empty:
        monthly = monthly.merge(pct, on=["ano", "mes", "ano_mes"], how="left")

    return {
        "raw_cpca_article_metrics": metrics.sort_values(["ano_mes", "metric_name"]),
        "gold_cpca_article_metrics": metrics.sort_values(["ano_mes", "metric_name"]),
        "gold_cpca_passenger_market_monthly": monthly.sort_values("ano_mes"),
    }


def extract_caam_evidence_catalog() -> pd.DataFrame:
    records: list[dict[str, object]] = []
    base_dir = RAW_DIR / "caam" / "articles"
    if not base_dir.exists():
        return pd.DataFrame()
    for path in sorted(base_dir.glob("*/*.html")):
        text = _clean_html_text(path)
        title_match = re.search(r"正文\s+([^发布时间]+)\s+发布时间", text)
        title = title_match.group(1).strip() if title_match else _extract_title(text)
        date_match = re.search(r"发布时间：\s*(20\d{2}-\d{2}-\d{2})", text)
        images = list(path.parent.glob(f"{path.stem}_*"))
        records.append(
            {
                "source": "CAAM",
                "article_type": path.parent.name,
                "title": title,
                "published_date": date_match.group(1) if date_match else None,
                "source_file": str(path),
                "image_count": len(images),
                "evidence_role": "structured_pending_ocr",
                "extracted_at": datetime.now().isoformat(timespec="seconds"),
            }
        )
    return pd.DataFrame.from_records(records)


def _norm_text(value: object) -> str:
    text = "" if value is None else str(value)
    text = " ".join(text.replace("\xa0", " ").split())
    return text.strip()


def _norm_key(value: object) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", _norm_text(value).upper()).strip()


def _is_indented(value: object) -> bool:
    text = "" if value is None else str(value)
    text = text.replace("\xa0", " ")
    return bool(text.strip()) and text != text.lstrip(" ")


def load_brand_classification() -> list[dict[str, object]]:
    path = OPS_DIR / "metadata" / "brand_classification.yml"
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    return config["brands"]


def _load_chinese_brand_aliases() -> dict[str, str]:
    """Mapa alias normalizado -> nome canonico das marcas no recorte chines."""
    aliases: dict[str, str] = {}
    for item in load_brand_classification():
        if not item.get("include_in_chinese_cars_scope"):
            continue
        for alias in item.get("aliases", [item["brand"]]):
            aliases[_norm_key(alias)] = item["brand"]
    return aliases


# O grupo "Caminhoes" aparece duas vezes nas planilhas: aberto por subcategoria
# (Semileves/Leves/...) e consolidado em "Caminhoes - Total por empresa".
# Para somas usamos apenas a versao consolidada.
ANFAVEA_DUPLICATED_TRUCK_GROUP = "Caminhões"
ANFAVEA_GROUP_CANONICAL = {
    "Caminhões - Total por empresa": "Caminhões",
    "Ônibus (chassi)": "Ônibus",
}


def _canonical_vehicle_groups(df: pd.DataFrame) -> pd.DataFrame:
    df = df[df["vehicle_group"] != ANFAVEA_DUPLICATED_TRUCK_GROUP].copy()
    df["vehicle_group"] = df["vehicle_group"].replace(ANFAVEA_GROUP_CANONICAL)
    return df


def _parse_anfavea_company_sheet(
    sheet, *, year: int, path: Path, sheet_name: str
) -> list[dict[str, object]]:
    """Parseia planilhas de emplacamento por empresa (workbook anual e arquivos
    por marca), preservando hierarquia: grupo > secao > empresa > marca."""
    parsed_rows: list[dict[str, object]] = []
    current_group: str | None = None
    current_section: str | None = None
    current_sub_group: str | None = None

    for row_number, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        raw_company = row[3] if len(row) > 3 else None
        group = _norm_text(row[1] if len(row) > 1 else None)
        section_label = _norm_text(row[2] if len(row) > 2 else None)
        company = _norm_text(raw_company)

        values: list[tuple[int, int]] = []
        for idx, month_name in enumerate(MONTHS, start=4):
            value = row[idx] if len(row) > idx else None
            if value is None:
                continue
            try:
                values.append((int(MONTHS[month_name]), int(value)))
            except (TypeError, ValueError):
                continue

        def add_row(label: str, level: str) -> None:
            parsed_rows.append(
                {
                    "vehicle_group": current_group,
                    "sub_group": current_sub_group,
                    "section": current_section,
                    "row_level": level,
                    "company_or_brand": label,
                    "source_row": row_number,
                    "values": values,
                }
            )

        if group == "Total":
            current_group = "Total"
            current_section = None
            current_sub_group = None
            add_row("Total", "total")
            continue
        if group:
            current_group = group
            current_section = None
            current_sub_group = None
            continue
        if section_label:
            section_key = _norm_key(section_label)
            if section_key.startswith("EMPRESAS ASSOCIADAS"):
                current_section = "associadas"
                add_row(section_label, "section")
            elif section_key.startswith("OUTRAS EMPRESAS"):
                current_section = "outras"
                add_row(section_label, "section")
            elif section_key != "UNIDADES":
                # Subcategorias de caminhoes (Semileves, Leves, Medios, ...).
                current_sub_group = section_label
                current_section = None
            continue
        if company:
            add_row(company, "brand" if _is_indented(raw_company) else "company")

    # Uma empresa e "folha" quando nao possui marcas filhas logo abaixo dela.
    for index, parsed in enumerate(parsed_rows):
        if parsed["row_level"] == "company":
            nxt = parsed_rows[index + 1] if index + 1 < len(parsed_rows) else None
            parsed["is_leaf"] = not (nxt and nxt["row_level"] == "brand")
        else:
            parsed["is_leaf"] = parsed["row_level"] == "brand"

    records: list[dict[str, object]] = []
    extracted_at = datetime.now().isoformat(timespec="seconds")
    for parsed in parsed_rows:
        for mes, registrations in parsed["values"]:
            records.append(
                {
                    "ano": year,
                    "mes": mes,
                    "ano_mes": f"{year}-{mes:02d}",
                    "vehicle_group": parsed["vehicle_group"],
                    "sub_group": parsed["sub_group"],
                    "section": parsed["section"],
                    "row_level": parsed["row_level"],
                    "is_leaf": parsed["is_leaf"],
                    "company_or_brand": parsed["company_or_brand"],
                    "company_or_brand_norm": _norm_key(parsed["company_or_brand"]),
                    "emplacamentos": registrations,
                    "source_file": str(path),
                    "source_sheet": sheet_name,
                    "source_row": parsed["source_row"],
                    "extracted_at": extracted_at,
                }
            )
    return records


def _has_company_sheet(path: Path) -> bool:
    workbook = load_workbook(path, read_only=True, data_only=True)
    try:
        return any("empresa" in name.lower() for name in workbook.sheetnames)
    finally:
        workbook.close()


def _iter_anfavea_workbooks() -> Iterable[Path]:
    """Um workbook de emplacamento por empresa por ano. Re-downloads da ANFAVEA
    podem gerar o mesmo dado sob nomes diferentes; mantemos apenas o arquivo
    mais recente por ano para evitar dupla contagem."""
    for year in range(2021, 2027):
        candidates = [
            path
            for path in sorted((RAW_DIR / "anfavea" / str(year)).glob("*autove*culos*.xlsx"))
            if "por_empresa_e_marca" not in path.name.lower() and _has_company_sheet(path)
        ]
        if candidates:
            yield max(candidates, key=lambda p: p.stat().st_mtime)


def extract_anfavea_company_monthly() -> pd.DataFrame:
    records: list[dict[str, object]] = []

    for path in _iter_anfavea_workbooks():
        year_match = re.search(r"(20\d{2})", path.name)
        if not year_match:
            continue
        year = int(year_match.group(1))

        workbook = load_workbook(path, read_only=True, data_only=True)
        sheet_name = next((s for s in workbook.sheetnames if "empresa" in s.lower()), None)
        if sheet_name is None:
            continue
        records.extend(
            _parse_anfavea_company_sheet(
                workbook[sheet_name], year=year, path=path, sheet_name=sheet_name
            )
        )

    return pd.DataFrame.from_records(records)


def extract_anfavea_origin_brand_monthly() -> pd.DataFrame:
    """Extrai os arquivos de emplacamento de importados/nacionais por empresa e
    marca, unica fonte ANFAVEA com detalhe por marca das "Outras empresas"
    (BYD, GWM, Omoda, ...). Meses sem divulgacao aparecem zerados na planilha e
    sao removidos pelo filtro Total > 0 por arquivo."""
    frames: list[pd.DataFrame] = []

    for year in range(2021, 2027):
        for path in sorted(
            (RAW_DIR / "anfavea" / str(year)).glob("*por_empresa_e_marca*.xlsx")
        ):
            origem = "importados" if "importados" in path.name.lower() else "nacionais"
            workbook = load_workbook(path, read_only=True, data_only=True)
            sheet_name = next(
                (s for s in workbook.sheetnames if s.upper() in {"IMPORTADOS", "NACIONAIS"}),
                workbook.sheetnames[0],
            )
            records = _parse_anfavea_company_sheet(
                workbook[sheet_name], year=year, path=path, sheet_name=sheet_name
            )
            if not records:
                continue
            df = pd.DataFrame.from_records(records)
            totals = df[df["row_level"] == "total"]
            valid_periods = set(totals.loc[totals["emplacamentos"].gt(0), "ano_mes"])
            df = df[df["ano_mes"].isin(valid_periods)].copy()
            df.insert(3, "origem", origem)
            frames.append(df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def build_anfavea_outputs(
    company_monthly: pd.DataFrame, origin_monthly: pd.DataFrame
) -> dict[str, pd.DataFrame]:
    aliases = _load_chinese_brand_aliases()
    df = company_monthly.copy()

    totals = df[df["row_level"] == "total"].copy()
    valid_periods = set(totals.loc[totals["emplacamentos"].gt(0), "ano_mes"])
    if valid_periods:
        df = df[df["ano_mes"].isin(valid_periods)].copy()

    df["marca_chinesa"] = df["company_or_brand_norm"].map(aliases)
    df["is_chinese_scope"] = df["marca_chinesa"].notna()

    # Marcas chinesas identificaveis no workbook anual (empresas associadas):
    # apenas linhas-folha para nao somar empresa-mae e marca-filha em dobro.
    leaves = _canonical_vehicle_groups(
        df[df["row_level"].isin(["company", "brand"]) & df["is_leaf"]]
    )
    associadas = leaves[leaves["marca_chinesa"].notna()].copy()
    by_brand_associadas = (
        associadas.groupby(
            ["ano", "mes", "ano_mes", "vehicle_group", "marca_chinesa"], as_index=False
        )["emplacamentos"]
        .sum()
        .rename(columns={"marca_chinesa": "company_or_brand"})
        .assign(fonte="workbook_anual_associadas")
    )

    # Marcas chinesas dentro de "Outras empresas", disponiveis apenas nos
    # arquivos por marca (importados/nacionais). Secao "associadas" e ignorada
    # aqui porque ja esta coberta pelo workbook anual.
    if not origin_monthly.empty:
        origin = origin_monthly.copy()
        origin["marca_chinesa"] = origin["company_or_brand_norm"].map(aliases)
        outras_detalhe = _canonical_vehicle_groups(
            origin[
                origin["row_level"].isin(["company", "brand"])
                & origin["is_leaf"]
                & origin["section"].eq("outras")
                & origin["marca_chinesa"].notna()
            ]
        )
    else:
        outras_detalhe = pd.DataFrame(
            columns=["ano", "mes", "ano_mes", "vehicle_group", "marca_chinesa", "emplacamentos"]
        )

    by_brand_outras = (
        outras_detalhe.groupby(
            ["ano", "mes", "ano_mes", "vehicle_group", "marca_chinesa"], as_index=False
        )["emplacamentos"]
        .sum()
        .rename(columns={"marca_chinesa": "company_or_brand"})
        .assign(fonte="arquivos_por_marca_outras_empresas")
    )

    by_brand = (
        pd.concat([by_brand_associadas, by_brand_outras], ignore_index=True)
        .sort_values(["ano_mes", "vehicle_group", "company_or_brand"])
        .reset_index(drop=True)
    )

    # Serie mensal: piso = marcas chinesas identificadas; teto = piso + linha
    # agregada "Outras empresas" nos meses sem detalhe por marca (a linha
    # agregada inclui marcas nao chinesas como Kia, Porsche e Volvo).
    total = (
        totals[totals["emplacamentos"].gt(0)]
        .groupby(["ano", "mes", "ano_mes"], as_index=False)["emplacamentos"]
        .sum()
        .rename(columns={"emplacamentos": "emplacamentos_total_anfavea"})
    )
    monthly = total.copy()

    assoc_monthly = (
        associadas.groupby(["ano_mes"], as_index=False)["emplacamentos"]
        .sum()
        .rename(columns={"emplacamentos": "emplacamentos_chinesas_associadas"})
    )
    outras_aggregate = (
        _canonical_vehicle_groups(df[df["row_level"].eq("section") & df["section"].eq("outras")])
        .groupby(["ano_mes"], as_index=False)["emplacamentos"]
        .sum()
        .rename(columns={"emplacamentos": "emplacamentos_outras_empresas_total"})
    )
    outras_detalhe_monthly = (
        outras_detalhe.groupby(["ano_mes"], as_index=False)["emplacamentos"]
        .sum()
        .rename(columns={"emplacamentos": "emplacamentos_chinesas_outras_detalhe"})
    )

    monthly = (
        monthly.merge(assoc_monthly, on="ano_mes", how="left")
        .merge(outras_aggregate, on="ano_mes", how="left")
        .merge(outras_detalhe_monthly, on="ano_mes", how="left")
    )
    for col in (
        "emplacamentos_chinesas_associadas",
        "emplacamentos_outras_empresas_total",
    ):
        monthly[col] = monthly[col].fillna(0).astype(int)

    has_detail = monthly["emplacamentos_chinesas_outras_detalhe"].notna()
    monthly["metodo_outras"] = has_detail.map(
        {True: "detalhe_por_marca", False: "proxy_outras_empresas"}
    )
    monthly["emplacamentos_chinesas_min"] = (
        monthly["emplacamentos_chinesas_associadas"]
        + monthly["emplacamentos_chinesas_outras_detalhe"].fillna(0)
    ).astype(int)
    monthly["emplacamentos"] = (
        monthly["emplacamentos_chinesas_associadas"]
        + monthly["emplacamentos_chinesas_outras_detalhe"].where(
            has_detail, monthly["emplacamentos_outras_empresas_total"]
        )
    ).astype(int)
    monthly["participacao_total_anfavea"] = (
        monthly["emplacamentos"] / monthly["emplacamentos_total_anfavea"]
    )
    monthly["participacao_min"] = (
        monthly["emplacamentos_chinesas_min"] / monthly["emplacamentos_total_anfavea"]
    )
    monthly = monthly.sort_values("ano_mes").reset_index(drop=True)

    return {
        "raw_anfavea_company_monthly": df,
        "raw_anfavea_origin_brand_monthly": origin_monthly,
        "gold_anfavea_chinese_registrations_by_brand_monthly": by_brand,
        "gold_anfavea_chinese_registrations_monthly": monthly,
    }


def _matching_ncm_prefix(code: str) -> str | None:
    for prefix in sorted(COMEX_NCM_PREFIXES, key=len, reverse=True):
        if code.startswith(prefix):
            return prefix
    return None


def _read_ncm_descriptions() -> dict[str, str]:
    path = RAW_DIR / "comex_stat" / "auxiliary" / "NCM.csv"
    if not path.exists():
        return {}

    descriptions: dict[str, str] = {}
    with path.open("r", encoding="latin1", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        for row in reader:
            code = row.get("CO_NCM")
            description = row.get("NO_NCM_POR")
            if code and description:
                descriptions[code] = description
    return descriptions


def extract_comex_monthly(flow: str = "IMP") -> pd.DataFrame:
    records: list[pd.DataFrame] = []
    usecols = ["CO_ANO", "CO_MES", "CO_NCM", "CO_UNID", "CO_PAIS", "QT_ESTAT", "KG_LIQUIDO", "VL_FOB"]
    source_dir = RAW_DIR / "comex_stat" / flow.lower()
    descriptions = _read_ncm_descriptions()

    for year in range(2021, 2027):
        path = source_dir / f"{flow}_{year}.csv"
        if not path.exists():
            continue
        for chunk in pd.read_csv(
            path,
            sep=";",
            quotechar='"',
            dtype=str,
            usecols=usecols,
            chunksize=500_000,
        ):
            chunk = chunk[chunk["CO_PAIS"].eq(COMEX_CHINA_CODE)].copy()
            if chunk.empty:
                continue

            chunk["codigo_ncm"] = chunk["CO_NCM"].str.zfill(8)
            chunk["ncm_prefixo_consulta"] = chunk["codigo_ncm"].map(_matching_ncm_prefix)
            chunk = chunk[chunk["ncm_prefixo_consulta"].notna()].copy()
            if chunk.empty:
                continue

            if year == 2026:
                chunk = chunk[chunk["CO_MES"].astype(int).le(6)].copy()

            for col in ("QT_ESTAT", "KG_LIQUIDO", "VL_FOB"):
                chunk[col] = pd.to_numeric(chunk[col], errors="coerce").fillna(0)
            chunk["ano"] = chunk["CO_ANO"].astype(int)
            chunk["mes"] = chunk["CO_MES"].astype(int)
            chunk["ano_mes"] = chunk["ano"].astype(str) + "-" + chunk["CO_MES"].str.zfill(2)
            chunk["fluxo"] = "importacao" if flow == "IMP" else "exportacao"
            chunk["pais"] = "China"
            chunk["descricao_ncm"] = chunk["codigo_ncm"].map(descriptions)
            chunk["source_file"] = str(path)
            records.append(
                chunk[
                    [
                        "ano",
                        "mes",
                        "ano_mes",
                        "fluxo",
                        "pais",
                        "ncm_prefixo_consulta",
                        "codigo_ncm",
                        "descricao_ncm",
                        "CO_UNID",
                        "QT_ESTAT",
                        "KG_LIQUIDO",
                        "VL_FOB",
                        "source_file",
                    ]
                ]
            )

    if not records:
        return pd.DataFrame()

    detail = pd.concat(records, ignore_index=True)
    detail = detail.rename(
        columns={
            "CO_UNID": "codigo_unidade_estatistica",
            "QT_ESTAT": "quantidade_estatistica",
            "KG_LIQUIDO": "kg_liquido",
            "VL_FOB": "valor_fob_usd",
        }
    )
    # Quantidade em veiculos: apenas NCMs de veiculos completos e medidos em
    # numero de unidades. Evita somar kg (8708) com unidades na mesma metrica.
    is_vehicle = detail["ncm_prefixo_consulta"].isin(COMEX_VEHICLE_PREFIXES) & detail[
        "codigo_unidade_estatistica"
    ].eq(COMEX_UNIT_NUMBER_OF_ITEMS)
    detail["quantidade_veiculos"] = detail["quantidade_estatistica"].where(is_vehicle, 0.0)
    detail["extracted_at"] = datetime.now().isoformat(timespec="seconds")
    return detail


COMEX_MEASURES = ["quantidade_veiculos", "quantidade_estatistica", "kg_liquido", "valor_fob_usd"]


def build_comex_outputs(detail: pd.DataFrame) -> dict[str, pd.DataFrame]:
    by_ncm = (
        detail.groupby(
            ["ano", "mes", "ano_mes", "fluxo", "pais", "ncm_prefixo_consulta", "codigo_ncm", "descricao_ncm"],
            dropna=False,
            as_index=False,
        )[COMEX_MEASURES]
        .sum()
        .sort_values(["ano_mes", "ncm_prefixo_consulta", "codigo_ncm"])
    )
    monthly = (
        detail.groupby(["ano", "mes", "ano_mes", "fluxo", "pais"], as_index=False)[
            COMEX_MEASURES
        ]
        .sum()
        .sort_values("ano_mes")
    )
    by_prefix = (
        detail.groupby(
            ["ano", "mes", "ano_mes", "fluxo", "pais", "ncm_prefixo_consulta"],
            as_index=False,
        )[COMEX_MEASURES]
        .sum()
        .sort_values(["ano_mes", "ncm_prefixo_consulta"])
    )
    return {
        "raw_comex_china_automotive_detail": detail,
        "gold_comex_china_automotive_monthly": monthly,
        "gold_comex_china_automotive_by_ncm_monthly": by_ncm,
        "gold_comex_china_automotive_by_prefix_monthly": by_prefix,
    }


def write_duckdb(tables: dict[str, pd.DataFrame]) -> None:
    db_path = database_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(str(db_path)) as con:
        for name, df in tables.items():
            con.execute(f"drop table if exists {name}")
            con.register("_df", df)
            con.execute(f"create table {name} as select * from _df")
            con.unregister("_df")


def build_all_tables() -> dict[str, pd.DataFrame]:
    anfavea_company = extract_anfavea_company_monthly()
    anfavea_origin = extract_anfavea_origin_brand_monthly()
    tables = build_anfavea_outputs(anfavea_company, anfavea_origin)

    comex_imp = extract_comex_monthly("IMP")
    tables.update(build_comex_outputs(comex_imp))

    cpca_metrics = extract_cpca_article_metrics()
    tables.update(build_cpca_outputs(cpca_metrics))

    caam_catalog = extract_caam_evidence_catalog()
    tables["raw_caam_evidence_catalog"] = caam_catalog
    tables["gold_caam_evidence_catalog"] = caam_catalog
    return tables
