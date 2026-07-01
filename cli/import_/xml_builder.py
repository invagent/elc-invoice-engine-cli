"""将 Excel 行数据按 import mapping 构建 UBL 2.1 Invoice XML。"""
from __future__ import annotations

from lxml import etree

NS_INVOICE = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
NS_CAC = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
NS_CBC = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"

NSMAP = {
    None:  NS_INVOICE,
    "cac": NS_CAC,
    "cbc": NS_CBC,
}

CAC = f"{{{NS_CAC}}}"
CBC = f"{{{NS_CBC}}}"


def _sub(parent: etree._Element, tag: str, text: str | None = None,
         attrib: dict | None = None) -> etree._Element:
    el = etree.SubElement(parent, tag, attrib=attrib or {})
    if text is not None:
        el.text = str(text)
    return el


def build_xml(header: dict, lines: list[dict], mapping: dict) -> bytes:
    """
    header: 表头字段 {col_name: value}
    lines:  行项目列表 [{col_name: value}, ...]
    mapping: import mapping，包含 header_mapping / line_mapping / xml_template

    返回 UTF-8 编码的 XML bytes。
    """
    hm = mapping.get("header_mapping", {})
    lm = mapping.get("line_mapping", {})

    def hv(field: str) -> str | None:
        """取表头字段值，优先从 header dict，次选 mapping 中的 default。"""
        col = hm.get(field, {}).get("col")
        if col and col in header:
            return str(header[col]) if header[col] is not None else None
        return hm.get(field, {}).get("default")

    root = etree.Element(f"{{{NS_INVOICE}}}Invoice", nsmap=NSMAP)

    # 固定头
    _sub(root, f"{CBC}UBLVersionID", "2.1")
    _sub(root, f"{CBC}CustomizationID", "urn:piaozone.com:ubl-2.1-customizations:v1.0")
    _sub(root, f"{CBC}ProfileID",       "urn:piaozone.com:profile:bill:v1.0")

    # 发票头字段
    if hv("InvoiceTypeCode"):
        _sub(root, f"{CBC}InvoiceTypeCode", hv("InvoiceTypeCode"))
    if hv("Note"):
        _sub(root, f"{CBC}Note", hv("Note"))
    if hv("DueDate"):
        _sub(root, f"{CBC}DueDate", hv("DueDate"))
    if hv("TaxPointDate"):
        _sub(root, f"{CBC}TaxPointDate", hv("TaxPointDate"))
    if hv("DocumentCurrencyCode"):
        _sub(root, f"{CBC}DocumentCurrencyCode", hv("DocumentCurrencyCode"))
    if hv("TaxCurrencyCode"):
        _sub(root, f"{CBC}TaxCurrencyCode", hv("TaxCurrencyCode"))
    if hv("BuyerReference"):
        _sub(root, f"{CBC}BuyerReference", hv("BuyerReference"))

    # BillId (幂等去重)
    bill_id = hv("BillId")
    if bill_id:
        adr = _sub(root, f"{CAC}AdditionalDocumentReference")
        id_el = _sub(adr, f"{CBC}ID", bill_id)
        id_el.set("schemeName", "InvoiceTag")
        _sub(adr, f"{CBC}DocumentType", "BillId")

    # 销方
    supplier_id = hv("SupplierPartyId")
    if supplier_id:
        asp = _sub(root, f"{CAC}AccountingSupplierParty")
        party = _sub(asp, f"{CAC}Party")
        pi = _sub(party, f"{CAC}PartyIdentification")
        id_el = _sub(pi, f"{CBC}ID", supplier_id)
        id_el.set("schemeID", hv("SupplierPartySchemeID") or "ERP")
        # 国家
        country = hv("SupplierCountry")
        if country:
            addr = _sub(party, f"{CAC}PostalAddress")
            c = _sub(addr, f"{CAC}Country")
            _sub(c, f"{CBC}IdentificationCode", country)
        # 公司名
        if hv("SupplierName"):
            ple = _sub(party, f"{CAC}PartyLegalEntity")
            _sub(ple, f"{CBC}RegistrationName", hv("SupplierName"))

    # 买方
    customer_id = hv("CustomerPartyId")
    if customer_id:
        acp = _sub(root, f"{CAC}AccountingCustomerParty")
        party = _sub(acp, f"{CAC}Party")
        pi = _sub(party, f"{CAC}PartyIdentification")
        id_el = _sub(pi, f"{CBC}ID", customer_id)
        id_el.set("schemeID", hv("CustomerPartySchemeID") or "TAXID")
        # 地址
        addr = _sub(party, f"{CAC}PostalAddress")
        for field, tag in [
            ("CustomerStreet",     f"{CBC}StreetName"),
            ("CustomerCity",       f"{CBC}CityName"),
            ("CustomerPostalZone", f"{CBC}PostalZone"),
        ]:
            if hv(field):
                _sub(addr, tag, hv(field))
        country = hv("CustomerCountry")
        if country:
            c = _sub(addr, f"{CAC}Country")
            _sub(c, f"{CBC}IdentificationCode", country)
        # 公司名
        if hv("CustomerName"):
            ple = _sub(party, f"{CAC}PartyLegalEntity")
            _sub(ple, f"{CBC}RegistrationName", hv("CustomerName"))

    # 付款方式
    payee_account = hv("PayeeAccountNo")
    if payee_account:
        pm = _sub(root, f"{CAC}PaymentMeans")
        _sub(pm, f"{CBC}PaymentMeansCode", "30")
        pfa = _sub(pm, f"{CAC}PayeeFinancialAccount")
        _sub(pfa, f"{CBC}ID", payee_account)
        if hv("PayeeAccountName"):
            _sub(pfa, f"{CBC}Name", hv("PayeeAccountName"))
        branch_id = hv("FinancialInstitutionBranchId")
        if branch_id:
            fib = _sub(pfa, f"{CAC}FinancialInstitutionBranch")
            _sub(fib, f"{CBC}ID", branch_id)

    # 付款条款
    if hv("PaymentTermsNote"):
        pt = _sub(root, f"{CAC}PaymentTerms")
        _sub(pt, f"{CBC}Note", hv("PaymentTermsNote"))

    # 税总计（从行项目汇总）
    tax_amount = _sum_lines(lines, lm, "TaxAmount")
    tt = _sub(root, f"{CAC}TaxTotal")
    _sub(tt, f"{CBC}TaxAmount", f"{tax_amount:.2f}")

    # 金额总计
    tax_excl = _sum_lines(lines, lm, "LineExtensionAmount")
    lmt = _sub(root, f"{CAC}LegalMonetaryTotal")
    _sub(lmt, f"{CBC}TaxExclusiveAmount", f"{tax_excl:.2f}")
    _sub(lmt, f"{CBC}TaxInclusiveAmount", f"{tax_excl + tax_amount:.2f}")

    # 行项目
    for idx, line in enumerate(lines, 1):
        def lv(field: str) -> str | None:
            col = lm.get(field, {}).get("col")
            if col and col in line:
                return str(line[col]) if line[col] is not None else None
            return lm.get(field, {}).get("default")

        il = _sub(root, f"{CAC}InvoiceLine")
        _sub(il, f"{CBC}ID", str(idx))

        qty = lv("Quantity") or "1"
        unit = lv("UnitCode") or "H87"
        qty_el = _sub(il, f"{CBC}InvoicedQuantity", qty)
        qty_el.set("unitCode", unit)

        line_ext = lv("LineExtensionAmount") or "0"
        _sub(il, f"{CBC}LineExtensionAmount", line_ext)

        # 行税额
        line_tax = lv("TaxAmount")
        if line_tax:
            lt = _sub(il, f"{CAC}TaxTotal")
            _sub(lt, f"{CBC}TaxAmount", line_tax)

        # 商品信息
        item = _sub(il, f"{CAC}Item")
        if lv("ItemDescription"):
            _sub(item, f"{CBC}Description", lv("ItemDescription"))
        if lv("ItemName"):
            _sub(item, f"{CBC}Name", lv("ItemName"))
        if lv("ItemCode"):
            sii = _sub(item, f"{CAC}SellersItemIdentification")
            _sub(sii, f"{CBC}ID", lv("ItemCode"))

        # 税率
        tax_cat = lv("TaxCategoryCode") or "S"
        tax_rate = lv("TaxRate") or "0"
        ctc = _sub(item, f"{CAC}ClassifiedTaxCategory")
        _sub(ctc, f"{CBC}ID", tax_cat)
        _sub(ctc, f"{CBC}Percent", tax_rate)

        # 单价
        price = lv("UnitPrice")
        if price:
            p = _sub(il, f"{CAC}Price")
            _sub(p, f"{CBC}PriceAmount", price)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True)


def _sum_lines(lines: list[dict], lm: dict, field: str) -> float:
    total = 0.0
    col = lm.get(field, {}).get("col")
    if not col:
        return total
    for line in lines:
        try:
            total += float(line.get(col) or 0)
        except (ValueError, TypeError):
            pass
    return total
