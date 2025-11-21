import asyncio
import asyncpg
import json
import requests

# Database connection
DB_URL = "postgresql://clinical_user:clinical_pass@localhost:5433/clinical_trials"

async def verify():
    # 0. Check Health
    try:
        health = requests.get("http://localhost:8001/health")
        print(f"Health Check: {health.status_code} {health.text}")
    except Exception as e:
        print(f"Health Check Failed: {e}")
        return

    # 1. Connect and Ensure Study Exists
    conn = await asyncpg.connect(DB_URL)
    try:
        await conn.execute("""
            INSERT INTO studies (study_id, study_name, phase, status, created_at)
            VALUES ('STU003', 'Fix Verification Study', 'Phase 3', 'planning', NOW())
            ON CONFLICT (study_id) DO NOTHING
        """)
        print("Ensured STU003 exists.")

        # 2. Get the generated dataset
        row = await conn.fetchrow("SELECT metadata, data FROM generated_datasets WHERE dataset_name = 'Fix_Verification_Data'")
        if not row:
            print("Dataset 'Fix_Verification_Data' not found. Please generate it first.")
            return

        vitals_data = json.loads(row['data']) if isinstance(row['data'], str) else row['data']
        print(f"Found dataset with {len(vitals_data)} records.")

        # 2. Call Import API
        payload = {
            "study_id": "STU003",
            "data": vitals_data,
            "source": "verification_script"
        }
        
        print("Sending import request to EDC Service...")
        response = requests.post("http://localhost:8001/import/synthetic", json=payload)
        
        if response.status_code == 200:
            print("Import Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Import Failed: {response.status_code}")
            print(response.text)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify())
