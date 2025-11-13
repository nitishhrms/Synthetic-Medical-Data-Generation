#!/usr/bin/env python3
"""
Interactive Streamlit Dashboard for Real vs Synthetic Data Comparison
Run with: streamlit run streamlit_dashboard.py
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy import stats
import streamlit as st

# Add generators to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "microservices" / "data-generation-service" / "src"))

# Page config
st.set_page_config(
    page_title="Clinical Trial Data Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_all_data():
    """Load and cache all datasets"""
    from generators import load_pilot_vitals, generate_vitals_mvn, generate_vitals_bootstrap

    with st.spinner("Loading real CDISC data..."):
        real_data = load_pilot_vitals()
        real_data['Source'] = 'Real CDISC'

    with st.spinner("Generating MVN synthetic data..."):
        mvn_data = generate_vitals_mvn(n_per_arm=50, target_effect=-5.0, seed=123)
        mvn_data['Source'] = 'MVN Synthetic'

    with st.spinner("Generating Bootstrap synthetic data..."):
        bootstrap_data = generate_vitals_bootstrap(real_data, n_per_arm=50, target_effect=-5.0, seed=42)
        bootstrap_data['Source'] = 'Bootstrap Synthetic'

    return real_data, mvn_data, bootstrap_data

# Main app
def main():
    st.markdown('<h1 class="main-header">📊 Clinical Trial Data Analytics Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("### Real CDISC Data vs Synthetic Data Comparison")

    # Load data
    try:
        real_data, mvn_data, bootstrap_data = load_all_data()
        combined = pd.concat([real_data, mvn_data, bootstrap_data], ignore_index=True)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.stop()

    # Sidebar
    st.sidebar.header("Dashboard Controls")

    # Data source selection
    st.sidebar.subheader("1. Select Data Sources")
    show_real = st.sidebar.checkbox("Real CDISC Data", value=True)
    show_mvn = st.sidebar.checkbox("MVN Synthetic", value=True)
    show_bootstrap = st.sidebar.checkbox("Bootstrap Synthetic", value=True)

    # Filter data based on selection
    sources = []
    if show_real:
        sources.append('Real CDISC')
    if show_mvn:
        sources.append('MVN Synthetic')
    if show_bootstrap:
        sources.append('Bootstrap Synthetic')

    filtered_data = combined[combined['Source'].isin(sources)]

    # Visit selection
    st.sidebar.subheader("2. Select Visit")
    visit_options = ['All'] + list(filtered_data['VisitName'].unique())
    selected_visit = st.sidebar.selectbox("Visit", visit_options)

    # Treatment arm selection
    st.sidebar.subheader("3. Select Treatment Arm")
    arm_options = ['All', 'Active', 'Placebo']
    selected_arm = st.sidebar.selectbox("Treatment Arm", arm_options)

    # Apply filters
    if selected_visit != 'All':
        filtered_data = filtered_data[filtered_data['VisitName'] == selected_visit]
    if selected_arm != 'All':
        filtered_data = filtered_data[filtered_data['TreatmentArm'] == selected_arm]

    # Dashboard sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Overview",
        "📊 Distributions",
        "🔄 Temporal Analysis",
        "💊 Treatment Effects",
        "🔗 Correlations",
        "✅ Quality Metrics"
    ])

    # TAB 1: Overview
    with tab1:
        st.header("Data Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            if show_real:
                st.metric(
                    "Real CDISC Records",
                    f"{len(real_data):,}",
                    f"{real_data['SubjectID'].nunique()} subjects"
                )

        with col2:
            if show_mvn:
                st.metric(
                    "MVN Synthetic Records",
                    f"{len(mvn_data):,}",
                    f"{mvn_data['SubjectID'].nunique()} subjects"
                )

        with col3:
            if show_bootstrap:
                st.metric(
                    "Bootstrap Synthetic Records",
                    f"{len(bootstrap_data):,}",
                    f"{bootstrap_data['SubjectID'].nunique()} subjects"
                )

        st.markdown("---")

        # Summary statistics table
        st.subheader("Summary Statistics")

        summary_stats = []
        for source in sources:
            df = combined[combined['Source'] == source]
            summary_stats.append({
                'Dataset': source,
                'Records': len(df),
                'Subjects': df['SubjectID'].nunique(),
                'SBP Mean': f"{df['SystolicBP'].mean():.1f}",
                'SBP Std': f"{df['SystolicBP'].std():.1f}",
                'DBP Mean': f"{df['DiastolicBP'].mean():.1f}",
                'DBP Std': f"{df['DiastolicBP'].std():.1f}",
                'HR Mean': f"{df['HeartRate'].mean():.1f}",
                'Temp Mean': f"{df['Temperature'].mean():.2f}"
            })

        st.dataframe(pd.DataFrame(summary_stats), use_container_width=True)

        # Sample data
        st.subheader("Sample Data")
        st.dataframe(filtered_data.head(20), use_container_width=True)

    # TAB 2: Distributions
    with tab2:
        st.header("Distribution Analysis")

        vital_to_plot = st.selectbox(
            "Select Vital Sign",
            ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']
        )

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Histogram")
            fig = go.Figure()
            colors_map = {'Real CDISC': '#1f77b4', 'MVN Synthetic': '#ff7f0e', 'Bootstrap Synthetic': '#2ca02c'}

            for source in sources:
                data = combined[combined['Source'] == source][vital_to_plot]
                fig.add_trace(go.Histogram(
                    x=data,
                    name=source,
                    opacity=0.6,
                    marker_color=colors_map[source],
                    nbinsx=30
                ))

            fig.update_layout(
                barmode='overlay',
                xaxis_title=vital_to_plot,
                yaxis_title="Count",
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("Box Plot")
            fig = go.Figure()

            for source in sources:
                data = combined[combined['Source'] == source][vital_to_plot]
                fig.add_trace(go.Box(
                    y=data,
                    name=source,
                    marker_color=colors_map[source]
                ))

            fig.update_layout(
                yaxis_title=vital_to_plot,
                height=400
            )
            st.plotly_chart(fig, use_container_width=True)

        # Violin plot
        st.subheader("Violin Plot")
        fig = go.Figure()

        for source in sources:
            data = combined[combined['Source'] == source][vital_to_plot]
            fig.add_trace(go.Violin(
                y=data,
                name=source,
                box_visible=True,
                meanline_visible=True,
                fillcolor=colors_map[source],
                opacity=0.6
            ))

        fig.update_layout(
            yaxis_title=vital_to_plot,
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # TAB 3: Temporal Analysis
    with tab3:
        st.header("Temporal Progression Across Visits")

        visit_order = ['Screening', 'Day 1', 'Week 4', 'Week 12']

        vital_temporal = st.selectbox(
            "Select Vital Sign for Temporal Analysis",
            ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature'],
            key='temporal_vital'
        )

        fig = go.Figure()

        line_styles = {'Active': 'solid', 'Placebo': 'dash'}
        colors_map = {'Real CDISC': '#1f77b4', 'MVN Synthetic': '#ff7f0e', 'Bootstrap Synthetic': '#2ca02c'}

        for source in sources:
            for arm in ['Active', 'Placebo']:
                subset = combined[(combined['Source'] == source) &
                                (combined['TreatmentArm'] == arm)]

                means = []
                for visit in visit_order:
                    visit_data = subset[subset['VisitName'] == visit][vital_temporal]
                    means.append(visit_data.mean() if len(visit_data) > 0 else np.nan)

                fig.add_trace(go.Scatter(
                    x=visit_order,
                    y=means,
                    name=f"{source} - {arm}",
                    line=dict(color=colors_map[source], dash=line_styles[arm]),
                    mode='lines+markers'
                ))

        fig.update_layout(
            xaxis_title="Visit",
            yaxis_title=vital_temporal,
            height=500,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=1,
                xanchor="left",
                x=1.01
            )
        )
        st.plotly_chart(fig, use_container_width=True)

        st.info("**Solid lines** = Active treatment | **Dashed lines** = Placebo")

    # TAB 4: Treatment Effects
    with tab4:
        st.header("Treatment Effect Analysis")

        st.markdown("""
        Treatment effect is calculated as: **Mean(Active) - Mean(Placebo)** at Week 12.
        Target effect: **-5.0 mmHg** (Active should lower SBP by 5 mmHg compared to Placebo)
        """)

        effects = {}
        for source in sources:
            df = combined[(combined['Source'] == source) & (combined['VisitName'] == 'Week 12')]
            active_mean = df[df['TreatmentArm']=='Active']['SystolicBP'].mean()
            placebo_mean = df[df['TreatmentArm']=='Placebo']['SystolicBP'].mean()
            effects[source] = active_mean - placebo_mean

        # Bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=list(effects.keys()),
                y=list(effects.values()),
                marker_color=[colors_map[k] for k in effects.keys()],
                text=[f"{v:.2f} mmHg" for v in effects.values()],
                textposition='auto'
            )
        ])

        fig.add_hline(y=-5.0, line_dash="dash", line_color="red",
                      annotation_text="Target: -5.0 mmHg")

        fig.update_layout(
            title="Treatment Effect at Week 12 (Active - Placebo)",
            xaxis_title="Data Source",
            yaxis_title="SBP Difference (mmHg)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # Effect table
        st.subheader("Treatment Effect Summary")
        effect_df = pd.DataFrame([
            {'Data Source': k, 'Effect (mmHg)': f"{v:.2f}", 'Error from Target': f"{abs(v - (-5.0)):.2f}"}
            for k, v in effects.items()
        ])
        st.dataframe(effect_df, use_container_width=True)

    # TAB 5: Correlations
    with tab5:
        st.header("Correlation Analysis")

        vital_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

        # Correlation matrices
        st.subheader("Correlation Matrices")

        cols = st.columns(len(sources))

        for i, source in enumerate(sources):
            with cols[i]:
                df = combined[combined['Source'] == source]
                corr = df[vital_cols].corr()

                fig = go.Figure(data=go.Heatmap(
                    z=corr.values,
                    x=corr.columns,
                    y=corr.columns,
                    colorscale='RdBu',
                    zmid=0,
                    zmin=-1,
                    zmax=1,
                    text=corr.values.round(2),
                    texttemplate='%{text}',
                    textfont={"size": 10}
                ))

                fig.update_layout(
                    title=source,
                    height=350
                )
                st.plotly_chart(fig, use_container_width=True)

        # Scatter plot: SBP vs DBP
        st.subheader("Scatter Plot: Systolic vs Diastolic BP")

        fig = go.Figure()

        for source in sources:
            df = combined[combined['Source'] == source]
            fig.add_trace(go.Scatter(
                x=df['DiastolicBP'],
                y=df['SystolicBP'],
                mode='markers',
                name=source,
                marker=dict(size=4, opacity=0.5, color=colors_map[source])
            ))

        fig.update_layout(
            xaxis_title="Diastolic BP (mmHg)",
            yaxis_title="Systolic BP (mmHg)",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

    # TAB 6: Quality Metrics
    with tab6:
        st.header("Data Quality Metrics")

        vital_cols = ['SystolicBP', 'DiastolicBP', 'HeartRate', 'Temperature']

        quality_metrics = []
        for source in sources:
            df = combined[combined['Source'] == source]

            metrics = {
                'Dataset': source,
                'Missing Values (%)': f"{(df[vital_cols].isnull().sum().sum() / (len(df) * len(vital_cols)) * 100):.2f}",
                'SBP in Range [95-200] (%)': f"{(df['SystolicBP'].between(95, 200).sum() / len(df) * 100):.1f}",
                'DBP in Range [55-130] (%)': f"{(df['DiastolicBP'].between(55, 130).sum() / len(df) * 100):.1f}",
                'HR in Range [50-120] (%)': f"{(df['HeartRate'].between(50, 120).sum() / len(df) * 100):.1f}",
                'Temp in Range [35-40] (%)': f"{(df['Temperature'].between(35, 40).sum() / len(df) * 100):.1f}",
                'Complete Visits (%)': f"{(df.groupby('SubjectID')['VisitName'].nunique().eq(4).sum() / df['SubjectID'].nunique() * 100):.1f}"
            }
            quality_metrics.append(metrics)

        st.dataframe(pd.DataFrame(quality_metrics), use_container_width=True)

        # Statistical tests
        st.subheader("Kolmogorov-Smirnov Tests")
        st.markdown("Tests whether synthetic data distributions match real data (higher p-value = better match)")

        if show_real and (show_mvn or show_bootstrap):
            ks_results = []

            for vital in vital_cols:
                row = {'Vital Sign': vital}

                if show_mvn:
                    ks_stat, p_val = stats.ks_2samp(
                        real_data[vital].dropna(),
                        mvn_data[vital].dropna()
                    )
                    row['MVN KS-Stat'] = f"{ks_stat:.4f}"
                    row['MVN p-value'] = f"{p_val:.4f}"

                if show_bootstrap:
                    ks_stat, p_val = stats.ks_2samp(
                        real_data[vital].dropna(),
                        bootstrap_data[vital].dropna()
                    )
                    row['Bootstrap KS-Stat'] = f"{ks_stat:.4f}"
                    row['Bootstrap p-value'] = f"{p_val:.4f}"

                ks_results.append(row)

            st.dataframe(pd.DataFrame(ks_results), use_container_width=True)
            st.info("p-value > 0.05 suggests distributions are not significantly different (good match)")
        else:
            st.warning("Please select Real CDISC data and at least one synthetic dataset to run statistical tests.")

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray;'>
        <p>Clinical Trial Data Analytics Dashboard | Powered by Streamlit</p>
        <p>Data: CDISC Pilot Project | Synthetic Generation: MVN & Bootstrap Methods</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
