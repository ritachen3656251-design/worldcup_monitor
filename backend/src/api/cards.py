"""Cards API endpoints."""
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime

from src.core.database import get_db
from src.core.logging import get_logger
from src.models.source_content import SourceContent
from src.models.hot_card import HotCard
from src.models.topic_cluster import TopicCluster

logger = get_logger(__name__)

router = APIRouter(prefix="/api", tags=["cards"])


class HotCardResponse(BaseModel):
    """Response model for hot topic cards (Spec 2+)."""
    id: int
    title: str
    summary: str
    category: str
    credibility: str
    sources: List[str]
    image_url: Optional[str] = None
    hotness_score: float
    generated_at: str

    class Config:
        from_attributes = True


class SourceContentResponse(BaseModel):
    """Response model for source content (Spec 1: raw content list)."""
    id: int
    platform: str
    url: str
    title: str
    cleaned_text: str
    author: Optional[str]
    published_at: str
    interaction_count: int
    scraped_at: str

    class Config:
        from_attributes = True


class CardsListResponse(BaseModel):
    """Response wrapper for cards list."""
    success: bool = True
    data: dict
    timestamp: str


class CategoryResponse(BaseModel):
    """Response model for category."""
    name: str
    count: int


class CategoriesListResponse(BaseModel):
    """Response wrapper for categories list."""
    success: bool = True
    data: dict
    timestamp: str


@router.get("/cards", response_model=CardsListResponse)
def get_cards(
    category: str = Query(default="全部", description="Channel filter"),
    limit: int = Query(default=20, ge=1, le=50, description="Number of cards"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    """
    Get hot topic cards for discovery feed (Spec 2+).

    Falls back to raw content if no HotCards exist yet (Spec 1 compatibility).

    Args:
        category: Channel filter category
        limit: Maximum number of items to return
        offset: Pagination offset
        db: Database session

    Returns:
        List of hot cards or raw source content
    """
    # Check if we have any HotCards
    card_count = db.query(func.count(HotCard.id)).scalar()

    if card_count > 0:
        # Spec 2+: Return HotCards
        query = db.query(HotCard).join(
            TopicCluster,
            HotCard.cluster_id == TopicCluster.id,
        ).filter(TopicCluster.archived == False)

        # Apply category filter
        if category not in ("全部",):
            if category == "热门":
                # "热门" = top cards by hotness
                query = query.order_by(HotCard.hotness_score.desc())
            else:
                query = query.filter(HotCard.category == category)

        # Default sort by hotness
        query = query.order_by(HotCard.hotness_score.desc())

        # Get total count for pagination
        total = query.count()

        # Apply pagination
        items = query.offset(offset).limit(limit).all()

        cards = []
        for item in items:
            try:
                source_labels = json.loads(item.source_labels)
            except (json.JSONDecodeError, TypeError):
                source_labels = []

            cards.append(HotCardResponse(
                id=item.id,
                title=item.title,
                summary=item.summary,
                category=item.category,
                credibility=item.credibility,
                sources=source_labels,
                image_url=item.image_url,
                hotness_score=item.hotness_score,
                generated_at=item.generated_at.isoformat() if item.generated_at else "",
            ))

        return CardsListResponse(
            data={
                "cards": [c.model_dump() for c in cards],
                "total": total,
                "has_more": (offset + limit) < total,
            },
            timestamp=datetime.now().isoformat(),
        )

    else:
        # Spec 1 fallback: Return raw SourceContent
        query = db.query(SourceContent).filter(
            SourceContent.archived == False,
        ).order_by(SourceContent.scraped_at.desc())

        total = query.count()
        items = query.offset(offset).limit(limit).all()

        cards = []
        for item in items:
            cards.append({
                "id": item.id,
                "title": item.title,
                "summary": item.cleaned_text[:200] + "..." if len(item.cleaned_text) > 200 else item.cleaned_text,
                "category": "球队动态",
                "credibility": "待确认",
                "sources": [item.platform],
                "image_url": None,
                "hotness_score": float(item.interaction_count),
                "generated_at": item.scraped_at.isoformat() if item.scraped_at else "",
            })

        return CardsListResponse(
            data={
                "cards": cards,
                "total": total,
                "has_more": (offset + limit) < total,
            },
            timestamp=datetime.now().isoformat(),
        )


@router.get("/categories", response_model=CategoriesListResponse)
def get_categories(db: Session = Depends(get_db)):
    """
    Get available channel categories with card counts.

    Returns:
        List of categories with their card counts
    """
    # Define all categories
    all_categories = ["全部", "热门", "转会传闻", "球队动态", "赛程赛制", "球迷讨论"]

    # Get total active cards
    total = db.query(func.count(HotCard.id)).join(
        TopicCluster,
        HotCard.cluster_id == TopicCluster.id,
    ).filter(TopicCluster.archived == False).scalar()

    categories = [{"name": "全部", "count": total}]

    # "热门" = same as total (top cards sorted by hotness)
    categories.append({"name": "热门", "count": min(total, 10)})

    # Count per category
    for cat in ["转会传闻", "球队动态", "赛程赛制", "球迷讨论"]:
        count = db.query(func.count(HotCard.id)).join(
            TopicCluster,
            HotCard.cluster_id == TopicCluster.id,
        ).filter(
            TopicCluster.archived == False,
            HotCard.category == cat,
        ).scalar()
        categories.append({"name": cat, "count": count})

    return CategoriesListResponse(
        data={"categories": categories},
        timestamp=datetime.now().isoformat(),
    )


@router.get("/cards/new", response_model=CardsListResponse)
def get_new_cards(
    since: str = Query(..., description="ISO 8601 timestamp"),
    category: str = Query(default="全部", description="Channel filter"),
    db: Session = Depends(get_db),
):
    """
    Check for new hot topic cards since a given timestamp.

    Used by frontend polling service for real-time updates.

    Args:
        since: ISO 8601 timestamp - only return cards generated after this time
        category: Channel filter category
        db: Database session

    Returns:
        List of new cards since the given timestamp
    """
    try:
        since_dt = datetime.fromisoformat(since.replace("Z", "+00:00").replace("+00:00", ""))
    except (ValueError, TypeError):
        try:
            since_dt = datetime.fromisoformat(since)
        except Exception:
            since_dt = datetime.now()

    query = db.query(HotCard).join(
        TopicCluster,
        HotCard.cluster_id == TopicCluster.id,
    ).filter(
        HotCard.generated_at > since_dt,
        TopicCluster.archived == False,
    )

    if category not in ("全部",):
        if category != "热门":
            query = query.filter(HotCard.category == category)

    query = query.order_by(HotCard.generated_at.desc())
    items = query.all()

    cards = []
    for item in items:
        try:
            source_labels = json.loads(item.source_labels)
        except (json.JSONDecodeError, TypeError):
            source_labels = []

        cards.append({
            "id": item.id,
            "title": item.title,
            "summary": item.summary,
            "category": item.category,
            "credibility": item.credibility,
            "sources": source_labels,
            "image_url": item.image_url,
            "hotness_score": item.hotness_score,
            "generated_at": item.generated_at.isoformat() if item.generated_at else "",
        })

    return CardsListResponse(
        data={
            "cards": cards,
            "total": len(cards),
            "has_more": False,
        },
        timestamp=datetime.now().isoformat(),
    )
