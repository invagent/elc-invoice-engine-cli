# elc-invoice-engine-cli

ELC Invoice Engine V2 接口命令行工具。基于 Python + Typer 构建，支持开票申请单、发票、交易方、商品、税目、汇率等全套 V2 接口操作。

## 前置要求

- Python 3.9+（推荐通过 [Homebrew](https://brew.sh) 安装：`brew install python@3.10`）
- 可访问的 ELC Invoice Engine V2 服务

---

## 安装

### 方式一：从 PyPI 安装（推荐）

```bash
pip install elc-invoice-engine-cli
elc --help
```

### 方式二：从源码安装（开发用）

```bash
# 1. 进入项目目录
cd elc-invoice-engine-cli

# 2. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. 安装（可编辑模式，`elc` 命令立即可用）
pip install -e .
```

---

## 配置与登录

### 方式一：交互式登录（推荐）

```bash
elc login
```

按提示依次输入以下字段，已在 `.env.local` 中配置的字段可直接回车跳过：

| 字段 | 说明 |
|------|------|
| 服务地址 (url) | 如 `http://api-sit.piaozone.com/xm-demo`，对应 `BASE_URL` |
| 租户域名 (domain) | 如 `kingdee-fpy` |
| 应用 ID (appId) | SSO 应用 ID |
| 应用密钥 (secret) | SSO 密钥（输入时不回显） |
| 手机号 (mobile) | 登录手机号 |
| 组织编号 (orgNum) | 如 `HXB-10151` |

Token 保存到 `~/.elc/token.json`，有效期内无需重复登录。

也可以通过选项直接传入，跳过交互：

```bash
elc login \
  --url     http://api-sit.piaozone.com/xm-demo \
  --domain  kingdee-fpy \
  --app-id  your_app_id \
  --secret  your_secret \
  --mobile  138xxxx \
  --org-num HXB-10151
```

### 方式二：.env.local 文件（适合 CI / 脚本）

```bash
cp .env.example .env.local
# 然后编辑 .env.local 填写以下字段
```

| 字段 | 说明 |
|------|------|
| `BASE_URL` | 服务地址，如 `http://localhost:12007/xm-demo` |
| `SSO_APP_ID` | 应用 ID |
| `SSO_SECRET` | 应用密钥 |
| `SSO_DOMAIN` | 租户域名 |
| `SSO_MOBILE` | 登录手机号 |
| `SSO_ORG_NUM` | 组织编号 |
| `X_COMPANY_ID` | 租户公司 ID（`X-Company-Id` 请求头） |

### 登录状态管理

```bash
elc login status    # 查看当前登录状态
elc login logout    # 退出登录（清除本地 token）
```

---

## 命令参考

### 通用选项

所有查询命令均支持 `-o` 控制输出格式：

| 值 | 说明 |
|----|------|
| `table` | 富文本表格（默认） |
| `json` | 原始 JSON |

---

### `invoice-request` — 开票申请单

```bash
# 查询列表
elc invoice-request list
elc invoice-request list --status PENDING --source-system ERP -o json

# 查询详情
elc invoice-request get <invoiceRequestId>

# 创建（上传 KDUBL XML）
elc invoice-request create -f payload.xml --source-system MY_ERP --source-id BILL-001

# 同批次多单（共用 batch-id）
elc invoice-request create -f payload.xml --batch-id <uuid>

# 更新（状态为 draft / validate_failed / pending 时可更新）
elc invoice-request update <invoiceRequestId> -f updated.xml

# 作废
elc invoice-request void <invoiceRequestId>

# 触发开票
elc invoice-request issue <invoiceRequestId>

# 查询申请单下的发票
elc invoice-request invoices <invoiceRequestId>

# Credit Note 蓝冲匹配
elc invoice-request match-cn-create  -f cn.xml
elc invoice-request match-cn-run     <invoiceRequestId> --reason RETURN
elc invoice-request match-cn-results <invoiceRequestId>
elc invoice-request match-cn-unlink  <invoiceRequestId>
```

---

### `invoice` — 发票

```bash
# 查询详情
elc invoice get <invoiceId>

# 获取文件下载链接
elc invoice file-link <invoiceId> --type Humanreadable   # PDF
elc invoice file-link <invoiceId> --type Target          # 电子发票格式
elc invoice file-link <invoiceId> --type Source          # KDUBL 原文

# 取消发票（仅 MY，72 小时内）
elc invoice cancel <invoiceId> --reason "Customer requested cancellation"
```

---

### `party` — 注册主体

```bash
elc party list --keyword ACME --type 1
elc party get <id>
elc party upsert -f party.json
elc party upsert -d '{"type":1,"name":"ACME","organizationNo":"ORG001","country":"DE","status":1,"identifiers":[...]}'
elc party delete <id>
```

---

### `product` — 商品

```bash
elc product list --category GOODS
elc product get <id>
elc product upsert -f product.json
elc product delete <id>
```

---

### `tax` — 税目

```bash
elc tax list --country MY
elc tax get <id>
elc tax create -f tax.json
elc tax delete <id>
```

---

### `exchange` — 汇率

```bash
elc exchange list --from USD --to CNY
elc exchange latest USD CNY
elc exchange create --from USD --to EUR --rate 0.92 --date 2026-06-30
elc exchange delete <id>
elc exchange currencies
```

---

### `export` — 导出

```bash
elc export invoices --output invoices.xlsx
```

---

### `describe` — AI 上下文描述

```bash
elc describe
```

输出当前可用接口的结构化描述，供 AI 工具（如 Claude、GPT）理解 CLI 能力。

---

## 工程结构

```
elc-invoice-engine-cli/
├── pyproject.toml          # 构建配置 & 依赖，定义 `elc` 入口点
├── requirements.txt        # 锁定依赖版本（与 pyproject.toml 一致）
├── .env.example            # 配置模板，复制为 .env.local 后填写
├── .env.local              # 本地配置（不提交 git）
└── cli/
    ├── main.py             # 入口，注册所有命令组
    ├── auth.py             # SSO MD5 签名登录
    ├── client.py           # httpx 封装
    ├── config.py           # 环境变量读取
    ├── output.py           # rich 表格 / JSON 输出
    ├── session.py          # 懒加载 ApiClient（优先读本地 token）
    ├── token_store.py      # ~/.elc/token.json 读写
    ├── commands/
    │   ├── login.py        # elc login / logout / status
    │   ├── invoice.py      # elc invoice-request ...
    │   ├── invoice_doc.py  # elc invoice ...
    │   ├── party.py        # elc party ...
    │   ├── product.py      # elc product ...
    │   ├── tax.py          # elc tax ...
    │   ├── exchange.py     # elc exchange ...
    │   ├── export.py       # elc export ...
    │   └── describe.py     # elc describe
    └── export/
        ├── mapping_store.py
        ├── xml_parser.py
        └── excel_writer.py
```

---

## 常见问题

**Q: `elc: command not found`（pip install 后命令找不到）**

用系统 pip 安装时脚本会放到用户目录下，但该目录可能不在 PATH 里。

```bash
# 找到 elc 的实际位置
pip3 show elc-invoice-engine-cli | grep Location
# 例如输出：Location: /Users/yourname/Library/Python/3.9/lib/python/site-packages
# 则 elc 在：/Users/yourname/Library/Python/3.9/bin/elc

# 将对应 bin 目录加入 PATH（以 Python 3.9 为例）
echo 'export PATH="$HOME/Library/Python/3.9/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
elc --help
```

**Q: `ERROR: Ignored the following versions that require a different python version`**

系统自带 Python 版本过低（如 macOS 默认的 3.9 以下）。通过 Homebrew 安装新版本：

```bash
brew install python@3.10
# 然后用对应 pip 安装
pip3.10 install elc-invoice-engine-cli
```

**Q: `ProxyError` / 连接超时**

网络走了代理导致 SSL 握手超时，有两个解法：

```bash
# 方案一：临时绕过代理
env -u https_proxy -u http_proxy -u ALL_PROXY pip3 install elc-invoice-engine-cli

# 方案二：使用国内镜像源（注意：镜像同步有延迟，新版本发布后稍等几分钟再试）
pip3 install elc-invoice-engine-cli -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Q: 安装时出现依赖冲突 warning（`dependency conflicts`）**

如果提示 `openapi-python-client`、`spacy`、`streamlit` 等包冲突，这是已安装的其他工具与本包依赖版本不一致，属于 warning 不影响 `elc` 正常使用。推荐在虚拟环境中安装以隔离依赖：

```bash
python3 -m venv ~/.venvs/elc
source ~/.venvs/elc/bin/activate
pip install elc-invoice-engine-cli
elc --help
```

**Q: token 过期 / 401 错误**  
运行 `elc login` 重新登录，或检查 `.env.local` 中的 `SSO_SECRET` 是否正确。

**Q: 如何切换不同环境（dev / staging / prod）**  
修改 `.env.local` 中的 `BASE_URL`，或在登录时通过 `--url` 选项指定。

---

## Claude Code Skills

本项目附带两个 [Claude Code](https://claude.ai/code) Skills，让 Claude 能直接驱动 `elc` 完成复杂操作。

### 可用 Skills

| Skill | 触发命令 | 说明 |
|-------|----------|------|
| `elc-context` | `/elc-context` | 初始化 ELC 环境上下文，其他 Skill 的前置依赖 |
| `invoice-export` | `/invoice-export` | 引导 Claude 自动完成发票导出（采样 → 推断映射 → 导出 Excel） |

### 安装方法

**方式一：curl 下载（无需克隆整个仓库，推荐）**

```bash
# 全局安装（所有项目均可用）
mkdir -p ~/.claude/skills/elc-context ~/.claude/skills/invoice-export

curl -sL https://raw.githubusercontent.com/invagent/elc-invoice-engine-cli/main/skills/elc-context/SKILL.md \
     -o ~/.claude/skills/elc-context/SKILL.md

curl -sL https://raw.githubusercontent.com/invagent/elc-invoice-engine-cli/main/skills/invoice-export/SKILL.md \
     -o ~/.claude/skills/invoice-export/SKILL.md

# 项目级安装（仅当前项目可用，在项目根目录下执行）
mkdir -p .claude/skills/elc-context .claude/skills/invoice-export

curl -sL https://raw.githubusercontent.com/invagent/elc-invoice-engine-cli/main/skills/elc-context/SKILL.md \
     -o .claude/skills/elc-context/SKILL.md

curl -sL https://raw.githubusercontent.com/invagent/elc-invoice-engine-cli/main/skills/invoice-export/SKILL.md \
     -o .claude/skills/invoice-export/SKILL.md
```

**方式二：git clone（适合同时需要源码的场景）**

```bash
git clone https://github.com/invagent/elc-invoice-engine-cli.git

# 全局安装
mkdir -p ~/.claude/skills
cp -r elc-invoice-engine-cli/skills/elc-context     ~/.claude/skills/
cp -r elc-invoice-engine-cli/skills/invoice-export  ~/.claude/skills/

# 或项目级安装（仅当前项目可用）
mkdir -p .claude/skills
cp -r elc-invoice-engine-cli/skills/elc-context     .claude/skills/
cp -r elc-invoice-engine-cli/skills/invoice-export  .claude/skills/
```

### 使用示例

在 Claude Code 中：

```
/invoice-export 导出本月组织 BU-00008 的发票，模版用 ~/Downloads/template.xlsx
```

Claude 会自动执行：初始化映射表 → 推断字段对应关系 → 导出 Excel 并告知文件路径。

---

## 发布到 PyPI

### 前置准备

```bash
pip install build twine
```

注册账号：
- 正式发布：[https://pypi.org/account/register/](https://pypi.org/account/register/)
- 测试发布：[https://test.pypi.org/account/register/](https://test.pypi.org/account/register/)

在 PyPI 账户设置中创建 **API Token**，范围选"Entire account"（首次发布前包还不存在，无法选具体包）。

配置本地凭证（只需做一次）：

```bash
# ~/.pypirc
cat > ~/.pypirc <<'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-xxxxxxxxxxxxxxxx   # 替换为你的 API Token

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-xxxxxxxxxxxxxxxx   # 替换为 Test PyPI 的 API Token
EOF
chmod 600 ~/.pypirc
```

### 发布流程

**1. 更新版本号**

编辑 `pyproject.toml`，修改 `version` 字段，遵循 [语义化版本](https://semver.org/lang/zh-CN/)：

```toml
version = "0.2.0"
```

**2. 构建发行包**

```bash
# 清理旧产物
rm -rf dist/

# 构建 wheel + sdist
python -m build
```

构建完成后 `dist/` 目录下会生成：

```
dist/
├── elc_invoice_engine_cli-0.2.0-py3-none-any.whl
└── elc_invoice_engine_cli-0.2.0.tar.gz
```

**3. 先发到 Test PyPI 验证**

```bash
twine upload --repository testpypi dist/*
```

验证安装：

```bash
pip install --index-url https://test.pypi.org/simple/ elc-invoice-engine-cli
elc --help
```

**4. 发布到正式 PyPI**

```bash
twine upload dist/*
```

发布后用户即可直接安装：

```bash
pip install elc-invoice-engine-cli
elc --help
```

### 版本迭代

每次发布前必须递增 `pyproject.toml` 中的 `version`，PyPI 不允许覆盖已发布的版本号。

推荐在 `git` 中打 tag 与版本对应：

```bash
git tag v0.2.0
git push origin v0.2.0
```
