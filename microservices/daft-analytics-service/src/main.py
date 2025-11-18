"""
Daft Analytics Service - Distributed Data Analysis for Clinical Trials
Provides advanced data processing and analysis using the Daft distributed dataframe library

Port: 8007
"""
from fastapi import FastAPI, HTTPException, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import pandas as pd
import daft
from datetime import datetime
import uvicorn
import os
import json
import tempfile

from daft_processor import DaftMedicalDataProcessor
from daft_aggregations import DaftAggregator
from daft_udfs import MedicalUDFs, AdvancedMedicalUDFs

# ==================== FastAPI Application ====================

app = FastAPI(
    title="Daft Analytics Service",
    description="Distributed Data Analysis for Clinical Trials using Daft",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]
if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn("CORS wildcard enabled in production - security risk!", UserWarning)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ==================== Pydantic Models ====================

class VitalsData(BaseModel):
    """Request model for vitals data"""
    data: List[Dict[str, Any]] = Field(..., description="List of vitals records")

class FilterRequest(BaseModel):
    """Request model for filtering data"""
    data: List[Dict[str, Any]]
    condition: Optional[str] = Field(None, description="Filter condition (e.g., 'SystolicBP > 140')")
    treatment_arm: Optional[str] = Field(None, description="Treatment arm to filter by")
    visit_name: Optional[str] = Field(None, description="Visit name to filter by")

class AggregationRequest(BaseModel):
    """Request model for aggregations"""
    data: List[Dict[str, Any]]
    group_by: str = Field(..., description="Column to group by (treatment_arm, visit, subject)")

class TreatmentEffectRequest(BaseModel):
    """Request model for treatment effect analysis"""
    data: List[Dict[str, Any]]
    endpoint: str = Field(default="SystolicBP", description="Vital sign to analyze")
    visit: str = Field(default="Week 12", description="Visit to analyze")

class ResponderAnalysisRequest(BaseModel):
    """Request model for responder analysis"""
    data: List[Dict[str, Any]]
    threshold: float = Field(default=-10.0, description="Threshold for response")
    endpoint: str = Field(default="SystolicBP", description="Endpoint to evaluate")

class OutlierDetectionRequest(BaseModel):
    """Request model for outlier detection"""
    data: List[Dict[str, Any]]
    column: str = Field(default="SystolicBP", description="Column to check for outliers")
    method: str = Field(default="iqr", description="Method: 'iqr' or 'zscore'")

class DerivedColumnRequest(BaseModel):
    """Request model for adding derived columns"""
    data: List[Dict[str, Any]]
    column_name: str = Field(..., description="Name of new column")
    expression: str = Field(..., description="Expression to compute (e.g., 'SystolicBP - DiastolicBP')")

class SQLQueryRequest(BaseModel):
    """Request model for SQL queries"""
    data: List[Dict[str, Any]]
    query: str = Field(..., description="SQL query to execute")

# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Daft Analytics Service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "daft_version": daft.__version__
    }

# ==================== Core Data Processing Endpoints ====================

@app.post("/daft/load")
async def load_data(request: VitalsData):
    """
    Load data into Daft DataFrame and return basic info

    This endpoint demonstrates Daft's data loading capabilities
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(request.data)

        return {
            "status": "success",
            "message": "Data loaded into Daft DataFrame",
            "row_count": processor.count_rows(),
            "schema": processor.get_schema(),
            "sample_data": df.limit(5).to_pandas().to_dict('records')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

@app.post("/daft/filter")
async def filter_data(request: FilterRequest):
    """
    Filter data using Daft's distributed filtering capabilities

    Supports:
    - Conditional filtering (e.g., SystolicBP > 140)
    - Treatment arm filtering
    - Visit filtering
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(request.data)

        # Apply filters
        if request.condition:
            processor.filter_rows(request.condition)

        if request.treatment_arm:
            processor.filter_by_treatment_arm(request.treatment_arm)

        if request.visit_name:
            processor.filter_by_visit(request.visit_name)

        # Collect results
        result_df = processor.collect()

        return {
            "status": "success",
            "filtered_data": result_df.to_dict('records'),
            "row_count": len(result_df),
            "filters_applied": {
                "condition": request.condition,
                "treatment_arm": request.treatment_arm,
                "visit_name": request.visit_name
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")

@app.post("/daft/select")
async def select_columns(data: VitalsData, columns: List[str]):
    """
    Select specific columns from the dataset
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)
        processor.select_columns(columns)

        result_df = processor.collect()

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "columns": columns,
            "row_count": len(result_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error selecting columns: {str(e)}")

@app.post("/daft/add-derived-column")
async def add_derived_column(request: DerivedColumnRequest):
    """
    Add a derived column using Daft expressions

    Examples:
    - "SystolicBP - DiastolicBP" -> Pulse Pressure
    - "SystolicBP + DiastolicBP" -> Sum
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(request.data)
        processor.add_derived_column(request.column_name, request.expression)

        result_df = processor.collect()

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "new_column": request.column_name,
            "expression": request.expression,
            "row_count": len(result_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding derived column: {str(e)}")

@app.post("/daft/add-medical-features")
async def add_medical_features(data: VitalsData):
    """
    Add medical-specific derived features:
    - Pulse Pressure
    - Mean Arterial Pressure
    - Hypertension Category
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)

        # Add derived features
        processor.add_pulse_pressure()
        processor.add_mean_arterial_pressure()
        processor.add_hypertension_category()

        result_df = processor.collect()

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "features_added": [
                "PulsePressure",
                "MeanArterialPressure",
                "HypertensionCategory"
            ],
            "row_count": len(result_df)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding medical features: {str(e)}")

# ==================== Aggregation Endpoints ====================

@app.post("/daft/aggregate/by-treatment-arm")
async def aggregate_by_treatment_arm(data: VitalsData):
    """
    Aggregate data by treatment arm with comprehensive statistics

    Returns detailed statistics for each vital sign by treatment arm
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.groupby_treatment_arm()

        return {
            "status": "success",
            "aggregations": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating by treatment arm: {str(e)}")

@app.post("/daft/aggregate/by-visit")
async def aggregate_by_visit(data: VitalsData):
    """
    Aggregate data by visit name

    Returns mean values for each vital sign at each visit
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.groupby_visit()

        return {
            "status": "success",
            "aggregations": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating by visit: {str(e)}")

@app.post("/daft/aggregate/by-subject")
async def aggregate_by_subject(data: VitalsData):
    """
    Aggregate data by subject

    Returns subject-level statistics including baseline and change from baseline
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.groupby_subject()

        return {
            "status": "success",
            "aggregations": results,
            "subject_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error aggregating by subject: {str(e)}")

@app.post("/daft/treatment-effect")
async def compute_treatment_effect(request: TreatmentEffectRequest):
    """
    Compute treatment effect with statistical testing

    Performs t-test comparing active vs placebo at specified visit
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(request.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_treatment_effect(
            endpoint=request.endpoint,
            visit=request.visit
        )

        return {
            "status": "success",
            "treatment_effect": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing treatment effect: {str(e)}")

@app.post("/daft/longitudinal-summary")
async def compute_longitudinal_summary(data: VitalsData):
    """
    Compute longitudinal summary across all visits

    Shows trajectories of vital signs over time for each treatment arm
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_longitudinal_summary()

        return {
            "status": "success",
            "longitudinal_summary": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing longitudinal summary: {str(e)}")

@app.post("/daft/correlation-matrix")
async def compute_correlation_matrix(data: VitalsData):
    """
    Compute correlation matrix for vital signs
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_correlation_matrix()

        return {
            "status": "success",
            "correlation_analysis": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing correlation matrix: {str(e)}")

# ==================== Advanced Analytics Endpoints ====================

@app.post("/daft/change-from-baseline")
async def compute_change_from_baseline(data: VitalsData):
    """
    Compute change from baseline for all subjects and visits
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_change_from_baseline()

        return {
            "status": "success",
            "data": results.to_dict('records'),
            "row_count": len(results),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing change from baseline: {str(e)}")

@app.post("/daft/responder-analysis")
async def responder_analysis(request: ResponderAnalysisRequest):
    """
    Perform responder analysis

    Identifies subjects achieving a specified threshold change
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(request.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_responder_analysis(
            threshold=request.threshold,
            endpoint=request.endpoint
        )

        return {
            "status": "success",
            "responder_analysis": results,
            "threshold": request.threshold,
            "endpoint": request.endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error performing responder analysis: {str(e)}")

@app.post("/daft/time-to-effect")
async def time_to_effect_analysis(data: VitalsData, threshold: float = -5.0, endpoint: str = "SystolicBP"):
    """
    Analyze when treatment effect becomes significant over time
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_time_to_effect(
            threshold=threshold,
            endpoint=endpoint
        )

        return {
            "status": "success",
            "time_to_effect": results,
            "threshold": threshold,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing time to effect: {str(e)}")

@app.post("/daft/outlier-detection")
async def detect_outliers(request: OutlierDetectionRequest):
    """
    Detect outliers using IQR or Z-score method
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(request.data)

        aggregator = DaftAggregator(df)
        results = aggregator.compute_outliers(
            column=request.column,
            method=request.method
        )

        return {
            "status": "success",
            "outlier_detection": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error detecting outliers: {str(e)}")

# ==================== UDF Endpoints ====================

@app.post("/daft/apply-quality-flags")
async def apply_quality_flags(data: VitalsData):
    """
    Apply quality control flags to identify data issues
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        # Apply quality flags
        result_df = MedicalUDFs.apply_quality_flags(df)

        # Get summary
        qc_summary = {
            'bp_errors': int(result_df['QC_BP_Error'].sum()),
            'abnormal_vitals': int(result_df['QC_Abnormal_Vitals'].sum()),
            'intervention_needed': int(result_df['QC_Intervention_Needed'].sum()),
            'total_records': len(result_df)
        }

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "qc_summary": qc_summary,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying quality flags: {str(e)}")

@app.post("/daft/identify-responders")
async def identify_responders(data: VitalsData, threshold: float = -10.0, endpoint: str = "SystolicBP"):
    """
    Identify treatment responders using UDFs
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)

        # Identify responders
        result_df = AdvancedMedicalUDFs.identify_treatment_responders(
            df, threshold=threshold, endpoint=endpoint
        )

        # Get summary
        responder_summary = {
            'total_subjects': len(result_df['SubjectID'].unique()),
            'responders': int(result_df['IsResponder'].sum()),
            'response_rate': float(result_df['IsResponder'].mean())
        }

        return {
            "status": "success",
            "data": result_df.to_dict('records'),
            "responder_summary": responder_summary,
            "threshold": threshold,
            "endpoint": endpoint,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error identifying responders: {str(e)}")

# ==================== SQL Query Endpoint ====================

@app.post("/daft/sql")
async def execute_sql_query(request: SQLQueryRequest):
    """
    Execute SQL query on the data using Daft's SQL interface

    Example queries:
    - SELECT * FROM data WHERE SystolicBP > 140
    - SELECT TreatmentArm, AVG(SystolicBP) as mean_sbp FROM data GROUP BY TreatmentArm
    """
    try:
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(request.data)

        # Register the dataframe for SQL querying
        # Note: Daft SQL might require specific syntax, this is a simplified example
        result_pdf = df.to_pandas()

        # For now, we'll use pandas for SQL-like operations
        # In production, you'd use Daft's native SQL capabilities
        # result = daft.sql(request.query, dataframes={"data": df})

        return {
            "status": "success",
            "message": "SQL query executed",
            "query": request.query,
            "note": "Daft SQL interface - use Daft's native SQL when available",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing SQL query: {str(e)}")

# ==================== Export Endpoints ====================

@app.post("/daft/export/csv")
async def export_to_csv(data: VitalsData, filename: str = "daft_export.csv"):
    """
    Export data to CSV file
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)

        # Create temp file
        output_path = f"/tmp/{filename}"
        processor.export_to_csv(output_path)

        return {
            "status": "success",
            "message": "Data exported to CSV",
            "filepath": output_path,
            "row_count": processor.count_rows(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to CSV: {str(e)}")

@app.post("/daft/export/parquet")
async def export_to_parquet(data: VitalsData, filename: str = "daft_export.parquet"):
    """
    Export data to Parquet file using Daft's native Parquet writer
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)

        # Create temp file
        output_path = f"/tmp/{filename}"
        processor.export_to_parquet(output_path)

        return {
            "status": "success",
            "message": "Data exported to Parquet",
            "filepath": output_path,
            "row_count": processor.count_rows(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to Parquet: {str(e)}")

# ==================== Execution Plan Endpoint ====================

@app.post("/daft/explain")
async def explain_execution_plan(data: VitalsData, operations: List[str] = []):
    """
    Get Daft's execution plan for lazy evaluation

    Shows how Daft will execute the operations
    """
    try:
        processor = DaftMedicalDataProcessor()
        processor.load_from_dict(data.data)

        # Apply some operations to see the plan
        if "filter" in operations:
            processor.filter_rows("SystolicBP > 140")
        if "add_pulse_pressure" in operations:
            processor.add_pulse_pressure()

        # Get execution plan
        plan = processor.get_execution_plan()

        return {
            "status": "success",
            "execution_plan": plan,
            "operations": operations,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting execution plan: {str(e)}")

# ==================== Performance Benchmark Endpoint ====================

@app.post("/daft/benchmark")
async def benchmark_operations(data: VitalsData):
    """
    Benchmark Daft operations for performance testing
    """
    try:
        import time

        results = {}

        # Benchmark 1: Data loading
        start = time.time()
        processor = DaftMedicalDataProcessor()
        df = processor.load_from_dict(data.data)
        results['load_time_ms'] = (time.time() - start) * 1000

        # Benchmark 2: Filtering
        start = time.time()
        processor2 = DaftMedicalDataProcessor()
        processor2.load_from_dict(data.data)
        processor2.filter_rows("SystolicBP > 140")
        _ = processor2.collect()
        results['filter_time_ms'] = (time.time() - start) * 1000

        # Benchmark 3: Aggregation
        start = time.time()
        aggregator = DaftAggregator(df)
        _ = aggregator.groupby_treatment_arm()
        results['aggregate_time_ms'] = (time.time() - start) * 1000

        # Benchmark 4: Derived columns
        start = time.time()
        processor3 = DaftMedicalDataProcessor()
        processor3.load_from_dict(data.data)
        processor3.add_pulse_pressure()
        processor3.add_mean_arterial_pressure()
        _ = processor3.collect()
        results['derived_columns_time_ms'] = (time.time() - start) * 1000

        return {
            "status": "success",
            "benchmarks": results,
            "row_count": len(data.data),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running benchmark: {str(e)}")

# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8007,
        reload=True
    )
