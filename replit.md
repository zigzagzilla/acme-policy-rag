# Acme Corp Policy Assistant — RAG Application

## Project Overview

A Retrieval-Augmented Generation (RAG) application built as an educational AI Engineering project. Answers employee questions about company policies using a vector-search-backed LLM pipeline.

## Architecture

- **Embeddings**: `sentence-transformers` (`all-MiniLM-L6-v2`) — runs locally, no API needed
- **Vector Store**: ChromaDB (persistent, local at `./chroma_db/`)
- **LLM**: OpenRouter API (`openrouter/free` by default, auto-routes to best available free model)
- **Web Framework**: Flask on port 5000
- **Policy Corpus**: 12 synthetic Acme Corp policy documents in `./policies/`

## Key Files

| File | Purpose |
|---|---|
| `app.py` | Flask app — endpoints: `/`, `/chat` (POST), `/health` |
| `rag.py` | RAG pipeline — retrieval, prompt building, LLM call, guardrails |
| `ingest.py` | Ingestion script — parse, chunk, embed, store in ChromaDB |
| `policies/` | 12 Markdown policy documents (corpus) |
| `templates/index.html` | Chat UI |
| `requirements.txt` | Pinned Python dependencies |
| `.env.example` | Environment variable template |

## Environment Variables

Set via Replit Secrets / env vars:

| Variable | Value | Notes |
|---|---|---|
| `OPENAI_API_KEY` | (secret) | OpenRouter API key |
| `LLM_BASE_URL` | `https://openrouter.ai/api/v1` | OpenRouter base URL |
| `LLM_MODEL` | `openrouter/free` | Auto-routes to best free model |
| `LLM_API_KEY_ENV` | `OPENAI_API_KEY` | Which secret to use |
| `TOP_K` | `5` | Chunks retrieved per query |
| `CHUNK_SIZE` | `500` | Words per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `PORT` | `5000` | Flask port (required for Replit webview) |

## Workflow

**Start application**: `python3 app.py` on port 5000

## Setup Steps

After clone or environment reset:
1. `python3 ingest.py` — re-indexes documents into ChromaDB
2. Workflow auto-starts the Flask app

## Important Notes

- ChromaDB data is stored in `./chroma_db/` (gitignored, must run `ingest.py` after fresh clone)
- The embedding model (`all-MiniLM-L6-v2`) downloads automatically on first use (~90MB)
- `openrouter/free` auto-selects the best available free model; fallback models are configured in `rag.py`
- OpenAI Python SDK 2.x is used (pointing at OpenRouter's OpenAI-compatible endpoint)
