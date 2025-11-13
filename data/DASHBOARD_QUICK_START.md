# Analytics Dashboard - Quick Start

## 🚀 Launch Options

### Option 1: Interactive Web Dashboard (Recommended)
```bash
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/data
./launch_streamlit_dashboard.sh
```
**Opens in browser at:** http://localhost:8501

**Features:**
- ✅ Interactive filters (visit, treatment arm, data source)
- ✅ 6 tabs with different analyses
- ✅ Real-time visualization updates
- ✅ Click-and-explore interface

---

### Option 2: Jupyter Notebook (Comprehensive Analysis)
```bash
cd /Users/himanshu_jain/272/Synthetic-Medical-Data-Generation/data
./launch_jupyter_dashboard.sh
```

**Features:**
- ✅ 13 analysis sections
- ✅ Detailed statistical tests
- ✅ Export results to CSV
- ✅ Editable code cells

---

## 📊 What You'll See

### Real vs Synthetic Data Comparison

The dashboards compare **three datasets**:

1. **Real CDISC Data** (2,079 records from 254 subjects)
   - Industry-standard clinical trial data
   - Real patient vital signs

2. **MVN Synthetic Data** (400 records from 100 subjects)
   - Generated using Multivariate Normal distribution
   - Learns means and correlations from real data

3. **Bootstrap Synthetic Data** (998 records from 97 subjects)
   - Resampled from real data with jitter
   - Preserves realistic patterns

---

## 🎯 Key Visualizations

| Visualization | What It Shows | Why It Matters |
|---------------|---------------|----------------|
| **Histograms** | Distribution shapes | Ensure synthetic data matches real patterns |
| **Box Plots** | Median, quartiles, outliers | Verify realistic value ranges |
| **Temporal Progression** | Changes across visits | Validate visit-to-visit trends |
| **Treatment Effects** | Active vs Placebo | Check if -5mmHg effect is achieved |
| **Correlation Matrices** | Vital sign relationships | Preserve correlations (e.g., SBP↔DBP) |
| **Scatter Plots** | SBP vs DBP patterns | Visual correlation check |

---

## 📈 Interpretation Guide

### ✅ Good Synthetic Data

**Distributions:**
- Histograms overlap with real data
- Similar means: ±5% difference
- Similar std dev: ±10% difference

**Treatment Effects:**
- Week 12 effect: -5.0 mmHg ±1.0 mmHg
- Clear separation between Active and Placebo

**Correlations:**
- SBP vs DBP correlation: 0.4-0.6 (like real data)
- Patterns preserved across visits

**Quality Metrics:**
- 100% values in valid ranges
- Complete visit sequences
- p-value > 0.05 in KS tests

---

## 🔍 Streamlit Dashboard Controls

### Sidebar Filters

**1. Data Sources** (checkboxes)
- ☑️ Real CDISC Data
- ☑️ MVN Synthetic
- ☑️ Bootstrap Synthetic

**2. Visit Filter** (dropdown)
- All visits
- Screening
- Day 1
- Week 4
- Week 12

**3. Treatment Arm** (dropdown)
- All
- Active
- Placebo

### Tabs

| Tab | Focus Area |
|-----|------------|
| 📈 Overview | Summary stats, sample data |
| 📊 Distributions | Histograms, box plots, violins |
| 🔄 Temporal Analysis | Progression across visits |
| 💊 Treatment Effects | Week 12 efficacy |
| 🔗 Correlations | Heatmaps, scatter plots |
| ✅ Quality Metrics | Validation, statistical tests |

---

## 💡 Common Tasks

### Task 1: Check if synthetic data matches real data
1. Launch Streamlit dashboard
2. Select all 3 data sources
3. Go to **Distributions** tab
4. Compare histograms for each vital sign
5. ✅ Overlapping distributions = Good match

### Task 2: Verify treatment effect
1. Go to **Treatment Effects** tab
2. Check bar chart
3. ✅ Effect near -5.0 mmHg = Correct

### Task 3: Validate correlations
1. Go to **Correlations** tab
2. Compare heatmaps across datasets
3. ✅ Similar patterns = Preserved relationships

### Task 4: Statistical validation
1. Go to **Quality Metrics** tab
2. Check KS test p-values
3. ✅ p-value > 0.05 = Not significantly different

---

## 🐛 Troubleshooting

**Dashboard won't start?**
```bash
pip3 install streamlit plotly scipy pandas numpy
```

**Port already in use?**
```bash
streamlit run streamlit_dashboard.py --server.port 8502
```

**Data not loading?**
```bash
# Verify generators work first
python3 quick_test.py
```

**Jupyter kernel issues?**
```bash
pip3 install --upgrade jupyter ipykernel
```

---

## 📚 More Information

- Full guide: `DASHBOARD_GUIDE.md`
- Real data integration: `REAL_DATA_INTEGRATION.md`
- Generator tests: `python3 test_generators_with_real_data.py`

---

## ⚡ Quick Commands

```bash
# Interactive dashboard
./launch_streamlit_dashboard.sh

# Jupyter notebook
./launch_jupyter_dashboard.sh

# Test generators
python3 quick_test.py

# Verify setup
python3 verify_generators.py

# Full test suite
python3 test_generators_with_real_data.py
```

---

**Ready to explore?** Run `./launch_streamlit_dashboard.sh` and start analyzing! 🚀
