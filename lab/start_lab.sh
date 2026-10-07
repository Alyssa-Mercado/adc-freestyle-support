#!/usr/bin/env bash
# =============================================================================
# lab/start_lab.sh
# One-command lab startup script.
# Starts the mock API server in the background and opens the demo site.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

GREEN='\033[0;32m'; BLUE='\033[0;34m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; NC='\033[0m'

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${BOLD}  Abbott FreeStyle Libre AI Support Lab${NC}"
echo -e "${BOLD}  IBM watsonx Orchestrate${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""

cd "$PROJECT_ROOT"

# Load env
if [[ -f .env ]]; then
    set -a && source .env && set +a
    echo -e "${GREEN}[OK]${NC} Environment loaded"
fi

# Install flask if needed
python3 -c "import flask" 2>/dev/null || {
    echo -e "${YELLOW}[INFO]${NC} Installing Flask..."
    pip3 install flask --quiet
}

# Install fpdf2 if needed
python3 -c "import fpdf" 2>/dev/null || {
    echo -e "${YELLOW}[INFO]${NC} Installing fpdf2..."
    pip3 install fpdf2 --quiet
}

# Generate PDFs if docs folder is empty
KB_DOCS="$PROJECT_ROOT/knowledge_bases/docs"
if [[ ! -d "$KB_DOCS" ]] || [[ -z "$(ls -A $KB_DOCS 2>/dev/null)" ]]; then
    echo -e "${BLUE}[INFO]${NC} Generating knowledge base documents..."
    python3 lab/generate_docs.py
    echo -e "${GREEN}[OK]${NC} Documents generated"
else
    DOC_COUNT=$(ls "$KB_DOCS"/*.pdf 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}[OK]${NC} $DOC_COUNT knowledge base documents found"
fi

# Start mock API server in background
echo -e "${BLUE}[INFO]${NC} Starting mock API server on port 5001..."
python3 lab/mock_api/server.py > /tmp/mock_api.log 2>&1 &
MOCK_PID=$!
sleep 2

if kill -0 $MOCK_PID 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} Mock API server running (PID $MOCK_PID)"
else
    echo -e "${YELLOW}[WARN]${NC} Mock API server may have failed — check /tmp/mock_api.log"
fi

# Start demo site in background
echo -e "${BLUE}[INFO]${NC} Starting demo website on port 8080..."
cd "$PROJECT_ROOT/demo"
python3 -m http.server 8080 > /tmp/demo_site.log 2>&1 &
DEMO_PID=$!
sleep 1
cd "$PROJECT_ROOT"

if kill -0 $DEMO_PID 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} Demo website running (PID $DEMO_PID)"
fi

echo ""
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  Lab is ready!${NC}"
echo -e "${BOLD}═══════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Mock API:    ${BOLD}http://localhost:5001${NC}"
echo -e "  API Health:  ${BOLD}http://localhost:5001/health${NC}"
echo -e "  Demo Site:   ${BOLD}http://localhost:8080${NC}"
echo ""
echo -e "  Demo cases:"
echo -e "  - CASE-20261001-00001  (in_progress)"
echo -e "  - CASE-20261001-00002  (pending_customer)"
echo -e "  - CASE-20261001-00003  (resolved)"
echo ""
echo -e "  To stop:  kill $MOCK_PID $DEMO_PID"
echo -e "  Lab guide: ${BOLD}lab/LAB_GUIDE.md${NC}"
echo ""

# Open the demo site in browser
open http://localhost:8080 2>/dev/null || echo "Open http://localhost:8080 in your browser"
