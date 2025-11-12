"""
PHI (Protected Health Information) Detection
Blocks potential PHI uploads to prevent accidental exposure
Extracted from existing app.py lint_for_phi function
"""
import re
from typing import Dict, Any, List, Tuple
import pandas as pd

# Suspicious column names that might contain PHI
SUSPECT_COL_KEYS = {
    "name", "first", "last", "middle", "patient", "dob", "birth",
    "ssn", "phone", "email", "address", "street", "city", "state",
    "zip", "mrn", "member", "insurance", "device", "ip"
}

# Patterns to detect PHI in values
VALUE_PATTERNS = [
    ("email", re.compile(r"\b[^@\s]+@[^@\s]+\.[^@\s]+\b", re.I)),
    ("phone", re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("dob", re.compile(r"\b(19|20)\d{2}[-/]\d{2}[-/]\d{2}\b")),
]

def lint_for_phi(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Detect potential PHI in data
    
    Returns:
        (is_safe, findings_list) - is_safe=True means no PHI detected
    
    HIPAA Requirement: Block PHI uploads to prevent accidental exposure
    """
    findings = []
    
    # Handle dict input
    if isinstance(data, dict):
        df = pd.DataFrame([data])
    # Handle list of dicts
    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        df = pd.DataFrame(data)
    else:
        # Try to convert to DataFrame
        try:
            df = pd.DataFrame(data)
        except Exception:
            findings.append("Unable to parse data structure")
            return False, findings
    
    if df.empty:
        return True, []
    
    # Check column names for suspicious keywords
    bad_cols = [
        c for c in df.columns 
        if set(re.findall(r"[a-z]+", c.lower())) & SUSPECT_COL_KEYS
    ]
    if bad_cols:
        findings.append(f"suspicious columns detected: {bad_cols}")
    
    # Check values for PHI patterns
    for col in df.columns:
        try:
            # Sample first 200 values for performance
            series = df[col].astype(str).head(200)
        except Exception:
            continue
        
        for label, pattern in VALUE_PATTERNS:
            try:
                hit = series.str.contains(pattern, na=False).any()
                if hit:
                    findings.append(f"values in column '{col}' match {label} pattern")
            except Exception:
                continue
    
    # is_safe = no findings
    is_safe = len(findings) == 0
    return is_safe, findings

def check_dataframe_for_phi(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Direct DataFrame PHI check (for compatibility with existing code)
    """
    if df is None or df.empty:
        return True, []
    
    return lint_for_phi(df.to_dict('records'))

