import re

from intelligence_prompts import REQUIRED_INTELLIGENCE_SECTIONS


REQUIRED_TABLE_HEADERS = {
    "一、项目类型与区域定位": ["定位要素", "判断", "项目类型", "价值链位置"],
    "二、核心资源与原料条件": ["资源或原料事项", "区域公开信息", "与项目的关联", "初步影响"],
    "三、价格与成本基准": ["价格或成本项目", "区域基准与单位", "数据日期及来源", "对项目经济性的影响"],
    "四、基础设施与实施条件": ["基础设施或实施条件", "区域情况", "与项目的距离或连接关系", "对项目的影响"],
    "五、市场消纳与竞争格局": ["市场事项", "区域情况", "竞争或消纳影响", "初步判断"],
    "六、政策与投资环境": ["政策或投资事项", "公开信息", "对项目的影响", "需进一步关注"],
    "八、数据来源": ["编号", "数据主题", "来源机构或网站", "发布或更新日期", "链接"],
}


def _section_content(text: str, section: str, next_section: str | None) -> str:
    end_pattern = rf"(?=^##\s+{re.escape(next_section)}\s*$)" if next_section else r"$"
    match = re.search(
        rf"^##\s+{re.escape(section)}\s*$([\s\S]*?){end_pattern}",
        text,
        re.MULTILINE,
    )
    return match.group(1) if match else ""


def validate_intelligence_structure(text: str) -> list[str]:
    issues = []
    positions = []

    if not re.search(r"^#\s+.+区域资源与投资情报\s*$", text, re.MULTILINE):
        issues.append("缺少格式为“# [项目名称]区域资源与投资情报”的主标题")

    for section in REQUIRED_INTELLIGENCE_SECTIONS:
        match = re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.MULTILINE)
        if not match:
            issues.append(f"缺少或未严格使用章节标题：## {section}")
        else:
            positions.append(match.start())

    if len(positions) == len(REQUIRED_INTELLIGENCE_SECTIONS) and positions != sorted(positions):
        issues.append("八个区域情报章节的顺序不正确")

    for index, section in enumerate(REQUIRED_INTELLIGENCE_SECTIONS):
        if section not in REQUIRED_TABLE_HEADERS:
            continue
        next_section = (
            REQUIRED_INTELLIGENCE_SECTIONS[index + 1]
            if index + 1 < len(REQUIRED_INTELLIGENCE_SECTIONS)
            else None
        )
        content = _section_content(text, section, next_section)
        if not content:
            continue
        missing = [header for header in REQUIRED_TABLE_HEADERS[section] if header not in content]
        if content.count("|") < 8 or missing:
            detail = f"，缺少字段：{'、'.join(missing)}" if missing else ""
            issues.append(f"“{section}”未使用规定表格{detail}")

    conclusion = _section_content(
        text,
        "七、对项目投资判断的影响",
        "八、数据来源",
    )
    for heading in ["有利条件", "主要约束", "区域投资情报结论"]:
        if not re.search(rf"^###\s+{heading}\s*$", conclusion, re.MULTILINE):
            issues.append(f"投资判断章节缺少三级标题：### {heading}")

    return issues
