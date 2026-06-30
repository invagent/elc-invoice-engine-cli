"""invoice (发票) 命令组 — 区别于 invoice-request。"""
from __future__ import annotations

import httpx
import typer
from pathlib import Path
from typing import Optional
from cli.config import BASE_URL, REQUEST_TIMEOUT
from cli.session import get_client
from cli.output import print_result, console

app = typer.Typer(help="发票管理 (V2)")


@app.command("get")
def invoice_get(
    invoice_id: str = typer.Argument(..., help="发票 ID"),
    output: str = typer.Option("json", "-o"),
):
    """查询发票详情。

    GET /v2/invoices/{invoiceId}
    """
    status, body = get_client().get(f"/v2/invoices/{invoice_id}")
    print_result(status, body, output)


@app.command("file-link")
def invoice_file_link(
    invoice_id: str = typer.Argument(..., help="发票 ID"),
    file_type: str = typer.Option("Humanreadable", "--type",
                                   help="Humanreadable(PDF) / Target(电子发票) / Source(KDUBL)"),
    file_format: str = typer.Option("xml", "--format", help="xml / json"),
    link_type: str = typer.Option("EXTERNAL", "--link-type", help="EXTERNAL / INTERNAL"),
    expiry_days: int = typer.Option(7, "--expiry-days"),
    output: str = typer.Option("json", "-o"),
):
    """获取发票文件下载链接。

    GET /v2/invoices/file-link/{invoiceId}
    """
    params = {
        "fileType":   file_type,
        "fileFormat": file_format,
        "linkType":   link_type,
        "expiryDays": expiry_days,
    }
    status, body = get_client().get(f"/v2/invoices/file-link/{invoice_id}", params=params)
    print_result(status, body, output)


@app.command("cancel")
def invoice_cancel(
    invoice_id: str = typer.Argument(..., help="发票 ID"),
    reason: str = typer.Option(..., "--reason", help="取消原因（MY 发票必填，72小时内）"),
    output: str = typer.Option("json", "-o"),
):
    """取消发票（仅支持马来西亚 MY，72小时内）。

    POST /v1/invoice/{invoiceId}/cancel
    """
    status, body = get_client().post(f"/v1/invoice/{invoice_id}/cancel", json={"reason": reason})
    print_result(status, body, output)


@app.command("download")
def invoice_download(
    invoice_id: str = typer.Argument(..., help="发票 ID"),
    file_type: str = typer.Option("Source", "--type",
                                   help="Humanreadable(PDF) / Target(电子发票) / Source(KDUBL XML)"),
    file_format: str = typer.Option("xml", "--format", help="xml / json"),
    out: str = typer.Option(".", "--out", "-o", help="保存目录，默认当前目录"),
    filename: Optional[str] = typer.Option(None, "--name", "-n", help="文件名，默认用 invoiceId"),
):
    """直接下载发票文件到本地。

    使用内部接口 /v1/invoices/file/{invoiceId} 下载原始文件。
    """
    client = get_client()
    token = client.headers.get("Authorization", "").removeprefix("Bearer ")
    company = client.headers.get("X-Company-ID", "") or client.headers.get("X-Company-Id", "")

    headers = {"Authorization": f"Bearer {token}", "X-Company-Id": company}
    params = {"filetype": file_type, "fileFormat": file_format}

    resp = httpx.get(
        f"{BASE_URL}/v1/invoices/file/{invoice_id}",
        headers=headers,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )

    ct = resp.headers.get("content-type", "")
    if resp.status_code != 200 or ("xml" not in ct and not resp.content.strip().startswith(b"<")):
        console.print(f"[red]下载失败（HTTP {resp.status_code}）：{resp.content[:200]}[/red]")
        raise typer.Exit(1)

    ext = ".pdf" if file_type == "Humanreadable" else f".{file_format}"
    name = filename or f"{invoice_id}{ext}"
    out_path = Path(out).expanduser() / name
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(resp.content)

    console.print(f"[green]✓ 已下载：{out_path}（{len(resp.content)} 字节）[/green]")
