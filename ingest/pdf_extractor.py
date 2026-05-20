import fitz
import re
from langchain_text_splitters import RecursiveCharacterTextSplitter

HEADING_MIN_SIZE = 14.0
FOOTER_MAX_SIZE  = 9.5
NOISE_STRINGS    = {"fervi.com", "MACHINES AND", "ACCESSORIES"}


def get_page_heading(page) -> str:
    data       = page.get_text("dict")
    candidates = []

    for block in data["blocks"]:
        if block["type"] != 0:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                size = span["size"]

                if not text:
                    continue
                if size > 50:
                    continue
                if size <= FOOTER_MAX_SIZE:
                    continue
                if text in NOISE_STRINGS:
                    continue
                if len(text) < 4:
                    continue

                if size >= HEADING_MIN_SIZE:
                    y_pos = block["bbox"][1]
                    candidates.append((y_pos, size, text))

    # Strategy 1: font-size based
    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][2]

    # Strategy 2: regex fallback for pages where all text is same size
    # Matches "4.2.1 Supporting table" or "5 INSTALLATION" patterns
    all_text = page.get_text("text", sort=True)
    for line in all_text.split("\n"):
        line = line.strip()
        if re.match(r'^\d+(\.\d+)*\s+[A-Z]', line) and len(line) > 5:
            return line

    return ""


def extract_text_from_page(page) -> tuple:
    text = page.get_text("text", sort=True).strip()

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped in NOISE_STRINGS:
            continue
        if stripped.startswith("Page ") and "of 84" in stripped:
            continue
        if stripped == "fervi.com":
            continue
        cleaned_lines.append(stripped)

    clean_text = "\n".join(cleaned_lines)

    if len(clean_text) < 50:
        return clean_text, "needs_ocr"

    return clean_text, "native"


def chunk_text(text: str, page_num: int, heading: str) -> list:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 700,
        chunk_overlap = 150,
        separators    = ["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)
    result = []

    for i, chunk in enumerate(raw_chunks):
        tag = ""
        for keyword in ("WARNING", "CAUTION", "DANGER", "NOTE"):
            if chunk.upper().startswith(keyword):
                tag = keyword
                chunk = f"[{keyword}] {chunk}"
                break

        result.append({
            "text"      : chunk,
            "page"      : page_num,
            "chunk_idx" : i,
            "section"   : heading,
            "type"      : "text",
            "tag"       : tag,
            "char_count": len(chunk),
        })

    return result


if __name__ == "__main__":
    doc = fitz.open("data/doc2.pdf")

    print("=== HEADING TEST — First 20 pages ===\n")
    for i in range(20):
        page    = doc[i]
        heading = get_page_heading(page)
        print(f"  Page {i+1:2d}: '{heading}'")

    doc.close()
