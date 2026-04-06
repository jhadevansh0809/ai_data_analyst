"""Simple in-memory conversation manager.

This keeps lightweight state for each conversation so that
follow-up questions like "break it down by region" can be
interpreted in the context of earlier turns.

NOTE: This is intentionally simple and in-memory only. In a real
deployment, you would back this with Redis, a database, or a
vector store for persistence and scaling.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class ConversationTurn:
    """Represents a single QA turn in a conversation."""

    timestamp: datetime
    user_query: str
    sql_query: Optional[str] = None
    insights: Optional[str] = None
    chart_type: Optional[str] = None
    report_id: Optional[str] = None


@dataclass
class Conversation:
    """Represents a full conversation."""

    id: str
    turns: List[ConversationTurn] = field(default_factory=list)


class ConversationManager:
    """Manages conversations and provides simple context strings."""

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}
        self._lock = threading.Lock()

    def get_or_create(self, conversation_id: str) -> Conversation:
        """Get existing conversation or create a new one."""
        with self._lock:
            if conversation_id not in self._conversations:
                self._conversations[conversation_id] = Conversation(id=conversation_id)
            return self._conversations[conversation_id]

    def add_turn(
        self,
        conversation_id: str,
        user_query: str,
        sql_query: Optional[str] = None,
        insights: Optional[str] = None,
        chart_type: Optional[str] = None,
        report_id: Optional[str] = None,
    ) -> ConversationTurn:
        """Append a new turn to a conversation."""
        conv = self.get_or_create(conversation_id)
        turn = ConversationTurn(
            timestamp=datetime.utcnow(),
            user_query=user_query,
            sql_query=sql_query,
            insights=insights,
            chart_type=chart_type,
            report_id=report_id,
        )
        with self._lock:
            conv.turns.append(turn)
        return turn

    def get_context_summary(self, conversation_id: str, max_turns: int = 3) -> str:
        """Return a short text summary of recent turns for prompting.

        This is fed into the existing SQL / intent pipeline as additional
        context but does NOT change that pipeline's internal structure.
        """
        conv = self.get_or_create(conversation_id)
        if not conv.turns:
            return ""

        recent = conv.turns[-max_turns:]
        lines: List[str] = []
        for t in recent:
            lines.append(f"User: {t.user_query}")
            if t.sql_query:
                lines.append(f"SQL: {t.sql_query}")
            if t.insights:
                lines.append(f"Insight: {t.insights}")
        return "\n".join(lines)


# Singleton-style instance for easy importing
conversation_manager = ConversationManager()


