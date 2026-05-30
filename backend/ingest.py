#!/usr/bin/env python3
import os
import sys
import argparse
import hashlib
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
import pypdf


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> list[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk.strip())
        i += chunk_size - overlap
    return chunks


def extract_pdf(pdf_path: Path) -> list[tuple[str, int]]:
    pages = []
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            text = " ".join(text.split())
            if len(text) > 50:
                pages.append((text, page_num))
        print(f"  Extracted {len(pages)} pages from {pdf_path.name}")
    except Exception as e:
        print(f"  ERROR reading {pdf_path.name}: {e}")
    return pages


def ingest(data_dir: str, chroma_path: str):
    data_path = Path(data_dir)
    pdfs = list(data_path.glob("**/*.pdf"))

    if not pdfs:
        print(f"\nNo PDFs found in {data_dir}")
        print("Add PDFs to the data/ folder\n")
        sys.exit(1)

    print(f"\nFound {len(pdfs)} PDF(s) in {data_dir}")
    print("Loading embedding model (downloads ~80MB on first run)...")

    local_ef = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")

    db = chromadb.PersistentClient(path=chroma_path)
    collection = db.get_or_create_collection(
        name="medical_docs",
        embedding_function=local_ef,
        metadata={"hnsw:space": "cosine"}
    )

    print(f"Collection currently has {collection.count()} chunks\n")
    total_chunks = 0

    for pdf_path in pdfs:
        print(f"Processing: {pdf_path.name}")
        pages = extract_pdf(pdf_path)

        for page_text, page_num in pages:
            chunks = chunk_text(page_text)
            for chunk_idx, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(
                    f"{pdf_path.name}:{page_num}:{chunk_idx}:{chunk[:50]}".encode()
                ).hexdigest()

                existing_ids = collection.get(ids=[chunk_id])
                if existing_ids["ids"]:
                    continue

                collection.add(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[{"source": pdf_path.name, "page": page_num, "chunk_idx": chunk_idx}]
                )
                total_chunks += 1

        print(f"  Done. Running total: {collection.count()} chunks\n")

    print(f"Ingestion complete! Added {total_chunks} new chunks.")
    print(f"Collection now has {collection.count()} total chunks.")
    print("\nStart the backend: uvicorn main:app --reload")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MedBot PDF Ingestion")
    parser.add_argument("--data-dir", default="./data")
    parser.add_argument("--chroma-path", default="./chroma_db")
    args = parser.parse_args()
    ingest(args.data_dir, args.chroma_path)
