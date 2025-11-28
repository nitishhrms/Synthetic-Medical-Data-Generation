"""
Test Analytics Service Enhanced Validation Endpoints
=====================================================

Tests the new validation endpoints we added to analytics service.
"""

import sys
sys.path.insert(0, '/Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

from generate_vitals_enhanced import generate_vitals_enhanced
import requests
import json

print("=" * 80)
print("ANALYTICS SERVICE - ENHANCED VALIDATION TEST")
print("=" * 80)

# Generate test data
print("\n1. Generating test data...")
df = generate_vitals_enhanced(
    n_per_arm=50,
    use_temporal_correlation=True,
    use_heterogeneous_effects=True,
    missingness_mechanism='MAR',
    seed=42
)

print(f"   Generated {len(df)} measurements for {df['SubjectID'].nunique()} subjects")

# Convert to format expected by API
data_records = df.to_dict('records')

# Analytics service URL
ANALYTICS_URL = "http://localhost:8003"

print("\n" + "=" * 80)
print("2. TEST: Temporal Correlation Validation")
print("=" * 80)

try:
    response = requests.post(
        f"{ANALYTICS_URL}/validate/temporal-correlation",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: {result['status']}")
        print(f"✅ Grade: {result.get('grade', 'N/A')}")
        print(f"✅ Mean Correlation: {result['metrics'].get('mean_correlation', 'N/A')}")
        print(f"✅ Interpretation: {result.get('interpretation', 'N/A')}")
        print(f"✅ Recommendations: {len(result.get('recommendations', []))} provided")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to analytics service (port 8003)")
    print("   Make sure service is running: docker compose up")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("3. TEST: Heterogeneous Effects Validation")
print("=" * 80)

try:
    response = requests.post(
        f"{ANALYTICS_URL}/validate/heterogeneous-effects",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: {result['status']}")
        print(f"✅ Grade: {result.get('grade', 'N/A')}")
        print(f"✅ Heterogeneity Score: {result.get('heterogeneity_score', 'N/A')}/100")
        
        if 'metrics' in result and 'Active' in result['metrics']:
            active = result['metrics']['Active']
            print(f"✅ Active Arm Effect Std: {active.get('std_effect', 'N/A')} mmHg")
            print(f"✅ Effect Range: {active.get('min_effect', 'N/A')} to {active.get('max_effect', 'N/A')} mmHg")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to analytics service")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("4. TEST: Missingness Mechanism Validation")
print("=" * 80)

try:
    response = requests.post(
        f"{ANALYTICS_URL}/validate/missingness-mechanism",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Status: {result['status']}")
        print(f"✅ Classification: {result.get('classification', 'N/A')}")
        print(f"✅ Interpretation: {result.get('interpretation', 'N/A')}")
        
        if 'mar_tests' in result and 'adverse_events' in result['mar_tests']:
            ae_test = result['mar_tests']['adverse_events']
            print(f"✅ Dropout with AE: {ae_test.get('dropout_with_ae', 'N/A'):.1%}")
            print(f"✅ Dropout without AE: {ae_test.get('dropout_without_ae', 'N/A'):.1%}")
            print(f"✅ Significant: {ae_test.get('significant', False)}")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to analytics service")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("5. TEST: Comprehensive Validation")
print("=" * 80)

try:
    response = requests.post(
        f"{ANALYTICS_URL}/validate/enhanced-comprehensive",
        json={"data": data_records},
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Overall Score: {result['overall']['score']}/100")
        print(f"✅ Overall Grade: {result['overall']['grade']}")
        print(f"✅ Summary: {result['overall']['summary']}")
        print(f"✅ Subjects Analyzed: {result['n_subjects']}")
        print(f"✅ Total Measurements: {result['n_measurements']}")
        
        # Show individual validation statuses
        if 'validations' in result:
            print(f"\n   Individual Validations:")
            for key, val in result['validations'].items():
                status = val.get('status', 'unknown')
                grade = val.get('grade', val.get('classification', 'N/A'))
                print(f"     - {key:25s}: {status:6s} (Grade: {grade})")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to analytics service")
    print("   Is docker compose running?")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("""
✅ Enhanced validation endpoints added to Analytics Service!

Endpoints available:
  - POST /validate/temporal-correlation
  - POST /validate/heterogeneous-effects
  - POST /validate/missingness-mechanism
  - POST /validate/enhanced-comprehensive

These endpoints validate:
  1. Temporal correlation (ρ~0.7)
  2. Treatment effect heterogeneity (std>2.0)
  3. Missingness mechanisms (MAR vs MCAR)

Use these to ensure your generated data is research-grade!
""")

print("=" * 80)
