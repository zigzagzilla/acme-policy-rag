# AI Tooling

This document describes the AI tools and models used during the development of the Acme Corp Policy Assistant RAG application, including what worked well and what didn't.

---

## Tools Used

### 1. Replit Agent (Primary Development Tool)

**What it is**: An AI coding agent integrated directly in the Replit IDE that autonomously plans, writes, and runs code.

**How it was used**:
- Designed the full project architecture (Flask + ChromaDB + sentence-transformers + OpenRouter)
- Authored all 12 synthetic policy documents
- Wrote all application code: `ingest.py`, `rag.py`, `app.py`, `templates/index.html`
- Wrote the evaluation script and ran it end-to-end
- Configured environment variables, workflow, and package dependencies
- Authored all documentation (`README.md`, `design-and-evaluation.md`, `ai-tooling.md`)
- Created the GitHub Actions CI/CD workflow

**What worked well**:
- Extremely fast iteration: from empty project to running application in a single session
- Effective at debugging dependency conflicts (ChromaDB + NumPy 2.0, OpenAI SDK version issues)
- Proactively identified and used OpenRouter's `openrouter/free` endpoint when named free model slugs were returning 404 errors
- Generated realistic, well-structured policy documents that read like actual corporate policies
- Implemented guardrails (out-of-corpus rejection, citation enforcement fallback) without being asked

**What didn't work well**:
- Several OpenRouter `:free` model slugs (e.g., `meta-llama/llama-3.1-8b-instruct:free`, `mistralai/mistral-7b-instruct:free`) returned 404 during testing, requiring probing to find working endpoints
- The `installLanguagePackages` callback in the Replit environment failed silently; had to fall back to `python3 -m pip install --break-system-packages` directly
- Gemma models returned errors when a system prompt was used (doesn't support the `system` role), requiring a model switch

---

### 2. OpenRouter (`openrouter/free`)

**What it is**: A unified API gateway for LLM inference that routes requests to the best available model. The `openrouter/free` endpoint auto-selects from currently available free models.

**How it was used**:
- Powers all user-facing question answering in the `/chat` endpoint
- Also used as LLM-as-judge in `evaluation/evaluate.py` to score groundedness

**What worked well**:
- `openrouter/free` provides a stable single endpoint that remains available even when specific named free models go offline
- OpenAI-compatible API made integration with the `openai` Python SDK trivial
- Responses are consistently fast (~2–4 seconds for RAG queries)
- Free tier requires no credit card and has reasonable rate limits for development and evaluation

**What didn't work well**:
- Named `:free` model slugs are frequently rate-limited (429) or removed (404), making direct model selection unreliable
- The free auto-routing endpoint may route to different models across requests, which can cause slight variation in answer style
- No streaming support on some free models

---

### 3. sentence-transformers (`all-MiniLM-L6-v2`)

**What it is**: A lightweight open-source embedding model from HuggingFace, runs entirely locally.

**How it was used**:
- Generates embeddings for all policy document chunks during ingestion
- Generates query embeddings at inference time for semantic similarity search in ChromaDB

**What worked well**:
- Completely free: no API key, no rate limits, no cost
- `all-MiniLM-L6-v2` is fast (~50ms per batch) and produces high-quality 384-dimensional embeddings
- Downloads automatically on first use (~90MB) and caches locally
- Excellent performance on English-language HR/policy document similarity tasks

**What didn't work well**:
- First run requires downloading the model (~90MB), which adds to initial startup time
- Requires local compute (CPU); on resource-constrained environments, embedding at ingestion time can be slow for large corpora

---

### 4. ChromaDB

**What it is**: An open-source embedding database with a simple Python API for storing and querying vector embeddings locally.

**How it was used**:
- Stores all 129 document chunk embeddings with metadata (source title, filename, chunk index)
- Performs cosine similarity search to retrieve the top-k most relevant chunks at query time

**What worked well**:
- Zero-configuration local setup — just a `PersistentClient` pointing at a directory
- Cosine similarity retrieval is fast and accurate for this corpus size
- Metadata filtering and result formatting are clean and Pythonic

**What didn't work well**:
- Version 0.5.0 (pre-installed in Replit) was incompatible with NumPy 2.0 (`np.float_` removed), requiring an upgrade to 1.5.7
- ChromaDB data is not committed to git (gitignored), so `ingest.py` must be re-run after cloning

---

## Summary

The combination of Replit Agent + OpenRouter (free) + sentence-transformers (local) + ChromaDB (local) enabled building a fully functional RAG application at zero monetary cost. The agent dramatically accelerated development, compressing what might have been 2–3 days of manual coding into a single automated session. The primary friction points were LLM endpoint instability on the free tier and Python environment dependency version conflicts, both of which were resolved through automated probing and targeted package upgrades.
