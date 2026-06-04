import time

import requests

from config import DEEPSEEK_API_URL


def chat_completion(
    api_key: str,
    model: str,
    messages: list[dict],
    temperature: float = 0.2,
    timeout: int = 180,
    retries: int = 3,
) -> dict:
    last_error = None

    for attempt in range(1, retries + 1):
        try:
            response = requests.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except (
            requests.exceptions.ChunkedEncodingError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError,
        ) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(1.5 * attempt)

    raise RuntimeError(f"DeepSeek API 请求失败，已重试 {retries} 次：{last_error}")


def response_text(result: dict) -> str:
    return result["choices"][0]["message"]["content"].strip()
