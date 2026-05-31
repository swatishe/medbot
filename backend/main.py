from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from groq import Groq

load_dotenv()

app = FastAPI(title="MedBot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
client = chromadb.PersistentClient(path=CHROMA_PATH)

# DefaultEmbeddingFunction uses a tiny ONNX model (~30MB) — works within 512MB
ef = DefaultEmbeddingFunction()

try:
    collection = client.get_collection(name="medical_docs", embedding_function=ef)
    print(f"Loaded collection with {collection.count()} documents")
except Exception:
    collection = client.get_or_create_collection(name="medical_docs", embedding_function=ef)
    print("Created new empty collection — run ingest.py first")

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class QueryRequest(BaseModel):
    question: str
    top_k: Optional[int] = 5


class Source(BaseModel):
    source: str
    page: int
    excerpt: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    doc_count: int


@app.get("/health")
def health():
    return {"status": "ok", "doc_count": collection.count()}


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    if collection.count() == 0:
        raise HTTPException(status_code=503, detail="No documents ingested yet. Run ingest.py first.")

    results = collection.query(
        query_texts=[req.question],
        n_results=min(req.top_k, collection.count()),
        include=["documents", "metadatas", "distances"]
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]

    if not docs:
        raise HTTPException(status_code=404, detail="No relevant documents found.")

    context_blocks = []
    for i, (doc, meta) in enumerate(zip(docs, metas)):
        context_blocks.append(
            f"[Source {i+1}] {meta.get('source','Unknown')} (Page {meta.get('page',1)})\n{doc}"
        )
    context = "\n\n---\n\n".join(context_blocks)

    system_prompt = """You are MedBot, a clinical policy assistant for healthcare professionals.
Answer questions using ONLY the provided source documents.
Always cite your sources using [Source N] inline.
If the answer is not found in the sources, say so clearly — never fabricate medical information.
Be concise, accurate, and use plain language appropriate for clinical staff.
End with a "Sources:" section listing which documents you referenced."""

    chat = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {req.question}\n\nContext:\n{context}"},
        ],
        max_tokens=1024,
        temperature=0.2,
    )

    answer = chat.choices[0].message.content

    seen = set()
    sources = []
    for meta, doc, dist in zip(metas, docs, distances):
        key = (meta.get("source", ""), meta.get("page", 1))
        if key not in seen and dist < 1.2:
            seen.add(key)
            sources.append(Source(
                source=meta.get("source", "Unknown"),
                page=meta.get("page", 1),
                excerpt=doc[:200] + "..." if len(doc) > 200 else doc
            ))

    return QueryResponse(answer=answer, sources=sources, doc_count=collection.count())
