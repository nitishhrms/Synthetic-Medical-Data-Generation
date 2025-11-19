#!/usr/bin/env python3
"""
AACT Data Processor - Extract statistics and patterns using Daft

This script processes the raw AACT data (15GB) and creates small cached files
that can be committed to git and used by the data generation service.

Usage:
    cd /path/to/Synthetic-Medical-Data-Generation
    python data/aact/scripts/02_process_aact.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

AACT_RAW_DIR = project_root / "data" / "aact" / "raw"
AACT_PROCESSED_DIR = project_root / "data" / "aact" / "processed"

# Ensure processed directory exists
AACT_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def process_with_daft():
    """Process AACT data using Daft to extract key statistics"""

    print("=" * 80)
    print("🚀 AACT Data Processor (Using Daft)")
    print("=" * 80)

    # Check if Daft is installed
    try:
        import daft
        print("\n✅ Daft is installed")
    except ImportError:
        print("\n❌ Daft not installed!")
        print("Install with: pip install getdaft")
        return False

    import pandas as pd
    import numpy as np

    # Verify raw data exists
    studies_path = AACT_RAW_DIR / "studies.txt"
    conditions_path = AACT_RAW_DIR / "conditions.txt"

    if not studies_path.exists():
        print(f"\n❌ ERROR: studies.txt not found at {AACT_RAW_DIR}")
        print("Run: python data/aact/scripts/01_inspect_aact.py first")
        return False

    print(f"\n📂 Reading AACT data from: {AACT_RAW_DIR}")

    # Step 1: Load studies data with Daft
    print("\n1️⃣ Loading studies.txt with Daft...")
    try:
        studies_df = daft.read_csv(
            str(studies_path),
            delimiter="|",
            has_headers=True
        )
        print(f"   ✅ Loaded studies data")
    except Exception as e:
        print(f"   ❌ Error loading studies: {e}")
        print("\n   Falling back to pandas...")
        studies_df = pd.read_csv(studies_path, delimiter="|", low_memory=False)
        print(f"   ✅ Loaded {len(studies_df):,} studies with pandas")

    # Step 2: Load conditions data
    print("\n2️⃣ Loading conditions.txt...")
    try:
        if conditions_path.exists():
            conditions_df = daft.read_csv(
                str(conditions_path),
                delimiter="|",
                has_headers=True
            )
            print(f"   ✅ Loaded conditions data")
        else:
            print(f"   ⚠️ conditions.txt not found, skipping")
            conditions_df = None
    except Exception as e:
        print(f"   ❌ Error loading conditions: {e}")
        print("   Continuing without conditions data...")
        conditions_df = None

    # Convert to pandas for easier processing (Daft → pandas is fast)
    print("\n3️⃣ Converting to pandas for analysis...")
    if hasattr(studies_df, 'to_pandas'):
        studies_pd = studies_df.to_pandas()
    else:
        studies_pd = studies_df

    print(f"   ✅ Loaded {len(studies_pd):,} studies")

    if conditions_df is not None:
        if hasattr(conditions_df, 'to_pandas'):
            conditions_pd = conditions_df.to_pandas()
        else:
            conditions_pd = pd.read_csv(conditions_path, delimiter="|", low_memory=False)
        print(f"   ✅ Loaded {len(conditions_pd):,} condition records")
    else:
        conditions_pd = pd.DataFrame()

    # Step 3: Extract key statistics
    print("\n4️⃣ Extracting statistics by indication and phase...")

    statistics = {
        "generated_at": datetime.now().isoformat(),
        "source": "AACT ClinicalTrials.gov",
        "total_studies": int(len(studies_pd)),
        "indications": {}
    }

    # Get phase distribution
    if 'phase' in studies_pd.columns:
        phase_dist = studies_pd['phase'].value_counts().to_dict()
        statistics["phase_distribution"] = {str(k): int(v) for k, v in phase_dist.items()}

    # Get enrollment statistics
    if 'enrollment' in studies_pd.columns:
        enrollment_col = studies_pd['enrollment'].dropna()
        statistics["overall_enrollment"] = {
            "mean": float(enrollment_col.mean()) if len(enrollment_col) > 0 else 0,
            "median": float(enrollment_col.median()) if len(enrollment_col) > 0 else 0,
            "std": float(enrollment_col.std()) if len(enrollment_col) > 0 else 0,
            "min": float(enrollment_col.min()) if len(enrollment_col) > 0 else 0,
            "max": float(enrollment_col.max()) if len(enrollment_col) > 0 else 0
        }

    # Process by indication
    if len(conditions_pd) > 0 and 'downcase_name' in conditions_pd.columns:
        print("\n   Processing key indications...")

        # Join studies with conditions
        if 'nct_id' in studies_pd.columns and 'nct_id' in conditions_pd.columns:
            joined = studies_pd.merge(conditions_pd, on='nct_id', how='inner')
            print(f"   ✅ Joined {len(joined):,} study-condition pairs")

            # Extract statistics for key indications
            key_indications = [
                'hypertension', 'diabetes', 'cancer', 'oncology',
                'cardiovascular', 'heart failure', 'asthma', 'copd'
            ]

            for indication in key_indications:
                indication_data = joined[
                    joined['downcase_name'].str.contains(indication, case=False, na=False)
                ]

                if len(indication_data) > 0:
                    stats_by_phase = {}

                    if 'phase' in indication_data.columns:
                        for phase in ['Phase 1', 'Phase 2', 'Phase 3', 'Phase 4']:
                            phase_data = indication_data[indication_data['phase'] == phase]

                            if len(phase_data) > 0 and 'enrollment' in phase_data.columns:
                                enrollment = phase_data['enrollment'].dropna()

                                if len(enrollment) > 0:
                                    stats_by_phase[phase] = {
                                        "n_trials": int(len(phase_data)),
                                        "enrollment": {
                                            "mean": float(enrollment.mean()),
                                            "median": float(enrollment.median()),
                                            "std": float(enrollment.std()),
                                            "q25": float(enrollment.quantile(0.25)),
                                            "q75": float(enrollment.quantile(0.75))
                                        }
                                    }

                    if stats_by_phase:
                        statistics["indications"][indication] = {
                            "total_trials": int(len(indication_data)),
                            "by_phase": stats_by_phase
                        }
                        print(f"      ✓ {indication}: {len(indication_data):,} trials")

    # Step 4: Save statistics cache
    print("\n5️⃣ Saving cached statistics...")
    cache_path = AACT_PROCESSED_DIR / "aact_statistics_cache.json"

    with open(cache_path, 'w') as f:
        json.dump(statistics, f, indent=2)

    file_size = cache_path.stat().st_size / 1024
    print(f"   ✅ Saved to: {cache_path}")
    print(f"   📊 File size: {file_size:.1f} KB")

    # Step 5: Create quick reference guide
    print("\n6️⃣ Creating reference guide...")
    reference = {
        "description": "AACT Statistics Cache - Industry benchmarks from ClinicalTrials.gov",
        "generated_at": statistics["generated_at"],
        "total_studies": statistics["total_studies"],
        "available_indications": list(statistics["indications"].keys()),
        "usage": {
            "python": "with open('data/aact/processed/aact_statistics_cache.json') as f: stats = json.load(f)",
            "example": "stats['indications']['hypertension']['by_phase']['Phase 3']['enrollment']['median']"
        }
    }

    reference_path = AACT_PROCESSED_DIR / "README.json"
    with open(reference_path, 'w') as f:
        json.dump(reference, f, indent=2)

    print(f"   ✅ Saved reference to: {reference_path}")

    # Summary
    print("\n" + "=" * 80)
    print("✨ Processing Complete!")
    print("=" * 80)
    print(f"\n📊 Generated Files (can be committed to git):")
    print(f"   • {cache_path.name} ({file_size:.1f} KB)")
    print(f"   • {reference_path.name}")
    print(f"\n📈 Statistics Summary:")
    print(f"   • Total studies processed: {statistics['total_studies']:,}")
    print(f"   • Indications with data: {len(statistics['indications'])}")
    if statistics['indications']:
        print(f"   • Available indications:")
        for indication in statistics['indications'].keys():
            n_trials = statistics['indications'][indication]['total_trials']
            print(f"      - {indication}: {n_trials:,} trials")

    print("\n✅ Next Steps:")
    print("   1. Commit processed files: git add data/aact/processed/")
    print("   2. Services will now use AACT statistics instead of pilot data")
    print("   3. Run: python data/aact/scripts/03_test_integration.py to verify")

    return True


if __name__ == "__main__":
    success = process_with_daft()
    sys.exit(0 if success else 1)
