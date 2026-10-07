#!/usr/bin/env bash
# =============================================================================
# teardown.sh
# Removes all deployed resources from watsonx Orchestrate.
# Use with caution — this deletes agents, tools, and knowledge bases.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'
info()    { echo -e "\033[0;34m[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }

echo -e "${RED}${BOLD}WARNING: This will delete all FreeStyle Libre support agents, tools, and knowledge bases.${NC}"
read -p "Are you sure? Type 'yes' to continue: " confirm
[[ "$confirm" == "yes" ]] || { echo "Aborted."; exit 0; }

cd "$PROJECT_ROOT"

# Delete orchestrator first (it references sub-agents)
info "Deleting orchestrator agent..."
orchestrate agents delete libre_support_orchestrator 2>/dev/null && success "Deleted libre_support_orchestrator" || warn "Could not delete libre_support_orchestrator"

# Delete collaborator agents
for agent in sensor_troubleshooting_agent case_intake_agent eligibility_agent case_creation_agent general_support_agent; do
    info "Deleting agent: $agent"
    orchestrate agents delete "$agent" 2>/dev/null && success "Deleted $agent" || warn "Could not delete $agent"
done

# Delete tools
for tool_name in CreateSupportCase GetCaseStatus UploadSupportingDocuments LookupSensorDiagnostics TrackShipment; do
    info "Deleting tool: $tool_name"
    orchestrate tools delete "$tool_name" 2>/dev/null && success "Deleted $tool_name" || warn "Could not delete $tool_name"
done

# Delete knowledge bases
for kb in freestyle-libre-faq freestyle-libre-troubleshooting-guide freestyle-libre-warranty-policy freestyle-libre-replacement-policy freestyle-libre-support-kb; do
    info "Deleting knowledge base: $kb"
    orchestrate knowledge-bases delete "$kb" 2>/dev/null && success "Deleted $kb" || warn "Could not delete $kb"
done

echo ""
echo -e "${GREEN}${BOLD}Teardown complete.${NC}"
