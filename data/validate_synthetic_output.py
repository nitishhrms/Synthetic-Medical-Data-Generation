"""
Validation check for synthetic data output (NO REPAIR)
Purpose: Verify generators are producing valid data
"""
import pandas as pd
import sys

def validate_synthetic_data(df: pd.DataFrame, dataset_name: str = "Synthetic") -> dict:
    """
    Validate synthetic data quality - CHECKS ONLY, NO REPAIRS
    
    If validation fails, this indicates the generator needs improvement,
    not that the data should be repaired.
    """
    results = {
        'dataset': dataset_name,
        'total_records': len(df),
        'passed': True,
        'issues': []
    }
    
    # Check 1: Missing values
    missing = df.isnull().sum().sum()
    if missing > 0:
        results['passed'] = False
        results['issues'].append(f"Missing values: {missing}")
    
    # Check 2: Value ranges
    range_checks = {
        'SystolicBP': (95, 200),
        'DiastolicBP': (55, 130),
        'HeartRate': (50, 120),
        'Temperature': (35.0, 40.0)
    }
    
    for field, (min_val, max_val) in range_checks.items():
        out_of_range = ~df[field].between(min_val, max_val)
        count = out_of_range.sum()
        if count > 0:
            results['passed'] = False
            bad_values = df.loc[out_of_range, field].tolist()[:5]  # Show first 5
            results['issues'].append(
                f"{field} out of range [{min_val}-{max_val}]: {count} values "
                f"(examples: {bad_values})"
            )
    
    # Check 3: BP differential (SBP > DBP)
    bp_invalid = df['SystolicBP'] <= df['DiastolicBP']
    if bp_invalid.any():
        results['passed'] = False
        results['issues'].append(f"SBP <= DBP: {bp_invalid.sum()} records")
    
    # Check 4: Required columns
    required_cols = ['SubjectID', 'VisitName', 'TreatmentArm', 
                     'SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        results['passed'] = False
        results['issues'].append(f"Missing columns: {missing_cols}")
    
    return results


def print_validation_report(results: dict):
    """Print validation results"""
    print(f"\n{'='*70}")
    print(f"SYNTHETIC DATA VALIDATION: {results['dataset']}")
    print(f"{'='*70}")
    print(f"Total records: {results['total_records']}")
    
    if results['passed']:
        print("\n✅ ALL CHECKS PASSED")
        print("Generator is producing valid synthetic data!")
    else:
        print("\n❌ VALIDATION FAILED")
        print("\nIssues found:")
        for i, issue in enumerate(results['issues'], 1):
            print(f"  {i}. {issue}")
        print("\n⚠️  ACTION REQUIRED:")
        print("   → Review generator constraints")
        print("   → DO NOT repair synthetic data")
        print("   → Fix the generator to prevent these issues")
    print("="*70)


if __name__ == "__main__":
    # Example usage
    sys.path.append('/Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/microservices/data-generation-service/src')
    from generators import generate_vitals_mvn, generate_vitals_bootstrap, load_pilot_vitals
    
    print("Testing validation on synthetic data outputs...")
    
    # Test MVN generator
    print("\n1. Testing MVN Generator...")
    synthetic_mvn = generate_vitals_mvn(n_per_arm=50)
    mvn_results = validate_synthetic_data(synthetic_mvn, "MVN Generator")
    print_validation_report(mvn_results)
    
    # Test Bootstrap generator
    print("\n2. Testing Bootstrap Generator...")
    real_data = load_pilot_vitals(use_cleaned=True)
    synthetic_boot = generate_vitals_bootstrap(real_data, n_per_arm=50)
    boot_results = validate_synthetic_data(synthetic_boot, "Bootstrap Generator")
    print_validation_report(boot_results)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    print(f"MVN Generator: {'✅ PASS' if mvn_results['passed'] else '❌ FAIL'}")
    print(f"Bootstrap Generator: {'✅ PASS' if boot_results['passed'] else '❌ FAIL'}")
    
    if mvn_results['passed'] and boot_results['passed']:
        print("\n✅ All generators producing valid synthetic data!")
        sys.exit(0)
    else:
        print("\n⚠️  Some generators need improvement")
        sys.exit(1)
