"""Health check API endpoints."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/health", tags=["health"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    message: str


@router.get("/", response_model=HealthResponse)
def health_check():
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return HealthResponse(
        status="healthy",
        message="World Cup Monitor API is running"
    )
