-- init.sql - Complete PostgreSQL schema for Clinical Trials Platform

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- For encryption
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For JSON indexing

-- ============= CORE TABLES =============

-- 1. Patients (Main entity) - Multi-tenant enabled
CREATE TABLE IF NOT EXISTS patients (
    patient_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,  -- Multi-tenant isolation
    subject_number VARCHAR(50) NOT NULL,
    site_id VARCHAR(50) NOT NULL,
    protocol_id VARCHAR(50) NOT NULL,
    enrollment_date DATE NOT NULL,
    treatment_arm VARCHAR(100),
    demographics JSONB DEFAULT '{}',
    medical_history JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'ENROLLED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, subject_number)  -- Unique within tenant
);

-- Indexes for patients (tenant-aware)
CREATE INDEX IF NOT EXISTS idx_tenant ON patients(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tenant_site_protocol ON patients(tenant_id, site_id, protocol_id);
CREATE INDEX IF NOT EXISTS idx_enrollment ON patients(enrollment_date);
CREATE INDEX IF NOT EXISTS idx_demographics_gin ON patients USING gin(demographics);

-- Row-Level Security for multi-tenant isolation
ALTER TABLE patients ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their own tenant's data
CREATE POLICY tenant_isolation ON patients
    USING (tenant_id = current_setting('app.current_tenant', TRUE));

-- 2. Clinical Documents (Replaces MongoDB) - Multi-tenant enabled
CREATE TABLE IF NOT EXISTS documents (
    document_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,  -- Multi-tenant isolation
    patient_id UUID REFERENCES patients(patient_id),
    document_type VARCHAR(50) NOT NULL, -- 'protocol', 'consent', 'report', 'csr'
    title VARCHAR(500),
    content JSONB NOT NULL,  -- Full document as JSON
    metadata JSONB DEFAULT '{}',
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Indexes for documents (tenant-aware)
CREATE INDEX IF NOT EXISTS idx_tenant_docs ON documents(tenant_id);
CREATE INDEX IF NOT EXISTS idx_doc_type ON documents(tenant_id, document_type);
CREATE INDEX IF NOT EXISTS idx_content_gin ON documents USING gin(content);
CREATE INDEX IF NOT EXISTS idx_patient_docs ON documents(patient_id);

-- Row-Level Security
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_docs ON documents
    USING (tenant_id = current_setting('app.current_tenant', TRUE));

-- 3. Vital Signs (Time-series data) - Multi-tenant enabled
CREATE TABLE IF NOT EXISTS vital_signs (
    vital_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,  -- Multi-tenant isolation
    patient_id UUID REFERENCES patients(patient_id),
    visit_date DATE NOT NULL,
    measurement_time TIMESTAMP NOT NULL,
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4,1),
    respiratory_rate INTEGER,
    data_batch JSONB DEFAULT '{}',  -- Store additional measurements
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for vital signs (tenant-aware)
CREATE INDEX IF NOT EXISTS idx_tenant_vitals ON vital_signs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_patient_vitals ON vital_signs(tenant_id, patient_id, measurement_time DESC);
CREATE INDEX IF NOT EXISTS idx_visit_date ON vital_signs(visit_date);

-- Row-Level Security
ALTER TABLE vital_signs ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_vitals ON vital_signs
    USING (tenant_id = current_setting('app.current_tenant', TRUE));

-- 4. Events & Audit Log (For HIPAA compliance)
CREATE TABLE IF NOT EXISTS audit_events (
    event_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL,
    entity_type VARCHAR(50),
    entity_id UUID,
    user_id VARCHAR(100),
    action VARCHAR(50),
    payload JSONB DEFAULT '{}',
    ip_address INET,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit events
CREATE INDEX IF NOT EXISTS idx_event_type ON audit_events(event_type);
CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_entity ON audit_events(entity_type, entity_id);

-- 5. MCP Agent Context (For intelligent agents)
CREATE TABLE IF NOT EXISTS mcp_context (
    agent_id VARCHAR(100) PRIMARY KEY,
    context_type VARCHAR(50),
    context_data JSONB NOT NULL,
    decisions JSONB DEFAULT '[]',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for MCP context
CREATE INDEX IF NOT EXISTS idx_context_type ON mcp_context(context_type);

-- 6. Users & Authentication - Multi-tenant enabled
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,  -- Multi-tenant isolation
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    roles JSONB DEFAULT '["user"]',
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, username),  -- Username unique within tenant
    UNIQUE (tenant_id, email)      -- Email unique within tenant
);

-- Index for users
CREATE INDEX IF NOT EXISTS idx_tenant_users ON users(tenant_id);

-- Row-Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant', TRUE));

-- 7. Studies (Clinical Trial Studies)
CREATE TABLE IF NOT EXISTS studies (
    study_id VARCHAR(50) PRIMARY KEY,
    study_name VARCHAR(255) NOT NULL,
    indication VARCHAR(100),
    phase VARCHAR(50),
    sponsor VARCHAR(255),
    start_date DATE,
    end_date DATE,
    status VARCHAR(50) DEFAULT 'active',
    tenant_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_studies_tenant ON studies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_studies_status ON studies(status);

-- 8. Subjects (Trial Participants)
CREATE TABLE IF NOT EXISTS subjects (
    subject_id VARCHAR(50) PRIMARY KEY,
    study_id VARCHAR(50) REFERENCES studies(study_id),
    site_id VARCHAR(50),
    treatment_arm VARCHAR(50),
    enrollment_date DATE,
    status VARCHAR(50) DEFAULT 'enrolled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_subjects_study ON subjects(study_id);
CREATE INDEX IF NOT EXISTS idx_subjects_site ON subjects(site_id);

-- 9. Visits (Study Visits)
CREATE TABLE IF NOT EXISTS visits (
    visit_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50) REFERENCES subjects(subject_id),
    visit_name VARCHAR(50) NOT NULL,
    visit_date DATE,
    status VARCHAR(50) DEFAULT 'scheduled',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_visits_subject ON visits(subject_id);

-- 10. Vitals Observations
CREATE TABLE IF NOT EXISTS vitals_observations (
    observation_id SERIAL PRIMARY KEY,
    visit_id INTEGER REFERENCES visits(visit_id),
    subject_id VARCHAR(50) REFERENCES subjects(subject_id),
    systolic_bp INTEGER,
    diastolic_bp INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4,2),
    observation_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_vitals_obs_subject ON vitals_observations(subject_id);
CREATE INDEX IF NOT EXISTS idx_vitals_obs_visit ON vitals_observations(visit_id);

-- 11. Queries (Data Query Management)
CREATE TABLE IF NOT EXISTS queries (
    query_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50) NOT NULL,
    study_id VARCHAR(50),
    form_id VARCHAR(50),
    field_id VARCHAR(50),
    check_id VARCHAR(50),

    -- Query details
    query_text TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'warning',  -- info, warning, error, critical
    query_type VARCHAR(20) DEFAULT 'auto',   -- auto, manual

    -- Status tracking
    status VARCHAR(20) DEFAULT 'open',       -- open, answered, closed, cancelled

    -- Timestamps and ownership
    opened_at TIMESTAMP DEFAULT NOW(),
    opened_by INTEGER,
    assigned_to INTEGER,

    -- Response
    response_text TEXT,
    responded_at TIMESTAMP,
    responded_by INTEGER,

    -- Resolution
    resolved_at TIMESTAMP,
    resolved_by INTEGER,
    resolution_notes TEXT,

    -- Audit
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_queries_subject ON queries(subject_id);
CREATE INDEX IF NOT EXISTS idx_queries_status ON queries(status);
CREATE INDEX IF NOT EXISTS idx_queries_opened_at ON queries(opened_at);

-- 12. Query History (Audit trail for queries)
CREATE TABLE IF NOT EXISTS query_history (
    history_id SERIAL PRIMARY KEY,
    query_id INTEGER NOT NULL REFERENCES queries(query_id),
    action VARCHAR(50) NOT NULL,  -- opened, answered, closed, escalated, cancelled
    action_by INTEGER,
    action_at TIMESTAMP DEFAULT NOW(),
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_query_history_query ON query_history(query_id);

-- 13. Form Definitions (Dynamic form builder)
CREATE TABLE IF NOT EXISTS form_definitions (
    form_id VARCHAR(50) PRIMARY KEY,
    form_name VARCHAR(255) NOT NULL,
    form_version VARCHAR(20) DEFAULT '1.0',

    -- Form structure (stored as JSON)
    form_schema JSONB NOT NULL,

    -- Edit checks (YAML format)
    edit_checks_yaml TEXT,

    -- Metadata
    status VARCHAR(20) DEFAULT 'draft',  -- draft, active, archived
    created_at TIMESTAMP DEFAULT NOW(),
    created_by INTEGER,
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_form_definitions_status ON form_definitions(status);

-- 14. Form Data (Generic form data storage)
CREATE TABLE IF NOT EXISTS form_data (
    data_id SERIAL PRIMARY KEY,
    form_id VARCHAR(50) NOT NULL REFERENCES form_definitions(form_id),
    subject_id VARCHAR(50) NOT NULL,
    visit_name VARCHAR(50),

    -- Actual form data (JSON)
    form_data JSONB NOT NULL,

    -- Status
    status VARCHAR(20) DEFAULT 'draft',  -- draft, submitted, locked

    -- Timestamps
    submitted_at TIMESTAMP,
    submitted_by INTEGER,
    locked_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_form_data_subject ON form_data(subject_id);
CREATE INDEX IF NOT EXISTS idx_form_data_form ON form_data(form_id);

-- 15. Demographics
CREATE TABLE IF NOT EXISTS demographics (
    demo_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50) NOT NULL,

    -- Demographics
    age INTEGER CHECK (age BETWEEN 18 AND 85),
    gender VARCHAR(20),  -- Male, Female, Other
    race VARCHAR(50),    -- White, Black, Asian, Other
    ethnicity VARCHAR(50), -- Hispanic/Latino, Not Hispanic/Latino

    -- Physical measurements
    height_cm DECIMAL(5,2) CHECK (height_cm BETWEEN 140 AND 220),
    weight_kg DECIMAL(5,2) CHECK (weight_kg BETWEEN 40 AND 200),
    bmi DECIMAL(5,2),    -- Calculated

    -- Medical history
    smoking_status VARCHAR(50), -- Never, Former, Current

    -- Timestamps
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_demographics_subject ON demographics(subject_id);

-- 16. Lab Results
CREATE TABLE IF NOT EXISTS lab_results (
    lab_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50) NOT NULL,
    visit_name VARCHAR(50) NOT NULL,
    test_date DATE NOT NULL,

    -- Hematology (Complete Blood Count)
    hemoglobin DECIMAL(4,1),      -- 12-18 g/dL
    hematocrit DECIMAL(4,1),      -- 36-50%
    wbc DECIMAL(5,2),             -- 4-11 K/μL
    platelets DECIMAL(5,1),       -- 150-400 K/μL

    -- Chemistry (Metabolic Panel)
    glucose DECIMAL(5,1),         -- 70-100 mg/dL
    creatinine DECIMAL(4,2),      -- 0.7-1.3 mg/dL
    bun DECIMAL(4,1),             -- 7-20 mg/dL
    alt DECIMAL(5,1),             -- 7-56 U/L
    ast DECIMAL(5,1),             -- 10-40 U/L
    bilirubin DECIMAL(4,2),       -- 0.3-1.2 mg/dL

    -- Lipids
    total_cholesterol DECIMAL(5,1), -- mg/dL
    ldl DECIMAL(5,1),              -- mg/dL
    hdl DECIMAL(5,1),              -- mg/dL
    triglycerides DECIMAL(5,1),    -- mg/dL

    -- Timestamps
    recorded_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_lab_results_subject ON lab_results(subject_id);
CREATE INDEX IF NOT EXISTS idx_lab_results_visit ON lab_results(visit_name);

-- ============= FUNCTIONS & TRIGGERS =============

-- Auto-update timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger to patients table
DROP TRIGGER IF EXISTS update_patients_updated_at ON patients;
CREATE TRIGGER update_patients_updated_at
    BEFORE UPDATE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- Audit logging function
CREATE OR REPLACE FUNCTION audit_trigger()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_events (
        event_type,
        entity_type,
        entity_id,
        action,
        payload
    )
    VALUES (
        TG_OP || '_' || TG_TABLE_NAME,
        TG_TABLE_NAME,
        CASE
            WHEN TG_OP = 'DELETE' THEN OLD.patient_id
            ELSE NEW.patient_id
        END,
        TG_OP,
        to_jsonb(CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END)
    );
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Apply audit trigger to patients table
DROP TRIGGER IF EXISTS audit_patients ON patients;
CREATE TRIGGER audit_patients
    AFTER INSERT OR UPDATE OR DELETE ON patients
    FOR EACH ROW
    EXECUTE FUNCTION audit_trigger();

-- ============= PERFORMANCE OPTIMIZATIONS =============

-- Create materialized view for analytics
CREATE MATERIALIZED VIEW IF NOT EXISTS patient_analytics AS
SELECT
    p.site_id,
    p.protocol_id,
    COUNT(DISTINCT p.patient_id) as patient_count,
    AVG(EXTRACT(epoch FROM (NOW() - p.enrollment_date))/86400)::INT as avg_days_enrolled,
    COUNT(DISTINCT v.vital_id) as total_vitals,
    MAX(v.measurement_time) as last_vital_time
FROM patients p
LEFT JOIN vital_signs v ON p.patient_id = v.patient_id
GROUP BY p.site_id, p.protocol_id;

-- Index for analytics view
CREATE INDEX IF NOT EXISTS idx_patient_analytics ON patient_analytics(site_id, protocol_id);

-- ============= SAMPLE DATA (for testing) =============

-- Insert test user (demo tenant)
INSERT INTO users (tenant_id, username, email, password_hash, roles)
VALUES ('demo-org', 'admin', 'admin@clinicaltrials.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeWzJbvs/wlDJ2Nfu', '["admin","user"]')
ON CONFLICT (tenant_id, username) DO NOTHING;

-- Insert test patients (demo tenant)
INSERT INTO patients (tenant_id, subject_number, site_id, protocol_id, enrollment_date, treatment_arm, demographics)
VALUES
    ('demo-org', 'RA001-001', 'SITE001', 'PROTO-001', CURRENT_DATE - INTERVAL '30 days', 'Active',
     '{"age": 45, "gender": "F", "race": "Caucasian"}'::jsonb),
    ('demo-org', 'RA001-002', 'SITE001', 'PROTO-001', CURRENT_DATE - INTERVAL '25 days', 'Placebo',
     '{"age": 52, "gender": "M", "race": "Asian"}'::jsonb)
ON CONFLICT (tenant_id, subject_number) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Database schema initialized successfully!';
END $$;
