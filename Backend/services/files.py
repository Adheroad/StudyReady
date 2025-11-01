from fastapi.responses import StreamingResponse
import requests
import os
import glob
from fastapi import HTTPException
from zipfile import ZipFile
from pypdf import PdfReader, PdfWriter
import shutil

def download2client(paper):
    try:
        response = requests.get(paper['link'], stream=True)
        response.raise_for_status()

        filename = paper['link'].split('/')[-1]
        
        if filename.endswith('.zip'):
            media_type = 'application/zip'
        elif filename.endswith('.pdf'):
            media_type = 'application/pdf'
        else:
            media_type = 'application/octet-stream'
        
        return StreamingResponse(
            response.iter_content(chunk_size=1024 * 1024),  
            media_type=media_type,
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )
    
def merge_pdfs(pdf_list, output_path="/tmp/papers/merged.pdf"):
    """Merge multiple PDFs into a single PDF"""
    try:
        if not pdf_list:
            raise ValueError("No PDF files to merge")
        
        if len(pdf_list) == 1:
            # If only one PDF, just return it
            return pdf_list[0]
        
        writer = PdfWriter()
        
        for pdf in pdf_list:
            if os.path.exists(pdf):
                reader = PdfReader(pdf)
                for page in reader.pages:
                    writer.add_page(page)
                print(f"Added: {pdf}")
        
        with open(output_path, 'wb') as f:
            writer.write(f)
        
        print(f"✓ Merged {len(pdf_list)} PDFs into: {output_path}")
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"Failed to merge PDFs: {e}")


def extract_zip2pdf(zip_path):
    """Extract ZIP, find all PDFs in all subdirectories, and merge them"""
    extract_dir = "/tmp/papers/"
    os.makedirs(extract_dir, exist_ok=True)

    try:
        with ZipFile(zip_path, 'r') as zip_object:
            zip_object.extractall(extract_dir)

        pdf_files = glob.glob(os.path.join(extract_dir, "**/*.pdf"), recursive=True)
        print(f"Found PDFs: {pdf_files}")

        if not pdf_files:
            raise FileNotFoundError("No PDF found in the ZIP file.")

        print(f"Found {len(pdf_files)} PDFs in ZIP (including subdirectories)")

        if len(pdf_files) > 1:
            merged_pdf = merge_pdfs(pdf_files)
            for pdf in pdf_files:
                delete_file(pdf, silent=True)
        else:
            print(pdf_files)
            merged_pdf = pdf_files[0]

        for item in os.listdir(extract_dir):
            item_path = os.path.join(extract_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path, ignore_errors=True)

        delete_file(zip_path, silent=True)
        return merged_pdf

    except Exception as e:
        delete_file(zip_path, silent=True)
        raise RuntimeError(f"Failed to extract and merge ZIP: {e}")
    
def download2local(paper):
    try:
        response = requests.get(paper['link'], stream=True)
        response.raise_for_status()
        
        filename = paper['link'].split('/')[-1]
        local_path = f"/tmp/{filename}"
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        
        return local_path
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download file: {str(e)}"
        )


def delete_file(file_path, silent=False):
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            if not silent:
                print(f"Deleted: {file_path}")
            return True
        else:
            if not silent:
                print(f"File not found: {file_path}")
            return False
    except Exception as e:
        if not silent:
            print(f"Error deleting {file_path}: {e}")
        return False
