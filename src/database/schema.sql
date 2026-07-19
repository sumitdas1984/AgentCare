-- AgentCare schema. SQLite-compatible translation of the 11 entities
-- described in docs/PRD.md §6, plus the Session table added in FEATURE-1.2
-- (Authentication & RBAC).
--
-- Note: the PRD's pseudo-SQL used "column TYPE FOREIGN KEY REFERENCES x(id)",
-- which SQLite rejects because FOREIGN KEY belongs in a separate table
-- constraint clause. Inline references here are written as
--     column TYPE REFERENCES x(id)
-- which SQLite parses correctly. The resulting FK semantics are identical.

-- Core User Account
CREATE TABLE IF NOT EXISTS User (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,           -- 'patient' or 'staff'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Extended Patient Metrics
CREATE TABLE IF NOT EXISTS PatientProfile (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES User(id),
    date_of_birth DATE NOT NULL,
    phone VARCHAR(20),
    preferred_language VARCHAR(50),
    emergency_contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Internal Hospital Structures
CREATE TABLE IF NOT EXISTS Department (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS Doctor (
    id VARCHAR(36) PRIMARY KEY,
    department_id VARCHAR(36) REFERENCES Department(id),
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS AppointmentSlot (
    id VARCHAR(36) PRIMARY KEY,
    doctor_id VARCHAR(36) REFERENCES Doctor(id),
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'available'  -- 'available' or 'reserved'
);

-- Transactional Workflow Tables
CREATE TABLE IF NOT EXISTS Appointment (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES PatientProfile(id),
    doctor_id VARCHAR(36) REFERENCES Doctor(id),
    slot_id VARCHAR(36) REFERENCES AppointmentSlot(id),
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'confirmed', 'cancelled'
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS PatientDocument (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES PatientProfile(id),
    document_type VARCHAR(100),            -- 'ECG', 'Blood_Report', etc.
    file_path VARCHAR(512) NOT NULL,
    document_date DATE,
    checksum VARCHAR(64) NOT NULL,         -- Deduplication hash
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS WorkflowRun (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES PatientProfile(id),
    current_step VARCHAR(100),
    state TEXT,                            -- Serialized JSON configuration state
    status VARCHAR(50) DEFAULT 'running',  -- 'running', 'paused_for_human', 'completed', 'failed'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Reminder (
    id VARCHAR(36) PRIMARY KEY,
    patient_id VARCHAR(36) REFERENCES PatientProfile(id),
    appointment_id VARCHAR(36) REFERENCES Appointment(id),
    reminder_type VARCHAR(100),
    scheduled_at TIMESTAMP NOT NULL,
    status VARCHAR(50) DEFAULT 'scheduled'
);

CREATE TABLE IF NOT EXISTS Escalation (
    id VARCHAR(36) PRIMARY KEY,
    workflow_run_id VARCHAR(36) REFERENCES WorkflowRun(id),
    reason TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'open',     -- 'open' or 'resolved'
    reviewed_by VARCHAR(36) REFERENCES User(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS AuditEvent (
    id VARCHAR(36) PRIMARY KEY,
    actor_id VARCHAR(36) NOT NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id VARCHAR(36) NOT NULL,
    metadata TEXT,                          -- Serialized event metrics
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auth sessions (added in FEATURE-1.2). Opaque random tokens backed by
-- a UNIQUE index. Future HTTP layer can map these to bearer tokens.
CREATE TABLE IF NOT EXISTS Session (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES User(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hot read-path indexes
CREATE INDEX IF NOT EXISTS ix_appointment_patient_id ON Appointment(patient_id);
CREATE INDEX IF NOT EXISTS ix_workflow_run_status ON WorkflowRun(status);
CREATE INDEX IF NOT EXISTS ix_escalation_status ON Escalation(status);
CREATE INDEX IF NOT EXISTS ix_session_token ON Session(token);
CREATE INDEX IF NOT EXISTS ix_session_user_id ON Session(user_id);
