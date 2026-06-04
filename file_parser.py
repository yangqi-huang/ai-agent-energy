import shutil
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps
from PyPDF2 import PdfReader
from docx import Document
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE


def _preprocess_image(image_bytes: bytes) -> BytesIO:
    image = Image.open(BytesIO(image_bytes))
    image = ImageOps.exif_transpose(image).convert("L")
    width, height = image.size

    if max(width, height) < 1800:
        scale = min(3, 1800 / max(width, height))
        image = image.resize(
            (int(width * scale), int(height * scale)),
            Image.Resampling.LANCZOS,
        )

    image = ImageEnhance.Contrast(image).enhance(1.8)
    image = ImageOps.autocontrast(image)

    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return output


def ocr_image(image_bytes: bytes, lang: str = "chi_sim+eng") -> tuple[str, str | None]:
    try:
        processed = _preprocess_image(image_bytes)
    except Exception as exc:
        return "", f"图片预处理失败：{exc}"

    try:
        import pytesseract

        text = pytesseract.image_to_string(
            Image.open(processed),
            lang=lang,
            config="--psm 6",
        )
        return text.strip(), None
    except Exception as python_error:
        command = shutil.which("tesseract")
        if not command:
            return "", "未检测到OCR引擎，图片文字未提取。"

        with tempfile.NamedTemporaryFile(suffix=".png") as image_file:
            image_file.write(processed.getvalue())
            image_file.flush()
            try:
                result = subprocess.run(
                    [command, image_file.name, "stdout", "-l", lang, "--psm", "6"],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=45,
                )
                return result.stdout.strip(), None
            except Exception as cli_error:
                return "", f"OCR失败：{python_error}；{cli_error}"


def _parse_pdf(file_path: str) -> str:
    text = []
    reader = PdfReader(file_path)
    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        if page_text:
            text.append(f"【PDF第{index}页】\n{page_text}")
    return "\n\n".join(text)


def _parse_docx(file_path: str) -> str:
    document = Document(file_path)
    text = [paragraph.text for paragraph in document.paragraphs if paragraph.text]

    for index, table in enumerate(document.tables, start=1):
        rows = []
        for row in table.rows:
            cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            text.append(f"【Word表格 {index}】\n" + "\n".join(rows))

    return "\n\n".join(text)


def _parse_pptx(file_path: str) -> str:
    presentation = Presentation(file_path)
    output = []

    for slide_index, slide in enumerate(presentation.slides, start=1):
        slide_parts = []
        image_index = 0

        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text:
                slide_parts.append(shape.text.strip())

            if getattr(shape, "has_table", False):
                rows = []
                for row in shape.table.rows:
                    cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                    if any(cells):
                        rows.append(" | ".join(cells))
                if rows:
                    slide_parts.append("【表格】\n" + "\n".join(rows))

            if getattr(shape, "shape_type", None) == MSO_SHAPE_TYPE.PICTURE:
                image_index += 1
                recognized, error = ocr_image(shape.image.blob)
                if recognized:
                    slide_parts.append(f"【图片{image_index} OCR】\n{recognized}")
                elif error:
                    slide_parts.append(f"【图片{image_index}】{error}")

        try:
            notes = slide.notes_slide.notes_text_frame.text.strip()
            if notes:
                slide_parts.append(f"【备注】\n{notes}")
        except Exception:
            pass

        if slide_parts:
            output.append(f"【PPT第{slide_index}页】\n" + "\n\n".join(slide_parts))

    return "\n\n".join(output)


def _parse_image(file_path: str, file_name: str) -> str:
    text, error = ocr_image(Path(file_path).read_bytes())
    if text:
        return f"【图片文件：{file_name}】\n{text}"
    return f"【图片文件：{file_name}】\n{error or '未识别到图片文字'}"


def parse_file(file_path: str, file_name: str) -> str:
    extension = Path(file_name).suffix.lower()

    try:
        if extension == ".pdf":
            return _parse_pdf(file_path)
        if extension == ".docx":
            return _parse_docx(file_path)
        if extension == ".pptx":
            return _parse_pptx(file_path)
        if extension in {".png", ".jpg", ".jpeg"}:
            return _parse_image(file_path, file_name)
        return f"不支持的文件类型：{extension}"
    except Exception as exc:
        return f"解析失败：{exc}"


def parse_uploaded_files(files: list[dict]) -> str:
    blocks = []
    for file_info in files:
        name = file_info["name"]
        content = parse_file(file_info["datapath"], name)
        blocks.append(f"=== 文件名：{name} ===\n\n{content}")
    return "\n\n" + ("\n\n" + "=" * 50 + "\n\n").join(blocks)
