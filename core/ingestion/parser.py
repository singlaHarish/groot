from pypdf import PdfReader
from typing import Callable, Optional

def extract_text_from_pdf(pdf_file, progress_callback: Optional[Callable[[int, int], None]] = None) -> str:
    """Extracts all text from a given uploaded PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    total_pages = len(reader.pages)
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
        if progress_callback:
            progress_callback(i + 1, total_pages)
    return text
