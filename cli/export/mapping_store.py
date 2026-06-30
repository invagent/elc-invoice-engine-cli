"""映射表本地持久化：读写 ~/.elc/mappings/<template_md5>.json。"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path

MAPPINGS_DIR = Path.home() / ".elc" / "mappings"


def _md5(template_path: str) -> str:
    return hashlib.md5(Path(template_path).read_bytes()).hexdigest()


def load_mapping(template_path: str) -> dict | None:
    """读取缓存映射表；模版内容变了（MD5 不同）返回 None。"""
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    key = _md5(template_path)
    path = MAPPINGS_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def save_mapping(template_path: str, mapping: dict) -> None:
    """保存映射表，附带元信息。"""
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    key = _md5(template_path)
    payload = {
        "template_path": str(Path(template_path).resolve()),
        "template_md5":  key,
        "created_at":    datetime.now().isoformat(timespec="seconds"),
        **mapping,
    }
    (MAPPINGS_DIR / f"{key}.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2)
    )


def mapping_exists(template_path: str) -> bool:
    key = _md5(template_path)
    return (MAPPINGS_DIR / f"{key}.json").exists()
