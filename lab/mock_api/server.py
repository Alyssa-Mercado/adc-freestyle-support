"""
lab/mock_api/server.py

Mock REST API server for the Abbott FreeStyle Libre AI Support Lab.
Simulates the Abbott Support Case backend so the watsonx Orchestrate
tools work end-to-end without a real API connection.

Usage:
    pip install flask
    python3 lab/mock_api/server.py

The server runs on http://localhost:5001
Set ADC_SUPPORT_API_BASE_URL=http://localhost:5001 in your .env file.
"""

import json
import uuid
import logging
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ─── In-memory stores ─────────────────────────────────────────────────────────
cases: dict = {}
documents: dict = {}
shipments: dict = {}

# ─── Pre-loaded demo cases ────────────────────────────────────────────────────
SAMPLE_CASES = {
    "CASE-20261001-00001": {
        "caseId": "CASE-20261001-00001",
        "status": "in_progress",
        "lastUpdated": "2026-10-02T09:15:00Z",
        "notes": "Replacement sensor approved and dispatched via priority shipping. Expected delivery 2-3 business days.",
        "assignedAgent": "Sarah Johnson - Tier 2 Support",
        "estimatedResponseTime": "Within 1-2 business days",
        "createdAt": "2026-10-01T14:30:00Z",
    },
    "CASE-20261001-00002": {
        "caseId": "CASE-20261001-00002",
        "status": "pending_customer",
        "lastUpdated": "2026-10-03T11:00:00Z",
        "notes": "Awaiting additional photos of the sensor adhesive from the customer.",
        "assignedAgent": "Mike Chen - Tier 2 Support",
        "estimatedResponseTime": "Within 2-3 business days pending specialist review",
        "createdAt": "2026-10-02T10:00:00Z",
    },
    "CASE-20261001-00003": {
        "caseId": "CASE-20261001-00003",
        "status": "resolved",
        "lastUpdated": "2026-10-04T16:45:00Z",
        "notes": "Replacement sensor delivered. Customer confirmed receipt. Case closed.",
        "assignedAgent": "Sarah Johnson - Tier 2 Support",
        "estimatedResponseTime": "Resolved",
        "createdAt": "2026-09-29T09:00:00Z",
    },
}
cases.update(SAMPLE_CASES)

# ─── Pre-loaded demo shipments ────────────────────────────────────────────────
SAMPLE_SHIPMENTS = {
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
shipments.update(SAMPLE_SHIPMENTS)

# ─── Sensor diagnostics catalogue ─────────────────────────────────────────────
DIAGNOSTICS_CATALOGUE = {
    "E1": {
        "code": "E1", "title": "Low Battery",
        "description": "The FreeStyle Libre reader battery is critically low.",
        "recommended_action": "Charge the reader using the provided USB cable for at least 30 minutes before scanning again.",
        "severity": "low", "replacement_indicative": False, "category": "reader_device",
    },
    "E2": {
        "code": "E2", "title": "Temperature Out of Range",
        "description": "The sensor or reader is outside the operating temperature range (4C to 40C / 39F to 104F).",
        "recommended_action": "Move to a room-temperature environment (15C to 30C) and wait 15 minutes before scanning.",
        "severity": "medium", "replacement_indicative": False, "category": "sensor_failure",
    },
    "E3": {
        "code": "E3", "title": "Sensor Error",
        "description": "The sensor has encountered an unrecoverable internal error and cannot provide glucose readings.",
        "recommended_action": "Remove the sensor. Do not reapply. Contact FreeStyle Libre Support to initiate a replacement review.",
        "severity": "high", "replacement_indicative": True, "category": "sensor_failure",
    },
    "E4": {
        "code": "E4", "title": "Sensor Warmup",
        "description": "The sensor is in its initial 60-minute warmup period. No readings are available yet.",
        "recommended_action": "Wait for the warmup timer to complete. The app or reader will notify you when readings are ready.",
        "severity": "low", "replacement_indicative": False, "category": "sensor_failure",
    },
    "E5": {
        "code": "E5", "title": "Sensor Expired",
        "description": "The sensor has reached the end of its 14-day wear period.",
        "recommended_action": "Apply a new sensor. Ensure the new sensor lot number has not expired.",
        "severity": "low", "replacement_indicative": False, "category": "sensor_failure",
    },
    "E6": {
        "code": "E6", "title": "NFC Read Failure",
        "description": "The reader or phone could not establish an NFC connection with the sensor.",
        "recommended_action": "Remove any thick or metal phone case. Hold the reader flat and centered over the sensor for 1-2 seconds. Retry 3 times.",
        "severity": "medium", "replacement_indicative": False, "category": "scan_errors",
    },
    "E7": {
        "code": "E7", "title": "Sensor Not Detected",
        "description": "No sensor was detected during the scan. The sensor may have detached or shifted.",
        "recommended_action": "Check that the sensor is still firmly attached to the back of the upper arm. If detached before 14 days, contact support for a replacement review.",
        "severity": "medium", "replacement_indicative": True, "category": "sensor_fell_off",
    },
    "E8": {
        "code": "E8", "title": "Reader Software Error",
        "description": "The reader firmware has encountered a software exception.",
        "recommended_action": "Hold the power button for 10 seconds to force a restart. If the error persists, connect to FreeStyle LibreLink Desktop for firmware updates.",
        "severity": "medium", "replacement_indicative": False, "category": "reader_device",
    },
    "APP-001": {
        "code": "APP-001", "title": "LibreLink Sync Failure",
        "description": "FreeStyle LibreLink could not synchronize data with LibreView cloud.",
        "recommended_action": "Verify internet access. Toggle airplane mode. Go to Settings > Connected Services in LibreLink and reconnect LibreView.",
        "severity": "low", "replacement_indicative": False, "category": "app_connectivity",
    },
    "APP-002": {
        "code": "APP-002", "title": "Unsupported Device",
        "description": "This phone or OS version is not on the FreeStyle LibreLink compatibility list.",
        "recommended_action": "Visit the FreeStyle LibreLink compatibility page to confirm support. Use the dedicated reader as an alternative.",
        "severity": "medium", "replacement_indicative": False, "category": "app_connectivity",
    },
    "DASH": {
        "code": "DASH", "title": "No Reading / Dashes",
        "description": "Dashes are displayed instead of a glucose value, indicating the sensor is not transmitting data.",
        "recommended_action": "Attempt to scan again. If dashes persist for more than 3 scans over 10 minutes after warmup, the sensor may have failed. Contact support.",
        "severity": "high", "replacement_indicative": True, "category": "sensor_failure",
    },
}


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _new_case_id() -> str:
    date = datetime.utcnow().strftime("%Y%m%d")
    seq = str(len(cases) + 1).zfill(5)
    return f"CASE-{date}-{seq}"


def _eta(eligibility_status: str) -> str:
    status = (eligibility_status or "").lower()
    if "eligible" in status and "not" not in status:
        return "Within 1-2 business days"
    if "review" in status:
        return "Within 2-3 business days pending specialist review"
    return "Within 3-5 business days"


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "ADC Mock Support API", "timestamp": _timestamp()})


@app.route("/api/v1/support/cases", methods=["POST"])
def create_case():
    data = request.get_json(silent=True) or {}
    app.logger.info("CreateSupportCase — payload keys: %s", list(data.keys()))

    required = ["customerInfo", "productInfo", "issueInfo", "eligibilityResult"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    eligibility = data.get("eligibilityResult", {})
    eligibility_status = eligibility.get("status", "Needs Review")

    case_id = _new_case_id()
    case = {
        "caseId": case_id,
        "status": "open",
        "estimatedResponseTime": _eta(eligibility_status),
        "createdAt": _timestamp(),
        "customerInfo": data.get("customerInfo", {}),
        "productInfo": data.get("productInfo", {}),
        "issueInfo": data.get("issueInfo", {}),
        "eligibilityResult": eligibility,
        "humanReviewFlag": "review" in eligibility_status.lower(),
    }
    cases[case_id] = case
    app.logger.info("Case created: %s (eligibility: %s)", case_id, eligibility_status)

    return jsonify({
        "caseId": case_id,
        "status": "open",
        "estimatedResponseTime": case["estimatedResponseTime"],
        "createdAt": case["createdAt"],
    }), 201


@app.route("/api/v1/support/cases/<case_id>", methods=["GET"])
def get_case(case_id):
    app.logger.info("GetCaseStatus — case: %s", case_id)
    case = cases.get(case_id)
    if not case:
        return jsonify({"error": f"No case found with ID '{case_id}'"}), 404

    return jsonify({
        "caseId": case["caseId"],
        "status": case["status"],
        "lastUpdated": case.get("lastUpdated", case.get("createdAt", _timestamp())),
        "notes": case.get("notes", "Your case is being reviewed by our support team."),
        "assignedAgent": case.get("assignedAgent", "FreeStyle Libre Support Team"),
    })


@app.route("/api/v1/support/documents", methods=["POST"])
def upload_document():
    data = request.get_json(silent=True) or {}
    app.logger.info("UploadDocument — file: %s", data.get("fileName"))

    required = ["file", "fileName", "mimeType"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing required fields: {missing}"}), 400

    allowed_types = {"image/jpeg", "image/png", "application/pdf"}
    if data["mimeType"] not in allowed_types:
        return jsonify({"error": f"Unsupported MIME type: {data['mimeType']}"}), 422

    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    documents[doc_id] = {
        "documentId": doc_id,
        "fileName": data["fileName"],
        "mimeType": data["mimeType"],
        "caseReference": data.get("caseReference", ""),
        "uploadedAt": _timestamp(),
        "status": "ready",
    }
    app.logger.info("Document uploaded: %s -> %s", data["fileName"], doc_id)

    return jsonify({
        "documentId": doc_id,
        "uploadedAt": documents[doc_id]["uploadedAt"],
        "status": "ready",
    }), 201


@app.route("/api/v1/support/cases", methods=["GET"])
def list_cases():
    return jsonify({
        "cases": [
            {"caseId": c["caseId"], "status": c["status"], "createdAt": c.get("createdAt")}
            for c in cases.values()
        ],
        "total": len(cases),
    })


# ─── Diagnostics endpoint ──────────────────────────────────────────────────────
@app.route("/api/v1/diagnostics/<code>", methods=["GET"])
def get_diagnostic(code):
    normalized = code.strip().upper()
    app.logger.info("LookupSensorDiagnostics — code: %s", normalized)
    entry = DIAGNOSTICS_CATALOGUE.get(normalized)
    if not entry:
        return jsonify({"error": f"No diagnostic entry found for code '{normalized}'"}), 404
    return jsonify(entry)


@app.route("/api/v1/diagnostics", methods=["GET"])
def list_diagnostics():
    return jsonify({
        "codes": list(DIAGNOSTICS_CATALOGUE.keys()),
        "total": len(DIAGNOSTICS_CATALOGUE),
    })


# ─── Shipment tracking endpoints ──────────────────────────────────────────────
@app.route("/api/v1/shipments", methods=["GET"])
def get_shipments():
    case_id = request.args.get("caseId")
    shipment_id = request.args.get("shipmentId")
    tracking_number = request.args.get("trackingNumber")
    app.logger.info(
        "TrackShipment — caseId=%s shipmentId=%s tracking=%s",
        case_id, shipment_id, tracking_number,
    )

    results = []

    if shipment_id:
        s = shipments.get(shipment_id.strip().upper())
        if s:
            results = [s]
    elif case_id:
        results = [
            s for s in shipments.values()
            if s.get("caseId", "").upper() == case_id.strip().upper()
        ]
    elif tracking_number:
        tn_clean = tracking_number.strip().replace(" ", "")
        results = [
            s for s in shipments.values()
            if s.get("trackingNumber", "").replace(" ", "") == tn_clean
        ]

    if not results:
        return jsonify({"error": "No shipment found for the provided identifier"}), 404

    return jsonify({"shipments": results, "total": len(results)})


@app.route("/api/v1/shipments/<shipment_id>", methods=["GET"])
def get_shipment_by_id(shipment_id):
    app.logger.info("TrackShipment (direct) — shipmentId: %s", shipment_id)
    s = shipments.get(shipment_id.strip().upper())
    if not s:
        return jsonify({"error": f"No shipment found with ID '{shipment_id}'"}), 404
    return jsonify(s)


if __name__ == "__main__":
    print("\n" + "=" * 62)
    print("  Abbott FreeStyle Libre - Mock Support API")
    print("  Running on http://localhost:5001")
    print("=" * 62)
    print("\n  Endpoints:")
    print("  GET  /health")
    print("  POST /api/v1/support/cases")
    print("  GET  /api/v1/support/cases/<case_id>")
    print("  POST /api/v1/support/documents")
    print("  GET  /api/v1/diagnostics/<code>")
    print("  GET  /api/v1/shipments?caseId=<id>")
    print("  GET  /api/v1/shipments/<shipment_id>")
    print("\n  Pre-loaded demo cases:")
    for cid in SAMPLE_CASES:
        print(f"  - {cid}")
    print("\n  Pre-loaded demo shipments:")
    for sid in SAMPLE_SHIPMENTS:
        print(f"  - {sid}")
    print("\n  Diagnostic codes: E1 E2 E3 E4 E5 E6 E7 E8 APP-001 APP-002 DASH")
    print("\n  Add to your .env:")
    print("  ADC_SUPPORT_API_BASE_URL=http://localhost:5001")
    print("=" * 62 + "\n")
    app.run(host="0.0.0.0", port=5001, debug=True)
