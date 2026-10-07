#!/usr/bin/env bash
# =============================================================================
# deploy.sh
# Full deployment script for the Abbott FreeStyle Libre AI Support Partner
# on watsonx Orchestrate using the ADK (ibm-watsonx-orchestrate CLI).
#
# Usage:
#   chmod +x scripts/deploy.sh
#   ./scripts/deploy.sh
#
# Prerequisites:
#   - ibm-watsonx-orchestrate is installed (pip install ibm-watsonx-orchestrate)
#   - .env file is populated (copy from .env.example)
#   - orchestrate env activate <WXO_ENV_NAME> has been run
#   - PDF documents are placed under knowledge_bases/docs/
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# ─── Colour helpers ────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'
BOLD='\033[1m'; NC='\033[0m'

info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
step()    { echo -e "\n${BOLD}══ $* ══${NC}"; }

# ─── Load environment ─────────────────────────────────────────────────────
ENV_FILE="$PROJECT_ROOT/.env"
if [[ -f "$ENV_FILE" ]]; then
    set -a && source "$ENV_FILE" && set +a
    info "Loaded environment from .env"
else
    warn ".env file not found — relying on shell environment variables"
fi

# ─── Prerequisite checks ──────────────────────────────────────────────────
step "Checking prerequisites"

command -v orchestrate >/dev/null 2>&1 || \
    error "orchestrate CLI not found. Run: pip install ibm-watsonx-orchestrate"
success "orchestrate CLI found: $(orchestrate --version 2>/dev/null || echo 'version unknown')"

[[ -n "${WATSONX_ORCHESTRATE_URL:-}" ]] || \
    error "WATSONX_ORCHESTRATE_URL is not set. Check your .env file."
success "WATSONX_ORCHESTRATE_URL = $WATSONX_ORCHESTRATE_URL"

[[ -n "${IBM_CLOUD_API_KEY:-}" ]] || \
    error "IBM_CLOUD_API_KEY is not set. Check your .env file."
success "IBM_CLOUD_API_KEY is set"

[[ -n "${ADC_SUPPORT_API_BASE_URL:-}" ]] || \
    warn "ADC_SUPPORT_API_BASE_URL is not set — tool calls will use the default URL"

# ─── Step 1: Import tools ─────────────────────────────────────────────────
step "Step 1/4 — Importing Python tools"
cd "$PROJECT_ROOT"

info "Importing CreateSupportCase tool..."
orchestrate tools import -k python -f tools/create_support_case.py
success "CreateSupportCase imported"

info "Importing GetCaseStatus tool..."
orchestrate tools import -k python -f tools/get_case_status.py
success "GetCaseStatus imported"

info "Importing UploadSupportingDocuments tool..."
orchestrate tools import -k python -f tools/upload_supporting_documents.py
success "UploadSupportingDocuments imported"

info "Importing LookupSensorDiagnostics tool..."
orchestrate tools import -k python -f tools/lookup_sensor_diagnostics.py
success "LookupSensorDiagnostics imported"

info "Importing TrackShipment tool..."
orchestrate tools import -k python -f tools/track_shipment.py
success "TrackShipment imported"

# ─── Step 2: Import knowledge bases ───────────────────────────────────────
step "Step 2/4 — Importing knowledge bases"

KB_DOCS_DIR="$PROJECT_ROOT/knowledge_bases/docs"
if [[ ! -d "$KB_DOCS_DIR" ]]; then
    warn "knowledge_bases/docs/ directory not found — skipping knowledge base import."
    warn "To add knowledge bases later:"
    warn "  1. Create knowledge_bases/docs/ and add your PDF documents"
    warn "  2. Run: for f in knowledge_bases/*.yaml; do orchestrate knowledge-bases import -f \"\$f\"; done"
else
    DOC_COUNT=$(find "$KB_DOCS_DIR" -name "*.pdf" | wc -l | tr -d ' ')
    info "Found $DOC_COUNT PDF document(s) — importing knowledge bases..."
    for kb_file in knowledge_bases/*.yaml; do
        kb_name=$(grep '^name:' "$kb_file" | awk '{print $2}')
        info "Importing knowledge base: $kb_name"
        orchestrate knowledge-bases import -f "$kb_file" && success "Imported: $kb_name" || \
            warn "Knowledge base '$kb_name' import failed — check output above"
    done
fi

# ─── Step 3: Import agents (collaborators first, orchestrator last) ────────
step "Step 3/4 — Importing agents (collaborators first)"

COLLABORATOR_AGENTS=(
    "agents/sensor_troubleshooting_agent.yaml"
    "agents/case_intake_agent.yaml"
    "agents/eligibility_agent.yaml"
    "agents/case_creation_agent.yaml"
    "agents/general_support_agent.yaml"
)

for agent_file in "${COLLABORATOR_AGENTS[@]}"; do
    agent_name=$(grep '^name:' "$agent_file" | awk '{print $2}')
    info "Importing collaborator agent: $agent_name"
    orchestrate agents import -f "$agent_file"
    success "Imported: $agent_name"
done

info "Importing orchestrator agent: libre-support-orchestrator"
orchestrate agents import -f agents/libre_support_orchestrator.yaml
success "Imported: libre-support-orchestrator"

# ─── Step 4: Verify deployment ────────────────────────────────────────────
step "Step 4/4 — Verifying deployment"

info "Listing deployed tools..."
orchestrate tools list 2>/dev/null || warn "Could not list tools — check orchestrate CLI auth"

info "Listing deployed agents..."
orchestrate agents list 2>/dev/null || warn "Could not list agents — check orchestrate CLI auth"

info "Listing knowledge bases..."
orchestrate knowledge-bases list 2>/dev/null || warn "Could not list knowledge bases"

# ─── Done ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Deployment complete!${NC}"
echo -e "${GREEN}${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Orchestrator:  ${BOLD}libre_support_orchestrator${NC}"
echo -e "  Collaborators: sensor_troubleshooting_agent, case_intake_agent,"
echo -e "                 eligibility_agent, case_creation_agent,"
echo -e "                 general_support_agent"
echo -e "  Tools:         CreateSupportCase, GetCaseStatus,"
echo -e "                 UploadSupportingDocuments, LookupSensorDiagnostics,"
echo -e "                 TrackShipment"
echo -e "  Knowledge:     5 knowledge bases (RAG grounding for general_support_agent)"
echo ""
echo -e "  Next step: open your watsonx Orchestrate instance and test"
echo -e "  the ${BOLD}libre-support-orchestrator${NC} agent in the Preview panel."
echo ""
