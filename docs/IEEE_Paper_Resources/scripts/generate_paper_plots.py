import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Add data generation service to path
sys.path.append(os.path.abspath("microservices/data-generation-service/src"))

try:
    from generate_vitals_enhanced import generate_vitals_enhanced
except ImportError as e:
    print(f"Error importing generators: {e}")
    sys.exit(1)

# Redefine naive baseline here for simplicity
def generate_naive_baseline(n_per_arm=50):
    """Generate purely random data (no correlation, no heterogeneity)"""
    rng = np.random.default_rng(42)
    rows = []
    for i in range(n_per_arm * 2):
        sid = f"S{i:03d}"
        arm = "Active" if i < n_per_arm else "Placebo"
        # Match enhanced generator defaults: 0, 4, 12
        for visit_idx, visit in enumerate(["Screening", "Week 4", "Week 12"]):
            # Pure random noise, no subject baseline
            sbp = rng.normal(130, 15) 
            rows.append({
                "SubjectID": sid,
                "VisitName": visit,
                "VisitOrder": visit_idx,
                "TreatmentArm": arm,
                "SystolicBP": sbp
            })
    return pd.DataFrame(rows)

def plot_trajectories():
    print("Generating Trajectory Plots...")
    
    # Generate data
    n_subjects = 10 # Small number for clean plot
    df_basic = generate_naive_baseline(n_per_arm=n_subjects//2)
    df_enhanced = generate_vitals_enhanced(n_per_arm=n_subjects//2)
    
    # Filter to just 5 subjects from Active arm for clarity
    subjects_basic = df_basic[df_basic['TreatmentArm'] == 'Active']['SubjectID'].unique()[:5]
    subjects_enhanced = df_enhanced[df_enhanced['TreatmentArm'] == 'Active']['SubjectID'].unique()[:5]
    
    df_basic_plot = df_basic[df_basic['SubjectID'].isin(subjects_basic)].copy()
    df_enhanced_plot = df_enhanced[df_enhanced['SubjectID'].isin(subjects_enhanced)].copy()
    
    # Map visits to numeric for plotting
    visit_map = {"Screening": 0, "Week 4": 4, "Week 12": 12}
    df_basic_plot['Week'] = df_basic_plot['VisitName'].map(visit_map)
    df_enhanced_plot['Week'] = df_enhanced_plot['VisitName'].map(visit_map)
    
    # Setup plot
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    
    # Plot Baseline
    sns.lineplot(data=df_basic_plot, x='Week', y='SystolicBP', hue='SubjectID', 
                 marker='o', ax=axes[0], legend=False, palette='viridis')
    axes[0].set_title('Baseline Model: Independent Noise\n(No Temporal Correlation)', fontsize=14)
    axes[0].set_ylabel('Systolic BP (mmHg)', fontsize=12)
    axes[0].set_xlabel('Study Week', fontsize=12)
    axes[0].grid(True, alpha=0.3)
    
    # Plot Enhanced
    sns.lineplot(data=df_enhanced_plot, x='Week', y='SystolicBP', hue='SubjectID', 
                 marker='o', ax=axes[1], legend=False, palette='viridis')
    axes[1].set_title('Enhanced Model: Autoregressive Dynamics\n(Realistic Patient Trajectories)', fontsize=14)
    axes[1].set_xlabel('Study Week', fontsize=12)
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('figure1_trajectories.png', dpi=300)
    print("✅ Saved figure1_trajectories.png")

def plot_correlation_matrix():
    print("Generating Correlation Heatmaps...")
    
    # Generate larger dataset for stable correlation
    n_subjects = 200
    df_basic = generate_naive_baseline(n_per_arm=n_subjects//2)
    df_enhanced = generate_vitals_enhanced(n_per_arm=n_subjects//2)
    
    # Pivot to wide format: Subject x Visit
    # Basic
    df_basic_wide = df_basic.pivot(index='SubjectID', columns='VisitName', values='SystolicBP')
    # Reorder columns
    cols = ["Screening", "Week 4", "Week 12"]
    df_basic_wide = df_basic_wide[cols]
    corr_basic = df_basic_wide.corr()
    
    # Enhanced
    df_enhanced_wide = df_enhanced.pivot(index='SubjectID', columns='VisitName', values='SystolicBP')
    df_enhanced_wide = df_enhanced_wide[cols]
    corr_enhanced = df_enhanced_wide.corr()
    
    # Setup plot
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Plot Baseline
    sns.heatmap(corr_basic, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=axes[0], fmt=".2f")
    axes[0].set_title('Baseline Model: Correlation Matrix\n(Uncorrelated)', fontsize=14)
    
    # Plot Enhanced
    sns.heatmap(corr_enhanced, annot=True, cmap='coolwarm', vmin=-1, vmax=1, ax=axes[1], fmt=".2f")
    axes[1].set_title('Enhanced Model: Correlation Matrix\n(Strong Temporal Structure)', fontsize=14)
    
    plt.tight_layout()
    plt.savefig('figure2_correlation.png', dpi=300)
    print("✅ Saved figure2_correlation.png")

if __name__ == "__main__":
    # Set style
    sns.set_theme(style="whitegrid")
    
    plot_trajectories()
    plot_correlation_matrix()
