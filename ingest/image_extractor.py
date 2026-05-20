import sys
sys.path.insert(0, ".")
from ingest.pdf_extractor import get_page_heading
import fitz
from pathlib import Path

IMG_DIR    = Path("data/images")
IMG_DIR.mkdir(parents=True, exist_ok=True)

MIN_WIDTH  = 150
MIN_HEIGHT = 150

# xrefs we identified as repeating header/footer noise
# We discovered these by running the inventory and seeing xref=2 and xref=5 appear on almost every page
NOISE_XREFS = {2, 5, 516}

def extract_images(pdf_path: str) -> list[dict]:
    doc        = fitz.open(pdf_path)
    seen_xrefs = set()
    results    = []

    for page_idx in range(doc.page_count):
        page     = doc[page_idx]
        page_num = page_idx + 1
        images   = page.get_images(full=True)

        for img_idx, img in enumerate(images):
            xref   = img[0]
            width  = img[2]
            height = img[3]

            # FILTER 1: known noise xrefs (header/footer decorations)
            if xref in NOISE_XREFS:
                continue

            # FILTER 2: already processed this image (xref dedup)
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)

            # FILTER 3: too small to be a real diagram
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                continue

            # Extract and save
            base_image = doc.extract_image(xref)
            img_bytes  = base_image["image"]
            ext        = base_image["ext"]

            filename = f"p{page_num:03d}_img{img_idx:02d}.{ext}"
            filepath = IMG_DIR / filename
            filepath.write_bytes(img_bytes)

            results.append({
                "type"   : "image",
                "path"   : str(filepath),
                "page"   : page_num,
                "xref"   : xref,
                "width"  : width,
                "height" : height,
                "section": get_page_heading(page),
            })

    doc.close()
    return results


if __name__ == "__main__":
    for f in IMG_DIR.glob("*"):
        f.unlink()

    print("=== IMAGE EXTRACTION ===\n")
    images = extract_images("data/doc2.pdf")

    print(f"\nTotal images saved: {len(images)}")

    print("\n--- Sample with sections ---")
    for img in images[:8]:
        print(f"  Page {img['page']:2d} | {img['width']}x{img['height']}px | section='{img['section']}'")
