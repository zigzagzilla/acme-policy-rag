# Acme Corp Policy Assistant

A Retrieval-Augmented Generation (RAG) application that answers employee questions about company policies. Built with Flask, ChromaDB, sentence-transformers, and OpenRouter (free LLM API).

## Live Demo

The app is publicly hosted and ready to use — no setup required:

**[https://ai-rag-exercise.replit.app](https://ai-rag-exercise.replit.app)**

Try asking it questions like:
- *"How many PTO days do new employees get?"*
- *"What is the travel reimbursement limit for flights?"*
- *"What are the password requirements?"*

## Architecture

- **Embeddings**: `all-MiniLM-L6-v2` via sentence-transformers (local, free)
- **Vector Store**: ChromaDB (local persistent storage)
- **LLM**: OpenRouter free tier (`meta-llama/llama-3.1-8b-instruct:free`)
- **Framework**: Flask (Python)
- **Corpus**: 12 synthetic Acme Corp policy documents (Markdown)

## Setup

> **Just want to try it?** Use the [live demo](https://ai-rag-exercise.replit.app) above — no installation needed.

### 1. Prerequisites

- Python 3.10+
- A free [OpenRouter](https://openrouter.ai) API key (or Groq key)

### 2. Clone and create virtual environment

```bash
git clone https://github.com/zigzagzilla/acme-policy-rag
cd acme-policy-rag
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and set your API key:

```
OPENAI_API_KEY=your_openrouter_api_key_here
LLM_BASE_URL=https://openrouter.ai/api/v1
LLM_API_KEY_ENV=OPENAI_API_KEY
LLM_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

To use **Groq** instead, set:
```
OPENAI_API_KEY=your_groq_key
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=llama-3.1-8b-instant
```

### 5. Ingest policy documents

This parses, chunks, embeds, and indexes all policy documents into ChromaDB:

```bash
python ingest.py
```

Expected output:
```
Loading embedding model: all-MiniLM-L6-v2
Connecting to ChromaDB at: ./chroma_db
Ingesting: benefits_policy.md → 8 chunks
...
✓ Ingestion complete: 10 documents, 74 chunks indexed.
```

### 6. Run the application

```bash
python app.py
```

The app will be available at `http://localhost:5000`.

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Web chat interface |
| `/chat` | POST | RAG query API — accepts `{"question": "..."}`, returns answer with citations |
| `/health` | GET | Health check — returns index status and config |

### Example `/chat` request

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many PTO days do new employees get?"}'
```

### Example `/health` response

```json
{
  "status": "healthy",
  "indexed_chunks": 74,
  "index_ready": true,
  "llm_configured": true,
  "model": "meta-llama/llama-3.1-8b-instruct:free",
  "embed_model": "all-MiniLM-L6-v2"
}
```

## Policy Documents

Located in `./policies/`:

| File | Policy |
|---|---|
| `pto_policy.md` | Paid Time Off — accrual, carryover, bereavement |
| `holiday_calendar.md` | 2024 company holidays and floating holidays |
| `expense_policy.md` | Expense reimbursement limits and procedures |
| `remote_work_policy.md` | Remote and hybrid work arrangements |
| `security_policy.md` | Information security and password requirements |
| `it_usage_policy.md` | Acceptable use of IT systems |
| `code_of_conduct.md` | Workplace behavior and ethics |
| `onboarding_guide.md` | First-day setup and onboarding milestones |
| `travel_policy.md` | Business travel booking and limits |
| `performance_review_policy.md` | Review cycle, ratings, and merit increases |
| `data_privacy_policy.md` | Data handling, retention, and employee rights |
| `benefits_policy.md` | Health insurance, 401(k), parental leave |

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Default | Description |
|---|---|---|
| `OPENAI_API_KEY` | *(required)* | OpenRouter (or Groq) API key |
| `LLM_BASE_URL` | OpenRouter URL | LLM API base URL |
| `LLM_MODEL` | `meta-llama/llama-3.1-8b-instruct:free` | Model name |
| `TOP_K` | `5` | Number of chunks retrieved per query |
| `CHUNK_SIZE` | `500` | Approximate words per chunk |
| `CHUNK_OVERLAP` | `100` | Overlapping words between chunks |

## Fixed Seeds

`ingest.py` sets `random.seed(42)` for deterministic sampling where applicable.

## Project Structure

```
├── app.py              # Flask web application
├── rag.py              # RAG pipeline (retrieval + generation)
├── ingest.py           # Document ingestion and indexing
├── requirements.txt    # Python dependencies (pinned)
├── .env.example        # Environment variable template
├── README.md           # This file
├── policies/           # Policy corpus (Markdown)
├── templates/
│   └── index.html      # Chat UI
└── chroma_db/          # ChromaDB vector store (auto-generated, gitignored)
```
