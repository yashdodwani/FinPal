import json
import requests
from bs4 import BeautifulSoup
from pathlib import Path

LOCAL_POLICY_FILE = Path("app/data/policies/rbi_sebi_policies.json")

RBI_SOURCES = [
    "https://www.rbi.org.in/Scripts/PublicationDraftReports.aspx?ID=1200",   # Digital Lending Guidelines
    "https://www.rbi.org.in/commonman/english/scripts/Notification.aspx?Id=10585",  # Fraud Awareness
]

def load_local_policies():
    if LOCAL_POLICY_FILE.exists():
        with open(LOCAL_POLICY_FILE, "r") as f:
            return json.load(f)
    return []


def scrape_rbi_page(url):
    """Fetch RBI text content from a URL safely."""
    try:
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator="\n")
        return text[:5000]  # Limit text to avoid token explosion
    except Exception as e:
        print(f"[policy_fetch] Failed to fetch RBI page {url}: {e}")
        return None


def fetch_live_rbi_guidelines():
    results = []
    for url in RBI_SOURCES:
        content = scrape_rbi_page(url)
        if content:
            results.append({
                "source": url,
                "content": content
            })
    return results


def fetch_all_policies():
    """Main function called by policy_summarizer & policy_qa."""
    local = load_local_policies()
    remote = fetch_live_rbi_guidelines()

    combined = []

    for rule in local:
        combined.append({"source": "local", "content": rule})

    for item in remote:
        combined.append(item)

    return combined
def run_policy_fetch():
    """
    Backwards-compatible wrapper used by pipeline.py.
    Returns combined local + remote policy docs.
    """
    return fetch_all_policies()
