-- Core EDC Tables

CREATE TABLE IF NOT EXISTS studies (
    study_id VARCHAR(50) PRIMARY KEY,
    study_name VARCHAR(255) NOT NULL,
    indication VARCHAR(100),
    phase VARCHAR(50),
    sponsor VARCHAR(100),
    start_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    subjects_enrolled INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subjects (
    subject_id VARCHAR(50) PRIMARY KEY,
    study_id VARCHAR(50) REFERENCES studies(study_id),
    site_id VARCHAR(50),
    treatment_arm VARCHAR(50),
    enrollment_date DATE,
    status VARCHAR(50) DEFAULT 'enrolled',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Legacy/Clinical Data Tables (used by store_vitals)
-- Ensuring they exist to avoid errors
CREATE TABLE IF NOT EXISTS patients (
    patient_id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50) DEFAULT 'DEFAULT_TENANT',
    subject_number VARCHAR(50), -- Maps to subject_id
    site_id VARCHAR(50),
    protocol_id VARCHAR(50),
    enrollment_date DATE,
    treatment_arm VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vital_signs (
    vital_id SERIAL PRIMARY KEY,
    tenant_id VARCHAR(50),
    patient_id INTEGER REFERENCES patients(patient_id),
    visit_date DATE,
    measurement_time TIMESTAMP,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature FLOAT,
    data_batch JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Queries Table (for Quality Service integration)
CREATE TABLE IF NOT EXISTS queries (
    query_id SERIAL PRIMARY KEY,
    study_id VARCHAR(50) REFERENCES studies(study_id),
    subject_id VARCHAR(50) REFERENCES subjects(subject_id),
    query_text TEXT NOT NULL,
    field VARCHAR(100),
    severity VARCHAR(20), -- 'Major', 'Critical', etc.
    status VARCHAR(20) DEFAULT 'open', -- 'open', 'answered', 'closed'
    opened_by INTEGER, -- User ID
    opened_at TIMESTAMP DEFAULT NOW(),
    response_text TEXT,
    responded_by INTEGER,
    responded_at TIMESTAMP,
    closed_by INTEGER,
    closed_at TIMESTAMP,
    resolution_notes TEXT
);

CREATE TABLE IF NOT EXISTS query_history (
    history_id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES queries(query_id),
    action VARCHAR(50), -- 'opened', 'responded', 'closed'
    action_at TIMESTAMP DEFAULT NOW(),
    user_id INTEGER,
    notes TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_subjects_study_id ON subjects(study_id);
CREATE INDEX IF NOT EXISTS idx_queries_subject_id ON queries(subject_id);
CREATE INDEX IF NOT EXISTS idx_queries_status ON queries(status);
