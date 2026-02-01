from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Callable, Iterable, List, Tuple

from ollama import embed


@dataclass
class RagChunk:
    content: str
    source: str
    embedding: List[float]


def _read_pdf_text(path: str) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError("PDF support requires 'pypdf'. Install with: pip install pypdf") from exc

    reader = PdfReader(path)
    pages = [(page.extract_text() or "") for page in reader.pages]
    return "\n".join(pages).strip()


def load_text_files(
    root_dir: str,
    extensions: Tuple[str, ...] = (".txt", ".md", ".pdf"),
    on_progress: Callable[[str], None] | None = None,
) -> List[Tuple[str, str]]:
    documents: List[Tuple[str, str]] = []
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if not filename.lower().endswith(extensions):
                continue
            path = os.path.join(dirpath, filename)
            if on_progress:
                on_progress(f"Loading {path}...")
            if filename.lower().endswith(".pdf"):
                text = _read_pdf_text(path)
            else:
                with open(path, "r", encoding="utf-8") as handle:
                    text = handle.read()
            if text.strip():
                documents.append((path, text))
    return documents


def chunk_text(text: str, max_chars: int = 800, overlap: int = 120) -> List[str]:
    if max_chars <= 0:
        raise ValueError("max_chars must be > 0")
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")
    chunks: List[str] = []
    start = 0
    length = len(text)
    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chars - overlap
    return chunks


def build_index(
    model: str,
    docs: List[Tuple[str, str]],
    on_progress: Callable[[str], None] | None = None,
) -> List[RagChunk]:
    chunks: List[Tuple[str, str]] = []
    for source, text in docs:
        for chunk in chunk_text(text):
            chunks.append((source, chunk))
    if not chunks:
        return []

    if on_progress:
        on_progress(f"Embedding {len(chunks)} chunks...")
    embeddings = embed(
        model=model,
        input=[content for _, content in chunks],
    )["embeddings"]
    if on_progress:
        on_progress("Embedding complete.")

    return [
        RagChunk(content=content, source=source, embedding=embedding)
        for (source, content), embedding in zip(chunks, embeddings)
    ]


def search_index(
    model: str,
    index: List[RagChunk],
    query: str,
    top_k: int = 3,
) -> List[RagChunk]:
    if not index:
        return []
    query_embedding = embed(model=model, input=query)["embeddings"][0]
    scored = [
        (sum(a * b for a, b in zip(chunk.embedding, query_embedding)), chunk)
        for chunk in index
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def format_context(chunks: Iterable[RagChunk]) -> str:
    lines = ["Use the following context if relevant:"]
    for chunk in chunks:
        lines.append(f"- Source: {chunk.source}")
        lines.append(chunk.content)
    return "\n".join(lines)
