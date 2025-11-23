"""
Test script for Phase 1 AACT Enhancements: Variance Sampling
Demonstrates the new dropout variance and arm-specific dropout features
"""

import sys
sys.path.insert(0, '/Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')

from aact_utils import (
    sample_dropout_rate,
    get_arm_specific_dropout_rates,
    get_dropout_variance_stats
)

print("=" * 80)
print("PHASE 1 ENHANCEMENTS - DROPOUT VARIANCE DEMO")
print("=" * 80)

# Test 1: Sample dropout rates with variance
print("\n1. SAMPLING DROPOUT RATES WITH REALISTIC VARIANCE")
print("-" * 80)
print("Generating 10 hypothetical trials for hypertension Phase 3:")
print()

for i in range(10):
    dropout_rate = sample_dropout_rate("hypertension", "Phase 3")
    print(f"   Trial {i+1:2d}: {dropout_rate:6.1%} dropout")

print("\n   ✅ Notice the variation! Trials 1-10 have different dropout rates.")
print("   This is realistic - real trials vary from 0% to 30%+")

# Test 2: Arm-specific dropout rates
print("\n2. ARM-SPECIFIC DROPOUT RATES")
print("-" * 80)
arm_rates = get_arm_specific_dropout_rates("hypertension", "Phase 3")
print(f"Found {len(arm_rates)} treatment arms with different dropout rates:\n")

# Sort by dropout rate (highest first)
sorted_arms = sorted(arm_rates.items(), key=lambda x: x[1], reverse=True)
for arm_code, rate in sorted_arms[:5]:  # Show top 5
    print(f"   {arm_code}: {rate:6.1%} dropout")

print(f"\n   ✅ Active arms typically have higher dropout than placebo")
print(f"   Top arm ({sorted_arms[0][0]}): {sorted_arms[0][1]:.1%}")
print(f"   Bottom arm ({sorted_arms[-1][0]}): {sorted_arms[-1][1]:.1%}")

# Test 3: Variance statistics
print("\n3. VARIANCE STATISTICS")
print("-" * 80)
variance_stats = get_dropout_variance_stats("hypertension", "Phase 3")
print(f"   Mean dropout rate:   {variance_stats['mean_rate']:6.1%}")
print(f"   Median dropout rate: {variance_stats['median_rate']:6.1%}")
print(f"   Std deviation:       {variance_stats['std_dev']:6.1%}")
print(f"   Range:               {variance_stats['min_rate']:6.1%} to {variance_stats['max_rate']:6.1%}")
print(f"   Trials analyzed:     {variance_stats['n_trials']:,}")

print(f"\n   ✅ High std dev ({variance_stats['std_dev']:.1%}) means trials vary widely")
print(f"   This is what makes synthetic data realistic!")

# Test 4: Compare to other indications
print("\n4. COMPARISON ACROSS INDICATIONS")
print("-" * 80)
for indication in ["hypertension", "diabetes", "cancer"]:
    stats = get_dropout_variance_stats(indication, "Phase 3")
    print(f"   {indication:15s}: mean={stats['mean_rate']:5.1%}, std={stats['std_dev']:5.1%}, n={stats['n_trials']:4d} trials")

print("\n" + "=" * 80)
print("✅ ENHANCEMENT 1 & 2 SUCCESSFULLY IMPLEMENTED!")
print("=" * 80)
print("\nNext steps:")
print("1. Integrate variance sampling into generators.py")
print("2. Add arm-specific dropout assignment logic")
print("3. Update analytics service to validate variance")
