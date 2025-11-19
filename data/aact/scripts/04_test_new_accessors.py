"""
Test script for the 5 new AACT data accessor methods added in v4.0

This script demonstrates how to use the new methods:
- get_demographics()
- get_treatment_arms()
- get_geographic_distribution()
- get_baseline_characteristics()
- get_disease_taxonomy()

Run this AFTER regenerating the cache with 03_process_aact_comprehensive.py
"""

import sys
from pathlib import Path

# Add the data-generation-service to Python path
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root / "microservices" / "data-generation-service" / "src"))

from aact_utils import (
    get_aact_loader,
    get_demographics,
    get_treatment_arms,
    get_geographic_distribution,
    get_baseline_characteristics,
    get_disease_taxonomy
)


def test_new_accessors():
    """Test all 5 new accessor methods"""

    print("=" * 80)
    print("Testing New AACT v4.0 Accessor Methods")
    print("=" * 80)

    # Initialize loader
    aact = get_aact_loader()

    # Get available indications
    indications = aact.get_available_indications()
    print(f"\n✓ Found {len(indications)} indications in cache")

    if not indications:
        print("\n⚠ WARNING: No indications found. Run 03_process_aact_comprehensive.py first!")
        return

    # Test with first available indication
    test_indication = indications[0]
    test_phase = "Phase 3"

    print(f"\n📊 Testing with: {test_indication} ({test_phase})")
    print("=" * 80)

    # 1. Demographics
    print("\n1️⃣  DEMOGRAPHICS (calculated_values.txt)")
    print("-" * 80)
    demo = get_demographics(test_indication, test_phase)
    if demo and 'age' in demo:
        print(f"  Age (median): {demo['age'].get('median_years', 'N/A')} years")
        print(f"  Age (mean): {demo['age'].get('mean_years', 'N/A')} years")
        print(f"  Studies: {demo['age'].get('n_studies', 0)}")

        if 'gender' in demo:
            print(f"\n  Gender distribution:")
            print(f"    - Male: {demo['gender'].get('male_percentage', 0):.1f}%")
            print(f"    - Female: {demo['gender'].get('female_percentage', 0):.1f}%")

        if 'actual_duration' in demo:
            print(f"\n  Actual duration (median): {demo['actual_duration'].get('median_months', 'N/A')} months")
    else:
        print("  ⚠ No demographics data (using defaults)")

    # 2. Treatment Arms
    print("\n2️⃣  TREATMENT ARMS (design_groups.txt)")
    print("-" * 80)
    arms = get_treatment_arms(test_indication, test_phase)
    if arms and 'arm_type_distribution' in arms:
        print("  Arm type distribution:")
        for arm_type, pct in arms['arm_type_distribution'].items():
            print(f"    - {arm_type}: {pct:.1%}")

        if 'common_arm_names' in arms:
            print(f"\n  Top 5 common arm names:")
            for i, arm in enumerate(arms['common_arm_names'][:5], 1):
                print(f"    {i}. {arm['name']} (n={arm['frequency']})")

        print(f"\n  Typical # arms: {arms.get('typical_n_arms', 'N/A')}")
        print(f"  Studies: {arms.get('n_studies', 0)}")
    else:
        print("  ⚠ No treatment arms data (using defaults)")

    # 3. Geographic Distribution
    print("\n3️⃣  GEOGRAPHIC DISTRIBUTION (countries.txt)")
    print("-" * 80)
    geo = get_geographic_distribution(test_indication, test_phase, top_n=10)
    if geo and len(geo) > 0:
        print("  Top 10 countries:")
        for i, country in enumerate(geo, 1):
            print(f"    {i}. {country['country']}: {country['percentage']:.1%}")
    else:
        print("  ⚠ No geographic data (using defaults)")

    # 4. Baseline Characteristics
    print("\n4️⃣  BASELINE CHARACTERISTICS (baseline_counts.txt)")
    print("-" * 80)
    baseline = get_baseline_characteristics(test_indication, test_phase, top_n=5)
    if baseline and len(baseline) > 0:
        print("  Top 5 baseline characteristics:")
        for char_name, distribution in list(baseline.items())[:5]:
            print(f"\n  {char_name}:")
            for classif, pct in distribution.items():
                print(f"    - {classif}: {pct:.1%}")
    else:
        print("  ⚠ No baseline characteristics data (using defaults)")

    # 5. Disease Taxonomy
    print("\n5️⃣  DISEASE TAXONOMY (browse_conditions.txt)")
    print("-" * 80)
    taxonomy = get_disease_taxonomy(test_indication, max_terms=10)
    if taxonomy and 'mesh_terms' in taxonomy:
        print(f"  MeSH terms ({taxonomy['term_count']} total, showing 10):")
        for i, term in enumerate(taxonomy['mesh_terms'][:10], 1):
            print(f"    {i}. {term}")
        print(f"\n  Studies: {taxonomy.get('n_studies', 0)}")
    else:
        print("  ⚠ No disease taxonomy data (using defaults)")

    print("\n" + "=" * 80)
    print("✅ Test Complete!")
    print("=" * 80)

    # Cache info
    print("\n📦 Cache Information:")
    info = aact.get_source_info()
    print(f"  Source: {info.get('source', 'unknown')}")
    print(f"  Generated: {info.get('generated_at', 'unknown')}")
    print(f"  Total studies: {info.get('total_studies', 0):,}")
    print(f"  Cache path: {info.get('cache_path', 'unknown')}")


if __name__ == "__main__":
    test_new_accessors()
