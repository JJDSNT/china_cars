from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    ROOT / "data" / "raw",
    ROOT / "data" / "processed" / "china_cars.duckdb",
    ROOT / "outputs" / "excel" / "china_cars_outputs.xlsx",
]
OUTPUT = ROOT / "ops" / "metadata" / "file_manifest.yml"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(path: Path):
    if path.is_file():
        yield path
    elif path.is_dir():
        for child in sorted(path.rglob("*")):
            if child.is_file() and child.name != ".gitkeep":
                yield child


def main() -> None:
    files = []
    for target in TARGETS:
        for path in iter_files(target):
            files.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )

    OUTPUT.write_text(
        yaml.safe_dump(
            {
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "files": files,
            },
            sort_keys=False,
            allow_unicode=True,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
