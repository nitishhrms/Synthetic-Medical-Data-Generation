# Frontend-Backend Integration Status

**Date**: 2025-11-13
**Status**: 🚧 **In Progress** - Core functionality being connected

---

## ✅ Completed Integrations

### 1. Authentication ✅
- [x] User registration (`POST /auth/register`)
- [x] User login (`POST /auth/login`)
- [x] Token storage in localStorage
- [x] Auto-login after registration
- [x] Logout functionality
- [x] Fallback user object when `/auth/me` fails

### 2. Data Generation ✅
- [x] MVN generation (`POST /generate/mvn`)
- [x] Bootstrap generation (`POST /generate/bootstrap` with pilot data)
- [x] Rules generation (`POST /generate/rules`)
- [x] LLM generation (`POST /generate/llm`)
- [x] Response format normalization
- [x] Data display in table
- [x] CSV download functionality

### 3. Styling & UX ✅
- [x] Material Design 3 implementation
- [x] Colorful navigation sidebar with gradients
- [x] Enhanced top app bar
- [x] Vibrant dashboard cards
- [x] Hover effects and animations
- [x] Responsive layout

---

## 🚧 Needs Integration

### 3. Analytics Page ⚠️
**Current Status**: Placeholder page, not functional

**Needs**:
- [ ] Connect to Week-12 statistics endpoint
- [ ] Display treatment effect analysis
- [ ] Show statistical significance
- [ ] Add quality assessment charts
- [ ] Connect PCA comparison endpoint
- [ ] Display comprehensive quality metrics

**Required Endpoints**:
- `POST /stats/week12` - Efficacy analysis
- `POST /quality/comprehensive` - Quality metrics
- `POST /quality/pca-comparison` - PCA visualization

### 4. Quality Page ⚠️
**Current Status**: Identical to Analytics page

**Needs**:
- [ ] Create separate Quality screen
- [ ] Data validation interface
- [ ] Quality checks display
- [ ] Edit checks rules
- [ ] Validation results visualization

**Required Endpoints**:
- `POST /checks/validate` - Validate vitals data
- `GET /checks/rules` - Get validation rules

### 5. Studies Page ⚠️
**Current Status**: Placeholder, not functional

**Needs**:
- [ ] List all studies
- [ ] Create new study form
- [ ] View study details
- [ ] Enroll subjects
- [ ] Import synthetic data to study

**Required Endpoints**:
- `GET /studies` - List studies
- `POST /studies` - Create study
- `GET /studies/{id}` - Get study details
- `POST /subjects` - Enroll subject
- `POST /import/synthetic` - Import data

### 6. Dashboard Buttons ⚠️
**Current Status**: Static, don't navigate

**Needs**:
- [ ] Wire "Generate Synthetic Data" to navigate to Generate screen
- [ ] Wire "Run Quality Assessment" to navigate to Quality screen
- [ ] Wire "View Analytics" to navigate to Analytics screen
- [ ] Make stat cards clickable

---

## 📋 Detailed Integration Tasks

### Priority 1: Make Analytics Functional

**File**: `frontend/src/components/screens/Analytics.tsx`

**Current Code**: Placeholder

**Needed Implementation**:
```typescript
import { analyticsApi } from "@/services/api";

export function Analytics() {
  const [vitalsData, setVitalsData] = useState<VitalsRecord[]>([]);
  const [statistics, setStatistics] = useState<Week12StatsResponse | null>(null);
  const [qualityMetrics, setQualityMetrics] = useState<QualityAssessmentResponse | null>(null);

  const runAnalysis = async () => {
    // Get generated data from somewhere (context, props, or generate fresh)
    const stats = await analyticsApi.getWeek12Stats({ vitals_data: vitalsData });
    setStatistics(stats);

    // Get pilot data for comparison
    const pilotData = await dataGenerationApi.getPilotData();
    const quality = await analyticsApi.comprehensiveQuality(pilotData, vitalsData);
    setQualityMetrics(quality);
  };

  return (
    // Display statistics, charts, quality metrics
  );
}
```

**Required Charts**:
- Treatment effect bar chart (Active vs Placebo)
- Box plots for BP distribution
- Quality score gauge
- PCA scatter plot (original vs synthetic)

---

### Priority 2: Create Quality Screen

**File**: `frontend/src/components/screens/Quality.tsx`

**Create New File** (currently using Analytics.tsx)

**Implementation**:
```typescript
import { qualityApi } from "@/services/api";

export function Quality() {
  const [data, setData] = useState<VitalsRecord[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResponse | null>(null);

  const validateData = async () => {
    const results = await qualityApi.validateVitals(data);
    setValidationResults(results);
  };

  return (
    // Upload data or select generated data
    // Run validation
    // Display validation results with pass/fail indicators
    // Show edit check rules
  );
}
```

---

### Priority 3: Wire Dashboard Actions

**File**: `frontend/src/components/screens/Dashboard.tsx`

**Current**: Quick action buttons don't do anything

**Fix**:
```typescript
export function Dashboard({ onNavigate }: { onNavigate: (screen: Screen) => void }) {
  return (
    <div onClick={() => onNavigate("generate")}>
      <Activity className="h-5 w-5 text-primary" />
      <p>Generate Synthetic Data</p>
    </div>
  );
}
```

**In App.tsx**:
```typescript
<Dashboard onNavigate={setActiveScreen} />
```

---

### Priority 4: Studies Management

**File**: `frontend/src/components/screens/Studies.tsx`

**Current**: Shows "Coming Soon" message

**Implementation**:
```typescript
export function Studies() {
  const [studies, setStudies] = useState<Study[]>([]);
  const [showCreateForm, setShowCreateForm] = useState(false);

  const loadStudies = async () => {
    const response = await edcApi.listStudies();
    setStudies(response.studies);
  };

  const createStudy = async (studyData: StudyCreate) => {
    await edcApi.createStudy(studyData);
    loadStudies();
  };

  return (
    // List of studies
    // "Create New Study" button
    // Create study form modal
    // Study detail cards
  );
}
```

---

## 🔄 Data Flow Architecture

### Current Working Flow:
```
Login → Authentication → Dashboard → Generate Data → Display Results → Download CSV
```

### Target Complete Flow:
```
Login
  ↓
Dashboard (Stats Overview)
  ↓
  ├─→ Generate Data
  │     ↓
  │   Display Generated Data
  │     ↓
  │   Download or Import to Study
  │
  ├─→ Analytics
  │     ↓
  │   Select Generated/Study Data
  │     ↓
  │   Run Week-12 Analysis
  │     ↓
  │   Display Statistics & Charts
  │     ↓
  │   Run Quality Assessment
  │     ↓
  │   Show Quality Scores & PCA
  │
  ├─→ Quality
  │     ↓
  │   Upload/Select Data
  │     ↓
  │   Run Validation
  │     ↓
  │   Display Pass/Fail Results
  │
  └─→ Studies
        ↓
      List All Studies
        ↓
      Create New Study
        ↓
      View Study Details
        ↓
      Import Generated Data
        ↓
      View Enrolled Subjects
```

---

## 🎯 Implementation Plan

### Phase 1: Data Flow (2-3 hours)
1. Add global state management (Context API or Zustand)
2. Store generated data in state
3. Pass data between screens
4. Wire dashboard navigation

### Phase 2: Analytics Integration (3-4 hours)
1. Implement Week-12 stats API call
2. Create charts (Recharts or Chart.js)
3. Add quality metrics display
4. Implement PCA comparison

### Phase 3: Quality Screen (2-3 hours)
1. Create separate Quality component
2. Implement validation API call
3. Display validation results
4. Show edit check rules

### Phase 4: Studies Management (3-4 hours)
1. List studies from backend
2. Create study form
3. Study detail view
4. Subject enrollment
5. Import synthetic data workflow

### Phase 5: Polish & Testing (2-3 hours)
1. Error handling
2. Loading states
3. Success messages
4. E2E testing
5. Bug fixes

---

## 🚀 Quick Wins (Do These First!)

1. **Wire Dashboard Navigation** (15 minutes)
   - Make Quick Actions clickable
   - Navigate to respective screens

2. **Show Generated Data Count** (10 minutes)
   - Update "Generated Records" stat when data is generated
   - Store count in localStorage or state

3. **Add Loading States** (20 minutes)
   - Show spinners during API calls
   - Disable buttons while loading

4. **Error Messages** (15 minutes)
   - Display user-friendly errors
   - Show which endpoint failed

---

## 📦 Recommended State Management

**Option 1: Context API** (Simpler, built-in)
```typescript
// Create DataContext.tsx
export const DataContext = createContext({
  generatedData: null,
  setGeneratedData: () => {},
  statistics: null,
  setStatistics: () => {},
});

// Wrap app in provider
<DataProvider>
  <App />
</DataProvider>
```

**Option 2: Zustand** (More powerful, easier to use)
```typescript
// Create store.ts
import create from 'zustand';

export const useDataStore = create((set) => ({
  generatedData: null,
  setGeneratedData: (data) => set({ generatedData: data }),
  statistics: null,
  setStatistics: (stats) => set({ statistics: stats }),
}));
```

---

## 📊 Current vs Target State

| Feature | Current | Target |
|---------|---------|--------|
| Authentication | ✅ Working | ✅ Working |
| Data Generation | ✅ Working | ✅ Working |
| Data Display | ✅ Working | ✅ Working |
| CSV Download | ✅ Working | ✅ Working |
| Analytics | ❌ Placeholder | ✅ Functional |
| Quality | ❌ Same as Analytics | ✅ Separate & Functional |
| Studies | ❌ Placeholder | ✅ CRUD Operations |
| Dashboard Nav | ❌ Static | ✅ Interactive |
| Data Persistence | ❌ Lost on refresh | ✅ Stored in state |

---

## 🐛 Known Issues

1. **Bootstrap generation** - Now fixed, fetches pilot data first
2. **API response format** - Now normalized in API layer
3. **Analytics/Quality identical** - Needs separate implementations
4. **Dashboard buttons static** - Needs navigation wiring
5. **No state management** - Data lost between screens

---

## 📝 Next Steps

**Immediate** (Can do right now):
1. Wire dashboard navigation
2. Add generated data counter
3. Test data generation endpoints

**Short-term** (Next 1-2 hours):
1. Implement Analytics screen with Week-12 stats
2. Create separate Quality screen
3. Add state management

**Medium-term** (Next 3-4 hours):
1. Studies management
2. Charts and visualizations
3. Quality metrics

---

**Status**: Ready to continue integration!
**Blockers**: None - all backend endpoints are working
**Next**: User decision on prioritization
