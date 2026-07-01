---
name: invoice-export
description: 导出发票数据到 Excel。当用户说"导出发票"、"export invoice"、"生成发票Excel"、"导出本月发票数据"等时触发。
---

# Invoice Export Skill

## 前置条件

执行本 Skill 前，先运行 **elc-context** Skill 获取环境上下文（登录状态、company ID、接口行为等）。

## 触发条件

用户输入包含以下关键词时触发：
- 导出发票 / 发票导出 / 发票数据导出
- export invoice / export invoices
- 生成发票 Excel / 发票 Excel 导出
- 导出本月/上月/某月/最近N天/最近N周的发票

## 执行流程

### 第一步：解析用户意图

从用户输入中提取日期语义，统一转化为 `--from YYYY-MM-DD --to YYYY-MM-DD`：

| 用户说 | 转化规则 | 示例（今天 2026-07-01） |
|--------|---------|----------------------|
| "最近N天" / "过去N天" | from = 今天 - N天，to = 今天 | 最近15天 → `--from 2026-06-16 --to 2026-07-01` |
| "最近N周" / "过去N周" | from = 今天 - N*7天，to = 今天 | 最近2周 → `--from 2026-06-17 --to 2026-07-01` |
| "本月" | from = 本月1号，to = 今天 | `--from 2026-07-01 --to 2026-07-01` |
| "上个月" / "上月" | from = 上月1号，to = 上月最后一天 | `--from 2026-06-01 --to 2026-06-30` |
| "YYYY-MM" | from = 该月1号，to = 该月最后一天 | `--from 2026-05-01 --to 2026-05-31` |
| "从X到Y" / "X至Y" | 直接转为日期 | `--from 2026-06-01 --to 2026-06-30` |
| 未指定 | from = 本月1号，to = 今天 | 不传，使用默认值 |

其他参数：

| 参数 | 提取方式 | 默认值 |
|------|----------|--------|
| `company` | 直接识别如 "BU-00008" | 读 `env.company_id`（elc-context 已获取），已配置则无需传 |
| `template` | 用户提到的文件路径 | 自动使用已缓存模版，无需传入 |
| `out` | 用户提到的输出目录 | 默认 ~/Downloads，无需传入 |

如果 `company` 未提供且 `env.company_id` 为空，询问用户：
> 请提供公司 ID（如 BU-00008）

### 第二步：自动登录（如未登录）

elc-context 已处理登录状态。如果登录失败，停止并提示用户手动登录。

### 第三步：检查映射表是否已初始化

```bash
ls ~/.elc/mappings/ 2>/dev/null || echo "空"
```

**情况 A：已初始化** → 直接跳到第四步。

**情况 B：未初始化** → 自动执行初始化，无需询问用户。

#### 3.1 采集样本数据

```bash
elc export init \
  [--template {template}] \
  [--company {company}] \
  --output /tmp/elc_init_sample.json
```

#### 3.2 读取并推断字段映射

读取 `/tmp/elc_init_sample.json`，根据以下规则推断映射：
- `inline_invoice_fields` 列出的字段：使用 `source: json`，path 对应 JSON 字段名
- `sample_xml_fields` 中能匹配的字段：使用 `source: xml`，xpath 取相对路径
- 找不到来源的字段：使用 `source: none`

生成映射 JSON 格式：

```json
{
  "header_mapping": {
    "*invoiceNo":            {"source": "json", "path": "invoiceNo",            "example": "Inv-26-000001"},
    "*issueDate":            {"source": "json", "path": "issueDate",            "example": "2026-02-02"},
    "*invoiceType":          {"source": "json", "path": "invoiceTypeCode",      "example": "380"},
    "*documentCurrencyCode": {"source": "json", "path": "invoiceCurrencyCode",  "example": "EUR"},
    "*NetAmount":            {"source": "json", "path": "taxExclusiveAmount",   "example": "170.47"},
    "*TaxAmount":            {"source": "json", "path": "taxAmount",            "example": "1.58"},
    "*PayableAmount":        {"source": "json", "path": "totalAmount",          "example": "172.05"},
    "*buyerName":            {"source": "json", "path": "customerName",         "example": "Kingdee Test Buyer DE"},
    "*sellerName":           {"source": "json", "path": "supplierName",         "example": "DE-TEST-ORG"},
    "*sellerCountry":        {"source": "json", "path": "supplierCountryCode",  "example": "DE"},
    "*sellerTaxNo":          {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID", "example": ""},
    "*payeeAccountNo":       {"source": "xml",  "xpath": "cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID", "example": ""}
  },
  "line_mapping": {
    "*invoiceNo":  {"source": "json", "path": "invoiceNo",       "example": "Inv-26-000001"},
    "*itemName":   {"source": "json", "path": "itemName",        "example": "APPLE GREEN"},
    "*quantity":   {"source": "json", "path": "quantity",        "example": "1"},
    "*unitPrice":  {"source": "json", "path": "unitPrice",       "example": "13.2"},
    "*unit":       {"source": "json", "path": "unitCode",        "example": "KGM"},
    "*taxCode":    {"source": "json", "path": "taxCategoryCode", "example": "Z"},
    "*taxRate":    {"source": "json", "path": "taxRate",         "example": "0"}
  }
}
```

#### 3.3 保存映射

```bash
cat > /tmp/elc_mapping.json << 'EOF'
{推断的完整映射 JSON}
EOF

elc export save-mapping \
  [--template {template}] \
  --file /tmp/elc_mapping.json
```

### 第四步：执行导出

```bash
elc export invoice \
  [--template {template}] \
  --from {YYYY-MM-DD} --to {YYYY-MM-DD} \
  [--company {company}]
```

template、out 已有默认值，通常不需要传入。

### 第五步：报告结果

告知用户：
- 生成的文件完整路径
- 导出的发票数量
- 如有错误，说明原因和解决方法

---

## 使用示例

**用户输入：**
> 导出最近2周 BU-00008 的发票

**Claude 全自动执行（无需用户干预）：**
1. 运行 elc-context → 获取环境，检测到已登录
2. 解析日期：最近2周 → `--from 2026-06-17 --to 2026-07-01`
3. 检查映射表 → 已初始化 → 跳过 init
4. 运行：`elc export invoice --from 2026-06-17 --to 2026-07-01 --company BU-00008`
5. 报告：✓ 已导出 N 张发票到 ~/Downloads/invoice_export_20260617_20260701.xlsx

---

**用户输入：**
> 导出上个月的发票

**Claude 全自动执行（首次使用，未初始化）：**
1. 运行 elc-context → 检测到未登录 → 自动运行 `elc login` → 登录成功
2. 解析日期：上个月 → `--from 2026-06-01 --to 2026-06-30`
3. 检查映射表 → 未初始化 → 自动运行 `elc export init --output /tmp/elc_init_sample.json`
4. 读取样本，推断映射 JSON，写入 `/tmp/elc_mapping.json`
5. 运行 `elc export save-mapping --file /tmp/elc_mapping.json`
6. 运行：`elc export invoice --from 2026-06-01 --to 2026-06-30`
7. 报告：✓ 已导出 N 张发票到 ~/Downloads/invoice_export_20260601_20260630.xlsx
