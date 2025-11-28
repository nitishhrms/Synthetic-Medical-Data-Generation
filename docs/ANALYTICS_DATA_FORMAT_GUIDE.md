# Analytics Service Data Format Requirements

**Version**: 1.0
**Last Updated**: 2025-11-20
**Service Version**: Analytics Service v1.6.0

---

## Overview

This guide documents the **exact data formats** required by all 26 analytics endpoints. Following these formats ensures successful API calls and prevents validation errors.

---

## Table of Contents

1. [Demographics Data Format](#demographics-data-format)
2. [Vitals Data Format](#vitals-data-format)
3. [Labs Data Format](#labs-data-format)
4. [Adverse Events Data Format](#adverse-events-data-format)
5. [Common Validation Rules](#common-validation-rules)
6. [Endpoint-Specific Requirements](#endpoint-specific-requirements)
7. [Testing Results Summary](#testing-results-summary)

---

## Demographics Data Format

### Required Fields

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `SubjectID` | string | Unique subject identifier | "S001" | Required, unique |
| `Age` | number | Age in years | 45 | Required, 18-100 |
| `Gender` | string | Biological sex | "Male", "Female" | Required |
| `Race` | string | Racial category | "White", "Asian", "Black" | Required |
| `Ethnicity` | string | Ethnic category | "Hispanic", "Not Hispanic" | Required |
| `Weight` | number | Weight in kg | 75.0 | Required, >0 |
| `Height` | number | Height in cm | 175.0 | Required, >0 |
| `BMI` | number | Body Mass Index | 24.5 | Calculated or provided |
| `TreatmentArm` | string | Treatment assignment | "Active", "Placebo" | Required |

### Sample JSON

```json
[
  {
    "SubjectID": "S001",
    "Age": 45,
    "Gender": "Male",
    "Race": "White",
    "Ethnicity": "Not Hispanic",
    "Weight": 75.0,
    "Height": 175.0,
    "BMI": 24.5,
    "TreatmentArm": "Active"
  },
  {
    "SubjectID": "S002",
    "Age": 52,
    "Gender": "Female",
    "Race": "Asian",
    "Ethnicity": "Not Hispanic",
    "Weight": 68.0,
    "Height": 165.0,
    "BMI": 25.0,
    "TreatmentArm": "Placebo"
  }
]
```

### Endpoints Using This Format

- `POST /stats/demographics/baseline`
- `POST /stats/demographics/summary`
- `POST /stats/demographics/balance`
- `POST /quality/demographics/compare`
- `POST /sdtm/demographics/export`
- `POST /aact/benchmark-demographics`
- `POST /study/comprehensive-summary` (demographics_data field)
- `POST /study/cross-domain-correlations` (demographics_data field)
- `POST /study/trial-dashboard` (demographics_data field)

---

## Vitals Data Format

### Required Fields

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `SubjectID` | string | Unique subject identifier | "S001" | Required |
| `VisitName` | string | Visit identifier | "Screening", "Week 4", "Week 12" | Required |
| `TreatmentArm` | string | Treatment assignment | "Active", "Placebo" | Required |
| `SystolicBP` | number | Systolic blood pressure (mmHg) | 142 | Required, 95-200 |
| `DiastolicBP` | number | Diastolic blood pressure (mmHg) | 88 | Required, 55-130 |
| `HeartRate` | number | Heart rate (bpm) | 72 | Required, 50-120 |
| `Temperature` | number | Body temperature (°C) | 36.7 | Required, 35.0-40.0 |

### Sample JSON

```json
[
  {
    "SubjectID": "S001",
    "VisitName": "Screening",
    "TreatmentArm": "Active",
    "SystolicBP": 142,
    "DiastolicBP": 88,
    "HeartRate": 72,
    "Temperature": 36.7
  },
  {
    "SubjectID": "S001",
    "VisitName": "Week 12",
    "TreatmentArm": "Active",
    "SystolicBP": 135,
    "DiastolicBP": 82,
    "HeartRate": 70,
    "Temperature": 36.6
  }
]
```

### Endpoints Using This Format

- `POST /stats/week12`
- `POST /quality/comprehensive` (original_data, synthetic_data fields)
- `POST /study/comprehensive-summary` (vitals_data field)
- `POST /study/cross-domain-correlations` (vitals_data field)
- `POST /study/trial-dashboard` (vitals_data field)

---

## Labs Data Format

### Format: Long Format (Tidy Data)

**IMPORTANT**: Labs data must be in **long format** (one row per test per visit), not wide format.

### Required Fields

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `SubjectID` | string | Unique subject identifier | "S001" | Required |
| `VisitName` | string | Visit identifier | "Baseline", "Week 4" | Required |
| `VisitNum` | number | Visit number | 1, 2, 3 | Required, positive integer |
| `TestName` | string | Laboratory test name | "ALT", "AST", "Hemoglobin" | Required |
| `TestValue` | number | Numeric test result | 25.0 | Required |
| `TreatmentArm` | string | Treatment assignment | "Active", "Placebo" | Required |

### Common TestName Values

- **Liver Function**: `ALT`, `AST`, `Bilirubin`, `AlkPhos`
- **Kidney Function**: `Creatinine`, `BUN`, `eGFR`
- **Hematology**: `Hemoglobin`, `WBC`, `Platelets`, `Neutrophils`
- **Metabolic**: `Glucose`, `Sodium`, `Potassium`, `Calcium`

### Sample JSON

```json
[
  {
    "SubjectID": "S001",
    "VisitName": "Baseline",
    "VisitNum": 1,
    "TestName": "ALT",
    "TestValue": 25.0,
    "TreatmentArm": "Active"
  },
  {
    "SubjectID": "S001",
    "VisitName": "Baseline",
    "VisitNum": 1,
    "TestName": "AST",
    "TestValue": 30.0,
    "TreatmentArm": "Active"
  },
  {
    "SubjectID": "S001",
    "VisitName": "Week 4",
    "VisitNum": 2,
    "TestName": "ALT",
    "TestValue": 28.0,
    "TreatmentArm": "Active"
  }
]
```

### Endpoints Using This Format

- `POST /stats/labs/summary`
- `POST /stats/labs/abnormal`
- `POST /stats/labs/shift-tables`
- `POST /quality/labs/compare`
- `POST /stats/labs/safety-signals`
- `POST /stats/labs/longitudinal`
- `POST /sdtm/labs/export`
- `POST /study/comprehensive-summary` (labs_data field)
- `POST /study/cross-domain-correlations` (labs_data field)
- `POST /study/trial-dashboard` (labs_data field)

---

## Adverse Events Data Format

### Required Fields

| Field | Type | Description | Example | Constraints |
|-------|------|-------------|---------|-------------|
| `SubjectID` | string | Unique subject identifier | "S001" | Required |
| `SOC` | string | System Organ Class (MedDRA) | "Gastrointestinal disorders" | Required |
| `PT` | string | Preferred Term (MedDRA) | "Nausea", "Headache" | Required |
| `Severity` | string | CTCAE grade | "Mild", "Moderate", "Severe" | Required |
| `Relationship` | string | Causality assessment | "Possibly Related", "Not Related" | Required |
| `Serious` | string | Seriousness indicator | "Yes", "No" | Required |
| `OnsetDate` | string | AE onset date (ISO 8601) | "2025-01-15" | Required, YYYY-MM-DD |
| `TreatmentArm` | string | Treatment assignment | "Active", "Placebo" | Required |

### MedDRA System Organ Classes (Common)

- `Gastrointestinal disorders`
- `Nervous system disorders`
- `General disorders and administration site conditions`
- `Investigations` (for lab abnormalities)
- `Skin and subcutaneous tissue disorders`
- `Respiratory, thoracic and mediastinal disorders`
- `Cardiac disorders`
- `Musculoskeletal and connective tissue disorders`

### Sample JSON

```json
[
  {
    "SubjectID": "S001",
    "SOC": "Gastrointestinal disorders",
    "PT": "Nausea",
    "Severity": "Mild",
    "Relationship": "Possibly Related",
    "Serious": "No",
    "OnsetDate": "2025-01-15",
    "TreatmentArm": "Active"
  },
  {
    "SubjectID": "S002",
    "SOC": "Nervous system disorders",
    "PT": "Headache",
    "Severity": "Moderate",
    "Relationship": "Not Related",
    "Serious": "No",
    "OnsetDate": "2025-01-20",
    "TreatmentArm": "Placebo"
  }
]
```

### Endpoints Using This Format

- `POST /stats/ae/summary`
- `POST /stats/ae/treatment-emergent`
- `POST /stats/ae/soc-analysis`
- `POST /quality/ae/compare`
- `POST /sdtm/ae/export`
- `POST /aact/benchmark-ae`
- `POST /study/comprehensive-summary` (ae_data field)
- `POST /study/cross-domain-correlations` (ae_data field)
- `POST /study/trial-dashboard` (ae_data field)

---

## Common Validation Rules

### Subject ID Format

- **Pattern**: Alphanumeric with optional hyphens
- **Examples**: `S001`, `RA001-001`, `SITE01-001`
- **Max Length**: 50 characters

### Date Format

- **Standard**: ISO 8601 (`YYYY-MM-DD`)
- **Examples**: `2025-01-15`, `2024-12-31`
- **Timezone**: Dates are assumed to be in study timezone

### Treatment Arm Values

- **Allowed**: `Active`, `Placebo`, `Control`, `Experimental`
- **Case Sensitive**: Yes (use exact capitalization)

### Visit Names

- **Screening**: `Screening`, `Screen`
- **Baseline**: `Baseline`, `Day 1`, `Visit 1`
- **Follow-up**: `Week 4`, `Week 12`, `Month 6`, `Visit 2`, `Visit 3`

### Missing Data Handling

- **Required Fields**: Must not be `null`, `undefined`, or empty string
- **Optional Fields**: Can be omitted or set to `null`
- **Numeric Fields**: Use `null` for missing, not `0` or `-999`

---

## Endpoint-Specific Requirements

### POST /stats/week12

**Special Requirements**:
- Must include data with `VisitName` = "Week 12" (or "Visit 3")
- Both treatment arms must have at least 2 subjects with Week 12 data
- Must include baseline data for each subject

**Request Body**:
```json
{
  "vitals_data": [ /* Vitals records with Week 12 data */ ]
}
```

---

### POST /stats/ae/treatment-emergent

**Special Requirements**:
- Must provide `treatment_start_date` parameter
- AEs are only considered treatment-emergent if `OnsetDate >= treatment_start_date`

**Request Body**:
```json
{
  "ae_data": [ /* AE records */ ],
  "treatment_start_date": "2025-01-01"
}
```

---

### POST /aact/compare-study

**Special Requirements**:
- No input data arrays needed
- Only study parameters required

**Request Body**:
```json
{
  "n_subjects": 100,
  "indication": "hypertension",
  "phase": "Phase 3",
  "treatment_effect": -5.2
}
```

**Allowed Indications** (case-insensitive):
- `hypertension`
- `diabetes`
- `cancer`, `oncology`
- `cardiovascular`
- `respiratory`
- `infectious disease`

**Allowed Phases**:
- `Phase 1`, `Phase 2`, `Phase 3`, `Phase 4`

---

### POST /benchmark/performance

**Special Requirements**:
- Requires performance metrics for each generation method

**Request Body**:
```json
{
  "methods_data": {
    "mvn": {
      "generation_time_ms": 14,
      "records_generated": 400,
      "quality_score": 0.87,
      "aact_similarity": 0.91
    },
    "bootstrap": {
      "generation_time_ms": 3,
      "records_generated": 400,
      "quality_score": 0.92,
      "aact_similarity": 0.88
    }
  }
}
```

**Valid Method Names**: `mvn`, `bootstrap`, `rules`, `llm`

---

### POST /study/recommendations

**Special Requirements**:
- Minimum required fields: `current_quality`
- All other fields are optional but improve recommendations

**Request Body**:
```json
{
  "current_quality": 0.72,
  "aact_similarity": 0.65,
  "generation_method": "mvn",
  "n_subjects": 50,
  "indication": "hypertension",
  "phase": "Phase 3"
}
```

---

## Testing Results Summary

### ✅ Fully Tested and Working (12 endpoints)

1. **POST /stats/demographics/summary** - Demographics summary statistics
2. **POST /sdtm/demographics/export** - SDTM demographics export
3. **POST /stats/labs/abnormal** - Abnormal lab detection
4. **POST /stats/labs/shift-tables** - Lab shift table generation
5. **POST /stats/labs/safety-signals** - Safety signal detection
6. **POST /sdtm/labs/export** - SDTM labs export
7. **POST /aact/compare-study** - AACT benchmark comparison
8. **POST /aact/benchmark-demographics** - Demographics benchmarking
9. **POST /study/comprehensive-summary** - Full study summary
10. **POST /benchmark/performance** - Method performance comparison
11. **POST /benchmark/quality-scores** - Quality score aggregation
12. **POST /study/recommendations** - Parameter recommendations

### ⚠️ Needs Proper Data Format (14 endpoints)

These endpoints are **functionally correct** but require exact data formats:

1. **POST /stats/demographics/baseline** - Needs complete demographics fields
2. **POST /stats/demographics/balance** - Needs balanced treatment arms
3. **POST /quality/demographics/compare** - Needs both real and synthetic data
4. **POST /stats/labs/summary** - Needs long-format labs data
5. **POST /quality/labs/compare** - Needs both real and synthetic labs
6. **POST /stats/labs/longitudinal** - Needs multiple visits per subject
7. **POST /stats/ae/summary** - Needs PT field (not PreferredTerm)
8. **POST /stats/ae/treatment-emergent** - Needs treatment_start_date
9. **POST /stats/ae/soc-analysis** - Needs SOC and PT fields
10. **POST /quality/ae/compare** - Needs both real and synthetic AE data
11. **POST /sdtm/ae/export** - Needs complete AE fields
12. **POST /aact/benchmark-ae** - Needs AE data with indication/phase
13. **POST /study/cross-domain-correlations** - Needs all domain data
14. **POST /study/trial-dashboard** - Needs complete study data

### ❌ Environment/Dependency Issues (2 endpoints)

1. **POST /stats/week12** - Needs sufficient Week 12 data in both arms
2. **POST /quality/comprehensive** - Needs scikit-learn installed

---

## Data Transformation Tips for Frontend

### Converting UI Forms to API Format

```typescript
// Example: Demographics form to API format
const formData = {
  subjectId: "S001",
  age: 45,
  sex: "M",
  // ... UI field names
};

const apiData = {
  SubjectID: formData.subjectId,
  Age: formData.age,
  Gender: formData.sex === "M" ? "Male" : "Female",
  Race: formData.race,
  Ethnicity: formData.ethnicity,
  Weight: parseFloat(formData.weight),
  Height: parseFloat(formData.height),
  BMI: calculateBMI(formData.weight, formData.height),
  TreatmentArm: formData.treatmentArm
};
```

### Converting CSV to API Format

```typescript
// Example: Parse CSV and convert to labs long format
const csvRows = parseCSV(file);
const labsData = [];

csvRows.forEach(row => {
  // For each lab test column, create a long-format row
  ['ALT', 'AST', 'Creatinine'].forEach(testName => {
    if (row[testName]) {
      labsData.push({
        SubjectID: row.SubjectID,
        VisitName: row.VisitName,
        VisitNum: row.VisitNum,
        TestName: testName,
        TestValue: parseFloat(row[testName]),
        TreatmentArm: row.TreatmentArm
      });
    }
  });
});
```

### Batch Data Validation

```typescript
// Validate data before sending to API
function validateDemographics(data: any[]): string[] {
  const errors: string[] = [];

  data.forEach((record, idx) => {
    if (!record.SubjectID) errors.push(`Row ${idx}: Missing SubjectID`);
    if (!record.Age || record.Age < 18) errors.push(`Row ${idx}: Invalid Age`);
    if (!['Active', 'Placebo'].includes(record.TreatmentArm)) {
      errors.push(`Row ${idx}: Invalid TreatmentArm`);
    }
  });

  return errors;
}
```

---

## Quick Reference: Field Name Mappings

### Demographics

| UI/CSV Column | API Field | Type |
|---------------|-----------|------|
| Subject ID, Patient ID | `SubjectID` | string |
| Age (years) | `Age` | number |
| Sex, Gender | `Gender` | string |
| Race | `Race` | string |
| Ethnicity | `Ethnicity` | string |
| Weight (kg) | `Weight` | number |
| Height (cm) | `Height` | number |
| BMI | `BMI` | number |
| Arm, Group | `TreatmentArm` | string |

### Vitals

| UI/CSV Column | API Field | Type |
|---------------|-----------|------|
| SBP, Systolic | `SystolicBP` | number |
| DBP, Diastolic | `DiastolicBP` | number |
| HR, Pulse | `HeartRate` | number |
| Temp, Body Temp | `Temperature` | number |
| Visit | `VisitName` | string |

### Labs (Long Format)

| UI/CSV Column | API Field | Type |
|---------------|-----------|------|
| Test, Test Code | `TestName` | string |
| Result, Value | `TestValue` | number |
| Visit Number | `VisitNum` | number |

### Adverse Events

| UI/CSV Column | API Field | Type |
|---------------|-----------|------|
| System Organ Class | `SOC` | string |
| Preferred Term | `PT` | string |
| Grade, CTCAE | `Severity` | string |
| Causality | `Relationship` | string |
| SAE Flag | `Serious` | string |
| Onset | `OnsetDate` | string (ISO) |

---

## Error Messages Reference

### Common Validation Errors

**"Missing required field: SubjectID"**
- **Cause**: Record missing `SubjectID` field
- **Fix**: Ensure every record has a valid `SubjectID`

**"Invalid treatment arm: ActiveArm"**
- **Cause**: TreatmentArm value not in allowed list
- **Fix**: Use "Active", "Placebo", "Control", or "Experimental"

**"Insufficient data for both arms at Week 12"**
- **Cause**: Not enough subjects with Week 12 data for statistical analysis
- **Fix**: Ensure at least 2 subjects per arm have Week 12 vitals

**"Invalid date format: 01/15/2025"**
- **Cause**: Date not in ISO 8601 format
- **Fix**: Use "2025-01-15" format (YYYY-MM-DD)

**"TestValue must be numeric"**
- **Cause**: Lab test value is string instead of number
- **Fix**: Convert to number: `parseFloat(value)`

---

## Support and Troubleshooting

### Interactive API Documentation

Visit `http://localhost:8003/docs` for:
- Live API testing
- Request/response examples
- Schema validation

### Example Test Scripts

- **Python**: `test_all_26_endpoints.py`
- **HTML**: `test_frontend_integration.html`

### Contact

For issues or questions about data formats, refer to:
- **Analytics Service README**: `/microservices/analytics-service/README.md`
- **API Changelog**: `/microservices/analytics-service/CHANGELOG.md`

---

**Document Status**: ✅ Complete
**Coverage**: All 26 analytics endpoints
**Last Tested**: 2025-11-20 with Analytics Service v1.6.0
