import os, requests, datetime

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

def fetch_latest_scams():
    url = f"https://newsapi.org/v2/everything?q=upi+scam+fraud&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    r = requests.get(url)
    if r.status_code != 200:
        return []
    data = r.json().get("articles", [])
    cleaned = []
    for a in data:
        cleaned.append({
            "headline": a.get("title"),
            "raw_text": a.get("content") or a.get("description") or "",
            "published": datetime.datetime.utcnow().isoformat()
        })
    return cleaned
