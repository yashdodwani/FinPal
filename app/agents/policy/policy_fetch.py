"""
Policy Fetch Agent
------------------

For hackathon speed, this can:
- Load a few static sample policies from code or JSON files, OR
- Later be extended to call HTTP APIs / scrape RBI/SEBI.

Right now, we just return a small hard-coded set of PolicyRawDocument objects
you can tweak quickly.
"""

from typing import List

from app.schemas import PolicyRawDocument


async def run_policy_fetch() -> List[PolicyRawDocument]:
    """
    Return a small list of raw policy/regulation texts.

    In a real system, this would:
    - fetch from RBI/SEBI/NPCI websites
    - load from JSON files in app/data/policies
    - run cleaning/normalization

    For the hackathon, these 2–3 examples are enough to show functionality.
    """

    docs: List[PolicyRawDocument] = [
        PolicyRawDocument(
            id="rbi_upi_fraud_reporting",
            source="RBI",
            title="UPI Fraud Reporting Timelines",
            url=None,
            raw_text=(
                "If a customer reports an unauthorised electronic transaction to the bank "
                "within three working days, and the customer has not shared credentials "
                "knowingly or acted fraudulently, the customer shall bear zero liability. "
                "If the report is made after three days but within seven working days, "
                "the customer's liability shall be limited to the transaction value or "
                "the value defined by RBI guidelines, whichever is lower."
            ),
        ),
        PolicyRawDocument(
            id="upi_never_share_otp_pin",
            source="NPCI",
            title="UPI OTP / PIN Safety Guidelines",
            url=None,
            raw_text=(
                "Customers must never share their UPI PIN, OTP, or full card details with "
                "anyone, including people claiming to be from the bank, RBI, or support. "
                "Banks and official institutions will never ask for PIN, OTP, or full passwords "
                "over phone, SMS, email, or chat."
            ),
        ),
        PolicyRawDocument(
            id="digital_lending_charges_transparency",
            source="RBI",
            title="Digital Lending – Charges and Transparency",
            url=None,
            raw_text=(
                "All digital lenders must clearly disclose the annual percentage rate (APR), "
                "all fees, charges, and penalties before execution of the loan contract. "
                "Hidden charges or undisclosed fees are not permitted under RBI digital lending guidelines."
            ),
        ),
    ]

    return docs
