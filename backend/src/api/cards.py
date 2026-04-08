"""Cards API endpoints."""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from src.core.database import get_db
from src.models.source_content import SourceContent

router = APIRouter(prefix="/api/cards", tags=["cards"])


class SourceContentResponse(BaseModel):
    """Response model for source content (Spec 1: raw content list)."""
    id: int
    platform: str
    url: str
    title: str
    cleaned_text: str
    author: str | None
    published_at: str
    interaction_count: int
    scraped_at: str

    class Config:
        from_attributes = True


@router.get("/", response_model=List[SourceContentResponse])
def get_cards(
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """
    Get raw source content list (Spec 1: minimal pipeline).

    Args:
        limit: Maximum number of items to return
        db: Database session

    Returns:
        List of source content items
    """
    # Query raw content, ordered by scraped time (newest first)
    items = db.query(SourceContent)\
        .filter(SourceContent.archived == False)\
        .order_by(SourceContent.scraped_at.desc())\
        .limit(limit)\
        .all()

    # Convert to response format
    results = []
    for item in items:
        results.append(SourceContentResponse(
            id=item.id,
            platform=item.platform,
            url=item.url,
            title=item.title,
            cleaned_text=item.cleaned_text[:200] + "..." if len(item.cleaned_text) > 200 else item.cleaned_text,
            author=item.author,
            published_at=item.published_at.isoformat(),
            interaction_count=item.interaction_count,
            scraped_at=item.scraped_at.isoformat(),
        ))

    return results
