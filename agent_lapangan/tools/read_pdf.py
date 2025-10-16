from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

# PyMuPDF is typically imported as "fitz"; newer versions also allow "pymupdf".
# We prefer fitz for API stability (fitz.open, page.get_text, etc.).
try:
    import fitz  # type: ignore
except ImportError as e:
    raise ImportError(
        "PyMuPDF not installed. Install with: pip install pymupdf"
    ) from e


def read_pdf(
    file_path: str,
    page_start: Optional[int] = None,  # 1-based inclusive
    page_end: Optional[int] = None,  # 1-based inclusive
) -> dict[str, Any]:
    """
    Baca teks dari file PDF. Mengembalikan konten teks dan metadata dasar.
    - page_start/page_end opsional untuk membatasi rentang halaman (1-based).
    """
    p = Path(file_path).expanduser().resolve()
    if not p.exists() or not p.is_file():
        return {"success": False, "error": f"File not found: {p}"}

    try:
        with fitz.open(str(p)) as doc:
            num_pages = doc.page_count
            s = 1 if page_start is None else max(1, page_start)
            e = num_pages if page_end is None else min(num_pages, page_end)
            if s > e:
                return {
                    "success": False,
                    "error": f"Rentang halaman tidak valid: {s}-{e}",
                }

            texts: list[str] = []
            empty_pages: list[int] = []
            for i in range(s - 1, e):
                try:
                    page = doc.load_page(i)
                    # "text" layout returns plain text; adjust to "blocks"/"html" if needed
                    text = page.get_text("text") or ""
                except Exception:
                    text = ""
                if not text.strip():
                    empty_pages.append(i + 1)
                texts.append(text)

            content = "\n\n".join(texts)

    except Exception as ex:
        return {"success": False, "error": f"Gagal membuka/membaca PDF: {ex}"}

    return {
        "success": True,
        "path": str(p),
        "total_pages": num_pages,
        "extracted_range": [s, e],
        "empty_pages": empty_pages,
        "content": content,
        "note": (
            "Halaman kosong bisa jadi PDF hasil scan tanpa teks. "
            "Pertimbangkan OCR bila konten kosong."
        ),
    }
