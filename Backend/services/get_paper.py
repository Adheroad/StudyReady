from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from files import delete_file, download2local, extract_zip2pdf
import re
import os
import numpy as np
from paddleocr import PaddleOCR


def looks_like_garbage(text):
    garbage_ratio = len(re.findall(r'[-]', text)) / max(len(text), 1)
    return garbage_ratio > 0.05


def ocr_from_images(pdf_path):
    """
    OCR for Indian languages (CBSE papers).
    Uses PaddleOCR 3.0 with robust error handling.
    """
    try:
        images = convert_from_path(pdf_path, dpi=300)
        print(f"Found {len(images)} pages")

        # Initialize PaddleOCR 3.0
        ocr = PaddleOCR(
            use_angle_cls=True,
            lang='en'
        )

        all_text = ""

        for i, pil_image in enumerate(images, 1):
            print(f"Processing Page {i}...")

            try:
                # Convert PIL to numpy array
                image = np.array(pil_image)

                # Run OCR
                result = ocr.ocr(image)

                page_text = ""
                
                # ✅ Robust result handling with multiple safety checks
                if result is not None and isinstance(result, list) and len(result) > 0:
                    # Check if first element exists and is not None
                    if result[0] is not None and isinstance(result[0], list):
                        # Sort by vertical position (top to bottom)
                        sorted_result = sorted(result[0], key=lambda x: x[0][0][1] if x and len(x) > 0 and len(x[0]) > 0 else 0)
                        
                        for line in sorted_result:
                            try:
                                # Verify line structure before accessing
                                if line and isinstance(line, (list, tuple)) and len(line) >= 2:
                                    text_info = line[1]
                                    
                                    # Check if text_info is valid
                                    if text_info and isinstance(text_info, (list, tuple)) and len(text_info) >= 2:
                                        text = text_info[0]
                                        confidence = text_info[1]
                                        
                                        # Ensure text is a string
                                        if isinstance(text, str) and len(text) > 0 and confidence > 0.3:
                                            page_text += text + " "
                            except (IndexError, TypeError, AttributeError) as e:
                                # Skip this line if there's an issue
                                print(f"Warning: Skipping malformed line on page {i}: {e}")
                                continue
                        
                        if page_text.strip():
                            page_text += "\n"
                    else:
                        print(f"Warning: No text detected on page {i}")
                else:
                    print(f"Warning: Empty OCR result for page {i}")

                all_text += f"\n--- Page {i} ---\n{page_text.strip()}\n"

            except Exception as page_error:
                print(f"Error processing page {i}: {page_error}")
                all_text += f"\n--- Page {i} ---\n[Error processing this page]\n"
                continue

        # Check if we got any text at all
        if not all_text.strip() or len(all_text.strip()) < 10:
            print("Warning: Very little or no text extracted from PDF")
            return "No readable text found in the document."

        print(f"Extracted text preview: {all_text[:500]}")
        return all_text

    except Exception as e:
        raise RuntimeError(f"OCR failed: {e}")



def ocr(pdf_path, clean_text=True):
    try:
        print(pdf_path)
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

        if len(text.strip()) < 100 or looks_like_garbage(text):
            print("→ Fallback to OCR (PDFMiner output too short or unreadable)")
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
    print("Final text (first 500 chars):", text[:500])
    return text

# QQ silent failures.
def process_paper(paper):
    print("inside process")
    local_path = download2local(paper)
    pdf_path = None
    print("paper downloaded")
    print(local_path)
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
        
    except Exception:
        if local_path and os.path.exists(local_path):
            delete_file(local_path, silent=True)
        if pdf_path and pdf_path != local_path and os.path.exists(pdf_path):
            delete_file(pdf_path, silent=True)
        raise
