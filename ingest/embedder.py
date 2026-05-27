import json
import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


def embed_documents(documents_path: str, persist_dir: str = "data/vectorstore"):
    # Load the unified document list from the pipeline
    with open(documents_path, "r", encoding="utf-8") as f:
        documents = json.load(f)

    texts     = [doc["content"] for doc in documents]
    metadatas = [doc["metadata"] for doc in documents]
    ids       = [doc["id"] for doc in documents]

    # Filter out empty content — Chroma rejects empty strings
    filtered = [(t, m, i) for t, m, i in zip(texts, metadatas, ids) if t.strip()]
    texts, metadatas, ids = zip(*filtered)

    print(f"Embedding {len(texts)} documents...")

    # Free local model — downloads once (~90MB), then runs offline
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2"
    )

    vectorstore = Chroma.from_texts(
        texts=list(texts),
        embedding=embeddings,
        metadatas=list(metadatas),
        ids=list(ids),
        persist_directory=persist_dir
    )

    print(f"Vectorstore saved to {persist_dir}")
    return vectorstore


if __name__ == "__main__":
    embed_documents("data/processed/documents.json")