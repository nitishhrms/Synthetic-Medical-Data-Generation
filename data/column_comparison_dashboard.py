#!/usr/bin/env python3
"""
Column/Field-Level Comparison Dashboard
Detailed analysis of each field between real and synthetic data
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

# Add generators to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

def analyze_column_statistics(df, source_name):
    """Analyze each column's statistics"""
    stats = []

    for col in df.columns:
        if col in ['SubjectID', 'VisitName', 'TreatmentArm', 'Source']:
            # Categorical columns
            stat = {
                'Column': col,
                'Source': source_name,
                'Type': 'Categorical',
                'Unique Values': df[col].nunique(),
                'Missing Count': df[col].isnull().sum(),
                'Missing %': f"{df[col].isnull().sum() / len(df) * 100:.2f}%",
                'Most Common': df[col].mode()[0] if len(df[col].mode()) > 0 else 'N/A',
                'Most Common %': f"{df[col].value_counts().iloc[0] / len(df) * 100:.1f}%" if len(df) > 0 else 'N/A'
            }
        else:
            # Numeric columns
            stat = {
                'Column': col,
                'Source': source_name,
                'Type': 'Numeric',
                'Mean': f"{df[col].mean():.2f}",
                'Median': f"{df[col].median():.2f}",
                'Std Dev': f"{df[col].std():.2f}",
                'Min': f"{df[col].min():.2f}",
                'Max': f"{df[col].max():.2f}",
                'Missing Count': df[col].isnull().sum(),
                'Missing %': f"{df[col].isnull().sum() / len(df) * 100:.2f}%"
            }

        stats.append(stat)

    return pd.DataFrame(stats)

def compare_field_distributions(real_df, synthetic_df, field):
    """Compare distribution of a specific field"""
    fig = go.Figure()

    # Real data
    fig.add_trace(go.Histogram(
        x=real_df[field],
        name='Real Data',
        opacity=0.6,
        marker_color='#1f77b4',
        nbinsx=30
    ))

    # Synthetic data
    fig.add_trace(go.Histogram(
        x=synthetic_df[field],
        name='Synthetic Data',
        opacity=0.6,
        marker_color='#ff7f0e',
        nbinsx=30
    ))

    fig.update_layout(
        title=f'{field} Distribution Comparison',
        xaxis_title=field,
        yaxis_title='Count',
        barmode='overlay',
        height=400
    )

    return fig

def create_field_comparison_table(real_df, mvn_df, bootstrap_df):
    """Create comprehensive field comparison table"""

    fields = ['SubjectID', 'VisitName', 'TreatmentArm', 'SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

    comparison = []

    for field in fields:
        row = {'Field': field}

        if field in ['SubjectID', 'VisitName', 'TreatmentArm']:
            # Categorical fields
            row['Field Type'] = 'Categorical'
            row['Real Unique'] = real_df[field].nunique()
            row['MVN Unique'] = mvn_df[field].nunique()
            row['Bootstrap Unique'] = bootstrap_df[field].nunique()
            row['Real Most Common'] = real_df[field].mode()[0]
            row['MVN Most Common'] = mvn_df[field].mode()[0]
            row['Bootstrap Most Common'] = bootstrap_df[field].mode()[0]
        else:
            # Numeric fields
            row['Field Type'] = 'Numeric'
            row['Real Mean'] = f"{real_df[field].mean():.2f}"
            row['MVN Mean'] = f"{mvn_df[field].mean():.2f}"
            row['Bootstrap Mean'] = f"{bootstrap_df[field].mean():.2f}"
            row['Real Std'] = f"{real_df[field].std():.2f}"
            row['MVN Std'] = f"{mvn_df[field].std():.2f}"
            row['Bootstrap Std'] = f"{bootstrap_df[field].std():.2f}"
            row['Real Range'] = f"[{real_df[field].min():.0f}, {real_df[field].max():.0f}]"
            row['MVN Range'] = f"[{mvn_df[field].min():.0f}, {mvn_df[field].max():.0f}]"
            row['Bootstrap Range'] = f"[{bootstrap_df[field].min():.0f}, {bootstrap_df[field].max():.0f}]"

        comparison.append(row)

    return pd.DataFrame(comparison)

def create_data_completeness_chart(real_df, mvn_df, bootstrap_df):
    """Create data completeness visualization"""

    fields = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

    completeness = {
        'Field': [],
        'Real Data': [],
        'MVN Synthetic': [],
        'Bootstrap Synthetic': []
    }

    for field in fields:
        completeness['Field'].append(field)
        completeness['Real Data'].append(100 - (real_df[field].isnull().sum() / len(real_df) * 100))
        completeness['MVN Synthetic'].append(100 - (mvn_df[field].isnull().sum() / len(mvn_df) * 100))
        completeness['Bootstrap Synthetic'].append(100 - (bootstrap_df[field].isnull().sum() / len(bootstrap_df) * 100))

    df = pd.DataFrame(completeness)

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Real Data',
        x=df['Field'],
        y=df['Real Data'],
        marker_color='#1f77b4'
    ))

    fig.add_trace(go.Bar(
        name='MVN Synthetic',
        x=df['Field'],
        y=df['MVN Synthetic'],
        marker_color='#ff7f0e'
    ))

    fig.add_trace(go.Bar(
        name='Bootstrap Synthetic',
        x=df['Field'],
        y=df['Bootstrap Synthetic'],
        marker_color='#2ca02c'
    ))

    fig.update_layout(
        title='Data Completeness by Field (%)',
        xaxis_title='Field',
        yaxis_title='Completeness %',
        yaxis=dict(range=[0, 105]),
        barmode='group',
        height=500
    )

    return fig

def create_value_range_comparison(real_df, mvn_df, bootstrap_df):
    """Create value range comparison visualization"""

    fields = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=fields
    )

    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]

    for field, (row, col) in zip(fields, positions):
        # Real data range
        fig.add_trace(
            go.Box(
                y=real_df[field],
                name='Real',
                marker_color='#1f77b4',
                legendgroup='Real',
                showlegend=(row==1 and col==1)
            ),
            row=row, col=col
        )

        # MVN data range
        fig.add_trace(
            go.Box(
                y=mvn_df[field],
                name='MVN',
                marker_color='#ff7f0e',
                legendgroup='MVN',
                showlegend=(row==1 and col==1)
            ),
            row=row, col=col
        )

        # Bootstrap data range
        fig.add_trace(
            go.Box(
                y=bootstrap_df[field],
                name='Bootstrap',
                marker_color='#2ca02c',
                legendgroup='Bootstrap',
                showlegend=(row==1 and col==1)
            ),
            row=row, col=col
        )

    fig.update_layout(
        title_text="Value Range Comparison Across All Fields",
        height=700,
        showlegend=True
    )

    return fig

def create_categorical_field_comparison(real_df, mvn_df, bootstrap_df):
    """Compare categorical fields"""

    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=('Subject Count', 'Visit Distribution', 'Treatment Arm Balance'),
        specs=[[{'type': 'bar'}, {'type': 'bar'}, {'type': 'bar'}]]
    )

    # Subject count comparison
    subjects = {
        'Data Source': ['Real', 'MVN', 'Bootstrap'],
        'Count': [
            real_df['SubjectID'].nunique(),
            mvn_df['SubjectID'].nunique(),
            bootstrap_df['SubjectID'].nunique()
        ]
    }

    fig.add_trace(
        go.Bar(x=subjects['Data Source'], y=subjects['Count'],
               marker_color=['#1f77b4', '#ff7f0e', '#2ca02c'],
               showlegend=False),
        row=1, col=1
    )

    # Visit distribution
    visits = ['Screening', 'Day 1', 'Week 4', 'Week 12']
    for i, (df, color, name) in enumerate([
        (real_df, '#1f77b4', 'Real'),
        (mvn_df, '#ff7f0e', 'MVN'),
        (bootstrap_df, '#2ca02c', 'Bootstrap')
    ]):
        visit_counts = [len(df[df['VisitName'] == v]) for v in visits]
        fig.add_trace(
            go.Bar(x=visits, y=visit_counts, name=name,
                   marker_color=color, legendgroup=name,
                   showlegend=True),
            row=1, col=2
        )

    # Treatment arm balance
    for df, color, name in [
        (real_df, '#1f77b4', 'Real'),
        (mvn_df, '#ff7f0e', 'MVN'),
        (bootstrap_df, '#2ca02c', 'Bootstrap')
    ]:
        arm_counts = [
            df[df['TreatmentArm'] == 'Active']['SubjectID'].nunique(),
            df[df['TreatmentArm'] == 'Placebo']['SubjectID'].nunique()
        ]
        fig.add_trace(
            go.Bar(x=['Active', 'Placebo'], y=arm_counts, name=name,
                   marker_color=color, legendgroup=name,
                   showlegend=False),
            row=1, col=3
        )

    fig.update_layout(height=500, barmode='group')
    fig.update_xaxes(title_text="Data Source", row=1, col=1)
    fig.update_xaxes(title_text="Visit", row=1, col=2)
    fig.update_xaxes(title_text="Treatment Arm", row=1, col=3)
    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Records", row=1, col=2)
    fig.update_yaxes(title_text="Subjects", row=1, col=3)

    return fig

def main():
    """Main function to run column comparison analysis"""
    from generators import load_pilot_vitals, generate_vitals_mvn, generate_vitals_bootstrap

    print("\n" + "="*80)
    print(" "*20 + "COLUMN/FIELD-LEVEL COMPARISON ANALYSIS")
    print("="*80)

    # Load data
    print("\n📊 Loading data...")
    real_df = load_pilot_vitals()
    mvn_df = generate_vitals_mvn(n_per_arm=50, seed=123)
    bootstrap_df = generate_vitals_bootstrap(real_df, n_per_arm=50, seed=42)

    print(f"✓ Real data: {len(real_df)} records")
    print(f"✓ MVN synthetic: {len(mvn_df)} records")
    print(f"✓ Bootstrap synthetic: {len(bootstrap_df)} records")

    # 1. Field comparison table
    print("\n" + "="*80)
    print("1. COMPREHENSIVE FIELD COMPARISON")
    print("="*80)
    comparison_table = create_field_comparison_table(real_df, mvn_df, bootstrap_df)
    print(comparison_table.to_string(index=False))

    # 2. Column statistics for each dataset
    print("\n" + "="*80)
    print("2. DETAILED COLUMN STATISTICS")
    print("="*80)

    print("\n📊 Real Data Column Statistics:")
    real_stats = analyze_column_statistics(real_df, 'Real CDISC')
    print(real_stats.to_string(index=False))

    print("\n📊 MVN Synthetic Column Statistics:")
    mvn_stats = analyze_column_statistics(mvn_df, 'MVN Synthetic')
    print(mvn_stats.to_string(index=False))

    print("\n📊 Bootstrap Synthetic Column Statistics:")
    bootstrap_stats = analyze_column_statistics(bootstrap_df, 'Bootstrap Synthetic')
    print(bootstrap_stats.to_string(index=False))

    # 3. Data completeness analysis
    print("\n" + "="*80)
    print("3. DATA COMPLETENESS ANALYSIS")
    print("="*80)

    for field in ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']:
        real_complete = 100 - (real_df[field].isnull().sum() / len(real_df) * 100)
        mvn_complete = 100 - (mvn_df[field].isnull().sum() / len(mvn_df) * 100)
        boot_complete = 100 - (bootstrap_df[field].isnull().sum() / len(bootstrap_df) * 100)

        print(f"\n{field}:")
        print(f"  Real:      {real_complete:6.2f}%")
        print(f"  MVN:       {mvn_complete:6.2f}%")
        print(f"  Bootstrap: {boot_complete:6.2f}%")

    # 4. Value range validation
    print("\n" + "="*80)
    print("4. VALUE RANGE VALIDATION")
    print("="*80)

    ranges = {
        'SystolicBP': (95, 200),
        'DiastolicBP': (55, 130),
        'HeartRate': (50, 120),
        'Temperature': (35.0, 40.0)
    }

    for field, (min_val, max_val) in ranges.items():
        print(f"\n{field} [Valid: {min_val}-{max_val}]:")

        real_valid = real_df[field].between(min_val, max_val).sum() / len(real_df) * 100
        mvn_valid = mvn_df[field].between(min_val, max_val).sum() / len(mvn_df) * 100
        boot_valid = bootstrap_df[field].between(min_val, max_val).sum() / len(bootstrap_df) * 100

        print(f"  Real:      {real_valid:6.2f}% in valid range")
        print(f"  MVN:       {mvn_valid:6.2f}% in valid range")
        print(f"  Bootstrap: {boot_valid:6.2f}% in valid range")

    # 5. Categorical field analysis
    print("\n" + "="*80)
    print("5. CATEGORICAL FIELD ANALYSIS")
    print("="*80)

    print("\n📊 SubjectID:")
    print(f"  Real:      {real_df['SubjectID'].nunique():5} unique subjects")
    print(f"  MVN:       {mvn_df['SubjectID'].nunique():5} unique subjects")
    print(f"  Bootstrap: {bootstrap_df['SubjectID'].nunique():5} unique subjects")

    print("\n📊 VisitName:")
    print("  Real:")
    print(real_df['VisitName'].value_counts().to_string())
    print("\n  MVN:")
    print(mvn_df['VisitName'].value_counts().to_string())
    print("\n  Bootstrap:")
    print(bootstrap_df['VisitName'].value_counts().to_string())

    print("\n📊 TreatmentArm:")
    print("  Real:")
    print(real_df.groupby('TreatmentArm')['SubjectID'].nunique().to_string())
    print("\n  MVN:")
    print(mvn_df.groupby('TreatmentArm')['SubjectID'].nunique().to_string())
    print("\n  Bootstrap:")
    print(bootstrap_df.groupby('TreatmentArm')['SubjectID'].nunique().to_string())

    # Generate visualizations
    print("\n" + "="*80)
    print("6. GENERATING VISUALIZATIONS")
    print("="*80)

    print("\n📊 Creating data completeness chart...")
    fig1 = create_data_completeness_chart(real_df, mvn_df, bootstrap_df)
    fig1.write_html('column_comparison_completeness.html')
    print("✓ Saved: column_comparison_completeness.html")

    print("\n📊 Creating value range comparison...")
    fig2 = create_value_range_comparison(real_df, mvn_df, bootstrap_df)
    fig2.write_html('column_comparison_ranges.html')
    print("✓ Saved: column_comparison_ranges.html")

    print("\n📊 Creating categorical field comparison...")
    fig3 = create_categorical_field_comparison(real_df, mvn_df, bootstrap_df)
    fig3.write_html('column_comparison_categorical.html')
    print("✓ Saved: column_comparison_categorical.html")

    # Export tables to CSV
    print("\n" + "="*80)
    print("7. EXPORTING RESULTS")
    print("="*80)

    comparison_table.to_csv('column_comparison_summary.csv', index=False)
    print("✓ Exported: column_comparison_summary.csv")

    combined_stats = pd.concat([real_stats, mvn_stats, bootstrap_stats])
    combined_stats.to_csv('column_statistics_detailed.csv', index=False)
    print("✓ Exported: column_statistics_detailed.csv")

    print("\n" + "="*80)
    print("✅ COLUMN/FIELD COMPARISON ANALYSIS COMPLETE!")
    print("="*80)
    print("\nGenerated files:")
    print("  • column_comparison_completeness.html")
    print("  • column_comparison_ranges.html")
    print("  • column_comparison_categorical.html")
    print("  • column_comparison_summary.csv")
    print("  • column_statistics_detailed.csv")
    print("\n")

if __name__ == "__main__":
    main()
