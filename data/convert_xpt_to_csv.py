#!/usr/bin/env python3
"""
Convert CDISC pilot XPT files to CSV format for easier processing.
"""
import pandas as pd
import pyreadstat
import os

def convert_xpt_to_csv(xpt_file, csv_file):
    """Convert XPT file to CSV."""
    print(f"Converting {xpt_file} to {csv_file}...")
    df, meta = pyreadstat.read_xport(xpt_file)
    df.to_csv(csv_file, index=False)
    print(f"  Saved {len(df)} rows to {csv_file}")
    print(f"  Columns: {list(df.columns)[:10]}{'...' if len(df.columns) > 10 else ''}")
    return df

if __name__ == "__main__":
    data_dir = os.path.dirname(os.path.abspath(__file__))

    # Convert vital signs
    vs_df = convert_xpt_to_csv(
        os.path.join(data_dir, "vs.xpt"),
        os.path.join(data_dir, "vital_signs.csv")
    )

    # Convert demographics
    dm_df = convert_xpt_to_csv(
        os.path.join(data_dir, "dm.xpt"),
        os.path.join(data_dir, "demographics.csv")
    )

    # Convert adverse events
    ae_df = convert_xpt_to_csv(
        os.path.join(data_dir, "ae.xpt"),
        os.path.join(data_dir, "adverse_events.csv")
    )

    print("\nConversion complete!")
    print(f"Vital Signs: {len(vs_df)} records")
    print(f"Demographics: {len(dm_df)} records")
    print(f"Adverse Events: {len(ae_df)} records")
