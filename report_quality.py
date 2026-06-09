import re

from prompts import REQUIRED_REPORT_SECTIONS


def validate_report_structure(report_text: str) -> list[str]:
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
