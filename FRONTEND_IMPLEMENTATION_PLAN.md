# Frontend Implementation Plan - Synthetic Medical Data Platform

**Project**: Clinical Trial Analytics Dashboard
**Backend**: Analytics Service v1.6.0 (26 endpoints)
**Frontend**: React + TypeScript + Tailwind CSS
**Status**: Planning → Implementation

---

## 🎯 Objectives

Build a modern, responsive web application that provides:
1. **Data Generation**: Interface for generating synthetic clinical trial data
2. **Analytics Dashboard**: Visualizations for demographics, labs, AEs, vitals
3. **Quality Assessment**: Real-time quality scoring and validation
4. **AACT Benchmarking**: Industry comparison and recommendations
5. **Study Management**: Holistic study analytics and executive dashboards
6. **Method Optimization**: Performance comparison and parameter tuning

---

## 🏗️ Technology Stack

### Core Framework
- **React 18**: Component-based UI
- **TypeScript**: Type safety and IDE support
- **Vite**: Fast build tool and dev server
- **React Router**: Client-side routing

### Styling & UI
- **Tailwind CSS**: Utility-first styling
- **shadcn/ui**: High-quality component library
- **Lucide Icons**: Modern icon set
- **Recharts**: React charting library

### State Management
- **React Query (TanStack Query)**: Server state management
- **Zustand**: Lightweight client state
- **React Hook Form**: Form state and validation

### Data Handling
- **Axios**: HTTP client with interceptors
- **Zod**: Runtime type validation
- **date-fns**: Date manipulation

---

## 📐 Application Structure

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── components/
│   │   ├── ui/              # shadcn/ui components
│   │   ├── layout/          # Layout components (Header, Sidebar, Footer)
│   │   ├── charts/          # Chart components (BarChart, LineChart, ScatterPlot)
│   │   ├── tables/          # Data table components
│   │   └── forms/           # Form components
│   ├── pages/
│   │   ├── Dashboard.tsx    # Main dashboard
│   │   ├── Generate.tsx     # Data generation interface
│   │   ├── Analytics/
│   │   │   ├── Demographics.tsx
│   │   │   ├── Labs.tsx
│   │   │   ├── AdverseEvents.tsx
│   │   │   └── Vitals.tsx
│   │   ├── Quality/
│   │   │   ├── Assessment.tsx
│   │   │   └── Comparison.tsx
│   │   ├── AACT/
│   │   │   ├── Benchmarking.tsx
│   │   │   └── Recommendations.tsx
│   │   ├── Study/
│   │   │   ├── ComprehensiveSummary.tsx
│   │   │   ├── CrossDomain.tsx
│   │   │   └── Dashboard.tsx
│   │   └── Settings.tsx
│   ├── api/
│   │   ├── client.ts        # Axios instance
│   │   ├── analytics.ts     # Analytics API calls
│   │   ├── generation.ts    # Data generation API calls
│   │   ├── quality.ts       # Quality API calls
│   │   └── aact.ts          # AACT API calls
│   ├── types/
│   │   ├── analytics.ts     # Type definitions
│   │   ├── generation.ts
│   │   └── api.ts
│   ├── hooks/
│   │   ├── useAnalytics.ts  # Custom hooks
│   │   ├── useGeneration.ts
│   │   └── useQuality.ts
│   ├── store/
│   │   └── useStore.ts      # Zustand store
│   ├── utils/
│   │   ├── format.ts        # Formatting utilities
│   │   └── validation.ts    # Validation helpers
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

---

## 📱 Page Structure & Routes

### Main Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | Dashboard | Main overview with KPIs |
| `/generate` | Generate | Data generation interface |
| `/analytics/demographics` | Demographics | Demographics analytics |
| `/analytics/labs` | Labs | Laboratory analytics |
| `/analytics/ae` | AdverseEvents | AE analytics |
| `/analytics/vitals` | Vitals | Vitals analytics |
| `/quality/assessment` | Assessment | Quality scoring |
| `/quality/comparison` | Comparison | Real vs synthetic |
| `/aact/benchmark` | Benchmarking | AACT comparison |
| `/aact/recommendations` | Recommendations | Parameter optimization |
| `/study/summary` | ComprehensiveSummary | Holistic study view |
| `/study/correlations` | CrossDomain | Cross-domain analysis |
| `/study/dashboard` | Dashboard | Executive dashboard |
| `/settings` | Settings | App configuration |

---

## 🎨 UI/UX Design Principles

### Layout
- **Sidebar Navigation**: Persistent left sidebar with collapsible menu
- **Top Header**: Breadcrumbs, user info, notifications
- **Content Area**: Main content with responsive grid
- **Footer**: Copyright, version, links

### Color Scheme
- **Primary**: Blue (#3B82F6) - Analytics, buttons
- **Success**: Green (#10B981) - Quality passed, positive metrics
- **Warning**: Yellow (#F59E0B) - Medium priority, warnings
- **Danger**: Red (#EF4444) - Critical issues, failed validation
- **Neutral**: Gray (#6B7280) - Text, backgrounds

### Typography
- **Headings**: Inter font, bold
- **Body**: Inter font, regular
- **Code**: JetBrains Mono, monospace

---

## 🔧 Implementation Phases

### Phase 1: Project Setup & Core Infrastructure (Week 1)

**Tasks**:
1. Initialize Vite + React + TypeScript project
2. Install dependencies (Tailwind, shadcn/ui, React Query, etc.)
3. Configure Tailwind CSS
4. Set up folder structure
5. Create API client with Axios interceptors
6. Implement React Query configuration
7. Set up React Router
8. Create base layout components (Header, Sidebar, Footer)

**Deliverables**:
- ✅ Project initialized
- ✅ Routing configured
- ✅ API client ready
- ✅ Base layout working

---

### Phase 2: Data Generation Interface (Week 1-2)

**Page**: `/generate`

**Features**:
1. **Method Selection**:
   - Radio buttons: MVN, Bootstrap, Rules, LLM
   - Method descriptions and use cases

2. **Parameters Form**:
   - n_per_arm (subjects per arm)
   - target_effect (treatment effect)
   - seed (random seed)
   - Method-specific params (jitter_frac for Bootstrap, etc.)

3. **Generation**:
   - Submit button → POST to data generation service
   - Loading state with progress indicator
   - Success: Display generated data in table
   - Download options: CSV, JSON, Parquet

4. **Preview**:
   - Data table with pagination
   - Summary statistics
   - Distribution charts (histograms for SBP, DBP, HR, Temp)

**API Endpoints**:
- POST `/generate/mvn`
- POST `/generate/bootstrap`
- POST `/generate/rules`
- POST `/generate/llm`

**Components**:
- `MethodSelector.tsx`
- `GenerationForm.tsx`
- `DataPreviewTable.tsx`
- `DistributionCharts.tsx`

---

### Phase 3: Analytics Dashboards (Week 2-3)

#### 3.1 Demographics Analytics (`/analytics/demographics`)

**Features**:
1. **Baseline Characteristics (Table 1)**:
   - Age, Gender, Race, Ethnicity, BMI by treatment arm
   - P-values for balance tests
   - Cohen's d effect sizes

2. **Demographic Distributions**:
   - Age histogram with treatment arm overlay
   - Gender pie chart
   - Race/Ethnicity bar chart
   - BMI categories stacked bar chart

3. **Treatment Arm Balance**:
   - Visual balance indicators (green = balanced, red = imbalanced)
   - Standardized differences forest plot

**API Endpoints**:
- POST `/stats/demographics/baseline`
- POST `/stats/demographics/summary`
- POST `/stats/demographics/balance`

**Components**:
- `BaselineCharacteristicsTable.tsx`
- `DemographicDistributionCharts.tsx`
- `BalanceAssessment.tsx`

---

#### 3.2 Labs Analytics (`/analytics/labs`)

**Features**:
1. **Lab Summary Table**:
   - All lab tests with mean, median, SD, range
   - Filter by visit, treatment arm

2. **Abnormal Labs (CTCAE)**:
   - Table: Subject, Test, Value, Grade (1-4), Visit
   - Grade distribution bar chart
   - High-risk subjects (Grade 3-4) table

3. **Shift Tables**:
   - Baseline → Endpoint shift matrices
   - Heatmap visualization
   - Chi-square test results

4. **Safety Signals**:
   - 🚨 Hy's Law cases (CRITICAL)
   - ⚠️ Kidney decline (HIGH)
   - ⚠️ Bone marrow suppression (MEDIUM)
   - Signal counts and subject lists

5. **Longitudinal Trends**:
   - Line charts: Lab value over time by treatment arm
   - Slope, R², p-value annotations
   - Trend direction indicators

**API Endpoints**:
- POST `/stats/labs/summary`
- POST `/stats/labs/abnormal`
- POST `/stats/labs/shift-tables`
- POST `/stats/labs/safety-signals`
- POST `/stats/labs/longitudinal`

**Components**:
- `LabSummaryTable.tsx`
- `AbnormalLabsTable.tsx`
- `ShiftTableHeatmap.tsx`
- `SafetySignalsAlert.tsx`
- `LongitudinalTrendsChart.tsx`

---

#### 3.3 Adverse Events Analytics (`/analytics/ae`)

**Features**:
1. **AE Frequency Tables**:
   - By SOC: Table with AE count, subject count, incidence rate
   - By PT: Top 20 PTs with frequencies
   - By Severity: Mild, Moderate, Severe distribution
   - By Relationship: Related, Not Related, Possibly Related

2. **Treatment-Emergent AEs (TEAEs)**:
   - TEAE summary: Total, subjects with TEAEs, rate
   - Time-to-onset distribution (0-7d, 8-30d, 31-90d, >90d)
   - Median onset timeline visualization

3. **SOC Analysis**:
   - SOC ranking table
   - Top PTs within each SOC
   - Fisher's exact test: Odds ratio, p-value by treatment arm
   - Serious AEs by SOC

**API Endpoints**:
- POST `/stats/ae/summary`
- POST `/stats/ae/treatment-emergent`
- POST `/stats/ae/soc-analysis`

**Components**:
- `AEFrequencyTables.tsx`
- `TEAETimeline.tsx`
- `SOCRankingTable.tsx`

---

#### 3.4 Vitals Analytics (`/analytics/vitals`)

**Features**:
1. **Week-12 Efficacy**:
   - Treatment group statistics (Active vs Placebo)
   - Treatment effect with 95% CI
   - P-value, t-statistic
   - Interpretation: Significant/Not significant, effect size

2. **Distribution Comparison**:
   - Box plots: SBP, DBP, HR, Temp by treatment arm
   - Violin plots for distribution shape

3. **Longitudinal Trends**:
   - Line charts: Mean vitals over visits
   - Error bars (SE)
   - Treatment arms overlayed

**API Endpoints**:
- POST `/stats/week12`
- POST `/stats/recist` (for oncology)

**Components**:
- `EfficacyResultsTable.tsx`
- `VitalsDistributionCharts.tsx`
- `LongitudinalVitalsChart.tsx`

---

### Phase 4: Quality Assessment (Week 3)

#### 4.1 Quality Assessment (`/quality/assessment`)

**Features**:
1. **Upload Real + Synthetic Data**:
   - File upload: CSV/JSON
   - Or select from generated data

2. **Comprehensive Quality Metrics**:
   - Wasserstein distances (by column)
   - Correlation preservation score
   - RMSE by column
   - K-NN imputation score
   - Overall quality score with grade (A+ to F)

3. **Visualizations**:
   - PCA scatter plot (real vs synthetic)
   - Distribution comparison histograms
   - Quality score gauge

4. **Interpretation**:
   - Quality summary text
   - Recommendations for improvement

**API Endpoints**:
- POST `/quality/comprehensive`
- POST `/quality/pca-comparison`
- POST `/quality/demographics/compare`
- POST `/quality/labs/compare`
- POST `/quality/ae/compare`

**Components**:
- `FileUpload.tsx`
- `QualityMetricsTable.tsx`
- `PCAScatterPlot.tsx`
- `DistributionComparison.tsx`
- `QualityGauge.tsx`

---

### Phase 5: AACT Benchmarking (Week 4)

#### 5.1 AACT Benchmarking (`/aact/benchmark`)

**Features**:
1. **Study Comparison Form**:
   - n_subjects, indication, phase, treatment_effect
   - Submit → Compare with AACT

2. **Benchmark Results**:
   - Enrollment benchmark: Percentile, z-score, interpretation
   - Treatment effect benchmark: Percentile, z-score
   - Similarity score (0-1) with gauge
   - AACT reference data

3. **Demographics Benchmarking**:
   - Upload demographics data
   - Qualitative assessment vs industry norms

4. **AE Benchmarking**:
   - Upload AE data
   - Jaccard similarity with top AACT AEs
   - Frequency matching score

**API Endpoints**:
- POST `/aact/compare-study`
- POST `/aact/benchmark-demographics`
- POST `/aact/benchmark-ae`

**Components**:
- `AACTComparisonForm.tsx`
- `BenchmarkResults.tsx`
- `SimilarityGauge.tsx`

---

#### 5.2 Recommendations (`/aact/recommendations`)

**Features**:
1. **Current Status Input**:
   - current_quality, aact_similarity, generation_method
   - n_subjects, indication, phase

2. **Recommendations Display**:
   - Current status assessment (quality grade, AACT similarity)
   - Improvement opportunities (priority, issue, impact)
   - Parameter recommendations (current vs recommended)
   - Method recommendations (alternative methods)
   - Expected improvements (quality, AACT)

3. **Visualizations**:
   - Priority badges (HIGH/MEDIUM/LOW)
   - Before/After quality comparison
   - Improvement roadmap

**API Endpoints**:
- POST `/study/recommendations`

**Components**:
- `RecommendationsForm.tsx`
- `ImprovementOpportunities.tsx`
- `ParameterRecommendations.tsx`
- `ExpectedImprovements.tsx`

---

### Phase 6: Study Analytics (Week 4-5)

#### 6.1 Comprehensive Summary (`/study/summary`)

**Features**:
1. **Upload All Domains**:
   - Demographics, Vitals, Labs, AEs
   - Indication, Phase

2. **Study Overview**:
   - Total subjects, data domains available
   - Data completeness pie chart

3. **Summary Cards**:
   - Demographics: Age, gender, treatment arms, balance
   - Efficacy: Primary endpoint, treatment effect
   - Safety: Labs abnormalities, AEs, SAEs
   - AACT: Similarity score, percentiles
   - Quality: Completeness, regulatory readiness

4. **Regulatory Readiness**:
   - Requirements checklist (Table 1, efficacy, safety, AACT)
   - Readiness score gauge
   - Status: SUBMISSION READY / NEAR READY / IN PROGRESS / NOT READY

**API Endpoints**:
- POST `/study/comprehensive-summary`

**Components**:
- `StudyOverview.tsx`
- `SummaryCards.tsx`
- `RegulatoryReadiness.tsx`

---

#### 6.2 Cross-Domain Correlations (`/study/correlations`)

**Features**:
1. **Correlation Heatmap**:
   - Demographics vs Vitals
   - Demographics vs AE
   - Labs vs AE
   - Vitals vs Labs

2. **Statistical Tests Results**:
   - Pearson correlations (r, p-value)
   - T-tests (t-statistic, p-value)
   - Mann-Whitney U (U-statistic, p-value)

3. **Clinical Insights**:
   - List of key findings
   - Significance flags
   - Interpretation text

**API Endpoints**:
- POST `/study/cross-domain-correlations`

**Components**:
- `CorrelationHeatmap.tsx`
- `StatisticalTestsTable.tsx`
- `ClinicalInsights.tsx`

---

#### 6.3 Executive Dashboard (`/study/dashboard`)

**Features**:
1. **KPI Cards**:
   - Total subjects enrolled
   - Data completeness (X/4 domains)
   - Overall quality score
   - AACT similarity

2. **Enrollment Status**:
   - By treatment arm (Active vs Placebo)
   - Randomization balance indicator

3. **Efficacy Metrics**:
   - Primary endpoint visit
   - Mean SBP by arm
   - Treatment effect with assessment (STRONG/MODERATE/WEAK)

4. **Safety Metrics**:
   - Total AEs, SAEs
   - AE rate, SAE rate
   - Top 5 AEs
   - Safety signals (Hy's Law, kidney, bone marrow)

5. **Risk Flags**:
   - Table: Severity (CRITICAL/HIGH/MEDIUM), Category, Issue, Recommendation
   - Color-coded badges

**API Endpoints**:
- POST `/study/trial-dashboard`

**Components**:
- `KPICards.tsx`
- `EnrollmentStatus.tsx`
- `EfficacyMetrics.tsx`
- `SafetyMetrics.tsx`
- `RiskFlags.tsx`

---

### Phase 7: Performance Benchmarking (Week 5)

#### 7.1 Method Comparison (`/benchmark/performance`)

**Features**:
1. **Methods Input**:
   - Input performance data for MVN, Bootstrap, Rules, LLM
   - Records/second, quality score, AACT similarity, memory MB

2. **Comparison Table**:
   - All metrics side-by-side
   - Overall score ranking

3. **Recommendations**:
   - For speed, quality, realism, balanced
   - Use case recommendations

4. **Tradeoffs**:
   - Speed vs Quality scatter plot
   - Pareto frontier

**API Endpoints**:
- POST `/benchmark/performance`

**Components**:
- `MethodComparisonForm.tsx`
- `PerformanceTable.tsx`
- `TradeoffsChart.tsx`

---

#### 7.2 Quality Aggregation (`/benchmark/quality-scores`)

**Features**:
1. **Domain Scores Input**:
   - Demographics, Vitals, Labs, AE, AACT quality scores

2. **Aggregate Results**:
   - Overall quality score with grade
   - Domain breakdown table
   - Completeness indicator

3. **Interpretation**:
   - Quality status (Excellent/Good/Fair/Poor)
   - Strengths and weaknesses
   - Recommendations

**API Endpoints**:
- POST `/benchmark/quality-scores`

**Components**:
- `QualityAggregationForm.tsx`
- `AggregateResults.tsx`
- `QualityBreakdown.tsx`

---

## 🔐 Authentication & Security

**Note**: Backend security service exists but authentication can be added later.

**For MVP**:
- No authentication (development mode)
- Hardcoded API base URL

**For Production**:
- JWT authentication with login page
- Token stored in localStorage
- Axios interceptor to add Bearer token
- Protected routes with authentication guard
- Session timeout

---

## 📊 Data Visualization Library Choices

### Charts
**Recharts** - Chosen for:
- Native React components
- TypeScript support
- Good documentation
- Covers 90% of use cases

**Chart Types**:
- Line charts: Longitudinal trends
- Bar charts: Frequencies, comparisons
- Scatter plots: PCA, correlations
- Pie charts: Demographics distributions
- Box plots: Distribution comparisons
- Heatmaps: Shift tables, correlations
- Gauge charts: Quality scores

### Tables
**TanStack Table (React Table v8)** - Chosen for:
- Headless UI (bring your own markup)
- Sorting, filtering, pagination built-in
- TypeScript support
- Excellent performance

---

## 🧪 Testing Strategy

### Unit Tests
- **Vitest**: Component unit tests
- **React Testing Library**: Component integration tests

### E2E Tests
- **Playwright**: End-to-end user flows

### Coverage Target
- Components: 80%
- API calls: 90%
- Utils: 95%

---

## 🚀 Deployment

### Development
```bash
npm run dev
# Runs on http://localhost:5173
```

### Production Build
```bash
npm run build
# Output: dist/
```

### Deployment Options
- **Vercel**: Recommended for React apps
- **Netlify**: Alternative static hosting
- **Docker**: Containerized deployment
- **AWS S3 + CloudFront**: CDN hosting

---

## 📋 Implementation Checklist

### Phase 1: Setup ✅ (Week 1)
- [ ] Initialize Vite + React + TypeScript
- [ ] Install dependencies
- [ ] Configure Tailwind CSS
- [ ] Set up folder structure
- [ ] Create API client
- [ ] Configure React Query
- [ ] Set up routing
- [ ] Create base layout

### Phase 2: Generation (Week 1-2)
- [ ] Method selector component
- [ ] Generation form
- [ ] Data preview table
- [ ] Distribution charts
- [ ] Download functionality

### Phase 3: Analytics (Week 2-3)
- [ ] Demographics page
- [ ] Labs page
- [ ] AE page
- [ ] Vitals page

### Phase 4: Quality (Week 3)
- [ ] Quality assessment page
- [ ] Quality comparison page

### Phase 5: AACT (Week 4)
- [ ] Benchmarking page
- [ ] Recommendations page

### Phase 6: Study (Week 4-5)
- [ ] Comprehensive summary page
- [ ] Cross-domain correlations page
- [ ] Executive dashboard page

### Phase 7: Benchmarking (Week 5)
- [ ] Method comparison page
- [ ] Quality aggregation page

---

## 🎯 Success Criteria

### Functional
✅ All 26 backend endpoints integrated
✅ Data generation working with all 4 methods
✅ Analytics dashboards displaying results correctly
✅ Quality assessment with visualizations
✅ AACT benchmarking functional
✅ Study analytics comprehensive

### Non-Functional
✅ Responsive design (mobile, tablet, desktop)
✅ <2s page load time
✅ Accessibility (WCAG 2.1 AA)
✅ Cross-browser compatibility (Chrome, Firefox, Safari, Edge)

### User Experience
✅ Intuitive navigation
✅ Clear error messages
✅ Loading states for async operations
✅ Data export functionality
✅ Help tooltips for complex features

---

## 📝 Next Steps

1. **Review this plan** with stakeholders
2. **Set up development environment**
3. **Start Phase 1: Project Setup**
4. **Iterate on UI/UX** based on feedback
5. **Deploy MVP** after Phase 3-4
6. **Full production release** after Phase 7

---

**Estimated Timeline**: 5 weeks (with 1 developer)
**Tech Stack**: React + TypeScript + Tailwind + Recharts
**Backend**: Analytics Service v1.6.0 (26 endpoints)
**Status**: READY TO START IMPLEMENTATION 🚀

---

*Plan Created*: 2025-11-20
*Author*: Claude
*Version*: 1.0
