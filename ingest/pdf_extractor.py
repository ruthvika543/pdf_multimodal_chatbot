import fitz

HEADING_MIN_SIZE = 14.0
FOOTER_MAX_SIZE  = 9.5
NOISE_STRINGS    = {"fervi.com", "MACHINES AND", "ACCESSORIES"}


def get_page_heading(page) -> str:
    data = page.get_text("dict")
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
                if size > 50:        # skip watermarks
                    continue
                if size <= 9.5:      # skip footers
                    continue
                if text in NOISE_STRINGS:
                    continue

                # YOUR FIX 1: skip spans shorter than 4 characters
                if len(text) < 4:
                    continue

                # Only collect heading-sized text
                if size >= HEADING_MIN_SIZE:
                    # Store y-position (block["bbox"][1]) so we can sort by position
                    y_pos = block["bbox"][1]
                    candidates.append((y_pos, size, text))

    if not candidates:
        return ""

    # YOUR FIX 2: sort by y-position and take only the FIRST one
    candidates.sort(key=lambda x: x[0])  # sort by y_pos
    
    # Return just the first heading found (topmost on page)
    return candidates[0][2]   # [2] is the text

def extract_text_from_page(page) -> tuple[str, str]:
    """
    Extracts clean text from a page.
    Returns: (text, method) where method is "native" or "ocr"

    WHY check character count?
    Some pages are purely images (scanned) — get_text() returns
    almost nothing. We detect this and flag it for OCR later.
    We won't implement OCR today — just flag it.
    """
    text = page.get_text("text", sort=True).strip()

    # Remove known noise lines that appear on every page
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        # Skip noise: page numbers, repeated headers, empty lines
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

    # Flag pages with very little text — likely scanned images
    if len(clean_text) < 50:
        return clean_text, "needs_ocr"

    return clean_text, "native"

from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text: str, page_num: int, heading: str) -> list[dict]:
    """
    Splits page text into overlapping chunks with metadata.

    WHY 700 chars with 150 overlap?
    700 chars ≈ 175 tokens — small enough to be specific,
    big enough to hold a complete idea.
    150 char overlap prevents losing meaning at boundaries.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = 700,
        chunk_overlap = 150,
        separators    = ["\n\n", "\n", ". ", " ", ""],
    )

    raw_chunks = splitter.split_text(text)
    result = []

    for i, chunk in enumerate(raw_chunks):
        # Tag safety-related chunks for better retrieval later
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

    print("=== FULL PIPELINE — All 84 pages ===\n")
    all_chunks = []

    for i in range(doc.page_count):
        page    = doc[i]
        heading = get_page_heading(page)
        text, method = extract_text_from_page(page)

        if not text:
            continue

        chunks = chunk_text(text, page_num=i+1, heading=heading)
        all_chunks.extend(chunks)

    doc.close()

    print(f"Total chunks created: {len(all_chunks)}")
    print(f"Total pages processed: 84")
    print(f"Average chunks per page: {len(all_chunks)/84:.1f}")

    print("\n--- Sample chunks ---")
    for chunk in all_chunks[10:13]:
        print(f"\nPage {chunk['page']} | section='{chunk['section'][:35]}' | chunk {chunk['chunk_idx']}")
        print(f"chars={chunk['char_count']} | tag='{chunk['tag']}'")
        print(f"text: '{chunk['text'][:150]}...'")