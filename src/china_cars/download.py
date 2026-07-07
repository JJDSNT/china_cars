from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import requests
import yaml
from urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

from china_cars.paths import RAW_DIR


ANFAVEA_EXCEL_PAGE = "https://anfavea.com.br/site/edicoes-em-excel/"
COMEX_BASE_URL = "https://balanca.economia.gov.br/balanca/bd/comexstat-bd/ncm"
COMEX_TABLES_URL = "https://balanca.economia.gov.br/balanca/bd/tabelas"
YEARS = range(2021, 2027)
COMEX_FLOWS = ("IMP", "EXP")
COMEX_AUX_FILES = ("PAIS.csv", "NCM.csv", "NCM_SH.csv")


@dataclass(frozen=True)
class DownloadedFile:
    source: str
    url: str
    path: Path
    status: str


def _session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "ChinaCarsDataProject/0.1"
            )
        }
    )
    return session


def _download(
    url: str,
    path: Path,
    session: requests.Session,
    *,
    verify_tls: bool = True,
) -> DownloadedFile:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0:
        return DownloadedFile(source="existing", url=url, path=path, status="skipped")

    with session.get(url, timeout=120, stream=True, verify=verify_tls) as response:
        if response.status_code == 404:
            return DownloadedFile(source="missing", url=url, path=path, status="not_found")
        response.raise_for_status()
        with path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)

    return DownloadedFile(source="downloaded", url=url, path=path, status="ok")


def _slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "arquivo"


def _extract_anfavea_links(html: str) -> list[tuple[str, str]]:
    links = re.findall(
        r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    relevant: list[tuple[str, str]] = []
    for href, text in links:
        label = " ".join(re.sub(r"<.*?>", " ", text).split())
        href_lower = href.lower()
        label_lower = label.lower()
        is_excel = any(ext in href_lower for ext in (".xlsx", ".xls", ".xlsm"))
        is_relevant = any(
            token in label_lower
            for token in (
                "autove",
                "emplacamento",
                "licenciamento",
                "séries mensais",
                "series mensais",
            )
        )
        if is_excel and is_relevant:
            relevant.append((urljoin(ANFAVEA_EXCEL_PAGE, href), label))
    return relevant


def download_anfavea() -> list[DownloadedFile]:
    session = _session()
    html = session.get(ANFAVEA_EXCEL_PAGE, timeout=60).text
    links = _extract_anfavea_links(html)

    downloaded: list[DownloadedFile] = []
    for url, label in links:
        year_match = re.search(r"(20\d{2})", url + " " + label)
        year = year_match.group(1) if year_match else "unknown_year"
        suffix = Path(url.split("?")[0]).suffix or ".xlsx"
        filename = f"{year}_{_slug(label)[:100]}{suffix}"
        path = RAW_DIR / "anfavea" / year / filename
        downloaded.append(_download(url, path, session))

    manifest = [
        {"url": item.url, "path": str(item.path), "status": item.status}
        for item in downloaded
    ]
    manifest_path = RAW_DIR / "anfavea" / "manifest.yml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "source_page": ANFAVEA_EXCEL_PAGE,
                "downloaded_at": datetime.now().isoformat(timespec="seconds"),
                "files": manifest,
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return downloaded


def download_comex() -> list[DownloadedFile]:
    session = _session()
    downloaded: list[DownloadedFile] = []
    base_dir = RAW_DIR / "comex_stat"

    for flow in COMEX_FLOWS:
        for year in YEARS:
            url = f"{COMEX_BASE_URL}/{flow}_{year}.csv"
            path = base_dir / flow.lower() / f"{flow}_{year}.csv"
            downloaded.append(_download(url, path, session, verify_tls=False))

    for filename in COMEX_AUX_FILES:
        url = f"{COMEX_TABLES_URL}/{filename}"
        path = base_dir / "auxiliary" / filename
        try:
            downloaded.append(_download(url, path, session, verify_tls=False))
        except requests.HTTPError:
            continue

    manifest_path = base_dir / "manifest.yml"
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "base_url": COMEX_BASE_URL,
                "downloaded_at": datetime.now().isoformat(timespec="seconds"),
                "files": [
                    {"url": item.url, "path": str(item.path), "status": item.status}
                    for item in downloaded
                ],
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return downloaded


def read_comex_country_codes(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="latin1", newline="") as file:
        return list(csv.DictReader(file, delimiter=";"))


def download_all() -> list[DownloadedFile]:
    return [*download_anfavea(), *download_comex()]
