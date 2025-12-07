from fastapi import FastAPI
from pydantic import BaseModel
from app.agents.scam.pipeline import run

app = FastAPI(title="Scam Agent Standalone")

class ScamRequest(BaseModel):
    text: str
    language: str = "en"

@app.post("/analyze")
async def analyze_scam(req: ScamRequest):
    return run(req.text, req.language)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
