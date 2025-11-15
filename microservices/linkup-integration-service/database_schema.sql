-- Database Schema for Linkup Integration Service
-- This schema extends the main database with tables for:
-- 1. Evidence Pack storage
-- 2. Compliance monitoring
-- 3. Auto-generated edit check rules

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- Evidence Pack Tables
-- ============================================================================

-- Store evidence packs with quality runs
CREATE TABLE IF NOT EXISTS quality_evidence (
    evidence_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,
    quality_run_id UUID,  -- Link to quality assessment (optional)
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL,
    citation_title VARCHAR(500),
    citation_url TEXT,
    citation_snippet TEXT,
    source_domain VARCHAR(200),
    relevance_score DECIMAL,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE INDEX idx_quality_evidence_tenant_metric ON quality_evidence (tenant_id, metric_name);
CREATE INDEX idx_quality_evidence_quality_run ON quality_evidence (quality_run_id);
CREATE INDEX idx_quality_evidence_fetched_at ON quality_evidence (fetched_at DESC);

-- Store complete evidence packs
CREATE TABLE IF NOT EXISTS evidence_packs (
    pack_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,
    quality_run_id UUID,
    overall_quality_score DECIMAL,
    quality_level VARCHAR(50),  -- EXCELLENT, GOOD, NEEDS IMPROVEMENT
    citation_support VARCHAR(50),  -- STRONG, MODERATE, WEAK
    regulatory_ready BOOLEAN DEFAULT FALSE,
    evidence_summary TEXT,
    pack_data JSONB,  -- Full evidence pack as JSON
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE INDEX idx_evidence_packs_tenant ON evidence_packs (tenant_id);
CREATE INDEX idx_evidence_packs_quality_run ON evidence_packs (quality_run_id);
CREATE INDEX idx_evidence_packs_generated_at ON evidence_packs (generated_at DESC);


-- ============================================================================
-- Auto-Generated Edit Check Rules
-- ============================================================================

-- Store auto-generated edit check rules
CREATE TABLE IF NOT EXISTS auto_generated_rules (
    rule_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    variable_name VARCHAR(100) NOT NULL,
    indication VARCHAR(100),
    check_type VARCHAR(50),  -- range, allowed_values, differential, etc.
    severity VARCHAR(50),  -- Minor, Major, Critical
    rule_definition JSONB NOT NULL,  -- Full rule structure as JSON
    rule_yaml TEXT,  -- YAML representation
    confidence VARCHAR(50),  -- low, medium, high
    reviewed BOOLEAN DEFAULT FALSE,
    approved BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(100),
    approved_at TIMESTAMP,
    citations JSONB,  -- Array of citation objects
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE INDEX idx_auto_generated_rules_tenant ON auto_generated_rules (tenant_id);
CREATE INDEX idx_auto_generated_rules_variable ON auto_generated_rules (variable_name);
CREATE INDEX idx_auto_generated_rules_reviewed ON auto_generated_rules (reviewed, approved);
CREATE INDEX idx_auto_generated_rules_generated_at ON auto_generated_rules (generated_at DESC);


-- ============================================================================
-- Compliance Monitoring Tables
-- ============================================================================

-- Store compliance scan results
CREATE TABLE IF NOT EXISTS compliance_scans (
    scan_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sources_scanned INTEGER,
    total_updates INTEGER,
    high_impact_count INTEGER,
    medium_impact_count INTEGER,
    low_impact_count INTEGER,
    scan_status VARCHAR(50),  -- completed, in_progress, failed
    error_message TEXT,
    next_scan_scheduled TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_compliance_scans_timestamp ON compliance_scans (scan_timestamp DESC);


-- Store detected regulatory updates
CREATE TABLE IF NOT EXISTS regulatory_updates (
    update_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scan_id UUID REFERENCES compliance_scans(scan_id) ON DELETE CASCADE,
    source_name VARCHAR(100) NOT NULL,  -- FDA, ICH, CDISC, etc.
    title VARCHAR(500) NOT NULL,
    url TEXT NOT NULL,
    publication_date TIMESTAMP,
    snippet TEXT,
    impact_assessment VARCHAR(50),  -- HIGH, MEDIUM, LOW
    keywords_matched TEXT[],
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed BOOLEAN DEFAULT FALSE,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_regulatory_updates_scan ON regulatory_updates (scan_id);
CREATE INDEX idx_regulatory_updates_source ON regulatory_updates (source_name);
CREATE INDEX idx_regulatory_updates_impact ON regulatory_updates (impact_assessment);
CREATE INDEX idx_regulatory_updates_detected_at ON regulatory_updates (detected_at DESC);
CREATE INDEX idx_regulatory_updates_reviewed ON regulatory_updates (reviewed);


-- Store impact assessments for regulatory updates
CREATE TABLE IF NOT EXISTS update_impact_assessments (
    assessment_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    update_id UUID REFERENCES regulatory_updates(update_id) ON DELETE CASCADE,
    overall_impact VARCHAR(50),
    affected_rules_count INTEGER,
    affected_rules JSONB,  -- Array of affected rule objects
    recommendations TEXT[],
    requires_action BOOLEAN DEFAULT FALSE,
    action_taken TEXT,
    action_taken_by VARCHAR(100),
    action_taken_at TIMESTAMP,
    assessment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_impact_assessments_update ON update_impact_assessments (update_id);
CREATE INDEX idx_impact_assessments_requires_action ON update_impact_assessments (requires_action);


-- ============================================================================
-- Audit Log for Linkup Service
-- ============================================================================

CREATE TABLE IF NOT EXISTS linkup_audit_log (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100),
    user_id VARCHAR(100),
    action VARCHAR(100) NOT NULL,  -- search, generate_rule, scan_compliance, etc.
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    query_params JSONB,
    search_query TEXT,
    results_count INTEGER,
    success BOOLEAN,
    error_message TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_linkup_audit_tenant ON linkup_audit_log (tenant_id);
CREATE INDEX idx_linkup_audit_action ON linkup_audit_log (action);
CREATE INDEX idx_linkup_audit_timestamp ON linkup_audit_log (timestamp DESC);


-- ============================================================================
-- Configuration Tables
-- ============================================================================

-- Store Linkup API configuration and credentials
CREATE TABLE IF NOT EXISTS linkup_config (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id VARCHAR(100) NOT NULL,
    api_key_encrypted TEXT,  -- Encrypted Linkup API key
    search_depth_default VARCHAR(50) DEFAULT 'standard',  -- standard or deep
    max_results_default INTEGER DEFAULT 10,
    authoritative_domains TEXT[],  -- Preferred domains for regulatory search
    scan_frequency_hours INTEGER DEFAULT 24,
    alert_email VARCHAR(255),
    slack_webhook_url TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_tenant FOREIGN KEY (tenant_id) REFERENCES tenants(tenant_id) ON DELETE CASCADE
);

CREATE INDEX idx_linkup_config_tenant ON linkup_config (tenant_id);


-- ============================================================================
-- Views for Reporting
-- ============================================================================

-- View: Recent high-impact regulatory updates
CREATE OR REPLACE VIEW vw_recent_high_impact_updates AS
SELECT
    ru.update_id,
    ru.source_name,
    ru.title,
    ru.url,
    ru.publication_date,
    ru.snippet,
    ru.detected_at,
    ru.reviewed,
    uia.requires_action,
    uia.affected_rules_count
FROM regulatory_updates ru
LEFT JOIN update_impact_assessments uia ON ru.update_id = uia.update_id
WHERE ru.impact_assessment = 'HIGH'
  AND ru.detected_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
ORDER BY ru.detected_at DESC;


-- View: Evidence pack summary by tenant
CREATE OR REPLACE VIEW vw_evidence_pack_summary AS
SELECT
    ep.tenant_id,
    COUNT(*) as total_packs,
    SUM(CASE WHEN ep.regulatory_ready THEN 1 ELSE 0 END) as regulatory_ready_count,
    AVG(ep.overall_quality_score) as avg_quality_score,
    MAX(ep.generated_at) as last_pack_generated
FROM evidence_packs ep
GROUP BY ep.tenant_id;


-- View: Auto-generated rules needing review
CREATE OR REPLACE VIEW vw_rules_needing_review AS
SELECT
    agr.rule_id,
    agr.tenant_id,
    agr.rule_name,
    agr.variable_name,
    agr.confidence,
    agr.generated_at,
    jsonb_array_length(agr.citations) as citation_count
FROM auto_generated_rules agr
WHERE agr.reviewed = FALSE
ORDER BY agr.generated_at DESC;


-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger for auto_generated_rules
CREATE TRIGGER update_auto_generated_rules_updated_at
    BEFORE UPDATE ON auto_generated_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for linkup_config
CREATE TRIGGER update_linkup_config_updated_at
    BEFORE UPDATE ON linkup_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- Sample Data (for testing)
-- ============================================================================

-- Note: This section is commented out by default
-- Uncomment to insert sample data for testing

/*
-- Sample tenant (assumes tenants table exists)
INSERT INTO tenants (tenant_id, tenant_name)
VALUES ('tenant_test', 'Test Tenant')
ON CONFLICT (tenant_id) DO NOTHING;

-- Sample Linkup config
INSERT INTO linkup_config (tenant_id, authoritative_domains, scan_frequency_hours)
VALUES (
    'tenant_test',
    ARRAY['fda.gov', 'ich.org', 'cdisc.org', 'ema.europa.eu', 'transcelerate.org'],
    24
);

-- Sample compliance scan
INSERT INTO compliance_scans (sources_scanned, total_updates, high_impact_count, medium_impact_count, low_impact_count, scan_status)
VALUES (5, 12, 2, 5, 5, 'completed');
*/


-- ============================================================================
-- Grants (adjust based on your user setup)
-- ============================================================================

-- Grant permissions to application user (adjust username as needed)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT SELECT ON ALL VIEWS IN SCHEMA public TO your_app_user;
