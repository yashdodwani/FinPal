import os
import datetime
from typing import List, Dict, Any

import requests

NEWS_API_KEY = os.getenv("NEWS_API_KEY")


def fetch_latest_scams() -> List[Dict[str, Any]]:
    """
    Fetch latest UPI scam / fraud news using NewsAPI.

    Returns a list of dicts:
    {
        "headline": str,
        "raw_text": str,
        "published": iso8601 str,
        "url": str | None
    }
    """
    if not NEWS_API_KEY:
        # Graceful fallback if key is missing
        return []

    url = (
        "https://newsapi.org/v2/everything?"
        "q=upi+scam+fraud&language=en&sortBy=publishedAt&apiKey="
        f"{NEWS_API_KEY}"
    )
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        return []

    data = r.json().get("articles", [])
    cleaned = []
    for a in data:
        cleaned.append(
            {
                "headline": a.get("title"),
                "raw_text": a.get("content") or a.get("description") or "",
                "published": datetime.datetime.utcnow().isoformat(),
                "url": a.get("url"),
            }
        )
    return cleaned
