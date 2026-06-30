"""party V2 命令组。"""
from __future__ import annotations

import json
import typer
from typing import Optional
from cli.session import get_client
from cli.output import print_result

app = typer.Typer(help="注册主体（Party）管理 - V2")


@app.command("list")
def party_list(
    keyword: Optional[str] = typer.Option(None, "-k", "--keyword", help="关键字搜索"),
    type: Optional[int] = typer.Option(None, "--type", help="主体类型：1=供应商 2=客户"),
    page: int = typer.Option(1, help="页码"),
    page_size: int = typer.Option(20, "--page-size"),
    output: str = typer.Option("table", "-o"),
):
    """查询注册主体列表。"""
    payload = {"pageNum": page, "pageSize": page_size}
    if keyword:
        payload["keyword"] = keyword
    if type is not None:
        payload["type"] = type
    status, body = get_client().post("/api/party/page", json=payload)
    print_result(status, body, output, rows_key="rows",
                 columns=["id", "name", "organizationNo", "country", "type", "status"])


@app.command("get")
def party_get(
    id: int = typer.Argument(..., help="主体 ID"),
    output: str = typer.Option("json", "-o"),
):
    """查询注册主体详情。"""
    status, body = get_client().get(f"/api/party/{id}")
    print_result(status, body, output)


@app.command("upsert")
def party_upsert(
    file: Optional[str] = typer.Option(None, "-f", "--file", help="JSON 文件路径"),
    data: Optional[str] = typer.Option(None, "-d", "--data", help="内联 JSON 字符串"),
    output: str = typer.Option("json", "-o"),
):
    """创建或更新注册主体（传入 JSON）。

    示例：
      elc party upsert -f party.json
      elc party upsert -d '{"type":1,"name":"ACME","country":"DE",...}'
    """
    if file:
        with open(file) as f:
            payload = json.load(f)
    elif data:
        payload = json.loads(data)
    else:
        typer.echo("需要 --file 或 --data 参数", err=True)
        raise typer.Exit(1)
    status, body = get_client().post("/v2/parties/create-or-update", json=payload)
    print_result(status, body, output)


@app.command("delete")
def party_delete(
    id: int = typer.Argument(..., help="主体 ID"),
):
    """删除注册主体。"""
    status, body = get_client().delete(f"/api/party/{id}")
    print_result(status, body, "json")
