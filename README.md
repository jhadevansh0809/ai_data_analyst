# AI Data Analyst Backend

A production-style AI Data Analyst backend built with FastAPI, LangGraph, and OpenAI.

## Features

- Natural language to SQL query conversion
- SQL query validation and safety checks
- Automatic retry logic for failed queries
- Result analysis and insight generation
- Stateful workflow orchestration with LangGraph

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Create .env file in the project root
# Copy the example (if available) or create manually:
```

Create a `.env` file in the project root with:
```env
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini
PORT=8000

# LangSmith (optional - for tracing and monitoring)
LANGCHAIN_TRACING=true
LANGCHAIN_API_KEY=your_langsmith_api_key_here
LANGCHAIN_PROJECT=ai_data_analyst
```

**Important:** The application will automatically load variables from `.env` file. Make sure to set `DATABASE_URL` and `OPENAI_API_KEY` before running.

**LangSmith Setup (Optional):**
- Get your API key from https://smith.langchain.com
- Set `LANGCHAIN_TRACING=true` to enable tracing
- Set `LANGCHAIN_API_KEY` with your LangSmith API key
- Set `LANGCHAIN_PROJECT` to organize traces (default: "ai_data_analyst")
- View traces at https://smith.langchain.com

3. Set up the database:
   ```bash
   # Option 1: Using the Python script (recommended)
   python database_setup.py
   
   # Option 2: Using psql directly
   psql -U your_user -d your_database -f database_setup.sql
   ```
   
   This will create the required tables (`orders`, `cafes`, `vendors`) and populate them with sample data.

## Running the Application

### Option 1: Using the run script (Recommended)
```bash
python run.py
```

### Option 2: Using Python module syntax
```bash
python -m app.main
```

### Option 3: Using uvicorn directly
Make sure you're in the project root directory:
```bash
# From project root (d:\ai_data_analyst\)
python -m uvicorn app.main:app --reload
```

**Note:** If you get `ModuleNotFoundError: No module named 'app'`, make sure you're running from the project root directory where the `app` folder is located.

## API Endpoints

### POST /ask
Ask a question about your data.

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

### GET /health
Health check endpoint.

### GET /
API information endpoint.

## Architecture

- **LangGraph**: Orchestrates the stateful workflow
- **FastAPI**: REST API framework
- **SQLAlchemy**: Database ORM
- **OpenAI**: LLM for intent parsing, SQL generation, and result analysis
- **LangSmith**: Observability and tracing platform (optional)

## LangSmith Integration

LangSmith provides observability for your LLM applications. When enabled, you can:

- **View traces** of all LLM calls in real-time
- **Monitor performance** and latency
- **Debug issues** by seeing exact prompts and responses
- **Track costs** and token usage
- **Analyze patterns** across requests

### Setup:

1. Sign up at https://smith.langchain.com
2. Get your API key from the settings
3. Add to `.env`:
   ```env
   LANGCHAIN_TRACING=true
   LANGCHAIN_API_KEY=your_api_key_here
   LANGCHAIN_PROJECT=ai_data_analyst
   ```

4. Restart your server - traces will automatically appear in LangSmith dashboard

### What Gets Traced:

- Intent parsing LLM calls
- SQL generation LLM calls  
- Result analysis LLM calls
- Full workflow execution through LangGraph

## Workflow

1. Parse user question → structured intent JSON
2. Generate SQL query from intent
3. Validate SQL (safety checks, table restrictions, LIMIT enforcement)
4. Execute query (with retry logic)
5. Analyze results and generate insights
6. Format and return response

## Security

- Only SELECT statements allowed
- Restricted to specific tables (orders, cafes, vendors)
- Automatic LIMIT 100 enforcement
- No DDL/DML operations permitted

