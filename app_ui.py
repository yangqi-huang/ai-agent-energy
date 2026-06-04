from shiny import ui

from config import SUPPORTED_EXTENSIONS


def build_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.input_password(
                "api_key",
                "DeepSeek API Key",
                placeholder="输入你的 API Key",
            ),
            ui.hr(),
            ui.h5("上传项目材料"),
            ui.output_ui("upload_panel"),
            ui.input_action_button(
                "run_agent",
                "开始生成项目简报",
                class_="btn-primary w-100",
            ),
            ui.download_button(
                "download_word",
                "下载 Word 简报",
                class_="btn-success w-100 mt-2",
            ),
            ui.input_action_button(
                "clear_agent",
                "清空",
                class_="btn-outline-secondary w-100 mt-2",
            ),
            ui.hr(),
            ui.output_ui("uploaded_files_preview"),
            width=320,
        ),
        ui.tags.head(
            ui.tags.title("项目简报 AI Agent"),
            ui.tags.link(rel="stylesheet", href="styles.css"),
            ui.tags.script(src="app.js"),
        ),
        ui.card(
            ui.h4("AI 结构化输出"),
            ui.output_ui("report_output"),
            height="calc(100vh - 70px)",
            full_screen=True,
        ),
        fillable=True,
    )


def upload_input(version: int):
    return ui.div(
        ui.input_file(
            "upload",
            "上传 PPT / PDF / Word / 图片",
            multiple=True,
            accept=SUPPORTED_EXTENSIONS,
        ),
        id=f"upload_panel_{version}",
    )
