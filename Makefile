# ─── Variables ────────────────────────────────────────────────────────────────
PYTHON  ?= python3
PIP     ?= pip3
PROJECT := adc-freestyle-support

.DEFAULT_GOAL := help

# ─── Help ─────────────────────────────────────────────────────────────────────
.PHONY: help
help:
	@echo ""
	@echo "  Abbott FreeStyle Libre AI Support Partner — Make targets"
	@echo "  ─────────────────────────────────────────────────────────"
	@echo "  make install        Install Python dependencies"
	@echo "  make env            Copy .env.example → .env (edit before deploying)"
	@echo "  make lint           Run syntax checks on all Python tool files"
	@echo "  make validate-yaml  Validate all agent and knowledge base YAML specs"
	@echo "  make deploy         Run the full deployment script"
	@echo "  make teardown       Remove all deployed resources from watsonx Orchestrate"
	@echo "  make clean          Remove __pycache__ and .pyc files"
	@echo ""

# ─── Setup ────────────────────────────────────────────────────────────────────
.PHONY: install
install:
	$(PIP) install -r requirements.txt
	@echo "✓ Dependencies installed"

.PHONY: env
env:
	@if [ -f .env ]; then \
		echo ".env already exists — not overwriting"; \
	else \
		cp .env.example .env; \
		echo "✓ Created .env — fill in your values before deploying"; \
	fi

# ─── Validation ───────────────────────────────────────────────────────────────
.PHONY: lint
lint:
	@echo "Checking Python tool files..."
	@$(PYTHON) -m py_compile tools/create_support_case.py && echo "  ✓ create_support_case.py"
	@$(PYTHON) -m py_compile tools/get_case_status.py && echo "  ✓ get_case_status.py"
	@$(PYTHON) -m py_compile tools/upload_supporting_documents.py && echo "  ✓ upload_supporting_documents.py"
	@echo "All Python files OK"

.PHONY: validate-yaml
validate-yaml:
	@echo "Validating YAML files..."
	@$(PYTHON) -c "\
import yaml, glob, sys; \
errors = []; \
files = glob.glob('agents/*.yaml') + glob.glob('knowledge_bases/*.yaml'); \
[errors.append(f) or print(f'  ✗ {f}: {e}') \
  for f in files \
  for e in [None] \
  if not (yaml.safe_load(open(f)) or True) \
]; \
[print(f'  ✓ {f}') for f in files]; \
print(f'Validated {len(files)} YAML files')"

# ─── Deployment ───────────────────────────────────────────────────────────────
.PHONY: deploy
deploy: lint validate-yaml
	@echo "Starting deployment..."
	@chmod +x scripts/deploy.sh
	@bash scripts/deploy.sh

.PHONY: teardown
teardown:
	@chmod +x scripts/teardown.sh
	@bash scripts/teardown.sh

# ─── Cleanup ──────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✓ Cleaned"
