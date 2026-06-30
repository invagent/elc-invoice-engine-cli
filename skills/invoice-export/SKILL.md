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
- 导出本月/上月/某月的发票

## 执行流程

### 第一步：解析用户意图

从用户输入中提取以下参数：

| 参数 | 提取方式 | 默认值 |
|------|----------|--------|
| `month` | "本月"→当前年月；"上个月"→上月；"2026-05"→直接用 | 当前年月 |
| `company` | 直接识别如 "BU-00008" | 读 .env.local 的 X_COMPANY_ID |
| `template` | 用户提到的文件路径 | 需要询问 |
| `out` | 用户提到的输出目录 | 当前目录 `.` |

如果 `template` 未提供，询问用户：
> 请提供 Excel 模版文件路径（如 ~/Downloads/invoice_export_template.xlsx）

### 第二步：检查映射表是否已初始化

```bash
# 检查缓存目录
ls ~/.elc/mappings/ 2>/dev/null || echo "空"
```

**情况 A：已初始化** → 直接跳到第四步执行导出。

**情况 B：未初始化** → 执行第三步。

### 第三步：初始化字段映射（首次使用）

#### 3.1 采集样本数据

```bash
elc export init \
  --template {template} \
  --company {company} \
  --output /tmp/elc_init_sample.json
```

#### 3.2 读取样本数据

读取 `/tmp/elc_init_sample.json`，内容包含：
- `header_columns`：表头信息 Sheet 的所有列名（英文+中文）
- `line_columns`：商品详情 Sheet 的所有列名（英文+中文）
- `sample_invoice_json`：一条真实发票的完整 JSON
- `sample_xml_fields`：KDUBL XML 中提取的字段列表（xpath + 值）

#### 3.3 推断字段映射

根据样本数据，为每个模版列推断映射来源，生成如下格式的 JSON：

```json
{
  "header_mapping": {
    "*sourceSystem":         {"source": "json", "path": "sourceSystem",     "example": "ERP"},
    "*invoiceNo":            {"source": "json", "path": "invoiceNo",        "example": "Inv-26-000001"},
    "*issueDate":            {"source": "json", "path": "issueDate",        "example": "2026-02-02"},
    "*invoiceType":          {"source": "json", "path": "invoiceTypeCode",  "example": "380"},
    "*documentCurrencyCode": {"source": "json", "path": "invoiceCurrencyCode", "example": "EUR"},
    "*NetAmount":            {"source": "json", "path": "taxExclusiveAmount", "example": "170.47"},
    "*TaxAmount":            {"source": "json", "path": "taxAmount",        "example": "1.58"},
    "*PayableAmount":        {"source": "json", "path": "totalAmount",      "example": "172.05"},
    "*buyerName":            {"source": "json", "path": "customerName",     "example": "Kingdee Test Buyer DE"},
    "buyerCode":             {"source": "json", "path": "customerId",       "example": "DE00000001"},
    "*sellerName":           {"source": "json", "path": "supplierName",     "example": "DE-TEST-ORG"},
    "*sellerCode":           {"source": "json", "path": "supplierId",       "example": "GB559403414101"},
    "*sellerCountry":        {"source": "json", "path": "supplierCountryCode", "example": "DE"},
    "*sellerTaxNo":          {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID", "example": ""},
    "*sellerStreet":         {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:StreetName", "example": ""},
    "*sellerCity":           {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:CityName", "example": ""},
    "*sellerCountry":        {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode", "example": ""},
    "*sellerPostalCode":     {"source": "xml",  "xpath": "cac:AccountingSupplierParty/cac:Party/cac:PostalAddress/cbc:PostalZone", "example": ""},
    "*BuyerStreet":          {"source": "xml",  "xpath": "cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:StreetName", "example": ""},
    "*BuyerCity":            {"source": "xml",  "xpath": "cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:CityName", "example": ""},
    "*BuyerCountry":         {"source": "xml",  "xpath": "cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cac:Country/cbc:IdentificationCode", "example": ""},
    "*BuyerPostalCode":      {"source": "xml",  "xpath": "cac:AccountingCustomerParty/cac:Party/cac:PostalAddress/cbc:PostalZone", "example": ""},
    "buyerTaxNo":            {"source": "xml",  "xpath": "cac:AccountingCustomerParty/cac:Party/cac:PartyTaxScheme/cbc:CompanyID", "example": ""},
    "*payeeAccountNo":       {"source": "xml",  "xpath": "cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID", "example": ""},
    "*payeeAccountName":     {"source": "xml",  "xpath": "cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:Name", "example": ""},
    "*FinancialInstitutionBranchId":   {"source": "xml", "xpath": "cac:PaymentMeans/cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:ID", "example": ""},
    "*FinancialInstitutionBranchName": {"source": "xml", "xpath": "cac:PaymentMeans/cac:PayeeFinancialAccount/cac:FinancialInstitutionBranch/cbc:Name", "example": ""},
    "*dueDate":              {"source": "xml",  "xpath": "cac:PaymentTerms/cbc:PaymentDueDate", "example": ""},
    "paymentTerms":          {"source": "xml",  "xpath": "cac:PaymentTerms/cbc:Note", "example": ""}
  },
  "line_mapping": {
    "*invoiceNo":   {"source": "json", "path": "invoiceNo",       "example": "Inv-26-000001"},
    "*lineNo":      {"source": "json", "path": "id",              "example": "1"},
    "*itemCode":    {"source": "json", "path": "id",              "example": "1"},
    "*itemName":    {"source": "json", "path": "itemName",        "example": "APPLE GREEN"},
    "*quantity":    {"source": "json", "path": "quantity",        "example": "1"},
    "*unitPrice":   {"source": "json", "path": "unitPrice",       "example": "13.2"},
    "*unit":        {"source": "json", "path": "unitCode",        "example": "KGM"},
    "*taxCode":     {"source": "json", "path": "taxCategoryCode", "example": "Z"},
    "*taxRate":     {"source": "json", "path": "taxRate",         "example": "0"},
    "taxAmount":    {"source": "none", "note": "行级税额需计算，暂不映射"}
  }
}
```

**推断规则：**
- 对照 `sample_invoice_json` 的字段与列名语义，能对上的用 `source: json`
- `sample_xml_fields` 中能找到对应值的用 `source: xml`，xpath 取相对路径
- 确实找不到对应数据的用 `source: none`

#### 3.4 将映射 JSON 写入临时文件并保存

```bash
# 将推断的映射 JSON 写入临时文件
cat > /tmp/elc_mapping.json << 'EOF'
{... 上面推断的完整 JSON ...}
EOF

# 保存到本地缓存
elc export save-mapping \
  --template {template} \
  --file /tmp/elc_mapping.json
```

### 第四步：执行导出

```bash
elc export invoice \
  --template {template} \
  --month {month} \
  --company {company} \
  --out {out}
```

### 第五步：报告结果

告知用户：
- 生成的文件完整路径
- 导出的发票数量
- 如有错误，说明原因和解决方法

---

## 使用示例

**用户输入：**
> 导出本月组织为 BU-00008 的发票数据，模版用 ~/Downloads/invoice_export_template.xlsx

**Claude 执行：**
1. 解析：month=当前年月，company=BU-00008，template=~/Downloads/invoice_export_template.xlsx
2. 检查映射表 → 未初始化 → 运行 `elc export init` 采集样本
3. 读取样本，推断映射 JSON
4. 运行 `elc export save-mapping` 保存
5. 运行 `elc export invoice` 导出
6. 报告：✓ 已导出 N 张发票到 ./invoice_export_YYYYMM.xlsx
