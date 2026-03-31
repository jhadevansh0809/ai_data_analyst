"""FastAPI routes for chat-based analytics."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str
    query: str


class ChatResponse(BaseModel):
    message: str
    sql_query: str | None = None
    # Use a broad type here; we already ensure JSON-serializability
    # in the analytics service via fastapi.encoders.jsonable_encoder.
    chart: Optional[Any] = None
    report_download_url: str | None = None


def get_analytics_service() -> AnalyticsService:
    """Dependency placeholder; the actual instance is injected from main.py.

    main.py will set router.analytics_service at startup so that this
    dependency can access the compiled graph-backed service.
    """
    service: Optional[AnalyticsService] = getattr(router, "analytics_service", None)
    if service is None:
        raise HTTPException(status_code=500, detail="Analytics service not initialized")
    return service


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, service: AnalyticsService = Depends(get_analytics_service)):
    """Main chat endpoint for conversational analytics."""
    if not request.query or not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    result = service.run_chat_analysis(
        conversation_id=request.conversation_id,
        user_query=request.query.strip(),
    )

    report_id = result.get("report_id")
    report_download_url = f"/reports/{report_id}" if report_id else None

    return ChatResponse(
        message=result.get("message") or "",
        sql_query=result.get("sql_query"),
        chart=result.get("chart"),
        report_download_url=report_download_url,
    )


