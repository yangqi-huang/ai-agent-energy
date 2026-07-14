import re

from material_metrics import material_has_category, material_has_economic_metrics
from prompts import REQUIRED_REPORT_SECTIONS


def validate_report_structure(report_text: str, material_text: str = "") -> list[str]:
    issues = []
    positions = []

    if not re.search(r"^#\s+.+项目简报\s*$", report_text, re.MULTILINE):
        issues.append("缺少格式为“# [项目名称]项目简报”的主标题")

    for section in REQUIRED_REPORT_SECTIONS:
        match = re.search(rf"^##\s+{re.escape(section)}\s*$", report_text, re.MULTILINE)
        if not match:
            issues.append(f"缺少或未严格使用章节标题：## {section}")
        else:
            positions.append(match.start())

    if len(positions) == len(REQUIRED_REPORT_SECTIONS) and positions != sorted(positions):
        issues.append("八个章节的顺序不正确")

    summary_match = re.search(
        r"^##\s+一、项目摘要\s*$([\s\S]*?)(?=^##\s+二、项目定位\s*$)",
        report_text,
        re.MULTILINE,
    )
    if not summary_match:
        issues.append("无法识别项目摘要章节")
    else:
        summary = summary_match.group(1)
        required_rows = [
            "项目要素",
            "项目名称",
            "项目地点",
            "项目类型",
            "当前阶段",
            "核心建设或交易内容",
            "项目、区块或矿权面积",
            "资源量、储量及可采储量（含认证口径及日期）",
            "资源组分",
            "设计产能或项目规模",
            "主要合作方",
            "投资方式及投资金额",
            "经济投资指标（IRR、NPV、投资回收期等）",
            "商业模式及收益来源",
            "目标市场及消纳安排",
            "关键时间节点",
            "初步推进判断",
        ]
        if summary.count("|") < 30:
            issues.append("项目摘要未使用完整的两列表格")
        missing_rows = [row for row in required_rows if row not in summary]
        if missing_rows:
            issues.append(f"项目摘要表格缺少字段：{'、'.join(missing_rows)}")
        if material_has_economic_metrics(material_text):
            economic_row = re.search(
                r"^\|\s*经济投资指标（IRR、NPV、投资回收期等）\s*\|\s*(.*?)\s*\|",
                summary,
                re.MULTILINE,
            )
            economic_text = economic_row.group(1).strip() if economic_row else ""
            if (
                not economic_text
                or economic_text in {"待向合作方确认", "不适用", "-"}
                or not re.search(r"IRR|NPV|投资回收期|回收期|EBITDA|CAPEX|OPEX|净现值|内部收益率", economic_text, re.IGNORECASE)
            ):
                issues.append("材料中存在经济指标线索，但项目摘要的经济投资指标未提取IRR、NPV或回收期等内容")
        summary_row_checks = [
            (
                "资源储量与面积",
                "项目、区块或矿权面积",
                r"面积|区块|矿权|km|平方|acreage|\d",
            ),
            (
                "资源储量与面积",
                "资源量、储量及可采储量（含认证口径及日期）",
                r"储量|资源量|可采|reserve|resource|2P|3P|P50|P90|\d",
            ),
            (
                "资源组分与质量",
                "资源组分",
                r"组分|甲烷|乙烷|丙烷|丁烷|硫|热值|methane|ethane|propane|butane|HHV|LHV|\d",
            ),
            (
                "产能规模与建设内容",
                "设计产能或项目规模",
                r"产能|规模|处理量|吞吐|储罐|装置|capacity|MTPA|万吨|吨/年|\d",
            ),
            (
                "合作方与交易结构",
                "主要合作方",
                r"合作方|股权|合资|operator|partner|JV|equity",
            ),
            (
                "时间节点与审批许可",
                "关键时间节点",
                r"20\d{2}|投产|开工|建设期|FID|COD|审批|许可|permit|license",
            ),
        ]
        for category, row_name, expected_pattern in summary_row_checks:
            if not material_has_category(material_text, category):
                continue
            row_match = re.search(
                rf"^\|\s*{re.escape(row_name)}\s*\|\s*(.*?)\s*\|",
                summary,
                re.MULTILINE,
            )
            row_text = row_match.group(1).strip() if row_match else ""
            if (
                not row_text
                or row_text in {"待向合作方确认", "不适用", "-"}
                or not re.search(expected_pattern, row_text, re.IGNORECASE)
            ):
                issues.append(f"材料中存在“{category}”线索，但项目摘要的“{row_name}”未充分提取")

    market_match = re.search(
        r"^##\s+四、市场与消纳\s*$([\s\S]*?)(?=^##\s+五、投资方式与商业模式\s*$)",
        report_text,
        re.MULTILINE,
    )
    if not market_match:
        issues.append("无法识别市场与消纳章节")
    else:
        market = market_match.group(1)
        required_market_headers = [
            "需求点/企业名称",
            "所属产业或用能场景",
            "与项目设施或气田的距离及方位",
            "可能需求规模",
            "需求依据",
            "对项目消纳的意义",
        ]
        missing_market_headers = [
            header for header in required_market_headers if header not in market
        ]
        if missing_market_headers:
            issues.append(f"市场与消纳表格缺少字段：{'、'.join(missing_market_headers)}")
        if market.count("|") < 18:
            issues.append("市场与消纳应使用具体需求点表格，而不是泛泛描述")
        generic_names = {
            "化肥厂",
            "电厂",
            "工业园",
            "城市燃气",
            "大型工业用户",
            "炼厂",
            "矿山",
            "水泥厂",
            "玻璃厂",
            "陶瓷厂",
            "冶金企业",
            "港口用户",
            "待向合作方确认",
            "待测算",
        }
        named_rows = 0
        generic_rows = 0
        for line in market.splitlines():
            stripped = line.strip()
            if not stripped.startswith("|") or "---" in stripped or "需求点/企业名称" in stripped:
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if len(cells) < 6:
                continue
            name = cells[0]
            if not name:
                continue
            if (
                name in generic_names
                or name.startswith("待核实")
                or re.fullmatch(r"(附近|周边)?(化肥厂|电厂|工业园|城市燃气|大型工业用户|炼厂|矿山|水泥厂|玻璃厂|陶瓷厂|冶金企业).*", name)
            ):
                generic_rows += 1
            else:
                named_rows += 1
        if named_rows == 0:
            issues.append("市场与消纳必须至少列出1个可点名的具体需求点，不能只列化肥厂/电厂/工业园等类型词或待核实类型")

    questions_match = re.search(
        r"^##\s+八、项目推进问题清单\s*$([\s\S]*)$",
        report_text,
        re.MULTILINE,
    )
    if not questions_match:
        issues.append("无法识别项目推进问题清单")
    else:
        questions = re.findall(
            r"^\s*(?:[1-9]|10)[.、)]\s+.+",
            questions_match.group(1),
            re.MULTILINE,
        )
        if len(questions) != 10:
            issues.append(f"项目推进问题清单应有10个编号问题，当前识别到{len(questions)}个")

    forbidden_sections = [
        "项目评分模型",
        "外部数据验证",
        "外围证据验证",
        "外部证据摘要",
        "人工审慎把关判断",
        "建议下一步工作",
        "下一步计划",
    ]
    found_forbidden = [
        section
        for section in forbidden_sections
        if re.search(rf"^##+\s+.*{re.escape(section)}.*$", report_text, re.MULTILINE)
    ]
    if found_forbidden:
        issues.append(f"包含禁止输出的章节：{'、'.join(found_forbidden)}")

    return issues
