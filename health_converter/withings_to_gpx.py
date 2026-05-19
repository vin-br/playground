"""
withings2gpx.py — Convert Withings CSV export to Strava-compatible GPX files.

Usage:
    uv run withings2gpx.py <path_to_withings_export_folder> [--output <output_dir>]

The input folder should be the unzipped Withings data archive.
Output: output/<YYYY>/<YYYYMMDD_HHMMSS_sport>.gpx
"""

import argparse
import ast
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import gpxpy
import gpxpy.gpx
import pandas as pd

# ── Withings sport codes → Strava-compatible slug ───────────────────────────
# Source: Withings API (workoutsummary sport field)
SPORT_MAP: dict[int, str] = {
    1: "walk",
    2: "run",
    3: "hike",
    4: "skate",
    5: "bmx",
    6: "ride",           # cycling → Strava "ride"
    7: "swim",
    8: "surf",
    9: "kitesurf",
    10: "windsurf",
    11: "bodyboard",
    12: "tennis",
    13: "table_tennis",
    14: "squash",
    15: "badminton",
    16: "weight_training",
    17: "workout",       # calisthenics
    18: "elliptical",
    19: "yoga",
    20: "basketball",
    21: "soccer",
    22: "football",
    23: "rugby",
    24: "volleyball",
    25: "water_polo",
    26: "horse_riding",
    27: "golf",
    28: "yoga",
    29: "dance",
    30: "boxing",
    31: "fencing",
    32: "wrestling",
    33: "martial_arts",
    34: "ski",
    35: "snowboard",
    36: "other",
    306: "indoor_cycling", # Withings extended codes
    307: "indoor_run",
    308: "indoor_walk",
    309: "rowing",
    310: "indoor_rowing",
    311: "crossfit",
    312: "hiit",
    313: "pilates",
    314: "stretching",
    315: "ice_skate",
    316: "alpine_ski",
    317: "nordic_ski",
    318: "snowshoe",
}

# Activities that make sense as workouts (exclude daily step aggregates)
# The activities.csv has date-level aggregates. Workouts come from raw_tracker files.
WORKOUT_SPORTS: set[int] = set(SPORT_MAP.keys())


def load_csv(path: Path, **kwargs) -> pd.DataFrame | None:
    """Load a CSV, return None if missing or empty."""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, **kwargs)
        return df if not df.empty else None
    except Exception:
        return None


def parse_raw_series(value_str: str) -> list[float]:
    """Parse Withings bracketed list format: '[1,2,3]' → [1.0, 2.0, 3.0]."""
    try:
        return [float(x) for x in ast.literal_eval(value_str)]
    except Exception:
        return []


def expand_duration_value(df: pd.DataFrame, start_ts: float) -> pd.DataFrame:
    """
    Expand rows that have Duration=[...] and Value=[...] into individual
    timestamped readings.
    """
    rows = []
    t = start_ts
    for _, row in df.iterrows():
        durations = parse_raw_series(str(row.get("Duration", "[]")))
        values = parse_raw_series(str(row.get("Value", "[]")))
        for dur, val in zip(durations, values):
            rows.append({"timestamp": t, "value": val})
            t += dur
    return pd.DataFrame(rows)


def parse_iso_start(val: str) -> float:
    """Parse ISO datetime string to unix timestamp."""
    return pd.to_datetime(val, utc=True).timestamp()

def load_and_prep_raw(path: Path) -> pd.DataFrame | None:
    """Load a Withings raw CSV and add a numeric start_ts column."""
    df = load_csv(path)
    if df is None or "start" not in df.columns:
        return df
    
    # Vectorized timezone-aware parse is much faster
    # Errors are coerced to NaT, then dropped to avoid errors on timestamp()
    dt = pd.to_datetime(df["start"], format="mixed", utc=True, errors="coerce")
    df = df[dt.notna()].copy()
    dt = dt.dropna()
    df["start_ts"] = dt.map(pd.Timestamp.timestamp)
    return df

def load_gps(start: float, end: float, lat_df: pd.DataFrame, lon_df: pd.DataFrame, alt_df: pd.DataFrame) -> pd.DataFrame:
    """Load lat/lon/alt points within [start, end] unix timestamps."""
    if lat_df is None or lon_df is None or lat_df.empty or lon_df.empty:
        return pd.DataFrame()

    def parse_gps_file(df: pd.DataFrame) -> pd.DataFrame:
        # Filter down to relevant time window before parsing arrays
        # Add 1 hour buffer in case durations span past the start_ts
        subset = df[(df["start_ts"] >= start - 3600) & (df["start_ts"] <= end + 3600)]
        rows = []
        for _, row in subset.iterrows():
            t = row["start_ts"]
            durations = parse_raw_series(str(row.get("duration", "[]")))
            values = parse_raw_series(str(row.get("value", "[]")))
            for dur, val in zip(durations, values):
                rows.append({"timestamp": t, "value": val})
                t += dur
        return pd.DataFrame(rows)

    lats = parse_gps_file(lat_df)
    lons = parse_gps_file(lon_df)

    if lats.empty or lons.empty:
        return pd.DataFrame()

    # Merge on closest timestamp
    lats = lats.rename(columns={"value": "lat"})
    lons = lons.rename(columns={"value": "lon"})
    gps = pd.merge_asof(
        lats.sort_values("timestamp"),
        lons.sort_values("timestamp"),
        on="timestamp",
        tolerance=5,
    )

    if alt_df is not None:
        alts = parse_gps_file(alt_df).rename(columns={"value": "ele"})
        gps = pd.merge_asof(gps, alts.sort_values("timestamp"), on="timestamp", tolerance=5)

    return gps[(gps["timestamp"] >= start) & (gps["timestamp"] <= end)].reset_index(drop=True)


def load_hr(start: float, end: float, hr_df: pd.DataFrame) -> pd.DataFrame:
    """Load heart rate data within [start, end]."""
    if hr_df is None or hr_df.empty:
        return pd.DataFrame()

    subset = hr_df[(hr_df["start_ts"] >= start - 3600) & (hr_df["start_ts"] <= end + 3600)]
    rows = []
    for _, row in subset.iterrows():
        t = row["start_ts"]
        durations = parse_raw_series(str(row.get("duration", "[]")))
        values = parse_raw_series(str(row.get("value", "[]")))
        for dur, val in zip(durations, values):
            rows.append({"timestamp": t, "hr": val})
            t += dur

    if not rows:
        return pd.DataFrame()
        
    hr_parsed = pd.DataFrame(rows)
    return hr_parsed[(hr_parsed["timestamp"] >= start) & (hr_parsed["timestamp"] <= end)].reset_index(drop=True)


def build_gpx(workout: pd.Series, gps: pd.DataFrame, hr: pd.DataFrame) -> gpxpy.gpx.GPX:
    """Assemble a GPX object from workout metadata + GPS + HR."""
    gpx = gpxpy.gpx.GPX()
    gpx.name = workout.get("sport_label", "Workout")
    gpx.description = f"Withings export — {workout.get('sport_label', '')}"

    track = gpxpy.gpx.GPXTrack()
    track.name = gpx.name
    track.type = workout.get("gpx_type", "generic")
    gpx.tracks.append(track)

    segment = gpxpy.gpx.GPXTrackSegment()
    track.segments.append(segment)

    # Build HR lookup (nearest within 30s)
    hr_ts = hr["timestamp"].values if not hr.empty else []
    hr_vals = hr["hr"].values if not hr.empty else []

    for _, pt in gps.iterrows():
        dt = datetime.fromtimestamp(pt["timestamp"], tz=timezone.utc)
        trkpt = gpxpy.gpx.GPXTrackPoint(
            latitude=pt["lat"],
            longitude=pt["lon"],
            elevation=pt.get("ele"),
            time=dt,
        )
        # Store HR value on the point object; injected during XML post-processing
        if len(hr_ts) > 0:
            idx = (abs(hr_ts - pt["timestamp"])).argmin()
            if abs(hr_ts[idx] - pt["timestamp"]) < 30:
                trkpt.comment = f"__HR__{int(hr_vals[idx])}__"
        segment.points.append(trkpt)

    # If no GPS: create a single timestamped point at (0,0) so Strava still
    # imports the activity as manual with duration/calories metadata.
    if not segment.points:
        start_dt = datetime.fromtimestamp(float(workout["start"]), tz=timezone.utc)
        # Minimal valid track point — Strava accepts this for non-GPS sports
        segment.points.append(gpxpy.gpx.GPXTrackPoint(0.0, 0.0, time=start_dt))
        if float(workout["end"]) > float(workout["start"]):
            end_dt = datetime.fromtimestamp(float(workout["end"]), tz=timezone.utc)
            segment.points.append(gpxpy.gpx.GPXTrackPoint(0.0, 0.0, time=end_dt))

    return gpx


def load_workouts(data_dir: Path) -> pd.DataFrame:
    """
    Extract workouts from activities.csv.
    """
    act_path = data_dir / "activities.csv"
    if not act_path.exists():
        print(f"[ERROR] activities.csv not found in {data_dir}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(act_path)
    print(f"[INFO] activities.csv columns: {list(df.columns)}")

    # Detect workout rows
    sport_col = "Activity type" if "Activity type" in df.columns else next((c for c in df.columns if c.lower() in ("sport", "category", "workout")), None)
    start_col = "from" if "from" in df.columns else next((c for c in df.columns if "start" in c.lower()), None)
    end_col = "to" if "to" in df.columns else next((c for c in df.columns if "end" in c.lower()), None)

    if sport_col is None or start_col is None:
        # Fallback: dump column names and exit with instructions
        print(f"[WARN] Cannot auto-detect workout rows. Columns found: {list(df.columns)}", file=sys.stderr)
        print("[HINT] Open activities.csv and check column names, then update sport_col/start_col in the script.", file=sys.stderr)
        return pd.DataFrame()

    # Filter to actual workouts
    workouts = df[df[sport_col].notna()].copy()
    
    # Check if sport column contains numeric codes or string labels
    is_numeric = pd.to_numeric(workouts[sport_col], errors="coerce").notna().any()
    if is_numeric:
        workouts["sport_code"] = pd.to_numeric(workouts[sport_col], errors="coerce").fillna(36)
        workouts["sport_label"] = workouts["sport_code"].map(SPORT_MAP).fillna("unknown")
    else:
        workouts["sport_label"] = workouts[sport_col].astype(str).str.lower().str.replace(" ", "_")

    workouts["start"] = pd.to_datetime(workouts[start_col], errors="coerce", utc=True).apply(lambda x: x.timestamp() if pd.notna(x) else None)
    
    if end_col:
        workouts["end"] = pd.to_datetime(workouts[end_col], errors="coerce", utc=True).apply(lambda x: x.timestamp() if pd.notna(x) else None)
    else:
        workouts["end"] = workouts["start"] + 3600
        
    workouts = workouts.dropna(subset=["start"])

    # GPX track type (Strava uses these for sport detection on manual import)
    gpx_type_map = {
        "ride": "cycling", "indoor_cycling": "cycling", "run": "running",
        "indoor_run": "running", "walk": "walking", "indoor_walk": "walking",
        "hike": "hiking", "swim": "swimming", "row": "rowing",
        "indoor_rowing": "rowing", "ski": "skiing", "nordic_ski": "skiing",
    }
    workouts["gpx_type"] = workouts["sport_label"].map(gpx_type_map).fillna("generic")

    print(f"[INFO] Found {len(workouts)} workouts")
    return workouts.reset_index(drop=True)


def workout_filename(workout: pd.Series) -> str:
    """YYYYMMDD_HHMMSS_<sport>.gpx"""
    dt = datetime.fromtimestamp(float(workout["start"]), tz=timezone.utc)
    return f"{dt.strftime('%Y%m%d_%H%M%S')}_{workout['sport_label']}.gpx"


def main():
    parser = argparse.ArgumentParser(description="Convert Withings CSV export to GPX files for Strava.")
    parser.add_argument("data_dir", type=Path, help="Path to unzipped Withings export folder")
    parser.add_argument("--output", "-o", type=Path, default=Path("data/gpx"), help="Output directory (default: ./data/gpx)")
    args = parser.parse_args()

    data_dir: Path = args.data_dir.resolve()
    out_root: Path = args.output.resolve()

    if not data_dir.is_dir():
        print(f"[ERROR] Not a directory: {data_dir}", file=sys.stderr)
        sys.exit(1)

    workouts = load_workouts(data_dir)
    if workouts.empty:
        print("[ERROR] No workouts found. Check activities.csv.", file=sys.stderr)
        sys.exit(1)

    print("[INFO] Pre-loading GPS & HR data into memory (this will take a few seconds)...")
    lat_df = load_and_prep_raw(data_dir / "raw_location_latitude.csv")
    lon_df = load_and_prep_raw(data_dir / "raw_location_longitude.csv")
    alt_df = load_and_prep_raw(data_dir / "raw_location_altitude.csv")
    hr_df = load_and_prep_raw(data_dir / "raw_hr_hr.csv")

    exported = 0
    skipped = 0

    print("[INFO] Processing workouts...")
    for _, workout in workouts.iterrows():
        start_ts = float(workout["start"])
        end_ts = float(workout["end"])

        gps = load_gps(start_ts, end_ts, lat_df, lon_df, alt_df)
        hr = load_hr(start_ts, end_ts, hr_df)

        gpx = build_gpx(workout, gps, hr)

        year = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime("%Y")
        out_dir = out_root / year
        out_dir.mkdir(parents=True, exist_ok=True)

        fname = workout_filename(workout)
        out_path = out_dir / fname

        try:
            xml = gpx.to_xml()
            # Inject HR extensions: replace gpxpy comment markers with proper GPX extension XML
            HR_NS = 'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"'
            def inject_hr(m):
                bpm = m.group(1)
                ext = (
                    f'<extensions>'
                    f'<gpxtpx:TrackPointExtension {HR_NS}>'
                    f'<gpxtpx:hr>{bpm}</gpxtpx:hr>'
                    f'</gpxtpx:TrackPointExtension>'
                    f'</extensions>'
                )
                return ext
            xml = re.sub(r'<cmt>__HR__(\d+)__</cmt>', inject_hr, xml)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(xml)
            gps_info = f"{len(gps)} GPS pts" if not gps.empty else "no GPS"
            hr_info = f"{len(hr)} HR pts" if not hr.empty else "no HR"
            print(f"[OK] {year}/{fname}  ({gps_info}, {hr_info})")
            exported += 1
        except Exception as e:
            print(f"[FAIL] {fname}: {e}", file=sys.stderr)
            skipped += 1

    print(f"\nDone — {exported} exported, {skipped} failed → {out_root}")


if __name__ == "__main__":
    main()
