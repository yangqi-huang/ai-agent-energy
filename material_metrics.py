import re


KEY_INFO_CATEGORIES = {
    "经济投资指标": [
        r"\bI\s*R\s*R\b",
        r"\b1\s*R\s*R\b",
        r"\bN\s*P\s*V\b",
        r"\bN\s*P\s*Y\b",
        r"\bEBITDA\b",
        r"\bCAPEX\b",
        r"\bOPEX\b",
        r"内部收益率",
        r"净现值",
        r"投资回收期",
        r"回收期",
        r"pay\s*back",
        r"payback",
        r"投资额",
        r"资本金",
        r"融资",
        r"现金流",
        r"收益率",
        r"investasi",
        r"biaya",
        r"pendapatan",
        r"arus\s+kas",
        r"pengembalian",
        r"kelayakan",
    ],
    "资源储量与面积": [
        r"储量",
        r"资源量",
        r"可采",
        r"矿权",
        r"区块",
        r"面积",
        r"acreage",
        r"reserve",
        r"resource",
        r"\b2P\b",
        r"\b3P\b",
        r"\bP50\b",
        r"\bP90\b",
        r"\bMt\b",
        r"\bBcf\b",
        r"\bTcf\b",
        r"km2",
        r"km²",
        r"平方公里",
        r"cadangan",
        r"sumber\s+daya",
        r"luas",
        r"hektar",
        r"blok",
        r"lapangan",
        r"prospek",
    ],
    "资源组分与质量": [
        r"组分",
        r"品位",
        r"热值",
        r"硫",
        r"灰分",
        r"水分",
        r"甲烷",
        r"乙烷",
        r"丙烷",
        r"丁烷",
        r"methane",
        r"ethane",
        r"propane",
        r"butane",
        r"sulfur",
        r"calorific",
        r"\bHHV\b",
        r"\bLHV\b",
        r"kandungan",
        r"komposisi",
        r"kualitas",
        r"kalori",
    ],
    "产能规模与建设内容": [
        r"产能",
        r"规模",
        r"处理量",
        r"吞吐",
        r"储罐",
        r"码头",
        r"管道",
        r"装置",
        r"产量",
        r"capacity",
        r"\bMTPA\b",
        r"tpa",
        r"万吨",
        r"吨/年",
        r"mmscfd",
        r"bpd",
        r"kapasitas",
        r"produksi",
        r"fasilitas",
        r"sumur",
        r"kilang",
    ],
    "价格成本与商业条件": [
        r"价格",
        r"成本",
        r"运费",
        r"电价",
        r"水价",
        r"气价",
        r"煤价",
        r"税",
        r"费率",
        r"tariff",
        r"price",
        r"cost",
        r"margin",
        r"offtake",
        r"take[- ]or[- ]pay",
        r"harga",
        r"tarif",
        r"kontrak",
        r"pembeli",
        r"penjualan",
    ],
    "合作方与交易结构": [
        r"合作方",
        r"股权",
        r"收购",
        r"出售",
        r"合资",
        r"JV",
        r"\bMOU\b",
        r"\bSPA\b",
        r"\bHOA\b",
        r"shareholding",
        r"equity",
        r"partner",
        r"operator",
        r"承购",
        r"pemegang\s+saham",
        r"mitra",
        r"kontraktor",
        r"operator",
        r"partisipasi",
        r"hak\s+partisipasi",
    ],
    "时间节点与审批许可": [
        r"时间",
        r"节点",
        r"投产",
        r"开工",
        r"建设期",
        r"审批",
        r"许可",
        r"牌照",
        r"特许",
        r"commissioning",
        r"FID",
        r"COD",
        r"permit",
        r"license",
        r"concession",
        r"\b20\d{2}\b",
        r"jadwal",
        r"tanggal",
        r"persetujuan",
        r"izin",
        r"kontrak\s+kerja\s+sama",
        r"\bKKS\b",
        r"\bSKK\s*Migas\b",
    ],
    "基础设施与物流消纳": [
        r"港口",
        r"铁路",
        r"公路",
        r"管网",
        r"电网",
        r"水源",
        r"园区",
        r"客户",
        r"消纳",
        r"物流",
        r"需求",
        r"需求量",
        r"电厂",
        r"化肥",
        r"尿素",
        r"炼厂",
        r"工业园",
        r"城市燃气",
        r"陶瓷",
        r"玻璃",
        r"水泥",
        r"冶金",
        r"矿山",
        r"大型工业用户",
        r"pipeline",
        r"rail",
        r"port",
        r"grid",
        r"industrial park",
        r"customer",
        r"demand",
        r"offtaker",
        r"fertilizer",
        r"urea",
        r"ammonia",
        r"power plant",
        r"refinery",
        r"smelter",
        r"cement",
        r"ceramic",
        r"glass",
        r"pipa",
        r"pelabuhan",
        r"jalan",
        r"pembangkit",
        r"jaringan",
        r"pasar",
        r"transportasi",
        r"kebutuhan",
        r"permintaan",
        r"pupuk",
        r"urea",
        r"amonia",
        r"kilang",
        r"kawasan\s+industri",
        r"pabrik",
        r"semen",
        r"kaca",
        r"keramik",
        r"smelter",
    ],
}


ECONOMIC_PATTERNS = KEY_INFO_CATEGORIES["经济投资指标"][:13]


def _normalize_key_text(text: str) -> str:
    replacements = {
        "1RR": "IRR",
        "I RR": "IRR",
        "I R R": "IRR",
        "NPY": "NPV",
        "N PV": "NPV",
        "N P V": "NPV",
    }
    output = text
    for source, target in replacements.items():
        output = re.sub(source, target, output, flags=re.IGNORECASE)
    return output


def _line_has_number_or_unit(text: str) -> bool:
    return bool(
        re.search(
            r"\d|%|USD|RMB|CNY|km|mmbtu|ton|tpa|MW|MWh|万吨|亿元|万美元|百万|mmscfd|bpd",
            text,
            re.IGNORECASE,
        )
    )


def _collect_context_blocks(
    material_text: str,
    category: str,
    patterns: list[str],
    max_items: int,
) -> list[str]:
    lines = [line.strip() for line in material_text.splitlines()]
    compiled = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    matched = []
    seen = set()

    for index, line in enumerate(lines):
        normalized_line = _normalize_key_text(line)
        if not normalized_line or not any(pattern.search(normalized_line) for pattern in compiled):
            continue

        start = max(0, index - 1)
        end = min(len(lines), index + 2)
        block = " ".join(_normalize_key_text(item) for item in lines[start:end] if item.strip())
        block = re.sub(r"\s+", " ", block).strip()

        if not block or block in seen:
            continue
        seen.add(block)

        prefix = "高置信" if _line_has_number_or_unit(block) else "线索"
        matched.append(f"{prefix}：{block[:520]}")
        if len(matched) >= max_items:
            break

    return matched


def extract_key_information_context(material_text: str, max_items_per_category: int = 10) -> str:
    rows = [
        "| 类别 | 材料中自动抽取的关键信息线索 |",
        "|---|---|",
    ]
    has_rows = False

    for category, patterns in KEY_INFO_CATEGORIES.items():
        blocks = _collect_context_blocks(
            material_text,
            category,
            patterns,
            max_items_per_category,
        )
        if not blocks:
            continue
        has_rows = True
        value = "<br>".join(f"{index}. {block}" for index, block in enumerate(blocks, start=1))
        rows.append(f"| {category} | {value.replace('|', '/')} |")

    if not has_rows:
        return ""

    return "\n".join([
        "【系统提取：材料关键信息线索】",
        "以下内容由上传材料、PDF/PPT/图片OCR文本自动抽取，生成简报时必须优先核对；不得因为正文较长而遗漏。",
        "\n".join(rows),
    ])


def extract_metric_context(material_text: str, max_items: int = 30) -> str:
    blocks = _collect_context_blocks(
        material_text,
        "经济投资指标",
        KEY_INFO_CATEGORIES["经济投资指标"],
        max_items,
    )
    if not blocks:
        return ""

    rows = [
        "| 序号 | 材料中的经济指标相关原文 |",
        "|---|---|",
    ]
    for index, block in enumerate(blocks, start=1):
        rows.append(f"| {index} | {block.replace('|', '/')} |")

    return "\n".join([
        "【系统提取：关键经济投资指标线索】",
        "以下内容由上传材料和OCR文本中自动抽取，生成项目摘要和商业模式章节时必须优先核对。",
        "\n".join(rows),
    ])


def material_has_economic_metrics(material_text: str) -> bool:
    normalized = _normalize_key_text(material_text)
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in ECONOMIC_PATTERNS)


def material_has_category(material_text: str, category: str) -> bool:
    patterns = KEY_INFO_CATEGORIES.get(category, [])
    normalized = _normalize_key_text(material_text)
    return any(re.search(pattern, normalized, re.IGNORECASE) for pattern in patterns)
