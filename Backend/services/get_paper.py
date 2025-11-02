from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdf2image import convert_from_path
from files import delete_file, download2local, extract_zip2pdf
import re, os, pytesseract

def ocr(pdf_path, clean_text=True):
    try:
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        print(f"Processing: {pdf_path}")
        
        text = extract_text(
            pdf_path,
            laparams=LAParams(
                line_margin=0.5,
                word_margin=0.1,
                char_margin=2.0,
                detect_vertical=True
            )
        )
        
        if len(text.strip()) < 100:
            text = ocr_from_images(pdf_path)
        else:
            print(f"✓ Text extraction: {len(text)} characters")
        
        if clean_text:
            text = re.sub(r'\s+', ' ', text)  
            text = re.sub(r'\n\s*\n', '\n\n', text) 
            text = text.strip()
        
    except Exception as e:
        delete_file(pdf_path, silent=True)
        raise RuntimeError(f"Error reading PDF: {e}")
    
    delete_file(pdf_path, silent=True)
    return text


def ocr_from_images(pdf_path, language='eng'):
    try:
        images = convert_from_path(pdf_path, dpi=300)
        print(f"Found {len(images)} pages")
        
        text = ""
        for i, image in enumerate(images, 1):
            page_text = pytesseract.image_to_string(image, lang=language)
            text += f"\n--- Page {i} ---\n{page_text}\n"
        
        return text
        
    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")


def process_paper(paper):
    local_path = download2local(paper)
    pdf_path = None
    
    try:
        if local_path.endswith('.zip'):
            pdf_path = extract_zip2pdf(local_path)
        elif local_path.endswith('.pdf'):
            pdf_path = local_path
        else:
            delete_file(local_path, silent=True)
            raise ValueError("Unsupported file format")
        text = ocr(pdf_path)
        
        return text
        
    except Exception as e:
        if local_path and os.path.exists(local_path):
            delete_file(local_path, silent=True)
        if pdf_path and pdf_path != local_path and os.path.exists(pdf_path):
            delete_file(pdf_path, silent=True)
        raise