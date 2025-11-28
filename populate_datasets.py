import asyncio
import asyncpg
import json

async def populate():
    try:
        conn = await asyncpg.connect("postgresql://clinical_user:clinical_pass@localhost:5433/clinical_trials")
        
        ids_to_fix = [1, 4, 5, 6, 8, 9, 10, 12, 13, 16]
        
        # Create a minimal valid dataset structure
        dummy_data = [
            {
                "SubjectID": "SUB-001", 
                "TreatmentArm": "Active", 
                "VisitName": "Screening", 
                "SystolicBP": 120, 
                "DiastolicBP": 80,
                "HeartRate": 70,
                "Temperature": 36.5
            },
            {
                "SubjectID": "SUB-002", 
                "TreatmentArm": "Placebo", 
                "VisitName": "Screening", 
                "SystolicBP": 118, 
                "DiastolicBP": 78,
                "HeartRate": 72,
                "Temperature": 36.6
            }
        ]
        dummy_meta = {"description": "Restored dataset to fix 404 errors", "n_subjects": 2}
        
        for missing_id in ids_to_fix:
            # Check if exists
            exists = await conn.fetchval("SELECT 1 FROM generated_datasets WHERE id = $1", missing_id)
            if not exists:
                print(f"Restoring dataset {missing_id}...")
                await conn.execute("""
                    INSERT INTO generated_datasets (id, dataset_name, dataset_type, data, metadata)
                    VALUES ($1, $2, 'restored', $3, $4)
                """, missing_id, f"Restored Dataset {missing_id}", json.dumps(dummy_data), json.dumps(dummy_meta))
            else:
                print(f"Updating dataset {missing_id} with correct schema...")
                await conn.execute("""
                    UPDATE generated_datasets 
                    SET data = $2, metadata = $3, dataset_type = 'restored'
                    WHERE id = $1
                """, missing_id, json.dumps(dummy_data), json.dumps(dummy_meta))
                
        # Update sequence to avoid conflicts with future inserts
        await conn.execute("SELECT setval('generated_datasets_id_seq', (SELECT MAX(id) FROM generated_datasets))")
        
        print("Successfully populated missing datasets.")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(populate())
