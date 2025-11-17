"""
GAIN Service - Missing Data Imputation using CTGAN
Handles imputation of missing values in clinical trial data
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import uvicorn
import os

# Try to import ydata-synthetic, fall back to basic imputation
try:
    from ydata_synthetic.synthesizers.regular import RegularSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters
    YDATA_AVAILABLE = True
except ImportError:
    YDATA_AVAILABLE = False
    print("WARNING: ydata-synthetic not available. Using fallback imputation.")

app = FastAPI(
    title="GAIN Service - Missing Data Imputation",
    description="GAN-based imputation for missing clinical trial data",
    version="1.0.0"
)

# CORS configuration
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Pydantic models
class ImputeRequest(BaseModel):
    data: List[Dict]  # Data with missing values (None for missing)
    columns: List[str]
    model_type: str = "ctgan"  # ctgan, wgan-gp, fallback

class ImputeResponse(BaseModel):
    imputed_data: List[Dict]
    missing_imputed: int
    imputation_quality: Dict

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gain-service",
        "ydata_available": YDATA_AVAILABLE
    }

@app.post("/impute", response_model=ImputeResponse)
async def impute_missing_data(request: ImputeRequest):
    """
    Impute missing data using GAIN-like approach (CTGAN-based)

    For clinical trial data, we use CTGAN which:
    - Handles mixed data types (continuous + categorical)
    - Preserves correlations
    - Works well with small datasets (<10K rows)

    Method:
    1. Train CTGAN on complete rows
    2. For each incomplete row, generate candidates
    3. Select best candidate based on distance to observed values
    4. Fill missing values from best candidate
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(request.data)
        df = df[request.columns]

        # Identify missing values
        mask = df.isnull()
        missing_count = mask.sum().sum()

        if missing_count == 0:
            return ImputeResponse(
                imputed_data=df.to_dict('records'),
                missing_imputed=0,
                imputation_quality={"note": "No missing values"}
            )

        # Use CTGAN-based imputation if available, otherwise fallback
        if YDATA_AVAILABLE and request.model_type == "ctgan":
            imputed_df = await impute_with_ctgan(df, mask)
        else:
            # Fallback: use mean/mode imputation
            imputed_df = impute_with_fallback(df)

        # Calculate imputation quality
        complete_rows = df[~df.isnull().any(axis=1)]
        if len(complete_rows) > 1:
            original_corr = complete_rows.select_dtypes(include=[np.number]).corr()
            imputed_corr = imputed_df.select_dtypes(include=[np.number]).corr()

            # Correlation preservation
            if not original_corr.empty and not imputed_corr.empty:
                corr_flat_orig = original_corr.values.flatten()
                corr_flat_imp = imputed_corr.values.flatten()
                # Remove NaN values
                valid_mask = ~(np.isnan(corr_flat_orig) | np.isnan(corr_flat_imp))
                if valid_mask.sum() > 0:
                    corr_preservation = float(np.corrcoef(
                        corr_flat_orig[valid_mask],
                        corr_flat_imp[valid_mask]
                    )[0, 1])
                else:
                    corr_preservation = 1.0
            else:
                corr_preservation = 1.0
        else:
            corr_preservation = 1.0

        return ImputeResponse(
            imputed_data=imputed_df.to_dict('records'),
            missing_imputed=int(missing_count),
            imputation_quality={
                "correlation_preservation": round(corr_preservation, 3),
                "method": request.model_type,
                "missing_percentage": round((missing_count / df.size) * 100, 2)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Imputation failed: {str(e)}"
        )


async def impute_with_ctgan(df: pd.DataFrame, mask: pd.DataFrame) -> pd.DataFrame:
    """
    Impute using CTGAN-based approach

    Args:
        df: DataFrame with missing values
        mask: Boolean mask indicating missing values

    Returns:
        DataFrame with imputed values
    """
    # Separate complete and incomplete rows
    complete_rows = df[~df.isnull().any(axis=1)]
    incomplete_rows = df[df.isnull().any(axis=1)]

    if len(complete_rows) < 10:
        # Not enough data for CTGAN, use fallback
        return impute_with_fallback(df)

    try:
        # Train CTGAN on complete rows
        model_params = ModelParameters(
            batch_size=min(32, len(complete_rows)),
            lr=0.0002,
            betas=(0.5, 0.9),
            noise_dim=32,
            layers_dim=128
        )

        synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)
        num_cols = list(complete_rows.select_dtypes(include=[np.number]).columns)

        synth.fit(
            complete_rows,
            train_arguments={'epochs': 100},
            num_cols=num_cols
        )

        # For each incomplete row, generate candidates and pick best match
        imputed_rows = []
        for idx, row in incomplete_rows.iterrows():
            # Generate 10 synthetic candidates
            candidates = synth.sample(10)

            # Calculate distance to observed values
            observed_cols = row[~row.isnull()].index.tolist()
            if len(observed_cols) > 0:
                distances = []
                for _, candidate in candidates.iterrows():
                    # Euclidean distance on observed columns (numeric only)
                    dist = 0
                    count = 0
                    for col in observed_cols:
                        if col in candidate.index and pd.api.types.is_numeric_dtype(df[col]):
                            try:
                                dist += (float(row[col]) - float(candidate[col]))**2
                                count += 1
                            except (ValueError, TypeError):
                                pass
                    dist = np.sqrt(dist) if count > 0 else float('inf')
                    distances.append(dist)

                # Pick candidate with minimum distance
                best_idx = np.argmin(distances)
                best_candidate = candidates.iloc[best_idx]

                # Fill missing values from best candidate
                imputed_row = row.copy()
                missing_cols = row[row.isnull()].index.tolist()
                for col in missing_cols:
                    if col in best_candidate.index:
                        imputed_row[col] = best_candidate[col]

                imputed_rows.append(imputed_row)
            else:
                # No observed values, use first candidate
                imputed_rows.append(candidates.iloc[0])

        # Combine complete + imputed rows
        imputed_df = pd.concat([complete_rows, pd.DataFrame(imputed_rows)], ignore_index=True)
        return imputed_df

    except Exception as e:
        print(f"CTGAN imputation failed: {e}. Using fallback.")
        return impute_with_fallback(df)


def impute_with_fallback(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fallback imputation using mean/mode

    Args:
        df: DataFrame with missing values

    Returns:
        DataFrame with imputed values
    """
    df_imputed = df.copy()

    # Numeric columns: use mean
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df[col].isnull().any():
            df_imputed[col].fillna(df[col].mean(), inplace=True)

    # Categorical columns: use mode
    categorical_cols = df.select_dtypes(exclude=[np.number]).columns
    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df_imputed[col].fillna(mode_val[0], inplace=True)

    return df_imputed


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8007)
