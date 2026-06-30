"""SSO 认证：MD5 签名获取 token。"""
from __future__ import annotations

import hashlib
import time
import httpx
from cli.config import BASE_URL, SSO_CONFIG, REQUEST_TIMEOUT


def _sign(app_id: str, secret: str, timestamp: str) -> str:
    return hashlib.md5(f"{app_id}{secret}{timestamp}".encode()).hexdigest()


def fetch_token() -> tuple[str, int]:
    """调用 /api/sso/kingdee/token，返回 (access_token, expires_in)。"""
    app_id = SSO_CONFIG["app_id"]
    secret = SSO_CONFIG["secret"]
    timestamp = str(int(time.time() * 1000))

    body = {
        "domain":     SSO_CONFIG["domain"],
        "appId":      app_id,
        "timestamp":  timestamp,
        "sign":       _sign(app_id, secret, timestamp),
        "mobile":     SSO_CONFIG["mobile"],
        "userName":   SSO_CONFIG["username"],
        "workNumber": SSO_CONFIG["work_number"],
        "orgNum":     SSO_CONFIG["org_num"],
    }
    body = {k: v for k, v in body.items() if v}

    url = f"{BASE_URL}/api/sso/kingdee/token"
    resp = httpx.post(url, json=body, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    result = resp.json()
    data = result.get("data") or {}
    token = data.get("accessToken")
    expires_in = int(data.get("expiresIn", 7200))

    if not token:
        raise RuntimeError(f"SSO 登录失败：{result}")

    return token, expires_in
