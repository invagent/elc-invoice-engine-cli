"""Token 本地持久化：读写 ~/.elc/token.json。"""
from __future__ import annotations

import json
import time
from pathlib import Path

_TOKEN_FILE = Path.home() / ".elc" / "token.json"


def save_token(access_token: str, expires_in: int) -> None:
    _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "access_token": access_token,
        "expires_at": int(time.time()) + expires_in - 60,  # 提前 60s 过期
    }
    _TOKEN_FILE.write_text(json.dumps(payload, indent=2))


def load_token() -> str | None:
    """读取本地 token；过期或不存在返回 None。"""
    if not _TOKEN_FILE.exists():
        return None
    try:
        payload = json.loads(_TOKEN_FILE.read_text())
        if time.time() < payload.get("expires_at", 0):
            return payload["access_token"]
    except Exception:
        pass
    return None


def clear_token() -> None:
    if _TOKEN_FILE.exists():
        _TOKEN_FILE.unlink()
