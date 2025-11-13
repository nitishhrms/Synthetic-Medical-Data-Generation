#!/usr/bin/env python3
"""
Multi-panel Field Distribution Comparison
Similar to the Pima diabetes dataset visualization style
Shows overlapping histograms for all fields comparing real vs synthetic data
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Add generators to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

def create_distribution_comparison(real_df, synthetic_df, synthetic_name, output_file):
    """
    Create multi-panel histogram comparison

    Args:
        real_df: Real CDISC data
        synthetic_df: Synthetic data (MVN or Bootstrap)
        synthetic_name: Name for synthetic data (e.g., "MVN" or "Bootstrap")
        output_file: Output filename
    """
    # Define all fields to compare
    fields = {
        'SystolicBP': 'Systolic Blood Pressure (mmHg)',
        'DiastolicBP': 'Diastolic Blood Pressure (mmHg)',
        'HeartRate': 'Heart Rate (bpm)',
        'Temperature': 'Temperature (°C)',
        'SubjectCount': 'Subjects per Visit',
        'TreatmentBalance': 'Treatment Arm Distribution',
        'VisitSequence': 'Visit Sequence Completeness'
    }

    # Create figure with subplots
    fig = plt.figure(figsize=(20, 12))
    gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)

    colors = {
        'Real': '#5B9BD5',      # Blue
        'Synthetic': '#ED7D31'   # Orange
    }

    # Plot 1: Systolic BP
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.hist(real_df['SystolicBP'], bins=30, alpha=0.7, color=colors['Real'],
             label='Real Data', density=True, edgecolor='black', linewidth=0.5)
    ax1.hist(synthetic_df['SystolicBP'], bins=30, alpha=0.7, color=colors['Synthetic'],
             label=f'{synthetic_name} Synthetic', density=True, edgecolor='black', linewidth=0.5)
    ax1.set_xlabel('Systolic BP (mmHg)')
    ax1.set_ylabel('Density')
    ax1.set_title('SystolicBP', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Plot 2: Diastolic BP
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.hist(real_df['DiastolicBP'], bins=30, alpha=0.7, color=colors['Real'],
             label='Real Data', density=True, edgecolor='black', linewidth=0.5)
    ax2.hist(synthetic_df['DiastolicBP'], bins=30, alpha=0.7, color=colors['Synthetic'],
             label=f'{synthetic_name} Synthetic', density=True, edgecolor='black', linewidth=0.5)
    ax2.set_xlabel('Diastolic BP (mmHg)')
    ax2.set_ylabel('Density')
    ax2.set_title('DiastolicBP', fontsize=12, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8)
    ax2.grid(True, alpha=0.3)

    # Plot 3: Heart Rate
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.hist(real_df['HeartRate'], bins=30, alpha=0.7, color=colors['Real'],
             label='Real Data', density=True, edgecolor='black', linewidth=0.5)
    ax3.hist(synthetic_df['HeartRate'], bins=30, alpha=0.7, color=colors['Synthetic'],
             label=f'{synthetic_name} Synthetic', density=True, edgecolor='black', linewidth=0.5)
    ax3.set_xlabel('Heart Rate (bpm)')
    ax3.set_ylabel('Density')
    ax3.set_title('HeartRate', fontsize=12, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=8)
    ax3.grid(True, alpha=0.3)

    # Plot 4: Temperature
    ax4 = fig.add_subplot(gs[1, 0])
    ax4.hist(real_df['Temperature'], bins=30, alpha=0.7, color=colors['Real'],
             label='Real Data', density=True, edgecolor='black', linewidth=0.5)
    ax4.hist(synthetic_df['Temperature'], bins=30, alpha=0.7, color=colors['Synthetic'],
             label=f'{synthetic_name} Synthetic', density=True, edgecolor='black', linewidth=0.5)
    ax4.set_xlabel('Temperature (°C)')
    ax4.set_ylabel('Density')
    ax4.set_title('Temperature', fontsize=12, fontweight='bold')
    ax4.legend(loc='upper right', fontsize=8)
    ax4.grid(True, alpha=0.3)

    # Plot 5: Subject Count per Visit
    ax5 = fig.add_subplot(gs[1, 1])
    visit_order = ['Screening', 'Day 1', 'Week 4', 'Week 12']
    real_counts = [len(real_df[real_df['VisitName']==v]) for v in visit_order]
    synth_counts = [len(synthetic_df[synthetic_df['VisitName']==v]) for v in visit_order]

    x = np.arange(len(visit_order))
    width = 0.35
    ax5.bar(x - width/2, real_counts, width, alpha=0.7, color=colors['Real'],
            label='Real Data', edgecolor='black', linewidth=0.5)
    ax5.bar(x + width/2, synth_counts, width, alpha=0.7, color=colors['Synthetic'],
            label=f'{synthetic_name} Synthetic', edgecolor='black', linewidth=0.5)
    ax5.set_xlabel('Visit')
    ax5.set_ylabel('Record Count')
    ax5.set_title('Records per Visit', fontsize=12, fontweight='bold')
    ax5.set_xticks(x)
    ax5.set_xticklabels(visit_order, rotation=45, ha='right', fontsize=9)
    ax5.legend(loc='upper right', fontsize=8)
    ax5.grid(True, alpha=0.3, axis='y')

    # Plot 6: Treatment Arm Balance
    ax6 = fig.add_subplot(gs[1, 2])
    real_active = real_df[real_df['TreatmentArm']=='Active']['SubjectID'].nunique()
    real_placebo = real_df[real_df['TreatmentArm']=='Placebo']['SubjectID'].nunique()
    synth_active = synthetic_df[synthetic_df['TreatmentArm']=='Active']['SubjectID'].nunique()
    synth_placebo = synthetic_df[synthetic_df['TreatmentArm']=='Placebo']['SubjectID'].nunique()

    arms = ['Active', 'Placebo']
    real_arm_counts = [real_active, real_placebo]
    synth_arm_counts = [synth_active, synth_placebo]

    x = np.arange(len(arms))
    ax6.bar(x - width/2, real_arm_counts, width, alpha=0.7, color=colors['Real'],
            label='Real Data', edgecolor='black', linewidth=0.5)
    ax6.bar(x + width/2, synth_arm_counts, width, alpha=0.7, color=colors['Synthetic'],
            label=f'{synthetic_name} Synthetic', edgecolor='black', linewidth=0.5)
    ax6.set_xlabel('Treatment Arm')
    ax6.set_ylabel('Subject Count')
    ax6.set_title('Treatment Arm Balance', fontsize=12, fontweight='bold')
    ax6.set_xticks(x)
    ax6.set_xticklabels(arms)
    ax6.legend(loc='upper right', fontsize=8)
    ax6.grid(True, alpha=0.3, axis='y')

    # Plot 7: Visit Completeness (% subjects with all 4 visits)
    ax7 = fig.add_subplot(gs[2, 0])
    real_complete = (real_df.groupby('SubjectID')['VisitName'].nunique() == 4).sum()
    real_total = real_df['SubjectID'].nunique()
    synth_complete = (synthetic_df.groupby('SubjectID')['VisitName'].nunique() == 4).sum()
    synth_total = synthetic_df['SubjectID'].nunique()

    completeness = ['Complete\nSequences', 'Incomplete\nSequences']
    real_comp = [(real_complete/real_total)*100, ((real_total-real_complete)/real_total)*100]
    synth_comp = [(synth_complete/synth_total)*100, ((synth_total-synth_complete)/synth_total)*100]

    x = np.arange(len(completeness))
    ax7.bar(x - width/2, real_comp, width, alpha=0.7, color=colors['Real'],
            label='Real Data', edgecolor='black', linewidth=0.5)
    ax7.bar(x + width/2, synth_comp, width, alpha=0.7, color=colors['Synthetic'],
            label=f'{synthetic_name} Synthetic', edgecolor='black', linewidth=0.5)
    ax7.set_xlabel('Visit Sequence Status')
    ax7.set_ylabel('Percentage (%)')
    ax7.set_title('Visit Sequence Completeness', fontsize=12, fontweight='bold')
    ax7.set_xticks(x)
    ax7.set_xticklabels(completeness, fontsize=9)
    ax7.set_ylim(0, 105)
    ax7.legend(loc='upper right', fontsize=8)
    ax7.grid(True, alpha=0.3, axis='y')

    # Plot 8: BP Differential (SBP - DBP)
    ax8 = fig.add_subplot(gs[2, 1])
    real_diff = real_df['SystolicBP'] - real_df['DiastolicBP']
    synth_diff = synthetic_df['SystolicBP'] - synthetic_df['DiastolicBP']

    ax8.hist(real_diff, bins=30, alpha=0.7, color=colors['Real'],
             label='Real Data', density=True, edgecolor='black', linewidth=0.5)
    ax8.hist(synth_diff, bins=30, alpha=0.7, color=colors['Synthetic'],
             label=f'{synthetic_name} Synthetic', density=True, edgecolor='black', linewidth=0.5)
    ax8.set_xlabel('BP Differential (SBP - DBP) mmHg')
    ax8.set_ylabel('Density')
    ax8.set_title('Pulse Pressure Distribution', fontsize=12, fontweight='bold')
    ax8.legend(loc='upper right', fontsize=8)
    ax8.grid(True, alpha=0.3)

    # Plot 9: Summary Statistics Table
    ax9 = fig.add_subplot(gs[2, 2])
    ax9.axis('off')

    summary_data = [
        ['Metric', 'Real', synthetic_name],
        ['', '', ''],
        ['Total Records', f"{len(real_df):,}", f"{len(synthetic_df):,}"],
        ['Unique Subjects', f"{real_df['SubjectID'].nunique()}", f"{synthetic_df['SubjectID'].nunique()}"],
        ['', '', ''],
        ['SBP Mean', f"{real_df['SystolicBP'].mean():.1f}", f"{synthetic_df['SystolicBP'].mean():.1f}"],
        ['DBP Mean', f"{real_df['DiastolicBP'].mean():.1f}", f"{synthetic_df['DiastolicBP'].mean():.1f}"],
        ['HR Mean', f"{real_df['HeartRate'].mean():.1f}", f"{synthetic_df['HeartRate'].mean():.1f}"],
        ['Temp Mean', f"{real_df['Temperature'].mean():.2f}", f"{synthetic_df['Temperature'].mean():.2f}"],
        ['', '', ''],
        ['Active Subjects', f"{real_active}", f"{synth_active}"],
        ['Placebo Subjects', f"{real_placebo}", f"{synth_placebo}"],
    ]

    table = ax9.table(cellText=summary_data, cellLoc='left',
                     bbox=[0, 0, 1, 1],
                     colWidths=[0.4, 0.3, 0.3])

    table.auto_set_font_size(False)
    table.set_fontsize(9)

    # Style header row
    for i in range(3):
        cell = table[(0, i)]
        cell.set_facecolor('#D9D9D9')
        cell.set_text_props(weight='bold')

    # Style section separators
    for row in [1, 4, 9]:
        for col in range(3):
            cell = table[(row, col)]
            cell.set_facecolor('#F2F2F2')

    ax9.set_title('Summary Statistics', fontsize=12, fontweight='bold', pad=20)

    # Overall title
    fig.suptitle(f'Field Distribution Comparison: Real CDISC vs {synthetic_name} Synthetic Data',
                 fontsize=16, fontweight='bold', y=0.98)

    # Save figure
    plt.savefig(output_file, dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: {output_file}")

    return fig

def main():
    """Generate field distribution comparisons"""
    from generators import load_pilot_vitals, generate_vitals_mvn, generate_vitals_bootstrap

    print("\n" + "="*80)
    print(" "*15 + "FIELD DISTRIBUTION COMPARISON - MULTI-PANEL VIEW")
    print("="*80)

    # Load data
    print("\n📊 Loading data...")
    real_df = load_pilot_vitals()
    print(f"✓ Real CDISC: {len(real_df)} records from {real_df['SubjectID'].nunique()} subjects")

    mvn_df = generate_vitals_mvn(n_per_arm=50, seed=123)
    print(f"✓ MVN Synthetic: {len(mvn_df)} records from {mvn_df['SubjectID'].nunique()} subjects")

    bootstrap_df = generate_vitals_bootstrap(real_df, n_per_arm=50, seed=42)
    print(f"✓ Bootstrap Synthetic: {len(bootstrap_df)} records from {bootstrap_df['SubjectID'].nunique()} subjects")

    # Generate visualizations
    print("\n📊 Generating multi-panel distribution comparisons...")

    print("\n1. Real vs MVN Synthetic...")
    fig1 = create_distribution_comparison(
        real_df, mvn_df,
        'MVN',
        'field_distributions_real_vs_mvn.png'
    )
    plt.close(fig1)

    print("\n2. Real vs Bootstrap Synthetic...")
    fig2 = create_distribution_comparison(
        real_df, bootstrap_df,
        'Bootstrap',
        'field_distributions_real_vs_bootstrap.png'
    )
    plt.close(fig2)

    # Create combined comparison (all 3 datasets)
    print("\n3. Creating comprehensive 3-way comparison...")
    create_three_way_comparison(real_df, mvn_df, bootstrap_df)

    print("\n" + "="*80)
    print("✅ FIELD DISTRIBUTION COMPARISON COMPLETE!")
    print("="*80)
    print("\nGenerated files:")
    print("  • field_distributions_real_vs_mvn.png (3000x1800 px)")
    print("  • field_distributions_real_vs_bootstrap.png (3000x1800 px)")
    print("  • field_distributions_three_way.png (3000x2400 px)")
    print("\nOpen these PNG files to view the detailed comparisons!")
    print("="*80 + "\n")

def create_three_way_comparison(real_df, mvn_df, bootstrap_df):
    """Create 3-way comparison with all datasets"""

    fig = plt.figure(figsize=(24, 16))
    gs = fig.add_gridspec(4, 3, hspace=0.35, wspace=0.3)

    colors = {
        'Real': '#5B9BD5',      # Blue
        'MVN': '#ED7D31',       # Orange
        'Bootstrap': '#70AD47'  # Green
    }

    # Plot vital signs
    vitals = [
        ('SystolicBP', 'Systolic BP (mmHg)', gs[0, 0]),
        ('DiastolicBP', 'Diastolic BP (mmHg)', gs[0, 1]),
        ('HeartRate', 'Heart Rate (bpm)', gs[0, 2]),
        ('Temperature', 'Temperature (°C)', gs[1, 0])
    ]

    for field, label, position in vitals:
        ax = fig.add_subplot(position)
        ax.hist(real_df[field], bins=30, alpha=0.6, color=colors['Real'],
                label='Real', density=True, edgecolor='black', linewidth=0.5)
        ax.hist(mvn_df[field], bins=30, alpha=0.6, color=colors['MVN'],
                label='MVN', density=True, edgecolor='black', linewidth=0.5)
        ax.hist(bootstrap_df[field], bins=30, alpha=0.6, color=colors['Bootstrap'],
                label='Bootstrap', density=True, edgecolor='black', linewidth=0.5)
        ax.set_xlabel(label)
        ax.set_ylabel('Density')
        ax.set_title(field, fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=9)
        ax.grid(True, alpha=0.3)

    # Visit distribution
    ax = fig.add_subplot(gs[1, 1])
    visit_order = ['Screening', 'Day 1', 'Week 4', 'Week 12']
    real_counts = [len(real_df[real_df['VisitName']==v]) for v in visit_order]
    mvn_counts = [len(mvn_df[mvn_df['VisitName']==v]) for v in visit_order]
    boot_counts = [len(bootstrap_df[bootstrap_df['VisitName']==v]) for v in visit_order]

    x = np.arange(len(visit_order))
    width = 0.25
    ax.bar(x - width, real_counts, width, alpha=0.7, color=colors['Real'],
           label='Real', edgecolor='black', linewidth=0.5)
    ax.bar(x, mvn_counts, width, alpha=0.7, color=colors['MVN'],
           label='MVN', edgecolor='black', linewidth=0.5)
    ax.bar(x + width, boot_counts, width, alpha=0.7, color=colors['Bootstrap'],
           label='Bootstrap', edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Visit')
    ax.set_ylabel('Record Count')
    ax.set_title('Records per Visit', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(visit_order, rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Treatment arm balance
    ax = fig.add_subplot(gs[1, 2])
    arms = ['Active', 'Placebo']
    real_arms = [
        real_df[real_df['TreatmentArm']=='Active']['SubjectID'].nunique(),
        real_df[real_df['TreatmentArm']=='Placebo']['SubjectID'].nunique()
    ]
    mvn_arms = [
        mvn_df[mvn_df['TreatmentArm']=='Active']['SubjectID'].nunique(),
        mvn_df[mvn_df['TreatmentArm']=='Placebo']['SubjectID'].nunique()
    ]
    boot_arms = [
        bootstrap_df[bootstrap_df['TreatmentArm']=='Active']['SubjectID'].nunique(),
        bootstrap_df[bootstrap_df['TreatmentArm']=='Placebo']['SubjectID'].nunique()
    ]

    x = np.arange(len(arms))
    ax.bar(x - width, real_arms, width, alpha=0.7, color=colors['Real'],
           label='Real', edgecolor='black', linewidth=0.5)
    ax.bar(x, mvn_arms, width, alpha=0.7, color=colors['MVN'],
           label='MVN', edgecolor='black', linewidth=0.5)
    ax.bar(x + width, boot_arms, width, alpha=0.7, color=colors['Bootstrap'],
           label='Bootstrap', edgecolor='black', linewidth=0.5)
    ax.set_xlabel('Treatment Arm')
    ax.set_ylabel('Subject Count')
    ax.set_title('Treatment Arm Balance', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(arms)
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Box plots for all vitals (row 3)
    for idx, (field, label) in enumerate([
        ('SystolicBP', 'SBP'),
        ('DiastolicBP', 'DBP'),
        ('HeartRate', 'HR')
    ]):
        ax = fig.add_subplot(gs[2, idx])
        data = [real_df[field], mvn_df[field], bootstrap_df[field]]
        bp = ax.boxplot(data, labels=['Real', 'MVN', 'Bootstrap'],
                        patch_artist=True, showfliers=True)

        for patch, color in zip(bp['boxes'], [colors['Real'], colors['MVN'], colors['Bootstrap']]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_ylabel(f'{label} Value')
        ax.set_title(f'{field} Box Plot', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')

    # Statistical comparison table
    ax = fig.add_subplot(gs[3, :])
    ax.axis('off')

    summary_data = [
        ['Metric', 'Real CDISC', 'MVN Synthetic', 'Bootstrap Synthetic', 'MVN Diff %', 'Bootstrap Diff %'],
        ['Records', f"{len(real_df):,}", f"{len(mvn_df):,}", f"{len(bootstrap_df):,}", '', ''],
        ['Subjects', f"{real_df['SubjectID'].nunique()}", f"{mvn_df['SubjectID'].nunique()}", f"{bootstrap_df['SubjectID'].nunique()}", '', ''],
        ['', '', '', '', '', ''],
        ['SBP Mean',
         f"{real_df['SystolicBP'].mean():.2f}",
         f"{mvn_df['SystolicBP'].mean():.2f}",
         f"{bootstrap_df['SystolicBP'].mean():.2f}",
         f"{((mvn_df['SystolicBP'].mean() - real_df['SystolicBP'].mean())/real_df['SystolicBP'].mean()*100):.2f}%",
         f"{((bootstrap_df['SystolicBP'].mean() - real_df['SystolicBP'].mean())/real_df['SystolicBP'].mean()*100):.2f}%"],
        ['DBP Mean',
         f"{real_df['DiastolicBP'].mean():.2f}",
         f"{mvn_df['DiastolicBP'].mean():.2f}",
         f"{bootstrap_df['DiastolicBP'].mean():.2f}",
         f"{((mvn_df['DiastolicBP'].mean() - real_df['DiastolicBP'].mean())/real_df['DiastolicBP'].mean()*100):.2f}%",
         f"{((bootstrap_df['DiastolicBP'].mean() - real_df['DiastolicBP'].mean())/real_df['DiastolicBP'].mean()*100):.2f}%"],
        ['HR Mean',
         f"{real_df['HeartRate'].mean():.2f}",
         f"{mvn_df['HeartRate'].mean():.2f}",
         f"{bootstrap_df['HeartRate'].mean():.2f}",
         f"{((mvn_df['HeartRate'].mean() - real_df['HeartRate'].mean())/real_df['HeartRate'].mean()*100):.2f}%",
         f"{((bootstrap_df['HeartRate'].mean() - real_df['HeartRate'].mean())/real_df['HeartRate'].mean()*100):.2f}%"],
        ['Temp Mean',
         f"{real_df['Temperature'].mean():.3f}",
         f"{mvn_df['Temperature'].mean():.3f}",
         f"{bootstrap_df['Temperature'].mean():.3f}",
         f"{((mvn_df['Temperature'].mean() - real_df['Temperature'].mean())/real_df['Temperature'].mean()*100):.2f}%",
         f"{((bootstrap_df['Temperature'].mean() - real_df['Temperature'].mean())/real_df['Temperature'].mean()*100):.2f}%"],
    ]

    table = ax.table(cellText=summary_data, cellLoc='center',
                    bbox=[0.1, 0.2, 0.8, 0.7],
                    colWidths=[0.2, 0.15, 0.15, 0.15, 0.15, 0.15])

    table.auto_set_font_size(False)
    table.set_fontsize(10)

    # Style header
    for i in range(6):
        cell = table[(0, i)]
        cell.set_facecolor('#D9D9D9')
        cell.set_text_props(weight='bold')

    # Style separator
    for col in range(6):
        cell = table[(3, col)]
        cell.set_facecolor('#F2F2F2')

    ax.set_title('Comprehensive Statistical Comparison', fontsize=14, fontweight='bold')

    # Overall title
    fig.suptitle('Complete Field Distribution Analysis: Real vs MVN vs Bootstrap',
                 fontsize=18, fontweight='bold', y=0.995)

    plt.savefig('field_distributions_three_way.png', dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Saved: field_distributions_three_way.png")

if __name__ == "__main__":
    main()
