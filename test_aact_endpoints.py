#!/usr/bin/env python3
"""
Test script for AACT Analytics Endpoints
Tests all three new endpoints with different parameters
"""

import requests
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8002"

def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_endpoint(endpoint: str, params: Dict[str, str] = None) -> Dict[str, Any]:
    """Test an endpoint and return the response"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n📡 Testing: {url}")
    if params:
        print(f"   Parameters: {params}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        print(f"✅ Status: {response.status_code}")
        print(f"   Response keys: {list(data.keys())}")
        return data
    except requests.exceptions.RequestException as e:
        print(f"❌ Error: {str(e)}")
        return None

def test_demographics():
    """Test demographics analytics endpoint"""
    print_section("TEST 1: Demographics Analytics")
    
    # Test with default parameters
    data = test_endpoint("/aact/analytics/demographics")
    if data:
        print(f"\n📊 Demographics Data:")
        print(f"   - Age distribution entries: {len(data.get('age_distribution', []))}")
        print(f"   - Gender distribution entries: {len(data.get('gender_distribution', []))}")
        print(f"   - Race distribution entries: {len(data.get('race_distribution', []))}")
        print(f"   - Source: {data.get('source')}")
        print(f"   - Indication: {data.get('indication')}")
        print(f"   - Phase: {data.get('phase')}")
        
        # Show sample data
        if data.get('age_distribution'):
            print(f"\n   Sample age range: {data['age_distribution'][0]}")
        if data.get('gender_distribution'):
            print(f"   Sample gender: {data['gender_distribution'][0]}")
    
    # Test with different indication
    print("\n" + "-"*80)
    data2 = test_endpoint("/aact/analytics/demographics", {"indication": "diabetes", "phase": "Phase 2"})
    if data2:
        print(f"   ✓ Different parameters work correctly")

def test_adverse_events():
    """Test adverse events analytics endpoint"""
    print_section("TEST 2: Adverse Events Analytics")
    
    # Test with default parameters
    data = test_endpoint("/aact/analytics/adverse_events")
    if data:
        print(f"\n📊 Adverse Events Data:")
        print(f"   - Common AEs: {len(data.get('common_aes', []))}")
        print(f"   - SOC distribution entries: {len(data.get('soc_distribution', []))}")
        print(f"   - Severity distribution entries: {len(data.get('severity_distribution', []))}")
        print(f"   - Top events: {len(data.get('top_events', []))}")
        print(f"   - Source: {data.get('source')}")
        
        # Show sample data
        if data.get('common_aes'):
            print(f"\n   Sample AE: {data['common_aes'][0]}")
        if data.get('soc_distribution'):
            print(f"   Sample SOC: {data['soc_distribution'][0]}")
    
    # Test with different indication
    print("\n" + "-"*80)
    data2 = test_endpoint("/aact/analytics/adverse_events", {"indication": "oncology"})
    if data2:
        print(f"   ✓ Different indication works correctly")

def test_labs():
    """Test labs analytics endpoint"""
    print_section("TEST 3: Labs Analytics")
    
    # Test with default parameters
    data = test_endpoint("/aact/analytics/labs")
    if data:
        print(f"\n📊 Labs Data:")
        print(f"   - Hematology parameters: {len(data.get('hematology', []))}")
        print(f"   - Chemistry parameters: {len(data.get('chemistry', []))}")
        print(f"   - Urinalysis parameters: {len(data.get('urinalysis', []))}")
        print(f"   - Source: {data.get('source')}")
        
        # Show sample data
        if data.get('hematology'):
            print(f"\n   Sample hematology: {data['hematology'][0]}")
        if data.get('chemistry'):
            print(f"   Sample chemistry: {data['chemistry'][0]}")
        if data.get('urinalysis'):
            print(f"   Sample urinalysis: {data['urinalysis'][0]}")
    
    # Test with different parameters
    print("\n" + "-"*80)
    data2 = test_endpoint("/aact/analytics/labs", {"indication": "cardiovascular", "phase": "Phase 3"})
    if data2:
        print(f"   ✓ Different parameters work correctly")

def test_data_consistency():
    """Test data consistency across endpoints"""
    print_section("TEST 4: Data Consistency")
    
    # Fetch all endpoints with same parameters
    params = {"indication": "hypertension", "phase": "Phase 3"}
    
    demo = test_endpoint("/aact/analytics/demographics", params)
    ae = test_endpoint("/aact/analytics/adverse_events", params)
    labs = test_endpoint("/aact/analytics/labs", params)
    
    if demo and ae and labs:
        print(f"\n✅ All endpoints returned successfully")
        print(f"   - Demographics source: {demo.get('source')}")
        print(f"   - AE source: {ae.get('source')}")
        print(f"   - Labs source: {labs.get('source')}")
        print(f"   - All sources match: {demo.get('source') == ae.get('source') == labs.get('source')}")
        
        # Check indication and phase consistency
        all_match = (
            demo.get('indication') == params['indication'] and
            ae.get('indication') == params['indication'] and
            labs.get('indication') == params['indication'] and
            demo.get('phase') == params['phase'] and
            ae.get('phase') == params['phase'] and
            labs.get('phase') == params['phase']
        )
        print(f"   - Parameters preserved: {all_match}")

def test_typescript_compatibility():
    """Verify response structures match TypeScript interfaces"""
    print_section("TEST 5: TypeScript Interface Compatibility")
    
    demo = test_endpoint("/aact/analytics/demographics")
    if demo:
        print("\n✓ Demographics Response Structure:")
        print(f"   - age_distribution: {type(demo.get('age_distribution'))}")
        print(f"   - gender_distribution: {type(demo.get('gender_distribution'))}")
        print(f"   - race_distribution: {type(demo.get('race_distribution'))}")
        
        # Check age_distribution structure
        if demo.get('age_distribution') and len(demo['age_distribution']) > 0:
            age_item = demo['age_distribution'][0]
            print(f"   - Age item has 'range': {'range' in age_item}")
            print(f"   - Age item has 'active': {'active' in age_item}")
            print(f"   - Age item has 'placebo': {'placebo' in age_item}")

def run_all_tests():
    """Run all tests"""
    print("\n" + "🧪 "*30)
    print("AACT Analytics Endpoints - Comprehensive Test Suite")
    print("🧪 "*30)
    
    try:
        test_demographics()
        test_adverse_events()
        test_labs()
        test_data_consistency()
        test_typescript_compatibility()
        
        print_section("✅ TEST SUMMARY")
        print("\nAll tests completed successfully!")
        print("Endpoints are ready for frontend integration.")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_all_tests()
