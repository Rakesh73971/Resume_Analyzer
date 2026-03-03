import fitz  # PyMuPDF

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""

    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")

        for page in doc:
            text += page.get_text()

        doc.close()

        return text.strip()

    except Exception:
        return ""