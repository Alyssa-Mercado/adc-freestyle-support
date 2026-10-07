"""
tools/lookup_sensor_diagnostics.py

ADK Python tool — looks up FreeStyle Libre error codes and sensor diagnostic
information from Abbott's diagnostics knowledge API.

Deployed to watsonx Orchestrate via:
    orchestrate tools import -k python -f tools/lookup_sensor_diagnostics.py
"""

import os
import logging
from typing import Optional
from pydantic import BaseModel, Field

import httpx
from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool
from ibm_watsonx_orchestrate.agent_builder.tools.types import ToolPermission

logger = logging.getLogger(__name__)

# ── Hardcoded diagnostic catalogue (offline fallback) ────────────────────────
# Mirrors what the mock API returns. Used when the API is unreachable so the
# troubleshooting agent can still function during demos without network access.

_OFFLINE_CATALOGUE: dict[str, dict] = {
    "E1": {
        "code": "E1",
        "title": "Low Battery",
        "description": "The FreeStyle Libre reader battery is critically low.",
        "recommended_action": "Charge the reader using the provided USB cable for at least 30 minutes before scanning again.",
        "severity": "low",
        "replacement_indicative": False,
        "category": "reader_device",
    },
    "E2": {
        "code": "E2",
        "title": "Temperature Out of Range",
        "description": "The sensor or reader is outside the operating temperature range (4C to 40C / 39F to 104F).",
        "recommended_action": "Move to a room-temperature environment (15C to 30C) and wait 15 minutes before scanning.",
        "severity": "medium",
        "replacement_indicative": False,
        "category": "sensor_failure",
    },
    "E3": {
        "code": "E3",
        "title": "Sensor Error",
        "description": "The sensor has encountered an unrecoverable internal error. The sensor cannot provide glucose readings.",
        "recommended_action": "Remove the sensor. Do not reapply. Contact FreeStyle Libre Support to initiate a replacement review.",
        "severity": "high",
        "replacement_indicative": True,
        "category": "sensor_failure",
    },
    "E4": {
        "code": "E4",
        "title": "Sensor Warmup",
        "description": "The sensor is in its initial 60-minute warmup period. No readings are available yet.",
        "recommended_action": "Wait for the warmup timer to complete. The app or reader will notify you when readings are ready.",
        "severity": "low",
        "replacement_indicative": False,
        "category": "sensor_failure",
    },
    "E5": {
        "code": "E5",
        "title": "Sensor Expired",
        "description": "The sensor has reached the end of its 14-day wear period.",
        "recommended_action": "Apply a new sensor. Ensure the new sensor lot number has not expired.",
        "severity": "low",
        "replacement_indicative": False,
        "category": "sensor_failure",
    },
    "E6": {
        "code": "E6",
        "title": "NFC Read Failure",
        "description": "The reader or phone could not establish an NFC connection with the sensor.",
        "recommended_action": "Remove any thick or metal phone case. Hold the reader flat and centered directly over the sensor dome for 1 to 2 seconds. Retry 3 times.",
        "severity": "medium",
        "replacement_indicative": False,
        "category": "scan_errors",
    },
    "E7": {
        "code": "E7",
        "title": "Sensor Not Detected",
        "description": "No sensor was detected during the scan. The sensor may have detached or shifted.",
        "recommended_action": "Check that the sensor is still firmly attached to the back of the upper arm. If detached before 14 days, contact support for a replacement review.",
        "severity": "medium",
        "replacement_indicative": True,
        "category": "sensor_fell_off",
    },
    "E8": {
        "code": "E8",
        "title": "Reader Software Error",
        "description": "The reader firmware has encountered a software exception.",
        "recommended_action": "Hold the power button for 10 seconds to force a restart. If the error persists, connect to the FreeStyle LibreLink Desktop software to check for firmware updates.",
        "severity": "medium",
        "replacement_indicative": False,
        "category": "reader_device",
    },
    "APP-001": {
        "code": "APP-001",
        "title": "LibreLink Sync Failure",
        "description": "FreeStyle LibreLink could not synchronize data with LibreView cloud.",
        "recommended_action": "Verify the device has internet access. Toggle airplane mode off and on. Open LibreLink, go to Settings > Connected Services, and reconnect LibreView.",
        "severity": "low",
        "replacement_indicative": False,
        "category": "app_connectivity",
    },
    "APP-002": {
        "code": "APP-002",
        "title": "Unsupported Device",
        "description": "This phone or OS version is not on the FreeStyle LibreLink compatibility list.",
        "recommended_action": "Visit the FreeStyle LibreLink compatibility page to confirm your device is supported. Use the dedicated reader as an alternative.",
        "severity": "medium",
        "replacement_indicative": False,
        "category": "app_connectivity",
    },
    "DASH": {
        "code": "DASH",
        "title": "No Reading / Dashes",
        "description": "The reader or app is displaying dashes instead of a glucose value. This typically indicates the sensor is not transmitting data.",
        "recommended_action": "Attempt to scan again. If dashes persist for more than 3 scans over 10 minutes and the sensor warm-up has completed, the sensor may have failed. Contact support.",
        "severity": "high",
        "replacement_indicative": True,
        "category": "sensor_failure",
    },
}


def _api_base() -> str:
    return os.environ.get(
        "ADC_SUPPORT_API_BASE_URL",
        "https://api.freestyle-support.abbott.com",
    ).rstrip("/")


# ── Pydantic I/O models ──────────────────────────────────────────────────────

class DiagnosticsInput(BaseModel):
    error_code: str = Field(
        description=(
            "The error code displayed on the sensor, FreeStyle Libre reader, or LibreLink app. "
            "Examples: E3, E6, APP-001, DASH. Case-insensitive."
        )
    )
    product_model: Optional[str] = Field(
        default=None,
        description="FreeStyle Libre product model, e.g. 'FreeStyle Libre 3'. Optional context for model-specific guidance.",
    )


class DiagnosticsOutput(BaseModel):
    code: str = Field(description="Normalized error code")
    title: str = Field(description="Short human-readable error title")
    description: str = Field(description="Plain-language explanation of what the error means")
    recommended_action: str = Field(description="Step-by-step recommended resolution for the support agent to present to the customer")
    severity: str = Field(description="Severity level: low, medium, or high")
    replacement_indicative: bool = Field(description="True if this error code commonly indicates a sensor or device replacement is warranted")
    category: str = Field(description="Issue category: sensor_fell_off, sensor_failure, inaccurate_readings, scan_errors, app_connectivity, or reader_device")
    source: str = Field(description="Data source: api or offline_catalogue")


# ── Tool definition ──────────────────────────────────────────────────────────

@tool(
    name="LookupSensorDiagnostics",
    description=(
        "Looks up a FreeStyle Libre error code and returns a plain-language explanation, "
        "recommended resolution steps, severity level, and whether the error is indicative "
        "of a sensor or device replacement. Use this tool during troubleshooting whenever "
        "a customer reports an error code on their sensor, reader, or LibreLink app."
    ),
    permission=ToolPermission.READ,
)
def lookup_sensor_diagnostics(
    error_code: str,
    product_model: Optional[str] = None,
) -> DiagnosticsOutput:
    """
    Resolves a FreeStyle Libre error code to diagnostic guidance.

    Tries the live mock/production API first. Falls back to the offline
    catalogue if the API is unreachable, so troubleshooting is never blocked.
    """
    normalized = error_code.strip().upper()
    url = f"{_api_base()}/api/v1/diagnostics/{normalized}"

    # 1. Try live API
    try:
        response = httpx.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return DiagnosticsOutput(**data, source="api")
        if response.status_code == 404:
            logger.info("Error code %s not found in API — falling back to offline catalogue", normalized)
    except httpx.RequestError as exc:
        logger.warning("Diagnostics API unreachable (%s) — using offline catalogue", exc)

    # 2. Offline catalogue fallback
    entry = _OFFLINE_CATALOGUE.get(normalized)
    if entry:
        return DiagnosticsOutput(**entry, source="offline_catalogue")

    # 3. Unknown code — return a safe default so the agent can still proceed
    return DiagnosticsOutput(
        code=normalized,
        title="Unknown Error Code",
        description=f"Error code '{normalized}' was not found in the FreeStyle Libre diagnostic catalogue.",
        recommended_action=(
            "Ask the customer to describe what is displayed on screen in addition to the error code. "
            "Collect the code as part of the support case and escalate to a Tier 2 specialist."
        ),
        severity="medium",
        replacement_indicative=False,
        category="unknown",
        source="offline_catalogue",
    )
