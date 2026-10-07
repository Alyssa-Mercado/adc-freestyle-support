"""
tools/track_shipment.py

ADK Python tool — queries Abbott's shipment tracking API to look up the
delivery status of a replacement sensor or device shipment.

Deployed to watsonx Orchestrate via:
    orchestrate tools import -k python -f tools/track_shipment.py
"""

import os
import logging
from typing import Optional
from pydantic import BaseModel, Field

import httpx
from ibm_watsonx_orchestrate.agent_builder.tools.python_tool import tool
from ibm_watsonx_orchestrate.agent_builder.tools.types import ToolPermission

logger = logging.getLogger(__name__)

# ── Offline shipment catalogue (demo / fallback) ─────────────────────────────
# Returned when the real API is unreachable, so the agent can still demo the
# full conversation flow end-to-end without a live backend.

_SAMPLE_SHIPMENTS: dict[str, dict] = {
    "SHIP-20261001-00001": {
        "shipmentId": "SHIP-20261001-00001",
        "caseId": "CASE-20261001-00001",
        "carrier": "FedEx",
        "trackingNumber": "778133890023685",
        "status": "in_transit",
        "statusLabel": "In Transit",
        "estimatedDelivery": "2026-10-05",
        "lastEvent": "Departed FedEx hub — Memphis, TN",
        "lastEventTimestamp": "2026-10-03T22:14:00Z",
        "origin": "Abbott Distribution Center — Alameda, CA",
        "destination": "Customer address on file",
        "shipmentItems": ["FreeStyle Libre 3 Sensor (1-pack)"],
        "trackingUrl": "https://www.fedex.com/fedextrack/?trknbr=778133890023685",
    },
    "SHIP-20261001-00002": {
        "shipmentId": "SHIP-20261001-00002",
        "caseId": "CASE-20261001-00002",
        "carrier": "UPS",
        "trackingNumber": "1Z999AA10123456784",
        "status": "pending",
        "statusLabel": "Pending Shipment",
        "estimatedDelivery": "2026-10-08",
        "lastEvent": "Shipment label created — awaiting carrier pickup",
        "lastEventTimestamp": "2026-10-03T15:00:00Z",
        "origin": "Abbott Distribution Center — Alameda, CA",
        "destination": "Customer address on file",
        "shipmentItems": ["FreeStyle Libre 3 Sensor (1-pack)"],
        "trackingUrl": "https://www.ups.com/track?tracknum=1Z999AA10123456784",
    },
    "SHIP-20261001-00003": {
        "shipmentId": "SHIP-20261001-00003",
        "caseId": "CASE-20261001-00003",
        "carrier": "FedEx",
        "trackingNumber": "778133890023699",
        "status": "delivered",
        "statusLabel": "Delivered",
        "estimatedDelivery": "2026-10-02",
        "lastEvent": "Delivered — Front door. Signed by resident.",
        "lastEventTimestamp": "2026-10-02T14:32:00Z",
        "origin": "Abbott Distribution Center — Alameda, CA",
        "destination": "Customer address on file",
        "shipmentItems": ["FreeStyle Libre 3 Sensor (1-pack)"],
        "trackingUrl": "https://www.fedex.com/fedextrack/?trknbr=778133890023699",
    },
}


def _api_base() -> str:
    return os.environ.get(
        "ADC_SUPPORT_API_BASE_URL",
        "https://api.freestyle-support.abbott.com",
    ).rstrip("/")


# ── Pydantic I/O models ──────────────────────────────────────────────────────

class TrackShipmentInput(BaseModel):
    case_id: Optional[str] = Field(
        default=None,
        description=(
            "The support case ID associated with the shipment, e.g. CASE-20241105-00391. "
            "Use this to look up the most recent shipment for a given case."
        ),
    )
    shipment_id: Optional[str] = Field(
        default=None,
        description=(
            "The direct shipment ID, e.g. SHIP-20241105-00012. "
            "Use this if the customer has a specific shipment reference."
        ),
    )
    tracking_number: Optional[str] = Field(
        default=None,
        description=(
            "Carrier tracking number, e.g. 778133890023685 (FedEx) or 1Z999AA... (UPS). "
            "Use this if the customer provides a tracking number directly."
        ),
    )


class TrackShipmentOutput(BaseModel):
    shipment_id: str = Field(description="Unique shipment identifier")
    case_id: Optional[str] = Field(description="Associated support case ID, if available")
    carrier: str = Field(description="Shipping carrier name, e.g. FedEx, UPS")
    tracking_number: str = Field(description="Carrier tracking number")
    status: str = Field(description="Machine-readable status: pending, in_transit, out_for_delivery, delivered, exception")
    status_label: str = Field(description="Human-readable status label, e.g. 'In Transit'")
    estimated_delivery: Optional[str] = Field(description="Estimated delivery date in YYYY-MM-DD format")
    last_event: str = Field(description="Description of the most recent tracking event")
    last_event_timestamp: str = Field(description="ISO 8601 timestamp of the most recent tracking event")
    origin: str = Field(description="Shipment origin description")
    destination: str = Field(description="Shipment destination description (address masked for HIPAA)")
    shipment_items: list[str] = Field(description="List of items in the shipment")
    tracking_url: Optional[str] = Field(description="Public carrier tracking URL the customer can visit for full detail")
    source: str = Field(description="Data source: api or offline_catalogue")


# ── Tool definition ──────────────────────────────────────────────────────────

@tool(
    name="TrackShipment",
    description=(
        "Looks up the delivery status of a FreeStyle Libre replacement sensor or device shipment. "
        "Accepts a support case ID, a direct shipment ID, or a carrier tracking number. "
        "Use this tool when a customer asks about the status of a replacement they were told to expect, "
        "or after case creation to give the customer a shipment ETA. "
        "Returns carrier, tracking number, current status, estimated delivery date, and last tracking event."
    ),
    permission=ToolPermission.READ,
)
def track_shipment(
    case_id: Optional[str] = None,
    shipment_id: Optional[str] = None,
    tracking_number: Optional[str] = None,
) -> TrackShipmentOutput:
    """
    Retrieves shipment tracking information for a replacement sensor or device.

    Lookup priority:
      1. shipment_id (most specific)
      2. case_id (returns the most recent shipment linked to that case)
      3. tracking_number (carrier-level lookup via internal index)

    Falls back to the offline demo catalogue when the API is unreachable.
    """
    if not any([case_id, shipment_id, tracking_number]):
        raise ValueError(
            "At least one of case_id, shipment_id, or tracking_number must be provided."
        )

    # Build lookup key for offline fallback
    offline_key = None
    if shipment_id:
        offline_key = shipment_id.strip().upper()
    elif case_id:
        # Find the most recent sample shipment for this case
        for sid, s in _SAMPLE_SHIPMENTS.items():
            if s.get("caseId", "").upper() == case_id.strip().upper():
                offline_key = sid
                break
    elif tracking_number:
        for sid, s in _SAMPLE_SHIPMENTS.items():
            if s.get("trackingNumber", "").replace(" ", "") == tracking_number.strip().replace(" ", ""):
                offline_key = sid
                break

    # Build query params for live API
    params: dict = {}
    if shipment_id:
        params["shipmentId"] = shipment_id
    elif case_id:
        params["caseId"] = case_id
    elif tracking_number:
        params["trackingNumber"] = tracking_number

    url = f"{_api_base()}/api/v1/shipments"

    # 1. Try live API
    try:
        response = httpx.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            # API may return a list (multiple shipments); take the first
            if isinstance(data, list) and data:
                data = data[0]
            elif isinstance(data, dict) and "shipments" in data:
                shipments = data["shipments"]
                if shipments:
                    data = shipments[0]
                else:
                    data = None

            if data:
                return TrackShipmentOutput(
                    shipment_id=data.get("shipmentId", ""),
                    case_id=data.get("caseId"),
                    carrier=data.get("carrier", ""),
                    tracking_number=data.get("trackingNumber", ""),
                    status=data.get("status", ""),
                    status_label=data.get("statusLabel", data.get("status", "")),
                    estimated_delivery=data.get("estimatedDelivery"),
                    last_event=data.get("lastEvent", ""),
                    last_event_timestamp=data.get("lastEventTimestamp", ""),
                    origin=data.get("origin", "Abbott Distribution Center"),
                    destination=data.get("destination", "Customer address on file"),
                    shipment_items=data.get("shipmentItems", []),
                    tracking_url=data.get("trackingUrl"),
                    source="api",
                )

        if response.status_code == 404:
            logger.info("Shipment not found via API — checking offline catalogue")

    except httpx.RequestError as exc:
        logger.warning("Shipment API unreachable (%s) — using offline catalogue", exc)

    # 2. Offline catalogue fallback
    if offline_key and offline_key in _SAMPLE_SHIPMENTS:
        entry = _SAMPLE_SHIPMENTS[offline_key]
        return TrackShipmentOutput(
            shipment_id=entry["shipmentId"],
            case_id=entry.get("caseId"),
            carrier=entry["carrier"],
            tracking_number=entry["trackingNumber"],
            status=entry["status"],
            status_label=entry["statusLabel"],
            estimated_delivery=entry.get("estimatedDelivery"),
            last_event=entry["lastEvent"],
            last_event_timestamp=entry["lastEventTimestamp"],
            origin=entry["origin"],
            destination=entry["destination"],
            shipment_items=entry.get("shipmentItems", []),
            tracking_url=entry.get("trackingUrl"),
            source="offline_catalogue",
        )

    # 3. No match found
    identifier = shipment_id or case_id or tracking_number
    raise ValueError(
        f"No shipment found for '{identifier}'. "
        "If a replacement was recently approved, it may take 1 business day for tracking information to appear. "
        "Please ask the customer to check back later or contact support if they expected a shipment."
    )
