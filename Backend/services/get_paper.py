from pdfminer.high_level import extract_text
from files import delete_file

def ocr(pdf_path):
    try:
        text = extract_text(pdf_path)
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {e}")

    delete_file(pdf_path, silent=True)

    return text

