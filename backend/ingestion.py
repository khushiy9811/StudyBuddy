"""Flow A — Ingestion: File Loader -> Recursive Text Splitter -> Ollama Embeddings -> Chroma.

Mirrors Section 5 / Flow A of the project plan. Every chunk keeps `source`, `page`
and `topic` metadata so answers can cite them (F5).
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_ollama import OllamaEmbeddings
from pypdf import PdfReader

from backend import config
from backend.splitter import split_documents

# Loaders are hand-rolled (pypdf / plain read) rather than
# langchain_community.document_loaders: that package's PyPDFLoader/TextLoader
# route through langchain_core.document_loaders.base, which eagerly imports
# langchain_text_splitters -> sentence-transformers -> transformers, a heavy
# chain unrelated to what we need here and prone to breaking on machines with
# a mismatched local TensorFlow/Keras install.
_SUPPORTED_SUFFIXES = {".pdf", ".txt", ".md"}


def guess_topic(filename: str) -> str:
    """Best-effort topic label from the filename (e.g. 'DBMS_Unit2_Joins.pdf' -> 'Joins')."""
    stem = Path(filename).stem.replace("_", " ").replace("-", " ")
    return stem


def _load_pdf(path: Path, topic: str) -> list[Document]:
    reader = PdfReader(str(path))
    docs = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(
                Document(page_content=text, metadata={"source": path.name, "page": i, "topic": topic})
            )
    return docs


def _load_text(path: Path, topic: str) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return [Document(page_content=text, metadata={"source": path.name, "page": 1, "topic": topic})]


def load_documents(paths: Iterable[Path]) -> list[Document]:
    docs: list[Document] = []
    for path in paths:
        suffix = path.suffix.lower()
        if suffix not in _SUPPORTED_SUFFIXES:
            continue
        topic = guess_topic(path.name)
        if suffix == ".pdf":
            docs.extend(_load_pdf(path, topic))
        else:
            docs.extend(_load_text(path, topic))
    return docs


def get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=config.EMBED_MODEL, base_url=config.OLLAMA_BASE_URL)


def get_vectorstore() -> Chroma:
    return Chroma(
        collection_name=config.COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(config.CHROMA_DIR),
    )


def ingest(
    notes_dir: Path | None = None,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
) -> int:
    """Run the full ingestion flow. Returns the number of chunks indexed."""
    notes_dir = notes_dir or config.NOTES_DIR
    chunk_size = chunk_size or config.CHUNK_SIZE
    chunk_overlap = chunk_overlap or config.CHUNK_OVERLAP

    paths = sorted(p for p in notes_dir.glob("**/*") if p.suffix.lower() in _SUPPORTED_SUFFIXES)
    if not paths:
        return 0

    docs = load_documents(paths)
    chunks = split_documents(docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    vs = get_vectorstore()
    vs.add_documents(chunks)
    return len(chunks)


def reset_collection() -> None:
    vs = get_vectorstore()
    vs.delete_collection()


if __name__ == "__main__":
    n = ingest()
    print(f"Indexed {n} chunks from {config.NOTES_DIR}")
