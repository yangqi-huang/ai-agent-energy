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
            ui.input_action_button(
                "run_regional_intelligence",
                "生成区域投资情报",
                class_="btn-outline-primary w-100 mt-2",
            ),
            ui.download_button(
                "download_word",
                "下载 Word 简报",
                class_="btn-success w-100 mt-2",
            ),
            ui.download_button(
                "download_parsed_text",
                "下载解析文本",
                class_="btn-outline-secondary w-100 mt-2",
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
        ui.div(
            ui.navset_card_tab(
                ui.nav_panel(
                    "AI 结构化输出",
                    ui.output_ui("report_output"),
                ),
                ui.nav_panel(
                    "区域资源与投资情报",
                    ui.output_ui("regional_intelligence_output"),
                ),
                full_screen=True,
            ),
            class_="main-tab-shell",
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
