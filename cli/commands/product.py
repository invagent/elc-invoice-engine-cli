"""product V2 命令组。"""
from __future__ import annotations

import json
import typer
from typing import Optional
from cli.session import get_client
from cli.output import print_result

app = typer.Typer(help="商品/物料管理 - V2")


@app.command("list")
def product_list(
    keyword: Optional[str] = typer.Option(None, "-k", "--keyword"),
    category: Optional[str] = typer.Option(None, "--category", help="GOODS / SERVICE"),
    page: int = typer.Option(1),
    page_size: int = typer.Option(20, "--page-size"),
    output: str = typer.Option("table", "-o"),
):
    """查询商品列表。"""
    payload: dict = {"pageNum": page, "pageSize": page_size}
    if keyword:
        payload["keyword"] = keyword
    if category:
        payload["categoryType"] = category
    status, body = get_client().post("/api/product/page", json=payload)
    print_result(status, body, output, rows_key="rows",
                 columns=["id", "productCode", "productName", "uomCode", "categoryType", "status"])


@app.command("get")
def product_get(
    id: int = typer.Argument(...),
    output: str = typer.Option("json", "-o"),
):
    """查询商品详情。"""
    status, body = get_client().get(f"/api/product/{id}")
    print_result(status, body, output)


@app.command("upsert")
def product_upsert(
    file: Optional[str] = typer.Option(None, "-f", "--file"),
    data: Optional[str] = typer.Option(None, "-d", "--data"),
    output: str = typer.Option("json", "-o"),
):
    """创建或更新商品（传入 JSON）。"""
    if file:
        with open(file) as f:
            payload = json.load(f)
    elif data:
        payload = json.loads(data)
    else:
        typer.echo("需要 --file 或 --data 参数", err=True)
        raise typer.Exit(1)
    status, body = get_client().post("/v2/products/create-or-update", json=payload)
    print_result(status, body, output)


@app.command("delete")
def product_delete(
    id: int = typer.Argument(...),
):
    """删除商品。"""
    status, body = get_client().delete(f"/api/product/{id}")
    print_result(status, body, "json")
