"""
inspect_export.py — Diagnose your Withings export before running withings_to_gpx.py

Usage:
    uv run inspect_export.py <path_to_withings_export_folder>

Prints column names, sample rows, and unique sport codes found in activities.csv
so you can verify the mapping before converting.
"""

import sys
from pathlib import Path

import pandas as pd


def inspect(data_dir: Path):
    print(f"\n{'='*60}")
    print(f"Inspecting: {data_dir}")
    print(f"{'='*60}\n")

    csv_files = sorted(data_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} CSV files:\n  " + "\n  ".join(f.name for f in csv_files))

    # ── activities.csv ──────────────────────────────────────────
    act = data_dir / "activities.csv"
    if act.exists():
        df = pd.read_csv(act)
        print(f"\n{'─'*40}")
        print("activities.csv")
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {list(df.columns)}")
        print(f"\n  First 3 rows:")
        print(df.head(3).to_string(index=False))

        # Try to find sport/category column
        sport_col = next((c for c in df.columns if c.lower() in ("sport", "category", "workout")), None)
        if sport_col:
            non_null = df[sport_col].dropna()
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            print(f"\n  Sport column: '{sport_col}'")
            print(f"  Unique sport codes found: {sorted(numeric.unique().astype(int).tolist())}")
        else:
            print(f"\n  [WARN] No sport/category column found. All columns: {list(df.columns)}")
            print("  [HINT] Look for a column containing numeric workout type codes.")
    else:
        print("\n[ERROR] activities.csv not found!")

    # ── GPS check ───────────────────────────────────────────────
    for fname in ("raw_location_latitude.csv", "raw_location_longitude.csv", "raw_location_altitude.csv"):
        p = data_dir / fname
        if p.exists():
            df = pd.read_csv(p)
            print(f"\n{fname}")
            print(f"  Rows: {len(df)}  |  Columns: {list(df.columns)}")
            if not df.empty:
                print(f"  Sample row: {df.iloc[0].to_dict()}")
        else:
            print(f"\n{fname}: NOT FOUND (no GPS data)")

    # ── HR check ────────────────────────────────────────────────
    hr_path = data_dir / "raw_hr_hr.csv"
    if hr_path.exists():
        df = pd.read_csv(hr_path)
        print(f"\nraw_hr_hr.csv")
        print(f"  Rows: {len(df)}  |  Columns: {list(df.columns)}")
        if not df.empty:
            print(f"  Sample row: {df.iloc[0].to_dict()}")
    else:
        print("\nraw_hr_hr.csv: NOT FOUND")

    print(f"\n{'='*60}")
    print("Inspection complete.")
    print("If activities.csv columns look different from expected,")
    print("edit the sport_col/start_col/end_col detection in withings_to_gpx.py.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: uv run {sys.argv[0]} <withings_export_folder>")
        sys.exit(1)
    inspect(Path(sys.argv[1]).resolve())
