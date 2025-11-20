from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class SaveDataRequest(BaseModel):
    """Request model for saving generated data"""
    dataset_name: str = Field(..., description="Name of the dataset")
    dataset_type: str = Field(..., description="Type of data (vitals, demographics, labs, ae)")
    data: List[Dict[str, Any]] = Field(..., description="The actual data records")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")

class LoadDataResponse(BaseModel):
    """Response model for loading data"""
    id: int
    dataset_name: str
    dataset_type: str
    data: List[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
