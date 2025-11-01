from fastapi import FastAPI
from utils_cbse import get_all_previous_papers_cbse

app = FastAPI()

@app.get("/")
async def root():
    return get_all_previous_papers_cbse()