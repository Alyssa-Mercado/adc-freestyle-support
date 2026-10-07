# Abbott FreeStyle Libre AI Support Lab
## IBM watsonx Orchestrate — Hands-On Lab Guide

**Version:** 1.0  
**Platform:** IBM watsonx Orchestrate (ADK v2.17.0)  
**Duration:** ~90 minutes  
**Level:** Intermediate

---

## Lab Overview

In this lab you will build, deploy, and test a complete multi-agent AI support solution for Abbott Diabetes Care on IBM watsonx Orchestrate. The solution replaces a static web form with an intelligent, conversational support experience for FreeStyle Libre sensor customers.

By the end of this lab you will have:
- 5 AI agents deployed and working together in watsonx Orchestrate
- 3 REST API tools connected to a live mock backend
- 5 knowledge bases loaded with product documentation
- A demo website with the embedded agent

---

## Architecture

```
Customer (Chat / Web)
        |
        v
libre_support_orchestrator          <- You talk to this one
        |
        |-- sensor_troubleshooting_agent   (6 issue types, 5-step protocols)
        |-- case_intake_agent              (collects 12 fields, validates data)
        |-- eligibility_agent              (7 rules: Eligible / Needs Review / Not Eligible)
        |-- case_creation_agent            (calls REST API, returns case number)

Tools:  CreateSupportCase  |  GetCaseStatus  |  UploadSupportingDocuments
KBs:    FAQ  |  Troubleshooting  |  Warranty  |  Replacement  |  Support KB
```

---

## Prerequisites

Before starting, confirm you have:

- [ ] IBM watsonx Orchestrate instance (trial or paid)
- [ ] IBM Cloud API key from cloud.ibm.com/iam/apikeys
- [ ] watsonx Orchestrate API key (from inside Orchestrate — profile icon)
- [ ] Python 3.11 or later installed
- [ ] Terminal / command line access

---

## Module 1 — Environment Setup (15 minutes)

### Step 1.1 — Install the ADK

```bash
pip3 install ibm-watsonx-orchestrate==2.17.0 flask fpdf2
```

Verify the installation:
```bash
orchestrate --version
```

Expected output: `ADK Version: 2.17.0`

---

### Step 1.2 — Configure your environment

```bash
cd "/Users/alyssamercado/Desktop/ADC AI Support Partner/adc-freestyle-support"
make env
```

Open `.env` and fill in your values:

```bash
WATSONX_ORCHESTRATE_URL=https://api.dl.watson-orchestrate.ibm.com/instances/YOUR-INSTANCE-ID
IBM_CLOUD_API_KEY='your-ibm-cloud-api-key'
ADC_SUPPORT_API_BASE_URL=http://localhost:5001
WXO_ENV_NAME=adc-prod
```

> NOTE: Wrap your API key in single quotes if it contains slashes or special characters.

Load the variables:
```bash
set -a && source .env && set +a
```

---

### Step 1.3 — Connect to watsonx Orchestrate

```bash
orchestrate env add \
  --name adc-prod \
  --url "$WATSONX_ORCHESTRATE_URL" \
  --activate
```

When prompted for the API key, enter your **watsonx Orchestrate API key** (from the profile menu inside Orchestrate — not your IBM Cloud API key).

Verify the connection:
```bash
orchestrate env list
```

You should see `adc-prod` listed as active.

---

## Module 2 — Knowledge Base Setup (15 minutes)

### Step 2.1 — Generate knowledge base documents

```bash
pip3 install fpdf2
python3 lab/generate_docs.py
```

This creates 17 PDF documents in `knowledge_bases/docs/`.

Verify:
```bash
ls knowledge_bases/docs/
```

You should see 17 .pdf files.

---

### Step 2.2 — Import knowledge bases

```bash
for f in knowledge_bases/*.yaml; do
  orchestrate knowledge-bases import -f "$f"
done
```

Verify:
```bash
orchestrate knowledge-bases list
```

You should see 5 knowledge bases listed.

---

## Module 3 — Tool and Agent Deployment (15 minutes)

### Step 3.1 — Deploy everything with one command

```bash
make deploy
```

This deploys in the correct order:
1. 3 Python tools
2. 5 knowledge bases (skipped if no docs yet)
3. 4 collaborator agents
4. 1 orchestrator agent

Expected final output:
```
Deployment complete!
Orchestrator:   libre_support_orchestrator
Collaborators:  sensor_troubleshooting_agent, case_intake_agent,
                eligibility_agent, case_creation_agent
Tools:          CreateSupportCase, GetCaseStatus, UploadSupportingDocuments
```

---

### Step 3.2 — Verify in the watsonx Orchestrate UI

1. Open your watsonx Orchestrate instance in the browser
2. Click AI Agents in the left navigation
3. Confirm you see all 5 agents listed
4. Click libre_support_orchestrator
5. Confirm the Tools tab shows all 3 tools
6. Confirm the Agents tab shows all 4 collaborators

---

## Module 4 — Start the Mock API Server (5 minutes)

The tools need a backend API to call. Start the mock server:

```bash
pip3 install flask
python3 lab/mock_api/server.py
```

Leave this running in a separate terminal tab. You should see:
```
Abbott FreeStyle Libre - Mock Support API
Running on http://localhost:5001
```

Test it:
```bash
curl http://localhost:5001/health
```

Expected: `{"status": "ok", "service": "ADC Mock Support API"}`

The server has 3 pre-loaded demo cases:
- `CASE-20261001-00001` — in_progress
- `CASE-20261001-00002` — pending_customer  
- `CASE-20261001-00003` — resolved

---

## Module 5 — Testing the Agents (20 minutes)

### Step 5.1 — Set the welcome message

1. Open libre_support_orchestrator in the agent builder
2. Click the Behavior tab
3. Set the Welcome message to:
   > Hi! I'm your FreeStyle Libre Support assistant. What can I help you with today?
4. Add these Conversation starters:
   - I see an error message on my sensor or app
   - My sensor fell off during wear or use
   - My sensor reading is different than I expected
   - Track my sensor replacement
   - I need help with something else
5. Click Save, then Deploy to Live

---

### Step 5.2 — Run Exercise 1: Sensor Fell Off (Full End-to-End Flow)

Use the demo data from `lab/sample_data/demo_customers.json` — Customer CUST-001.

Open the Preview panel and send these messages in order:

**Message 1:**
```
My FreeStyle Libre 3 sensor fell off after only 4 days. I think I need a replacement.
```
Expected: Agent greets and asks for details

**Message 2:**
```
Lot number XY-990011, serial AB12345678, applied 2026-09-10, fell off 2026-09-14
```
Expected: Agent routes to eligibility_agent, returns "Eligible"

**Message 3:**
```
Yes I'd like to request a replacement please.
```
Expected: Agent routes to case_intake_agent, starts collecting contact info

**Message 4:**
```
Jane Doe, jane.doe@example.com, 312-555-0192
```
Expected: Agent confirms contact info, asks for remaining details

**Message 5:**
```
No error codes. Email is fine for updates.
```
Expected: Agent presents confirmation summary

**Message 6:**
```
Yes everything looks correct, please submit.
```
Expected: Agent calls CreateSupportCase, returns a case number

**Message 7:**
```
Can you check the status of my case?
```
Expected: Agent calls GetCaseStatus, returns current status

Click Show Reasoning after each step to see which agent is handling the request.

---

### Step 5.3 — Run Exercise 2: Error Code Scenario

Use Customer CUST-002 from the sample data.

**Message 1:**
```
My FreeStyle Libre 2 sensor is showing an E-3 error and completely stopped giving readings.
```

**Message 2:**
```
It started on day 3. I tried re-scanning 3 times but it keeps showing E-3.
```

**Message 3:**
```
Yes I need a replacement.
```

Continue with CUST-002 details from the sample data file.

Expected outcome: Eligible (Rule 2 — confirmed error code)

---

### Step 5.4 — Run Exercise 3: Case Status Lookup

**Message 1:**
```
I want to check on my existing support case.
```

**Message 2:**
```
My case number is CASE-20261001-00001
```

Expected: Agent calls GetCaseStatus, returns status "in_progress" with shipping notes.

Try also with:
- `CASE-20261001-00002` — pending_customer
- `CASE-20261001-00003` — resolved

---

### Step 5.5 — Run Exercise 4: Human Escalation

At any point in a conversation, send:
```
I'm really frustrated. I want to speak to a real person.
```

Expected: Orchestrator immediately escalates with a full context handoff summary.

---

## Module 6 — Demo Website (10 minutes)

### Step 6.1 — Open the demo site

```bash
cd "/Users/alyssamercado/Desktop/ADC AI Support Partner/adc-freestyle-support/demo"
python3 -m http.server 8080
```

Open http://localhost:8080 in your browser.

The page should show:
- FreeStyle Libre branding and navigation
- 5 support topic cards
- The watsonx Orchestrate chat widget in the bottom-right corner

### Step 6.2 — Test the card buttons

Click each support card and confirm it opens the chat and sends the corresponding message to the agent.

---

## Lab Complete — Checklist

Confirm you have completed all of the following:

- [ ] ADK installed and connected to watsonx Orchestrate
- [ ] 17 knowledge base PDFs generated
- [ ] 5 knowledge bases imported
- [ ] 3 tools deployed (CreateSupportCase, GetCaseStatus, UploadSupportingDocuments)
- [ ] 5 agents deployed and working together
- [ ] Mock API server running on localhost:5001
- [ ] Exercise 1 completed — full end-to-end case creation
- [ ] Exercise 2 completed — error code scenario
- [ ] Exercise 3 completed — case status lookup
- [ ] Exercise 4 completed — human escalation
- [ ] Demo website running on localhost:8080

---

## Troubleshooting

| Issue | Fix |
|---|---|
| `orchestrate: command not found` | Run `pip3 install ibm-watsonx-orchestrate` |
| `token missing or expired` | Run `orchestrate env activate adc-prod` |
| Agent returns error on first message | Send the message again — first message triggers session init |
| Tool call fails with connection error | Ensure mock API server is running on port 5001 |
| Knowledge base not found | Re-run `orchestrate knowledge-bases import` after generating PDFs |
| Agent names with hyphens rejected | Names must use underscores only |
| Wrong model error | Run `orchestrate models list` and update llm field in agent YAML |

---

## Next Steps

1. Replace the mock API with a real Abbott CRM endpoint
2. Add real Abbott policy PDFs to the knowledge bases
3. Configure watsonx.governance for agent monitoring
4. Set up IBM Cloud Logs for audit trail
5. Run a security review before production deployment
