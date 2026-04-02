# AI Data Analyst — FastAPI + LangGraph + Gradio
FROM python:3.11-slim

WORKDIR /app

# libpq: Postgres client. Kaleido (Plotly PNG for PDFs) needs Chromium runtime libs on slim images.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm1 \
    libasound2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Use `python -m` so we never rely on a possibly broken /usr/local/bin/uvicorn entrypoint.
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
