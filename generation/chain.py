from retrieval.retriever import retrieve
import requests
import json

def build_prompt(query: str, context_docs: list[dict]) -> str:
    context = "\n\n".join([doc["content"] for doc in context_docs])
    return f"""You are a helpful assistant for a machine manual chatbot.
Use only the context below to answer the question.
If the answer is not in the context, say "I don't know."

Context:
{context}

Question: {query}
Answer:"""


def call_ollama(prompt: str, model: str = "llama3.2") -> str:
    """Send prompt to local Ollama instance and return the response."""
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False}
    )
    return response.json()["response"]


def answer(query: str, k: int = 5) -> dict:
    docs = retrieve(query, k=k)
    prompt = build_prompt(query, docs)
    response = call_ollama(prompt)

    return {
        "query": query,
        "answer": response,
        "context": docs,
    }


if __name__ == "__main__":
    result = answer("What is the motor power?")
    print("Answer:", result["answer"])
    print("\nSources:")
    for doc in result["context"]:
        print(f"  - Page {doc['page']}: {doc['content'][:80]}")