"""describe 命令：输出当前 CLI 环境上下文，供 AI 使用。"""
from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich.console import Console

from cli.config import BASE_URL, SSO_CONFIG, DEFAULT_HEADERS
from cli.token_store import load_token
from cli.export.mapping_store import MAPPINGS_DIR

app = typer.Typer(help="输出 CLI 环境上下文（供 AI 使用）")
console = Console()


@app.callback(invoke_without_command=True)
def describe(
    ctx: typer.Context,
    output: str = typer.Option("json", "-o", help="输出格式：json / text"),
):
    """输出当前 CLI 环境、命令说明、接口行为和已知问题，供 AI 建立上下文。

    在开始任何 ELC CLI 操作前，先运行此命令让 AI 了解当前环境。
    """
    if ctx.invoked_subcommand is not None:
        return

    token = load_token()
    logged_in = token is not None

    # 已缓存的映射表
    mappings = []
    if MAPPINGS_DIR.exists():
        for f in MAPPINGS_DIR.glob("*.json"):
            try:
                m = json.loads(f.read_text())
                mappings.append({
                    "template": m.get("template_path", ""),
                    "created_at": m.get("created_at", ""),
                    "header_fields": len(m.get("header_mapping", {})),
                    "line_fields": len(m.get("line_mapping", {})),
                })
            except Exception:
                pass

    ctx_data = {
        "env": {
            "base_url":   BASE_URL,
            "company_id": DEFAULT_HEADERS.get("X-Company-ID", ""),
            "domain":     SSO_CONFIG.get("domain", ""),
            "logged_in":  logged_in,
            "token_file": str(Path.home() / ".elc" / "token.json"),
        },
        "cached_mappings": mappings,
        "commands": {
            "elc login":                     "交互式登录，token 保存到 ~/.elc/token.json",
            "elc login status":              "查看登录状态",
            "elc login logout":              "退出登录",
            "elc invoice-request list":      "查询开票申请单列表，支持 --status / --source-system / --month 过滤",
            "elc invoice-request get <id>":  "查询单条申请单详情（注意：/v2 单条接口有时返回 500，用 list 替代）",
            "elc invoice-request create -f <xml>": "创建申请单，上传 KDUBL XML，自动生成幂等键",
            "elc invoice-request update <id> -f <xml>": "更新申请单（状态需为 draft/validate_failed/pending）",
            "elc invoice-request void <id>": "作废申请单",
            "elc invoice-request issue <id>":"触发开票（状态需为 PENDING_INVOICE）",
            "elc invoice-request invoices <id>": "查询申请单下的发票列表",
            "elc invoice-request match-cn-create -f <xml>": "创建 Credit Note 蓝冲匹配任务",
            "elc invoice-request match-cn-run <id>": "触发蓝冲匹配",
            "elc invoice-request match-cn-results <id>": "查询匹配结果",
            "elc invoice-request match-cn-unlink <id>": "解除匹配绑定",
            "elc invoice get <id>":          "查询发票详情",
            "elc invoice file-link <id>":    "获取发票文件下载链接（--type Humanreadable/Target/Source）",
            "elc invoice download <id>":     "直接下载发票文件到本地（--type Source 下载 KDUBL XML）",
            "elc invoice cancel <id>":       "取消发票（仅 MY，72小时内）",
            "elc party list":                "查询注册主体列表",
            "elc party upsert -f <json>":    "创建或更新注册主体",
            "elc product list":              "查询商品列表",
            "elc product upsert -f <json>":  "创建或更新商品",
            "elc tax list":                  "查询税目列表",
            "elc exchange list":             "查询汇率列表",
            "elc exchange create":           "新增汇率",
            "elc export init -t <tmpl>":     "采集模版列名和样本数据，供 AI 推断字段映射",
            "elc export save-mapping -t <tmpl> -f <json>": "保存 AI 推断的字段映射到本地缓存",
            "elc export invoice -t <tmpl>":  "导出发票数据到 Excel（需先 init + save-mapping）",
            "elc describe":                  "输出本上下文（当前命令）",
        },
        "api_behaviors": {
            "pagination": {
                "type":        "cursor",
                "param":       "cursor（整数，初始不传，后续传 nextCursor 的值）",
                "page_size":   "pageSize（服务端固定每页20条，设置其他值无效）",
                "has_more":    "hasMore: true 时继续翻页，false 时停止",
                "example":     "第一页不传 cursor，返回 nextCursor=20，第二页传 cursor=20",
            },
            "time_filter": {
                "params":  "updatedFrom / updatedTo（格式 YYYY-MM-DD）",
                "note":    "按申请单 updatedTime 过滤，不是 createdTime",
            },
            "invoice_status": {
                "INVOICED_SUCCESS": "开票成功，有关联 invoices[]",
                "VALIDATION_FAILED": "校验失败，查看 failureDetails",
                "PENDING_INVOICE":  "待开票，可调用 issue 触发",
                "DRAFT":            "草稿，可更新",
            },
            "source_xml": {
                "available":   "仅通过 /v2/invoice-requests（上传 KDUBL XML）创建的发票才有 Source 文件",
                "endpoint":    "GET /v1/invoices/file/{invoiceId}?filetype=Source&fileFormat=xml",
                "error_403004":"No file found — 该发票不是通过 XML 上传创建的，无 Source 文件",
            },
        },
        "known_issues": {
            "header_case":    "X-Company-ID（大写 ID），不是 X-Company-Id",
            "get_single_ir":  "GET /v2/invoice-requests/{id} 有时返回 500，改用 list + sourceId 过滤",
            "issue_500":      "issue 命令返回 500 时，检查申请单状态是否为 PENDING_INVOICE",
            "xml_missing":    "SIT 环境大部分测试数据无 Source XML（通过 JSON 方式创建），正式数据通过 XML 上传则有",
            "max_batches":    "export invoice 默认 --max-batches 500（每批20条），数据量大时适当调小",
            "token_expiry":   "token 有效期约 7.5 小时，过期后自动重新登录",
        },
        "export_workflow": {
            "step1": "elc export init -t <template> -o /tmp/sample.json",
            "step2": "读取 /tmp/sample.json，AI 推断字段映射，生成 mapping JSON",
            "step3": "elc export save-mapping -t <template> -f /tmp/mapping.json",
            "step4": "elc export invoice -t <template> --month YYYY-MM --company BU-XXXXX --out <dir>",
            "note":  "同一模版只需初始化一次，模版文件内容变更后需重新 init",
        },
    }

    if output == "json":
        console.print_json(json.dumps(ctx_data, ensure_ascii=False, indent=2))
    else:
        console.print(f"[bold cyan]ELC CLI 环境上下文[/bold cyan]")
        console.print(f"BASE_URL:    {ctx_data['env']['base_url']}")
        console.print(f"Company:     {ctx_data['env']['company_id']}")
        console.print(f"Logged in:   {'✓' if logged_in else '✗ 请先运行 elc login'}")
        console.print(f"\n[bold]已缓存映射表：[/bold] {len(mappings)} 个")
        console.print(f"\n运行 elc describe -o json 获取完整上下文")
