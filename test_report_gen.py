import requests
import json
import pandas as pd
import numpy as np

# Create sample data
np.random.seed(42)
n = 100
real_data = pd.DataFrame({
    'SystolicBP': np.random.normal(120, 10, n),
    'DiastolicBP': np.random.normal(80, 8, n),
    'HeartRate': np.random.randint(60, 100, n)
}).to_dict(orient='records')

synthetic_data = pd.DataFrame({
    'SystolicBP': np.random.normal(120, 10, n),
    'DiastolicBP': np.random.normal(80, 8, n),
    'HeartRate': np.random.randint(60, 100, n)
}).to_dict(orient='records')

payload = {
    "method_name": "mvn",
    "real_data": real_data,
    "synthetic_data": synthetic_data,
    "generation_time_ms": 100
}

try:
    response = requests.post("http://localhost:8004/quality/report", json=payload)
    if response.status_code == 200:
        print("Report generation successful!")
        print(response.json()['report'][:500] + "...")
    else:
        print(f"Report generation failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
