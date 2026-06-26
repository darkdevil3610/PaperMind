from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def extract_pages_from_pdf(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    pages = []

    for index, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append({"page": index, "text": page_text})

    return pages


def get_pdf_stats(uploaded_file):
    uploaded_file.seek(0)
    reader = PdfReader(uploaded_file)
    metadata = reader.metadata or {}
    return {
        "pages": len(reader.pages),
        "title": metadata.get("/Title") or "",
        "author": metadata.get("/Author") or "",
        "subject": metadata.get("/Subject") or "",
    }
