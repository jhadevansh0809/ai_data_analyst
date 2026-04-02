"""FastAPI main application."""
import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import gradio as gr

from app.api.chat_routes import router as chat_router
from app.config import config
from app.graph.builder import build_graph
from app.graph.state import AnalystState
from app.services.analytics_service import create_analytics_service
from app.ui.gradio_app import build_interface

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize LangSmith tracing if enabled
if config.LANGCHAIN_TRACING.lower() == "true":
    os.environ["LANGCHAIN_TRACING"] = "true"
    if config.LANGCHAIN_API_KEY:
        os.environ["LANGCHAIN_API_KEY"] = config.LANGCHAIN_API_KEY
    if config.LANGCHAIN_PROJECT:
        os.environ["LANGCHAIN_PROJECT"] = config.LANGCHAIN_PROJECT
    if config.LANGCHAIN_ENDPOINT:
        os.environ["LANGCHAIN_ENDPOINT"] = config.LANGCHAIN_ENDPOINT
    logger.info(f"[LangSmith] Tracing enabled. Project: {config.LANGCHAIN_PROJECT}")
else:
    logger.info("[LangSmith] Tracing disabled. Set LANGCHAIN_TRACING=true to enable.")


app = FastAPI(
    title="My Cafe Chain AI Data Analyst API",
    description="Cafe chain analytics backend with LangGraph and Gradio UI at /ui",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the graph once at startup
graph = build_graph()

# Create analytics service (chat pipeline wrapper)
analytics_service = create_analytics_service(graph)

# Inject analytics service into chat router and include it
setattr(chat_router, "analytics_service", analytics_service)
app.include_router(chat_router)

# Mount Gradio UI under /ui
demo = build_interface()
app = gr.mount_gradio_app(app, demo, path="/ui")


class AskRequest(BaseModel):
    """Request model for /ask endpoint."""

    question: str


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""

    answer: str
    sql_query: str | None = None
    error: str | None = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "My Cafe Chain AI Data Analyst API",
        "version": "1.0.0",
        "endpoints": {
            "GET /ui": "My Cafe Chain AI Data Analyst — Gradio UI",
            "POST /ask": "Ask a question about your data",
            "POST /chat": "Chat-based analytics with conversation, charts and reports",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/ask", response_model=AskResponse)
async def ask_question(request: AskRequest):
    """Main endpoint for asking questions (original pipeline)."""
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    user_question = request.question.strip()
    logger.info(f"[ask_question] Received question: {user_question}")

    # Initialize state
    initial_state: AnalystState = {
        "messages": [],
        "user_question": user_question,
        "intent": None,
        "sql_query": None,
        "validated_sql": None,
        "query_result": None,
        "insights": None,
        "error": None,
        "retry_count": 0,
    }

    logger.info(f"[ask_question] Initial state: {initial_state}")

    try:
        # Run the graph
        logger.info("[ask_question] Invoking graph...")
        final_state = graph.invoke(initial_state)
        logger.info("[ask_question] Graph execution completed")
        logger.info(f"[ask_question] Final state keys: {list(final_state.keys())}")
        logger.info(f"[ask_question] Final state error: {final_state.get('error')}")
        logger.info(f"[ask_question] Final state intent: {final_state.get('intent')}")
        logger.info(f"[ask_question] Final state sql_query: {final_state.get('sql_query')}")
        logger.info(f"[ask_question] Final state validated_sql: {final_state.get('validated_sql')}")

        # Extract response
        messages = final_state.get("messages", [])
        answer = messages[-1]["content"] if messages else "No response generated"
        logger.info(f"[ask_question] Answer: {answer[:200]}...")

        return AskResponse(
            answer=answer,
            sql_query=final_state.get("validated_sql"),
            error=final_state.get("error"),
        )
    except Exception as e:
        logger.error(f"[ask_question] Exception occurred: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


if __name__ == "__main__":
    import sys

    # Add project root to Python path when running directly
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=config.PORT, reload=True)

