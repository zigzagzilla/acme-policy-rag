# Design and Evaluation Report
## Acme Corp Policy Assistant — RAG Application

**Project**: AI Engineering Practicum — Quantic Holdings  
**Date**: April 2026  
**Author**: Engineering Team

---

## 1. Executive Summary

This document describes the design, architecture, implementation decisions, and evaluation methodology for the Acme Corp Policy Assistant — a Retrieval-Augmented Generation (RAG) application that answers employee questions about HR policies using a curated document corpus. The system combines dense vector retrieval (ChromaDB + sentence-transformers) with an instruction-tuned language model (via OpenRouter) to produce grounded, cited answers.

Key results from the evaluation pilot (7 of 30 questions, remaining blocked by API rate limits):
- **Citation accuracy**: 100% — every answer included a `[Source: ...]` reference
- **Heuristic groundedness**: 40–67% per question (answers are factually correct on the main point; heuristic penalizes missing secondary facts)
- **Latency p50**: ~3.2 seconds; **p95**: ~7.2 seconds

---

## 2. System Architecture

```
User (browser)
    │  HTTP POST /chat  { "message": "..." }
    ▼
Flask app (app.py)
    │
    ▼
RAG Pipeline (rag.py)
    ├── 1. Embed query          sentence-transformers/all-MiniLM-L6-v2
    ├── 2. Retrieve top-k=5     ChromaDB (cosine similarity)
    ├── 3. Build context        Concatenate retrieved chunks w/ source metadata
    ├── 4. Generate answer      OpenRouter LLM (openrouter/free)
    └── 5. Return answer + sources
    │
    ▼
JSON response  { answer, sources, latency_ms, snippets }
```

### Component Summary

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Web framework | Flask | Minimal, well-understood, fast to iterate |
| Embedding model | all-MiniLM-L6-v2 | Runs locally, no API cost, strong semantic quality for short passages |
| Vector store | ChromaDB (local) | Zero infrastructure, file-based persistence, suitable for ≤100k chunks |
| LLM provider | OpenRouter (auto-route) | Aggregates many free/low-cost models; single API key; easy to swap models |
| Chunking strategy | Fixed-size 500 tokens, 100-token overlap | Balances context completeness vs. precision of retrieval |
| Similarity metric | Cosine | Standard for normalized embedding vectors |

---

## 3. Design Decisions

### 3.1 Chunking Strategy

Documents are split into 500-token chunks with a 100-token overlap. This was chosen because:

- **500 tokens** fits comfortably in both the retrieval context window and the embedding model's limit (256 word-pieces for MiniLM, but the sentence-splitter handles truncation gracefully).
- **100-token overlap** ensures that sentences spanning a chunk boundary are not lost from both chunks, reducing retrieval gaps at boundaries.
- An alternative — semantic paragraph splitting — was considered but not implemented, as the policy documents are already well-structured with clear section headings.

### 3.2 Top-k Retrieval

`TOP_K=5` chunks are retrieved per query. Increasing this would improve recall at the cost of:
- Larger context windows (higher token usage / cost)
- More noise injected into the generation prompt

Five chunks was chosen as a reasonable default; it can be tuned via the `TOP_K` environment variable without a code change.

### 3.3 Guardrails

The system prompt enforces two key constraints:
1. **Scope restriction**: The model is instructed to answer only from retrieved policy context and to explicitly state when information is not available rather than hallucinating.
2. **Citation requirement**: Every answer must include `[Source: <document title>]` references.

This was validated empirically: Q05 (holiday count) demonstrated the desired behavior when the retrieved chunks did not contain the specific fact — the model correctly said "the information is not in the excerpts" and redirected the user to HR.

### 3.4 LLM Provider Selection

The original design used Groq's free tier. This was switched to OpenRouter at the user's request, which provides:
- Access to multiple free-tier models under one API key
- Automatic model routing when a specific model is unavailable
- Model fallback list: `liquid/lfm-2.5-1.2b-instruct:free`, `liquid/lfm-2.5-1.2b-thinking:free`

**Limitation**: The free tier imposes a hard limit of 16 requests/minute and 50 requests/day, which is the primary constraint on evaluation throughput.

### 3.5 Ingest Pipeline

`ingest.py` processes 12 synthetic Acme Corp policy documents from the `policies/` directory and ingests 129 chunks into ChromaDB. Metadata stored per chunk:
- `source` (filename), `title` (human-readable), `chunk_id`, `total_chunks`

Re-ingestion is idempotent: the collection is cleared and rebuilt on each run.

---

## 4. Evaluation Design

### 4.1 Question Set

30 questions were authored across 10 policy topics (3 per topic on average):

| Topic | Questions | Example |
|-------|-----------|---------|
| PTO | Q01–Q04 | "How many PTO days do employees receive in their first year?" |
| Holidays | Q05–Q07 | "When is Juneteenth observed in 2024?" |
| Expenses | Q08–Q11 | "What is the maximum reimbursable hotel rate for domestic travel?" |
| Remote Work | Q12–Q14 | "What are the core hours that remote employees must be available?" |
| Security | Q15–Q17 | "What is the minimum password length required by the security policy?" |
| Benefits | Q18–Q21 | "How much does the company match for 401(k) contributions?" |
| Code of Conduct | Q22–Q23 | "What is the anonymous ethics hotline number?" |
| Onboarding | Q24–Q25 | "What mandatory training must be completed within 30 days?" |
| Travel | Q26–Q27 | "What class of airfare is allowed for domestic flights?" |
| Performance | Q28–Q29 | "When does the annual performance review cycle take place?" |
| Data Privacy | Q30 | "How long does Acme Corp retain employee HR records?" |

Questions were written to have specific, verifiable answers present in the policy corpus — each has a `key_facts` list of expected verbatim strings used for heuristic scoring.

### 4.2 Metrics

Three metrics were selected to cover the core dimensions of RAG quality:

**Groundedness** measures whether the generated answer is supported by retrieved context, not by LLM prior knowledge. It is the most important metric because unsupported answers represent hallucination risk.

- Primary: LLM-as-judge (GROUNDED / PARTIAL / UNGROUNDED classification)
- Fallback: Key-fact heuristic (fraction of `key_facts` strings found in the answer)

**Citation Accuracy** measures whether the answer correctly attributes information to the source document. This is important for user trust and auditability.

- Heuristic: Presence of a `[Source: <title>]` tag matching a retrieved document title

**Latency** measures end-to-end response time (p50 and p95). Acceptable thresholds for an internal HR tool: p50 < 5s, p95 < 15s.

### 4.3 LLM-as-Judge Design

The judge prompt presents the retrieved context, the question, and the answer, then asks for a one-word verdict. This mirrors published best practices (RAGAS, TruLens) for RAG evaluation. The key design choice was to separate the judge context from the full document corpus — the judge sees only what the RAG system retrieved, not the entire policy library, ensuring the metric reflects retrieval quality, not just LLM knowledge.

### 4.4 Known Evaluation Limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| Same model as judge and system | Judge may be biased toward its own style; free-tier models produce inconsistent verdicts | Use a separate, stronger judge model in production evaluation |
| Key-fact heuristic is strict | Correct paraphrased answers scored low (e.g., "five" vs. "5") | Supplement with semantic similarity (BERTScore) |
| Free API rate limits | Only 7/30 questions completed in full run | Re-run after daily limit resets; consider paid API access |
| 12 synthetic documents | Results may not generalize to real-world policy corpora | Replace with actual policy documents |

---

## 5. Evaluation Results

> Full results are in `evaluation/results.md`. This section summarizes the key findings from the 7 completed responses.

### 5.1 Citation Accuracy: 100%

All 7 answered questions included at least one `[Source: ...]` attribution referencing a retrieved document. This confirms the system prompt's citation constraint is being respected by the model.

### 5.2 Groundedness: 40–67% (heuristic)

The range reflects varying question complexity:
- Simple factual lookups (Q01, Q02, Q06): 67% — the model reliably included the primary fact
- Multi-fact questions (Q04, Q09): 40–50% — the model answered the main point but omitted secondary details

The LLM judge scores are not reliable in this run — several clearly correct answers (Q01, Q02, Q04) were scored UNGROUNDED. This failure mode is documented in the results and attributed to the low capability of the free-tier judge model.

### 5.3 Latency: 3.2s p50, 7.2s p95

Response times are dominated by LLM generation (typically 2–6s), with retrieval contributing <100ms. This is acceptable for an internal tool but would benefit from response streaming to reduce perceived latency.

### 5.4 Graceful Degradation (Q05)

Q05 asked for the exact number of paid holidays. The retrieved chunks referenced the Holiday Calendar document but did not include the specific count. Rather than fabricating an answer, the model explicitly stated the information was not in the excerpts and directed the user to consult the document or contact HR. This is the correct behavior for a grounded RAG system.

---

## 6. Strengths and Weaknesses

### Strengths

- **Citation accuracy**: Reliable source attribution builds user trust
- **Scope guardrails**: Model refuses to answer out-of-scope questions
- **Graceful retrieval failure**: Model communicates uncertainty rather than hallucinating
- **Modular architecture**: LLM, embedding model, and top-k are all environment-variable configurable
- **Local embeddings**: No API cost or latency for the retrieval step

### Weaknesses

- **LLM quality on free tier**: Free-tier models produce variable-quality answers and cannot reliably serve as their own judges
- **Chunking is not semantic**: Fixed-size chunking may split related policy clauses across chunk boundaries, reducing coherence of retrieved context
- **No re-ranking**: Top-k retrieval by cosine similarity alone may return less relevant chunks when multiple documents share similar vocabulary
- **No streaming**: Full answer must be generated before the response is sent, making latency more perceptible to users
- **Stateless chat**: Each query is independent; multi-turn conversational context is not maintained

---

## 7. Potential Improvements

### Near-term (low effort, high impact)

1. **Response streaming**: Add `stream=True` to the LLM call and use Server-Sent Events in the frontend. Eliminates the perception of latency for long answers.
2. **Re-ranking**: Add a cross-encoder re-ranker (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) after initial retrieval to improve chunk relevance before prompting.
3. **Conversation memory**: Store the last N turns in session and include them in the system context for multi-turn coherence.

### Medium-term

4. **Semantic chunking**: Split documents at paragraph or section boundaries rather than fixed token counts, preserving logical policy units.
5. **Hybrid retrieval**: Combine dense vector search (semantic) with BM25 (keyword) for better recall on queries containing specific numbers or proper nouns.
6. **Metadata filtering**: Allow users to scope queries to a specific policy domain (e.g., "only search Benefits documents") by adding ChromaDB metadata filters.

### Long-term

7. **Production LLM**: Replace the free-tier model with a production-grade model (GPT-4o-mini, Claude Haiku) for consistent quality and no rate limits.
8. **Dedicated evaluation infrastructure**: Use RAGAS or TruLens with a separate, stronger judge model for ongoing automated quality monitoring.
9. **Active learning loop**: Track questions the model could not answer and use them to identify gaps in the document corpus.

---

## 8. CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request:

1. **Install dependencies** (`pip install -r requirements.txt`)
2. **Lint** (`flake8` with line-length 120, skipping E501)
3. **Security scan** (`bandit -r . --skip B101`)
4. **Import smoke test** (verify `app`, `rag`, `ingest` modules import without error)

The evaluation script is deliberately excluded from CI due to API cost and rate-limit constraints. A separate scheduled workflow could run it nightly against a subset of questions using a paid API key.

---

## 9. Conclusion

The Acme Corp Policy Assistant demonstrates a functional, well-structured RAG system that correctly retrieves policy information, cites its sources, and refuses to answer questions outside its knowledge scope. The primary limitations are tied to the free-tier LLM provider — quality, rate limits, and judge reliability all improve with a production-grade model. The evaluation framework, question set, and metric definitions are all in place to support a full re-run as soon as the API rate limit resets.

The project successfully covers all five deliverables:

| Deliverable | Status | Location |
|-------------|--------|----------|
| Working RAG application | Complete | `app.py`, `rag.py`, `ingest.py` |
| Evaluation framework + results | Complete (partial data) | `evaluation/` |
| Design documentation | Complete | `design-and-evaluation.md` |
| AI tooling reflection | Complete | `ai-tooling.md` |
| CI/CD pipeline | Complete | `.github/workflows/ci.yml` |
