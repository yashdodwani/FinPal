"""
Policy Summarizer Agent
-----------------------

Input: List[PolicyRawDocument]
Output: List[PolicyEntry]

Uses Gemini 3 to:
- Convert raw regulatory language into user-friendly bullets
- Provide 'when it applies' and 'actions_if_affected'
"""

from typing import List
from pathlib import Path

from app.schemas import PolicyRawDocument, PolicyEntry
from app.core.gemini import run_gemini

PROMPT_PATH = "app/agents/policy/prompts/summarize_prompt.txt"


def _load_prompt() -> str:
    return Path(PROMPT_PATH).read_text(encoding="utf-8")


async def run_policy_summarizer(raw_docs: List[PolicyRawDocument]) -> List[PolicyEntry]:
    """
    Summarize raw policy documents into structured PolicyEntry objects.
    """

    prompt = _load_prompt()

    # You can summarize one-by-one for clarity (small number of docs)
    entries: List[PolicyEntry] = []

    for doc in raw_docs:
        payload = {
            "system_instruction": prompt,
            "user": {
                "id": doc.id,
                "title": doc.title,
                "source": doc.source,
                "raw_text": doc.raw_text,
            },
        }

        llm_response = await run_gemini(payload)

        try:
            entry = PolicyEntry.model_validate(llm_response)
            entries.append(entry)
        except Exception as exc:
            # If parsing fails, create a fallback entry with minimal info
            print(f"[PolicySummarizer] Failed to parse PolicyEntry for {doc.id}: {exc}")
            entries.append(
                PolicyEntry(
                    id=doc.id,
                    title=doc.title,
                    category="general",
                    target_user="general_public",
                    summary_bullets=[doc.raw_text[:200] + "..."],
                    when_it_applies=None,
                    actions_if_affected=[],
                )
            )

    return entries
