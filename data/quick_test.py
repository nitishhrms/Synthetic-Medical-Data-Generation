#!/usr/bin/env python3
"""Quick test to verify generators.py is working"""
import sys
from pathlib import Path

# Add generators to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

print("Testing generators.py...\n")

# Test 1: Import the module
try:
    from generators import (
        load_pilot_vitals,
        generate_vitals_mvn,
        generate_vitals_bootstrap,
        generate_vitals_rules
    )
    print("✓ Successfully imported all generator functions")
except Exception as e:
    print(f"✗ Import failed: {e}")
    exit(1)

# Test 2: Load real data
try:
    pilot_df = load_pilot_vitals()
    print(f"✓ Loaded {len(pilot_df)} real clinical trial records from {pilot_df['SubjectID'].nunique()} subjects")
except Exception as e:
    print(f"✗ Failed to load pilot data: {e}")
    exit(1)

# Test 3: Generate with MVN (10 subjects only for speed)
try:
    mvn_df = generate_vitals_mvn(n_per_arm=5, seed=123)
    print(f"✓ MVN generator created {len(mvn_df)} records")
    print(f"  Columns: {list(mvn_df.columns)}")
except Exception as e:
    print(f"✗ MVN generation failed: {e}")
    exit(1)

# Test 4: Generate with Bootstrap (10 subjects only for speed)
try:
    bootstrap_df = generate_vitals_bootstrap(pilot_df, n_per_arm=5, seed=42)
    print(f"✓ Bootstrap generator created {len(bootstrap_df)} records")
except Exception as e:
    print(f"✗ Bootstrap generation failed: {e}")
    exit(1)

# Test 5: Generate with Rules (baseline method)
try:
    rules_df = generate_vitals_rules(n_per_arm=5, seed=42)
    print(f"✓ Rules generator created {len(rules_df)} records")
except Exception as e:
    print(f"✗ Rules generation failed: {e}")
    exit(1)

print("\n" + "="*60)
print("All tests passed! generators.py is working correctly.")
print("="*60)
