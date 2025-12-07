"""
Policy QA Agent
---------------

Input:
- PolicyQARequest (user question + language)
- List[PolicyEntry] (summarized policies)

Output:
- PolicyQAResponse (answer, steps, disclaimers, source_ids)

We do a very lightweight "RAG":
- Filter / rank entries by simple keyword overlap
- Send the most relevant ones to Gemini 3 with a QA prompt
"""

from typing import List
from pathlib import Path

from app.schemas import PolicyQARequest, PolicyQAResponse, PolicyEntry
from app.core.gemini import run_gemini


PROMPT_PATH = "app/agents/policy/prompts/qa_prompt.txt"


def _load_prompt() -> str:
    return Path(PROMPT_PATH).read_text(encoding="utf-8")


def _simple_rank_entries(question: str, entries: List[PolicyEntry], top_k: int = 3) -> List[PolicyEntry]:
    """
    Very naive ranking: count keyword overlap between question and entry text.

    Good enough for hackathon demo, and very small corpus.
    """

    question_lower = question.lower()
    keywords = set(question_lower.split())
    scored: List[tuple[int, PolicyEntry]] = []

    for entry in entries:
        text = (
            " ".join(entry.summary_bullets)
            + " "
            + (entry.when_it_applies or "")
            + " "
            + " ".join(entry.actions_if_affected)
        ).lower()
        score = sum(1 for w in keywords if w in text)
        scored.append((score, entry))

    # Sort by descending score, keep those with score > 0
    scored.sort(key=lambda x: x[0], reverse=True)
    filtered = [e for s, e in scored if s > 0]

    # If no entry matched, just return the first few
    if not filtered:
        return entries[:top_k]

    return filtered[:top_k]


async def run_policy_qa(
    request: PolicyQARequest,
    policy_entries: List[PolicyEntry],
) -> PolicyQAResponse:
    """
    Main QA function: select relevant entries and ask Gemini 3 to answer.
    """

    prompt = _load_prompt()

    # 1. Select top-k relevant entries
    top_entries = _simple_rank_entries(request.question, policy_entries, top_k=3)

    # 2. Prepare payload for Gemini
    payload = {
        "system_instruction": prompt,
        "user": {
            "question": request.question,
            "language": request.language,
            "policies": [e.model_dump() for e in top_entries],
        },
    }

    llm_response = await run_gemini(payload)

    try:
        response = PolicyQAResponse.model_validate(llm_response)
    except Exception as exc:
        print(f"[PolicyQA] Failed to parse PolicyQAResponse: {exc}")
        # Fallback answer
        response = PolicyQAResponse(
            language=request.language,
            answer=(
                "I'm sorry, I couldn't generate a detailed answer right now. "
                "However, you should immediately contact your bank's official customer support "
                "and verify the latest RBI/SEBI guidelines on their official website."
            ),
            steps=[
                "Contact your bank through the official app, website, or branch.",
                "Do not share OTP, PIN, or passwords with anyone on calls or messages.",
                "Check RBI or SEBI official website for updated rules.",
            ],
            disclaimers=[
                "This is not legal advice.",
                "Financial regulations can change; always verify with official sources.",
            ],
            source_ids=[e.id for e in top_entries],
        )

    # Ensure source_ids are present (helpful for UI)
    if not response.source_ids:
        response.source_ids = [e.id for e in top_entries]

    return response
