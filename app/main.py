"""FastAPI application entrypoint."""

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from api.router import api_router
from agents.scam.pipeline import run   # correct import



from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FinPal API")

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

@app.get("/")
async def root():
    return {"message": "Financial Safety Net API"}


@app.post("/scam/analyze")
async def analyze_scam(req: ScamRequest):
    return run(req.text, req.language)   # returns ScamAnalysisResult.model_dump()


# Include other system routers
app.include_router(api_router)


if __name__ == "__main__":
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
