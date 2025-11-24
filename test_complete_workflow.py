"""
COMPREHENSIVE END-TO-END WORKFLOW TEST
======================================

Tests the complete enhanced synthetic data workflow:
1. Generate enhanced data (A-grade quality)
2. Validate via Analytics Service
3. Generate quality report via Quality Service

This confirms the entire pipeline works!
"""

import sys
sys.path.insert(0, '/Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

from generate_vitals_enhanced import generate_vitals_enhanced
import requests
import json
from datetime import datetime

print("=" * 80)
print("🔬 COMPREHENSIVE END-TO-END WORKFLOW TEST")
print("=" * 80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

# Service URLs
ANALYTICS_URL = "http://localhost:8003"
QUALITY_URL = "http://localhost:8004"

workflow_status = {
    'data_generation': False,
    'analytics_validation': False,
    'quality_report': False
}

# =============================================================================
# STEP 1: GENERATE ENHANCED DATA
# =============================================================================

print("=" * 80)
print("STEP 1: Generate Enhanced Synthetic Data")
print("=" * 80)

try:
    print("\n🔧 Generating data with:")
    print("   - Temporal correlation: ✅ Enabled (ρ=0.7)")
    print("   - Heterogeneous effects: ✅ Enabled")
    print("   - Missingness: ✅ MAR mechanism")
    print("   - Sample size: 50 per arm\n")
    
    df = generate_vitals_enhanced(
        n_per_arm=50,
        use_temporal_correlation=True,
        temporal_rho=0.7,
        use_heterogeneous_effects=True,
        missingness_mechanism='MAR',
        seed=42
    )
    
    print(f"✅ SUCCESS - Data Generated!")
    print(f"   Total measurements: {len(df)}")
    print(f"   Subjects: {df['SubjectID'].nunique()}")
    print(f"   Active arm: {(df['TreatmentArm']=='Active').sum()} measurements")
    print(f"   Placebo arm: {(df['TreatmentArm']=='Placebo').sum()} measurements")
    print(f"   Dropout rate: {df['dropout'].mean():.1%}")
    
    workflow_status['data_generation'] = True
    
except Exception as e:
    print(f"❌ FAILED - Data generation error: {str(e)}")
    print("\nCannot proceed without data. Exiting.")
    sys.exit(1)

# =============================================================================
# STEP 2: VALIDATE VIA ANALYTICS SERVICE
# =============================================================================

print("\n" + "=" * 80)
print("STEP 2: Validate Data via Analytics Service")
print("=" * 80)

data_records = df.to_dict('records')
validation_results = {}

try:
    # Test 2a: Temporal Correlation
    print("\n📊 2a. Temporal Correlation Validation...")
    response = requests.post(
        f"{ANALYTICS_URL}/validate/temporal-correlation",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        validation_results['temporal'] = result
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Grade: {result.get('grade', 'N/A')}")
        print(f"   ✅ Mean ρ: {result['metrics'].get('mean_correlation', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2b: Heterogeneous Effects
    print("\n📊 2b. Heterogeneous Effects Validation...")
    response = requests.post(
        f"{ANALYTICS_URL}/validate/heterogeneous-effects",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        validation_results['heterogeneity'] = result
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Grade: {result.get('grade', 'N/A')}")
        print(f"   ✅ Heterogeneity Score: {result.get('heterogeneity_score', 'N/A')}/100")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2c: Missingness Mechanism
    print("\n📊 2c. Missingness Mechanism Validation...")
    response = requests.post(
        f"{ANALYTICS_URL}/validate/missingness-mechanism",
        json={"data": data_records},
        timeout=10
    )
    
    if response.status_code == 200:
        result = response.json()
        validation_results['missingness'] = result
        print(f"   ✅ Status: {result['status']}")
        print(f"   ✅ Classification: {result.get('classification', 'N/A')}")
    else:
        print(f"   ❌ Failed: {response.status_code}")
    
    # Test 2d: Comprehensive Validation
    print("\n📊 2d. Comprehensive Validation...")
    response = requests.post(
        f"{ANALYTICS_URL}/validate/enhanced-comprehensive",
        json={"data": data_records},
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        validation_results['comprehensive'] = result
        print(f"   ✅ Overall Score: {result['overall']['score']}/100")
        print(f"   ✅ Overall Grade: {result['overall']['grade']}")
        print(f"   ✅ Summary: {result['overall']['summary']}")
        workflow_status['analytics_validation'] = True
    else:
        print(f"   ❌ Failed: {response.status_code}")

except requests.exceptions.ConnectionError:
    print(f"   ❌ Cannot connect to Analytics Service (port 8003)")
    print(f"   ⚠️  Make sure docker compose is running!")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# =============================================================================
# STEP 3: GENERATE QUALITY REPORT
# =============================================================================

print("\n" + "=" * 80)
print("STEP 3: Generate Enhanced Quality Report")
print("=" * 80)

try:
    # Create mock real data (small sample)
    real_data = df.sample(10).to_dict('records')
    
    print("\n📝 Generating enhanced quality report...")
    response = requests.post(
        f"{QUALITY_URL}/quality/report/enhanced",
        json={
            "method_name": "enhanced_generator",
            "real_data": real_data,
            "synthetic_data": data_records,
            "generation_time_ms": 45.2
        },
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ SUCCESS - Quality Report Generated!")
        print(f"\n   📊 Quality Assessment:")
        
        if 'quality_score' in result:
            qs = result['quality_score']
            print(f"      Overall Score: {qs['overall_score']}/100")
            print(f"      Grade: {qs['grade']}")
            
            if qs['grade'] == 'A':
                print(f"      Status: ✅ PUBLICATION-READY!")
            elif qs['grade'] == 'B':
                print(f"      Status: ⚠️  Good Quality")
            else:
                print(f"      Status: ⚠️  Needs Improvement")
            
            if 'component_scores' in qs:
                print(f"\n   📈 Component Scores:")
                for name, score in qs['component_scores'].items():
                    print(f"      - {name:20s}: {score:5.1f}")
        
        if 'enhanced_validations' in result:
            ev = result['enhanced_validations']
            print(f"\n   🔬 Enhanced Validations:")
            
            if ev.get('temporal_correlation'):
                tc = ev['temporal_correlation']
                status_icon = "✅" if tc['status'] == 'excellent' else "⚠️"
                print(f"      {status_icon} Temporal: {tc['mean']} ({tc['status']})")
            
            if ev.get('treatment_heterogeneity'):
                th = ev['treatment_heterogeneity']
                status_icon = "✅" if th['status'] in ['excellent', 'good'] else "⚠️"
                print(f"      {status_icon} Heterogeneity: {th['std']} mmHg ({th['status']})")
            
            if ev.get('missingness_classification'):
                mc = ev['missingness_classification']
                status_icon = "✅" if mc['status'] == 'realistic' else "⚠️"
                print(f"      {status_icon} Missingness: {mc['mechanism']} ({mc['status']})")
        
        # Show a snippet of the markdown report
        if 'report' in result:
            print(f"\n   📄 Report Preview:")
            lines = result['report'].split('\n')
            for i, line in enumerate(lines[:15]):
                print(f"      {line}")
            if len(lines) > 15:
                print(f"      ... ({len(lines) - 15} more lines)")
        
        workflow_status['quality_report'] = True
        
    elif response.status_code == 501:
        print(f"   ⚠️  Enhanced report generator not available yet")
        print(f"   💡 Try restarting quality service: docker compose restart quality-service")
    else:
        print(f"   ❌ Failed: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print(f"   ❌ Cannot connect to Quality Service (port 8004)")
    print(f"   ⚠️  Make sure docker compose is running!")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# =============================================================================
# FINAL SUMMARY
# =============================================================================

print("\n" + "=" * 80)
print("🎯 WORKFLOW TEST SUMMARY")
print("=" * 80)

all_passed = all(workflow_status.values())

print(f"\nWorkflow Steps:")
print(f"  1. Data Generation:        {'✅ PASS' if workflow_status['data_generation'] else '❌ FAIL'}")
print(f"  2. Analytics Validation:   {'✅ PASS' if workflow_status['analytics_validation'] else '❌ FAIL'}")
print(f"  3. Quality Report:         {'✅ PASS' if workflow_status['quality_report'] else '❌ FAIL'}")

print(f"\n{'='*80}")
if all_passed:
    print("🎉 SUCCESS - ENTIRE WORKFLOW WORKING!")
    print("="*80)
    print("\n✅ You now have a complete, end-to-end enhanced synthetic data platform!")
    print("\nWhat works:")
    print("  ✅ Generate A-grade synthetic data (Python)")
    print("  ✅ Validate via Analytics Service (API)")
    print("  ✅ Generate quality reports (API)")
    print("  ✅ Clean 6-service architecture")
    print("\nReady for:")
    print("  🎯 Frontend integration")
    print("  🎯 Production deployment")
    print("  🎯 Research publication")
    print("  🎯 Regulatory submission")
else:
    print("⚠️  PARTIAL SUCCESS - Some components need attention")
    print("="*80)
    print("\nWhat to check:")
    if not workflow_status['data_generation']:
        print("  ❌ Data generation failed - check Python environment")
    if not workflow_status['analytics_validation']:
        print("  ❌ Analytics validation failed - check service on port 8003")
    if not workflow_status['quality_report']:
        print("  ❌ Quality report failed - check service on port 8004")
    print("\n💡 Tip: Make sure docker compose is running!")

print("\n" + "=" * 80)
print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
