import json
import re
from html import unescape

import requests
from duckduckgo_search import DDGS

from config import (
    SEARCH_PAGE_TEXT_CHARS,
    SEARCH_PAGES_PER_QUERY,
    SEARCH_RESULTS_PER_QUERY,
)


def parse_search_plan(raw_text: str) -> list[dict]:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    return [
        {
            "topic": str(item.get("topic", "行业背景")).strip(),
            "query": str(item.get("query", "")).strip(),
            "expected_context": str(item.get("expected_context", "补充行业背景")).strip(),
        }
        for item in data
        if isinstance(item, dict) and item.get("query")
    ]


def clean_html(html: str, max_chars: int = SEARCH_PAGE_TEXT_CHARS) -> str:
    html = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</(p|div|li|tr|h1|h2|h3)>", "\n", html)
    text = re.sub(r"(?is)<.*?>", " ", html)
    text = unescape(text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text)
    return text.strip()[:max_chars]


def fetch_page(url: str) -> str:
    try:
        response = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 Chrome/124 Safari/537.36"},
            timeout=10,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").lower()
        if "text/html" not in content_type and "text/plain" not in content_type:
            return ""
        return clean_html(response.text)
    except Exception:
        return ""


def run_search_plan(plan: list[dict]) -> str:
    blocks = []

    with DDGS() as ddgs:
        for item in plan:
            query = item["query"]
            try:
                results = list(ddgs.text(query, max_results=SEARCH_RESULTS_PER_QUERY))
            except Exception as exc:
                blocks.append(f"## {item['topic']}\n搜索失败：{exc}")
                continue

            result_lines = [
                f"## {item['topic']}",
                f"搜索词：{query}",
                f"用途：{item['expected_context']}",
            ]

            for index, result in enumerate(results, start=1):
                title = result.get("title", "")
                summary = result.get("body", "")[:700]
                url = result.get("href", "")
                page_text = fetch_page(url) if index <= SEARCH_PAGES_PER_QUERY else ""
                result_lines.append(
                    "\n".join([
                        f"### 结果 {index}: {title}",
                        f"摘要：{summary}",
                        f"正文摘录：{page_text}",
                        f"链接：{url}",
                    ])
                )

            blocks.append("\n\n".join(result_lines))

    return "\n\n---\n\n".join(blocks)
