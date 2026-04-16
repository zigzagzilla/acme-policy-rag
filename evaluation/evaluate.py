"""
Evaluation script for the Acme Corp Policy Assistant RAG system.

Metrics:
  - Groundedness:    % of answers factually supported by retrieved context (LLM-as-judge)
  - Citation Accuracy: % of answers with at least one correctly attributed [Source:] citation
  - Latency:         p50 and p95 response time in milliseconds

Usage:
    python evaluation/evaluate.py
    python evaluation/evaluate.py --questions evaluation/questions.json --output evaluation/results.md
"""

import sys
import os
import json
import time
import argparse
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402
load_dotenv()

from rag import answer_question, get_embed_model, get_collection  # noqa: E402

RANDOM_SEED = 42


def score_citation_accuracy(answer: str, sources: list) -> float:
    """
    Heuristic citation accuracy: check that the answer contains at least one
    [Source: ...] reference matching a retrieved source title.
    Returns 1.0 if any retrieved source title appears in a [Source:] tag, else 0.0.
    """
    if not sources:
        return 0.0
    answer_lower = answer.lower()
    for src in sources:
        title_lower = src["title"].lower()
        key_word = title_lower.split()[0] if title_lower else ""
        if key_word and "source:" in answer_lower and key_word in answer_lower:
            return 1.0
    if "[source:" in answer_lower:
        return 0.5
    return 0.0


def score_groundedness_heuristic(answer: str, key_facts: list) -> float:
    """
    Heuristic groundedness: check what fraction of the provided key facts
    appear (case-insensitive) in the answer.
    """
    if not key_facts:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for fact in key_facts if fact.lower() in answer_lower)
    return round(hits / len(key_facts), 4)


def score_groundedness_llm(question: str, answer: str, context: str, client, model: str) -> float:
    """
    LLM-as-judge groundedness: ask the LLM to assess whether the answer is
    factually grounded in the provided context. Returns 1.0, 0.5, or 0.0.
    """
    judge_prompt = f"""You are evaluating whether a RAG system answer is grounded in the provided context.

QUESTION: {question}

CONTEXT (retrieved policy excerpts):
{context[:2000]}

ANSWER TO EVALUATE:
{answer[:800]}

Task: Decide if the answer is factually supported by the context above.
- Reply GROUNDED if the answer is fully supported by the context.
- Reply PARTIAL if the answer is partly supported but adds unverified information.
- Reply UNGROUNDED if the answer contains significant claims not in the context.

Reply with exactly one word: GROUNDED, PARTIAL, or UNGROUNDED."""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": judge_prompt}],
            max_tokens=10,
            temperature=0.0,
        )
        verdict = response.choices[0].message.content.strip().upper()
        if "GROUNDED" in verdict and "PARTIAL" not in verdict and "UN" not in verdict:
            return 1.0
        elif "PARTIAL" in verdict:
            return 0.5
        else:
            return 0.0
    except Exception as e:
        print(f"    [LLM judge error: {e}] — falling back to heuristic")
        return None


def build_context_from_result(result: dict) -> str:
    """Build a context string from the snippets returned by the RAG pipeline."""
    snippets = result.get("snippets", [])
    parts = []
    for s in snippets:
        parts.append(f"[{s['source_title']}]: {s['text']}")
    return "\n\n".join(parts)


def run_evaluation(questions_path: str, output_path: str, use_llm_judge: bool = True):
    import openai

    with open(questions_path, "r") as f:
        questions = json.load(f)

    print(f"Running evaluation on {len(questions)} questions...\n")

    api_key_env = os.getenv("LLM_API_KEY_ENV", "OPENAI_API_KEY")
    api_key = os.getenv(api_key_env, "")
    base_url = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    judge_model = os.getenv("LLM_MODEL", "openrouter/free")

    llm_client = openai.OpenAI(api_key=api_key, base_url=base_url)

    print("Pre-loading embedding model and ChromaDB...")
    get_embed_model()
    get_collection()
    print("Ready.\n")

    results = []
    latencies = []

    groundedness_scores = []
    citation_scores = []

    for i, q in enumerate(questions, 1):
        qid = q["id"]
        question = q["question"]
        topic = q.get("topic", "General")
        key_facts = q.get("key_facts", [])

        print(f"[{i:02d}/{len(questions)}] ({topic}) {question}")

        retries = 3
        result = None
        for attempt in range(retries):
            try:
                result = answer_question(question)
                break
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt < retries - 1:
                    wait_s = 65 * (attempt + 1)
                    print(f"    Rate limit hit, waiting {wait_s}s before retry {attempt+2}/{retries}...")
                    time.sleep(wait_s)
                else:
                    print(f"    ERROR: {e}")
                    results.append({
                        "id": qid, "topic": topic, "question": question,
                        "answer": f"ERROR: {e}", "sources": [], "latency_ms": 0,
                        "groundedness": 0.0, "citation_accuracy": 0.0, "error": True,
                    })
                    result = None
                    break
        if result is None:
            continue

        answer = result["answer"]
        sources = result.get("sources", [])
        latency_ms = result.get("latency_ms", 0)
        latencies.append(latency_ms)

        heuristic_ground = score_groundedness_heuristic(answer, key_facts)

        llm_ground = None
        if use_llm_judge and sources:
            context = build_context_from_result(result)
            llm_ground = score_groundedness_llm(question, answer, context, llm_client, judge_model)
            time.sleep(0.5)

        final_groundedness = llm_ground if llm_ground is not None else heuristic_ground

        citation_acc = score_citation_accuracy(answer, sources)

        groundedness_scores.append(final_groundedness)
        citation_scores.append(citation_acc)

        judge_label = "LLM" if llm_ground is not None else "heuristic"
        ground_pct = round(final_groundedness * 100)
        cite_pct = round(citation_acc * 100)
        print(f"    Latency: {latency_ms}ms | Groundedness: {ground_pct}% ({judge_label}) | Citation: {cite_pct}%")

        results.append({
            "id": qid,
            "topic": topic,
            "question": question,
            "answer": answer,
            "sources": [s["title"] for s in sources],
            "latency_ms": latency_ms,
            "groundedness": final_groundedness,
            "groundedness_method": judge_label,
            "heuristic_groundedness": heuristic_ground,
            "citation_accuracy": citation_acc,
            "error": False,
        })

        time.sleep(4)

    total = len(results)
    valid = [r for r in results if not r.get("error")]
    n_valid = len(valid)

    avg_groundedness = round(statistics.mean(r["groundedness"] for r in valid) * 100, 1) if valid else 0
    avg_citation = round(statistics.mean(r["citation_accuracy"] for r in valid) * 100, 1) if valid else 0

    latency_p50 = round(statistics.median(latencies)) if latencies else 0
    latency_p95 = round(sorted(latencies)[int(len(latencies) * 0.95)]) if latencies else 0

    summary = {
        "total_questions": total,
        "successful_responses": n_valid,
        "avg_groundedness_pct": avg_groundedness,
        "avg_citation_accuracy_pct": avg_citation,
        "latency_p50_ms": latency_p50,
        "latency_p95_ms": latency_p95,
    }

    print(f"\n{'='*60}")
    print("EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Questions evaluated:      {total}")
    print(f"Successful responses:     {n_valid}/{total}")
    print(f"Avg Groundedness:         {avg_groundedness}%")
    print(f"Avg Citation Accuracy:    {avg_citation}%")
    print(f"Latency p50:              {latency_p50}ms")
    print(f"Latency p95:              {latency_p95}ms")

    json_output = output_path.replace(".md", ".json")
    with open(json_output, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print(f"\nFull results saved to: {json_output}")

    write_results_md(summary, results, output_path)
    print(f"Markdown report saved to: {output_path}")

    return summary, results


def write_results_md(summary: dict, results: list, output_path: str):
    """Write evaluation results as a Markdown report."""
    by_topic = {}
    for r in results:
        topic = r.get("topic", "General")
        by_topic.setdefault(topic, []).append(r)

    lines = [
        "# Evaluation Results",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d')}  ",
        f"**Model**: {os.getenv('LLM_MODEL', 'openrouter/free')}  ",
        "**Embedding model**: all-MiniLM-L6-v2  ",
        "**Vector store**: ChromaDB (local, cosine similarity)  ",
        f"**Top-k**: {os.getenv('TOP_K', '5')}",
        "",
        "---",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Questions evaluated | {summary['total_questions']} |",
        f"| Successful responses | {summary['successful_responses']}/{summary['total_questions']} |",
        f"| **Groundedness** | **{summary['avg_groundedness_pct']}%** |",
        f"| **Citation Accuracy** | **{summary['avg_citation_accuracy_pct']}%** |",
        f"| Latency p50 | {summary['latency_p50_ms']} ms |",
        f"| Latency p95 | {summary['latency_p95_ms']} ms |",
        "",
        "---",
        "",
        "## Metric Definitions",
        "",
        "- **Groundedness**: Measured via LLM-as-judge. The judge LLM reads the retrieved context and the generated answer, then classifies as GROUNDED (1.0), PARTIAL (0.5), or UNGROUNDED (0.0). Heuristic key-fact matching used as fallback.",
        "- **Citation Accuracy**: Heuristic check — answer receives 1.0 if a `[Source: ...]` tag references a retrieved document title, 0.5 if `[Source:]` appears but can't be matched, 0.0 if no citation found.",
        "- **Latency**: Wall-clock time from request receipt to answer return (includes embedding, retrieval, and LLM call).",
        "",
        "---",
        "",
        "## Results by Topic",
        "",
    ]

    for topic, qs in sorted(by_topic.items()):
        lines.append(f"### {topic}")
        lines.append("")
        lines.append("| ID | Question | Groundedness | Citation | Latency |")
        lines.append("|-----|---------|--------------|----------|---------|")
        for r in qs:
            g = f"{round(r['groundedness']*100)}%"
            c = f"{round(r['citation_accuracy']*100)}%"
            lat = f"{r['latency_ms']}ms"
            q_short = r['question'][:60] + ("..." if len(r['question']) > 60 else "")
            lines.append(f"| {r['id']} | {q_short} | {g} | {c} | {lat} |")
        lines.append("")

    lines += [
        "---",
        "",
        "## Sample Answers",
        "",
    ]

    sample_ids = ["Q01", "Q08", "Q18", "Q28"]
    for r in results:
        if r["id"] in sample_ids and not r.get("error"):
            lines.append(f"**{r['id']} — {r['question']}**")
            lines.append("")
            lines.append(f"> {r['answer'][:500].replace(chr(10), ' ')}")
            lines.append("")
            lines.append(f"*Sources: {', '.join(r['sources'])} | Latency: {r['latency_ms']}ms | Groundedness: {round(r['groundedness']*100)}%*")
            lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def run_retrieval_only_evaluation(questions_path: str, output_path: str):
    """
    Evaluate the retrieval stage only — no LLM calls, no API budget consumed.
    Metrics:
      - Retrieval groundedness: fraction of key_facts found in top-k retrieved chunks
      - Source recall: at least one retrieved chunk is from a relevant source document
      - Retrieval latency: time to embed the query + ChromaDB search (p50, p95)
    """
    with open(questions_path, "r") as f:
        questions = json.load(f)

    print(f"Running retrieval-only evaluation on {len(questions)} questions...\n")

    embed_model = get_embed_model()
    collection = get_collection()
    top_k = int(os.getenv("TOP_K", "5"))

    results = []
    latencies = []
    groundedness_scores = []
    source_recall_scores = []

    for i, q in enumerate(questions, 1):
        qid = q["id"]
        question = q["question"]
        topic = q.get("topic", "General")
        key_facts = q.get("key_facts", [])

        print(f"[{i:02d}/{len(questions)}] ({topic}) {question[:70]}")

        t0 = time.time()
        query_embedding = embed_model.encode([question])[0].tolist()
        retrieval_result = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        latency_ms = round((time.time() - t0) * 1000)
        latencies.append(latency_ms)

        docs = retrieval_result["documents"][0] if retrieval_result["documents"] else []
        metas = retrieval_result["metadatas"][0] if retrieval_result["metadatas"] else []
        retrieved_titles = [m.get("source_title", m.get("title", "")) for m in metas]

        combined_text = " ".join(docs).lower()
        if key_facts:
            hits = sum(1 for fact in key_facts if fact.lower() in combined_text)
            groundedness = round(hits / len(key_facts), 4)
        else:
            groundedness = 1.0

        source_recall = 1.0 if retrieved_titles else 0.0

        groundedness_scores.append(groundedness)
        source_recall_scores.append(source_recall)

        g_pct = round(groundedness * 100)
        print(f"    Retrieval latency: {latency_ms}ms | Key-fact recall: {g_pct}% | Sources: {retrieved_titles[:2]}")

        results.append({
            "id": qid,
            "topic": topic,
            "question": question,
            "retrieved_sources": retrieved_titles,
            "latency_ms": latency_ms,
            "retrieval_groundedness": groundedness,
            "source_recall": source_recall,
            "key_facts_found": sum(1 for fact in key_facts if fact.lower() in combined_text),
            "key_facts_total": len(key_facts),
            "mode": "retrieval-only",
        })

    total = len(results)
    avg_ground = round(statistics.mean(groundedness_scores) * 100, 1)
    avg_recall = round(statistics.mean(source_recall_scores) * 100, 1)
    latency_p50 = round(statistics.median(latencies))
    latency_p95 = round(sorted(latencies)[int(total * 0.95)])

    summary = {
        "mode": "retrieval-only",
        "total_questions": total,
        "avg_retrieval_groundedness_pct": avg_ground,
        "avg_source_recall_pct": avg_recall,
        "latency_p50_ms": latency_p50,
        "latency_p95_ms": latency_p95,
    }

    print(f"\n{'='*60}")
    print("RETRIEVAL-ONLY EVALUATION SUMMARY")
    print(f"{'='*60}")
    print(f"Questions evaluated:          {total}")
    print(f"Avg Key-fact Recall:          {avg_ground}%")
    print(f"Avg Source Recall:            {avg_recall}%")
    print(f"Retrieval Latency p50:        {latency_p50}ms")
    print(f"Retrieval Latency p95:        {latency_p95}ms")

    json_output = output_path.replace(".md", ".json")
    with open(json_output, "w") as f:
        json.dump({"summary": summary, "results": results}, f, indent=2)
    print(f"\nFull results saved to: {json_output}")

    _write_retrieval_only_md(summary, results, output_path)
    print(f"Markdown report saved to: {output_path}")
    return summary, results


def _write_retrieval_only_md(summary: dict, results: list, output_path: str):
    by_topic = {}
    for r in results:
        by_topic.setdefault(r.get("topic", "General"), []).append(r)

    lines = [
        "# Evaluation Results (Retrieval-Only Mode)",
        "",
        f"**Date**: {time.strftime('%Y-%m-%d')}  ",
        "**Mode**: Retrieval-only — no LLM calls; evaluates the ChromaDB retrieval stage  ",
        "**Embedding model**: all-MiniLM-L6-v2  ",
        "**Vector store**: ChromaDB (local, cosine similarity)  ",
        f"**Top-k**: {os.getenv('TOP_K', '5')}",
        "",
        "> **Note**: This report covers retrieval-stage metrics only. For end-to-end answer",
        "> quality (groundedness, citation accuracy) re-run without `--retrieval-only` once",
        "> the OpenRouter daily API rate limit has reset.",
        "",
        "---",
        "",
        "## Summary Metrics",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Questions evaluated | {summary['total_questions']} |",
        f"| **Key-fact Recall** | **{summary['avg_retrieval_groundedness_pct']}%** |",
        f"| **Source Recall** | **{summary['avg_source_recall_pct']}%** |",
        f"| Retrieval Latency p50 | {summary['latency_p50_ms']} ms |",
        f"| Retrieval Latency p95 | {summary['latency_p95_ms']} ms |",
        "",
        "---",
        "",
        "## Metric Definitions",
        "",
        "- **Key-fact Recall**: Fraction of pre-defined `key_facts` strings found (case-insensitive) in the concatenated text of all top-k retrieved chunks. Measures whether the retrieval step surfaces the relevant information before LLM generation.",
        "- **Source Recall**: Whether at least one chunk was successfully retrieved (sanity check; expected 100% for in-scope questions).",
        "- **Retrieval Latency**: Wall-clock time for query embedding + ChromaDB cosine search. Excludes LLM generation time.",
        "",
        "---",
        "",
        "## Results by Topic",
        "",
    ]

    for topic, qs in sorted(by_topic.items()):
        lines.append(f"### {topic}")
        lines.append("")
        lines.append("| ID | Question | Key-fact Recall | Found/Total | Latency | Top Sources |")
        lines.append("|----|----------|-----------------|-------------|---------|-------------|")
        for r in qs:
            g = f"{round(r['retrieval_groundedness']*100)}%"
            kt = f"{r['key_facts_found']}/{r['key_facts_total']}"
            lat = f"{r['latency_ms']}ms"
            q_short = r['question'][:55] + ("..." if len(r['question']) > 55 else "")
            srcs = ", ".join(r['retrieved_sources'][:2])
            lines.append(f"| {r['id']} | {q_short} | {g} | {kt} | {lat} | {srcs} |")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the RAG policy assistant")
    parser.add_argument("--questions", default="evaluation/questions.json")
    parser.add_argument("--output", default="evaluation/results.md")
    parser.add_argument("--no-llm-judge", action="store_true", help="Use heuristic scoring only (no LLM judge calls)")
    parser.add_argument("--retrieval-only", action="store_true",
                        help="Score retrieval stage only — no LLM calls at all")
    args = parser.parse_args()

    if args.retrieval_only:
        run_retrieval_only_evaluation(
            questions_path=args.questions,
            output_path=args.output,
        )
    else:
        run_evaluation(
            questions_path=args.questions,
            output_path=args.output,
            use_llm_judge=not args.no_llm_judge,
        )
