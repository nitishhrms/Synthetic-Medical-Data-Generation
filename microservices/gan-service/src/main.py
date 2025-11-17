"""
GAN Service - Synthetic Data Generation using CTGAN
Handles conditional synthetic data generation for clinical trials
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import pandas as pd
import numpy as np
import uvicorn
import os

# Try to import ydata-synthetic
try:
    from ydata_synthetic.synthesizers.regular import RegularSynthesizer
    from ydata_synthetic.synthesizers import ModelParameters
    YDATA_AVAILABLE = True
except ImportError:
    YDATA_AVAILABLE = False
    print("WARNING: ydata-synthetic not available. GAN generation disabled.")

app = FastAPI(
    title="GAN Service - Synthetic Data Generation",
    description="CTGAN-based synthetic clinical trial data generation",
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
class GenerateRequest(BaseModel):
    training_data: List[Dict[str, Any]]
    n_samples: int = Field(..., ge=10, le=10000)
    condition_column: Optional[str] = None  # e.g., "TreatmentArm"
    condition_values: Optional[List[str]] = None  # e.g., ["Active", "Placebo"]
    epochs: int = Field(default=300, ge=50, le=1000)
    batch_size: Optional[int] = None

class GenerateResponse(BaseModel):
    data: List[Dict[str, Any]]
    metadata: Dict[str, Any]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "gan-service",
        "ydata_available": YDATA_AVAILABLE
    }

@app.post("/generate/ctgan", response_model=GenerateResponse)
async def generate_synthetic_ctgan(request: GenerateRequest):
    """
    Generate synthetic clinical trial data using CTGAN

    CTGAN advantages:
    - Handles mixed data types (numeric + categorical)
    - Conditional generation (treatment arms, sites, etc.)
    - Good for small-medium datasets (<10K rows)

    Conditional generation:
    - If condition_column is provided, generates data separately for each condition value
    - Ensures balanced representation across conditions
    - Preserves condition-specific patterns

    Args:
        training_data: Real data to train on
        n_samples: Number of synthetic samples to generate
        condition_column: Column to use for conditional generation (optional)
        condition_values: Values to generate for (optional)
        epochs: Training epochs (default: 300)
        batch_size: Batch size for training (auto if None)

    Returns:
        Synthetic data with metadata
    """
    if not YDATA_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ydata-synthetic library not available. Please install it."
        )

    try:
        # Convert training data
        train_df = pd.DataFrame(request.training_data)

        if len(train_df) < 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Need at least 10 training samples"
            )

        if request.condition_column and request.condition_values:
            # Conditional generation
            synthetic_df = await generate_conditional(
                train_df,
                request.condition_column,
                request.condition_values,
                request.n_samples,
                request.epochs,
                request.batch_size
            )
        else:
            # Unconditional generation
            synthetic_df = await generate_unconditional(
                train_df,
                request.n_samples,
                request.epochs,
                request.batch_size
            )

        return GenerateResponse(
            data=synthetic_df.to_dict('records'),
            metadata={
                "method": "ctgan",
                "rows": len(synthetic_df),
                "columns": list(synthetic_df.columns),
                "conditional": request.condition_column is not None,
                "training_size": len(train_df),
                "epochs": request.epochs
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Generation failed: {str(e)}"
        )


async def generate_conditional(
    train_df: pd.DataFrame,
    condition_column: str,
    condition_values: List[str],
    n_samples: int,
    epochs: int,
    batch_size: Optional[int]
) -> pd.DataFrame:
    """
    Generate synthetic data with conditional generation

    Args:
        train_df: Training data
        condition_column: Column to condition on
        condition_values: Values to generate for
        n_samples: Total samples to generate
        epochs: Training epochs
        batch_size: Batch size (auto if None)

    Returns:
        Synthetic data with balanced conditions
    """
    synthetic_dfs = []
    n_per_condition = n_samples // len(condition_values)

    for condition_val in condition_values:
        # Filter training data for this condition
        train_subset = train_df[train_df[condition_column] == condition_val]

        if len(train_subset) < 5:
            print(f"Warning: Only {len(train_subset)} samples for {condition_val}, skipping")
            continue

        # Train CTGAN on this subset
        model_params = ModelParameters(
            batch_size=batch_size or min(32, len(train_subset)),
            lr=0.0002,
            betas=(0.5, 0.9),
            noise_dim=64,
            layers_dim=256
        )

        synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)

        # Identify numeric columns
        num_cols = list(train_subset.select_dtypes(include=[np.number]).columns)

        synth.fit(
            train_subset,
            train_arguments={'epochs': epochs},
            num_cols=num_cols
        )

        # Generate synthetic samples
        synthetic = synth.sample(n_per_condition)
        synthetic[condition_column] = condition_val

        synthetic_dfs.append(synthetic)

    # Combine all conditions
    synthetic_df = pd.concat(synthetic_dfs, ignore_index=True)

    return synthetic_df


async def generate_unconditional(
    train_df: pd.DataFrame,
    n_samples: int,
    epochs: int,
    batch_size: Optional[int]
) -> pd.DataFrame:
    """
    Generate synthetic data without conditioning

    Args:
        train_df: Training data
        n_samples: Samples to generate
        epochs: Training epochs
        batch_size: Batch size (auto if None)

    Returns:
        Synthetic data
    """
    model_params = ModelParameters(
        batch_size=batch_size or min(32, len(train_df)),
        lr=0.0002,
        betas=(0.5, 0.9),
        noise_dim=64,
        layers_dim=256
    )

    synth = RegularSynthesizer(modelname='ctgan', model_parameters=model_params)
    num_cols = list(train_df.select_dtypes(include=[np.number]).columns)

    synth.fit(train_df, train_arguments={'epochs': epochs}, num_cols=num_cols)
    synthetic_df = synth.sample(n_samples)

    return synthetic_df


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8008)
