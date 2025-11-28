# Scaling to Millions of Records: Complete Guide

## 📊 Current State Analysis

### Records Generated So Far

**Answer: ~400-600 records per run (not persistently saved)**

**Files on Disk:**
- ✗ No `synthetic_vitals_mvn.csv`
- ✗ No `synthetic_vitals_bootstrap.csv`
- ✗ No `synthetic_vitals_rules.csv`
- ✗ No `synthetic_vitals_llm.csv`

**Real Data (Baseline):**
- ✅ `pilot_trial_cleaned.csv`: 945 records
- ✅ `pilot_trial.csv`: 2,079 records (original with duplicates)

### Why No Saved Files?

1. **API-based generation**: Data returned as JSON, not saved server-side
2. **Test scripts**: Generate data temporarily in memory
3. **Dashboards**: Generate dynamically for visualization
4. **No persistent storage**: Architecture designed for on-demand generation

---

## ⚡ Current Performance Benchmarks

### Generation Speed (Tested)

| Method | Records | Time | Records/Second |
|--------|---------|------|----------------|
| **MVN** | 4,000 | 137ms | ~29,000/sec |
| **Bootstrap** | 4,065 | 29ms | ~140,000/sec |
| **Rules** | 4,000 | ~50ms | ~80,000/sec |
| **LLM** | 200 | ~2-3 sec | ~70/sec |

### Memory Usage

- **1 million records**: ~0.21 GB
- **10 million records**: ~2.1 GB
- **100 million records**: ~21 GB

### Extrapolated Performance (Single Core)

| Target Records | MVN Time | Bootstrap Time | Memory |
|----------------|----------|----------------|--------|
| 100,000 | 3.5 sec | 0.7 sec | 21 MB |
| 1,000,000 | 35 sec | 7 sec | 210 MB |
| 10,000,000 | 5.8 min | 1.2 min | 2.1 GB |
| 100,000,000 | 58 min | 12 min | 21 GB |

---

## ❌ Current Limitations (Blockers)

### 1. API Timeout (CRITICAL ⛔)

**Problem:**
```python
# Current architecture
@app.post("/generate/mvn")
async def generate_mvn(request: GenerateRequest):
    df = generate_vitals_mvn(n_per_arm=request.n_per_arm)  # ← Blocks here
    return df.to_dict(orient="records")  # ← Timeout before this
```

**Issues:**
- FastAPI default timeout: 30-60 seconds
- Cannot return millions of records in HTTP response
- Client disconnects before completion
- No way to resume or retry

**Impact:** **Cannot generate > ~10,000 records via API**

---

### 2. Synchronous Architecture (CRITICAL ⛔)

**Problem:**
- All generation happens in request/response cycle
- No background job processing
- No progress tracking
- User must wait for completion

**Current Flow:**
```
User → API Request → Generate → Block → Return JSON
      (waits 30-60s)           ↑
                               stuck here for millions
```

**Impact:** **User experience terrible for large datasets**

---

### 3. Database Writes (CRITICAL ⛔)

**Problem:**
```python
# Current ORM-based inserts
for record in synthetic_data:
    db_record = VitalsRecord(**record)
    db.session.add(db_record)  # ← Slow for millions
db.session.commit()  # ← Transaction overhead
```

**Issues:**
- SQLAlchemy ORM inserts: ~1,000-5,000 records/second
- Transaction overhead for millions of records
- Network latency to database
- Would take **hours** to write 1M records

**Impact:** **Database becomes bottleneck**

---

### 4. Memory Management (CONCERN ⚠️)

**Problem:**
- All data held in memory before returning
- No streaming or chunking
- 100M+ records could exceed available RAM

**Code:**
```python
# All records loaded into memory at once
df = generate_vitals_mvn(n_per_arm=50000)  # ← 200K records in RAM
return df.to_dict(orient="records")  # ← More memory for JSON
```

**Impact:** **Memory exhaustion for very large datasets**

---

### 5. File I/O (CONCERN ⚠️)

**Problem:**
```python
# Single write operation
df.to_csv("synthetic_data.csv")  # ← Slow for huge files
```

**Issues:**
- No chunked writing
- No progress indication
- Large files slow to write/transmit
- No compression options

**Impact:** **File operations become slow**

---

## 🎯 Required Changes for Millions

### Architecture Comparison

#### Current (Synchronous)
```
┌──────┐                          ┌────────────┐
│      │ POST /generate/mvn      │            │
│ User │ ─────────────────────>  │    API     │
│      │                          │            │
│      │ <─────────────────────  │ (blocks)   │
│      │   Returns JSON           │            │
└──────┘   (times out at 60s)    └────────────┘
           Max: ~10,000 records
```

#### Target (Asynchronous)
```
┌──────┐                          ┌────────────┐                     ┌─────────┐
│      │ POST /generate/async    │            │  Enqueue Job       │         │
│ User │ ─────────────────────>  │    API     │ ─────────────────> │  Redis  │
│      │                          │            │                     │  Queue  │
│      │ <─────────────────────  │            │                     └─────────┘
│      │   Returns job_id         └────────────┘                          │
│      │   (immediate)                                                     │
│      │                                                                   │
│      │                          ┌────────────┐                          │
│      │ GET /jobs/{id}/status   │            │   Pick Job               │
│      │ ─────────────────────>  │   Worker   │ <────────────────────────┘
│      │                          │  Process   │
│      │ <─────────────────────  │            │  Generate in batches
│      │   Progress: 45%          │            │  Write to S3/disk
│      │                          └────────────┘
│      │                                  │
│      │ GET /jobs/{id}/download         │
│      │ ─────────────────────────────────┘
│      │   Download file URL
└──────┘   Max: Unlimited
```

---

## 🔧 Implementation Roadmap

### Phase 1: Async Job System (Week 1) 🔴 CRITICAL

#### Goal
Enable background generation with job tracking

#### Changes Required

**1.1 Add Redis Queue**

**File:** `requirements.txt`
```python
# Add to data-generation-service
redis==5.0.1
celery==5.3.4
# OR
rq==1.15.1  # Simpler alternative
```

**File:** `microservices/data-generation-service/src/queue.py` (NEW)
```python
"""
Job Queue Manager for Async Generation
"""
from redis import Redis
from rq import Queue
import os

# Initialize Redis connection
redis_conn = Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=0,
    decode_responses=True
)

# Create queue
generation_queue = Queue("generation", connection=redis_conn)

def enqueue_generation(generator_type: str, params: dict) -> str:
    """
    Enqueue a generation job

    Args:
        generator_type: "mvn", "bootstrap", "rules", "llm"
        params: Generation parameters (n_per_arm, target_effect, etc.)

    Returns:
        job_id: Unique job identifier
    """
    from worker import generate_async  # Import task

    job = generation_queue.enqueue(
        generate_async,
        generator_type=generator_type,
        params=params,
        job_timeout="24h",  # Allow up to 24 hours
        result_ttl=86400 * 7  # Keep results 7 days
    )

    return job.id

def get_job_status(job_id: str) -> dict:
    """
    Get job status and progress

    Returns:
        {
            "job_id": str,
            "status": "queued|started|finished|failed",
            "progress": float,  # 0.0 to 1.0
            "result": dict,  # When finished
            "error": str  # When failed
        }
    """
    from rq.job import Job

    job = Job.fetch(job_id, connection=redis_conn)

    return {
        "job_id": job_id,
        "status": job.get_status(),
        "progress": job.meta.get("progress", 0.0),
        "records_generated": job.meta.get("records_generated", 0),
        "total_records": job.meta.get("total_records", 0),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "ended_at": job.ended_at.isoformat() if job.ended_at else None,
        "result": job.result if job.is_finished else None,
        "error": str(job.exc_info) if job.is_failed else None
    }
```

**1.2 Add Background Worker**

**File:** `microservices/data-generation-service/src/worker.py` (NEW)
```python
"""
Background Worker for Async Generation
"""
from generators import (
    generate_vitals_mvn,
    generate_vitals_bootstrap,
    generate_vitals_rules,
    load_pilot_vitals
)
import pandas as pd
from pathlib import Path
import boto3
import os
from rq import get_current_job

def update_progress(current: int, total: int):
    """Update job progress in Redis"""
    job = get_current_job()
    if job:
        progress = current / total if total > 0 else 0
        job.meta["progress"] = progress
        job.meta["records_generated"] = current
        job.meta["total_records"] = total
        job.save_meta()

def generate_async(generator_type: str, params: dict) -> dict:
    """
    Background task for async generation

    Args:
        generator_type: "mvn", "bootstrap", "rules", "llm"
        params: {
            "n_per_arm": int,
            "target_effect": float,
            "output_format": "csv|parquet",
            "upload_to_s3": bool
        }

    Returns:
        {
            "records": int,
            "file_path": str,
            "download_url": str
        }
    """
    n_per_arm = params.get("n_per_arm", 50)
    target_effect = params.get("target_effect", -5.0)
    output_format = params.get("output_format", "csv")
    upload_to_s3 = params.get("upload_to_s3", False)

    # Estimate total records
    total_records = n_per_arm * 2 * 4  # 2 arms, 4 visits
    update_progress(0, total_records)

    # Generate data
    if generator_type == "mvn":
        df = generate_vitals_mvn(
            n_per_arm=n_per_arm,
            target_effect=target_effect
        )
    elif generator_type == "bootstrap":
        real_data = load_pilot_vitals(use_cleaned=True)
        df = generate_vitals_bootstrap(
            real_data,
            n_per_arm=n_per_arm,
            target_effect=target_effect
        )
    elif generator_type == "rules":
        from generators import generate_vitals_rules
        df = generate_vitals_rules(
            n_per_arm=n_per_arm,
            target_effect=target_effect
        )
    else:
        raise ValueError(f"Unknown generator: {generator_type}")

    records_generated = len(df)
    update_progress(records_generated, total_records)

    # Save to file
    output_dir = Path("/tmp/synthetic_data")
    output_dir.mkdir(exist_ok=True)

    job = get_current_job()
    file_name = f"{generator_type}_{job.id}.{output_format}"
    file_path = output_dir / file_name

    if output_format == "csv":
        df.to_csv(file_path, index=False)
    elif output_format == "parquet":
        df.to_parquet(file_path, index=False, compression="snappy")

    # Upload to S3 (optional)
    download_url = None
    if upload_to_s3:
        s3 = boto3.client("s3")
        bucket = os.getenv("S3_BUCKET", "synthetic-data-output")
        s3_key = f"generated/{file_name}"
        s3.upload_file(str(file_path), bucket, s3_key)
        download_url = f"https://{bucket}.s3.amazonaws.com/{s3_key}"
    else:
        download_url = f"/download/{file_name}"

    return {
        "records": records_generated,
        "file_path": str(file_path),
        "download_url": download_url,
        "file_size_mb": file_path.stat().st_size / (1024 * 1024)
    }
```

**1.3 Update API Endpoints**

**File:** `microservices/data-generation-service/src/main.py`

Add new endpoints:

```python
from queue import enqueue_generation, get_job_status
from fastapi.responses import FileResponse

@app.post("/generate/async")
async def generate_async_endpoint(request: AsyncGenerateRequest):
    """
    Asynchronous generation - Returns job ID immediately

    Use this for large datasets (>10,000 records)

    Request:
        {
            "generator_type": "mvn|bootstrap|rules",
            "n_per_arm": 125000,  # Up to millions
            "target_effect": -5.0,
            "output_format": "csv|parquet",
            "upload_to_s3": false
        }

    Response:
        {
            "job_id": "abc123",
            "status": "queued",
            "estimated_time_seconds": 45
        }
    """
    # Estimate time
    records_per_sec = 29000 if request.generator_type == "mvn" else 140000
    total_records = request.n_per_arm * 2 * 4
    estimated_time = total_records / records_per_sec

    # Enqueue job
    job_id = enqueue_generation(
        generator_type=request.generator_type,
        params=request.dict()
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "estimated_time_seconds": int(estimated_time),
        "status_url": f"/jobs/{job_id}/status",
        "download_url": f"/jobs/{job_id}/download"
    }

@app.get("/jobs/{job_id}/status")
async def get_job_status_endpoint(job_id: str):
    """
    Get job status and progress

    Response:
        {
            "job_id": "abc123",
            "status": "started",
            "progress": 0.45,
            "records_generated": 450000,
            "total_records": 1000000,
            "started_at": "2025-11-12T10:30:00",
            "estimated_completion": "2025-11-12T10:35:00"
        }
    """
    status = get_job_status(job_id)

    # Calculate estimated completion
    if status["status"] == "started" and status["progress"] > 0:
        import datetime
        started_at = datetime.datetime.fromisoformat(status["started_at"])
        elapsed = (datetime.datetime.utcnow() - started_at).total_seconds()
        estimated_total = elapsed / status["progress"]
        estimated_completion = started_at + datetime.timedelta(seconds=estimated_total)
        status["estimated_completion"] = estimated_completion.isoformat()

    return status

@app.get("/jobs/{job_id}/download")
async def download_job_result(job_id: str):
    """
    Download generated file

    Returns file if job is complete, else error
    """
    status = get_job_status(job_id)

    if status["status"] != "finished":
        raise HTTPException(
            status_code=400,
            detail=f"Job not finished. Current status: {status['status']}"
        )

    file_path = status["result"]["file_path"]

    if not Path(file_path).exists():
        raise HTTPException(
            status_code=404,
            detail="File not found. It may have been deleted."
        )

    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=Path(file_path).name
    )
```

**1.4 Start Worker Process**

**File:** `microservices/data-generation-service/start_worker.sh` (NEW)
```bash
#!/bin/bash
# Start RQ worker for background generation

cd "$(dirname "$0")/src"

echo "Starting RQ worker for synthetic data generation..."
echo "Press Ctrl+C to stop"

rq worker generation \
  --url redis://localhost:6379 \
  --path . \
  --verbose
```

**1.5 Docker Compose Update**

**File:** `docker-compose.yml`

Add Redis and worker services:

```yaml
services:
  # ... existing services ...

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  generation-worker:
    build:
      context: ./microservices/data-generation-service
      dockerfile: Dockerfile
    command: rq worker generation --url redis://redis:6379
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - DATABASE_URL=postgresql://user:pass@postgres:5432/db
      - S3_BUCKET=synthetic-data-output
    volumes:
      - ./data:/tmp/synthetic_data

volumes:
  redis_data:
```

---

### Phase 2: Optimize Generation (Week 2) 🟡 HIGH PRIORITY

#### Goal
Improve generation speed through vectorization and parallelization

#### Changes Required

**2.1 Vectorize MVN Generation**

**File:** `microservices/data-generation-service/src/generators.py`

**Current (Loop-based):**
```python
def generate_vitals_mvn(n_per_arm=50, ...):
    rows = []
    for arm, subjects in [("Active", subj_active), ("Placebo", subj_placebo)]:
        for sid in subjects:  # ← Loop per subject
            for visit in VISITS:  # ← Loop per visit
                m = models[(visit, arm)]
                x = rng.multivariate_normal(mean=m["mu"], cov=m["cov"], size=1)[0]
                # ...
                rows.append([...])  # ← List append slow
```

**Optimized (Vectorized):**
```python
def generate_vitals_mvn_vectorized(n_per_arm=50, ...):
    """
    Vectorized MVN generation - 5-10x faster
    """
    # Pre-allocate arrays
    n_subjects = n_per_arm * 2
    n_visits = len(VISITS)
    n_records = n_subjects * n_visits

    # Generate all samples at once
    all_samples = []
    for visit in VISITS:
        for arm in ["Active", "Placebo"]:
            m = models[(visit, arm)]
            # Generate n_per_arm samples in one call
            samples = rng.multivariate_normal(
                mean=m["mu"],
                cov=m["cov"],
                size=n_per_arm  # ← Single call, not loop
            )
            all_samples.append(samples)

    # Stack and reshape
    all_samples = np.vstack(all_samples)

    # Create DataFrame directly from arrays (faster than list of dicts)
    df = pd.DataFrame({
        "SubjectID": np.repeat(subject_ids, n_visits),
        "VisitName": np.tile(VISITS, n_subjects),
        "TreatmentArm": np.repeat(["Active"]*n_per_arm + ["Placebo"]*n_per_arm, n_visits),
        "SystolicBP": np.clip(all_samples[:, 0].round(), 95, 200).astype(int),
        "DiastolicBP": np.clip(all_samples[:, 1].round(), 55, 130).astype(int),
        "HeartRate": np.clip(all_samples[:, 2].round(), 50, 120).astype(int),
        "Temperature": np.clip(all_samples[:, 3], 35.0, 40.0)
    })

    return df
```

**Performance Gain:** 5-10x faster for large n_per_arm

---

**2.2 Optimize Bootstrap Concat**

**Current (Multiple concat):**
```python
def generate_vitals_bootstrap(training_df, n_per_arm=50, ...):
    syn = pd.DataFrame()
    for _ in range(n_per_arm * 2):
        sample = training_df.sample(n=4, replace=True)
        syn = pd.concat([syn, sample])  # ← Slow repeated concat
```

**Optimized (Pre-allocate):**
```python
def generate_vitals_bootstrap_optimized(training_df, n_per_arm=50, ...):
    """
    Optimized bootstrap - pre-allocate and batch operations
    """
    n_subjects = n_per_arm * 2
    samples_per_subject = 4

    # Sample all at once
    indices = rng.choice(
        len(training_df),
        size=n_subjects * samples_per_subject,
        replace=True
    )

    # Select rows once
    syn = training_df.iloc[indices].copy()

    # Apply jitter vectorized
    numeric_cols = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
    for col in numeric_cols:
        std = training_df[col].std()
        jitter = rng.normal(0, std * jitter_frac, size=len(syn))
        syn[col] = syn[col] + jitter

    return syn
```

**Performance Gain:** 3-5x faster

---

**2.3 Add Batch Generation with Progress**

**File:** `microservices/data-generation-service/src/generators.py`

```python
def generate_in_batches(
    generator_func,
    total_n_per_arm: int,
    batch_size: int = 10000,
    progress_callback=None,
    **kwargs
) -> pd.DataFrame:
    """
    Generate large datasets in batches to manage memory

    Args:
        generator_func: generate_vitals_mvn or generate_vitals_bootstrap
        total_n_per_arm: Total subjects per arm (can be millions)
        batch_size: Subjects per batch (default 10,000)
        progress_callback: Function to call with (current, total)
        **kwargs: Other args for generator_func

    Returns:
        DataFrame with all records (or writes to file if too large)

    Example:
        df = generate_in_batches(
            generate_vitals_mvn,
            total_n_per_arm=125000,  # 1M records
            batch_size=10000,
            progress_callback=update_progress
        )
    """
    batches = []
    n_batches = (total_n_per_arm + batch_size - 1) // batch_size

    for batch_idx in range(n_batches):
        # Calculate batch size (last batch may be smaller)
        current_batch_size = min(batch_size, total_n_per_arm - batch_idx * batch_size)

        # Generate batch
        batch_df = generator_func(n_per_arm=current_batch_size, **kwargs)
        batches.append(batch_df)

        # Update progress
        if progress_callback:
            current = (batch_idx + 1) * batch_size * 2 * 4  # 2 arms, 4 visits
            total = total_n_per_arm * 2 * 4
            progress_callback(min(current, total), total)

    # Concatenate all batches
    return pd.concat(batches, ignore_index=True)
```

---

**2.4 Add Parallel Generation**

**File:** `microservices/data-generation-service/src/parallel.py` (NEW)

```python
"""
Parallel generation using multiprocessing
"""
from multiprocessing import Pool, cpu_count
from generators import generate_vitals_mvn
import pandas as pd

def generate_parallel(
    generator_type: str,
    n_per_arm: int,
    n_workers: int = None,
    **kwargs
) -> pd.DataFrame:
    """
    Generate synthetic data in parallel across multiple cores

    Args:
        generator_type: "mvn" or "bootstrap"
        n_per_arm: Total subjects per arm
        n_workers: Number of parallel workers (default: CPU count)
        **kwargs: Other generation parameters

    Returns:
        Combined DataFrame from all workers

    Example:
        # Generate 1M records using 8 cores
        df = generate_parallel("mvn", n_per_arm=125000, n_workers=8)
    """
    if n_workers is None:
        n_workers = cpu_count()

    # Divide work among workers
    per_worker = n_per_arm // n_workers
    remainder = n_per_arm % n_workers

    # Create tasks
    tasks = []
    for i in range(n_workers):
        worker_n_per_arm = per_worker + (1 if i < remainder else 0)
        seed = kwargs.get("seed", 123) + i  # Different seed per worker
        tasks.append((generator_type, worker_n_per_arm, {**kwargs, "seed": seed}))

    # Execute in parallel
    with Pool(n_workers) as pool:
        results = pool.starmap(_generate_worker, tasks)

    # Combine results
    return pd.concat(results, ignore_index=True)

def _generate_worker(generator_type: str, n_per_arm: int, params: dict):
    """Worker function for parallel generation"""
    if generator_type == "mvn":
        return generate_vitals_mvn(n_per_arm=n_per_arm, **params)
    # ... other generators
```

**Performance Gain:** Near-linear speedup with CPU cores (8 cores = 8x faster)

---

**2.5 Add Chunked File Writing**

**File:** `microservices/data-generation-service/src/io_utils.py` (NEW)

```python
"""
Efficient file I/O for large datasets
"""
import pandas as pd
from pathlib import Path

def write_csv_chunked(
    df_or_generator,
    output_path: Path,
    chunk_size: int = 100000,
    progress_callback=None
):
    """
    Write large DataFrame to CSV in chunks

    Args:
        df_or_generator: DataFrame or generator yielding chunks
        output_path: Output file path
        chunk_size: Records per chunk
        progress_callback: Function to call with (current, total)
    """
    if isinstance(df_or_generator, pd.DataFrame):
        # Convert DataFrame to chunks
        df = df_or_generator
        total_records = len(df)
        chunks = (df[i:i+chunk_size] for i in range(0, total_records, chunk_size))
    else:
        chunks = df_or_generator
        total_records = None

    # Write header
    with open(output_path, 'w') as f:
        first_chunk = next(chunks)
        first_chunk.to_csv(f, index=False, mode='w')

        records_written = len(first_chunk)
        if progress_callback:
            progress_callback(records_written, total_records)

        # Write remaining chunks (append, no header)
        for chunk in chunks:
            chunk.to_csv(f, index=False, mode='a', header=False)
            records_written += len(chunk)
            if progress_callback:
                progress_callback(records_written, total_records)

def write_parquet_chunked(
    df_or_generator,
    output_path: Path,
    chunk_size: int = 100000,
    progress_callback=None
):
    """
    Write large DataFrame to Parquet with optimal compression

    Parquet advantages:
    - 10-100x compression vs CSV
    - Column-oriented (faster queries)
    - Preserves data types
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    # Similar implementation with parquet writer
    # ...
```

---

### Phase 3: Scale & Monitor (Week 3) 🟢 MEDIUM PRIORITY

#### Goal
Production-ready scaling with monitoring and distributed generation

**3.1 Add Distributed Generation**

**File:** `microservices/data-generation-service/src/distributed.py` (NEW)

```python
"""
Distributed generation across multiple worker nodes
"""

def partition_generation(
    total_n_per_arm: int,
    n_workers: int
) -> list[dict]:
    """
    Partition large generation job across workers

    Args:
        total_n_per_arm: Total subjects per arm (e.g., 1 million)
        n_workers: Number of worker nodes

    Returns:
        List of tasks for each worker

    Example:
        # Distribute 1M records across 10 workers
        tasks = partition_generation(125000, n_workers=10)
        # Each worker generates 12,500 subjects
    """
    per_worker = total_n_per_arm // n_workers
    remainder = total_n_per_arm % n_workers

    tasks = []
    for i in range(n_workers):
        n_per_arm = per_worker + (1 if i < remainder else 0)
        tasks.append({
            "worker_id": i,
            "n_per_arm": n_per_arm,
            "seed": 123 + i,
            "subject_id_offset": i * per_worker * 2
        })

    return tasks

def merge_results(result_files: list[Path], output_file: Path):
    """
    Merge results from distributed workers

    Efficiently combines Parquet files without loading all into memory
    """
    import pyarrow.parquet as pq

    # Read schemas
    tables = [pq.read_table(f) for f in result_files]

    # Concatenate
    combined = pa.concat_tables(tables)

    # Write merged file
    pq.write_table(combined, output_file, compression='snappy')
```

**3.2 Add Monitoring & Metrics**

**File:** `microservices/data-generation-service/src/metrics.py` (NEW)

```python
"""
Prometheus metrics for generation monitoring
"""
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics
records_generated_total = Counter(
    'synthetic_records_generated_total',
    'Total synthetic records generated',
    ['generator_type']
)

generation_duration_seconds = Histogram(
    'generation_duration_seconds',
    'Time to generate synthetic data',
    ['generator_type', 'n_per_arm_bucket']
)

active_generation_jobs = Gauge(
    'active_generation_jobs',
    'Number of generation jobs currently running'
)

def track_generation(generator_type: str, n_per_arm: int):
    """
    Decorator to track generation metrics
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Track active jobs
            active_generation_jobs.inc()

            # Time execution
            start_time = time.time()
            try:
                result = func(*args, **kwargs)

                # Track success
                records_generated_total.labels(
                    generator_type=generator_type
                ).inc(len(result))

                return result
            finally:
                # Track duration
                duration = time.time() - start_time
                bucket = _get_bucket(n_per_arm)
                generation_duration_seconds.labels(
                    generator_type=generator_type,
                    n_per_arm_bucket=bucket
                ).observe(duration)

                active_generation_jobs.dec()

        return wrapper
    return decorator

def _get_bucket(n_per_arm: int) -> str:
    """Categorize n_per_arm into buckets for metrics"""
    if n_per_arm < 100:
        return "small"
    elif n_per_arm < 1000:
        return "medium"
    elif n_per_arm < 10000:
        return "large"
    else:
        return "xlarge"
```

**3.3 Add Grafana Dashboard Config**

**File:** `monitoring/grafana/dashboards/synthetic-generation.json` (NEW)

```json
{
  "dashboard": {
    "title": "Synthetic Data Generation",
    "panels": [
      {
        "title": "Records Generated (Total)",
        "targets": [
          {
            "expr": "sum(rate(synthetic_records_generated_total[5m])) by (generator_type)"
          }
        ]
      },
      {
        "title": "Active Generation Jobs",
        "targets": [
          {
            "expr": "active_generation_jobs"
          }
        ]
      },
      {
        "title": "Generation Duration (p95)",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, generation_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

---

## 📊 Performance Targets

### After All Optimizations

| Records | Original Time | Optimized Time | Speedup |
|---------|--------------|----------------|---------|
| 100K | 3.5 sec | 0.4 sec | 8.75x |
| 1M | 35 sec | 4 sec | 8.75x |
| 10M | 5.8 min | 40 sec | 8.7x |
| 100M | 58 min | 6.7 min | 8.7x |

**With 8-core parallelization:**
- 1M records: ~0.5 seconds
- 10M records: ~5 seconds
- 100M records: ~50 seconds

---

## 🚀 Deployment Guide

### Local Development

**1. Start Redis:**
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

**2. Start Worker:**
```bash
cd microservices/data-generation-service/src
rq worker generation --url redis://localhost:6379
```

**3. Start API:**
```bash
uvicorn main:app --reload --port 8002
```

**4. Test Async Generation:**
```bash
# Enqueue job
curl -X POST http://localhost:8002/generate/async \
  -H "Content-Type: application/json" \
  -d '{
    "generator_type": "mvn",
    "n_per_arm": 125000,
    "target_effect": -5.0
  }'

# Response: {"job_id": "abc123", "status": "queued"}

# Check status
curl http://localhost:8002/jobs/abc123/status

# Download result
curl http://localhost:8002/jobs/abc123/download -o synthetic_1m.csv
```

---

### Production Deployment (Kubernetes)

**File:** `kubernetes/deployments/generation-worker.yaml` (NEW)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: generation-worker
spec:
  replicas: 4  # Scale based on load
  selector:
    matchLabels:
      app: generation-worker
  template:
    metadata:
      labels:
        app: generation-worker
    spec:
      containers:
      - name: worker
        image: synthetic-data/generation-worker:latest
        command: ["rq", "worker", "generation"]
        env:
        - name: REDIS_HOST
          value: "redis-service"
        - name: REDIS_PORT
          value: "6379"
        - name: S3_BUCKET
          value: "synthetic-data-prod"
        resources:
          requests:
            memory: "2Gi"
            cpu: "2000m"
          limits:
            memory: "8Gi"
            cpu: "4000m"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: generation-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: generation-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 🎯 Testing Plan

### Load Testing Script

**File:** `tests/load_test_generation.py` (NEW)

```python
"""
Load test for million-scale generation
"""
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def test_million_records():
    """Test generating 1 million records"""
    print("Testing 1M record generation...")

    # Submit job
    response = requests.post(
        "http://localhost:8002/generate/async",
        json={
            "generator_type": "mvn",
            "n_per_arm": 125000,
            "output_format": "parquet"
        }
    )
    job_id = response.json()["job_id"]
    print(f"Job submitted: {job_id}")

    # Poll status
    start_time = time.time()
    while True:
        status_response = requests.get(
            f"http://localhost:8002/jobs/{job_id}/status"
        )
        status = status_response.json()

        print(f"Progress: {status['progress']*100:.1f}% - "
              f"{status['records_generated']:,} / {status['total_records']:,}")

        if status["status"] == "finished":
            break
        elif status["status"] == "failed":
            raise Exception(f"Job failed: {status['error']}")

        time.sleep(2)

    elapsed = time.time() - start_time
    records = status["result"]["records"]
    rate = records / elapsed

    print(f"\n✅ Success!")
    print(f"   Records: {records:,}")
    print(f"   Time: {elapsed:.1f} seconds")
    print(f"   Rate: {rate:,.0f} records/second")

def test_concurrent_jobs():
    """Test multiple concurrent generation jobs"""
    print("Testing 10 concurrent jobs...")

    def submit_job(i):
        response = requests.post(
            "http://localhost:8002/generate/async",
            json={
                "generator_type": "mvn",
                "n_per_arm": 10000
            }
        )
        return response.json()["job_id"]

    # Submit 10 jobs concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        job_ids = list(executor.map(submit_job, range(10)))

    print(f"Submitted {len(job_ids)} jobs")
    # Wait for all to complete...

if __name__ == "__main__":
    test_million_records()
    test_concurrent_jobs()
```

---

## 📋 Summary Checklist

### Phase 1: Async System ✅
- [ ] Add Redis queue (`queue.py`)
- [ ] Create background worker (`worker.py`)
- [ ] Add async endpoints (`/generate/async`, `/jobs/{id}/status`, `/jobs/{id}/download`)
- [ ] Update docker-compose with Redis and worker services
- [ ] Test async generation with 100K records

### Phase 2: Optimization ✅
- [ ] Vectorize MVN generation
- [ ] Optimize Bootstrap concat operations
- [ ] Add batch generation with progress tracking
- [ ] Implement parallel generation (multiprocessing)
- [ ] Add chunked file writing
- [ ] Test generation speed improvements

### Phase 3: Scale & Monitor ✅
- [ ] Add distributed generation support
- [ ] Implement Prometheus metrics
- [ ] Create Grafana dashboards
- [ ] Add Kubernetes HPA for workers
- [ ] Load test with 1M, 10M, 100M records
- [ ] Document production deployment

---

## 🎓 Key Takeaways

### Current State
- ✅ **Algorithm fast**: 29K-140K records/second
- ✅ **Memory efficient**: 0.21 GB per million
- ❌ **Architecture blocking**: Timeouts, no async, slow DB writes

### To Generate Millions
**Must Have (Blocking):**
1. Async job queue (Redis/RQ)
2. Background workers
3. Bulk database writes
4. Chunked/streaming output

**Should Have (Performance):**
5. Vectorized generation
6. Parallel processing
7. Progress tracking

**Nice to Have (Scale):**
8. Distributed generation
9. Monitoring/metrics
10. Auto-scaling workers

### Effort Estimate
- **Phase 1 (Critical)**: 1 week - Enables millions
- **Phase 2 (Performance)**: 1 week - Makes it fast
- **Phase 3 (Production)**: 1 week - Makes it robust

**Total**: 3 weeks for production-ready million-scale generation

---

## 📚 References

**Technologies Used:**
- **Redis**: Job queue storage
- **RQ (Redis Queue)**: Python task queue
- **Multiprocessing**: Parallel CPU utilization
- **Parquet**: Columnar storage format
- **Prometheus + Grafana**: Monitoring
- **Kubernetes HPA**: Auto-scaling

**Alternatives Considered:**
- **Celery** vs RQ: RQ simpler, Celery more features
- **Ray** vs Multiprocessing: Ray for distributed, MP for single-node
- **Dask** vs Pandas: Dask for 100M+ records

---

**Document Version**: 1.0
**Last Updated**: 2025-11-12
**Status**: Implementation pending - No changes made yet

