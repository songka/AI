"""Chinese display labels for UI and spreadsheet exports."""

from __future__ import annotations

from typing import Any

FIELD_LABELS = {
    "id": "记录序号",
    "ai_used": "是否使用智能辅助",
    "excel_path": "导出文件路径",
    "quote_id": "报价编号",
    "job_id": "任务编号",
    "drawing_number": "图号",
    "file_name": "文件名",
    "file_path": "文件路径",
    "quotation_status": "报价状态",
    "status_display": "状态",
    "cost_completion": "报价完整度",
    "unknown_count": "待确认项数",
    "subtotal_excl_tax": "未税小计",
    "tax_rate": "税率",
    "tax_amount": "税额",
    "total_incl_tax": "含税总价",
    "rule_version": "规则版本",
    "price_version": "价格版本",
    "quote_version": "报价版本",
    "quoted_by": "报价人",
    "pc_username": "电脑登录者",
    "pc_name": "电脑名称",
    "pc_ip": "IP 地址",
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "line_id": "费用行编号",
    "category": "费用类别",
    "name": "报价项目",
    "source": "价格来源",
    "source_display": "价格来源说明",
    "quantity": "数量",
    "unit": "单位",
    "unit_price": "单价",
    "amount": "未税金额",
    "confidence": "可信度",
    "status": "状态",
    "resolution_source": "定价依据",
    "resolution_display": "定价依据说明",
    "field_name": "调整字段",
    "value": "调整值",
    "old_value": "调整前",
    "new_value": "调整后",
    "reason": "调整原因",
    "operator": "操作人",
    "quote_version_before": "调整前版本",
    "quote_version_after": "调整后版本",
    "review_id": "审核编号",
    "target_type": "价格类型",
    "canonical_code": "材料/工艺名称",
    "canonical_code_display": "材料/工艺名称",
    "specification": "规格",
    "origin_supplier_id": "来源供应商",
    "origin_supplier_name": "来源供应商",
    "price_version_id": "价格版本",
    "company_price_id": "公司价格编号",
    "record_id": "来源记录编号",
    "supplier_name": "供应商",
    "supplier_id": "供应商编号",
    "material_code": "材料代码",
    "material_spec": "材料规格",
    "parsed_value": "报价",
    "price_basis": "计价口径",
    "effective_from": "生效日期",
    "effective_to": "失效日期",
    "read_only": "只读",
    "ai_estimated_unit_price": "智能辅助参考单价",
    "ai_estimated_amount": "智能辅助参考总额",
    "ai_estimated_unit": "智能辅助估价单位",
    "ai_estimate_reason": "智能辅助估价依据",
    "ai_estimate_confidence": "智能辅助估价可信度",
}

PRICE_CODE_LABELS = {
    "40CR": "40Cr 合金钢",
    "4CR13": "4Cr13 不锈钢",
    "738": "738 模具钢",
    "A6061-T6": "6061-T6 铝合金",
    "A6061T6": "6061-T6 铝合金",
    "ACRYLIC": "亚克力",
    "ALUMINUM": "铝材",
    "AL_PROFILE": "铝型材",
    "ANGLE_STEEL": "角钢",
    "BAKELITE": "电木",
    "BERYLLIUM_COPPER": "铍铜",
    "BRASS": "黄铜",
    "H13": "H13 模具钢",
    "IRON_STEEL_GENERIC": "普通钢材",
    "NAK80": "NAK80 模具钢",
    "P20": "P20 模具钢",
    "PC": "聚碳酸酯板",
    "POM": "聚甲醛（POM）",
    "PTFE": "聚四氟乙烯（PTFE）",
    "RED_COPPER": "紫铜",
    "S50C": "S50C 中碳钢",
    "SKD11": "SKD11 模具钢",
    "SKD61": "SKD61 模具钢",
    "SPCC": "SPCC 冷轧钢板",
    "SQUARE_TUBE": "方管",
    "STEEL": "钢材",
    "SUS304": "304 不锈钢",
    "URETHANE_RUBBER": "聚氨酯橡胶",
    "CNC": "数控加工",
    "車床": "车床",
    "銑床": "铣床",
    "磨床": "磨床",
    "鉗工": "钳工",
    "放電": "放电加工",
    "快絲": "快丝线切割",
    "慢絲": "慢丝线切割",
    "鍍鉻": "镀铬",
    "熱處理": "热处理",
    "陽極": "阳极氧化",
    "發黑": "发黑处理",
    "COATING_RAL9003": "RAL9003 喷涂",
}

ORIGIN_SUPPLIER_LABELS = {
    "SUP-TONGRUI": "通瑞",
    "SUP-LIANGWEI": "良伟",
    "SUP-FUYUCHANG": "富裕昌",
    "SUP-GUANGZHICHENG": "广致诚",
    "SUP-WENDI": "稳迪",
    "SUP-JMD": "捷密达",
}

STATUS_LABELS = {
    "COMPLETE": "报价完整",
    "INCOMPLETE": "部分价格待确认",
    "REVIEW_REQUIRED": "需要人工审核",
    "PARSE_FAILED": "图纸解析失败",
    "QUOTE_FAILED": "报价计算失败",
    "UNSUPPORTED": "暂不支持此文件",
    "WAITING": "等待处理",
    "PARSING": "正在解析图纸",
    "SCANNED": "已扫描",
    "DWG_CONVERTING": "正在转换 DWG 图纸",
    "DWG_CONVERSION_FAILED": "DWG 转换失败",
    "SUCCESS": "成功",
    "FAILED": "失败",
    "PENDING": "待审核",
    "PUBLISHED": "已发布",
    "MATCHED": "已配对",
    "UNMATCHED": "未配对",
    "DUPLICATE": "存在重复文件",
}

TYPE_LABELS = {
    "MATERIAL": "材料价格",
    "PROCESS": "加工价格",
    "SURFACE": "表面处理价格",
    "material": "材料费用",
    "process": "加工费用",
    "surface": "表面处理费用",
    "machining": "加工费用",
    "purchased": "外购费用",
    "assembly": "装配费用",
    "other": "整件价格",
}

FIELD_VALUE_LABELS = {
    "material": "材料",
    "thickness": "厚度",
    "dimensions": "尺寸",
    "surface_treatment": "表面处理",
    "process": "加工方式",
    "manual_price": "人工单价",
}

UNIT_LABELS = {
    "kg": "千克",
    "g": "克",
    "m": "米",
    "mm": "毫米",
    "m2": "平方米",
    "m²": "平方米",
    "hour": "小时",
    "h": "小时",
    "item": "件",
    "pcs": "件",
    "piece": "件",
    "set": "套",
    "each": "件",
}

CONFIDENCE_LABELS = {"high": "高", "medium": "中", "low": "低", "uncertain": "未确定"}

SOURCE_LABELS = {
    "C": "公司核准价格",
    "H": "历史成交价格",
    "E": "系统估算价格",
    "S": "供应商报价",
    "AI": "智能辅助建议",
    "M": "人工确认价格",
    "U": "价格待确认",
}

RESOLUTION_LABELS = {
    "PUBLISHED_COMPANY_PRICEBOOK": "已发布公司价格表",
    "LEGACY_YAML": "旧版报价规则",
    "LEGACY_YAML_DRAFT": "旧版草稿规则，需人工确认",
    "MANUAL_QUOTE_OVERRIDE": "仅限当前报价的人工确认价格",
    "FEATURE_CALIBRATION_MODEL": "图纸特征价格校准模型",
}


def field_label(key: str) -> str:
    return FIELD_LABELS.get(key, key.replace("_", " "))


def display_price_code(value: Any) -> str:
    """Show a user-facing Chinese material/process name while retaining codes internally."""
    if value is None or value == "":
        return "—"
    text = str(value).strip()
    return PRICE_CODE_LABELS.get(text.upper(), PRICE_CODE_LABELS.get(text, text))


def display_origin_supplier(value: Any) -> str:
    """Never expose supplier IDs as the user-facing source name."""
    if value is None or value == "":
        return "公司内部核准价"
    return ORIGIN_SUPPLIER_LABELS.get(str(value), "供应商名称未维护")


def display_value(key: str, value: Any) -> str:
    if value is None or value == "":
        return "—"
    text = str(value)
    if key in {"canonical_code", "canonical_code_display", "material_code", "target_name"}:
        return display_price_code(value)
    if key in {"origin_supplier_id", "origin_supplier_name"}:
        return display_origin_supplier(value)
    if key in {"quotation_status", "status"}:
        return STATUS_LABELS.get(text, text)
    if key in {"target_type", "category"}:
        return TYPE_LABELS.get(text, text)
    if key == "field_name":
        return FIELD_VALUE_LABELS.get(text, text)
    if key == "unit":
        return UNIT_LABELS.get(text.casefold(), text)
    if key in {"confidence", "ai_estimate_confidence"}:
        if key == "ai_estimate_confidence":
            try:
                return f"{float(value) * 100:.0f}%"
            except (TypeError, ValueError):
                return text
        return CONFIDENCE_LABELS.get(text.casefold(), text)
    if key in {"source", "quote_price_source", "origin_price_source"}:
        return SOURCE_LABELS.get(text, text)
    if key in {"resolution_source", "resolution_display"}:
        return RESOLUTION_LABELS.get(text, text)
    if key in {"read_only", "fallback_warning", "ai_accepted", "recalculated", "ai_used"}:
        return "是" if bool(value) else "否"
    if key == "tax_rate":
        try:
            numeric = float(value)
            return f"{numeric * 100:.0f}%" if numeric <= 1 else f"{numeric:.0f}%"
        except (TypeError, ValueError):
            return text
    if key == "cost_completion":
        return f"{float(value):.1f}%"
    if key in {
        "unit_price",
        "amount",
        "subtotal_excl_tax",
        "tax_amount",
        "total_incl_tax",
        "parsed_value",
        "ai_estimated_unit_price",
        "ai_estimated_amount",
    }:
        try:
            return f"{float(value):,.2f}"
        except (TypeError, ValueError):
            return text
    if key == "quantity":
        try:
            return f"{float(value):,.4f}".rstrip("0").rstrip(".")
        except (TypeError, ValueError):
            return text
    if key in {"created_at", "updated_at"}:
        return text.replace("T", " ").split("+")[0]
    return text
