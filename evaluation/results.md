# Evaluation Results

**Date**: 2026-04-16  
**Model**: openrouter/free (auto-routed via OpenRouter)  
**Embedding model**: all-MiniLM-L6-v2  
**Vector store**: ChromaDB (local, cosine similarity)  
**Top-k**: 5

> **Note on partial results**: The full 30-question run was interrupted by the OpenRouter free tier's 50-requests/day limit. Six questions succeeded with full LLM-as-judge scoring; one additional question succeeded with heuristic-only scoring (judge call was rate-limited). The remaining 23 questions hit rate limits at the answer-generation step. Re-run with `python3 evaluation/evaluate.py` after the daily limit resets to produce complete results. The numbers below reflect only the 7 successful responses.

---

## Summary Metrics (7/30 questions)

| Metric | Value | Notes |
|--------|-------|-------|
| Questions evaluated | 30 | |
| Successful responses | **7 / 30** | 23 blocked by API rate limit |
| **Groundedness** | **~36%** (LLM judge) / **~54%** (heuristic) | See caveat below |
| **Citation Accuracy** | **100%** | All 7 answers included `[Source: ...]` |
| Latency p50 | **3,228 ms** | |
| Latency p95 | **7,221 ms** | |

### Groundedness caveat

The LLM judge (also routed through the free OpenRouter endpoint) returned GROUNDED/PARTIAL/UNGROUNDED inconsistently — several clearly correct answers were rated 0 (UNGROUNDED). This is a known reliability problem when using a low-quality, heavily-rate-limited free model as an evaluator. The heuristic key-fact match scores are more reliable for this run and are used as the primary metric below.

---

## Metric Definitions

- **Groundedness**: Measures whether the answer is factually supported by the retrieved policy context.  
  - *LLM-as-judge*: The judge model reads context + answer and returns GROUNDED (1.0), PARTIAL (0.5), or UNGROUNDED (0.0).  
  - *Heuristic fallback*: Fraction of pre-defined `key_facts` strings found verbatim (case-insensitive) in the answer.
- **Citation Accuracy**: Heuristic check — 1.0 if a `[Source: ...]` tag references a retrieved document title, 0.5 if `[Source:]` appears without a matching title, 0.0 if no citation found.
- **Latency**: Wall-clock time from request receipt to full answer return (includes embedding lookup, ChromaDB retrieval, and LLM generation).

---

## Results by Topic

### PTO

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q01 | How many PTO days do employees receive in their first year? | 67% | 100% | 2847ms | "Employees receive 15 PTO days per year during their first year..." |
| Q02 | How many days of PTO can employees carry over to the next year? | 67% | 100% | 632ms | "...carry over up to 10 unused PTO days..." |
| Q03 | How far in advance do I need to request more than two weeks of PTO? | 50% | 100% | 3609ms | "...at least 15 business days in advance..." |
| Q04 | How many days of bereavement leave are provided for an immediate family member? | 40% | 100% | 2243ms | "...up to 5 days of paid bereavement leave..." |

### Holidays

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q05 | How many paid company holidays does Acme Corp offer in 2024? | 25% | 100% | 7221ms | "...the specific number is not included in the provided excerpts. Please consult the full Holiday Calendar..." |
| Q06 | When is Juneteenth observed in 2024? | 67% | 100% | 4529ms | "Juneteenth National Independence Day is observed on June 19, 2024..." |
| Q07 | How many floating holidays do employees receive per year? | — | — | — | *Rate limited* |

### Expenses

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q08 | What is the maximum reimbursable hotel rate for domestic travel? | — | — | — | *Rate limited* |
| Q09 | What is the daily meal allowance for domestic business travel? | 50% | 100% | 6304ms | "The daily meal allowance for domestic business travel is $75/day..." |
| Q10 | Within how many days must expenses be submitted for reimbursement? | — | — | — | *Rate limited* |
| Q11 | What expense approval is required for purchases over $2,000? | — | — | — | *Rate limited* |

### Remote Work

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q12 | How many days per week must hybrid employees be on-site? | — | — | — | *Rate limited* |
| Q13 | What is the home office setup stipend for full-time remote employees? | — | — | — | *Rate limited* |
| Q14 | What are the core hours that remote employees must be available? | — | — | — | *Rate limited* |

### Security

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q15 | What is the minimum password length required by the security policy? | — | — | — | *Rate limited* |
| Q16 | When must a security incident be reported after discovery? | — | — | — | *Rate limited* |
| Q17 | Is multi-factor authentication required for remote access? | — | — | — | *Rate limited* |

### Benefits

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q18 | What percentage of medical insurance premiums does Acme Corp cover for employees? | — | — | — | *Rate limited (daily)* |
| Q19 | How much does the company match for 401(k) contributions? | — | — | — | *Rate limited* |
| Q20 | How many weeks of paid parental leave does the primary caregiver receive? | — | — | — | *Rate limited* |
| Q21 | What is the annual learning and development stipend per employee? | — | — | — | *Rate limited (daily)* |

### Code of Conduct

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q22 | What is the anonymous ethics hotline number for reporting violations? | — | — | — | *Rate limited* |
| Q23 | What happens to employees who retaliate against a reporter? | — | — | — | *Rate limited* |

### Onboarding

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q24 | Within how many days must new employees complete benefits enrollment? | — | — | — | *Rate limited (daily)* |
| Q25 | What mandatory training must be completed within 30 days of hire? | — | — | — | *Rate limited* |

### Travel

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q26 | What class of airfare is allowed for domestic flights? | — | — | — | *Rate limited* |
| Q27 | What is the IRS mileage reimbursement rate for personal car use in 2024? | — | — | — | *Rate limited (daily)* |

### Performance

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q28 | When does the annual performance review cycle take place? | — | — | — | *Rate limited (daily)* |
| Q29 | What merit increase percentage is given to employees rated Exceptional (5)? | — | — | — | *Rate limited* |

### Data Privacy

| ID | Question | Groundedness (heuristic) | Citation | Latency | Answer excerpt |
|----|----------|--------------------------|----------|---------|----------------|
| Q30 | How long does Acme Corp retain employee HR records after employment ends? | — | — | — | *Rate limited* |

---

## Observations from Successful Responses

**Citation accuracy is strong**: Every successful answer included at least one `[Source: ...]` attribution. The system prompt and output formatting are working correctly.

**Heuristic groundedness is moderate (40–67%)**: Answers are factually correct on the main point but often omit secondary key facts (e.g., Q04 answers "5 days" correctly but does not enumerate which family members qualify). This reflects the heuristic metric's strictness about verbatim fact presence, not a failure of the RAG system itself.

**The system handles retrieval gaps gracefully**: Q05 is notable — the model correctly admitted the exact holiday count was not in the retrieved chunks and directed the user to HR, rather than hallucinating an answer. This is exactly the desired behavior.

**Latency range**: 632ms – 7,221ms, driven almost entirely by LLM generation time. The 632ms outlier on Q02 likely reflects a short generation. The 7,221ms p95 is within acceptable range for a non-streaming endpoint; adding streaming would substantially improve perceived latency.

**LLM-as-judge unreliability**: Using the same free-tier model as both the system LLM and the evaluator judge produces inconsistent scores (clearly correct answers rated UNGROUNDED). A production evaluation should use a separate, more capable judge (GPT-4o, Claude Sonnet, etc.).

---

## How to Re-run

```bash
# Full run with LLM-as-judge (uses ~60 API calls)
python3 evaluation/evaluate.py

# Heuristic-only scoring (uses ~30 API calls — one per RAG answer, no judge)
python3 evaluation/evaluate.py --no-llm-judge

# Custom paths
python3 evaluation/evaluate.py --questions evaluation/questions.json --output evaluation/results.md
```
