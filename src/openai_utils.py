import re
import time
from typing import Any


def is_rate_limit_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True
    text = str(exc or "").lower()
    return (
        "rate limit" in text
        or "rate_limit_exceeded" in text
        or "tokens per min" in text
        or "error code: 429" in text
        or " status code 429" in text
    )


def compute_retry_delay(exc: Exception, attempt: int) -> float:
    text = str(exc or "")
    match = re.search(r"Please try again in ([0-9.]+)s", text)
    if match:
        return max(0.5, float(match.group(1)) + 0.5)
    return min(2 ** max(attempt - 1, 0), 8)


def call_chat_completion_with_backoff(
    client: Any,
    *,
    model: str,
    messages: list[dict[str, str]],
    max_tokens: int,
    logger: Any,
    operation_name: str,
    max_api_attempts: int = 4,
) -> Any:
    last_error: Exception | None = None
    for attempt in range(1, max_api_attempts + 1):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if not is_rate_limit_error(exc) or attempt >= max_api_attempts:
                raise
            delay = compute_retry_delay(exc, attempt)
            logger.warning(
                "Rate limit during %s on API attempt %s/%s. Sleeping %.2fs before retry. Error=%s",
                operation_name,
                attempt,
                max_api_attempts,
                delay,
                exc,
            )
            time.sleep(delay)
    raise last_error or RuntimeError(f"{operation_name} failed without a concrete exception")
