"""invoice-request V2 命令组。

接口基路径：/v2/invoice-requests
"""
from __future__ import annotations

import json
import uuid
import typer
from typing import Optional
from cli.session import get_client
from cli.output import print_result, console

app = typer.Typer(help="开票申请单管理 (V2)")

# ── 公共 header 选项 ─────────────────────────────────────────────────────────

def _idempotency_key() -> str:
    return str(uuid.uuid4())


# ── 命令 ─────────────────────────────────────────────────────────────────────

@app.command("list")
def invoice_list(
    source_system: Optional[str] = typer.Option(None, "--source-system"),
    source_id: Optional[str] = typer.Option(None, "--source-id"),
    status: Optional[str] = typer.Option(None, "--status"),
    page: int = typer.Option(1),
    page_size: int = typer.Option(20, "--page-size"),
    output: str = typer.Option("table", "-o"),
):
    """查询开票申请单列表。

    GET /v2/invoice-requests
    """
    params: dict = {"pageNum": page, "pageSize": page_size}
    if source_system:
        params["sourceSystem"] = source_system
    if source_id:
        params["sourceId"] = source_id
    if status:
        params["status"] = status
    status_code, body = get_client().get("/v2/invoice-requests", params=params)
    # V2 响应：data.invoiceRequests 列表
    data = body.get("data") or {}
    if isinstance(data, dict):
        rows = data.get("invoiceRequests", [])
        body = {"data": rows}
    print_result(status_code, body, output, rows_key="data",
                 columns=["invoiceRequestId", "sourceSystem", "sourceId", "invoiceRequestStatus", "createdTime"])


@app.command("get")
def invoice_get(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("json", "-o"),
):
    """查询申请单详情。

    GET /v2/invoice-requests/{invoiceRequestId}
    """
    status, body = get_client().get(f"/v2/invoice-requests/{invoice_request_id}")
    print_result(status, body, output)


@app.command("create")
def invoice_create(
    file: str = typer.Option(..., "-f", "--file", help="KDUBL XML 文件路径"),
    source_system: str = typer.Option("CLI", "--source-system"),
    source_id: Optional[str] = typer.Option(None, "--source-id"),
    batch_id: Optional[str] = typer.Option(None, "--batch-id", help="批次 ID（UUID），同批次多单共用"),
    idempotency_key: Optional[str] = typer.Option(None, "--idempotency-key", help="幂等键，默认自动生成"),
    timezone: str = typer.Option("UTC+00:00", "--timezone"),
    output: str = typer.Option("json", "-o"),
):
    """创建开票申请单（上传 KDUBL XML）。

    POST /v2/invoice-requests  (multipart/form-data)
    """
    import httpx
    from cli.config import BASE_URL, REQUEST_TIMEOUT

    source_id = source_id or f"CLI-{uuid.uuid4().hex[:8].upper()}"
    ikey = idempotency_key or _idempotency_key()

    client = get_client()
    headers = {k: v for k, v in client.headers.items() if k.lower() != "content-type"}
    headers.update({
        "X-Request-Id":      uuid.uuid4().hex,
        "X-Idempotency-Key": ikey,
        "X-Timezone":        timezone,
    })

    form_data: dict = {"sourceSystem": source_system, "sourceId": source_id}
    if batch_id:
        form_data["batchId"] = batch_id

    with open(file, "rb") as f:
        files = {"payload": (file.split("/")[-1], f, "application/xml")}
        resp = httpx.post(
            f"{BASE_URL}/v2/invoice-requests",
            headers=headers,
            files=files,
            data=form_data,
            timeout=REQUEST_TIMEOUT,
        )

    body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"raw": resp.text}
    console.print(f"[dim]幂等键：{ikey}[/dim]")
    print_result(resp.status_code, body, output)


@app.command("update")
def invoice_update(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    file: str = typer.Option(..., "-f", "--file", help="KDUBL XML 文件路径"),
    idempotency_key: Optional[str] = typer.Option(None, "--idempotency-key"),
    timezone: str = typer.Option("UTC+00:00", "--timezone"),
    output: str = typer.Option("json", "-o"),
):
    """更新开票申请单（状态为 draft/validate_failed/pending 时可更新）。

    PUT /v2/invoice-requests/{invoiceRequestId}  (multipart/form-data)
    """
    import httpx
    from cli.config import BASE_URL, REQUEST_TIMEOUT

    ikey = idempotency_key or _idempotency_key()
    client = get_client()
    headers = {k: v for k, v in client.headers.items() if k.lower() != "content-type"}
    headers.update({
        "X-Request-Id":      uuid.uuid4().hex,
        "X-Idempotency-Key": ikey,
        "X-Timezone":        timezone,
    })

    with open(file, "rb") as f:
        files = {"payload": (file.split("/")[-1], f, "application/xml")}
        resp = httpx.put(
            f"{BASE_URL}/v2/invoice-requests/{invoice_request_id}",
            headers=headers,
            files=files,
            timeout=REQUEST_TIMEOUT,
        )

    body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"raw": resp.text}
    print_result(resp.status_code, body, output)


@app.command("void")
def invoice_void(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("json", "-o"),
):
    """作废开票申请单（设置状态为 void）。

    POST /v2/invoice-requests/{invoiceRequestId}/void
    """
    client = get_client()
    status, body = client.post(f"/v2/invoice-requests/{invoice_request_id}/void")
    print_result(status, body, output)


@app.command("issue")
def invoice_issue(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("json", "-o"),
):
    """触发开票（Issue Invoice）。

    POST /v2/invoice-requests/{invoiceRequestId}/issue
    """
    client = get_client()
    status, body = client.post(f"/v2/invoice-requests/{invoice_request_id}/issue")
    print_result(status, body, output)


@app.command("invoices")
def invoice_get_invoices(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("table", "-o"),
):
    """查询申请单下的发票列表。

    GET /v2/invoice-requests/{invoiceRequestId}/invoices
    """
    status, body = get_client().get(f"/v2/invoice-requests/{invoice_request_id}/invoices")
    print_result(status, body, output, rows_key="data",
                 columns=["invoiceId", "invoiceNo", "invoiceStatus", "issueStatus", "totalAmount"])


# ── Credit Note 匹配 ──────────────────────────────────────────────────────────

@app.command("match-cn-create")
def match_cn_create(
    file: str = typer.Option(..., "-f", "--file", help="Credit Note KDUBL XML 文件路径"),
    idempotency_key: Optional[str] = typer.Option(None, "--idempotency-key"),
    output: str = typer.Option("json", "-o"),
):
    """创建 Credit Note 蓝冲匹配任务。

    POST /v2/invoice-requests/match-cn  (multipart/form-data)
    """
    import httpx
    from cli.config import BASE_URL, REQUEST_TIMEOUT

    ikey = idempotency_key or _idempotency_key()
    client = get_client()
    headers = {k: v for k, v in client.headers.items() if k.lower() != "content-type"}
    headers.update({"X-Request-Id": uuid.uuid4().hex, "X-Idempotency-Key": ikey})

    with open(file, "rb") as f:
        resp = httpx.post(
            f"{BASE_URL}/v2/invoice-requests/match-cn",
            headers=headers,
            files={"payload": (file.split("/")[-1], f, "application/xml")},
            timeout=REQUEST_TIMEOUT,
        )

    body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"raw": resp.text}
    console.print(f"[dim]幂等键：{ikey}[/dim]")
    print_result(resp.status_code, body, output)


@app.command("match-cn-run")
def match_cn_run(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    reason_code: str = typer.Option("OTHER", "--reason", help="RETURN / ALLOWANCE / OTHER"),
    output: str = typer.Option("json", "-o"),
):
    """触发 Credit Note 蓝冲匹配任务。

    POST /v2/invoice-requests/match-cn/{invoiceRequestId}/run
    """
    status, body = get_client().post(
        f"/v2/invoice-requests/match-cn/{invoice_request_id}/run",
        json={"reasonCode": reason_code},
    )
    print_result(status, body, output)


@app.command("match-cn-results")
def match_cn_results(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("json", "-o"),
):
    """查询 Credit Note 蓝冲匹配结果。

    GET /v2/invoice-requests/{invoiceRequestId}/matchResults
    """
    status, body = get_client().get(f"/v2/invoice-requests/{invoice_request_id}/matchResults")
    print_result(status, body, output)


@app.command("match-cn-unlink")
def match_cn_unlink(
    invoice_request_id: str = typer.Argument(..., help="申请单 ID"),
    output: str = typer.Option("json", "-o"),
):
    """解除 Credit Note 蓝冲匹配绑定。

    POST /v2/invoice-requests/match-cn/{invoiceRequestId}/unlink
    """
    status, body = get_client().post(
        f"/v2/invoice-requests/match-cn/{invoice_request_id}/unlink"
    )
    print_result(status, body, output)
