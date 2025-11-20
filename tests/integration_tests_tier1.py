#!/usr/bin/env python3
"""
Integration Tests for Tier 1 Features
Tests Survival Analysis, ADaM Generation, and TLF Automation endpoints
"""

import json
import requests
import sys
from typing import Dict, Any, List

BASE_URL = "http://localhost:8003"

# Test data
DEMOGRAPHICS_DATA = [
    {"SubjectID": f"SUB-{str(i+1).zfill(3)}", "TreatmentArm": "Active" if i % 2 == 0 else "Placebo",
     "Age": 55 + i % 20, "Gender": "Male" if i % 2 == 0 else "Female",
     "Race": "White", "Ethnicity": "Not Hispanic or Latino",
     "Weight": 70 + i, "Height": 165 + i % 20}
    for i in range(100)
]

VITALS_DATA = [
    {"SubjectID": f"SUB-{str(i+1).zfill(3)}", "VisitName": visit,
     "TreatmentArm": "Active" if i % 2 == 0 else "Placebo",
     "SystolicBP": 130 + i % 30, "DiastolicBP": 80 + i % 20,
     "HeartRate": 70 + i % 20, "Temperature": 36.5 + (i % 10) / 10}
    for i in range(50)
    for visit in ["Screening", "Week 4", "Week 12"]
]

AE_DATA = [
    {"SubjectID": f"SUB-{str(i+1).zfill(3)}",
     "PT": ["Headache", "Nausea", "Fatigue", "Dizziness"][i % 4],
     "SOC": ["Nervous system disorders", "Gastrointestinal disorders",
                  "General disorders", "Nervous system disorders"][i % 4],
     "Severity": ["MILD", "MODERATE", "SEVERE"][i % 3],
     "Serious": "Yes" if i % 10 == 0 else "No",
     "Relationship": "Related" if i % 2 == 0 else "Not Related",
     "StartDate": "2025-01-15", "EndDate": "2025-01-20",
     "TreatmentArm": "Active" if i % 2 == 0 else "Placebo"}
    for i in range(30)
]


def test_endpoint(name: str, method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint and return results"""
    print(f"\n{'='*80}")
    print(f"Testing: {name}")
    print(f"Endpoint: {method} {url}")
    print(f"{'='*80}")

    try:
        if method == "GET":
            response = requests.get(url, timeout=30)
        else:  # POST
            response = requests.post(url, json=data, timeout=30)

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ SUCCESS")
            print(f"Response keys: {list(result.keys())}")
            return {"status": "PASS", "response": result, "name": name}
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            return {"status": "FAIL", "error": response.text, "name": name}

    except Exception as e:
        print(f"❌ EXCEPTION: {str(e)}")
        return {"status": "ERROR", "error": str(e), "name": name}


def main():
    """Run all integration tests"""
    print("\n" + "="*80)
    print("TIER 1 FEATURES - INTEGRATION TESTS")
    print("Testing: Survival Analysis, ADaM Generation, TLF Automation")
    print("="*80)

    results = []

    # =========================================================================
    # 1. SURVIVAL ANALYSIS TESTS
    # =========================================================================
    print("\n\n" + "="*80)
    print("1. SURVIVAL ANALYSIS MODULE")
    print("="*80)

    # Test 1.1: Comprehensive Survival Analysis
    results.append(test_endpoint(
        "Comprehensive Survival Analysis",
        "POST",
        f"{BASE_URL}/survival/comprehensive",
        {
            "demographics_data": DEMOGRAPHICS_DATA,
            "indication": "oncology",
            "median_survival_active": 18.0,
            "median_survival_placebo": 12.0,
            "seed": 42
        }
    ))

    # Get survival data from first test for subsequent tests
    if results[-1]["status"] == "PASS":
        survival_data = results[-1]["response"]["survival_data"]

        # Test 1.2: Kaplan-Meier Calculation
        results.append(test_endpoint(
            "Kaplan-Meier Calculation",
            "POST",
            f"{BASE_URL}/survival/kaplan-meier",
            {
                "survival_data": survival_data,
                "treatment_arm": "Active"
            }
        ))

        # Test 1.3: Log-Rank Test
        results.append(test_endpoint(
            "Log-Rank Test",
            "POST",
            f"{BASE_URL}/survival/log-rank-test",
            {
                "survival_data": survival_data,
                "arm1": "Active",
                "arm2": "Placebo"
            }
        ))

        # Test 1.4: Hazard Ratio
        results.append(test_endpoint(
            "Hazard Ratio Calculation",
            "POST",
            f"{BASE_URL}/survival/hazard-ratio",
            {
                "survival_data": survival_data,
                "reference_arm": "Placebo",
                "treatment_arm": "Active"
            }
        ))

    # =========================================================================
    # 2. ADAM GENERATION TESTS
    # =========================================================================
    print("\n\n" + "="*80)
    print("2. ADAM DATASET GENERATION MODULE")
    print("="*80)

    # Test 2.1: Generate All ADaM Datasets
    results.append(test_endpoint(
        "Generate All ADaM Datasets",
        "POST",
        f"{BASE_URL}/adam/generate-all",
        {
            "demographics_data": DEMOGRAPHICS_DATA,
            "vitals_data": VITALS_DATA,
            "ae_data": AE_DATA,
            "study_id": "INTTEST001"
        }
    ))

    # Test 2.2: Generate ADSL Only
    results.append(test_endpoint(
        "Generate ADSL Dataset",
        "POST",
        f"{BASE_URL}/adam/adsl",
        {
            "demographics_data": DEMOGRAPHICS_DATA,
            "vitals_data": VITALS_DATA,
            "study_id": "INTTEST001"
        }
    ))

    # =========================================================================
    # 3. TLF AUTOMATION TESTS
    # =========================================================================
    print("\n\n" + "="*80)
    print("3. TLF AUTOMATION MODULE")
    print("="*80)

    # Test 3.1: Generate All TLF Tables
    results.append(test_endpoint(
        "Generate All TLF Tables",
        "POST",
        f"{BASE_URL}/tlf/generate-all",
        {
            "demographics_data": DEMOGRAPHICS_DATA,
            "ae_data": AE_DATA,
            "vitals_data": VITALS_DATA
        }
    ))

    # Test 3.2: Table 1 - Demographics
    results.append(test_endpoint(
        "Table 1: Demographics",
        "POST",
        f"{BASE_URL}/tlf/table1-demographics",
        {
            "demographics_data": DEMOGRAPHICS_DATA,
            "include_stats": True
        }
    ))

    # Test 3.3: Table 2 - Adverse Events
    results.append(test_endpoint(
        "Table 2: Adverse Events",
        "POST",
        f"{BASE_URL}/tlf/table2-adverse-events",
        {
            "ae_data": AE_DATA,
            "by_soc": True,
            "min_incidence": 5.0
        }
    ))

    # Test 3.4: Table 3 - Efficacy
    results.append(test_endpoint(
        "Table 3: Efficacy",
        "POST",
        f"{BASE_URL}/tlf/table3-efficacy",
        {
            "vitals_data": VITALS_DATA,
            "endpoint_type": "vitals"
        }
    ))

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n\n" + "="*80)
    print("INTEGRATION TEST SUMMARY")
    print("="*80)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    errors = sum(1 for r in results if r["status"] == "ERROR")
    total = len(results)

    print(f"\nTotal Tests: {total}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"💥 Errors: {errors}")
    print(f"\nSuccess Rate: {(passed/total)*100:.1f}%")

    # Detailed results
    print("\n" + "-"*80)
    print("DETAILED RESULTS")
    print("-"*80)
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result["status"] == "PASS" else "❌"
        print(f"{i}. {status_icon} {result['name']}: {result['status']}")

    # Return exit code
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
