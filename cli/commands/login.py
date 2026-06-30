"""login / logout 命令。"""
from __future__ import annotations

import os
import typer
from rich.console import Console
from cli.token_store import save_token, clear_token, load_token
from cli.auth import fetch_token
from cli.session import reset_client

app = typer.Typer(help="登录与认证管理", invoke_without_command=True)
console = Console()


@app.callback(invoke_without_command=True)
def login(
    ctx: typer.Context,
    domain: str = typer.Option(None, "--domain", help="租户域名，如 kingdee-fpy"),
    app_id: str = typer.Option(None, "--app-id", help="应用 ID"),
    secret: str = typer.Option(None, "--secret", help="应用密钥"),
    mobile: str = typer.Option(None, "--mobile", help="手机号"),
    org_num: str = typer.Option(None, "--org-num", help="组织编号"),
    base_url: str = typer.Option(None, "--url", help="服务地址，如 http://host:port/xm-demo"),
):
    """登录并保存凭证到 ~/.elc/token.json。

    凭证可通过选项传入，也可以交互式输入。已有 .env.local 配置的字段可直接回车跳过。
    """
    if ctx.invoked_subcommand is not None:
        return

    import cli.config as cfg

    console.print("[bold cyan]ELC Invoice Engine CLI — 登录[/bold cyan]")
    console.print("已有 .env.local 配置的字段可直接回车跳过\n")

    # 覆盖配置（命令行优先，其次交互，再次 .env.local）
    def _ask(label: str, current: str, opt_val: str | None, secret_input: bool = False) -> str:
        if opt_val:
            return opt_val
        display = f"[dim]{current}[/dim]" if current else "[dim](未配置)[/dim]"
        prompt = f"{label} {display}"
        val = typer.prompt(prompt, default="", hide_input=secret_input, show_default=False)
        return val.strip() or current

    if base_url:
        os.environ["BASE_URL"] = base_url
        cfg.BASE_URL = base_url.rstrip("/")

    cfg.SSO_CONFIG["domain"]      = _ask("租户域名    (domain)   ", cfg.SSO_CONFIG["domain"], domain)
    cfg.SSO_CONFIG["app_id"]      = _ask("应用 ID     (appId)    ", cfg.SSO_CONFIG["app_id"], app_id)
    cfg.SSO_CONFIG["secret"]      = _ask("应用密钥    (secret)   ", cfg.SSO_CONFIG["secret"], secret, secret_input=True)
    cfg.SSO_CONFIG["mobile"]      = _ask("手机号      (mobile)   ", cfg.SSO_CONFIG["mobile"], mobile)
    cfg.SSO_CONFIG["org_num"]     = _ask("组织编号    (orgNum)   ", cfg.SSO_CONFIG["org_num"], org_num)

    console.print("\n正在登录...")
    try:
        token, expires_in = fetch_token()
        save_token(token, expires_in)
        reset_client()
        console.print(f"[green]✓ 登录成功[/green]，token 已保存至 ~/.elc/token.json（有效期 {expires_in // 3600}h）")
    except Exception as e:
        console.print(f"[red]✗ 登录失败：{e}[/red]")
        raise typer.Exit(1)


@app.command("logout")
def logout():
    """清除本地保存的 token。"""
    clear_token()
    reset_client()
    console.print("[green]✓ 已退出登录[/green]")


@app.command("status")
def status():
    """查看当前登录状态。"""
    token = load_token()
    if token:
        console.print(f"[green]✓ 已登录[/green]，token 前缀：{token[:20]}...")
    else:
        console.print("[yellow]未登录或 token 已过期[/yellow]，请运行 elc login")
