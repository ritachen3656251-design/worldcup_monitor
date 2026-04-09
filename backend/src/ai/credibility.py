"""Credibility scoring using Qwen AI."""
from typing import Optional, List, Dict, Any
from pathlib import Path
from pydantic import BaseModel, Field

from src.ai.client import call_qwen_api, parse_llm_response
from src.core.config import get_config
from src.core.logging import get_logger

logger = get_logger(__name__)

# Source authority weights
SOURCE_WEIGHTS = {
    "hupu": 3.0,
    "dongqiudi": 3.0,
    "bilibili": 2.0,
    "bing": 1.0,
}

# Platform display name mapping
PLATFORM_NAMES = {
    "hupu": "虎扑",
    "dongqiudi": "懂球帝",
    "bilibili": "B站",
    "bing": "搜索引擎聚合",
}


class CredibilityScore(BaseModel):
    """AI output for credibility scoring."""
    credibility: str = Field(pattern=r"^(可信|待确认|传闻)$")
    reason: str = Field(min_length=1, max_length=200)


def _load_prompt_template() -> str:
    """Load credibility scoring prompt template from file."""
    prompt_path = Path(__file__).parent.parent.parent / "prompts" / "credibility_scoring.txt"
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


def calculate_credibility(
    sources: List[Dict[str, Any]],
    summary: str = "",
) -> Optional[CredibilityScore]:
    """
    Calculate credibility score using multi-factor analysis.

    Uses both algorithmic scoring and optional AI refinement.

    Constitution compliance:
    - Multi-factor scoring (source authority + multi-source verification)
    - Defensive engineering (try-except wrapping)

    Args:
        sources: List of source content dicts with 'platform', 'title', etc.
        summary: Card summary for AI context

    Returns:
        CredibilityScore with credibility label and reason, or None if failed
    """
    config = get_config()

    try:
        # Algorithmic multi-factor scoring
        if not sources:
            return CredibilityScore(credibility="传闻", reason="无来源数据")

        # Factor 1: Source authority score
        authority_score = sum(
            SOURCE_WEIGHTS.get(s.get("platform", ""), 1.0)
            for s in sources
        )

        # Factor 2: Multi-source verification bonus
        unique_platforms = set(s.get("platform", "") for s in sources)
        multi_source_bonus = 1.5 if len(unique_platforms) >= 2 else 1.0

        # Factor 3: Source count factor
        source_count_factor = min(len(sources) / 2, 2.0)

        # Calculate total score
        total = authority_score * multi_source_bonus * source_count_factor

        # Determine credibility label
        if total >= 8:
            credibility = "可信"
            reason = f"多来源验证（{len(unique_platforms)}个平台），权威性高"
        elif total >= 4:
            credibility = "待确认"
            if len(unique_platforms) == 1:
                platform_name = PLATFORM_NAMES.get(
                    list(unique_platforms)[0],
                    list(unique_platforms)[0]
                )
                reason = f"单一来源（{platform_name}），需进一步确认"
            else:
                reason = f"来源可信度中等，建议关注后续报道"
        else:
            credibility = "传闻"
            reason = "信源权威性较低，仅供参考"

        # Special case: Bing-only sources always "待确认"
        if unique_platforms == {"bing"}:
            credibility = "待确认"
            reason = "搜索引擎聚合来源，需进一步核实"

        # Special case: Single source always at most "待确认"
        if len(sources) == 1:
            if credibility == "可信":
                credibility = "待确认"
                reason = "单一来源，待其他来源确认"

        result = CredibilityScore(credibility=credibility, reason=reason)

        logger.info(
            "Credibility calculated",
            credibility=result.credibility,
            source_count=len(sources),
            platforms=list(unique_platforms),
            total_score=total,
        )

        return result

    except Exception as e:
        logger.error(
            "Credibility scoring failed",
            error=str(e),
            exc_info=True,
        )
        return CredibilityScore(credibility="待确认", reason="评估异常，默认待确认")
