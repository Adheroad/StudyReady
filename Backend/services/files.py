from fastapi.responses import StreamingResponse
import requests
from fastapi import HTTPException

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