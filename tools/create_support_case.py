"""
tools/create_support_case.py

ADK Python tool — wraps the Abbott FreeStyle Libre support case REST API.
Deployed to watsonx Orchestrate via: orchestrate tools import -k python -f tools/create_support_case.py
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

# ─── Shared IAM token helper ────────────────────────────────────────────────

_token_cache: dict = {}


def _get_iam_token() -> str:
    """
    Returns a valid IBM Cloud IAM bearer token, refreshing if within
    60 seconds of expiry.  Reads IBM_CLOUD_API_KEY from the environment.
    """
    now = time.time()
    if _token_cache.get("expiration", 0) - now > 60:
        return _token_cache["access_token"]

    api_key = os.environ.get("IBM_CLOUD_API_KEY", "")
    if not api_key:
        raise RuntimeError(
            "IBM_CLOUD_API_KEY environment variable is not set. "
            "Add it to your .env file before deploying."
        )

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
    logger.debug("IAM token refreshed, expires in %s seconds", data.get("expires_in"))
    return data["access_token"]


def _api_base() -> str:
    return os.environ.get(
        "ADC_SUPPORT_API_BASE_URL",
        "https://api.freestyle-support.abbott.com",
    ).rstrip("/")


# ─── Pydantic models for structured I/O ─────────────────────────────────────

class CustomerInfo(BaseModel):
    first_name: str = Field(description="Customer's first name")
    last_name: str = Field(description="Customer's last name")
    email: str = Field(description="Customer's email address")
    phone: str = Field(description="Customer's phone number including country code")


class ProductInfo(BaseModel):
    product_model: str = Field(
        description="FreeStyle Libre model, e.g. 'FreeStyle Libre 3'"
    )
    sensor_serial_number: str = Field(
        description="Sensor serial number from the applicator packaging (8-16 alphanumeric characters)"
    )
    lot_number: str = Field(
        description="Lot number printed on the sensor packaging"
    )
    sensor_start_date: str = Field(
        description="Date the sensor was applied, in YYYY-MM-DD format"
    )


class IssueInfo(BaseModel):
    failure_date: str = Field(
        description="Date the issue was first noticed, in YYYY-MM-DD format"
    )
    failure_description: str = Field(
        description="Detailed description of the issue as reported by the customer"
    )
    device_error_codes: Optional[list[str]] = Field(
        default=None,
        description="List of error codes displayed on the sensor, reader, or app"
    )
    document_ids: Optional[list[str]] = Field(
        default=None,
        description="Document IDs returned by the UploadSupportingDocuments tool"
    )


class EligibilityResult(BaseModel):
    eligibility_status: str = Field(
        description="Eligibility determination: 'Eligible', 'Needs Review', or 'Not Eligible'"
    )
    justification: str = Field(
        description="Plain-language justification for the eligibility decision"
    )
    policy_reference: str = Field(
        description="Reference to the warranty or replacement policy section"
    )
    confidence_score: Optional[float] = Field(
        default=None,
        description="Confidence score between 0.0 and 1.0 for the eligibility determination"
    )


class CreateCaseInput(BaseModel):
    customer_info: CustomerInfo
    product_info: ProductInfo
    issue_info: IssueInfo
    eligibility_result: EligibilityResult


class CreateCaseOutput(BaseModel):
    case_id: str = Field(description="Unique case identifier, e.g. CASE-20241105-00391")
    status: str = Field(description="Initial status of the created case, e.g. 'open'")
    estimated_response_time: str = Field(
        description="Estimated response time, e.g. '1-2 business days'"
    )
    created_at: str = Field(description="ISO 8601 timestamp of case creation")


# ─── Tool definition ─────────────────────────────────────────────────────────

@tool(
    name="CreateSupportCase",
    description=(
        "Creates a new FreeStyle Libre sensor support case in Abbott's CRM. "
        "Call this tool only after customer information, product details, issue details, "
        "and eligibility determination have all been collected and confirmed. "
        "Returns a case ID, status, and estimated response time."
    ),
    permission=ToolPermission.READ_WRITE,
)
def create_support_case(
    customer_info: CustomerInfo,
    product_info: ProductInfo,
    issue_info: IssueInfo,
    eligibility_result: EligibilityResult,
) -> CreateCaseOutput:
    """
    Submit a fully assembled FreeStyle Libre sensor support case to the Abbott
    support backend via REST API.

    Retries up to 3 times on transient server errors (5xx) with a 2-second
    delay between attempts.
    """
    payload = {
        "customerInfo": {
            "firstName": customer_info.first_name,
            "lastName": customer_info.last_name,
            "email": customer_info.email,
            "phone": customer_info.phone,
        },
        "productInfo": {
            "productModel": product_info.product_model,
            "sensorSerialNumber": product_info.sensor_serial_number,
            "lotNumber": product_info.lot_number,
            "sensorStartDate": product_info.sensor_start_date,
        },
        "issueInfo": {
            "failureDate": issue_info.failure_date,
            "failureDescription": issue_info.failure_description,
            "deviceErrorCodes": issue_info.device_error_codes or [],
            "documentIds": issue_info.document_ids or [],
        },
        "eligibilityResult": {
            "status": eligibility_result.eligibility_status,
            "justification": eligibility_result.justification,
            "policyReference": eligibility_result.policy_reference,
            "confidenceScore": eligibility_result.confidence_score,
        },
    }

    url = f"{_api_base()}/api/v1/support/cases"
    last_error: Exception | None = None

    for attempt in range(1, 4):
        try:
            token = _get_iam_token()
            response = httpx.post(
                url,
                json=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return CreateCaseOutput(
                case_id=data["caseId"],
                status=data["status"],
                estimated_response_time=data.get("estimatedResponseTime", "2 business days"),
                created_at=data.get("createdAt", ""),
            )
        except httpx.HTTPStatusError as exc:
            # Don't retry client errors (4xx) — only server errors (5xx)
            if exc.response.status_code < 500:
                logger.error(
                    "CreateSupportCase failed with client error %s on attempt %d",
                    exc.response.status_code,
                    attempt,
                )
                raise RuntimeError(
                    f"Case creation failed: HTTP {exc.response.status_code}. "
                    "Please verify the submitted information and try again."
                ) from exc
            last_error = exc
            logger.warning(
                "CreateSupportCase server error %s on attempt %d of 3 — retrying in 2s",
                exc.response.status_code,
                attempt,
            )
        except httpx.RequestError as exc:
            last_error = exc
            logger.warning(
                "CreateSupportCase network error on attempt %d of 3 — retrying in 2s: %s",
                attempt,
                exc,
            )

        if attempt < 3:
            time.sleep(2)

    raise RuntimeError(
        "Case creation failed after 3 attempts due to a server error. "
        "A support specialist will follow up with you within 1 business day."
    ) from last_error
