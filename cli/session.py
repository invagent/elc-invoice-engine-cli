"""懒加载 ApiClient：优先读取本地缓存 token，过期才重新登录。"""
from __future__ import annotations

import typer
from rich.console import Console
from cli.token_store import load_token, save_token
from cli.auth import fetch_token
from cli.client import ApiClient

_console = Console()
_client: ApiClient | None = None


def get_client() -> ApiClient:
    global _client
    if _client is not None:
        return _client

    # 优先读本地缓存
    token = load_token()
    if not token:
        try:
            token, expires_in = fetch_token()
            save_token(token, expires_in)
        except Exception as e:
            _console.print(f"[red]认证失败：{e}[/red]")
            _console.print("[yellow]提示：请先运行 elc login 配置凭证[/yellow]")
            raise typer.Exit(1)

    _client = ApiClient(token=token)
    return _client


def reset_client() -> None:
    global _client
    _client = None
