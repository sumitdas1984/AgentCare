# Product Requirement Document (PRD): AgentCare System

## 1. Executive Summary & Objective

AgentCare is an agentic AI-driven healthcare administration system designed to automate a patient’s non-clinical journey—spanning registration, department routing, appointment scheduling, document collection, reminders, and follow-ups.

> ⚠️ **CRITICAL SAFETY BOUNDARY (RULE-5):** This is strictly an administrative system. Autonomous medical diagnosis, treatment prescription, dosage recommendations, or any claim to replace a clinician is completely prohibited. The application must enforce this boundary in code and gracefully escalate clinical requests to human staff.

---

## 2. Core User Roles & Permissions (RBAC)

Role-based access control must be strictly enforced in **backend code**, not just hidden via the user interface.

* **Patient:**
* Create/update demographic profiles.
* Submit administrative/appointment requests.
* Book, reschedule, or cancel appointments.
* Upload medical documents and track approval/processing status.
* View active reminders and follow-up schedules.


* **Hospital Staff / Administrator:**
* View and filter patient records and incoming requests.
* Manage operational parameters (departments, doctor directories, slot availability).
* Review, approve, or reject cases escalated by the AI system (Human-in-the-Loop workflow).
* Access persistent system audit logs and workflow tracking metrics.



---

## 3. Core Workflow & Scope

The application must execute and persist state across the following sequence:

```
[Patient Registration / ID Match]
               ↓
 [Administrative Intent Detection]
               ↓
     [Department Routing]
               ↓
[Appointment Slot Check & Booking]
               ↓
[Medical Document Collection / Verification]
               ↓
    [Confirmation & Reminders]
               ↓
     [Follow-up Scheduling]

```

---

## 4. Agentic Architecture & Orchestration

The core backend requires at least **three genuinely distinct agent roles**, each defined by a unique system prompt, localized tool access, and specific state responsibilities.

### Proposed Multi-Agent Breakdown

* **Coordinator Agent (Orchestrator):** Ingests the initial raw user query, creates/loads the specific workflow execution context, delegates sub-tasks to specialized agents, aggregates results, and manages state persistence.
* **Department Routing Agent:** Analyzes the patient intent, maps the request to an active department, checks for conversational uncertainty, and flags emergency or out-of-scope requests.
* **Appointment Agent:** Interfaces with the schedule database, checks for scheduling conflicts, evaluates slot availability, and executes transactional state changes (book/modify/cancel).
* **Document Agent:** Accepts file uploads, classifies document types (e.g., ECG, Lab Report), extracts/validates metadata, tracks MD5/SHA checksums to prevent duplicates, and flags missing documentation required for specific visits.
* **Safety & Escalation Agent:** Continuously reviews inputs/outputs to block medical diagnostic behavior. If an emergency or a sensitive request is caught, it pauses execution and generates a human-review record.
* **Follow-up Agent:** Monitors completed appointments, triggers external notification stubs, and schedules future automated reminder hooks.

---

## 5. Technical Requirements & Architecture Stack

* **Language Backend:** Python (100% compliant with syntax and execution requirements).
* **Orchestration Framework:** LangGraph, CrewAI, AutoGen, or a robust custom state-machine orchestrator.
* **LLM Core Integration:** OpenAI, Anthropic, or Groq (fast-tier client must be declared explicitly in dependencies).
* **Database:** A persistent SQL Relational Database (SQLite, PostgreSQL, or MySQL). *In-memory arrays or volatile JSON caches that wipe on reset are disqualifying.*
* **State Management:** Explicitly persist `WorkflowRun` state configurations to allow recovery, pausing for human intervention, and resumption.
* **Traceability:** System-wide audit logging that registers actors, entities, timestamped actions, and raw metadata.

---

## 6. Target Data Model (SQL Relational Schema)

```sql
-- Core User Account
CREATE TABLE User (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'patient' or 'staff'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extended Patient Metrics
CREATE TABLE PatientProfile (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) FOREIGN KEY REFERENCES User(id),
    date_of_birth DATE NOT NULL,
    phone VARCHAR(20),
    preferred_language VARCHAR(50),
    emergency_contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Internal Hospital Structures
CREATE TABLE Department (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE Doctor (
    id VARCHAR(36) PRIMARY KEY,
    department_id VARCHAR(36) FOREIGN KEY REFERENCES Department(id),
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT TRUE
);

CREATE TABLE AppointmentSlot (
    id VARCHAR(36) PRIMARY KEY,
    doctor_id VARCHAR(36) FOREIGN KEY REFERENCES Doctor(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'available' -- 'available', 'reserved'
);

-- Transactional Workflow Tables
CREATE TABLE Appointment (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) FOREIGN KEY REFERENCES PatientProfile(id),
    doctor_id VARCHAR(36) FOREIGN KEY REFERENCES Doctor(id),
    slot_id VARCHAR(36) FOREIGN KEY REFERENCES AppointmentSlot(id),
    status VARCHAR(50) DEFAULT 'pending', -- 'pending', 'confirmed', 'cancelled'
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE PatientDocument (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) FOREIGN KEY REFERENCES PatientProfile(id),
    document_type VARCHAR(100), -- 'ECG', 'Blood_Report', etc.
    file_path VARCHAR(512) NOT NULL,
    document_date DATE,
    checksum VARCHAR(64) NOT NULL, -- Deduplication check
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE WorkflowRun (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) FOREIGN KEY REFERENCES PatientProfile(id),
    current_step VARCHAR(100),
    state TEXT, -- Serialized JSON configuration state
    status VARCHAR(50) DEFAULT 'running', -- 'running', 'paused_for_human', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Reminder (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) FOREIGN KEY REFERENCES PatientProfile(id),
    appointment_id VARCHAR(36) FOREIGN KEY REFERENCES Appointment(id),
    reminder_type VARCHAR(100),
    scheduled_at TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled'
);

CREATE TABLE Escalation (
    id VARCHAR(36) PRIMARY KEY,
    workflow_run_id VARCHAR(36) FOREIGN KEY REFERENCES WorkflowRun(id),
    reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open', -- 'open', 'resolved'
    reviewed_by VARCHAR(36) FOREIGN KEY REFERENCES User(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE AuditEvent (
    id VARCHAR(36) PRIMARY KEY,
    actor_id VARCHAR(36) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    metadata TEXT, -- Serialized event metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

---

## 7. User Interface (UI) Requirements

A functional user interface connected directly to the backend logic is required (API docs alone are insufficient). The interface should be built using a simple framework like **Streamlit**, **Gradio**, or standard HTML/Jinja2 templates.

* **Patient Dashboard:** Views to submit natural language administrative requests, upload test documentation files, verify scheduled time slots, and monitor workflow progress.
* **Staff Administration Desk:** A functional dashboard rendering a table of active `Escalation` records, allowing approvals/denials, manual appointment overriding, and a view into system audit trails.

---

## 8. CI/CD & Repository Structuring (For Hackathon Compliance)

To ensure the automated evaluation checks pass, the repository structure must match the format expected by the evaluation suite:

```
├── .github/
│   └── workflows/
│       └── agentcare-checks.yml  <-- Downloaded from hackathon API
├── src/
│   ├── agents/
│   ├── models/
│   └── database/
├── pyproject.toml                <-- Manages Python dependencies (replaces requirements.txt)
├── README.md                     <-- Containing architecture explanations
├── .env.example                  <-- Template file excluding actual keys
└── .gitignore                    <-- Confirmed rule excluding local .env files

```

> 🔒 **SECURITY GUARDRAIL (RULE-6):** Never commit production API keys, database credentials, or real patient PII to the repository. Keep everything contained in local, gitignored environmental variables. Use synthetic or seed scripts to construct sample records for judging validation.

---

## 9. Single Prompt Setup Guide for Claude Code

*You can pass this target initialization block directly to Claude Code to spin up the application structure:*

```text
Initialize a Python project for the AgentCare hackathon challenge using the structural outline in this PRD. 
1. Build a persistent relational schema (SQLite preferred for quick out-of-the-box local testing) mapping User, PatientProfile, Department, Doctor, AppointmentSlot, Appointment, PatientDocument, WorkflowRun, Reminder, Escalation, and AuditEvent.
2. Implement an agent orchestration model using three distinct agents (Coordinator, Routing, Appointment/Document) running with a declared Python LLM client package.
3. Enforce the clinical safety guardrail (no diagnoses) in the Safety Agent prompts and route anomalies to the Escalation data tables.
4. Set up an administrative interface via Streamlit/Gradio to verify patient task flows and handle supervisor approvals.
5. Provide a mock data seed module to auto-populate departments, doctor listings, and slots. Ensure a robust pyproject.toml and standard .env.example matching the architecture parameters are included.

```