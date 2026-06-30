"""输出格式化：table / json / raw。"""
from __future__ import annotations

import json as _json
import typer
from rich.console import Console
from rich.table import Table

console = Console()


def print_json(data: dict | list) -> None:
    console.print_json(_json.dumps(data, ensure_ascii=False, indent=2))


def print_table(rows: list[dict], columns: list[str] | None = None) -> None:
    if not rows:
        typer.echo("(无数据)")
        return
    cols = columns or list(rows[0].keys())
    t = Table(show_header=True, header_style="bold cyan")
    for c in cols:
        t.add_column(c)
    for row in rows:
        t.add_row(*[str(row.get(c, "")) for c in cols])
    console.print(t)


def print_result(status: int, body: dict, output: str = "table",
                 rows_key: str = "data", columns: list[str] | None = None) -> None:
    """统一打印 V2 响应：output 为 'table'、'json' 或 'raw'。"""
    if output == "json":
        print_json(body)
        return
    if status >= 400:
        console.print(f"[red]HTTP {status}[/red]  {body}")
        return
    data = body.get(rows_key, body)
    if output == "table" and isinstance(data, list):
        print_table(data, columns)
    elif output == "table" and isinstance(data, dict):
        print_table([data], columns)
    else:
        console.print(data)
