# 🎯 Implementation Roadmap: Make Project Industry-Grade

**Date**: 2025-11-17
**Goal**: Transform current prototype into industry-grade clinical trial platform
**Timeline**: 6-8 weeks (realistic for class project)

---

## 🚨 CRITICAL GAPS IDENTIFIED

### **1. Missing Core EDC Features**
- ❌ **Form Builder** (CRF Designer) - Users can't create custom forms
- ❌ **Query Management** - No workflow for data clarification
- ❌ **RBQM Dashboard** - No site performance monitoring

### **2. Limited Data Model**
Current parameters (only 4):
- SystolicBP, DiastolicBP, HeartRate, Temperature

**Missing critical domains**:
- ❌ Demographics (age, gender, race, ethnicity)
- ❌ Laboratory values (CBC, liver enzymes, kidney function)
- ❌ Adverse Events (severity, relationship, outcome)
- ❌ Medications (concomitant meds, dose, frequency)
- ❌ Medical history (prior conditions, surgeries)

### **3. Missing ML Core**
- ❌ **GAIN** (Generative Adversarial Imputation Networks)
- ❌ **GANs** (Conditional GANs for synthetic generation)

Currently using: MVN, Bootstrap, Rules, LLM (none are GANs!)

---

## 📋 IMPLEMENTATION PLAN (Priority Order)

### **Phase 1: Expand Data Model** (Week 1-2) - CRITICAL
*Without realistic data, form builder and GAIN have nothing to work with*

#### **1.1 Demographics Domain** (3 days)
```python
# New table: demographics
class Demographics(BaseModel):
    subject_id: str
    age: int                    # 18-75 years
    gender: str                 # Male, Female, Other
    race: str                   # White, Black, Asian, Other
    ethnicity: str              # Hispanic/Latino, Not Hispanic/Latino
    height_cm: float            # 150-200 cm
    weight_kg: float            # 50-150 kg
    bmi: float                  # Calculated: weight / (height/100)^2
    smoking_status: str         # Never, Former, Current
```

**Implementation**:
- Create database table
- Add API endpoints (POST /demographics, GET /demographics/{subject_id})
- Update synthetic generators to include demographics

#### **1.2 Laboratory Values Domain** (4 days)
```python
# New table: laboratory_results
class LabResult(BaseModel):
    subject_id: str
    visit_name: str
    test_date: datetime

    # Hematology (Complete Blood Count)
    hemoglobin: float           # 12-18 g/dL
    hematocrit: float           # 36-50%
    wbc: float                  # 4-11 K/μL (white blood cells)
    platelets: float            # 150-400 K/μL

    # Chemistry (Metabolic Panel)
    glucose: float              # 70-100 mg/dL (fasting)
    creatinine: float           # 0.7-1.3 mg/dL (kidney function)
    bun: float                  # 7-20 mg/dL (blood urea nitrogen)
    alt: float                  # 7-56 U/L (liver enzyme)
    ast: float                  # 10-40 U/L (liver enzyme)
    bilirubin: float            # 0.3-1.2 mg/dL

    # Lipids
    total_cholesterol: float    # <200 mg/dL
    ldl: float                  # <100 mg/dL (bad cholesterol)
    hdl: float                  # >40 mg/dL (good cholesterol)
    triglycerides: float        # <150 mg/dL
```

**Implementation**:
- Create database table
- Add API endpoints
- Add lab-specific validation rules
- Update synthetic generators

#### **1.3 Adverse Events Domain** (3 days)
```python
# New table: adverse_events
class AdverseEvent(BaseModel):
    ae_id: str
    subject_id: str
    event_term: str             # "Headache", "Nausea", "Hypertensive Crisis"
    severity: str               # Mild, Moderate, Severe, Life-threatening
    onset_date: datetime
    resolution_date: Optional[datetime]
    outcome: str                # Recovered, Recovering, Not Recovered, Fatal
    relationship: str           # Not Related, Unlikely, Possibly, Probably, Definitely
    action_taken: str           # None, Dose Reduced, Drug Interrupted, Drug Withdrawn
    serious: bool               # True if SAE (Serious Adverse Event)

    # SAE criteria (if serious=True)
    sae_death: bool = False
    sae_life_threatening: bool = False
    sae_hospitalization: bool = False
    sae_disability: bool = False
```

**Implementation**:
- Create database table
- Add API endpoints
- Add AE-specific validation
- Generate realistic AE data (use probability distributions)

#### **1.4 Medications Domain** (2 days)
```python
# New table: concomitant_medications
class Medication(BaseModel):
    med_id: str
    subject_id: str
    medication_name: str        # "Metformin", "Lisinopril", "Aspirin"
    indication: str             # "Diabetes", "Hypertension"
    dose: str                   # "500 mg"
    frequency: str              # "Twice daily", "Once daily"
    route: str                  # "Oral", "IV", "Subcutaneous"
    start_date: datetime
    end_date: Optional[datetime]
    ongoing: bool
```

**Implementation**:
- Create database table
- Add API endpoints
- Common medication library (top 50 drugs in hypertension trials)

---

### **Phase 2: Implement Form Builder** (Week 3) - HIGH PRIORITY

#### **2.1 Form Definition System** (4 days)

**Form Schema Structure**:
```json
{
  "form_id": "VITALS_V1",
  "form_name": "Vital Signs",
  "version": "1.0",
  "visit_applicable": ["Screening", "Day 1", "Week 4", "Week 12"],
  "fields": [
    {
      "field_id": "systolic_bp",
      "field_label": "Systolic Blood Pressure (mmHg)",
      "field_type": "number",
      "required": true,
      "validation": {
        "min": 95,
        "max": 200,
        "type": "range"
      }
    },
    {
      "field_id": "diastolic_bp",
      "field_label": "Diastolic Blood Pressure (mmHg)",
      "field_type": "number",
      "required": true,
      "validation": {
        "min": 55,
        "max": 130,
        "type": "range"
      }
    }
  ],
  "edit_checks": [
    {
      "check_id": "BP_DIFFERENTIAL",
      "check_type": "logical",
      "expression": "systolic_bp > diastolic_bp",
      "error_message": "Systolic BP must be greater than Diastolic BP",
      "severity": "error"
    }
  ]
}
```

**Database Schema**:
```sql
-- Store form definitions
CREATE TABLE form_definitions (
    form_id VARCHAR(50) PRIMARY KEY,
    form_name VARCHAR(255),
    version VARCHAR(20),
    form_schema JSONB,  -- Store entire form structure
    status VARCHAR(20),  -- draft, active, archived
    created_at TIMESTAMP,
    created_by INTEGER
);

-- Store form data (generic)
CREATE TABLE form_data (
    data_id SERIAL PRIMARY KEY,
    form_id VARCHAR(50),
    subject_id VARCHAR(50),
    visit_name VARCHAR(50),
    form_data JSONB,  -- Actual field values
    status VARCHAR(20),  -- draft, submitted, locked
    submitted_at TIMESTAMP,
    submitted_by INTEGER
);
```

**API Endpoints**:
```python
POST /forms/definitions          # Create new form definition
GET /forms/definitions           # List all forms
GET /forms/definitions/{form_id} # Get form schema
PUT /forms/definitions/{form_id} # Update form (version control)

POST /forms/data                 # Submit form data
GET /forms/data/{subject_id}     # Get all forms for subject
PUT /forms/data/{data_id}        # Update form data (if not locked)
```

#### **2.2 Form Builder UI** (3 days)

**React Components**:
```tsx
// FormBuilder.tsx - Drag-and-drop form designer
interface FormBuilderProps {
  onSave: (formDefinition: FormDefinition) => void;
}

// Field Types Available:
const FIELD_TYPES = [
  { type: 'text', label: 'Text Input' },
  { type: 'number', label: 'Numeric' },
  { type: 'date', label: 'Date' },
  { type: 'dropdown', label: 'Dropdown' },
  { type: 'checkbox', label: 'Checkbox' },
  { type: 'radio', label: 'Radio Buttons' },
];

// Edit Check Builder:
const EDIT_CHECK_TYPES = [
  { type: 'range', label: 'Range Check (min-max)' },
  { type: 'logical', label: 'Logical Check (field1 > field2)' },
  { type: 'required', label: 'Required Field' },
  { type: 'cross-form', label: 'Cross-Form Check' },
];
```

**Features**:
- Drag-and-drop field placement
- Configure validation rules (range, required, logical)
- Define edit checks
- Preview form before publishing
- Version control (can't edit published forms, must create new version)

---

### **Phase 3: Implement Query Management** (Week 4) - HIGH PRIORITY

#### **3.1 Query System** (5 days)

**Database Schema**:
```sql
CREATE TABLE queries (
    query_id SERIAL PRIMARY KEY,
    subject_id VARCHAR(50),
    form_id VARCHAR(50),
    field_id VARCHAR(50),
    query_type VARCHAR(50),  -- auto, manual
    query_text TEXT,
    severity VARCHAR(20),    -- info, warning, critical
    status VARCHAR(20),      -- open, answered, closed, cancelled

    -- Who and when
    opened_by INTEGER,
    opened_at TIMESTAMP,
    assigned_to INTEGER,     -- CRC who needs to respond

    -- Response tracking
    response_text TEXT,
    responded_by INTEGER,
    responded_at TIMESTAMP,

    -- Resolution
    resolved_by INTEGER,
    resolved_at TIMESTAMP,
    resolution_notes TEXT
);

CREATE TABLE query_history (
    history_id SERIAL PRIMARY KEY,
    query_id INTEGER,
    action VARCHAR(50),      -- opened, answered, closed, escalated
    action_by INTEGER,
    action_at TIMESTAMP,
    notes TEXT
);
```

**Query Types**:
```python
# Auto-queries (system generated)
class AutoQuery:
    RANGE_VIOLATION = "Value {value} outside range [{min}-{max}]"
    MISSING_REQUIRED = "Required field '{field}' is missing"
    LOGICAL_FAIL = "Check failed: {expression}"
    OUTLIER = "Value is 3+ standard deviations from mean"

# Manual queries (data manager creates)
class ManualQuery:
    CLARIFICATION = "Please clarify the value"
    VERIFICATION = "Please verify this value against source"
    INCONSISTENCY = "Value inconsistent with {other_field}"
```

**API Endpoints**:
```python
POST /queries                    # Create manual query
GET /queries                     # List all queries (filter by status, subject, site)
GET /queries/{query_id}          # Get query details
PUT /queries/{query_id}/respond  # CRC responds to query
PUT /queries/{query_id}/close    # Data manager closes query
GET /queries/stats               # Query metrics (for RBQM)
```

**Workflow**:
```
1. Auto-Query Generation:
   User submits form → Validation runs → If fails, auto-create query

2. Manual Query Creation:
   Data Manager reviews data → Sees outlier → Creates manual query

3. Query Response:
   CRC receives notification → Checks source data → Responds

4. Query Resolution:
   Data Manager reviews response → Closes or escalates
```

#### **3.2 Query UI** (2 days)

**CRC View** (Respond to queries):
```tsx
// QueryList.tsx - Shows all queries for CRC's site
interface Query {
  query_id: number;
  subject_id: string;
  field_label: string;
  query_text: string;
  severity: 'info' | 'warning' | 'critical';
  status: 'open' | 'answered' | 'closed';
}

// QueryResponse.tsx - Form to respond
interface QueryResponseProps {
  query: Query;
  onRespond: (response: string) => void;
}
```

**Data Manager View** (Review and close):
```tsx
// QueryDashboard.tsx - Overview of all queries
interface QueryMetrics {
  total_open: number;
  total_answered: number;
  avg_response_time_hours: number;
  queries_by_site: { site_id: string; count: number }[];
}
```

---

### **Phase 4: Implement RBQM Dashboard** (Week 5) - HIGH PRIORITY

#### **4.1 RBQM Metrics Calculation** (3 days)

**Key Risk Indicators (KRIs)**:
```python
class RBQMMetrics:
    # Query Metrics
    query_rate: float           # Queries per 100 CRFs
    query_response_time: float  # Hours to respond
    query_closure_time: float   # Hours to close

    # Data Quality Metrics
    missing_data_rate: float    # % of required fields missing
    out_of_range_rate: float    # % of values outside ranges
    protocol_deviation_rate: float

    # Timeliness Metrics
    data_entry_lag: float       # Days between visit and data entry
    visit_compliance_rate: float # % of visits within window

    # Site Performance
    enrollment_rate: float      # Subjects per month
    dropout_rate: float         # % subjects withdrawn
    ae_reporting_rate: float    # AEs per subject

    # Risk Score
    overall_risk_score: float   # 0-100 (weighted composite)
    risk_level: str             # low, medium, high, critical
```

**Calculation Service**:
```python
# microservices/rbqm-service/src/metrics.py

async def calculate_site_metrics(site_id: str, study_id: str) -> SiteMetrics:
    """Calculate RBQM metrics for a site"""

    # Get all queries for site
    queries = await db.fetch_all(
        "SELECT * FROM queries WHERE site_id = $1 AND study_id = $2",
        site_id, study_id
    )

    # Calculate query rate
    total_forms = await db.fetchval(
        "SELECT COUNT(*) FROM form_data WHERE site_id = $1",
        site_id
    )
    query_rate = (len(queries) / total_forms) * 100 if total_forms > 0 else 0

    # Calculate response time
    answered_queries = [q for q in queries if q['status'] == 'answered']
    if answered_queries:
        response_times = [
            (q['responded_at'] - q['opened_at']).total_seconds() / 3600
            for q in answered_queries
        ]
        avg_response_time = sum(response_times) / len(response_times)
    else:
        avg_response_time = 0

    # Missing data rate
    all_data = await db.fetch_all(
        "SELECT form_data FROM form_data WHERE site_id = $1",
        site_id
    )
    missing_count = sum(
        1 for data in all_data
        if has_missing_required_fields(data['form_data'])
    )
    missing_rate = (missing_count / len(all_data)) * 100 if all_data else 0

    # Risk score (weighted)
    risk_score = calculate_risk_score({
        'query_rate': query_rate,
        'response_time': avg_response_time,
        'missing_rate': missing_rate,
        # ... other metrics
    })

    return SiteMetrics(
        site_id=site_id,
        query_rate=query_rate,
        avg_response_time=avg_response_time,
        missing_data_rate=missing_rate,
        risk_score=risk_score,
        risk_level=classify_risk(risk_score)
    )
```

#### **4.2 RBQM Dashboard UI** (4 days)

**Dashboard Components**:
```tsx
// RBQMDashboard.tsx - Main dashboard

interface RBQMDashboardProps {
  study_id: string;
}

const RBQMDashboard = ({ study_id }: RBQMDashboardProps) => {
  return (
    <div>
      {/* Study-Level Metrics */}
      <StudyOverview metrics={studyMetrics} />

      {/* Site Comparison Table */}
      <SiteComparisonTable sites={siteMetrics} />

      {/* Risk Heatmap */}
      <RiskHeatmap sites={siteMetrics} />

      {/* Trending Charts */}
      <TrendingCharts metrics={historicalMetrics} />

      {/* Alerts */}
      <AlertsPanel alerts={activeAlerts} />
    </div>
  );
};
```

**Site Comparison Table**:
```
┌────────┬───────────┬──────────┬─────────────┬────────────┬──────────┐
│ Site   │ Query     │ Response │ Missing     │ Enrollment │ Risk     │
│ ID     │ Rate      │ Time (h) │ Data (%)    │ Rate       │ Level    │
├────────┼───────────┼──────────┼─────────────┼────────────┼──────────┤
│ Site001│ 4.2       │ 12.3     │ 1.5         │ 2.5/month  │ Low      │
│ Site002│ 12.8 ⚠️   │ 48.7 ⚠️  │ 8.2 ⚠️      │ 1.2/month  │ High ⚠️  │
│ Site003│ 3.1       │ 8.5      │ 0.8         │ 3.1/month  │ Low      │
│ Site004│ 15.2 🔴   │ 72.4 🔴  │ 12.4 🔴     │ 0.8/month  │Critical🔴│
└────────┴───────────┴──────────┴─────────────┴────────────┴──────────┘

🟢 Low Risk    │ 🟡 Medium Risk │ ⚠️  High Risk   │ 🔴 Critical Risk
```

**Risk Heatmap** (Visual):
```tsx
// RiskHeatmap.tsx
const RiskHeatmap = ({ sites }) => {
  // Color code: Green (low), Yellow (medium), Orange (high), Red (critical)
  return (
    <div className="grid grid-cols-4 gap-2">
      {sites.map(site => (
        <div
          key={site.site_id}
          className={`p-4 rounded ${getRiskColor(site.risk_level)}`}
        >
          <h3>{site.site_id}</h3>
          <div>Risk: {site.risk_score}/100</div>
        </div>
      ))}
    </div>
  );
};
```

---

### **Phase 5: Implement GAIN** (Week 6-7) - RESEARCH CORE

#### **5.1 GAIN Architecture** (5 days)

**GAIN Overview**:
- **Generator (G)**: Imputes missing values
- **Discriminator (D)**: Distinguishes real vs imputed
- **Hint Matrix (H)**: Provides hints to discriminator

**Implementation** (PyTorch):
```python
# microservices/gain-service/src/gain_model.py

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np

class Generator(nn.Module):
    """GAIN Generator - Imputes missing values"""
    def __init__(self, dim, h_dim):
        super(Generator, self).__init__()
        self.fc1 = nn.Linear(dim * 2, h_dim)  # Input: data + mask
        self.fc2 = nn.Linear(h_dim, h_dim)
        self.fc3 = nn.Linear(h_dim, dim)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, m):
        """
        x: Data with missing values (NaNs replaced with 0)
        m: Mask (1 = observed, 0 = missing)
        """
        inputs = torch.cat([x, m], dim=1)
        h = self.relu(self.fc1(inputs))
        h = self.relu(self.fc2(h))
        out = self.sigmoid(self.fc3(h))
        return out

class Discriminator(nn.Module):
    """GAIN Discriminator - Distinguishes real vs imputed"""
    def __init__(self, dim, h_dim):
        super(Discriminator, self).__init__()
        self.fc1 = nn.Linear(dim * 2, h_dim)  # Input: data + hint
        self.fc2 = nn.Linear(h_dim, h_dim)
        self.fc3 = nn.Linear(h_dim, dim)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, h):
        """
        x: Imputed data
        h: Hint matrix
        """
        inputs = torch.cat([x, h], dim=1)
        h = self.relu(self.fc1(inputs))
        h = self.relu(self.fc2(h))
        out = self.sigmoid(self.fc3(h))
        return out

class GAIN:
    """GAIN Model for Missing Data Imputation"""
    def __init__(self, dim, h_dim=256, alpha=100):
        self.dim = dim
        self.alpha = alpha  # Hint rate parameter

        self.generator = Generator(dim, h_dim)
        self.discriminator = Discriminator(dim, h_dim)

        self.g_optimizer = optim.Adam(self.generator.parameters(), lr=0.001)
        self.d_optimizer = optim.Adam(self.discriminator.parameters(), lr=0.001)

    def train(self, data_with_missing, mask, epochs=1000, batch_size=128):
        """
        Train GAIN model

        Args:
            data_with_missing: np.array with NaN for missing
            mask: np.array (1 = observed, 0 = missing)
            epochs: Number of training epochs
            batch_size: Batch size
        """
        n_samples = data_with_missing.shape[0]

        for epoch in range(epochs):
            # Shuffle data
            idx = np.random.permutation(n_samples)

            for i in range(0, n_samples, batch_size):
                batch_idx = idx[i:i+batch_size]
                batch_x = data_with_missing[batch_idx]
                batch_m = mask[batch_idx]

                # Replace NaN with 0 for computation
                batch_x_filled = np.nan_to_num(batch_x, 0)

                # Convert to torch tensors
                x = torch.FloatTensor(batch_x_filled)
                m = torch.FloatTensor(batch_m)

                # Generate hint matrix
                h = self.sample_hint(m, self.alpha)
                h = torch.FloatTensor(h)

                # Train Discriminator
                self.d_optimizer.zero_grad()
                g_sample = self.generator(x, m)
                x_hat = m * x + (1 - m) * g_sample
                d_prob = self.discriminator(x_hat, h)

                # Discriminator loss
                d_loss = -torch.mean(
                    m * torch.log(d_prob + 1e-8) +
                    (1 - m) * torch.log(1 - d_prob + 1e-8)
                )
                d_loss.backward()
                self.d_optimizer.step()

                # Train Generator
                self.g_optimizer.zero_grad()
                g_sample = self.generator(x, m)
                x_hat = m * x + (1 - m) * g_sample
                d_prob = self.discriminator(x_hat, h)

                # Generator loss
                g_loss_adv = -torch.mean((1 - m) * torch.log(d_prob + 1e-8))
                g_loss_mse = torch.mean((m * x - m * g_sample) ** 2)
                g_loss = g_loss_adv + self.alpha * g_loss_mse

                g_loss.backward()
                self.g_optimizer.step()

            if epoch % 100 == 0:
                print(f"Epoch {epoch}: D_loss={d_loss.item():.4f}, G_loss={g_loss.item():.4f}")

    def impute(self, data_with_missing, mask):
        """
        Impute missing values

        Args:
            data_with_missing: np.array with NaN for missing
            mask: np.array (1 = observed, 0 = missing)

        Returns:
            Imputed data (np.array)
        """
        self.generator.eval()

        x = torch.FloatTensor(np.nan_to_num(data_with_missing, 0))
        m = torch.FloatTensor(mask)

        with torch.no_grad():
            g_sample = self.generator(x, m)
            x_hat = m * x + (1 - m) * g_sample

        return x_hat.numpy()

    def sample_hint(self, mask, alpha):
        """Generate hint matrix"""
        hint = np.random.binomial(1, alpha, mask.shape)
        hint = mask * hint  # Only hint on observed values
        return hint
```

**FastAPI Service**:
```python
# microservices/gain-service/src/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
import numpy as np
import pandas as pd

app = FastAPI(title="GAIN Service")

# Global model (in production, load from disk)
trained_models: Dict[str, GAIN] = {}

class ImputeRequest(BaseModel):
    data: List[Dict[str, float]]  # Data with missing values (None for missing)
    columns: List[str]
    model_id: str = "default"

class ImputeResponse(BaseModel):
    imputed_data: List[Dict[str, float]]
    metadata: Dict

@app.post("/train")
async def train_model(request: TrainRequest):
    """Train GAIN model on provided data"""
    # Convert to numpy
    df = pd.DataFrame(request.data)
    data = df[request.columns].values
    mask = (~pd.isna(data)).astype(float)

    # Train GAIN
    gain = GAIN(dim=len(request.columns), h_dim=256, alpha=100)
    gain.train(data, mask, epochs=1000, batch_size=128)

    # Save model
    model_id = request.model_id or f"gain_{len(trained_models)}"
    trained_models[model_id] = gain

    return {"model_id": model_id, "status": "trained"}

@app.post("/impute")
async def impute_missing(request: ImputeRequest):
    """Impute missing values using trained GAIN model"""
    if request.model_id not in trained_models:
        raise HTTPException(404, f"Model {request.model_id} not found")

    gain = trained_models[request.model_id]

    # Convert to numpy
    df = pd.DataFrame(request.data)
    data = df[request.columns].values
    mask = (~pd.isna(data)).astype(float)

    # Impute
    imputed = gain.impute(data, mask)

    # Convert back to records
    imputed_df = pd.DataFrame(imputed, columns=request.columns)

    return ImputeResponse(
        imputed_data=imputed_df.to_dict('records'),
        metadata={
            "rows": len(imputed_df),
            "columns": list(imputed_df.columns),
            "missing_imputed": int((mask == 0).sum())
        }
    )
```

#### **5.2 Conditional GAN for Synthetic Generation** (5 days)

**Conditional GAN** (conditions on treatment arm):
```python
# microservices/gan-service/src/cgan_model.py

class ConditionalGenerator(nn.Module):
    """Conditional GAN Generator"""
    def __init__(self, noise_dim, condition_dim, output_dim, h_dim=256):
        super(ConditionalGenerator, self).__init__()
        self.fc1 = nn.Linear(noise_dim + condition_dim, h_dim)
        self.fc2 = nn.Linear(h_dim, h_dim)
        self.fc3 = nn.Linear(h_dim, output_dim)
        self.relu = nn.ReLU()
        self.tanh = nn.Tanh()

    def forward(self, z, c):
        """
        z: Noise vector
        c: Condition (e.g., [1, 0] for Active, [0, 1] for Placebo)
        """
        x = torch.cat([z, c], dim=1)
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.tanh(self.fc3(x))  # Output in [-1, 1]
        return x

class ConditionalDiscriminator(nn.Module):
    """Conditional GAN Discriminator"""
    def __init__(self, input_dim, condition_dim, h_dim=256):
        super(ConditionalDiscriminator, self).__init__()
        self.fc1 = nn.Linear(input_dim + condition_dim, h_dim)
        self.fc2 = nn.Linear(h_dim, h_dim)
        self.fc3 = nn.Linear(h_dim, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, c):
        """
        x: Data
        c: Condition
        """
        inputs = torch.cat([x, c], dim=1)
        h = self.relu(self.fc1(inputs))
        h = self.relu(self.fc2(h))
        out = self.sigmoid(self.fc3(h))
        return out

class ConditionalGAN:
    """Conditional GAN for Synthetic Clinical Trial Data"""
    def __init__(self, data_dim, condition_dim, noise_dim=100):
        self.generator = ConditionalGenerator(noise_dim, condition_dim, data_dim)
        self.discriminator = ConditionalDiscriminator(data_dim, condition_dim)

        self.g_optimizer = optim.Adam(self.generator.parameters(), lr=0.0002, betas=(0.5, 0.999))
        self.d_optimizer = optim.Adam(self.discriminator.parameters(), lr=0.0002, betas=(0.5, 0.999))

        self.criterion = nn.BCELoss()
        self.noise_dim = noise_dim

    def train(self, real_data, conditions, epochs=5000, batch_size=128):
        """Train conditional GAN"""
        n_samples = real_data.shape[0]

        for epoch in range(epochs):
            for i in range(0, n_samples, batch_size):
                batch_real = real_data[i:i+batch_size]
                batch_cond = conditions[i:i+batch_size]

                real = torch.FloatTensor(batch_real)
                cond = torch.FloatTensor(batch_cond)
                batch_size_actual = real.size(0)

                # Train Discriminator
                self.d_optimizer.zero_grad()

                # Real data
                d_real = self.discriminator(real, cond)
                d_real_loss = self.criterion(d_real, torch.ones(batch_size_actual, 1))

                # Fake data
                z = torch.randn(batch_size_actual, self.noise_dim)
                fake = self.generator(z, cond)
                d_fake = self.discriminator(fake.detach(), cond)
                d_fake_loss = self.criterion(d_fake, torch.zeros(batch_size_actual, 1))

                d_loss = d_real_loss + d_fake_loss
                d_loss.backward()
                self.d_optimizer.step()

                # Train Generator
                self.g_optimizer.zero_grad()

                z = torch.randn(batch_size_actual, self.noise_dim)
                fake = self.generator(z, cond)
                d_fake = self.discriminator(fake, cond)
                g_loss = self.criterion(d_fake, torch.ones(batch_size_actual, 1))

                g_loss.backward()
                self.g_optimizer.step()

            if epoch % 500 == 0:
                print(f"Epoch {epoch}: D_loss={d_loss.item():.4f}, G_loss={g_loss.item():.4f}")

    def generate(self, conditions, n_samples):
        """Generate synthetic data"""
        self.generator.eval()

        cond = torch.FloatTensor(conditions)
        z = torch.randn(n_samples, self.noise_dim)

        with torch.no_grad():
            fake = self.generator(z, cond)

        return fake.numpy()
```

**FastAPI Service**:
```python
@app.post("/generate")
async def generate_synthetic(request: GenerateRequest):
    """Generate synthetic clinical trial data using conditional GAN"""

    # Conditions: [1, 0] = Active, [0, 1] = Placebo
    conditions_active = np.tile([1, 0], (request.n_per_arm, 1))
    conditions_placebo = np.tile([0, 1], (request.n_per_arm, 1))
    conditions = np.vstack([conditions_active, conditions_placebo])

    # Generate
    synthetic = cgan.generate(conditions, request.n_per_arm * 2)

    # Denormalize (convert from [-1, 1] to actual ranges)
    synthetic_df = denormalize(synthetic, feature_columns)

    # Add metadata (SubjectID, VisitName, TreatmentArm)
    synthetic_df = add_metadata(synthetic_df, request.n_per_arm)

    return {
        "data": synthetic_df.to_dict('records'),
        "metadata": {
            "method": "conditional_gan",
            "records": len(synthetic_df),
            "subjects": request.n_per_arm * 2
        }
    }
```

---

### **Phase 6: Integration & Testing** (Week 8)

#### **6.1 End-to-End Integration** (3 days)
- Connect form builder → EDC → query management
- Connect GAIN/GAN → quality validation
- Test full workflow: Create study → Enroll subjects → Enter data → Generate queries → Impute missing → Generate synthetic → Validate quality

#### **6.2 Frontend Development** (4 days)
- Form builder UI (React drag-and-drop)
- Query management UI (CRC + Data Manager views)
- RBQM dashboard (charts, heatmaps, tables)
- GAIN/GAN integration (impute button, generate button)

---

## 📊 EFFORT ESTIMATION

| Phase | Feature | Days | Difficulty | Priority |
|-------|---------|------|------------|----------|
| 1 | Expand Data Model | 12 | ⭐⭐⭐ Medium | 🔴 Critical |
| 2 | Form Builder | 7 | ⭐⭐⭐⭐⭐ Very Hard | 🔴 Critical |
| 3 | Query Management | 7 | ⭐⭐⭐⭐ Hard | 🔴 Critical |
| 4 | RBQM Dashboard | 7 | ⭐⭐⭐⭐ Hard | 🔴 Critical |
| 5 | GAIN + GAN | 10 | ⭐⭐⭐⭐⭐ Very Hard | 🔴 Critical |
| 6 | Integration & Testing | 7 | ⭐⭐⭐ Medium | 🟠 Important |

**Total: 50 days (7-8 weeks full-time)**

---

## 🎯 REALISTIC TIMELINE

### **Option 1: Full Implementation** (8 weeks)
- All features implemented
- Industry-grade EDC platform
- GAIN + Conditional GAN
- Ready for serious demo

### **Option 2: MVP** (4 weeks) - RECOMMENDED FOR CLASS PROJECT
**Week 1-2**: Expand data model (Demographics, Labs, AEs)
**Week 3**: Simple form builder (no drag-and-drop, just JSON config)
**Week 4**: Basic query management + RBQM dashboard + GAIN (no conditional GAN)

**Result**: 70% industry-grade, demonstrates all key concepts

### **Option 3: Research Focus** (3 weeks)
Skip form builder/queries, focus on:
- Week 1: Expand data model
- Week 2-3: GAIN + Conditional GAN implementation
- Position as "ML research platform" not "full EDC"

---

## ✅ WHAT THIS ACHIEVES

After implementing these features, your platform will have:

### **EDC Completeness**: 70-80% (vs 35% now)
- ✅ Form builder (customizable CRFs)
- ✅ Query management (full workflow)
- ✅ RBQM dashboard (site monitoring)
- ✅ Multiple data domains (Vitals, Labs, AEs, Demographics, Meds)
- ❌ Still missing: Medical coding, ePRO, IRT/IWRS (but those are advanced)

### **ML/AI Completeness**: 90-95% (vs 75% now)
- ✅ GAIN for intelligent imputation
- ✅ Conditional GAN for synthetic generation
- ✅ Quality validation (Wasserstein, correlation, RMSE)
- ✅ Multiple generation baselines (MVN, Bootstrap, LLM)

### **Overall**: 75-85% of Medidata RAVE (vs 35% now)

---

## 🚀 NEXT STEPS

**Decision Time**: Which timeline do you want?

1. **Full Implementation (8 weeks)** - Best for thesis/capstone, not realistic for regular class
2. **MVP (4 weeks)** - Best for class project, still impressive
3. **Research Focus (3 weeks)** - Focus on GAIN/GAN, skip EDC features

**My Recommendation**: Go with **MVP (4 weeks)** - it gives you:
- Industry-grade core features (form builder, queries, RBQM)
- Research contribution (GAIN)
- Realistic timeline for class project
- 70% complete vs Medidata (huge jump from 35%)

Want me to start implementing Phase 1 (Expand Data Model)?
