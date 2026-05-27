from ingest.text_extractor import extract_all_text
from ingest.image_extractor import extract_images
from ingest.table_extractor import extract_tables
import json
import os

def build_documents(pdf_path: str):
    text_docs = extract_all_text(pdf_path)
    image_docs = extract_images(pdf_path)
    table_docs = extract_tables(pdf_path, pages="10")

    documents = []

    for i, doc in enumerate(text_docs):
        documents.append({
            "id": f"text_{i}",
            "type": "text_chunk",
            "content": doc["text"],
            "metadata": {
                "source": pdf_path,
                "page": doc.get("page"),
                "section": doc.get("section"),
                "image_path": None,
                "table_title": None
            }
        })

    for i, doc in enumerate(image_docs):
        documents.append({
            "id": f"image_{i}",
            "type": "image",
            "content": doc.get("caption", ""),
            "metadata": {
                "source": pdf_path,
                "page": doc.get("page"),
                "section": doc.get("section"),
                "image_path": doc.get("image_path"),
                "table_title": None
            }
        })

    for i, doc in enumerate(table_docs):
        documents.append({
            "id": f"table_{i}",
            "type": "table_row",
            "content": doc["text"],
            "metadata": {
                "source": pdf_path,
                "page": doc.get("page"),
                "section": doc.get("table_title"),
                "image_path": None,
                "table_title": doc.get("table_title")
            }
        })

    return documents


if __name__ == "__main__":
    pdf_path = "data/doc2.pdf"
    documents = build_documents(pdf_path)

    os.makedirs("data/processed", exist_ok=True)
    with open("data/processed/documents.json", "w", encoding="utf-8") as f:
        json.dump(documents, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(documents)} documents to data/processed/documents.json")