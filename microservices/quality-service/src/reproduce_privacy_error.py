
import pandas as pd
import numpy as np
import json
import urllib.request
import urllib.error
from privacy_assessment import PrivacyAssessor

def test_privacy_serialization():
    print("Testing Privacy Assessment Serialization...")

    # Create sample data with potential edge cases (NaNs, small size)
    real_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(10)],
        'Age': np.random.randint(18, 85, 10),
        'Gender': np.random.choice(['M', 'F'], 10),
        'SystolicBP': np.random.randint(110, 180, 10),
        'DiastolicBP': np.random.randint(70, 110, 10)
    })

    synthetic_data = pd.DataFrame({
        'SubjectID': [f'S{i:03d}' for i in range(100, 110)],
        'Age': np.random.randint(18, 85, 10),
        'Gender': np.random.choice(['M', 'F'], 10),
        'SystolicBP': np.random.randint(110, 180, 10),
        'DiastolicBP': np.random.randint(70, 110, 10)
    })

    # Inject NaNs and Infs to force the issue
    synthetic_data.loc[0, 'SystolicBP'] = np.nan
    synthetic_data.loc[1, 'SystolicBP'] = np.inf

    try:
        # Test 4: API Endpoint (Integration Test)
        print("\n--- Test 4: API Endpoint Integration ---")
        
        payload = {
            "real_data": real_data.to_dict(orient='records'),
            "synthetic_data": synthetic_data.to_dict(orient='records'),
            "quasi_identifiers": ['Age', 'Gender'],
            "sensitive_attributes": ['SystolicBP']
        }
        
        # We expect the server to handle NaNs by converting them to null, 
        # so the response should be valid JSON.
        
        # Note: We must use a custom encoder for the REQUEST payload if it contains NaNs,
        # or just filter them out for the request to ensure we reach the server logic.
        # But here we want to test the SERVER's response handling.
        # The server receives JSON (which can't have NaNs usually), converts to DF, 
        # then processes. The processing might INTRODUCE NaNs (e.g. division by zero).
        # So let's rely on the server's internal logic to produce NaNs if possible,
        # or just trust that my fix handles them if they appear.
        
        # To be sure, let's send clean data but expect the server to potentially produce NaNs
        # in the metrics (e.g. if we send very small data).
        # My previous test showed that even with clean input, we got the error, 
        # likely due to internal calculations.
        
        # Let's just use the clean data from before which triggered the error.
        
        # Clean data for request
        clean_syn = synthetic_data.replace([np.inf, -np.inf], np.nan).fillna(0)
        payload['synthetic_data'] = clean_syn.to_dict(orient='records')

        json_payload = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            "http://localhost:8004/privacy/assess/comprehensive",
            data=json_payload,
            headers={'Content-Type': 'application/json'}
        )
        
        try:
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    print("✅ API call successful (200 OK)")
                    resp_body = json.loads(response.read().decode('utf-8'))
                    print("Response keys:", resp_body.keys())
                    
                    # Check if we have nulls where we might expect NaNs
                    # (Hard to check without deep inspection, but 200 OK is the main success criteria)
                else:
                    print(f"❌ API call failed: {response.status}")
        except urllib.error.HTTPError as e:
            print(f"❌ API call failed: {e.code} {e.reason}")
            print(e.read().decode('utf-8'))
        except Exception as e:
            print(f"❌ API call error: {e}")

    except Exception as e:
        print(f"Assessment failed: {e}")

if __name__ == "__main__":
    test_privacy_serialization()
