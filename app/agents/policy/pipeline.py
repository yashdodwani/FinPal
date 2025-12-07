"""
Policy & Rules Pipeline
-----------------------

Responsible for:

1. Fetching raw policy/rule text (optional for hackathon).
2. Summarizing policy docs into structured entries.
3. Running a RAG-style QA over the summarized entries.

Master agent calls:  await run_policy_pipeline(PolicyQARequest)
"""

from app.schemas import (
    PolicyQARequest,
    PolicyQAResponse,
    PolicyEntry,
)

from .policy_fetch import run_policy_fetch
from .policy_summarizer import run_policy_summarizer
from .policy_qa import run_policy_qa


async def run_policy_pipeline(request: PolicyQARequest) -> PolicyQAResponse:
    """
    End-to-end policy QA pipeline.
    """

    # NOTE: For hackathon speed, you MAY skip real fetch and load static data.
    raw_docs = await run_policy_fetch()

    # Summarize docs to structured FAQ entries
    policy_entries: list[PolicyEntry] = await run_policy_summarizer(raw_docs)

    # Perform retrieval + QA
    response: PolicyQAResponse = await run_policy_qa(
        request=request,
        policy_entries=policy_entries,
    )

    return response
