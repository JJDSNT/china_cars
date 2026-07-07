from __future__ import annotations

import csv
import html
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
CPCA_BASE_URL = "https://www.cpcaauto.com/"
CPCA_CATEGORIES = {
    "monthly_ranking": "news.php?types=csjd&anid=129&nid=27&page={page}",
    "monthly_analysis": "news.php?types=csjd&anid=129&nid=24&page={page}",
    "nev_wholesale_flash": "news.php?types=csjd&anid=129&nid=37&page={page}",
}
CAAM_BASE_URL = "http://www.caam.org.cn/"
CAAM_CATEGORIES = {
    "production_sales": "chn/4/cate_30/list_{page}.html",
    "import_export": "chn/4/cate_34/list_{page}.html",
}


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
                "(KHTML, like Gecko) Chrome/126 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
    )
    return session


def _download(
    url: str,
    path: Path,
    session: requests.Session,
    *,
    verify_tls: bool = True,
    refresh: bool = False,
) -> DownloadedFile:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size > 0 and not refresh:
        return DownloadedFile(source="existing", url=url, path=path, status="skipped")

    temp_path = path.with_suffix(path.suffix + ".part")
    try:
        with session.get(url, timeout=120, stream=True, verify=verify_tls) as response:
            if response.status_code == 404:
                return DownloadedFile(source="missing", url=url, path=path, status="not_found")
            response.raise_for_status()
            with temp_path.open("wb") as file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        file.write(chunk)
        temp_path.replace(path)
    except requests.RequestException:
        temp_path.unlink(missing_ok=True)
        if path.exists() and path.stat().st_size > 0:
            return DownloadedFile(source="existing", url=url, path=path, status="kept_stale")
        return DownloadedFile(source="error", url=url, path=path, status="error")

    return DownloadedFile(source="downloaded", url=url, path=path, status="ok")


def _slug(value: str) -> str:
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_") or "arquivo"


def _extract_anfavea_links(page_html: str) -> list[tuple[str, str]]:
    links = re.findall(
        r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        page_html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    relevant: list[tuple[str, str]] = []
    for href, text in links:
        label = " ".join(re.sub(r"<.*?>", " ", html.unescape(text)).split())
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

    current_year = str(datetime.now().year)
    downloaded: list[DownloadedFile] = []
    for url, label in links:
        year_match = re.search(r"(20\d{2})", url + " " + label)
        year = year_match.group(1) if year_match else "unknown_year"
        suffix = Path(url.split("?")[0]).suffix or ".xlsx"
        filename = f"{year}_{_slug(label)[:100]}{suffix}"
        path = RAW_DIR / "anfavea" / year / filename
        # Arquivos do ano corrente sao atualizados mensalmente na mesma URL.
        refresh = year in {current_year, "unknown_year"}
        downloaded.append(_download(url, path, session, refresh=refresh))

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

    current_year = datetime.now().year
    for flow in COMEX_FLOWS:
        for year in YEARS:
            url = f"{COMEX_BASE_URL}/{flow}_{year}.csv"
            path = base_dir / flow.lower() / f"{flow}_{year}.csv"
            # O CSV do ano corrente cresce a cada divulgacao mensal do MDIC.
            downloaded.append(
                _download(url, path, session, verify_tls=False, refresh=year == current_year)
            )

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


def _extract_links(html: str) -> list[tuple[str, str]]:
    links = re.findall(
        r"<a[^>]+href=[\"']([^\"']+)[\"'][^>]*>(.*?)</a>",
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    results: list[tuple[str, str]] = []
    for href, text in links:
        label = " ".join(re.sub(r"<.*?>", " ", text).split())
        if label:
            results.append((href, label))
    return results


def download_cpca(max_pages: int = 6) -> list[DownloadedFile]:
    session = _session()
    session.headers.update({"Referer": CPCA_BASE_URL})
    downloaded: list[DownloadedFile] = []
    article_links: dict[str, tuple[str, str]] = {}

    for category, template in CPCA_CATEGORIES.items():
        for page in range(1, max_pages + 1):
            url = urljoin(CPCA_BASE_URL, template.format(page=page))
            path = RAW_DIR / "cpca" / "lists" / category / f"page_{page}.html"
            item = _download(url, path, session)
            downloaded.append(item)

            html = path.read_text(encoding="utf-8", errors="ignore")
            for href, label in _extract_links(html):
                if "newslist.php" not in href:
                    continue
                if not any(token in label for token in ("月度", "新能源", "销量", "市场")):
                    continue
                article_url = urljoin(CPCA_BASE_URL, href)
                article_id = re.search(r"id=(\d+)", article_url)
                filename = f"{article_id.group(1) if article_id else _slug(label)}.html"
                article_links[article_url] = (category, filename)

    for article_url, (category, filename) in sorted(article_links.items()):
        path = RAW_DIR / "cpca" / "articles" / category / filename
        downloaded.append(_download(article_url, path, session))

    manifest_path = RAW_DIR / "cpca" / "manifest.yml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "base_url": CPCA_BASE_URL,
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


def download_caam(max_pages: int = 2) -> list[DownloadedFile]:
    session = _session()
    downloaded: list[DownloadedFile] = []
    article_links: dict[str, tuple[str, str]] = {}

    for category, template in CAAM_CATEGORIES.items():
        for page in range(1, max_pages + 1):
            url = urljoin(CAAM_BASE_URL, template.format(page=page))
            path = RAW_DIR / "caam" / "lists" / category / f"page_{page}.html"
            item = _download(url, path, session, verify_tls=False)
            downloaded.append(item)

            html = path.read_text(encoding="utf-8", errors="ignore")
            for href, label in _extract_links(html):
                if "con_" not in href:
                    continue
                if not any(token in label for token in ("产销", "出口", "汽车工业", "新能源汽车")):
                    continue
                article_url = urljoin(url, href)
                article_id = re.search(r"con_(\d+)", article_url)
                filename = f"{article_id.group(1) if article_id else _slug(label)}.html"
                article_links[article_url] = (category, filename)

    for article_url, (category, filename) in sorted(article_links.items()):
        path = RAW_DIR / "caam" / "articles" / category / filename
        item = _download(article_url, path, session, verify_tls=False)
        downloaded.append(item)

        if path.exists():
            html = path.read_text(encoding="utf-8", errors="ignore")
            for image_url in re.findall(r"<img[^>]+src=[\"']([^\"']+)[\"']", html, flags=re.I):
                if "file.caam.org.cn" not in image_url:
                    continue
                image_url = urljoin(article_url, image_url)
                image_name = Path(image_url.split("?")[0]).name
                image_path = path.parent / f"{path.stem}_{image_name}"
                downloaded.append(_download(image_url, image_path, session, verify_tls=False))

    manifest_path = RAW_DIR / "caam" / "manifest.yml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        yaml.safe_dump(
            {
                "base_url": CAAM_BASE_URL,
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
    return [*download_anfavea(), *download_comex(), *download_cpca(), *download_caam()]
