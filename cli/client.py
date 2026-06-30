"""HTTP 客户端：封装 httpx，统一注入认证头和 requestId。"""
from __future__ import annotations

import uuid
import httpx
from cli.config import BASE_URL, DEFAULT_HEADERS, REQUEST_TIMEOUT


class ApiClient:
    def __init__(self, token: str = ""):
        self.base_url = BASE_URL
        self.headers = dict(DEFAULT_HEADERS)
        if token:
            self.headers["Authorization"] = f"Bearer {token}"
        self._client = httpx.Client(timeout=REQUEST_TIMEOUT)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def _req_headers(self) -> dict:
        return {**self.headers, "X-Request-Id": uuid.uuid4().hex}

    def get(self, path: str, params: dict = None) -> tuple[int, dict]:
        r = self._client.get(self._url(path), headers=self._req_headers(), params=params or {})
        return r.status_code, self._body(r)

    def post(self, path: str, json: dict | list = None, params: dict = None) -> tuple[int, dict]:
        r = self._client.post(self._url(path), headers=self._req_headers(), json=json, params=params or {})
        return r.status_code, self._body(r)

    def put(self, path: str, json: dict | list = None) -> tuple[int, dict]:
        r = self._client.put(self._url(path), headers=self._req_headers(), json=json)
        return r.status_code, self._body(r)

    def delete(self, path: str, params: dict = None) -> tuple[int, dict]:
        r = self._client.delete(self._url(path), headers=self._req_headers(), params=params or {})
        return r.status_code, self._body(r)

    @staticmethod
    def _body(r: httpx.Response) -> dict:
        try:
            return r.json()
        except Exception:
            return {"raw": r.text}

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
