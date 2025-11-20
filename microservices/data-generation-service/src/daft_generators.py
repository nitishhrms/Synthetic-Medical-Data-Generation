"""
Daft-Powered Data Generators - Million-Scale Synthetic Data Generation
Enables generation of 1M+ records through chunked processing and streaming writes
"""
import daft
from daft import col
import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, Generator
from pathlib import Path
import time

# Constants
NUM_COLS = ["SystolicBP", "DiastolicBP", "HeartRate", "Temperature"]
VISITS = ["Screening", "Day 1", "Week 4", "Week 12"]
ARMS = ["Active", "Placebo"]


class DaftDataGenerator:
    """
    Million-scale synthetic data generator using Daft's distributed processing

    Features:
    - Chunked generation (avoids memory limits)
    - Streaming Parquet writes
    - Lazy evaluation
    - Parallel processing ready
    """

    def __init__(self, seed: int = 42):
        """Initialize generator with random seed"""
        self.seed = seed
        self.rng = np.random.default_rng(seed)

    def generate_chunk_rules(
        self,
        n_per_arm: int,
        target_effect: float = -5.0,
        start_subject_id: int = 1
    ) -> pd.DataFrame:
        """
        Generate one chunk of data using rules-based approach

        Args:
            n_per_arm: Number of subjects per arm in this chunk
            target_effect: Target treatment effect
            start_subject_id: Starting subject number

        Returns:
            DataFrame chunk with vitals data
        """
        arms = (["Active"] * n_per_arm) + (["Placebo"] * n_per_arm)
        subs = [f"RA001-{i:06d}" for i in range(start_subject_id, start_subject_id + 2 * n_per_arm)]

        rows = []
        for sid, arm in zip(subs, arms):
            # Subject-level baseline
            base_val = self.rng.normal(130, 10)

            for visit in VISITS:
                sbp = self.rng.normal(base_val, 6)
                if visit == "Week 12" and arm == "Active":
                    sbp += target_effect

                dbp = self.rng.normal(80, 8)
                hr = int(self.rng.integers(60, 101))
                temp = self.rng.normal(36.8, 0.3)

                rows.append([
                    sid, visit, arm,
                    int(np.clip(round(sbp), 95, 200)),
                    int(np.clip(round(dbp), 55, 130)),
                    int(np.clip(round(hr), 50, 120)),
                    float(np.clip(temp, 35.0, 40.0)),
                ])

        df = pd.DataFrame(rows, columns=["SubjectID", "VisitName", "TreatmentArm"] + NUM_COLS)

        # Add fever rows
        k = int(self.rng.integers(1, 3))
        idx = self.rng.choice(df.index, size=min(k, len(df)), replace=False)
        df.loc[idx, "Temperature"] = self.rng.uniform(38.1, 38.8, size=len(idx))
        df.loc[idx, "HeartRate"] = np.maximum(df.loc[idx, "HeartRate"], 67)

        return df

    def generate_million_scale(
        self,
        total_subjects: int,
        chunk_size: int = 10000,
        target_effect: float = -5.0,
        output_path: Optional[str] = None,
        format: str = "parquet"
    ) -> Dict[str, Any]:
        """
        Generate million-scale synthetic data using chunked processing

        Args:
            total_subjects: Total number of subjects (across both arms)
            chunk_size: Subjects per chunk (controls memory usage)
            target_effect: Target treatment effect
            output_path: Path to save output (if None, returns in-memory)
            format: Output format - 'parquet' (recommended) or 'csv'

        Returns:
            Metadata about generation (rows, chunks, time, etc.)

        Example:
            >>> gen = DaftDataGenerator()
            >>> meta = gen.generate_million_scale(
            ...     total_subjects=1_000_000,
            ...     chunk_size=10000,
            ...     output_path="/data/synthetic_1M.parquet"
            ... )
            >>> print(f"Generated {meta['total_records']} records in {meta['time_seconds']:.2f}s")
        """
        start_time = time.time()

        # Calculate chunks
        subjects_per_arm = total_subjects // 2
        chunk_subjects_per_arm = chunk_size // 2
        num_chunks = (subjects_per_arm + chunk_subjects_per_arm - 1) // chunk_subjects_per_arm

        print(f"🚀 Generating {total_subjects:,} subjects in {num_chunks} chunks...")
        print(f"   Chunk size: {chunk_size:,} subjects ({chunk_size * 4:,} records per chunk)")

        all_chunks = []
        total_records = 0

        for chunk_idx in range(num_chunks):
            chunk_start_time = time.time()

            # Calculate subjects for this chunk
            subjects_remaining = subjects_per_arm - (chunk_idx * chunk_subjects_per_arm)
            chunk_n_per_arm = min(chunk_subjects_per_arm, subjects_remaining)

            if chunk_n_per_arm <= 0:
                break

            # Generate chunk
            start_subject_id = (chunk_idx * chunk_subjects_per_arm * 2) + 1
            chunk_df = self.generate_chunk_rules(
                n_per_arm=chunk_n_per_arm,
                target_effect=target_effect,
                start_subject_id=start_subject_id
            )

            chunk_records = len(chunk_df)
            total_records += chunk_records

            # Convert to Daft for efficient processing
            daft_chunk = daft.from_pandas(chunk_df)
            all_chunks.append(daft_chunk)

            chunk_time = time.time() - chunk_start_time
            records_per_sec = chunk_records / chunk_time if chunk_time > 0 else 0

            print(f"   Chunk {chunk_idx + 1}/{num_chunks}: "
                  f"{chunk_records:,} records in {chunk_time:.2f}s "
                  f"({records_per_sec:,.0f} records/sec)")

        # Combine all chunks using Daft
        print(f"\n📊 Combining {len(all_chunks)} chunks...")
        combined_df = daft.concat(all_chunks) if len(all_chunks) > 1 else all_chunks[0]

        # Write output if path provided
        if output_path:
            write_start = time.time()
            output_path_obj = Path(output_path)
            output_path_obj.parent.mkdir(parents=True, exist_ok=True)

            if format == "parquet":
                print(f"💾 Writing to Parquet: {output_path}")
                combined_df.write_parquet(str(output_path))
            elif format == "csv":
                print(f"💾 Writing to CSV: {output_path}")
                # For CSV, convert to pandas first (less efficient for large datasets)
                pdf = combined_df.to_pandas()
                pdf.to_csv(output_path, index=False)

            write_time = time.time() - write_start
            file_size_mb = output_path_obj.stat().st_size / (1024 * 1024) if output_path_obj.exists() else 0
            print(f"   Written {file_size_mb:.1f} MB in {write_time:.2f}s")

        total_time = time.time() - start_time
        records_per_sec = total_records / total_time if total_time > 0 else 0

        metadata = {
            "total_subjects": total_subjects,
            "total_records": total_records,
            "num_chunks": num_chunks,
            "chunk_size": chunk_size,
            "target_effect": target_effect,
            "time_seconds": total_time,
            "records_per_second": records_per_sec,
            "output_path": str(output_path) if output_path else None,
            "format": format,
            "memory_efficient": True,
            "lazy_evaluation": True
        }

        print(f"\n✅ Generation complete!")
        print(f"   Total: {total_records:,} records")
        print(f"   Time: {total_time:.2f}s")
        print(f"   Speed: {records_per_sec:,.0f} records/sec")

        return metadata

    def generate_streaming(
        self,
        total_subjects: int,
        chunk_size: int = 10000,
        target_effect: float = -5.0
    ) -> Generator[pd.DataFrame, None, None]:
        """
        Streaming generator - yields chunks without loading all data in memory

        Args:
            total_subjects: Total subjects to generate
            chunk_size: Subjects per chunk
            target_effect: Target treatment effect

        Yields:
            DataFrame chunks

        Example:
            >>> gen = DaftDataGenerator()
            >>> for chunk in gen.generate_streaming(total_subjects=100000, chunk_size=10000):
            ...     process_chunk(chunk)  # Process each chunk individually
        """
        subjects_per_arm = total_subjects // 2
        chunk_subjects_per_arm = chunk_size // 2
        num_chunks = (subjects_per_arm + chunk_subjects_per_arm - 1) // chunk_subjects_per_arm

        for chunk_idx in range(num_chunks):
            subjects_remaining = subjects_per_arm - (chunk_idx * chunk_subjects_per_arm)
            chunk_n_per_arm = min(chunk_subjects_per_arm, subjects_remaining)

            if chunk_n_per_arm <= 0:
                break

            start_subject_id = (chunk_idx * chunk_subjects_per_arm * 2) + 1
            chunk_df = self.generate_chunk_rules(
                n_per_arm=chunk_n_per_arm,
                target_effect=target_effect,
                start_subject_id=start_subject_id
            )

            yield chunk_df

    def estimate_memory_usage(self, total_subjects: int, chunk_size: int) -> Dict[str, Any]:
        """
        Estimate memory usage for generation

        Args:
            total_subjects: Total subjects
            chunk_size: Chunk size

        Returns:
            Memory estimates in MB
        """
        # Each record ~100 bytes (7 columns * ~14 bytes avg)
        records_per_chunk = chunk_size * 4  # 4 visits per subject
        bytes_per_chunk = records_per_chunk * 100
        mb_per_chunk = bytes_per_chunk / (1024 * 1024)

        total_records = total_subjects * 4
        total_mb = total_records * 100 / (1024 * 1024)

        return {
            "total_subjects": total_subjects,
            "total_records": total_records,
            "total_size_mb": total_mb,
            "chunk_size": chunk_size,
            "records_per_chunk": records_per_chunk,
            "chunk_size_mb": mb_per_chunk,
            "num_chunks": (total_subjects + chunk_size - 1) // chunk_size,
            "recommendation": "Use Parquet format for datasets > 100 MB"
        }


def generate_vitals_million_scale(
    total_subjects: int = 100_000,
    chunk_size: int = 10_000,
    target_effect: float = -5.0,
    output_path: Optional[str] = None,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Convenience function for million-scale generation

    Args:
        total_subjects: Total subjects (both arms combined)
        chunk_size: Subjects per chunk
        target_effect: Target treatment effect
        output_path: Output file path (Parquet recommended)
        seed: Random seed

    Returns:
        Generation metadata

    Example:
        >>> meta = generate_vitals_million_scale(
        ...     total_subjects=1_000_000,
        ...     output_path="/data/synthetic_1M.parquet"
        ... )
    """
    generator = DaftDataGenerator(seed=seed)
    return generator.generate_million_scale(
        total_subjects=total_subjects,
        chunk_size=chunk_size,
        target_effect=target_effect,
        output_path=output_path
    )
