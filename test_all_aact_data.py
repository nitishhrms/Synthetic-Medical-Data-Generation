#!/usr/bin/env python3
"""
Test script to verify all AACT indications and phases work correctly
"""

import sys
from pathlib import Path

# Add data-generation-service src to path
sys.path.insert(0, str(Path(__file__).parent / "microservices" / "data-generation-service" / "src"))

from aact_utils import get_aact_loader

def test_all_indications():
    """Test all indications and phases"""
    aact = get_aact_loader()

    print("=" * 80)
    print("Testing All AACT Indications and Phases")
    print("=" * 80)

    indications = aact.get_available_indications()
    print(f"\nFound {len(indications)} indications: {indications}")

    all_passed = True
    total_tests = 0
    passed_tests = 0

    for indication in indications:
        print(f"\n{'=' * 80}")
        print(f"Testing: {indication.upper()}")
        print(f"{'=' * 80}")

        # Get phase distribution
        phase_dist = aact.get_phase_distribution(indication)
        print(f"\nPhases available: {list(phase_dist.keys())}")

        for phase in phase_dist.keys():
            print(f"\n  Testing {phase}...")
            total_tests += 1
            phase_passed = True

            try:
                # Test enrollment stats
                enrollment = aact.get_enrollment_stats(indication, phase)
                if enrollment['median'] == 0:
                    print(f"    WARNING: Enrollment median is 0")
                    phase_passed = False
                else:
                    print(f"    OK: Enrollment median = {enrollment['median']:.0f}")

                # Test demographics
                demographics = aact.get_demographics(indication, phase)
                if 'age' not in demographics:
                    print(f"    ERROR: Missing age in demographics")
                    phase_passed = False
                elif demographics['age']['n_studies'] == 0:
                    print(f"    WARNING: Demographics has 0 studies")
                else:
                    print(f"    OK: Demographics age median = {demographics['age']['median_years']:.0f} years")

                # Test baseline vitals
                vitals = aact.get_baseline_vitals(indication, phase)
                if 'systolic' in vitals and vitals['systolic'].get('n_measurements', 0) > 0:
                    print(f"    OK: Baseline vitals available ({vitals['systolic']['n_measurements']} measurements)")
                else:
                    print(f"    INFO: Using default vitals (no AACT data)")

                # Test baseline characteristics
                baseline_chars = aact.get_baseline_characteristics(indication, phase)
                if baseline_chars and len(baseline_chars) > 0:
                    print(f"    OK: Baseline characteristics ({len(baseline_chars)} categories)")
                else:
                    print(f"    ERROR: Missing baseline characteristics")
                    phase_passed = False

                # Test dropout patterns
                dropout = aact.get_dropout_patterns(indication, phase)
                if dropout['dropout_rate'] > 0:
                    print(f"    OK: Dropout rate = {dropout['dropout_rate']:.1%}")
                else:
                    print(f"    INFO: Using default dropout rate")

                # Test adverse events
                aes = aact.get_adverse_events(indication, phase, top_n=5)
                if aes and len(aes) > 0 and aes[0].get('n_trials', 0) > 0:
                    print(f"    OK: Adverse events ({len(aes)} events from real data)")
                else:
                    print(f"    INFO: Using default AEs (no AACT data)")

                # Test realistic defaults (integrates all above)
                defaults = aact.get_realistic_defaults(indication, phase)
                print(f"    OK: Realistic defaults - N={defaults['target_enrollment']}, "
                      f"dropout={defaults['dropout_rate']:.1%}, sites={defaults['n_sites']}")

                if phase_passed:
                    passed_tests += 1
                    print(f"    PASSED")
                else:
                    print(f"    FAILED")
                    all_passed = False

            except Exception as e:
                print(f"    ERROR: {e}")
                all_passed = False

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")

    if all_passed:
        print("\nALL TESTS PASSED!")
        return True
    else:
        print("\nSOME TESTS FAILED - See details above")
        return False


if __name__ == "__main__":
    success = test_all_indications()
    sys.exit(0 if success else 1)
