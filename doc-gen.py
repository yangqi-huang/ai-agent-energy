from pathlib import Path

from shiny import App, Inputs, Outputs, Session, reactive, render, ui

from ai_service import chat_completion, response_text
from app_ui import build_ui, upload_input
from config import FAST_MODEL, MAX_SEARCH_QUERIES, REPORT_MODEL
from file_parser import parse_uploaded_files
from intelligence_prompts import (
    REGIONAL_INTELLIGENCE_SYSTEM_PROMPT,
    repair_intelligence_prompt,
    regional_intelligence_prompt,
    regional_search_plan_prompt,
)
from intelligence_quality import validate_intelligence_structure
from prompts import (
    SYSTEM_PROMPT,
    repair_report_prompt,
    report_user_prompt,
    research_plan_prompt,
)
from report_quality import validate_report_structure
from search_service import parse_search_plan, run_search_plan
from word_export import html_to_docx_bytes, markdown_to_html, word_filename


app_ui = build_ui()


def server(input: Inputs, output: Outputs, session: Session):
    material_text = reactive.Value("")
    report_markdown = reactive.Value("")
    regional_intelligence_markdown = reactive.Value("")
    upload_version = reactive.Value(0)
    upload_cleared = reactive.Value(False)

    @reactive.Effect
    @reactive.event(input.upload)
    def mark_upload_active():
        if input.upload():
            upload_cleared.set(False)
            material_text.set("")
            report_markdown.set("")
            regional_intelligence_markdown.set("")

    @reactive.Effect
    @reactive.event(input.clear_agent)
    def clear_agent():
        material_text.set("")
        report_markdown.set("")
        regional_intelligence_markdown.set("")
        upload_cleared.set(True)
        upload_version.set(upload_version() + 1)
        ui.notification_show("已清空，可上传新的项目材料。", type="message")

    @reactive.Effect
    @reactive.event(input.run_agent)
    def generate_report():
        with reactive.isolate():
            api_key = input.api_key().strip()
            files = None if upload_cleared() else input.upload()

        if not api_key:
            ui.notification_show("请输入 DeepSeek API Key", type="error")
            return

        if not files:
            ui.notification_show("请上传项目材料", type="error")
            return

        with ui.Progress(min=0, max=100) as progress:
            try:
                progress.set(10, message="正在解析项目材料...")
                parsed_material = parse_uploaded_files(files)
                material_text.set(parsed_material)

                progress.set(35, message="正在规划补充搜索...")
                plan_result = chat_completion(
                    api_key=api_key,
                    model=FAST_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是海外能源、化工和基础设施项目研究计划助手。",
                        },
                        {
                            "role": "user",
                            "content": research_plan_prompt(parsed_material),
                        },
                    ],
                    temperature=0.1,
                    timeout=90,
                )
                plan = parse_search_plan(response_text(plan_result))[:MAX_SEARCH_QUERIES]

                progress.set(55, message="正在补充行业与背景资料...")
                search_context = run_search_plan(plan)

                progress.set(75, message="正在生成项目简报...")
                report_result = chat_completion(
                    api_key=api_key,
                    model=REPORT_MODEL,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {
                            "role": "user",
                            "content": report_user_prompt(parsed_material, search_context),
                        },
                    ],
                    temperature=0.2,
                    timeout=180,
                )
                report_text = response_text(report_result)
                structure_issues = validate_report_structure(report_text)

                if structure_issues:
                    progress.set(90, message="正在校正简报结构...")
                    repair_result = chat_completion(
                        api_key=api_key,
                        model=REPORT_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {
                                "role": "user",
                                "content": repair_report_prompt(
                                    report_text,
                                    structure_issues,
                                ),
                            },
                        ],
                        temperature=0.1,
                        timeout=180,
                    )
                    repaired_text = response_text(repair_result)
                    repaired_issues = validate_report_structure(repaired_text)
                    if len(repaired_issues) < len(structure_issues):
                        report_text = repaired_text

                report_markdown.set(report_text)

                progress.set(100, message="完成")
                ui.notification_show("项目简报已生成。", type="message")
            except Exception as exc:
                ui.notification_show(f"生成失败：{exc}", type="error")

    @reactive.Effect
    @reactive.event(input.run_regional_intelligence)
    def generate_regional_intelligence():
        with reactive.isolate():
            api_key = input.api_key().strip()
            files = None if upload_cleared() else input.upload()
            parsed_material = material_text()

        if not api_key:
            ui.notification_show("请输入 DeepSeek API Key", type="error")
            return

        if not files and not parsed_material:
            ui.notification_show("请上传项目材料", type="error")
            return

        with ui.Progress(min=0, max=100) as progress:
            try:
                if not parsed_material:
                    progress.set(10, message="正在解析项目材料...")
                    parsed_material = parse_uploaded_files(files)
                    material_text.set(parsed_material)

                progress.set(30, message="正在识别项目区域并规划搜索...")
                plan_result = chat_completion(
                    api_key=api_key,
                    model=FAST_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是海外能源项目区域情报搜索规划助手。",
                        },
                        {
                            "role": "user",
                            "content": regional_search_plan_prompt(parsed_material),
                        },
                    ],
                    temperature=0.1,
                    timeout=90,
                )
                plan = parse_search_plan(response_text(plan_result))[:MAX_SEARCH_QUERIES]

                progress.set(55, message="正在搜索区域资源、成本与投资数据...")
                search_context = run_search_plan(plan)

                progress.set(78, message="正在整理区域投资情报...")
                intelligence_result = chat_completion(
                    api_key=api_key,
                    model=REPORT_MODEL,
                    messages=[
                        {
                            "role": "system",
                            "content": REGIONAL_INTELLIGENCE_SYSTEM_PROMPT,
                        },
                        {
                            "role": "user",
                            "content": regional_intelligence_prompt(
                                parsed_material,
                                search_context,
                            ),
                        },
                    ],
                    temperature=0.2,
                    timeout=180,
                )
                intelligence_text = response_text(intelligence_result)
                intelligence_issues = validate_intelligence_structure(intelligence_text)

                if intelligence_issues:
                    progress.set(90, message="正在校正区域情报结构...")
                    repair_result = chat_completion(
                        api_key=api_key,
                        model=REPORT_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": REGIONAL_INTELLIGENCE_SYSTEM_PROMPT,
                            },
                            {
                                "role": "user",
                                "content": repair_intelligence_prompt(
                                    intelligence_text,
                                    intelligence_issues,
                                ),
                            },
                        ],
                        temperature=0.1,
                        timeout=180,
                    )
                    repaired_text = response_text(repair_result)
                    repaired_issues = validate_intelligence_structure(repaired_text)
                    if len(repaired_issues) < len(intelligence_issues):
                        intelligence_text = repaired_text

                regional_intelligence_markdown.set(intelligence_text)
                progress.set(100, message="完成")
                ui.notification_show("区域资源与投资情报已生成。", type="message")
            except Exception as exc:
                ui.notification_show(f"区域情报生成失败：{exc}", type="error")

    @output
    @render.ui
    def upload_panel():
        return upload_input(upload_version())

    @output
    @render.ui
    def uploaded_files_preview():
        upload_version()
        files = input.upload()

        if upload_cleared() or not files:
            return ui.tags.small(
                "尚未上传文件，可一次选择多个文件。",
                class_="sidebar-note",
            )

        items = [
            ui.tags.li(f"{file_info.get('name', '未命名文件')}")
            for file_info in files
        ]
        return ui.div(
            ui.h6(f"已上传 {len(files)} 个文件"),
            ui.tags.ul(*items),
            ui.tags.small(
                "所有材料会合并进入同一份项目简报。",
                class_="sidebar-note",
            ),
        )

    @output
    @render.ui
    def report_output():
        content = report_markdown()
        if not content:
            return ui.div(
                "上传项目材料并点击“开始生成项目简报”。",
                class_="report-shell",
            )
        return ui.div(ui.HTML(markdown_to_html(content)), class_="report-shell")

    @output
    @render.ui
    def regional_intelligence_output():
        content = regional_intelligence_markdown()
        if not content:
            return ui.div(
                "上传项目材料后，点击左侧“生成区域投资情报”。",
                class_="report-shell",
            )
        return ui.div(ui.HTML(markdown_to_html(content)), class_="report-shell")

    @output
    @render.download(filename=word_filename)
    def download_word():
        content = report_markdown()
        if not content:
            content = "# 项目简报\n\n暂无内容，请先生成项目简报。"
        yield html_to_docx_bytes(markdown_to_html(content))


app = App(
    app_ui,
    server,
    static_assets=(Path(__file__).resolve().parent / "www"),
)
