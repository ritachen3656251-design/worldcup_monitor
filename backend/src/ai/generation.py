"""Card and detail page generation using Qwen AI."""
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from src.ai.client import call_qwen_api, parse_llm_response
from src.core.config import get_config
from src.core.logging import get_logger
from src.utils.mock import generate_mock_card, generate_mock_detail

logger = get_logger(__name__)


class CardGeneration(BaseModel):
    """AI output for card generation."""
    title: str = Field(min_length=1, max_length=50)
    summary: str = Field(min_length=1, max_length=200)
    category: str
    sources: List[str] = Field(default_factory=list)


class ViewpointSchema(BaseModel):
    """A viewpoint in detail page."""
    source: str = ""
    view: str = ""
    citation: str = ""

    def __init__(self, **data):
        # Map common LLM field name variants
        if "content" in data and "view" not in data:
            data["view"] = data.pop("content")
        if "opinion" in data and "view" not in data:
            data["view"] = data.pop("opinion")
        super().__init__(**data)


class TimelineEventSchema(BaseModel):
    """A timeline event in detail page."""
    time: str = ""
    event: str = ""
    citation: str = ""

    def __init__(self, **data):
        if "date" in data and "time" not in data:
            data["time"] = data.pop("date")
        if "description" in data and "event" not in data:
            data["event"] = data.pop("description")
        super().__init__(**data)


class SourceDetailSchema(BaseModel):
    """A source detail entry."""
    id: int = 0
    platform: str = ""
    title: str = ""
    url: str = ""
    author: str = ""
    published_at: str = ""

    def __init__(self, **data):
        if "number" in data and "id" not in data:
            data["id"] = data.pop("number")
        super().__init__(**data)


class DetailGeneration(BaseModel):
    """AI output for detail page generation."""
    overview: str = Field(min_length=1)
    viewpoints: List[ViewpointSchema] = Field(default_factory=list)
    timeline: List[TimelineEventSchema] = Field(default_factory=list)
    sources: List[SourceDetailSchema] = Field(default_factory=list)


def _load_prompt_template(template_name: str) -> str:
    """Load prompt template from file."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / template_name
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def _format_sources_for_prompt(sources: List[Dict[str, Any]]) -> str:
    """
    Format source content items for inclusion in prompts.

    Args:
        sources: List of source content dicts with 'platform', 'title', 'cleaned_text'

    Returns:
        Formatted string for prompt insertion
    """
    formatted = []
    for i, source in enumerate(sources, 1):
        platform = source.get("platform", "unknown")
        title = source.get("title", "")
        text = source.get("cleaned_text", "")
        # Truncate individual source texts to keep prompt manageable
        if len(text) > 300:
            text = text[:300] + "..."
        formatted.append(f"来源{i}（{platform}）：标题：{title}\n内容：{text}")
    return "\n\n".join(formatted)


def generate_card(sources: List[Dict[str, Any]]) -> Optional[CardGeneration]:
    """
    Generate a hot card summary from one or more source content items.

    Constitution compliance:
    - Prompt loaded from external file (Principle V)
    - Try-except wrapping (Principle III)
    - Input truncation handled by client (Principle III)

    Args:
        sources: List of source content dicts with 'platform', 'title', 'cleaned_text'

    Returns:
        CardGeneration with title, summary, category, sources, or None if failed
    """
    config = get_config()

    # Dry-run mode: return mock data
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock card generation")
        mock_data = generate_mock_card()
        return CardGeneration(**mock_data)

    try:
        # Format sources for prompt
        sources_text = _format_sources_for_prompt(sources)

        # Load and format prompt
        template = _load_prompt_template("card_generation.txt")
        prompt = template.replace("{sources}", sources_text)

        # Call Qwen-Max (high quality model for generation)
        model = config.ai.models.get("generation", "qwen-max")
        response = call_qwen_api(prompt, model=model)

        if response is None:
            logger.warning("Card generation API call returned None")
            return None

        # Parse response
        result = parse_llm_response(response, CardGeneration)

        if result:
            # If AI didn't return sources, extract from input
            if not result.sources:
                platform_map = {
                    "hupu": "虎扑",
                    "dongqiudi": "懂球帝",
                    "bilibili": "B站",
                    "bing": "搜索引擎聚合",
                }
                result.sources = list(set(
                    platform_map.get(s.get("platform", ""), s.get("platform", ""))
                    for s in sources
                ))

            # Validate category
            valid_categories = ["转会传闻", "球队动态", "赛程赛制", "球迷讨论"]
            if result.category not in valid_categories:
                result.category = "球队动态"  # Default fallback

            logger.info(
                "Card generated",
                title=result.title,
                category=result.category,
                source_count=len(result.sources),
            )

        return result

    except Exception as e:
        logger.error(
            "Card generation failed",
            error=str(e),
            exc_info=True,
        )
        return None


def generate_detail(sources: List[Dict[str, Any]]) -> Optional[DetailGeneration]:
    """
    Generate a detailed page from source content items.

    Constitution compliance:
    - Prompt loaded from external file (Principle V)
    - Try-except wrapping (Principle III)
    - Inline citations required for all factual claims

    Args:
        sources: List of source content dicts with 'platform', 'title', 'cleaned_text',
                 'url', 'author', 'published_at'

    Returns:
        DetailGeneration with overview, viewpoints, timeline, sources, or None if failed
    """
    config = get_config()

    # Dry-run mode: return mock data
    if config.dry_run.enabled:
        logger.info("[DRY-RUN] Using mock detail generation")
        mock_data = generate_mock_detail()
        return DetailGeneration(**mock_data)

    try:
        # Format sources for prompt (include all metadata)
        formatted_parts = []
        source_list = []
        for i, source in enumerate(sources, 1):
            platform = source.get("platform", "unknown")
            title = source.get("title", "")
            text = source.get("cleaned_text", "")
            url = source.get("url", "")
            author = source.get("author", "")
            published_at = source.get("published_at", "")

            if len(text) > 500:
                text = text[:500] + "..."

            formatted_parts.append(
                f"来源[{i}]（{platform}）：\n"
                f"标题：{title}\n"
                f"作者：{author}\n"
                f"时间：{published_at}\n"
                f"内容：{text}\n"
                f"链接：{url}"
            )

            source_list.append({
                "id": i,
                "platform": platform,
                "title": title,
                "url": url,
                "author": author or "未知",
                "published_at": str(published_at) if published_at else "",
            })

        sources_text = "\n\n".join(formatted_parts)

        # Load and format prompt
        template = _load_prompt_template("detail_generation.txt")
        prompt = template.replace("{sources}", sources_text)

        # Call Qwen-Max (high quality for detail generation)
        model = config.ai.models.get("generation", "qwen-max")
        response = call_qwen_api(prompt, model=model)

        if response is None:
            logger.warning("Detail generation API call returned None")
            return None

        # Parse response
        result = parse_llm_response(response, DetailGeneration)

        # If parse fails (LLM returned Markdown instead of JSON), retry with stronger instruction
        if result is None:
            logger.warning("Detail parse failed, retrying with JSON enforcement")
            retry_prompt = (
                "请严格按照JSON格式重新输出上面的内容。不要使用Markdown，不要添加任何解释文字。"
                "只输出一个JSON对象，格式如下：\n"
                '{"overview": "...", "viewpoints": [...], "timeline": [...], "sources": [...]}\n'
                "原始内容：\n" + response[:800]
            )
            retry_response = call_qwen_api(retry_prompt, model=model)
            if retry_response:
                result = parse_llm_response(retry_response, DetailGeneration)

        if result:
            # If AI didn't return sources, use the ones we built
            if not result.sources:
                result.sources = [SourceDetailSchema(**s) for s in source_list]

            logger.info(
                "Detail generated",
                overview_length=len(result.overview),
                viewpoints_count=len(result.viewpoints),
                timeline_count=len(result.timeline),
            )

        return result

    except Exception as e:
        logger.error(
            "Detail generation failed",
            error=str(e),
            exc_info=True,
        )
        return None
