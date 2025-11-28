#!/usr/bin/env python3
"""
Comprehensive Test Suite for All 26 Analytics Endpoints
Tests every endpoint with appropriate sample data
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8003"

# Sample test data
SAMPLE_DEMOGRAPHICS = [
    {"SubjectID": "S001", "Age": 45, "Gender": "Male", "Race": "White", "Ethnicity": "Not Hispanic",
     "Weight": 75, "Height": 175, "BMI": 24.5, "TreatmentArm": "Active"},
    {"SubjectID": "S002", "Age": 52, "Gender": "Female", "Race": "Asian", "Ethnicity": "Not Hispanic",
     "Weight": 68, "Height": 165, "BMI": 25.0, "TreatmentArm": "Placebo"}
]

SAMPLE_VITALS = [
    {"SubjectID": "S001", "VisitName": "Screening", "TreatmentArm": "Active",
     "SystolicBP": 142, "DiastolicBP": 88, "HeartRate": 72, "Temperature": 36.7},
    {"SubjectID": "S001", "VisitName": "Week 12", "TreatmentArm": "Active",
     "SystolicBP": 135, "DiastolicBP": 82, "HeartRate": 70, "Temperature": 36.6}
]

SAMPLE_LABS_LONG = [
    {"SubjectID": "S001", "VisitName": "Baseline", "VisitNum": 1, "TestName": "ALT", "TestValue": 25, "TreatmentArm": "Active"},
    {"SubjectID": "S001", "VisitName": "Baseline", "VisitNum": 1, "TestName": "AST", "TestValue": 30, "TreatmentArm": "Active"},
    {"SubjectID": "S001", "VisitName": "Week 4", "VisitNum": 2, "TestName": "ALT", "TestValue": 28, "TreatmentArm": "Active"}
]

SAMPLE_AE = [
    {"SubjectID": "S001", "SOC": "Gastrointestinal disorders", "PT": "Nausea",
     "Severity": "Mild", "Relationship": "Possibly Related", "Serious": "No",
     "OnsetDate": "2025-01-15", "TreatmentArm": "Active"},
    {"SubjectID": "S002", "SOC": "Nervous system disorders", "PT": "Headache",
     "Severity": "Moderate", "Relationship": "Not Related", "Serious": "No",
     "OnsetDate": "2025-01-20", "TreatmentArm": "Placebo"}
]

def test_endpoint(name: str, url: str, payload: Dict[str, Any]) -> bool:
    """Test a single endpoint"""
    try:
        response = requests.post(f"{BASE_URL}{url}", json=payload, timeout=10)
        if response.ok:
            print(f"✅ {name}")
            return True
        else:
            print(f"❌ {name} - HTTP {response.status_code}: {response.text[:100]}")
            return False
    except Exception as e:
        print(f"❌ {name} - Error: {str(e)}")
        return False

def main():
    print("=" * 80)
    print("COMPREHENSIVE ANALYTICS SERVICE TEST - ALL 26 ENDPOINTS")
    print("=" * 80)

    results = {}

    # Phase 1: Demographics (5 endpoints)
    print("\n📊 PHASE 1: Demographics Analytics (5 endpoints)")
    print("-" * 80)
    results["demographics_baseline"] = test_endpoint(
        "POST /stats/demographics/baseline",
        "/stats/demographics/baseline",
        {"demographics_data": SAMPLE_DEMOGRAPHICS}
    )
    results["demographics_summary"] = test_endpoint(
        "POST /stats/demographics/summary",
        "/stats/demographics/summary",
        {"demographics_data": SAMPLE_DEMOGRAPHICS}
    )
    results["demographics_balance"] = test_endpoint(
        "POST /stats/demographics/balance",
        "/stats/demographics/balance",
        {"demographics_data": SAMPLE_DEMOGRAPHICS}
    )
    results["demographics_quality"] = test_endpoint(
        "POST /quality/demographics/compare",
        "/quality/demographics/compare",
        {"real_demographics": SAMPLE_DEMOGRAPHICS, "synthetic_demographics": SAMPLE_DEMOGRAPHICS}
    )
    results["demographics_sdtm"] = test_endpoint(
        "POST /sdtm/demographics/export",
        "/sdtm/demographics/export",
        {"demographics_data": SAMPLE_DEMOGRAPHICS}
    )

    # Phase 2: Labs (7 endpoints)
    print("\n🧪 PHASE 2: Labs Analytics (7 endpoints)")
    print("-" * 80)
    results["labs_summary"] = test_endpoint(
        "POST /stats/labs/summary",
        "/stats/labs/summary",
        {"labs_data": SAMPLE_LABS_LONG}
    )
    results["labs_abnormal"] = test_endpoint(
        "POST /stats/labs/abnormal",
        "/stats/labs/abnormal",
        {"labs_data": SAMPLE_LABS_LONG}
    )
    results["labs_shift"] = test_endpoint(
        "POST /stats/labs/shift-tables",
        "/stats/labs/shift-tables",
        {"labs_data": SAMPLE_LABS_LONG}
    )
    results["labs_quality"] = test_endpoint(
        "POST /quality/labs/compare",
        "/quality/labs/compare",
        {"real_labs": SAMPLE_LABS_LONG, "synthetic_labs": SAMPLE_LABS_LONG}
    )
    results["labs_safety"] = test_endpoint(
        "POST /stats/labs/safety-signals",
        "/stats/labs/safety-signals",
        {"labs_data": SAMPLE_LABS_LONG}
    )
    results["labs_longitudinal"] = test_endpoint(
        "POST /stats/labs/longitudinal",
        "/stats/labs/longitudinal",
        {"labs_data": SAMPLE_LABS_LONG}
    )
    results["labs_sdtm"] = test_endpoint(
        "POST /sdtm/labs/export",
        "/sdtm/labs/export",
        {"labs_data": SAMPLE_LABS_LONG}
    )

    # Phase 3: Adverse Events (5 endpoints)
    print("\n⚠️  PHASE 3: Adverse Events Analytics (5 endpoints)")
    print("-" * 80)
    results["ae_summary"] = test_endpoint(
        "POST /stats/ae/summary",
        "/stats/ae/summary",
        {"ae_data": SAMPLE_AE}
    )
    results["ae_teae"] = test_endpoint(
        "POST /stats/ae/treatment-emergent",
        "/stats/ae/treatment-emergent",
        {"ae_data": SAMPLE_AE, "treatment_start_date": "2025-01-01"}
    )
    results["ae_soc"] = test_endpoint(
        "POST /stats/ae/soc-analysis",
        "/stats/ae/soc-analysis",
        {"ae_data": SAMPLE_AE}
    )
    results["ae_quality"] = test_endpoint(
        "POST /quality/ae/compare",
        "/quality/ae/compare",
        {"real_ae": SAMPLE_AE, "synthetic_ae": SAMPLE_AE}
    )
    results["ae_sdtm"] = test_endpoint(
        "POST /sdtm/ae/export",
        "/sdtm/ae/export",
        {"ae_data": SAMPLE_AE}
    )

    # Phase 4: AACT Integration (3 endpoints)
    print("\n🌍 PHASE 4: AACT Integration (3 endpoints)")
    print("-" * 80)
    results["aact_compare"] = test_endpoint(
        "POST /aact/compare-study",
        "/aact/compare-study",
        {"n_subjects": 100, "indication": "hypertension", "phase": "Phase 3", "treatment_effect": -5.2}
    )
    results["aact_demographics"] = test_endpoint(
        "POST /aact/benchmark-demographics",
        "/aact/benchmark-demographics",
        {"demographics_data": SAMPLE_DEMOGRAPHICS, "indication": "hypertension", "phase": "Phase 3"}
    )
    results["aact_ae"] = test_endpoint(
        "POST /aact/benchmark-ae",
        "/aact/benchmark-ae",
        {"ae_data": SAMPLE_AE, "indication": "hypertension", "phase": "Phase 3"}
    )

    # Phase 5: Comprehensive Study Analytics (3 endpoints)
    print("\n📈 PHASE 5: Comprehensive Study Analytics (3 endpoints)")
    print("-" * 80)
    results["study_summary"] = test_endpoint(
        "POST /study/comprehensive-summary",
        "/study/comprehensive-summary",
        {"demographics_data": SAMPLE_DEMOGRAPHICS, "vitals_data": SAMPLE_VITALS,
         "labs_data": SAMPLE_LABS_LONG, "ae_data": SAMPLE_AE,
         "indication": "hypertension", "phase": "Phase 3"}
    )
    results["study_correlations"] = test_endpoint(
        "POST /study/cross-domain-correlations",
        "/study/cross-domain-correlations",
        {"demographics_data": SAMPLE_DEMOGRAPHICS, "vitals_data": SAMPLE_VITALS,
         "labs_data": SAMPLE_LABS_LONG, "ae_data": SAMPLE_AE}
    )
    results["study_dashboard"] = test_endpoint(
        "POST /study/trial-dashboard",
        "/study/trial-dashboard",
        {"demographics_data": SAMPLE_DEMOGRAPHICS, "vitals_data": SAMPLE_VITALS,
         "labs_data": SAMPLE_LABS_LONG, "ae_data": SAMPLE_AE,
         "indication": "hypertension", "phase": "Phase 3"}
    )

    # Phase 6: Benchmarking (3 endpoints)
    print("\n🎯 PHASE 6: Benchmarking & Extensions (3 endpoints)")
    print("-" * 80)
    results["benchmark_performance"] = test_endpoint(
        "POST /benchmark/performance",
        "/benchmark/performance",
        {"methods_data": {
            "mvn": {"generation_time_ms": 14, "records_generated": 400, "quality_score": 0.87, "aact_similarity": 0.91},
            "bootstrap": {"generation_time_ms": 3, "records_generated": 400, "quality_score": 0.92, "aact_similarity": 0.88}
        }}
    )
    results["benchmark_quality"] = test_endpoint(
        "POST /benchmark/quality-scores",
        "/benchmark/quality-scores",
        {"demographics_quality": 0.89, "vitals_quality": 0.92, "labs_quality": 0.88,
         "ae_quality": 0.85, "aact_similarity": 0.91}
    )
    results["study_recommendations"] = test_endpoint(
        "POST /study/recommendations",
        "/study/recommendations",
        {"current_quality": 0.72, "aact_similarity": 0.65, "generation_method": "mvn",
         "n_subjects": 50, "indication": "hypertension", "phase": "Phase 3"}
    )

    # Legacy endpoints (already existed)
    print("\n📊 LEGACY ENDPOINTS (2 endpoints)")
    print("-" * 80)
    results["week12_stats"] = test_endpoint(
        "POST /stats/week12",
        "/stats/week12",
        {"vitals_data": SAMPLE_VITALS}
    )
    results["quality_comprehensive"] = test_endpoint(
        "POST /quality/comprehensive",
        "/quality/comprehensive",
        {"original_data": SAMPLE_VITALS, "synthetic_data": SAMPLE_VITALS, "k": 5}
    )

    # Summary
    print("\n" + "=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\n✅ Passed: {passed}/{total} endpoints ({100*passed/total:.1f}%)")
    print(f"❌ Failed: {total-passed}/{total} endpoints")

    if passed == total:
        print("\n🎉 ALL ENDPOINTS WORKING PERFECTLY!")
        return 0
    else:
        print("\n⚠️  Some endpoints failed. Review errors above.")
        failed_endpoints = [name for name, passed in results.items() if not passed]
        print(f"\nFailed endpoints: {', '.join(failed_endpoints)}")
        return 1

if __name__ == "__main__":
    exit(main())
