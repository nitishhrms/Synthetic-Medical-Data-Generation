#!/usr/bin/env python3
"""
AACT Data Inspector - Quick exploration of downloaded AACT data

Run this FIRST to see what you have in your AACT download.

Usage:
    cd /path/to/Synthetic-Medical-Data-Generation
    python data/aact/scripts/01_inspect_aact.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

AACT_RAW_DIR = project_root / "data" / "aact" / "raw"


def inspect_aact_files():
    """Inspect what files exist in AACT raw directory"""

    print("=" * 80)
    print("🔍 AACT Data Inspector")
    print("=" * 80)

    if not AACT_RAW_DIR.exists():
        print(f"\n❌ ERROR: AACT raw directory not found at: {AACT_RAW_DIR}")
        print("\nExpected structure:")
        print("  data/aact/raw/")
        print("    ├── studies.txt")
        print("    ├── conditions.txt")
        print("    ├── baseline_measurements.txt")
        print("    └── ... (other AACT files)")
        print("\nPlease download AACT data and place .txt files in data/aact/raw/")
        return False

    # List all files
    txt_files = list(AACT_RAW_DIR.glob("*.txt"))

    if not txt_files:
        print(f"\n❌ ERROR: No .txt files found in {AACT_RAW_DIR}")
        print("\nDid you extract the AACT zip file?")
        return False

    print(f"\n✅ Found {len(txt_files)} AACT files in {AACT_RAW_DIR}")
    print("\n📋 Available Files:")
    print("-" * 80)

    total_size = 0
    key_files = {
        'studies.txt': 'Study metadata (phase, enrollment, dates)',
        'conditions.txt': 'Disease/indication mappings',
        'baseline_measurements.txt': '⭐ VITALS DATA - baseline measurements',
        'calculated_values.txt': 'Actual enrollment, dropout stats',
        'interventions.txt': 'Treatment descriptions',
        'outcomes.txt': 'Outcome measures',
        'eligibilities.txt': 'Inclusion/exclusion criteria',
        'sponsors.txt': 'Sponsor information'
    }

    for txt_file in sorted(txt_files):
        size_mb = txt_file.stat().st_size / (1024 * 1024)
        total_size += size_mb

        name = txt_file.name
        desc = key_files.get(name, "")

        if name in key_files:
            print(f"  ✓ {name:30} {size_mb:8.1f} MB  {desc}")
        else:
            print(f"    {name:30} {size_mb:8.1f} MB")

    print("-" * 80)
    print(f"  Total Size: {total_size:,.1f} MB ({total_size/1024:.2f} GB)")

    # Quick peek at key files
    print("\n" + "=" * 80)
    print("📊 Quick Preview of Key Files")
    print("=" * 80)

    key_file_previews = ['studies.txt', 'conditions.txt', 'baseline_measurements.txt']

    for filename in key_file_previews:
        filepath = AACT_RAW_DIR / filename
        if filepath.exists():
            print(f"\n📄 {filename} (first 3 lines):")
            print("-" * 80)
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f):
                    if i >= 3:
                        break
                    # Show first 200 chars of each line
                    print(f"  {line[:200].rstrip()}")

            # Count total lines
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            print(f"  → Total rows: {line_count:,}")

    print("\n" + "=" * 80)
    print("✨ Inspection Complete!")
    print("=" * 80)
    print("\nNext Steps:")
    print("  1. Run: python data/aact/scripts/02_process_aact.py")
    print("  2. This will create cached statistics from AACT data")
    print("  3. The cached files (~10-50MB) can be committed to git")

    return True


if __name__ == "__main__":
    success = inspect_aact_files()
    sys.exit(0 if success else 1)
