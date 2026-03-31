"""Gradio UI for the Chat-Based AI Data Analyst.

This provides a modern chat interface that talks to the FastAPI backend
`/chat` endpoint and displays:
- conversational messages
- automatically generated charts (via Plotly)
- a link to download the latest PDF report
"""

from __future__ import annotations

import json
from typing import List, Tuple

import gradio as gr
import plotly.graph_objects as go
import requests

from app.config import config


BACKEND_URL = f"http://localhost:{config.PORT}"


def _call_backend(conversation_id: str, query: str) -> dict:
    """Call the FastAPI /chat endpoint."""
    url = f"{BACKEND_URL}/chat"
    payload = {"conversation_id": conversation_id, "query": query}
    resp = requests.post(url, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _chart_from_response(chart_data: dict | None) -> go.Figure | None:
    """Convert backend chart JSON to a Plotly Figure if possible.

    - If chart_data looks like a Plotly figure dict (has 'data' and 'layout'),
      we reconstruct a Figure.
    - If it's a table-type JSON, we show a simple textual placeholder;
      the raw table can be displayed in the future as a dedicated component.
    """
    if not chart_data:
        return None

    # Backend table fallback
    if chart_data.get("type") == "table":
        # Represent table as a basic Plotly table
        columns = chart_data.get("columns", [])
        rows = chart_data.get("rows", [])
        values = [[row.get(col) for row in rows] for col in columns]
        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(values=columns),
                    cells=dict(values=values),
                )
            ]
        )
        fig.update_layout(title=chart_data.get("title") or "Table")
        return fig

    # Assume proper Plotly figure dict
    if "data" in chart_data and "layout" in chart_data:
        return go.Figure(chart_data)

    return None


def add_user_message(message: str, history: List[Tuple[str, str]] | None):
    """Append the user's message to the chat immediately (with empty assistant reply)."""
    history = history or []
    if message:
        history.append((message, ""))
    # Clear the textbox and update history
    return "", history


def chat_fn(
    history: List[Tuple[str, str]] | None,
    conversation_id: str,
):
    """Call backend for the latest user message and update the last turn with the reply."""
    history = history or []
    if not history:
        return history, conversation_id, None, ""

    last_user_message = history[-1][0]

    # Ensure we have a conversation id
    if not conversation_id:
        conversation_id = "conv-" + str(len(history))

    try:
        backend_resp = _call_backend(conversation_id, last_user_message)
        reply_text = backend_resp.get("message") or ""
        chart_json = backend_resp.get("chart")
        report_url = backend_resp.get("report_download_url") or ""

        fig = _chart_from_response(chart_json)

        history[-1] = (last_user_message, reply_text)
        return history, conversation_id, fig, report_url
    except Exception as e:
        error_msg = f"Backend error: {e}"
        history[-1] = (last_user_message, error_msg)
        return history, conversation_id, None, ""


def build_interface() -> gr.Blocks:
    """Build the full Gradio UI."""
    with gr.Blocks(title="AI Data Analyst") as demo:
        gr.Markdown("## AI Data Analyst\nChat with your data, get visual insights, and download reports.")

        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Chat",
                    type="tuples",
                    height=500,
                )
                msg = gr.Textbox(
                    placeholder="Ask a question about your data, e.g., 'Show monthly revenue'",
                    label="Your message",
                )
                conversation_id_state = gr.State("")

                send_btn = gr.Button("Send", variant="primary")

            with gr.Column(scale=1):
                gr.Markdown("### Chart")
                chart_plot = gr.Plot(label="Visualization")
                gr.Markdown("### Report")
                report_link = gr.Textbox(
                    label="Download URL",
                    interactive=False,
                    placeholder="Will appear after the first answer.",
                )

        # 1) First add the user message to the chat immediately,
        # 2) Then call the backend to fill in the assistant reply + chart + report link.
        send_btn.click(
            add_user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        ).then(
            chat_fn,
            inputs=[chatbot, conversation_id_state],
            outputs=[chatbot, conversation_id_state, chart_plot, report_link],
        )

        msg.submit(
            add_user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        ).then(
            chat_fn,
            inputs=[chatbot, conversation_id_state],
            outputs=[chatbot, conversation_id_state, chart_plot, report_link],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    # Gradio will run its own local server (default port 7860)
    demo.launch()


