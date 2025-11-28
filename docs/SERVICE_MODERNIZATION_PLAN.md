# Service Modernization Plan: AACT Integration Strategy

**Date:** November 20, 2025
**Status:** Draft
**Target Audience:** Product Management, Engineering Team

---

## 1. Executive Summary

The recent integration of **AACT (Aggregate Analysis of ClinicalTrials.gov)** into the Data Generation Service has transformed our platform's ability to produce realistic, indication-specific clinical trial data. However, our downstream services—**EDC (Electronic Data Capture)**, **Quality Service**, and **RBQM (Risk-Based Quality Management)**—are currently operating with static, generic rules and do not yet leverage this rich intelligence.

This document outlines a comprehensive strategy to modernize these services. By integrating AACT data across the entire platform, we will move from a "Generic Trial Simulator" to an **"Intelligent Clinical Trial Platform"** that adapts its validation, quality checks, and risk monitoring to the specific disease area being studied.

**Business Value:**
*   **Higher Data Quality:** Validation rules that match real-world clinical norms (e.g., Hypertension trials have different BP thresholds than Oncology trials).
*   **Realistic Risk Monitoring:** RBQM thresholds based on historical industry performance, reducing false positives.
*   **Faster Study Setup:** Auto-configuration of study parameters based on AACT historical data.

---

## 2. Current State vs. Target State

| Feature | Current State (Generic) | Target State (AACT-Driven) |
| :--- | :--- | :--- |
| **Study Design** | Manual setup with generic parameters. | **Auto-configured** based on Indication (e.g., "Diabetes" pre-selects relevant vitals, labs, and visit schedules). |
| **EDC Validation** | Hardcoded ranges (e.g., SBP 95-200 mmHg). | **Dynamic Ranges** based on AACT baseline stats (e.g., Mean ± 3SD for the specific indication). |
| **Edit Checks** | Static YAML file (`DEFAULT_RULES_YAML`). | **Adaptive Rules** generated dynamically from AACT distributions. |
| **Anomaly Detection** | Simple statistical outliers (Z-score > 3). | **Context-Aware Detection** comparing site data against AACT industry benchmarks. |
| **RBQM KRIs** | Static thresholds (e.g., Dropout > 20%). | **Data-Driven Thresholds** (e.g., "Dropout > Industry Avg + 10%"). |
| **Safety Monitoring** | Generic AE reporting. | **Expected vs. Observed** analysis using AACT AE frequency data. |

---

## 3. Implementation Plan

### Phase 1: Intelligent EDC (Study Design & Validation)

**Goal:** Enable the EDC service to "understand" the study indication and adapt its behavior.

#### 1.1 AACT-Aware Study Creation
*   **New Endpoint:** `POST /studies/from-indication`
*   **Functionality:**
    *   User selects "Hypertension".
    *   System queries Data Gen Service for Hypertension metadata (avg duration, common inclusion criteria).
    *   Creates Study with optimized configuration.

#### 1.2 Dynamic Validation Ranges
*   **Current:** `VitalsRecord` Pydantic model has hardcoded `ge=95, le=200`.
*   **Update:** Remove hardcoded constraints from Pydantic. Implement `DynamicValidator` class.
*   **Logic:**
    *   On startup/study-load, fetch baseline stats for the study's indication.
    *   Set `Min = Mean - 4*SD`, `Max = Mean + 4*SD`.
    *   *Example:* For Hypertension, SBP Max might be 220, but for Hypotension study, it might be 160.

### Phase 2: Adaptive Quality Service

**Goal:** Move from static YAML rules to dynamic rule generation.

#### 2.1 Dynamic Rule Generation
*   **Current:** `load_default_rules()` returns a static string.
*   **Update:** Create `RuleGenerator` service.
*   **Logic:**
    *   Input: Indication (e.g., "Diabetes").
    *   Action: Fetch AACT Labs data (Glucose, HbA1c).
    *   Output: Generate YAML rules specifically for Diabetes (e.g., "HbA1c > 15% is Critical").

#### 2.2 Context-Aware Outlier Detection
*   **Feature:** Instead of just checking if a value is an outlier within the *current* dataset, check if it's an outlier compared to *historical* AACT data.
*   **Value:** Detects "fabricated data" where a site might generate data that looks internally consistent but is statistically impossible for the disease population.

### Phase 3: Data-Driven RBQM (Risk-Based Quality Management)

**Goal:** Set risk thresholds based on industry reality, not guesses.

#### 3.1 Dynamic KRI Thresholds
*   **Current:** `generate_rbqm_summary` uses default thresholds (e.g., `q_rate_site=6.0`).
*   **Update:** Fetch thresholds from AACT.
    *   **Dropout Rate:** If AACT says "Diabetes Phase 3" has 12% dropout, set KRI Warning at 15%, Critical at 20%.
    *   **Screen Failure Rate:** Use AACT "Enrollment" data to set realistic screen fail expectations.

#### 3.2 Safety Signal Detection (Expected vs. Observed)
*   **Feature:** Compare observed Adverse Event rates at a site against AACT expected rates.
*   **Logic:**
    *   *Scenario:* Site 001 reports 0% "Nausea".
    *   *AACT Data:* "Nausea" occurs in 25% of patients in this indication.
    *   *Flag:* "Potential Under-reporting of AEs" (Risk Signal).

---

## 4. Technical Architecture Updates

```mermaid
graph TD
    AACT[AACT Database / Cache]
    DG[Data Generation Service]
    EDC[EDC Service]
    QS[Quality Service]
    RBQM[Analytics / RBQM]

    AACT -->|Raw Stats| DG
    DG -->|Expose API /stats/{indication}| EDC
    DG -->|Expose API /stats/{indication}| QS
    DG -->|Expose API /stats/{indication}| RBQM

    subgraph "Phase 1"
    EDC -- Fetch Ranges --> DG
    end

    subgraph "Phase 2"
    QS -- Fetch Distribution --> DG
    end

    subgraph "Phase 3"
    RBQM -- Fetch Benchmarks --> DG
    end
```

**Key Architectural Decision:**
*   The **Data Generation Service** will act as the "Source of Truth" for AACT statistics. It already has the logic to process and cache this data.
*   Other services will query Data Gen via internal API (e.g., `http://data-generation-service:8002/aact/stats/{indication}`) to get the parameters they need.

---

## 5. Roadmap & Timeline

| Sprint | Focus | Key Deliverables |
| :--- | :--- | :--- |
| **Sprint 1** | **EDC Modernization** | - `POST /studies/from-indication`<br>- Dynamic Vitals Validation |
| **Sprint 2** | **Quality Service** | - Dynamic YAML Rule Generator<br>- AACT-based Outlier Detection |
| **Sprint 3** | **RBQM Evolution** | - Dynamic KRI Thresholds<br>- "Expected vs. Observed" Safety Analysis |
| **Sprint 4** | **Frontend Integration** | - Update UI to show "Industry Benchmark" comparisons in charts |

---

## 6. Conclusion

This modernization plan leverages our unique advantage—access to 400,000+ real clinical trials—to create a platform that is not just a data collector, but an intelligent partner in clinical trial management. This directly supports our "Predictive AI" value proposition.
