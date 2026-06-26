import hashlib
import os
import re
from functools import lru_cache
from pathlib import Path

from google.genai import types

from utils.gemini_client import get_gemini_client


CHROMA_PATH = Path(".papermind_chroma")
COLLECTION_NAME = "papermind_papers"
EMBEDDING_MODEL_CANDIDATES = tuple(
    dict.fromkeys(
        model
        for model in [
            os.getenv("GEMINI_EMBEDDING_MODEL"),
            "gemini-embedding-001",
            "text-embedding-004",
            "embedding-001",
            "models/gemini-embedding-001",
            "models/text-embedding-004",
            "models/embedding-001",
        ]
        if model
    )
)
EMBEDDING_TASK_TYPES = {
    "retrieval_document": "RETRIEVAL_DOCUMENT",
    "retrieval_query": "RETRIEVAL_QUERY",
}


def file_digest(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()[:16]


def clean_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def first_words(text, limit=500):
    words = clean_text(text).split()
    return " ".join(words[:limit])


def extract_doi(text):
    match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text or "", re.IGNORECASE)
    return match.group(0).rstrip(".,;)") if match else ""


def chunk_page_text(text, chunk_words=240, overlap_words=45):
    words = clean_text(text).split()
    if not words:
        return []

    chunks = []
    step = max(1, chunk_words - overlap_words)
    for start in range(0, len(words), step):
        chunk = " ".join(words[start : start + chunk_words])
        if len(chunk.split()) >= 30:
            chunks.append(chunk)
        if start + chunk_words >= len(words):
            break
    return chunks


def build_chunks(paper):
    chunks = []
    for page in paper.get("pages", []):
        for page_chunk_index, chunk in enumerate(chunk_page_text(page["text"])):
            chunks.append(
                {
                    "text": chunk,
                    "metadata": {
                        "digest": paper["digest"],
                        "file_name": paper["file_name"],
                        "title": paper["title"],
                        "paper_index": paper["paper_index"],
                        "page": page["page"],
                        "page_chunk_index": page_chunk_index,
                        "doi": paper.get("doi", ""),
                        "citation": paper.get("citation", ""),
                    },
                }
            )
    return chunks


def chroma_available():
    try:
        import chromadb  # noqa: F401

        return True
    except Exception:
        return False


def get_collection():
    import chromadb

    CHROMA_PATH.mkdir(exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


@lru_cache(maxsize=1)
def available_embedding_models():
    try:
        client = get_gemini_client()
        return [
            model.name
            for model in client.models.list()
            if "embedding" in (model.name or "").lower()
            or any("embed" in action.lower() for action in (getattr(model, "supported_actions", []) or []))
        ]
    except Exception:
        return []


def model_name_aliases(model_name):
    if model_name.startswith("models/"):
        return [model_name.removeprefix("models/"), model_name]
    return [model_name, f"models/{model_name}"]


@lru_cache(maxsize=1)
def resolve_embedding_model():
    available_models = available_embedding_models()
    if available_models:
        available = set(available_models)
        for candidate in EMBEDDING_MODEL_CANDIDATES:
            for alias in model_name_aliases(candidate):
                if alias in available:
                    return alias
        return available_models[0]
    return EMBEDDING_MODEL_CANDIDATES[0]


def is_model_availability_error(error):
    message = str(error).lower()
    return (
        "404" in message
        or "not found" in message
        or "not supported for embedcontent" in message
        or "not supported" in message
    )


def embed_text(text, task_type):
    model_order = [resolve_embedding_model(), *EMBEDDING_MODEL_CANDIDATES]
    last_error = None

    for model_name in dict.fromkeys(model_order):
        try:
            response = get_gemini_client().models.embed_content(
                model=model_name,
                contents=text,
                config=types.EmbedContentConfig(
                    task_type=EMBEDDING_TASK_TYPES.get(task_type, task_type),
                ),
            )
            if not response.embeddings:
                raise RuntimeError("Gemini embedding response did not include embeddings.")
            return response.embeddings[0].values
        except Exception as exc:
            last_error = exc
            if not is_model_availability_error(exc):
                raise

    raise RuntimeError(
        "No usable Gemini embedding model was found. "
        f"Tried: {', '.join(dict.fromkeys(model_order))}. "
        f"Last error: {last_error}"
    )


def embedding_status():
    available_models = available_embedding_models()
    return {
        "selected": resolve_embedding_model(),
        "available": available_models,
        "candidates": list(EMBEDDING_MODEL_CANDIDATES),
    }


def reset_embedding_model_cache():
    available_embedding_models.cache_clear()
    resolve_embedding_model.cache_clear()


def index_papers(papers):
    if not chroma_available():
        return {"available": False, "indexed": 0, "skipped": 0, "message": "ChromaDB is not installed."}

    collection = get_collection()
    indexed = 0
    skipped = 0

    for paper in papers:
        chunks = build_chunks(paper)
        if not chunks:
            continue

        existing = collection.get(where={"digest": paper["digest"]}, limit=1)
        if existing.get("ids"):
            skipped += len(chunks)
            continue

        ids = []
        documents = []
        metadatas = []
        embeddings = []

        for chunk_index, chunk in enumerate(chunks):
            ids.append(f"{paper['digest']}-{chunk_index}")
            documents.append(chunk["text"])
            metadatas.append(chunk["metadata"] | {"chunk_index": chunk_index})
            embeddings.append(embed_text(chunk["text"], "retrieval_document"))

        collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        indexed += len(chunks)

    return {"available": True, "indexed": indexed, "skipped": skipped, "message": "Vector index ready."}


def search_papers(query, top_k=6, digests=None):
    if not query.strip() or not chroma_available():
        return []

    collection = get_collection()
    where = {"digest": {"$in": digests}} if digests else None
    query_kwargs = {
        "query_embeddings": [embed_text(query, "retrieval_query")],
        "n_results": top_k,
        "include": ["documents", "metadatas", "distances"],
    }
    if where:
        query_kwargs["where"] = where
    results = collection.query(**query_kwargs)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    hits = []
    for document, metadata, distance in zip(documents, metadatas, distances):
        hits.append(
            {
                "text": document,
                "metadata": metadata,
                "score": max(0.0, 1.0 - float(distance or 0)),
            }
        )
    return hits


def delete_paper(digest):
    if not chroma_available():
        return False
    collection = get_collection()
    collection.delete(where={"digest": digest})
    return True


def vector_count():
    if not chroma_available():
        return 0
    return get_collection().count()


def source_label(hit):
    metadata = hit.get("metadata", {})
    return f"Paper {metadata.get('paper_index', '?')}, p. {metadata.get('page', '?')}"
