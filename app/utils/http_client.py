"""HTTP client wrapper using httpx (stub)."""
import httpx

async def get_json(url: str):
    """Stub: fetch JSON from a URL."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return {"status": "todo", "code": resp.status_code}

