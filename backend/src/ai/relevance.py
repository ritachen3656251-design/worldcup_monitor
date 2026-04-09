"""Relevance filtering using Qwen AI."""
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field

from src.ai.client import call_qwen_api, parse_llm_response
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_relevance_score

logger = get_logger(__name__)


class RelevanceScore(BaseModel):
    """AI output for relevance filtering."""
    score: int = Field(ge=1, le=10)
    reason: str = Field(min_length=1, max_length=200)


def _load_prompt_template() -> str:
    """Load relevance filter prompt template from file."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "relevance_filter.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def filter_relevance(title: str, content: str) -> Optional[RelevanceScore]:
    """
    Filter content by relevance to 2026 World Cup using Qwen AI.

    Constitution compliance:
    - Prompt loaded from external file (Principle V)
    - Try-except wrapping (Principle III)
    - Input truncation handled by client (Principle III)

    Args:
        title: Content title
        content: Cleaned text content

    Returns:
        RelevanceScore with score (1-10) and reason, or None if failed
    """
    config = get_config()

    # Dry-run mode: return mock data
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock relevance score")
        mock_data = generate_mock_relevance_score()
        return RelevanceScore(**mock_data)

    try:
        # Load and format prompt
        template = _load_prompt_template()
        prompt = template.replace("{title}", title).replace("{content}", content)

        # Call Qwen-Turbo (lightweight model for filtering)
        model = config.ai.models.get("relevance", "qwen-turbo")
        response = call_qwen_api(prompt, model=model)

        if response is None:
            logger.warning("Relevance API call returned None", title=title[:30])
            return None

        # Parse response
        result = parse_llm_response(response, RelevanceScore)
        if result:
            logger.info(
                "Relevance scored",
                title=title[:30],
                score=result.score,
                reason=result.reason,
            )
        return result

    except Exception as e:
        logger.error(
            "Relevance filtering failed",
            error=str(e),
            title=title[:30],
            exc_info=True,
        )
        return None
