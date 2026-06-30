"""exchange-rates 命令组。"""
from __future__ import annotations

import typer
from typing import Optional
from cli.session import get_client
from cli.output import print_result

app = typer.Typer(help="汇率管理")


@app.command("list")
def exchange_list(
    currency_from: Optional[str] = typer.Option(None, "--from", help="源货币代码"),
    currency_to: Optional[str] = typer.Option(None, "--to", help="目标货币代码"),
    page: int = typer.Option(1, help="页码"),
    page_size: int = typer.Option(20, "--page-size", help="每页条数"),
    output: str = typer.Option("table", "-o", help="输出格式：table / json"),
):
    """查询汇率列表。"""
    params = {"pageNum": page, "pageSize": page_size}
    if currency_from:
        params["currencyFrom"] = currency_from
    if currency_to:
        params["currencyTo"] = currency_to
    status, body = get_client().get("/api/exchange-rates/list", params=params)
    print_result(status, body, output, rows_key="rows",
                 columns=["id", "currencyFrom", "currencyTo", "exchangeRate", "rateDate", "status"])


@app.command("latest")
def exchange_latest(
    currency_from: str = typer.Argument(..., help="源货币代码，如 USD"),
    currency_to: str = typer.Argument(..., help="目标货币代码，如 CNY"),
    output: str = typer.Option("table", "-o", help="输出格式：table / json"),
):
    """查询最新汇率。"""
    status, body = get_client().get(
        "/api/exchange-rates/latest",
        params={"currencyFrom": currency_from, "currencyTo": currency_to},
    )
    print_result(status, body, output)


@app.command("create")
def exchange_create(
    currency_from: str = typer.Option(..., "--from", help="源货币代码"),
    currency_to: str = typer.Option(..., "--to", help="目标货币代码"),
    rate: float = typer.Option(..., "--rate", help="汇率"),
    rate_date: str = typer.Option(..., "--date", help="生效日期，格式 YYYY-MM-DD"),
    output: str = typer.Option("json", "-o", help="输出格式：table / json"),
):
    """新增汇率记录。"""
    payload = {
        "currencyFrom": currency_from,
        "currencyTo": currency_to,
        "exchangeRate": rate,
        "rateDate": rate_date,
        "baseAmount": 1,
        "rateSource": "MANUAL",
        "status": 1,
    }
    status, body = get_client().post("/api/exchange-rates", json=payload)
    print_result(status, body, output)


@app.command("delete")
def exchange_delete(
    id: int = typer.Argument(..., help="汇率记录 ID"),
):
    """删除汇率记录。"""
    status, body = get_client().delete(f"/api/exchange-rates/{id}")
    print_result(status, body, "json")


@app.command("currencies")
def exchange_currencies(
    output: str = typer.Option("table", "-o", help="输出格式：table / json"),
):
    """查询支持的货币代码列表。"""
    status, body = get_client().get("/api/exchange-rates/currencies")
    print_result(status, body, output)
