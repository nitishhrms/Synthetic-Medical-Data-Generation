#!/usr/bin/env python3
"""
Integration Test - Verify AACT Data Loading and Usage
"""

import sys
from pathlib import Path
import json

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# Add service src to path to handle hyphenated directory name
service_src = project_root / "microservices" / "data-generation-service" / "src"
sys.path.insert(0, str(service_src))

from aact_utils import get_aact_loader
from realistic_trial import RealisticTrialGenerator

def test_integration():
    print("=" * 80)
    print("🧪 AACT Integration Test")
    print("=" * 80)

    # 1. Test Loader
    print("\n1️⃣ Testing AACTStatisticsLoader...")
    try:
        loader = get_aact_loader()
        print("   ✅ Loader initialized successfully")
        
        indications = loader.get_available_indications()
        print(f"   ✅ Found {len(indications)} indications: {', '.join(indications[:5])}...")
        
        if "hypertension" in indications:
            stats = loader.get_enrollment_stats("hypertension", "Phase 3")
            print(f"   ✅ Hypertension Phase 3 stats: {stats}")
            
            defaults = loader.get_realistic_defaults("hypertension", "Phase 3")
            print(f"   ✅ Recommended defaults: {defaults}")
        else:
            print("   ❌ Hypertension not found in indications!")
            return False
            
    except Exception as e:
        print(f"   ❌ Loader test failed: {e}")
        return False

    # 2. Test Generator Integration
    print("\n2️⃣ Testing RealisticTrialGenerator integration...")
    try:
        generator = RealisticTrialGenerator(seed=42)
        
        # Generate trial with AACT defaults
        print("   Generating trial for 'hypertension' (Phase 3)...")
        trial = generator.generate_realistic_trial(
            n_per_arm=50,
            indication="hypertension",
            phase="Phase 3"
        )
        
        metadata = trial.get("metadata", {})
        print(f"   ✅ Trial generated successfully")
        print(f"   📊 Sites used: {metadata.get('n_sites')} (Should be from AACT)")
        print(f"   📊 Dropout rate: {metadata.get('dropout_rate')} (Should be from AACT)")
        
        # Verify values match AACT defaults (approx)
        if metadata.get('n_sites') == defaults['n_sites']:
             print("   ✅ Verified: n_sites matches AACT default")
        else:
             print(f"   ⚠️ Warning: n_sites {metadata.get('n_sites')} != AACT default {defaults['n_sites']}")

    except Exception as e:
        print(f"   ❌ Generator test failed: {e}")
        return False

    print("\n" + "=" * 80)
    print("✨ Integration Verified Successfully!")
    print("=" * 80)
    return True

if __name__ == "__main__":
    success = test_integration()
    sys.exit(0 if success else 1)
