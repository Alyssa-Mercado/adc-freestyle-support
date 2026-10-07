"""
tools/upload_supporting_documents.py

ADK Python tool — uploads supporting documents (sensor photos, error screenshots)
for a FreeStyle Libre support case.

Deployed to watsonx Orchestrate via:
    orchestrate tools import -k python -f tools/upload_supporting_documents.py
"""

import base64
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

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "application/pdf"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


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

class UploadDocumentOutput(BaseModel):
    document_id: str = Field(
        description="Unique document identifier to include in the CreateSupportCase documentIds field"
    )
    uploaded_at: str = Field(description="ISO 8601 timestamp of the upload")
    status: str = Field(
        description="Upload status: 'accepted', 'processing', 'ready', or 'rejected'"
    )


# ─── Tool definition ─────────────────────────────────────────────────────────

@tool(
    name="UploadSupportingDocuments",
    description=(
        "Uploads a supporting document — such as a photo of the failed sensor, "
        "a screenshot of the error message, or a photo of the sensor packaging — "
        "for a FreeStyle Libre support case. "
        "Accepts JPEG, PNG, or PDF files up to 10 MB. "
        "Returns a document_id that must be included when creating the support case. "
        "Call this tool BEFORE calling CreateSupportCase if the customer has images to attach."
    ),
    permission=ToolPermission.READ_WRITE,
)
def upload_supporting_documents(
    file_content_base64: str = Field(
        description="Base64-encoded content of the file to upload"
    ),
    file_name: str = Field(
        description="Original file name including extension, e.g. 'sensor_photo.jpg'"
    ),
    mime_type: str = Field(
        description="MIME type of the file: 'image/jpeg', 'image/png', or 'application/pdf'"
    ),
    case_reference: Optional[str] = Field(
        default=None,
        description=(
            "Case ID to associate this document with, if the case already exists. "
            "If the case has not been created yet, leave this empty."
        ),
    ),
) -> UploadDocumentOutput:
    """
    Upload a supporting document to the Abbott support document storage service.
    The returned document_id should be passed to CreateSupportCase in the
    issue_info.document_ids list.

    Validates:
    - MIME type is one of: image/jpeg, image/png, application/pdf
    - Decoded file size does not exceed 10 MB
    """
    # Validate MIME type
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(
            f"Unsupported file type '{mime_type}'. "
            "Please upload a JPEG image, PNG image, or PDF document."
        )

    # Validate file size
    try:
        decoded = base64.b64decode(file_content_base64)
    except Exception as exc:
        raise ValueError(
            "The file content could not be decoded. "
            "Please ensure the file is base64-encoded before uploading."
        ) from exc

    if len(decoded) > MAX_FILE_SIZE_BYTES:
        size_mb = len(decoded) / (1024 * 1024)
        raise ValueError(
            f"File size {size_mb:.1f} MB exceeds the 10 MB limit. "
            "Please reduce the file size and try again."
        )

    payload = {
        "file": file_content_base64,
        "fileName": file_name,
        "mimeType": mime_type,
        "caseReference": case_reference or "",
    }

    url = f"{_api_base()}/api/v1/support/documents"
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
                timeout=60,  # larger timeout for file uploads
            )
            response.raise_for_status()
            data = response.json()
            return UploadDocumentOutput(
                document_id=data["documentId"],
                uploaded_at=data.get("uploadedAt", ""),
                status=data.get("status", "accepted"),
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                logger.error(
                    "UploadSupportingDocuments client error %s on attempt %d",
                    exc.response.status_code,
                    attempt,
                )
                raise RuntimeError(
                    f"Document upload failed: HTTP {exc.response.status_code}. "
                    "Please check the file and try again."
                ) from exc
            last_error = exc
            logger.warning(
                "UploadSupportingDocuments server error on attempt %d of 3 — retrying", attempt
            )
        except httpx.RequestError as exc:
            last_error = exc
            logger.warning(
                "UploadSupportingDocuments network error on attempt %d of 3: %s", attempt, exc
            )

        if attempt < 3:
            time.sleep(2)

    raise RuntimeError(
        "Document upload failed after 3 attempts. "
        "Your case can still be created — you can email the images to Abbott support "
        "and reference your case number."
    ) from last_error
