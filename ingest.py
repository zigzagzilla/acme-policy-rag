"""
Document ingestion and indexing pipeline for the Acme Corp Policy Assistant.
Reads policy markdown files, chunks them, embeds with sentence-transformers,
and stores in ChromaDB.

Usage:
    python ingest.py
"""

import os
import re
import random
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

POLICIES_DIR = os.getenv("POLICIES_DIR", "./policies")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "acme_policies"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def load_document(filepath: Path) -> dict:
    """Read a markdown file and return its content and metadata."""
    text = filepath.read_text(encoding="utf-8")

    title = filepath.stem.replace("_", " ").title()
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    if first_line.startswith("#"):
        title = first_line.lstrip("#").strip()

    return {
        "text": text,
        "source_title": title,
        "source_file": filepath.name,
    }


def clean_text(text: str) -> str:
    """Remove excessive whitespace and markdown formatting noise."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    return text


def chunk_by_tokens(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks by approximate word count.
    Falls back gracefully for short documents.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end == len(words):
            break
        start += chunk_size - overlap

    return chunks


def chunk_by_headings(text: str) -> list[str]:
    """
    Split markdown text at heading boundaries (## or ###).
    Returns sections; falls back to word chunking if sections are too large.
    """
    sections = re.split(r"\n(?=#{1,3} )", text)
    result = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        words = section.split()
        if len(words) > CHUNK_SIZE * 1.5:
            result.extend(chunk_by_tokens(section))
        else:
            result.append(section)
    return result if result else [text]


def ingest_documents():
    policies_path = Path(POLICIES_DIR)
    md_files = list(policies_path.glob("*.md")) + list(policies_path.glob("*.txt"))

    if not md_files:
        print(f"No documents found in {POLICIES_DIR}")
        return

    print(f"Loading embedding model: {EMBED_MODEL_NAME}")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    print(f"Connecting to ChromaDB at: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"Cleared existing collection: {COLLECTION_NAME}")
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0
    all_ids = []
    all_docs = []
    all_embeddings = []
    all_metadatas = []

    for filepath in sorted(md_files):
        print(f"\nIngesting: {filepath.name}")
        doc = load_document(filepath)
        clean = clean_text(doc["text"])
        chunks = chunk_by_headings(clean)

        print(f"  → {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            if len(chunk.strip()) < 30:
                continue

            chunk_id = f"{filepath.stem}__chunk_{i}"
            embedding = model.encode(chunk).tolist()

            all_ids.append(chunk_id)
            all_docs.append(chunk)
            all_embeddings.append(embedding)
            all_metadatas.append({
                "source_title": doc["source_title"],
                "source_file": doc["source_file"],
                "chunk_index": i,
            })
            total_chunks += 1

    if all_ids:
        batch_size = 100
        for start in range(0, len(all_ids), batch_size):
            end = start + batch_size
            collection.add(
                ids=all_ids[start:end],
                documents=all_docs[start:end],
                embeddings=all_embeddings[start:end],
                metadatas=all_metadatas[start:end],
            )

    print(f"\n✓ Ingestion complete: {len(md_files)} documents, {total_chunks} chunks indexed.")
    print(f"  Vector store: {CHROMA_PATH}/{COLLECTION_NAME}")


if __name__ == "__main__":
    ingest_documents()
