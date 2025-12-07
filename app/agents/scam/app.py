from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from pathlib import Path
import os

# Load .env from project root
root_dir = Path(__file__).resolve().parents[3]
load_dotenv(root_dir / ".env")

from app.agents.scam.pipeline import run
from app.agents.scam.scam_news_harvester import fetch_latest_scams
from app.agents.scam.pattern_extractor import extract_patterns, save_patterns
from app.schemas.scam import HarvestResponse

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Scam Agent Standalone")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ScamRequest(BaseModel):
    text: str
    language: str = "en"

@app.post("/analyze")
async def analyze_scam(req: ScamRequest):
    return await run(req.text, req.language)

@app.post("/harvest", response_model=HarvestResponse)
async def harvest_scams(save: bool = False):
    """
    Fetches latest scam news, extracts patterns, and optionally saves them.
    """
    articles = fetch_latest_scams()
    patterns = await extract_patterns(articles)
    
    if save and patterns:
        save_patterns(patterns)
        
    return {
        "articles_found": len(articles),
        "patterns_extracted": len(patterns),
        "patterns": patterns,
        "articles": articles
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
