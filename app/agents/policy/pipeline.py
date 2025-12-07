"""
Policy & Rules Pipeline
-----------------------

High-level orchestrator for the policy team.

Master agent calls:  await run_policy_pipeline(PolicyQARequest)
"""

from typing import List

from app.schemas import (
    PolicyQARequest,
    PolicyQAResponse,
    PolicyRawDocument,
    PolicyEntry,
)

from .policy_fetch import run_policy_fetch
from .policy_summarizer import run_policy_summarizer
from .policy_qa import run_policy_qa


async def run_policy_pipeline(request: PolicyQARequest) -> PolicyQAResponse:
    """
    End-to-end policy QA pipeline.

    1. Fetch / load raw policy docs (can be static for hackathon).
    2. Summarize them into PolicyEntry objects.
    3. Answer the user's question using those entries.
    """

    # 1. Fetch raw docs (or load from local JSON)
    raw_docs: List[PolicyRawDocument] = await run_policy_fetch()

    # 2. Summarize into structured entries (FAQ-style)
    policy_entries: List[PolicyEntry] = await run_policy_summarizer(raw_docs)

    # 3. RAG-style QA
    response: PolicyQAResponse = await run_policy_qa(
        request=request,
        policy_entries=policy_entries,
    )

    return response
