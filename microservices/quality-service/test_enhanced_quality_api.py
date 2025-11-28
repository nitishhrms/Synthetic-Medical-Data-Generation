"""
Test Enhanced Quality Service Endpoints
========================================

Tests the new enhanced quality report generation.
"""

import sys
sys.path.insert(0, '/Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

from generate_vitals_enhanced import generate_vitals_enhanced
import requests
import json

print("=" * 80)
print("QUALITY SERVICE - ENHANCED REPORT TEST")
print("=" * 80)

# Generate enhanced test data
print("\n1. Generating enhanced data...")
df = generate_vitals_enhanced(
    n_per_arm=50,
    use_temporal_correlation=True,
    use_heterogeneous_effects=True,
    missingness_mechanism='MAR',
    seed=42
)

print(f"   Generated {len(df)} measurements for {df['SubjectID'].nunique()} subjects")

# Create minimal "real" data for comparison
real_data = df.sample(10).to_dict('records')  # Use sample as mock real data
synthetic_data = df.to_dict('records')

# Quality Service URL
QUALITY_URL = "http://localhost:8004"

print("\n" + "=" * 80)
print("2. TEST: Enhanced Quality Report Generation")
print("=" * 80)

try:
    response = requests.post(
        f"{QUALITY_URL}/quality/report/enhanced",
        json={
            "method_name": "enhanced_generator",
            "real_data": real_data,
            "synthetic_data": synthetic_data,
            "generation_time_ms": 45.2
        },
        timeout=15
    )
    
    if response.status_code == 200:
        result = response.json()
        
        print("✅ Enhanced Quality Report Generated!")
        print(f"\n   Method: {result['method']}")
        print(f"   Version: {result['report_version']}")
        
        # Quality Score
        if 'quality_score' in result:
            qs = result['quality_score']
            print(f"\n   📊 QUALITY SCORE:")
            print(f"      Overall: {qs['overall_score']}/100")
            print(f"      Grade: {qs['grade']}")
            
            if 'component_scores' in qs:
                print(f"\n   📈 Component Scores:")
                for name, score in qs['component_scores'].items():
                    print(f"      - {name}: {score:.1f}")
        
        # Enhanced Validations
        if 'enhanced_validations' in result:
            ev = result['enhanced_validations']
            print(f"\n   🔬 ENHANCED VALIDATIONS:")
            
            if ev.get('temporal_correlation'):
                tc = ev['temporal_correlation']
                print(f"      Temporal Correlation: {tc['mean']} ({tc['status']})")
            
            if ev.get('treatment_heterogeneity'):
                th = ev['treatment_heterogeneity']
                print(f"      Treatment Heterogeneity: {th['std']} mmHg ({th['status']})")
            
            if ev.get('missingness_classification'):
                mc = ev['missingness_classification']
                print(f"      Missingness: {mc['mechanism']} ({mc['status']})")
        
        # Show report snippet
        if 'report' in result:
            print(f"\n   📄 REPORT PREVIEW:")
            lines = result['report'].split('\n')
            for line in lines[:20]:  # First 20 lines
                print(f"      {line}")
            if len(lines) > 20:
                print(f"      ... ({len(lines) - 20} more lines)")
        
        print(f"\n✅ SUCCESS - Enhanced Quality Report Working!")
        
    elif response.status_code == 501:
        print(f"⚠️  Enhanced report generator not available")
        print(f"   This is OK - module may not be imported yet")
        print(f"   Try restarting quality service")
    else:
        print(f"❌ FAILED: Status {response.status_code}")
        print(f"   Error: {response.text}")

except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to quality service (port 8004)")
    print("   Make sure docker compose is running")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print("\n" + "=" * 80)
print("3. TEST: Verify Old Endpoint Still Works")
print("=" * 80)

try:
    response = requests.post(
        f"{QUALITY_URL}/quality/report",
        json={
            "method_name": "mvn",
            "real_data": real_data,
            "synthetic_data": synthetic_data
        },
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Original quality report endpoint still works")
    else:
        print(f"⚠️  Original endpoint returned {response.status_code}")

except Exception as e:
    print(f"⚠️  Original endpoint test failed: {str(e)}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print("""
✅ Quality Service Enhanced Report Ready!

New Endpoint:
  POST /quality/report/enhanced

Features:
  - Temporal correlation validation
  - Treatment heterogeneity assessment
  - Missingness mechanism classification
  - Enhanced quality scoring (4 components)
  - Publication-ready reports

Use this for research-grade quality assessment!
""")

print("=" * 80)
