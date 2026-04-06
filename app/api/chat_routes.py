"""FastAPI routes for chat-based analytics."""

from __future__ import annotations

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.services.analytics_service import AnalyticsService


router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    conversation_id: str
    query: str


class ChatResponse(BaseModel):
    message: str
    sql_query: str | None = None
    chart: Optional[Any] = None
    report_pdf_base64: str | None = None


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
async def chat(
    payload: ChatRequest,
    service: AnalyticsService = Depends(get_analytics_service),
):
    """Main chat endpoint for conversational analytics."""
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    logger.info(
        "[chat] conversation_id=%s query=%s",
        payload.conversation_id,
        payload.query.strip()[:500],
    )

    result = service.run_chat_analysis(
        conversation_id=payload.conversation_id,
        user_query=payload.query.strip(),
    )

    return ChatResponse(
        message=result.get("message") or "",
        sql_query=result.get("sql_query"),
        chart=result.get("chart"),
        report_pdf_base64=result.get("report_pdf_base64"),
    )

