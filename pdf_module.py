import pdfplumber
from pdf2image import convert_from_path
from modules.ocr_module import extract_text_from_image
import os

def extract_text_from_pdf(pdf_path):
    """
    Extracts text from a PDF file. It attempts to extract text directly, 
    but falls back to OCR if the PDF is scanned or yields minimal text.
    """
    text = ''
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
        
        if len(text.strip()) < 100:
            raise ValueError("Minimal text extracted, likely a scanned PDF. Forcing OCR.")

    except Exception:
        text = ''
        try:
            pages = convert_from_path(pdf_path, dpi=300)
            
            for i, page_image in enumerate(pages):
                temp_image_path = f"temp_page_for_ocr_{i}.png"
                try:
                    page_image.save(temp_image_path, 'PNG')
                    text += extract_text_from_image(temp_image_path) + '\n'
                finally:
                    if os.path.exists(temp_image_path):
                        os.remove(temp_image_path)
        except Exception as ocr_error:
            print(f"Error during OCR fallback: {ocr_error}")
            return "Could not extract text from this PDF file."
            
    return text