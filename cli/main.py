"""CLI 主入口。"""
from __future__ import annotations

import typer
from cli.commands import describe, exchange, export, invoice, invoice_doc, login, party, product, tax

app = typer.Typer(
    name="elc",
    help="ELC Invoice Engine CLI — V2 接口命令行工具",
    no_args_is_help=True,
)

# 认证
app.add_typer(login.app,        name="login")

# 上下文（AI 使用）
app.add_typer(describe.app,     name="describe")

# 核心业务
app.add_typer(invoice.app,      name="invoice-request")
app.add_typer(invoice_doc.app,  name="invoice")
app.add_typer(party.app,        name="party")
app.add_typer(product.app,      name="product")
app.add_typer(tax.app,          name="tax")
app.add_typer(exchange.app,     name="exchange")
app.add_typer(export.app,       name="export")

if __name__ == "__main__":
    app()
