"""
tools/get_case_status.py

ADK Python tool — retrieves the current status of a FreeStyle Libre support case.
Deployed to watsonx Orchestrate via: orchestrate tools import -k python -f tools/get_case_status.py
"""

import os
import time
import logging
from typing import Optional
from pydantic import BaseModel, Field

import httpx
from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool
from ibm_watsonx_orchestrate.agent_builder.tools.types import ToolPermission

logger = logging.getLogger(__name__)

# ─── Shared IAM token helper (same pattern as create_support_case.py) ────────

_token_cache: dict = {}


def _get_iam_token() -> str:
    now = time.time()
    if _token_cache.get("expiration", 0) - now > 60:
        return _token_cache["access_token"]

    api_key = os.environ.get("IBM_CLOUD_API_KEY", "")
    if not api_key:
        raise RuntimeError("IBM_CLOUD_API_KEY environment variable is not set.")

    response = httpx.post(
        "https://iam.cloud.ibm.com/identity/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={
            "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
            "apikey": api_key,
        },
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    _token_cache.update(data)
    return data["access_token"]


def _api_base() -> str:
    return os.environ.get(
        "ADC_SUPPORT_API_BASE_URL",
        "https://api.freestyle-support.abbott.com",
    ).rstrip("/")


# ─── I/O schemas ─────────────────────────────────────────────────────────────

class GetCaseStatusInput(BaseModel):
    case_id: str = Field(
        description="Unique case identifier returned when the case was created, e.g. CASE-20241105-00391"
    )


class GetCaseStatusOutput(BaseModel):
    case_id: str = Field(description="The case identifier")
    status: str = Field(
        description=(
            "Current case status: 'open', 'in_progress', 'pending_customer', "
            "'resolved', or 'closed'"
        )
    )
    last_updated: str = Field(description="ISO 8601 timestamp of the last status update")
    notes: Optional[str] = Field(
        default=None,
        description="Latest notes from the support team on this case"
    )
    assigned_agent: Optional[str] = Field(
        default=None,
        description="Name or ID of the support agent currently handling the case"
    )


# ─── Tool definition ─────────────────────────────────────────────────────────

@tool(
    name="GetCaseStatus",
    description=(
        "Retrieves the current status, notes, and assigned agent for an existing "
        "FreeStyle Libre sensor support case. Use this when a customer provides "
        "a case number and asks for an update, or immediately after case creation "
        "to confirm the case was received."
    ),
    permission=ToolPermission.READ_ONLY,
)
def get_case_status(case_id: str) -> GetCaseStatusOutput:
    """
    Look up the status of an existing Abbott FreeStyle Libre support case by
    its case ID.  Returns the current status, last-updated timestamp, any
    notes from the support team, and the name of the assigned agent.
    """
    if not case_id or not case_id.strip():
        raise ValueError(
            "A valid case ID is required to look up a case status. "
            "Please ask the customer to provide their case number."
        )

    url = f"{_api_base()}/api/v1/support/cases/{case_id.strip()}"

    try:
        token = _get_iam_token()
        response = httpx.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
            },
            timeout=15,
        )

        if response.status_code == 404:
            raise ValueError(
                f"No support case found with ID '{case_id}'. "
                "Please double-check the case number and try again."
            )

        response.raise_for_status()
        data = response.json()

        return GetCaseStatusOutput(
            case_id=data.get("caseId", case_id),
            status=data.get("status", "unknown"),
            last_updated=data.get("lastUpdated", ""),
            notes=data.get("notes"),
            assigned_agent=data.get("assignedAgent"),
        )

    except httpx.HTTPStatusError as exc:
        logger.error("GetCaseStatus HTTP error %s for case %s", exc.response.status_code, case_id)
        raise RuntimeError(
            f"Unable to retrieve case status at this time (HTTP {exc.response.status_code}). "
            "Please try again shortly."
        ) from exc
    except httpx.RequestError as exc:
        logger.error("GetCaseStatus network error for case %s: %s", case_id, exc)
        raise RuntimeError(
            "Unable to connect to the support system right now. Please try again in a moment."
        ) from exc
