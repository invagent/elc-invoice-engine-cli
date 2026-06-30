"""KDUBL XML 解析：按映射表中的 XPath 批量提取字段。"""
from __future__ import annotations

from lxml import etree

NSMAP = {
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
    "ext": "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
}


def _xpath_text(root: etree._Element, xpath: str) -> str | None:
    try:
        nodes = root.xpath(xpath, namespaces=NSMAP)
        if not nodes:
            return None
        node = nodes[0]
        return node.text.strip() if hasattr(node, "text") and node.text else str(node).strip()
    except Exception:
        return None


def extract_fields(xml_bytes: bytes, xpath_map: dict[str, str]) -> dict[str, str | None]:
    """按 xpath_map 批量提取字段，返回 {col_name: value}。"""
    root = etree.fromstring(xml_bytes)
    return {col: _xpath_text(root, xpath) for col, xpath in xpath_map.items()}


def flatten_xml_fields(xml_bytes: bytes) -> list[dict]:
    """提取 XML 中所有叶子节点的 XPath + 值，用于 AI 推断映射时的上下文。"""
    root = etree.fromstring(xml_bytes)
    results = []

    def _walk(node: etree._Element, path: str) -> None:
        tag = etree.QName(node.tag).localname if node.tag else ""
        current_path = f"{path}/{tag}" if path else tag
        # 属性
        for attr_name, attr_val in node.attrib.items():
            attr_local = etree.QName(attr_name).localname if "{" in attr_name else attr_name
            results.append({"xpath": f"{current_path}[@{attr_local}]", "value": attr_val})
        # 文本值
        text = (node.text or "").strip()
        if text:
            results.append({"xpath": current_path, "value": text})
        for child in node:
            _walk(child, current_path)

    _walk(root, "")
    return results
