"""Detail page API endpoints."""
import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.hot_card import HotCard
from src.models.topic_cluster import TopicCluster
from src.models.detail_page import DetailPage
from src.models.source_content import SourceContent
from src.ai.generation import generate_detail

logger = get_logger(__name__)

router = APIRouter(prefix="/api/cards", tags=["details"])


class DetailResponse(BaseModel):
    """Response model for detail page."""
    success: bool = True
    data: dict
    timestamp: str


@router.get("/{card_id}/detail", response_model=DetailResponse)
def get_card_detail(
    card_id: int,
    db: Session = Depends(get_db),
):
    """
    Get detailed AI-generated content for a specific hot topic.

    Generates on-demand (lazy generation) and caches for 1 hour.

    Args:
        card_id: Hot card ID
        db: Database session

    Returns:
        DetailResponse with overview, viewpoints, timeline, sources
    """
    # Get the card
    card = db.query(HotCard).filter_by(id=card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")

    # Check if detail page exists and is cached
    detail = db.query(DetailPage).filter_by(cluster_id=card.cluster_id).first()

    if detail and detail.cached_until > datetime.now():
        # Return cached detail
        try:
            viewpoints = json.loads(detail.viewpoints) if detail.viewpoints else []
            timeline = json.loads(detail.timeline) if detail.timeline else []
            sources = json.loads(detail.sources) if detail.sources else []
        except json.JSONDecodeError:
            viewpoints = []
            timeline = []
            sources = []

        return DetailResponse(
            data={
                "id": detail.id,
                "card": {
                    "title": card.title,
                    "credibility": card.credibility,
                    "generated_at": card.generated_at.isoformat() if card.generated_at else "",
                },
                "overview": detail.overview,
                "viewpoints": viewpoints,
                "timeline": timeline,
                "sources": sources,
            },
            timestamp=datetime.now().isoformat(),
        )

    # Generate new detail page (lazy generation)
    # Get all source content for this cluster
    source_items = db.query(SourceContent).filter_by(
        cluster_id=card.cluster_id,
    ).order_by(SourceContent.published_at.asc()).all()

    if not source_items:
        raise HTTPException(status_code=404, detail="No source content found for this card")

    # Prepare source data for generation
    source_data = []
    for item in source_items:
        source_data.append({
            "platform": item.platform,
            "title": item.title,
            "cleaned_text": item.cleaned_text,
            "url": item.url,
            "author": item.author or "未知",
            "published_at": item.published_at.isoformat() if item.published_at else "",
        })

    # Generate detail content
    detail_result = generate_detail(source_data)

    if detail_result is None:
        raise HTTPException(status_code=500, detail="Failed to generate detail content")

    # Serialize JSON fields
    viewpoints_json = json.dumps(
        [v.model_dump() for v in detail_result.viewpoints],
        ensure_ascii=False,
    )
    timeline_json = json.dumps(
        [t.model_dump() for t in detail_result.timeline],
        ensure_ascii=False,
    )
    sources_json = json.dumps(
        [s.model_dump() for s in detail_result.sources],
        ensure_ascii=False,
    )

    # Create or update detail page
    if detail:
        detail.overview = detail_result.overview
        detail.viewpoints = viewpoints_json
        detail.timeline = timeline_json
        detail.sources = sources_json
        detail.generated_at = datetime.now()
        detail.cached_until = datetime.now() + timedelta(hours=1)
    else:
        detail = DetailPage(
            cluster_id=card.cluster_id,
            overview=detail_result.overview,
            viewpoints=viewpoints_json,
            timeline=timeline_json,
            sources=sources_json,
            generated_at=datetime.now(),
            cached_until=datetime.now() + timedelta(hours=1),
        )
        db.add(detail)

    db.commit()

    logger.info(
        "Detail page generated",
        card_id=card_id,
        cluster_id=card.cluster_id,
        overview_length=len(detail_result.overview),
    )

    return DetailResponse(
        data={
            "id": detail.id,
            "card": {
                "title": card.title,
                "credibility": card.credibility,
                "generated_at": card.generated_at.isoformat() if card.generated_at else "",
            },
            "overview": detail_result.overview,
            "viewpoints": [v.model_dump() for v in detail_result.viewpoints],
            "timeline": [t.model_dump() for t in detail_result.timeline],
            "sources": [s.model_dump() for s in detail_result.sources],
        },
        timestamp=datetime.now().isoformat(),
    )
