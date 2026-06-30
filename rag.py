"""
RAG (Retrieval-Augmented Generation) pipeline for the Acme Corp Policy Assistant.
"""

import os
import time
import chromadb
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "acme_policies"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = int(os.getenv("TOP_K", "5"))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "800"))
LLM_MODEL = os.getenv("LLM_MODEL", "openrouter/free")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
LLM_API_KEY_ENV = os.getenv("LLM_API_KEY_ENV", "OPENAI_API_KEY")

FREE_FALLBACK_MODELS = [
    LLM_MODEL,
    "openrouter/free",
    "liquid/lfm-2.5-1.2b-instruct:free",
    "liquid/lfm-2.5-1.2b-thinking:free",
]

_embed_model = None
_chroma_client = None
_collection = None
_llm_client = None


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
    return _embed_model


def get_collection():
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def get_llm_client():
    global _llm_client
    if _llm_client is None:
        api_key = os.getenv(LLM_API_KEY_ENV, "")
        _llm_client = OpenAI(
            api_key=api_key,
            base_url=LLM_BASE_URL,
        )
    return _llm_client


SYSTEM_PROMPT = """You are a helpful HR and policy assistant for Acme Corp. You answer employee questions strictly based on the company policy documents provided as context.

Rules you must follow:
1. Only answer questions that are directly addressed in the provided context. If the answer is not in the context, respond: "I can only answer questions about Acme Corp policies, and I couldn't find relevant information on this topic in our policy documents."
2. Always cite the specific policy document(s) your answer is drawn from using the format: [Source: <Policy Title>].
3. Keep answers concise and factual — no speculation or information not in the context.
4. If asked about something unrelated to company policy (e.g., general knowledge, personal advice), politely decline and redirect to policy topics.
5. Maximum response length: approximately 300 words."""

QUERY_PROMPT_TEMPLATE = """Use the following policy document excerpts to answer the employee's question.

--- POLICY EXCERPTS ---
{context}
--- END OF EXCERPTS ---

Employee question: {question}

Answer (cite sources using [Source: <Policy Title>]):"""


def retrieve_chunks(query: str, k: int = TOP_K):
    """Embed the query and retrieve the top-k most relevant chunks from ChromaDB."""
    model = get_embed_model()
    collection = get_collection()

    query_embedding = model.encode(query).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if results and results["documents"]:
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            chunks.append({
                "text": doc,
                "source_title": meta.get("source_title", "Unknown Policy"),
                "source_file": meta.get("source_file", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "similarity": round(1 - dist, 4),
            })
    return chunks


def build_context(chunks: list) -> str:
    """Format retrieved chunks into a context string for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(
            f"[Excerpt {i} from: {chunk['source_title']}]\n{chunk['text']}"
        )
    return "\n\n".join(parts)


def is_in_corpus(chunks: list, similarity_threshold: float = 0.25) -> bool:
    """
    Return False if the best matching chunk has low similarity,
    suggesting the question is out of scope for the corpus.
    """
    if not chunks:
        return False
    return chunks[0]["similarity"] >= similarity_threshold


def answer_question(question: str, k: int = TOP_K):
    """
    Full RAG pipeline: retrieve relevant chunks, build prompt, call LLM.
    Returns a dict with answer, sources, snippets, and latency.
    """
    start_time = time.time()

    chunks = retrieve_chunks(question, k=k)

    if not is_in_corpus(chunks):
        latency_ms = round((time.time() - start_time) * 1000)
        return {
            "answer": (
                "I can only answer questions about Acme Corp policies. "
                "Your question doesn't appear to match any topics covered in our policy documents. "
                "Please ask about topics such as PTO, expenses, remote work, benefits, "
                "security, holidays, IT usage, onboarding, travel, or the code of conduct."
            ),
            "sources": [],
            "snippets": [],
            "latency_ms": latency_ms,
            "retrieved_chunks": 0,
        }

    context = build_context(chunks)
    prompt = QUERY_PROMPT_TEMPLATE.format(context=context, question=question)

    client = get_llm_client()
    tried_models = list(dict.fromkeys(FREE_FALLBACK_MODELS))
    last_error = None
    response = None
    used_model = LLM_MODEL

    for model in tried_models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.1,
            )
            used_model = model
            break
        except Exception as e:
            last_error = e
            continue

    if response is None:
        latency_ms = round((time.time() - start_time) * 1000)
        error_hint = str(last_error)
        if "429" in error_hint or "rate" in error_hint.lower():
            msg = (
                "The AI service is temporarily rate-limited. "
                "Please wait a moment and try again. "
                "(The relevant policy sources have been retrieved below.)"
            )
        else:
            msg = (
                "The AI service is temporarily unavailable. "
                "Please try again in a few seconds. "
                "(The relevant policy sources have been retrieved below.)"
            )
        sources_for_error = []
        seen = set()
        for chunk in chunks:
            if chunk["source_title"] not in seen:
                seen.add(chunk["source_title"])
                sources_for_error.append({
                    "title": chunk["source_title"],
                    "file": chunk["source_file"],
                })
        return {
            "answer": msg,
            "sources": sources_for_error,
            "snippets": [],
            "latency_ms": latency_ms,
            "retrieved_chunks": len(chunks),
        }

    answer_text = response.choices[0].message.content.strip()

    if not answer_text:
        answer_text = (
            "The AI model returned an empty response. "
            "Please try again — this is usually a temporary issue with the free-tier model."
        )

    latency_ms = round((time.time() - start_time) * 1000)

    if "[Source:" not in answer_text and chunks:
        top_titles = list(dict.fromkeys(c["source_title"] for c in chunks[:2]))
        citation_suffix = " " + ", ".join(f"[Source: {t}]" for t in top_titles)
        answer_text = answer_text.rstrip(".") + "." + citation_suffix

    seen_sources = set()
    sources = []
    snippets = []
    for chunk in chunks:
        if chunk["source_title"] not in seen_sources:
            seen_sources.add(chunk["source_title"])
            sources.append({
                "title": chunk["source_title"],
                "file": chunk["source_file"],
            })
        snippets.append({
            "source_title": chunk["source_title"],
            "text": chunk["text"][:300] + ("..." if len(chunk["text"]) > 300 else ""),
            "similarity": chunk["similarity"],
        })

    return {
        "answer": answer_text,
        "sources": sources,
        "snippets": snippets[:3],
        "latency_ms": latency_ms,
        "retrieved_chunks": len(chunks),
        "model_used": used_model,
    }
