#!/usr/bin/env python3
"""
Validate and Repair Real CDISC Clinical Trial Data

This script applies validation checks and auto-repair functions to the real dataset,
not the synthetic data. It identifies and fixes data quality issues in the actual
clinical trial data.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List

# Add generators to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

# Validation rules (same as edit checks)
VALIDATION_RULES = {
    'SystolicBP': {
        'min': 95,
        'max': 200,
        'type': 'numeric',
        'unit': 'mmHg'
    },
    'DiastolicBP': {
        'min': 55,
        'max': 130,
        'type': 'numeric',
        'unit': 'mmHg'
    },
    'HeartRate': {
        'min': 50,
        'max': 120,
        'type': 'numeric',
        'unit': 'bpm'
    },
    'Temperature': {
        'min': 35.0,
        'max': 40.0,
        'type': 'numeric',
        'unit': '°C'
    }
}

def validate_real_data(df: pd.DataFrame) -> Dict:
    """
    Comprehensive validation of real clinical trial data

    Returns:
        Dictionary with validation results and identified issues
    """
    print("\n" + "="*80)
    print("VALIDATING REAL CLINICAL TRIAL DATA")
    print("="*80)

    issues = {
        'total_records': len(df),
        'issues_found': [],
        'severity': []
    }

    # 1. Check for missing values
    print("\n1. Checking for missing values...")
    missing = df.isnull().sum()
    for col, count in missing.items():
        if count > 0:
            pct = (count / len(df)) * 100
            issues['issues_found'].append({
                'type': 'missing_values',
                'field': col,
                'count': int(count),
                'percentage': f"{pct:.2f}%"
            })
            issues['severity'].append('HIGH' if pct > 5 else 'MEDIUM')
            print(f"   ⚠️  {col}: {count} missing values ({pct:.2f}%)")

    if missing.sum() == 0:
        print("   ✓ No missing values found")

    # 2. Check value ranges
    print("\n2. Checking value ranges...")
    for field, rules in VALIDATION_RULES.items():
        if field in df.columns:
            out_of_range = ~df[field].between(rules['min'], rules['max'])
            count = out_of_range.sum()
            if count > 0:
                pct = (count / len(df)) * 100
                issues['issues_found'].append({
                    'type': 'out_of_range',
                    'field': field,
                    'count': int(count),
                    'percentage': f"{pct:.2f}%",
                    'valid_range': f"[{rules['min']}, {rules['max']}] {rules['unit']}"
                })
                issues['severity'].append('HIGH')

                # Show examples
                invalid_values = df[out_of_range][field].head(5).tolist()
                print(f"   ⚠️  {field}: {count} values out of range ({pct:.2f}%)")
                print(f"      Valid range: [{rules['min']}, {rules['max']}] {rules['unit']}")
                print(f"      Examples: {invalid_values}")
            else:
                print(f"   ✓ {field}: All values in valid range")

    # 3. Check SBP > DBP differential
    print("\n3. Checking BP differential (SBP > DBP)...")
    if 'SystolicBP' in df.columns and 'DiastolicBP' in df.columns:
        invalid_diff = df['SystolicBP'] <= df['DiastolicBP']
        count = invalid_diff.sum()
        if count > 0:
            pct = (count / len(df)) * 100
            issues['issues_found'].append({
                'type': 'invalid_bp_differential',
                'count': int(count),
                'percentage': f"{pct:.2f}%"
            })
            issues['severity'].append('HIGH')
            print(f"   ⚠️  {count} records where SBP ≤ DBP ({pct:.2f}%)")
        else:
            print(f"   ✓ All records have SBP > DBP")

        # Check minimum differential (should be ≥5 mmHg)
        small_diff = (df['SystolicBP'] - df['DiastolicBP']) < 5
        count = small_diff.sum()
        if count > 0:
            pct = (count / len(df)) * 100
            issues['issues_found'].append({
                'type': 'small_bp_differential',
                'count': int(count),
                'percentage': f"{pct:.2f}%",
                'note': 'SBP-DBP differential < 5 mmHg'
            })
            issues['severity'].append('MEDIUM')
            print(f"   ⚠️  {count} records with BP differential < 5 mmHg ({pct:.2f}%)")

    # 4. Check for duplicate records
    print("\n4. Checking for duplicate records...")
    duplicates = df.duplicated(subset=['SubjectID', 'VisitName'])
    count = duplicates.sum()
    if count > 0:
        pct = (count / len(df)) * 100
        issues['issues_found'].append({
            'type': 'duplicate_records',
            'count': int(count),
            'percentage': f"{pct:.2f}%"
        })
        issues['severity'].append('MEDIUM')
        print(f"   ⚠️  {count} duplicate SubjectID+VisitName combinations ({pct:.2f}%)")
    else:
        print(f"   ✓ No duplicate records found")

    # 5. Check visit completeness
    print("\n5. Checking visit sequence completeness...")
    expected_visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']
    incomplete_subjects = []
    for subject in df['SubjectID'].unique():
        subject_visits = df[df['SubjectID'] == subject]['VisitName'].unique()
        if len(subject_visits) < len(expected_visits):
            missing = set(expected_visits) - set(subject_visits)
            incomplete_subjects.append({
                'subject': subject,
                'has_visits': len(subject_visits),
                'missing': list(missing)
            })

    if incomplete_subjects:
        count = len(incomplete_subjects)
        pct = (count / df['SubjectID'].nunique()) * 100
        issues['issues_found'].append({
            'type': 'incomplete_visit_sequence',
            'count': count,
            'percentage': f"{pct:.2f}%",
            'note': f'{count} subjects missing some visits'
        })
        issues['severity'].append('LOW')
        print(f"   ⚠️  {count} subjects with incomplete visit sequences ({pct:.2f}%)")
        print(f"      Examples: {incomplete_subjects[:3]}")
    else:
        print(f"   ✓ All subjects have complete visit sequences")

    # 6. Check treatment arm consistency
    print("\n6. Checking treatment arm consistency...")
    inconsistent_arms = []
    for subject in df['SubjectID'].unique():
        subject_arms = df[df['SubjectID'] == subject]['TreatmentArm'].unique()
        if len(subject_arms) > 1:
            inconsistent_arms.append({
                'subject': subject,
                'arms': list(subject_arms)
            })

    if inconsistent_arms:
        count = len(inconsistent_arms)
        pct = (count / df['SubjectID'].nunique()) * 100
        issues['issues_found'].append({
            'type': 'inconsistent_treatment_arm',
            'count': count,
            'percentage': f"{pct:.2f}%"
        })
        issues['severity'].append('CRITICAL')
        print(f"   🔴 CRITICAL: {count} subjects with multiple treatment arms ({pct:.2f}%)")
        print(f"      Examples: {inconsistent_arms[:3]}")
    else:
        print(f"   ✓ All subjects have consistent treatment arms")

    # 7. Check for extreme outliers (beyond 3 std devs)
    print("\n7. Checking for statistical outliers...")
    for field in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
        if field in df.columns:
            mean = df[field].mean()
            std = df[field].std()
            outliers = (df[field] < mean - 3*std) | (df[field] > mean + 3*std)
            count = outliers.sum()
            if count > 0:
                pct = (count / len(df)) * 100
                issues['issues_found'].append({
                    'type': 'statistical_outlier',
                    'field': field,
                    'count': int(count),
                    'percentage': f"{pct:.2f}%",
                    'note': 'Beyond 3 standard deviations'
                })
                issues['severity'].append('LOW')
                print(f"   ⚠️  {field}: {count} outliers ({pct:.2f}%)")

    # Summary
    print("\n" + "="*80)
    print("VALIDATION SUMMARY")
    print("="*80)
    print(f"Total records analyzed: {len(df):,}")
    print(f"Total issues found: {len(issues['issues_found'])}")

    if issues['issues_found']:
        critical = issues['severity'].count('CRITICAL')
        high = issues['severity'].count('HIGH')
        medium = issues['severity'].count('MEDIUM')
        low = issues['severity'].count('LOW')

        print(f"\nBy severity:")
        if critical > 0:
            print(f"  🔴 CRITICAL: {critical}")
        if high > 0:
            print(f"  ⚠️  HIGH:     {high}")
        if medium > 0:
            print(f"  ⚠️  MEDIUM:   {medium}")
        if low > 0:
            print(f"  ℹ️  LOW:      {low}")
    else:
        print("✅ No issues found - data is clean!")

    return issues

def repair_real_data(df: pd.DataFrame, issues: Dict) -> Tuple[pd.DataFrame, Dict]:
    """
    Auto-repair identified issues in real data

    Returns:
        Tuple of (repaired_dataframe, repair_report)
    """
    print("\n" + "="*80)
    print("AUTO-REPAIR REAL CLINICAL TRIAL DATA")
    print("="*80)

    df_repaired = df.copy()
    repairs = {
        'applied': [],
        'records_modified': 0
    }

    # 1. Handle out-of-range values
    print("\n1. Repairing out-of-range values...")
    for field, rules in VALIDATION_RULES.items():
        if field in df_repaired.columns:
            out_of_range = ~df_repaired[field].between(rules['min'], rules['max'])
            count = out_of_range.sum()

            if count > 0:
                # Clip values to valid range
                df_repaired[field] = df_repaired[field].clip(rules['min'], rules['max'])
                repairs['applied'].append({
                    'type': 'clip_to_range',
                    'field': field,
                    'count': int(count),
                    'action': f"Clipped to [{rules['min']}, {rules['max']}]"
                })
                repairs['records_modified'] += count
                print(f"   ✓ {field}: Clipped {count} values to valid range")

    # 2. Fix BP differential issues
    print("\n2. Repairing BP differential issues...")
    if 'SystolicBP' in df_repaired.columns and 'DiastolicBP' in df_repaired.columns:
        invalid_diff = df_repaired['SystolicBP'] <= df_repaired['DiastolicBP']
        count = invalid_diff.sum()

        if count > 0:
            # Swap if SBP <= DBP
            for idx in df_repaired[invalid_diff].index:
                sbp = df_repaired.loc[idx, 'SystolicBP']
                dbp = df_repaired.loc[idx, 'DiastolicBP']
                # Swap values
                df_repaired.loc[idx, 'SystolicBP'] = dbp
                df_repaired.loc[idx, 'DiastolicBP'] = sbp

            repairs['applied'].append({
                'type': 'swap_bp_values',
                'count': int(count),
                'action': 'Swapped SBP and DBP where SBP <= DBP'
            })
            repairs['records_modified'] += count
            print(f"   ✓ Swapped SBP/DBP for {count} records")

        # Ensure minimum differential of 5 mmHg
        small_diff = (df_repaired['SystolicBP'] - df_repaired['DiastolicBP']) < 5
        count = small_diff.sum()

        if count > 0:
            for idx in df_repaired[small_diff].index:
                # Adjust DBP to maintain 5 mmHg differential
                df_repaired.loc[idx, 'DiastolicBP'] = df_repaired.loc[idx, 'SystolicBP'] - 5
                # Re-clip to valid range
                df_repaired.loc[idx, 'DiastolicBP'] = np.clip(
                    df_repaired.loc[idx, 'DiastolicBP'],
                    55, 130
                )

            repairs['applied'].append({
                'type': 'adjust_bp_differential',
                'count': int(count),
                'action': 'Adjusted DBP to maintain minimum 5 mmHg differential'
            })
            repairs['records_modified'] += count
            print(f"   ✓ Adjusted BP differential for {count} records")

    # 3. Remove duplicate records
    print("\n3. Removing duplicate records...")
    duplicates = df_repaired.duplicated(subset=['SubjectID', 'VisitName'], keep='first')
    count = duplicates.sum()

    if count > 0:
        df_repaired = df_repaired[~duplicates].reset_index(drop=True)
        repairs['applied'].append({
            'type': 'remove_duplicates',
            'count': int(count),
            'action': 'Removed duplicate SubjectID+VisitName records (kept first)'
        })
        repairs['records_modified'] += count
        print(f"   ✓ Removed {count} duplicate records")

    # 4. Handle missing values (if any)
    print("\n4. Handling missing values...")
    missing_count = df_repaired.isnull().sum().sum()

    if missing_count > 0:
        # For numeric fields, use subject-specific median
        for field in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
            if field in df_repaired.columns and df_repaired[field].isnull().any():
                # Fill with subject-specific median
                df_repaired[field] = df_repaired.groupby('SubjectID')[field].transform(
                    lambda x: x.fillna(x.median())
                )
                # If still missing, use global median
                df_repaired[field].fillna(df_repaired[field].median(), inplace=True)

        repairs['applied'].append({
            'type': 'impute_missing',
            'count': int(missing_count),
            'action': 'Imputed using subject-specific median, then global median'
        })
        repairs['records_modified'] += missing_count
        print(f"   ✓ Imputed {missing_count} missing values")

    # 5. Fix treatment arm consistency
    print("\n5. Fixing treatment arm inconsistencies...")
    inconsistent_count = 0
    for subject in df_repaired['SubjectID'].unique():
        subject_mask = df_repaired['SubjectID'] == subject
        subject_arms = df_repaired[subject_mask]['TreatmentArm'].unique()

        if len(subject_arms) > 1:
            # Use most common arm for this subject
            most_common_arm = df_repaired[subject_mask]['TreatmentArm'].mode()[0]
            df_repaired.loc[subject_mask, 'TreatmentArm'] = most_common_arm
            inconsistent_count += 1

    if inconsistent_count > 0:
        repairs['applied'].append({
            'type': 'fix_treatment_arm',
            'count': inconsistent_count,
            'action': 'Set to most common arm for each subject'
        })
        repairs['records_modified'] += inconsistent_count
        print(f"   ✓ Fixed treatment arm for {inconsistent_count} subjects")

    # Summary
    print("\n" + "="*80)
    print("REPAIR SUMMARY")
    print("="*80)
    print(f"Total repair actions: {len(repairs['applied'])}")
    print(f"Total records modified: {repairs['records_modified']}")

    if repairs['applied']:
        print("\nRepairs applied:")
        for repair in repairs['applied']:
            print(f"  • {repair['type']}: {repair['count']} ({repair['action']})")

    return df_repaired, repairs

def compare_before_after(original_df: pd.DataFrame, repaired_df: pd.DataFrame):
    """Compare statistics before and after repair"""
    print("\n" + "="*80)
    print("BEFORE vs AFTER COMPARISON")
    print("="*80)

    print("\n📊 Record counts:")
    print(f"  Before: {len(original_df):,} records")
    print(f"  After:  {len(repaired_df):,} records")
    print(f"  Change: {len(repaired_df) - len(original_df):+,} records")

    print("\n📊 Data quality metrics:")

    # Missing values
    orig_missing = original_df.isnull().sum().sum()
    rep_missing = repaired_df.isnull().sum().sum()
    print(f"  Missing values:  {orig_missing} → {rep_missing}")

    # Out of range
    for field, rules in VALIDATION_RULES.items():
        if field in original_df.columns:
            orig_oor = (~original_df[field].between(rules['min'], rules['max'])).sum()
            rep_oor = (~repaired_df[field].between(rules['min'], rules['max'])).sum()
            if orig_oor > 0 or rep_oor > 0:
                print(f"  {field} out of range: {orig_oor} → {rep_oor}")

    # BP differential
    if 'SystolicBP' in original_df.columns and 'DiastolicBP' in original_df.columns:
        orig_bp = (original_df['SystolicBP'] <= original_df['DiastolicBP']).sum()
        rep_bp = (repaired_df['SystolicBP'] <= repaired_df['DiastolicBP']).sum()
        print(f"  Invalid BP differential: {orig_bp} → {rep_bp}")

    # Duplicates
    orig_dup = original_df.duplicated(subset=['SubjectID', 'VisitName']).sum()
    rep_dup = repaired_df.duplicated(subset=['SubjectID', 'VisitName']).sum()
    print(f"  Duplicate records: {orig_dup} → {rep_dup}")

    print("\n📊 Statistical comparison:")
    for field in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
        if field in original_df.columns:
            orig_mean = original_df[field].mean()
            rep_mean = repaired_df[field].mean()
            diff = ((rep_mean - orig_mean) / orig_mean) * 100
            print(f"  {field} mean: {orig_mean:.2f} → {rep_mean:.2f} ({diff:+.2f}%)")

def main():
    """Main validation and repair pipeline"""
    print("\n" + "="*80)
    print("REAL DATA VALIDATION AND REPAIR PIPELINE")
    print("="*80)

    # Load real data
    print("\n📂 Loading real CDISC clinical trial data...")
    data_path = Path(__file__).parent / 'pilot_trial.csv'

    if not data_path.exists():
        print(f"❌ Error: Data file not found at {data_path}")
        return

    original_df = pd.read_csv(data_path)
    print(f"✓ Loaded {len(original_df):,} records from {original_df['SubjectID'].nunique()} subjects")

    # Validate
    issues = validate_real_data(original_df)

    # Repair if issues found
    if issues['issues_found']:
        print("\n🔧 Issues detected. Applying auto-repair...")
        repaired_df, repairs = repair_real_data(original_df, issues)

        # Compare
        compare_before_after(original_df, repaired_df)

        # Re-validate
        print("\n🔍 Re-validating repaired data...")
        final_issues = validate_real_data(repaired_df)

        # Save repaired data
        output_path = Path(__file__).parent / 'pilot_trial_cleaned.csv'
        repaired_df.to_csv(output_path, index=False)
        print(f"\n💾 Saved cleaned data to: {output_path}")

        # Generate report
        report_path = Path(__file__).parent / 'data_validation_report.txt'
        with open(report_path, 'w') as f:
            f.write("DATA VALIDATION AND REPAIR REPORT\n")
            f.write("="*80 + "\n\n")
            f.write(f"Original records: {len(original_df):,}\n")
            f.write(f"Cleaned records: {len(repaired_df):,}\n")
            f.write(f"Issues found: {len(issues['issues_found'])}\n")
            f.write(f"Repairs applied: {len(repairs['applied'])}\n")
            f.write(f"\nOutput file: {output_path}\n")

        print(f"📄 Saved validation report to: {report_path}")

    else:
        print("\n✅ No issues found - data is already clean!")
        print("No repairs needed.")

    print("\n" + "="*80)
    print("VALIDATION AND REPAIR COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
