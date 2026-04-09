"""Aliyun Qwen API client wrapper."""
import json
from typing import Optional, Dict, Any
from datetime import date
from pydantic import BaseModel, ValidationError
import dashscope
from dashscope import Generation

from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.text import truncate_input

logger = get_logger(__name__)


def _log_api_call_to_db():
    """Log API call to database for persistent tracking."""
    try:
        from src.core.database import get_session
        from src.models.api_call_log import APICallLog
        config = get_config()
        session = get_session()
        today = date.today()
        log_entry = session.query(APICallLog).filter_by(date=today).first()
        if log_entry:
            log_entry.call_count += 1
        else:
            log_entry = APICallLog(
                date=today,
                call_count=1,
                limit=config.ai.daily_limit,
            )
            session.add(log_entry)
        session.commit()
        session.close()
    except Exception as e:
        logger.warning("Failed to log API call to DB", error=str(e))


class APICallLimiter:
    """Track and enforce daily API call limits."""

    def __init__(self, daily_limit: int):
        """
        Initialize API call limiter.

        Args:
            daily_limit: Maximum API calls per day
        """
        self.daily_limit = daily_limit
        self.calls_today = 0
        self.reset_date = date.today()

    def check_and_increment(self) -> bool:
        """
        Check if call is allowed and increment counter.

        Returns:
            True if call allowed, False if limit exceeded
        """
        # Reset counter if new day
        if date.today() > self.reset_date:
            self.calls_today = 0
            self.reset_date = date.today()

        # Check limit
        if self.calls_today >= self.daily_limit:
            logger.error(
                "Daily API limit exceeded",
                limit=self.daily_limit,
                calls=self.calls_today,
            )
            return False

        # Increment counter
        self.calls_today += 1
        # Log to database
        _log_api_call_to_db()
        return True


# Global limiter instance
_limiter: Optional[APICallLimiter] = None


def get_limiter() -> APICallLimiter:
    """Get global API call limiter instance."""
    global _limiter
    if _limiter is None:
        config = get_config()
        _limiter = APICallLimiter(config.ai.daily_limit)
    return _limiter


def call_qwen_api(
    prompt: str,
    model: str = "qwen-turbo",
    max_retries: int = 3,
) -> Optional[str]:
    """
    Call Aliyun Qwen API with error handling and retry logic.

    Constitution compliance:
    - Try-except wrapping for all LLM calls
    - Input truncation to 1500 chars
    - Exponential backoff retry
    - Daily API call limiting

    Args:
        prompt: Input prompt
        model: Model name (qwen-turbo, qwen-max)
        max_retries: Maximum retry attempts

    Returns:
        API response text or None if failed
    """
    config = get_config()

    # Check dry-run mode
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Skipping API call", model=model)
        return None

    # Check API call limit
    limiter = get_limiter()
    if not limiter.check_and_increment():
        return None

    # Truncate input
    truncated_prompt = truncate_input(prompt, config.ai.input_max_chars)

    # Set API key
    dashscope.api_key = config.ai.api_key

    # Retry logic
    for attempt in range(max_retries):
        try:
            logger.info(
                "Calling Qwen API",
                model=model,
                prompt_length=len(truncated_prompt),
                attempt=attempt + 1,
            )

            response = Generation.call(
                model=model,
                prompt=truncated_prompt,
                result_format='message',
            )

            if response.status_code == 200:
                result = response.output.choices[0].message.content
                logger.info(
                    "API call successful",
                    model=model,
                    response_length=len(result),
                )
                return result
            else:
                logger.warning(
                    "API call failed",
                    model=model,
                    status_code=response.status_code,
                    error=response.message,
                )

        except Exception as e:
            logger.error(
                "API call exception",
                model=model,
                attempt=attempt + 1,
                error=str(e),
                exc_info=True,
            )

        # Exponential backoff
        if attempt < max_retries - 1:
            import time
            backoff = 2 ** attempt
            time.sleep(backoff)

    logger.error("API call failed after max retries", model=model, max_retries=max_retries)
    return None


def parse_llm_response(response: str, schema: type[BaseModel]) -> Optional[BaseModel]:
    """
    Safely parse LLM JSON response with error handling.

    Constitution compliance:
    - All JSON parsing wrapped in try-except
    - Pydantic validation for schema enforcement

    Args:
        response: Raw LLM response string
        schema: Pydantic model for validation

    Returns:
        Parsed model instance or None if parsing fails
    """
    try:
        # Try to extract JSON from response (handle markdown code blocks)
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()

        # Parse JSON
        data = json.loads(response)

        # Validate with Pydantic
        return schema(**data)

    except json.JSONDecodeError as e:
        logger.error(
            "LLM JSON parse failed",
            error=str(e),
            response_sample=response[:200],
            schema=schema.__name__,
        )
        return None

    except ValidationError as e:
        logger.error(
            "LLM schema validation failed",
            error=str(e),
            response_sample=response[:200],
            schema=schema.__name__,
        )
        return None

    except Exception as e:
        logger.error(
            "LLM parse unexpected error",
            error=str(e),
            response_sample=response[:200],
            schema=schema.__name__,
            exc_info=True,
        )
        return None
