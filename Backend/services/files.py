from fastapi.responses import StreamingResponse
import requests, os, glob
from fastapi import HTTPException
from zipfile import ZipFile
from get_paper import ocr

def download(paper):
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


def extract_zip2pdf(zip_path):
    extract_dir = "/tmp/papers/"
    os.makedirs(extract_dir, exist_ok=True)

    with ZipFile(zip_path, 'r') as zip_object:
        zip_object.extractall(extract_dir)

    pdf_files = glob.glob(os.path.join(extract_dir, "*.pdf"))
    if not pdf_files:
        raise FileNotFoundError("No PDF found in the ZIP file.")

    delete_file(zip_path, silent=True)

    return pdf_files[0]