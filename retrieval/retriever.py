from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# Load once and reuse across queries
_vectorstore = None

def get_vectorstore(persist_dir: str = "data/vectorstore") -> Chroma:
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        _vectorstore = Chroma(
            persist_directory=persist_dir,
            embedding_function=embeddings
        )
    return _vectorstore


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Returns the top-k most relevant documents for a given query.
    Each result includes page_content and metadata.
    """
    vectorstore = get_vectorstore()
    results = vectorstore.similarity_search(query, k=k)

    return [
        {
            "content": r.page_content,
            "page": r.metadata.get("page"),
            "section": r.metadata.get("section"),
            "source": r.metadata.get("source"),
            "type": r.metadata.get("type"),
        }
        for r in results
    ]


if __name__ == "__main__":
    hits = retrieve("what is the motor power?")
    for hit in hits:
        print(hit)
        print("---")