# Contributing

This repository contains the Abbott Diabetes Care FreeStyle Libre AI Support Partner,
a watsonx Orchestrate multi-agent solution. Contributions are welcome from internal
ADC / IBM team members with repository access.

---

## Development Setup

```bash
git clone https://github.com/<your-org>/adc-freestyle-support.git
cd adc-freestyle-support
python3 -m venv .venv
source .venv/bin/activate
make install
```

---

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Production-ready, deployed to `adc-prod` WXO environment |
| `develop` | Integration branch — all PRs target this branch |
| `feat/<name>` | New agents, tools, or knowledge base additions |
| `fix/<name>` | Bug fixes to existing agents or tools |
| `lab/<name>` | Lab guide and demo changes only |

---

## Making Changes

### Adding or modifying an agent

1. Edit the YAML under `agents/`.
2. Ensure `name:` uses **underscores only** — hyphens are rejected by the WXO API.
3. Ensure `llm:` is set to `groq/openai/gpt-oss-120b`.
4. Ensure agent `instructions:` contain **plain ASCII only** — no Unicode box-drawing
   characters (`─`, `•`, `–`, `→`). These cause runtime errors in WXO.
5. Validate the YAML: `make validate-yaml`
6. Redeploy: `orchestrate agents import -f agents/<file>.yaml`

### Adding or modifying a tool

1. Edit or create the Python file under `tools/`.
2. Follow the existing pattern: `@tool(name=..., description=..., permission=...)`.
3. Use Pydantic `BaseModel` for all input/output types.
4. Include an offline fallback if the tool calls an external API.
5. Lint: `make lint`
6. Redeploy: `orchestrate tools import -k python -f tools/<file>.py`

### Adding a knowledge base

1. Add a YAML spec under `knowledge_bases/`.
2. Ensure `name:` uses **underscores only**.
3. Add the corresponding PDF to `knowledge_bases/docs/` (not committed to git).
4. Add the KB name to `general_support_agent.yaml` under `knowledge:`.
5. Redeploy: `orchestrate knowledge-bases import -f knowledge_bases/<file>.yaml`

### Updating the mock API

- Edit `lab/mock_api/server.py`.
- Add pre-loaded demo data for any new endpoint.
- Update the startup banner to list new endpoints.

---

## Code Style

- Python: follow PEP 8. Use type annotations. Keep functions focused.
- YAML: 2-space indent. Use `>` for multi-line description strings.
- Commit messages: `type(scope): short description`
  - Types: `feat`, `fix`, `docs`, `refactor`, `lab`, `chore`
  - Example: `feat(tools): add LookupSensorDiagnostics with offline fallback`

---

## Compliance Rules (non-negotiable)

All contributions **must** maintain:

- **No medical advice**: No agent or tool may provide clinical guidance, interpret
  glucose readings, or suggest dosing changes.
- **HIPAA-aware design**: PII must be masked in all logs. PHI must never be stored
  beyond the session.
- **Human escalation**: The orchestrator must always offer human escalation. Never
  block or delay escalation requests.
- **Plain ASCII instructions**: Agent instruction strings must use plain ASCII only.

Any PR that removes or weakens these controls will be rejected.

---

## Pull Request Checklist

- [ ] `make lint` passes with no errors
- [ ] `make validate-yaml` passes with no errors
- [ ] Agent instruction strings contain no Unicode special characters
- [ ] Agent and KB names use underscores only (no hyphens)
- [ ] No real credentials, API keys, or PII added to any file
- [ ] `knowledge_bases/docs/*.pdf` not included in the commit
- [ ] README updated if new agents, tools, or endpoints were added
- [ ] Mock API updated if a new tool endpoint was added

---

## Questions

Open an issue in this repository or contact the ADC AI Platform team.
