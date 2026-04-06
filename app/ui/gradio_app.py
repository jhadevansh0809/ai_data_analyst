"""Gradio UI for My Cafe Chain AI Data Analyst.

Chat interface for the FastAPI `/chat` endpoint: messages, Plotly charts, PDF download.
"""

from __future__ import annotations

import base64
import logging
import tempfile
from typing import List, Optional, Tuple

import gradio as gr
import plotly.graph_objects as go
import requests

from app.config import config
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

BACKEND_URL = config.BASE_URL

# When the UI is mounted in `app.main`, we inject the same AnalyticsService used by
# `POST /chat` so Gradio runs the pipeline in-process. Mis-set BASE_URL in Docker often
# makes HTTP self-requests miss this app, so graph/node logs never appear.
_analytics_service: Optional[AnalyticsService] = None


def set_analytics_service(service: AnalyticsService) -> None:
    """Register the shared analytics service (call from main.py before build_interface)."""
    global _analytics_service
    _analytics_service = service


def _call_backend(conversation_id: str, query: str) -> dict:
    """Run chat analysis: in-process when mounted in FastAPI, else HTTP to BASE_URL."""
    if _analytics_service is not None:
        logger.info(
            "[gradio] in-process chat conversation_id=%s query=%s",
            conversation_id,
            query[:500],
        )
        return _analytics_service.run_chat_analysis(conversation_id, query)

    url = f"{BACKEND_URL.rstrip('/')}/chat"
    payload = {"conversation_id": conversation_id, "query": query}
    resp = requests.post(url, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _prepare_download_after_chat(b64: str):
    """Decode PDF after each reply and attach it to DownloadButton so one user click downloads.

    If we only set the file on button-click, Gradio uses the first click to run the fn and
    the second click to actually download — pre-setting `value` avoids that.
    """
    if not (b64 or "").strip():
        return gr.update(value=None)
    try:
        raw = base64.b64decode(b64)
    except Exception:
        return gr.update(value=None)
    tmp = tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf",
        prefix="analyst_report_",
        mode="wb",
    )
    try:
        tmp.write(raw)
    finally:
        tmp.close()
    return gr.update(value=tmp.name)


def _apply_cafe_plot_theme(fig: go.Figure) -> go.Figure:
    """Light chart chrome — bright plot area; dark text for contrast vs the dark app shell."""
    _paper = "#fafaf9"
    _plot = "#ffffff"
    _text = "#292524"
    _muted = "#57534e"
    _grid = "rgba(0, 0, 0, 0.08)"
    _line = "#a8a29e"
    _title = "#c2410c"

    is_table = bool(fig.data) and getattr(fig.data[0], "type", None) == "table"
    if is_table:
        fig.update_layout(
            paper_bgcolor=_paper,
            plot_bgcolor=_plot,
            font=dict(color=_text, family="system-ui, -apple-system, sans-serif"),
            title_font=dict(color=_title),
        )
        return fig

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor=_paper,
        plot_bgcolor=_plot,
        font=dict(color=_text, family="system-ui, -apple-system, sans-serif"),
        title_font=dict(color=_title),
        legend=dict(font=dict(color=_muted)),
    )
    fig.update_xaxes(
        tickfont=dict(color=_muted),
        title_font=dict(color=_text),
        linecolor=_line,
        gridcolor=_grid,
    )
    fig.update_yaxes(
        tickfont=dict(color=_muted),
        title_font=dict(color=_text),
        linecolor=_line,
        gridcolor=_grid,
    )
    return fig


def _chart_from_response(chart_data: dict | None) -> go.Figure | None:
    """Convert backend chart JSON to a Plotly Figure if possible."""
    if not chart_data:
        return None

    if chart_data.get("type") == "table":
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
        return _apply_cafe_plot_theme(fig)

    if "data" in chart_data and "layout" in chart_data:
        fig = go.Figure(chart_data)
        return _apply_cafe_plot_theme(fig)

    return None


# Non-empty placeholder so Chatbot does not render a blank assistant bubble while waiting.
_ASSISTANT_PENDING_REPLY = "Thinking…"


def add_user_message(message: str, history: List[Tuple[str, str]] | None):
    """Append the user's message immediately; assistant side shows until the reply replaces it."""
    history = history or []
    if message:
        history.append((message, _ASSISTANT_PENDING_REPLY))
    return "", history


def send_suggestion(text: str, history: List[Tuple[str, str]] | None) -> Tuple[str, List[Tuple[str, str]]]:
    """Append a canned suggestion as a user turn (same as typing + Send)."""
    history = history or []
    if text:
        history.append((text, _ASSISTANT_PENDING_REPLY))
    return "", history


def chat_fn(
    history: List[Tuple[str, str]] | None,
    conversation_id: str,
):
    """Call backend for the latest user message and update the last turn with the reply."""
    history = history or []
    empty_b64 = ""
    if not history:
        return history, conversation_id, None, empty_b64

    last_user_message = history[-1][0]

    if not conversation_id:
        conversation_id = "conv-" + str(len(history))

    try:
        backend_resp = _call_backend(conversation_id, last_user_message)
        reply_text = backend_resp.get("message") or ""
        chart_json = backend_resp.get("chart")
        report_b64 = backend_resp.get("report_pdf_base64") or ""

        fig = _chart_from_response(chart_json)

        history[-1] = (last_user_message, reply_text)
        return history, conversation_id, fig, report_b64
    except Exception as e:
        error_msg = f"Backend error: {e}"
        history[-1] = (last_user_message, error_msg)
        return history, conversation_id, None, empty_b64


# Header: simple sans for the brand line; warm “kitchen” colors (no italic).
_TITLE_HTML = """
<div style="text-align:center;padding:1.1rem 0.5rem 1.25rem;margin-bottom:0.35rem;border-bottom:1px solid rgba(251,146,60,0.22);">
  <div style="line-height:1.3;">
    <span style="
      font-family:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',sans-serif;
      font-style:normal;
      font-weight:700;
      font-size:clamp(1.5rem,3.6vw,2.05rem);
      letter-spacing:-0.02em;
      background:linear-gradient(100deg,#ea580c 0%,#f59e0b 100%);
      -webkit-background-clip:text;
      background-clip:text;
      -webkit-text-fill-color:transparent;
      color:#f97316;
    " title="Café &amp; food service analytics">My Cafe Chain</span><span style="
      font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;
      font-weight:600;
      font-size:clamp(1.1rem,2.6vw,1.65rem);
      color:#fef3c7;
      letter-spacing:-0.03em;
    "> AI Data Analyst</span>
  </div>
  <p style="margin:0.65rem 0 0;font-size:0.95rem;color:#d6d3d1;max-width:36rem;margin-left:auto;margin-right:auto;">
    Ask in plain language about <strong style="color:#e7e5e4;">sales</strong>, <strong style="color:#e7e5e4;">your locations</strong>, and <strong style="color:#e7e5e4;">suppliers</strong> — get answers, charts, and a PDF you can download.
  </p>
</div>
"""

# Warm dark UI: charcoal-brown surfaces, cream text (WCAG-friendly on these browns).
_BG_DEEP = "#2c2825"
_BG_PAGE = "#3a3532"
_BG_CARD = "#454039"
_BG_INPUT = "#3f3a36"
_TEXT = "#fafaf9"
_TEXT_SOFT = "#e7e5e4"
_TEXT_MUTED = "#d6d3d1"
_BORDER = "#6b6560"
_BORDER_SOFT = "#57534e"
_ACCENT_ORANGE = "#ea580c"

_CAFE_UI_CSS = f"""
:root {{
    color-scheme: dark !important;
    --cafe-text: {_TEXT};
    --cafe-text-soft: {_TEXT_SOFT};
    --cafe-border: {_BORDER};
}}
.gradio-container {{
    background: linear-gradient(165deg, {_BG_DEEP} 0%, {_BG_PAGE} 55%, #3d3834 100%) !important;
    max-width: 100%;
}}
.gradio-container {{
    --body-background-fill: {_BG_PAGE} !important;
    --background-fill-primary: {_BG_CARD} !important;
    --background-fill-secondary: #4a4540 !important;
    --border-color-primary: {_BORDER_SOFT} !important;
    --body-text-color: {_TEXT} !important;
    --body-text-color-subdued: {_TEXT_MUTED} !important;
    --color-text-heading: #fef3c7 !important;
    --button-primary-background-fill: {_ACCENT_ORANGE} !important;
    --button-primary-text-color: #fffbeb !important;
    --button-secondary-background-fill: #57534e !important;
    --button-secondary-text-color: {_TEXT} !important;
    --input-background-fill: {_BG_INPUT} !important;
    --shadow-drop: 0 4px 20px rgba(0,0,0,0.25) !important;
    --chatbot-user-message-background-fill: rgba(194, 65, 12, 0.4) !important;
    --chatbot-bot-message-background-fill: rgba(47, 43, 40, 0.95) !important;
    --color-text-placeholder: #a8a29e !important;
}}
.gradio-container h1, .gradio-container h2, .gradio-container h3 {{
    color: #fef3c7 !important;
    font-weight: 600 !important;
}}
/* Conversation panel shell */
.cafe-chat-wrap {{
    border: 1px solid {_BORDER} !important;
    border-radius: 14px !important;
    background: {_BG_CARD} !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2), inset 0 1px 0 rgba(255,255,255,0.04) !important;
    padding: 4px !important;
}}
/* Wrappers: no border/bg — avoids double frame with inner .message bubble */
#cafe-chatbot .message-wrap.user,
#cafe-chatbot .message-wrap.bot {{
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}}
/* Chat bubbles: single border on inner .message only; compact padding */
#cafe-chatbot .message.user {{
    background: linear-gradient(165deg, rgba(194, 65, 12, 0.42) 0%, rgba(124, 45, 18, 0.5) 100%) !important;
    border: 1px solid rgba(251, 146, 60, 0.65) !important;
    border-radius: 10px !important;
    color: #fffbeb !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2) !important;
    padding: 0.2rem 0.4rem !important;
    margin: 0.1rem 0 !important;
}}
#cafe-chatbot .message.user * {{
    color: #fffbeb !important;
}}
#cafe-chatbot .message.bot,
#cafe-chatbot .message.assistant {{
    background: rgba(47, 43, 40, 0.95) !important;
    border: 1px solid #6b6560 !important;
    border-radius: 10px !important;
    color: #fafaf9 !important;
    border-left: 3px solid #34d399 !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
    padding: 0.2rem 0.4rem !important;
    margin: 0.1rem 0 !important;
}}
#cafe-chatbot .message.bot *,
#cafe-chatbot .message.assistant * {{
    color: #fafaf9 !important;
}}
#cafe-chatbot .message .prose,
#cafe-chatbot .message .markdown-body,
#cafe-chatbot .message p {{
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.4 !important;
}}
#cafe-chatbot [class*="message-row"],
#cafe-chatbot [class*="chatbot"] .wrap {{
    gap: 0.25rem !important;
}}
/* Same bubbles when id lives on inner node only */
.cafe-chat-wrap .message-wrap.user,
.cafe-chat-wrap .message-wrap.bot {{
    border: none !important;
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
}}
.cafe-chat-wrap .message.user {{
    background: linear-gradient(165deg, rgba(194, 65, 12, 0.42) 0%, rgba(124, 45, 18, 0.5) 100%) !important;
    border: 1px solid rgba(251, 146, 60, 0.65) !important;
    border-radius: 10px !important;
    color: #fffbeb !important;
    padding: 0.2rem 0.4rem !important;
    margin: 0.1rem 0 !important;
}}
.cafe-chat-wrap .message.bot {{
    background: rgba(47, 43, 40, 0.95) !important;
    border: 1px solid #6b6560 !important;
    border-radius: 10px !important;
    color: #fafaf9 !important;
    border-left: 3px solid #34d399 !important;
    padding: 0.2rem 0.4rem !important;
    margin: 0.1rem 0 !important;
}}
/* Input: label + field clearly visible on dark UI */
#cafe-message-input label,
#cafe-message-input .label-wrap,
#cafe-message-input .label-wrap span {{
    color: #fef3c7 !important;
    font-weight: 600 !important;
    opacity: 1 !important;
}}
/* Message field: compact single-line feel (Gradio often ignores rows; we force height) */
#cafe-message-input.block,
.cafe-msg-input.block {{
    min-height: unset !important;
}}
/* Your message: comfortable typing height (not the tiny chat-bubble padding) */
.cafe-msg-input textarea,
#cafe-message-input textarea {{
    color: #fafaf9 !important;
    border-radius: 8px !important;
    background: #2d2825 !important;
    border: 1px solid #d6d3d1 !important;
    caret-color: #fde68a !important;
    min-height: 3.25rem !important;
    max-height: 10rem !important;
    line-height: 1.45 !important;
    padding: 0.5rem 0.65rem !important;
    resize: vertical !important;
    box-shadow: none !important;
    overflow-y: auto !important;
}}
.cafe-msg-input input,
#cafe-message-input input {{
    color: #fafaf9 !important;
    border-radius: 8px !important;
    background: #2d2825 !important;
    border: 1px solid #d6d3d1 !important;
}}
.cafe-msg-input textarea::placeholder,
#cafe-message-input textarea::placeholder {{
    color: #a8a29e !important;
    opacity: 1 !important;
}}
.cafe-msg-input:focus-within,
#cafe-message-input:focus-within {{
    border: 1px solid #e7e5e4 !important;
    box-shadow: none !important;
    outline: none !important;
}}
.cafe-msg-input:focus-within textarea,
#cafe-message-input:focus-within textarea {{
    border-color: #fb923c !important;
    outline: none !important;
}}
.cafe-msg-input {{
    border: 1px solid #d6d3d1 !important;
    border-radius: 10px !important;
    background: {_BG_INPUT} !important;
    box-shadow: none !important;
    margin-top: 0.75rem !important;
    padding: 4px 6px 6px !important;
}}
/* Sidebar */
.cafe-insights {{
    border: 1px solid {_BORDER} !important;
    border-radius: 14px !important;
    background: {_BG_CARD} !important;
    padding: 0.75rem 1rem 1rem !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.18) !important;
}}
.cafe-insights .prose, .cafe-insights .markdown-body {{
    color: {_TEXT_SOFT} !important;
}}
/* Scope blurb — compact strip under the title */
.cafe-scope-top {{
    max-width: min(92rem, 98%) !important;
    width: 100% !important;
    margin: 0 auto 0.45rem auto !important;
    padding: 0.35rem 0.65rem 0.4rem !important;
    border-radius: 8px !important;
    border: 1px solid rgba(251, 146, 60, 0.18) !important;
    background: rgba(69, 64, 57, 0.45) !important;
    box-shadow: none !important;
}}
.cafe-scope-top .markdown-body, .cafe-scope-top .prose, .cafe-scope-panel.cafe-scope-top {{
    color: {_TEXT_MUTED} !important;
    font-size: 0.8rem !important;
    line-height: 1.32 !important;
}}
.cafe-scope-top p {{
    margin: 0 !important;
}}
.cafe-scope-panel, .cafe-scope-panel .markdown-body, .cafe-scope-panel .prose {{
    color: {_TEXT_SOFT} !important;
    font-size: 0.88rem !important;
    line-height: 1.45 !important;
}}
.cafe-scope-panel h3 {{
    color: #fef3c7 !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    margin: 0.35rem 0 0.4rem !important;
}}
.cafe-scope-panel h3:first-child {{
    margin-top: 0 !important;
}}
.cafe-scope-panel ul {{
    margin: 0.2rem 0 0.5rem 1.1rem !important;
    padding: 0 !important;
}}
.cafe-scope-panel li {{
    margin-bottom: 0.25rem !important;
}}
.cafe-scope-panel p {{
    margin: 0.35rem 0 !important;
}}
.cafe-scope-panel strong {{
    color: #fef3c7 !important;
    font-weight: 600 !important;
}}
.cafe-scope-panel code {{
    background: rgba(0,0,0,0.25) !important;
    padding: 0.1rem 0.35rem !important;
    border-radius: 4px !important;
    font-size: 0.82rem !important;
}}
.cafe-plot-wrap {{
    border: 1px solid #d6d3d1 !important;
    border-radius: 12px !important;
    background: #fafaf9 !important;
    padding: 0.5rem !important;
    margin-top: 0.25rem !important;
}}
.cafe-main-col .block-label {{
    color: #fde68a !important;
}}
footer {{ opacity: 0.45; color: {_TEXT_MUTED} !important; }}
/* Quick suggestion chips above the message field */
.cafe-suggestions-label p {{
    margin: 0.35rem 0 0.25rem !important;
    font-size: 0.82rem !important;
    color: {_TEXT_MUTED} !important;
    font-weight: 600 !important;
}}
.cafe-suggestions-row {{
    flex-wrap: wrap !important;
    gap: 0.4rem !important;
    margin-bottom: 0.15rem !important;
}}
.cafe-suggestions-row button {{
    font-size: 0.78rem !important;
    padding: 0.55rem 0.95rem !important;
    min-height: unset !important;
    line-height: 1.35 !important;
}}
"""

# What the app knows — shown in the UI so visitors understand scope before chatting.
_SCOPE_MARKDOWN = """
**What this is**  
A simple assistant for your café chain: you ask in everyday language, and it helps you understand **sales**, **each location**, and **who supplies you**.

**What it can answer**  
Anything that fits that picture — trends, comparisons, totals — and you may see a chart or download a short PDF summary on the right.
"""

# Short example queries shown above the message box (click to fill the input).
_CHAT_SUGGESTIONS: Tuple[str, ...] = (
    "Last four months order sales graph",
    "Cafe-wise sales breakdown",
    "Top vendors by orders",
)


def build_interface() -> gr.Blocks:
    """Build the full Gradio UI."""
    with gr.Blocks(
        title="My Cafe Chain AI Data Analyst",
        theme=gr.themes.Soft(primary_hue="orange", neutral_hue="stone"),
        css=_CAFE_UI_CSS,
        head='<meta name="color-scheme" content="dark" /><meta name="theme-color" content="#3a3532" />',
    ) as demo:
        gr.HTML(_TITLE_HTML)
        gr.Markdown(
            _SCOPE_MARKDOWN,
            elem_classes=["cafe-scope-panel", "cafe-scope-top"],
        )

        with gr.Row():
            with gr.Column(scale=2, elem_classes=["cafe-main-col"]):
                chatbot = gr.Chatbot(
                    label="Conversation",
                    type="tuples",
                    height=500,
                    elem_id="cafe-chatbot",
                    elem_classes=["cafe-chat-wrap"],
                )
                gr.Markdown(
                    "Try asking",
                    elem_classes=["cafe-suggestions-label"],
                )
                suggestion_buttons: List[gr.Button] = []
                with gr.Row(elem_classes=["cafe-suggestions-row"]):
                    for suggestion_text in _CHAT_SUGGESTIONS:
                        suggestion_buttons.append(
                            gr.Button(
                                suggestion_text,
                                size="sm",
                                variant="secondary",
                            )
                        )
                msg = gr.Textbox(
                    placeholder="e.g. Show top-selling items by location this month",
                    label="Your message",
                    lines=1,
                    max_lines=5,
                    elem_id="cafe-message-input",
                    elem_classes=["cafe-msg-input"],
                )
                conversation_id_state = gr.State("")

                send_btn = gr.Button("Send", variant="primary")

            with gr.Column(scale=1, elem_classes=["cafe-insights"]):
                gr.Markdown("### Chart")
                chart_plot = gr.Plot(
                    label="Visualization",
                    elem_classes=["cafe-plot-wrap"],
                )
                gr.Markdown("### Report")
                report_pdf_b64 = gr.State("")
                download_btn = gr.DownloadButton(label="Download PDF", variant="secondary")

        for btn, fill_text in zip(suggestion_buttons, _CHAT_SUGGESTIONS):
            btn.click(
                lambda hist, t=fill_text: send_suggestion(t, hist),
                inputs=[chatbot],
                outputs=[msg, chatbot],
            ).then(
                chat_fn,
                inputs=[chatbot, conversation_id_state],
                outputs=[chatbot, conversation_id_state, chart_plot, report_pdf_b64],
            ).then(
                _prepare_download_after_chat,
                inputs=[report_pdf_b64],
                outputs=[download_btn],
            )

        send_btn.click(
            add_user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        ).then(
            chat_fn,
            inputs=[chatbot, conversation_id_state],
            outputs=[chatbot, conversation_id_state, chart_plot, report_pdf_b64],
        ).then(
            _prepare_download_after_chat,
            inputs=[report_pdf_b64],
            outputs=[download_btn],
        )

        msg.submit(
            add_user_message,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
        ).then(
            chat_fn,
            inputs=[chatbot, conversation_id_state],
            outputs=[chatbot, conversation_id_state, chart_plot, report_pdf_b64],
        ).then(
            _prepare_download_after_chat,
            inputs=[report_pdf_b64],
            outputs=[download_btn],
        )

    return demo


if __name__ == "__main__":
    demo = build_interface()
    demo.launch()
