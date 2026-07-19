# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## ⚠️ Non-negotiable safety boundary

This is a **healthcare** project. The single most important rule:

> AgentCare must never diagnose, prescribe, recommend dosages, or otherwise substitute for a clinician. All clinical requests must be caught by the Safety & Escalation agent and routed to human staff via the `Escalation` table.

This guardrail must be enforced **in code** (Safety agent + DB-level checks), not only hidden in the UI. See `docs/PRD.md` §1 (RULE-5) and §4 (Safety & Escalation Agent).

---

## What this project is

Agentic AI healthcare **administration** system. Automates the non-clinical side of a hospital visit — registration, department routing, appointment booking, document collection, reminders, follow-ups. Built for the **agentcare-build-challenge-2026** hackathon.

The full scope, schema, and agent breakdown live in `docs/PRD.md`. Read that first before adding any feature.

---

## Architecture (planned, not yet implemented)

Six distinct agent roles, each with its own system prompt and tool surface:

| Agent | Responsibility |
|---|---|
| **Coordinator** | Owns the `WorkflowRun`, delegates to others, persists state |
| **Department Routing** | Maps patient intent → active department, flags emergencies |
| **Appointment** | Slot lookup, conflict checks, transactional book/modify/cancel |
| **Document** | Classify uploads, dedupe by MD5/SHA, validate per-visit requirements |
| **Safety & Escalation** | Blocks diagnostic behavior, writes to `Escalation` table |
| **Follow-up** | Triggers reminders, schedules future hooks |

Persistent SQL backend (SQLite default) is mandatory — in-memory state is a disqualification per the PRD. The full schema (11 tables) is in `docs/PRD.md` §6 and must be created under `src/database/`.

## Locked technology choices (decided 2026-07-19)

- **Agent framework:** LangGraph — the explicit `WorkflowRun` state machine and pause/resume on `Escalation` map onto LangGraph's graph + checkpointer model.
- **LLM provider:** Anthropic Claude — strongest instruction-following for the no-diagnosis guardrail. Declare the `anthropic` SDK in `pyproject.toml` and read `ANTHROPIC_API_KEY` from `.env`.
- **Front end:** Streamlit — both surfaces are dashboards, not chat UIs.

When the corresponding FEATURE lands (FEATURE-2.1 for the LLM client, FEATURE-2.2 for the LangGraph state machine, FEATURE-5.1 / FEATURE-5.2 for the UIs), don't second-guess these choices — they've been made.

## Testing policy

Lean. After each feature lands, write **one test per acceptance criterion** in the issue body. Lock in only what the AC literally says. Don't test ORM internals, don't write tests for helpers just to bump coverage, and don't write aspirational tests for behavior the code doesn't yet have.

---

## Repository layout (what the evaluation suite expects)

```
src/agents/      # One module per agent
src/models/      # SQLAlchemy / ORM models matching the PRD schema
src/database/    # Schema bootstrap + seed data
docs/PRD.md      # Source of truth for requirements
pyproject.toml   # PEP 621 dependencies (replaces requirements.txt)
.env.example     # Template only — .env is gitignored
.github/workflows/agentcare-build-challenge-2026-checks.yml  # CI
```

Do not invent alternative layouts; the CI check downloads a script at runtime and validates against this shape.

---

## Development workflow

The project uses **`uv`** for Python env and dependency management.

```bash
uv venv                    # creates .venv at the Python version in .python-version (3.13)
uv pip install -e .        # install project in editable mode once deps are added to pyproject.toml
uv add <package>           # add a runtime dep (writes to pyproject.toml + uv.lock)
uv add --dev <package>     # dev-only dep (linters, test runners, etc.)
```

Run a one-off command without activating:

```bash
uv run python -m src.database.seed
uv run streamlit run src/admin/app.py
```

There is no test runner, linter, or formatter wired up yet. When you add one, prefer tools with `uv add --dev` integration (e.g. `ruff`, `pytest`) and document the invocation here.

---

## CI — what to know before touching `.github/workflows/`

- The workflow `agentcare-build-challenge-2026-checks.yml` **downloads the actual check script at runtime** from `https://careerapi-production.krishnaik.in` using an OIDC token. The committed YAML is just the runner.
- `permissions: id-token: write` is required — removing it breaks auth silently.
- `concurrency.cancel-in-progress: true` is intentional: a newer push should supersede an older run.
- `secrets.SUBMISSION_TOKEN` must remain a secret; never echo or log it.
- The checks only use the Python stdlib (no deps installed) — keep it that way.

---

## Secrets and patient data

- `.env` is in `.gitignore`. Never commit it. The PRD's RULE-6 forbids committing real API keys, DB credentials, or real patient PII.
- All demo, seed, and CI data must be synthetic. Seed scripts live under `src/database/seed.py` (to be created) and should generate UUIDs and fake records — never read from real sources.

---

## When adding a new dependency

1. Add it to `pyproject.toml` under `dependencies` (or `[project.optional-dependencies]` for non-runtime tooling).
2. Run `uv lock` so `uv.lock` stays in sync.
3. If it's an LLM client library (Anthropic, OpenAI, Groq), the PRD requires it to be **declared explicitly** — bare imports with no declared dep are a disqualification.

---

## Documentation pointers

- `README.md` — user-facing overview, getting started, security
- `docs/PRD.md` — full requirements, schema, agent breakdown, evaluation rules
