# AI Data Analyst

A production-style AI Data Analyst backend built with FastAPI, LangGraph, OpenAI, and a Gradio UI (`/ui`).

## Features

- Natural language to SQL query conversion
- SQL query validation and safety checks
- Automatic retry logic for failed queries
- Result analysis and insight generation
- Stateful workflow orchestration with LangGraph
- Chat API with charts and PDF reports

## Environment variables

Copy the template and fill in values (never commit real secrets):

```bash
cp .example.env .env
```

See **Configuration** below for what each key does. The application loads `.env` from the project root automatically.

---

## Run with Docker (recommended for servers / EC2)

**Prerequisites:** Docker and Docker Compose.

1. **Configure environment**

   ```bash
   cp .example.env .env
   ```


2. **Build and start**

   ```bash
   docker compose -f docker-compose.main.yaml up -d --build
   ```

3. **Initialize the database schema (first run only)**

   After containers are healthy, apply the SQL. Use the same user and database name as in `.env` (`POSTGRES_USER`, `POSTGRES_DB`):

   ```bash
   docker compose -f docker-compose.main.yaml exec -T db psql -U postgres -d ai_data_analyst < database_setup.sql
   ```

   Change `-U` and `-d` if your `.env` uses different values. If you expose Postgres on the host (for example with `docker-compose.local.yaml`), you can run the same file with a local `psql` client instead.

4. **Open the app**

   - API root: `http://<host>:8000/`
   - Gradio UI: `http://<host>:8000/ui`
   - Health: `GET http://<host>:8000/health`

**Notes**

- use `.example.env` as the key-only template.
- Rebuild the image after code changes: `docker compose -f docker-compose.main.yaml build --no-cache` then `up -d`.
- For local development with a bind-mounted `app/` folder, you can use `docker-compose.local.yaml` instead (exposes Postgres on 5432).

---

## Configuration (keys in `.example.env`)

| Key | Purpose |
|-----|--------|
| `BASE_URL` | Base URL for server-side HTTP calls from the UI to the API (include scheme and port). Default in code: `http://localhost:8000`. |
| `PORT` | Uvicorn listen port inside the container (Compose maps `8000:8000` by default). |
| `DATABASE_URL` | SQLAlchemy URL for Postgres. With Docker Compose, hostname is **`db`**. |
| `POSTGRES_USER` | Postgres superuser (used by the `db` service). |
| `POSTGRES_PASSWORD` | Postgres password. |
| `POSTGRES_DB` | Database name created on first start. |
| `OPENAI_API_KEY` | OpenAI API key (required). |
| `OPENAI_MODEL` | Model name (default `gpt-4o-mini`). |
| `LANGCHAIN_TRACING` | Set to `true` to enable LangSmith tracing. |
| `LANGCHAIN_API_KEY` | LangSmith API key (optional). |
| `LANGCHAIN_PROJECT` | LangSmith project name (optional). |
| `LANGCHAIN_ENDPOINT` | LangSmith API endpoint (optional; default used if unset). |

LangSmith’s UI uses the name “LangSmith”; this project still expects the **`LANGCHAIN_*`** environment variable names (LangChain’s convention), not `LANGSMITH_*`.

---

## Local development (without Docker)

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set up `.env` as above; for a local Postgres on your machine, use `localhost` in `DATABASE_URL`.

3. Initialize the database (creates tables and sample data):

   ```bash
   psql -U your_user -d your_database -f database_setup.sql
   ```

4. Run the app:

   ```bash
   python run.py
   ```

   Or:

   ```bash
   python -m app.main
   ```

   Or:

   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

If you see `ModuleNotFoundError: No module named 'app'`, run commands from the project root (the directory that contains the `app` package).

---

## API endpoints

### `GET /`

API metadata and links.

### `GET /health`

Health check for load balancers and monitoring.

### `POST /ask`

Ask a single question about your data.

**Request:**

```json
{
  "question": "What is the total revenue from orders last month?"
}
```

**Response:**

```json
{
  "answer": "Based on the query results...",
  "sql_query": "SELECT ... LIMIT 100",
  "error": null
}
```

### `POST /chat`

Chat-style analytics (used by the Gradio UI).

### `GET /ui`

Gradio web interface (mounted under `/ui`).

---

## Architecture

- **LangGraph**: Orchestrates the stateful workflow
- **FastAPI**: REST API
- **SQLAlchemy**: Database access
- **OpenAI**: LLM for intent, SQL, and analysis
- **LangSmith**: Optional tracing (via `LANGCHAIN_*` variables in `app/config.py`)

---

## LangSmith (optional)

1. Sign up at [LangSmith](https://smith.langchain.com) and create an API key.
2. In `.env`:

   ```env
   LANGCHAIN_TRACING=true
   LANGCHAIN_API_KEY=your_api_key_here
   LANGCHAIN_PROJECT=ai_data_analyst
   ```

3. Restart the app; traces appear in the LangSmith dashboard.

---

## Workflow

1. Parse user question → structured intent JSON  
2. Generate SQL from intent  
3. Validate SQL (safety, allowed tables, `LIMIT`)  
4. Execute query (with retries)  
5. Analyze results and produce insights  
6. Return response (and optional chart / PDF in chat flow)

---

## Security

- Only `SELECT` statements are allowed  
- Queries are restricted to approved tables  
- Automatic `LIMIT` enforcement  
- No DDL/DML in the analyst path  
