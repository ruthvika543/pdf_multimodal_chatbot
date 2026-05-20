import camelot
import fitz
import re


def clean_cell(text: str) -> str:
    """
    Normalize raw cell text extracted from a PDF table.

    This removes line breaks, extra whitespace, dotted fillers, and
    small stray OCR / extraction artifacts that sometimes appear in
    Camelot output.
    """
    if text is None:
        return ""

    text = str(text)

    # Flatten multi-line cell text into a single line.
    text = text.replace("\\n", " ").replace("\n", " ")

    # Remove isolated single-character artifacts that sometimes appear
    # from PDF extraction noise.
    text = re.sub(r"\b[mociv]\b", "", text)

    # Remove dotted fillers or leader-style noise.
    text = re.sub(r"\s+[.]+\s*", " ", text)

    # Remove a stray single letter at the end of a cell, such as:
    # "Tailstock base length (mm) e"
    text = re.sub(r"\b[a-zA-Z]\b$", "", text).strip()

    # Collapse repeated whitespace.
    text = re.sub(r"\s+", " ", text).strip()

    return text


def get_page_text(pdf_path: str, page_num: int) -> str:
    """
    Extract full plain text from one PDF page.

    We use PyMuPDF here because Camelot is good at table structure,
    but page text can help recover values Camelot misses.
    """
    doc = fitz.open(pdf_path)
    text = doc[page_num - 1].get_text("text", sort=True)
    doc.close()
    return text


def repair_value_from_text(key: str, page_text: str) -> str:
    """
    Try to recover a missing table value from the page's raw text.

    Strategy:
    1. Find the line containing the table key.
    2. If text remains on that same line after the key, use it.
    3. Otherwise, use the next non-empty line as the value.
    """
    lines = [line.strip() for line in page_text.split("\n") if line.strip()]

    for i, line in enumerate(lines):
        if key in line:
            # Some PDFs keep key and value on the same line.
            remainder = line.replace(key, "").strip()
            if remainder:
                return remainder

            # Other PDFs split the value onto the next line.
            if i + 1 < len(lines):
                return lines[i + 1].strip()

    return ""


def extract_tables(pdf_path: str, pages: str = "10") -> list[dict]:
    """
    Extract structured table rows from a PDF page.

    Camelot provides the table grid / row structure.
    PyMuPDF page text is used as a fallback to repair missing values.

    Returns:
        A list of dictionaries, where each dictionary represents
        one table row as a structured record.
    """
    all_records = []

    # Use Camelot's lattice mode because this PDF table appears to
    # have visible ruling lines that define the cell boundaries.
    tables = camelot.read_pdf(
        pdf_path,
        pages=pages,
        flavor="lattice"
    )

    for table in tables:
        df = table.df.copy()

        # Clean every extracted cell before building records.
        df = df.map(clean_cell)

        # Remove rows that are completely empty after cleaning.
        df = df[(df != "").any(axis=1)].reset_index(drop=True)

        # Skip malformed or trivial tables.
        if len(df) < 2:
            continue

        # Current prototype assumes one page value like "10".
        # Later, this can be generalized for multiple pages.
        page_num = int(pages)
        page_text = get_page_text(pdf_path, page_num)

        # Treat the first row as table headers.
        header_left = df.iloc[0, 0]
        header_right = df.iloc[0, 1]

        # Convert each remaining row into a structured metadata record.
        for i in range(1, len(df)):
            key = df.iloc[i, 0]
            value = df.iloc[i, 1]

            if not key:
                continue

            # If Camelot missed the value, try to recover it from page text.
            if not value:
                value = repair_value_from_text(key, page_text)

            all_records.append({
                "type": "table_row",
                "page": page_num,
                "table_title": "Technical Specifications",
                "column_1": header_left,
                "column_2": header_right,
                "key": key,
                "value": value,
                "text": f"Technical Specifications | {key}: {value}"
            })

    return all_records


if __name__ == "__main__":
    # Example run against your current test PDF and page.
    records = extract_tables("data/doc2.pdf", pages="10")

    print(f"Total table records: {len(records)}")
    print("\n--- Sample records ---")
    for row in records[:10]:
        print(row)