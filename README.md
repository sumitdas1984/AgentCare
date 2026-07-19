# AgentCare

Agentic AI-driven healthcare administration system that automates the **non-clinical** patient journey — registration, department routing, appointment scheduling, document collection, reminders, and follow-ups.

> ⚠️ **Critical Safety Boundary:** AgentCare is strictly administrative. Autonomous diagnosis, treatment prescription, dosage recommendations, or any claim to replace a clinician is prohibited. The system enforces this boundary in code and escalates clinical requests to human staff.

---

## What It Does

AgentCare orchestrates a team of specialized AI agents that walk a patient through every administrative step of a hospital visit, end-to-end:

```
Registration → Intent Detection → Department Routing → Slot Booking
     → Document Collection → Confirmation & Reminders → Follow-up
```

Each step is backed by a persistent relational schema and an audit log, so every action is traceable, recoverable, and resumable after human-in-the-loop review.

## Key Features

- **Multi-agent orchestration** — distinct agents for coordination, department routing, appointment booking, document handling, safety/escalation, and follow-up.
- **Persistent SQL backend** — SQLite for local dev, swappable for PostgreSQL/MySQL. Workflow state and audit events survive restarts.
- **Clinical safety guardrail** — a dedicated Safety & Escalation agent blocks diagnostic behavior and routes anomalies to human supervisors.
- **Role-based access control** — patient and hospital-staff roles enforced in backend code, not just in the UI.
- **Document tracking** — uploads are classified, checksummed (MD5/SHA), and validated against the requirements of the visit.
- **Reminders & follow-ups** — automated hooks keep patients on schedule after their visit.

## Tech Stack

- **Language:** Python 3.13+
- **Orchestration:** LangGraph / CrewAI / AutoGen / custom state machine
- **LLM provider:** Anthropic, OpenAI, or Groq (declared explicitly in `pyproject.toml`)
- **Database:** SQLite (default), PostgreSQL, or MySQL
- **Admin UI:** Streamlit or Gradio for supervisor review
- **Dependency management:** `pyproject.toml` (PEP 621)

## Project Structure

```
.
├── src/
│   ├── agents/          # Coordinator, Routing, Appointment, Document, Safety, Follow-up
│   ├── models/          # SQLAlchemy / data models
│   └── database/        # Schema, migrations, seed data
├── docs/
│   └── PRD.md           # Product requirements
├── .github/workflows/   # CI checks
├── pyproject.toml       # Python dependencies
├── .env.example         # Environment variable template
└── .gitignore
```

## Getting Started

1. **Clone and enter the project**
   ```bash
   git clone <repo-url>
   cd AgentCare
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e .
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database settings
   ```

5. **Initialize the database and seed sample data**
   ```bash
   python -m src.database.seed
   ```

6. **Run the admin UI** (once implemented)
   ```bash
   streamlit run src/admin/app.py
   ```

## Security

- **Never commit** `.env`, real API keys, or patient PII. Use synthetic/seed data for demos and CI.
- The `.gitignore` excludes `.env` automatically.
- All clinical requests must be routed through the Safety & Escalation agent — never bypassed at the UI layer.

## License

See repository for license details.
