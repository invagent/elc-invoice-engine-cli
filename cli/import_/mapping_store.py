"""Import 映射表本地持久化：读写 ~/.elc/import-mappings/<template_md5>.json。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

IMPORT_MAPPINGS_DIR = Path.home() / ".elc" / "import-mappings"


def _md5(template_path: str) -> str:
    return hashlib.md5(Path(template_path).read_bytes()).hexdigest()


def load_mapping(template_path: str) -> dict | None:
    IMPORT_MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    key = _md5(template_path)
    path = IMPORT_MAPPINGS_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def save_mapping(template_path: str, mapping: dict) -> None:
    IMPORT_MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    key = _md5(template_path)
    payload = {
        "template_path": str(Path(template_path).resolve()),
        "template_md5":  key,
        "created_at":    datetime.now().isoformat(timespec="seconds"),
        **mapping,
    }
    (IMPORT_MAPPINGS_DIR / f"{key}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )


def mapping_exists(template_path: str) -> bool:
    key = _md5(template_path)
    return (IMPORT_MAPPINGS_DIR / f"{key}.json").exists()
