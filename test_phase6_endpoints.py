#!/usr/bin/env python3
"""
Test Phase 6 Benchmarking Endpoints
Tests the 3 new endpoints added in Phase 6
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'microservices/analytics-service/src'))

from benchmarking import (
    compare_generation_methods,
    aggregate_quality_scores,
    generate_recommendations
)

def test_compare_generation_methods():
    """Test method comparison endpoint"""
    print("\n" + "="*70)
    print("TEST 1: compare_generation_methods()")
    print("="*70)

    methods_data = {
        "mvn": {
            "records_per_second": 29000,
            "quality_score": 0.87,
            "aact_similarity": 0.91,
            "memory_mb": 45
        },
        "bootstrap": {
            "records_per_second": 140000,
            "quality_score": 0.92,
            "aact_similarity": 0.88,
            "memory_mb": 38
        },
        "rules": {
            "records_per_second": 80000,
            "quality_score": 0.79,
            "aact_similarity": 0.82,
            "memory_mb": 35
        },
        "llm": {
            "records_per_second": 70,
            "quality_score": 0.95,
            "aact_similarity": 0.94,
            "memory_mb": 120
        }
    }

    try:
        result = compare_generation_methods(methods_data)
        print("✅ SUCCESS - Method comparison completed")
        print(f"   - Methods compared: {len(result['method_comparison'])}")
        print(f"   - Ranking: {[r['method'] for r in result['ranking']]}")
        print(f"   - Fastest method: {result['recommendations'].get('for_speed', 'N/A')}")
        print(f"   - Best quality: {result['recommendations'].get('for_quality', 'N/A')}")
        return True
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_aggregate_quality_scores():
    """Test aggregate quality scores endpoint"""
    print("\n" + "="*70)
    print("TEST 2: aggregate_quality_scores()")
    print("="*70)

    try:
        result = aggregate_quality_scores(
            demographics_quality=0.89,
            vitals_quality=0.92,
            labs_quality=0.88,
            ae_quality=0.85,
            aact_similarity=0.91
        )
        print("✅ SUCCESS - Quality aggregation completed")
        print(f"   - Overall quality: {result['overall_quality']:.3f}")
        print(f"   - Quality grade: {result['interpretation']['grade']}")
        print(f"   - Quality status: {result['interpretation']['status']}")
        print(f"   - Completeness: {result['completeness']:.2f}")
        print(f"   - Recommendation: {result['interpretation']['recommendation'][:60]}...")
        return True
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_recommendations():
    """Test recommendations generation endpoint"""
    print("\n" + "="*70)
    print("TEST 3: generate_recommendations()")
    print("="*70)

    try:
        # Test with low quality
        result = generate_recommendations(
            current_quality=0.72,
            aact_similarity=0.65,
            generation_method="rules",
            n_subjects=50,
            indication="hypertension",
            phase="Phase 3"
        )
        print("✅ SUCCESS - Recommendations generated")
        print(f"   - Current quality: {result['current_status']['quality_score']:.3f}")
        print(f"   - Quality grade: {result['current_status']['quality_grade']}")
        print(f"   - Improvement opportunities: {len(result['improvement_opportunities'])}")
        if result['improvement_opportunities']:
            print(f"   - Top priority: {result['improvement_opportunities'][0]['priority']}")

        # Test with high quality
        result2 = generate_recommendations(
            current_quality=0.90,
            aact_similarity=0.88,
            generation_method="bootstrap",
            n_subjects=100,
            indication="diabetes",
            phase="Phase 3"
        )
        print(f"   - High quality test grade: {result2['current_status']['quality_grade']}")
        print(f"   - High quality opportunities: {len(result2['improvement_opportunities'])}")
        return True
    except Exception as e:
        print(f"❌ FAILED - {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("PHASE 6 BENCHMARKING ENDPOINTS TEST SUITE")
    print("="*70)

    tests = [
        test_compare_generation_methods,
        test_aggregate_quality_scores,
        test_generate_recommendations
    ]

    results = [test() for test in tests]

    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✅ ALL TESTS PASSED - Phase 6 endpoints are working correctly!")
        return 0
    else:
        print("\n❌ SOME TESTS FAILED - Review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
