"""Minimal recursive character text splitter.

`langchain_text_splitters.RecursiveCharacterTextSplitter` eagerly imports
`sentence-transformers` (for an unrelated optional feature) which in turn can
drag in a broken local TensorFlow/Keras install and crash on import. Since we
only need plain recursive character splitting (no sentence-transformers token
counting), this small self-contained version avoids that dependency chain
entirely.
"""
from __future__ import annotations

from langchain_core.documents import Document

_SEPARATORS = ["\n\n", "\n", ". ", " "]


def _split_text(text: str, chunk_size: int, chunk_overlap: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if text.strip() else []

    sep = separators[0] if separators else ""
    rest = separators[1:]
    parts = text.split(sep) if sep else list(text)

    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = current + (sep if current else "") + part if current else part
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
            tail = current[-chunk_overlap:] if chunk_overlap else ""
            current = f"{tail}{sep}{part}" if tail else part
            if len(current) <= chunk_size:
                continue

        if rest:
            chunks.extend(_split_text(current if current else part, chunk_size, chunk_overlap, rest))
            current = ""
        else:
            step = max(chunk_size - chunk_overlap, 1)
            piece = current if current else part
            for i in range(0, len(piece), step):
                chunks.append(piece[i : i + chunk_size])
            current = ""

    if current.strip():
        chunks.append(current)
    return chunks


def split_documents(docs: list[Document], chunk_size: int, chunk_overlap: int) -> list[Document]:
    out = []
    for doc in docs:
        for piece in _split_text(doc.page_content, chunk_size, chunk_overlap, _SEPARATORS):
            out.append(Document(page_content=piece, metadata=dict(doc.metadata)))
    return out
