"""tax-category 命令组。"""
from __future__ import annotations

import json
import typer
from typing import Optional
from cli.session import get_client
from cli.output import print_result

app = typer.Typer(help="税目管理")


@app.command("list")
def tax_list(
    country: Optional[str] = typer.Option(None, "--country", help="国家代码，如 MY"),
    keyword: Optional[str] = typer.Option(None, "-k", "--keyword"),
    page: int = typer.Option(1),
    page_size: int = typer.Option(20, "--page-size"),
    output: str = typer.Option("table", "-o"),
):
    """查询税目列表。"""
    payload = {"pageNum": page, "pageSize": page_size}
    if country:
        payload["country"] = country
    if keyword:
        payload["keyword"] = keyword
    status, body = get_client().post("/api/taxCategory/page", json=payload)
    print_result(status, body, output, rows_key="rows",
                 columns=["id", "code", "name", "country", "taxType", "schemeId"])


@app.command("get")
def tax_get(
    id: int = typer.Argument(...),
    output: str = typer.Option("json", "-o"),
):
    """查询税目详情。"""
    status, body = get_client().get(f"/api/taxCategory/{id}")
    print_result(status, body, output)


@app.command("create")
def tax_create(
    file: Optional[str] = typer.Option(None, "-f", "--file"),
    data: Optional[str] = typer.Option(None, "-d", "--data"),
    output: str = typer.Option("json", "-o"),
):
    """新增税目（传入 JSON）。"""
    if file:
        with open(file) as f:
            payload = json.load(f)
    elif data:
        payload = json.loads(data)
    else:
        typer.echo("需要 --file 或 --data 参数", err=True)
        raise typer.Exit(1)
    status, body = get_client().post("/api/taxCategory", json=payload)
    print_result(status, body, output)


@app.command("delete")
def tax_delete(
    id: int = typer.Argument(...),
):
    """删除税目。"""
    status, body = get_client().delete(f"/api/taxCategory/{id}")
    print_result(status, body, "json")
