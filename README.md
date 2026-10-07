# Abbott FreeStyle Libre — AI Support Partner
### watsonx Orchestrate Multi-Agent Solution · IBM ADK (ibm-watsonx-orchestrate v2.17.0)

A production-ready, HIPAA-aware multi-agent solution that replaces the static
FreeStyle Libre sensor support web form with an AI-driven end-to-end support
experience built on [IBM watsonx Orchestrate](https://www.ibm.com/products/watsonx-orchestrate).

---

## Architecture

```
Customer (Webchat / Web)
        │
        ▼
libre_support_orchestrator          ← Supervisor agent (9-step flow)
        │
        ├── sensor_troubleshooting_agent   (6 issue types · step-by-step protocols)
        ├── general_support_agent          (RAG · cited answers · 5 knowledge bases)
        ├── eligibility_agent              (7 rules → Eligible / Needs Review / Not Eligible)
        ├── case_intake_agent              (12 fields · validation · PII masking)
        └── case_creation_agent            (REST API · 3x retry · case number)

Tools:  CreateSupportCase · GetCaseStatus · UploadSupportingDocuments
        LookupSensorDiagnostics · TrackShipment

KBs:    freestyle_libre_faq · freestyle_libre_troubleshooting_guide
        freestyle_libre_warranty_policy · freestyle_libre_replacement_policy
        freestyle_libre_support_kb
```

---

## Project Structure

```
adc-freestyle-support/
├── agents/
│   ├── libre_support_orchestrator.yaml        # Supervisor · 6 collaborators · 3 tools
│   ├── sensor_troubleshooting_agent.yaml      # 6 issue categories · 5-step protocols
│   ├── general_support_agent.yaml             # RAG · citation-required answers
│   ├── eligibility_agent.yaml                 # Warranty / replacement rules
│   ├── case_intake_agent.yaml                 # 12-field intake · PII masking
│   └── case_creation_agent.yaml               # REST API submission · retry logic
├── tools/
│   ├── create_support_case.py                 # POST /api/v1/support/cases
│   ├── get_case_status.py                     # GET  /api/v1/support/cases/{id}
│   ├── upload_supporting_documents.py         # POST /api/v1/support/documents
│   ├── lookup_sensor_diagnostics.py           # GET  /api/v1/diagnostics/{code}
│   └── track_shipment.py                      # GET  /api/v1/shipments
├── knowledge_bases/
│   ├── freestyle_libre_faq.yaml
│   ├── freestyle_libre_troubleshooting_guide.yaml
│   ├── freestyle_libre_warranty_policy.yaml
│   ├── freestyle_libre_replacement_policy.yaml
│   ├── freestyle_libre_support_kb.yaml
│   └── docs/                                  # ← PDFs go here (run lab/generate_docs.py)
├── demo/
│   └── index.html                             # Fake Abbott site + live WXO webchat embed
├── scripts/
│   ├── deploy.sh                              # Full deployment (tools → KBs → agents)
│   └── teardown.sh                            # Remove all deployed resources
├── lab/
│   ├── LAB_GUIDE.md                           # 6-module hands-on lab guide
│   ├── generate_docs.py                       # Generates 17 KB PDFs with fpdf2
│   ├── start_lab.sh                           # One-command lab startup
│   ├── mock_api/
│   │   ├── server.py                          # Flask mock API · port 5001
│   │   └── requirements.txt
│   └── sample_data/
│       └── demo_customers.json                # 4 demo personas with full scripts
├── Makefile                                   # install · lint · validate-yaml · deploy · teardown
├── requirements.txt                           # ibm-watsonx-orchestrate==2.17.0 + deps
└── .env.example                               # Environment variable template
```

---

## Prerequisites

| Requirement | Version / Notes |
|---|---|
| Python | 3.11+ |
| `ibm-watsonx-orchestrate` | 2.17.0 (`make install`) |
| watsonx Orchestrate instance | SaaS / preview — `mcsp_v2` auth |
| WXO API Key | From WXO UI: profile icon → API key (NOT IBM Cloud IAM) |
| `fpdf2` | For lab PDF generation (`pip install fpdf2`) |

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/<your-org>/adc-freestyle-support.git
cd adc-freestyle-support
make install
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
WATSONX_ORCHESTRATE_URL=https://api.preview.watson-orchestrate.ibm.com/instances/<your-instance>.orchestrate.ibm.com
WXO_API_KEY=<your-wxo-api-key>           # from WXO UI profile → API key
ADC_SUPPORT_API_BASE_URL=http://localhost:5001   # mock API (or production URL)
```

### 3. Activate your WXO environment

```bash
orchestrate env activate adc-prod
```

### 4. Generate knowledge base PDFs

```bash
python3 lab/generate_docs.py
# Creates 17 PDFs under knowledge_bases/docs/
```

### 5. Start the mock API

```bash
python3 lab/mock_api/server.py
# Runs on http://localhost:5001
# Supports: cases, documents, diagnostics (E1-E8, APP-001/002, DASH), shipments
```

### 6. Deploy everything

```bash
make deploy
# Imports: 5 tools → 5 knowledge bases → 6 agents
```

### 7. Test

Open your watsonx Orchestrate instance, navigate to **libre_support_orchestrator**
in the Preview panel, and run the smoke test below.

---

## Smoke Tests

### Error code lookup flow
```
User: My sensor is showing an E3 error and I can't get any readings.

Expected:
  1. Orchestrator calls LookupSensorDiagnostics(error_code="E3")
  2. Returns: Sensor Error — replacement_indicative=true
  3. Offers to check eligibility
  4. Routes to eligibility_agent → Eligible
  5. Routes to case_intake_agent → collects 12 fields
  6. Routes to case_creation_agent → returns CASE-XXXXXXXX
```

### General knowledge / RAG flow
```
User: What is the FreeStyle Libre 3 sensor wear duration?

Expected:
  1. Orchestrator routes to general_support_agent
  2. Agent retrieves from knowledge base
  3. Returns: "14 days [Source: FreeStyle Libre FAQ, Section: Sensor Wear Duration]"
```

### Shipment tracking flow
```
User: Can you check on my replacement shipment for case CASE-20261001-00001?

Expected:
  1. Orchestrator calls TrackShipment(case_id="CASE-20261001-00001")
  2. Returns: FedEx · In Transit · Est. delivery 2026-10-05
```

### Full sensor fell off flow
```
User: My FreeStyle Libre 3 sensor fell off after only 4 days. I need a replacement.

Expected:
  1. Greeting
  2. Routes to sensor_troubleshooting_agent (sensor_fell_off)
  3. 5-step adhesion troubleshooting protocol
  4. replacement_recommended=true → eligibility_agent → Eligible
  5. case_intake_agent → 12 fields collected
  6. Masked confirmation summary → customer confirms
  7. case_creation_agent → CASE-XXXXXXXX returned
  8. TrackShipment offered for future shipment lookup
```

---

## Manual Deployment (step by step)

```bash
# Tools (import all 5)
orchestrate tools import -k python -f tools/create_support_case.py
orchestrate tools import -k python -f tools/get_case_status.py
orchestrate tools import -k python -f tools/upload_supporting_documents.py
orchestrate tools import -k python -f tools/lookup_sensor_diagnostics.py
orchestrate tools import -k python -f tools/track_shipment.py

# Knowledge bases (must be imported before general_support_agent)
orchestrate knowledge-bases import -f knowledge_bases/freestyle_libre_faq.yaml
orchestrate knowledge-bases import -f knowledge_bases/freestyle_libre_troubleshooting_guide.yaml
orchestrate knowledge-bases import -f knowledge_bases/freestyle_libre_warranty_policy.yaml
orchestrate knowledge-bases import -f knowledge_bases/freestyle_libre_replacement_policy.yaml
orchestrate knowledge-bases import -f knowledge_bases/freestyle_libre_support_kb.yaml

# Collaborator agents (import BEFORE the orchestrator)
orchestrate agents import -f agents/sensor_troubleshooting_agent.yaml
orchestrate agents import -f agents/general_support_agent.yaml
orchestrate agents import -f agents/eligibility_agent.yaml
orchestrate agents import -f agents/case_intake_agent.yaml
orchestrate agents import -f agents/case_creation_agent.yaml

# Orchestrator last
orchestrate agents import -f agents/libre_support_orchestrator.yaml
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WATSONX_ORCHESTRATE_URL` | Yes | WXO instance base URL |
| `WXO_API_KEY` | Yes | API key from WXO UI profile (mcsp_v2 auth) |
| `ADC_SUPPORT_API_BASE_URL` | Yes | Support API base URL (mock: `http://localhost:5001`) |
| `LOG_LEVEL` | No | Logging verbosity (default: `INFO`) |

> **Auth note:** This solution uses `mcsp_v2` authentication (SaaS/preview instances).
> The `WXO_API_KEY` comes from inside the WXO UI (profile icon → API key),
> **not** from IBM Cloud IAM.

---

## Mock API

The lab mock API (`lab/mock_api/server.py`) runs on `http://localhost:5001` and
provides all endpoints the tools call, with pre-loaded demo data.

| Method | Path | Tool |
|---|---|---|
| `POST` | `/api/v1/support/cases` | CreateSupportCase |
| `GET` | `/api/v1/support/cases/{id}` | GetCaseStatus |
| `POST` | `/api/v1/support/documents` | UploadSupportingDocuments |
| `GET` | `/api/v1/diagnostics/{code}` | LookupSensorDiagnostics |
| `GET` | `/api/v1/shipments?caseId=` | TrackShipment |

Pre-loaded demo cases: `CASE-20261001-00001`, `CASE-20261001-00002`, `CASE-20261001-00003`
Pre-loaded demo shipments: `SHIP-20261001-00001`, `SHIP-20261001-00002`, `SHIP-20261001-00003`
Diagnostic codes: `E1 E2 E3 E4 E5 E6 E7 E8 APP-001 APP-002 DASH`

---

## Compliance Notes

- **HIPAA-aware**: PII masked in all logs — `[NAME]` `[EMAIL]` `[PHONE]` `[SENSOR_SN]`
- **No medical advice**: All agents refuse clinical questions and redirect to HCP
- **No treatment recommendations**: Sensor readings are never interpreted clinically
- **Human escalation**: 5 defined triggers (customer request, safety, complexity, frustration, unresolved)
- **PII minimization**: SSN, DOB, insurance ID, payment cards refused at intake
- **Adverse events**: `[PRIORITY: HEALTH RISK]` flag routes to Abbott pharmacovigilance team

---

## Teardown

```bash
make teardown
```

---

## Lab Guide

A full 6-module hands-on lab is included at [`lab/LAB_GUIDE.md`](lab/LAB_GUIDE.md).
Run the entire lab environment with one command:

```bash
bash lab/start_lab.sh
```

---

## License

© Abbott Diabetes Care. Internal use only. Not for distribution.
