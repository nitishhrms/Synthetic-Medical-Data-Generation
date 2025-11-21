# Parallel Development Plan: EDC & Quality Services

## Goal
Enable parallel development of the **EDC (Electronic Data Capture) Service** and **Quality Service** while the core data generation bug is being resolved. These services can be developed independently by mocking input data and focusing on infrastructure, schema design, and business logic.

## 1. EDC Service Development
**Objective:** Build the system for managing clinical trial data, including study setup, subject enrollment, and form data capture.

### Phase 1: Database Schema & Models (Independent)
- [ ] **Refine Database Schema:**
    - Review `medical_images_schema.sql` and ensure it covers all requirements (DICOM metadata, storage paths).
    - Design schemas for `studies`, `sites`, `subjects`, `visits`, and `forms` (currently in-memory in `main.py`, move to PostgreSQL).
- [ ] **Pydantic Models:**
    - Enhance `Study`, `Subject`, and `FormDefinition` models to match industry standards (CDISC ODM-like structure).

### Phase 2: API Implementation (Independent)
- [ ] **Study Management:**
    - Implement persistent CRUD endpoints for Studies and Sites (backed by DB, not memory).
- [ ] **Subject Management:**
    - Implement Subject Enrollment and Status tracking APIs.
- [ ] **Form Engine:**
    - Build the "Form Definition" engine:
        - Store JSON schemas for CRFs (Case Report Forms).
        - Implement `POST /forms/submit` to validate and store form data against these schemas.
    - **Mocking:** Use hardcoded JSON schemas for "Vitals", "Demographics", and "Labs" forms to test the engine without needing generated data.

### Phase 3: Frontend Integration (Parallel)
- [ ] **EDC Dashboard:**
    - Create a new "EDC" tab in the frontend.
    - Build a "Study Config" page to create studies/sites.
    - Build a "Subject Matrix" view showing subjects vs. visits.
- [ ] **Data Entry Forms:**
    - Create a dynamic form renderer component that takes a JSON schema and renders inputs.
    - Connect to `POST /forms/submit`.

## 2. Quality Service Development
**Objective:** Build the engine for running edit checks, calculating quality metrics, and managing queries.

### Phase 1: Edit Check Engine (Independent)
- [ ] **Rule Engine Enhancement:**
    - Expand `edit_checks.py` to support more complex logic (e.g., cross-form validation, date comparisons).
    - Implement a "Rule Builder" API where users can define rules via JSON/YAML.
- [ ] **Query Management:**
    - Fully implement the Query lifecycle (Open -> Answered -> Closed).
    - Ensure `POST /checks/validate-and-save-queries` correctly persists queries to the DB.

### Phase 2: Quality Metrics (Mock-Data Driven)
- [ ] **SYNDATA Implementation:**
    - Verify `syndata_metrics.py` logic using **manually created CSVs** (one "real", one "synthetic").
    - You do *not* need the generator to be working to test if the math for "Support Coverage" or "K-Anonymity" is correct.
    - Create a test suite with known datasets to validate these metrics.
- [ ] **Privacy Assessment:**
    - Similarly, test `privacy_assessment.py` with mock datasets containing known re-identification risks.

### Phase 3: Frontend Quality Dashboard (Parallel)
- [ ] **Quality Dashboard:**
    - Create a "Data Quality" tab.
    - **Widgets:**
        - "Open Queries" counter.
        - "Data Quality Score" gauge (mocked for now).
        - "Validation Issues" table.
- [ ] **Query Management UI:**
    - Build a UI for Data Managers to view, answer, and close queries.

## 3. Integration Strategy (Post-Fix)
Once the data generation bug is fixed:
1.  **Connect Pipelines:** Point the `generate_comprehensive_study` output to automatically ingest into the EDC database via `POST /import/synthetic`.
2.  **Real Validation:** Run the Quality Service against the *actual* generated data to produce real quality reports.

## Immediate Action Items for Team Member
1.  **Database Migration:** Move EDC `studies_db` and `subjects_db` from in-memory dictionaries to proper PostgreSQL tables in `db_utils.py`.
2.  **Form Engine:** Implement the JSON Schema storage and validation logic in `edc-service`.
3.  **Quality UI:** Start building the "Data Quality" dashboard frontend using mock data.
