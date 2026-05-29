"""
Withings CSV export importer.

Reads a Withings Health Mate data export (unzipped folder) and produces
canonical Workout objects with GPS trackpoints and heart rate data.
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pandas as pd

from ..models import TrackPoint, Workout
from ..sport_mapping import (
    INDOOR_SPORTS,
    SPORT_MAP,
    resolve_strava_type,
)
from .base import BaseImporter

# Meters per degree of latitude (approximate)
_METERS_PER_DEG_LAT = 111_320


class WithingsImporter(BaseImporter):
    """Import workouts from a Withings Health Mate CSV export."""

    source_name = "Withings"

    def load(self, source_path: Path) -> list[Workout]:
        """Load all workouts from the Withings export directory."""
        data_dir = source_path.resolve()
        if not data_dir.is_dir():
            raise FileNotFoundError(f"Not a directory: {data_dir}")

        raw_workouts = self._load_activity_table(data_dir)
        if raw_workouts.empty:
            return []

        print("[INFO] Pre-loading GPS & HR data into memory...")
        lat_df = self._load_raw_csv(data_dir / "raw_location_latitude.csv")
        lon_df = self._load_raw_csv(data_dir / "raw_location_longitude.csv")
        alt_df = self._load_raw_csv(data_dir / "raw_location_altitude.csv")
        hr_df = self._load_raw_csv(data_dir / "raw_hr_hr.csv")

        workouts: list[Workout] = []
        for _, row in raw_workouts.iterrows():
            start_ts = float(row["start"])
            end_ts = float(row["end"])

            gps_points = self._load_gps(start_ts, end_ts, lat_df, lon_df, alt_df)
            hr_data = self._load_hr(start_ts, end_ts, hr_df)

            sport_label = row["sport_label"]
            strava_type = resolve_strava_type(sport_label)
            distance_m = float(row.get("activity_distance", 0) or 0)

            trackpoints = self._build_trackpoints(
                gps_points, hr_data, sport_label, distance_m,
                start_ts, end_ts,
                ref_lat=float(row.get("ref_lat", 0.0) or 0.0),
                ref_lon=float(row.get("ref_lon", 0.0) or 0.0),
            )

            workout = Workout(
                sport_label=sport_label,
                strava_type=strava_type,
                start=start_ts,
                end=end_ts,
                distance_m=distance_m,
                calories=float(row.get("activity_calories", 0) or 0),
                ref_lat=float(row.get("ref_lat", 0.0) or 0.0),
                ref_lon=float(row.get("ref_lon", 0.0) or 0.0),
                trackpoints=trackpoints,
                source=self.source_name,
            )
            workouts.append(workout)

        return workouts

    def inspect(self, source_path: Path) -> str:
        """Return diagnostic info about the Withings export."""
        data_dir = source_path.resolve()
        lines: list[str] = []

        lines.append(f"{'=' * 60}")
        lines.append(f"Inspecting: {data_dir}")
        lines.append(f"{'=' * 60}\n")

        csv_files = sorted(data_dir.glob("*.csv"))
        lines.append(f"Found {len(csv_files)} CSV files:")
        for f in csv_files:
            lines.append(f"  {f.name}")

        # activities.csv
        act = data_dir / "activities.csv"
        if act.exists():
            df = pd.read_csv(act)
            lines.append(f"\n{'-' * 40}")
            lines.append("activities.csv")
            lines.append(f"  Rows: {len(df)}")
            lines.append(f"  Columns: {list(df.columns)}")
            lines.append(f"\n  First 3 rows:")
            lines.append(df.head(3).to_string(index=False))

            sport_col = next(
                (c for c in df.columns if c.lower() in ("sport", "category", "workout", "activity type")),
                None,
            )
            if sport_col:
                non_null = df[sport_col].dropna()
                numeric = pd.to_numeric(non_null, errors="coerce").dropna()
                lines.append(f"\n  Sport column: '{sport_col}'")
                if not numeric.empty:
                    lines.append(f"  Unique sport codes: {sorted(numeric.unique().astype(int).tolist())}")
                else:
                    lines.append(f"  Unique labels: {sorted(non_null.unique().tolist())}")
        else:
            lines.append("\n[ERROR] activities.csv not found!")

        # GPS check
        for fname in ("raw_location_latitude.csv", "raw_location_longitude.csv", "raw_location_altitude.csv"):
            p = data_dir / fname
            if p.exists():
                df = pd.read_csv(p)
                lines.append(f"\n{fname}")
                lines.append(f"  Rows: {len(df)}  |  Columns: {list(df.columns)}")
                if not df.empty:
                    lines.append(f"  Sample: {df.iloc[0].to_dict()}")
            else:
                lines.append(f"\n{fname}: NOT FOUND")

        # HR check
        hr_path = data_dir / "raw_hr_hr.csv"
        if hr_path.exists():
            df = pd.read_csv(hr_path)
            lines.append(f"\nraw_hr_hr.csv")
            lines.append(f"  Rows: {len(df)}  |  Columns: {list(df.columns)}")
            if not df.empty:
                lines.append(f"  Sample: {df.iloc[0].to_dict()}")
        else:
            lines.append("\nraw_hr_hr.csv: NOT FOUND")

        lines.append(f"\n{'=' * 60}")
        lines.append("Inspection complete.")
        return "\n".join(lines)

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _load_raw_csv(path: Path) -> pd.DataFrame | None:
        """Load a Withings raw CSV and add a numeric start_ts column."""
        if not path.exists():
            return None
        try:
            df = pd.read_csv(path)
        except Exception:
            return None
        if df is None or df.empty or "start" not in df.columns:
            return None
        dt = pd.to_datetime(df["start"], format="mixed", utc=True, errors="coerce")
        df = df[dt.notna()].copy()
        dt = dt.dropna()
        df["start_ts"] = dt.map(pd.Timestamp.timestamp)
        return df

    @staticmethod
    def _parse_json(value: str | float) -> dict:
        if pd.isna(value) or not isinstance(value, str):
            return {}
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            return {}

    @staticmethod
    def _parse_raw_series(value_str: str) -> list[float]:
        try:
            return [float(x) for x in ast.literal_eval(value_str)]
        except Exception:
            return []

    def _load_activity_table(self, data_dir: Path) -> pd.DataFrame:
        """Parse activities.csv into a normalized DataFrame."""
        act_path = data_dir / "activities.csv"
        if not act_path.exists():
            print(f"[ERROR] activities.csv not found in {data_dir}", file=sys.stderr)
            return pd.DataFrame()

        df = pd.read_csv(act_path)
        print(f"[INFO] activities.csv columns: {list(df.columns)}")

        sport_col = (
            "Activity type" if "Activity type" in df.columns
            else next((c for c in df.columns if c.lower() in ("sport", "category", "workout")), None)
        )
        start_col = "from" if "from" in df.columns else next((c for c in df.columns if "start" in c.lower()), None)
        end_col = "to" if "to" in df.columns else next((c for c in df.columns if "end" in c.lower()), None)

        if sport_col is None or start_col is None:
            print(f"[WARN] Cannot detect workout columns. Found: {list(df.columns)}", file=sys.stderr)
            return pd.DataFrame()

        workouts = df[df[sport_col].notna()].copy()

        # Numeric codes or string labels?
        is_numeric = pd.to_numeric(workouts[sport_col], errors="coerce").notna().any()
        if is_numeric:
            workouts["sport_code"] = pd.to_numeric(workouts[sport_col], errors="coerce").fillna(36)
            workouts["sport_label"] = workouts["sport_code"].map(SPORT_MAP).fillna("unknown")
        else:
            workouts["sport_label"] = workouts[sport_col].astype(str).str.lower().str.replace(" ", "_")

        # Parse Data JSON
        data_col = "Data" if "Data" in workouts.columns else None
        gps_col = "GPS" if "GPS" in workouts.columns else None

        if data_col:
            parsed_data = workouts[data_col].apply(self._parse_json)
            workouts["activity_distance"] = parsed_data.apply(self._get_distance)
            workouts["activity_calories"] = parsed_data.apply(lambda d: float(d.get("calories", 0) or 0))
        else:
            workouts["activity_distance"] = 0.0
            workouts["activity_calories"] = 0.0

        # Parse GPS JSON for ref coords and indoor detection
        if gps_col:
            parsed_gps = workouts[gps_col].apply(self._parse_json)
            workouts["ref_lat"] = parsed_gps.apply(lambda g: float(g.get("start_coordinate_latitude", 0) or 0))
            workouts["ref_lon"] = parsed_gps.apply(lambda g: float(g.get("start_coordinate_longitude", 0) or 0))

            reclassified = 0
            for idx in workouts.index:
                if self._detect_indoor_cycling(workouts.at[idx, "sport_label"], parsed_gps.at[idx]):
                    workouts.at[idx, "sport_label"] = "indoor_cycling"
                    reclassified += 1
            if reclassified:
                print(f"[INFO] Reclassified {reclassified} 'Cycling' as indoor_cycling (no GPS movement)")
        else:
            workouts["ref_lat"] = 0.0
            workouts["ref_lon"] = 0.0

        workouts["start"] = pd.to_datetime(
            workouts[start_col], errors="coerce", utc=True
        ).apply(lambda x: x.timestamp() if pd.notna(x) else None)

        if end_col:
            workouts["end"] = pd.to_datetime(
                workouts[end_col], errors="coerce", utc=True
            ).apply(lambda x: x.timestamp() if pd.notna(x) else None)
        else:
            workouts["end"] = workouts["start"] + 3600

        workouts = workouts.dropna(subset=["start"])

        print(f"[INFO] Found {len(workouts)} workouts")
        type_counts = workouts.groupby("sport_label").size()
        for label, count in type_counts.items():
            strava = resolve_strava_type(label)
            print(f"  {label} -> {strava.value}: {count}")

        return workouts.reset_index(drop=True)

    @staticmethod
    def _get_distance(data: dict) -> float:
        manual = data.get("manual_distance", 0) or 0
        auto = data.get("distance", 0) or 0
        return float(manual) if manual > 0 else float(auto)

    @staticmethod
    def _detect_indoor_cycling(sport_label: str, gps_meta: dict) -> bool:
        if sport_label != "cycling":
            return False
        if not gps_meta:
            return True
        span_lat = gps_meta.get("span_latitude_delta", -1)
        span_lon = gps_meta.get("span_longitude_delta", -1)
        avg_speed = gps_meta.get("avg_speed", -1)
        gps_distance = gps_meta.get("distance", -1)
        if span_lat == 0 and span_lon == 0:
            return True
        if avg_speed <= 0 and gps_distance <= 0:
            return True
        return False

    def _load_gps(
        self, start: float, end: float,
        lat_df: pd.DataFrame | None, lon_df: pd.DataFrame | None,
        alt_df: pd.DataFrame | None,
    ) -> pd.DataFrame:
        if lat_df is None or lon_df is None or lat_df.empty or lon_df.empty:
            return pd.DataFrame()

        def parse_gps_file(df: pd.DataFrame) -> pd.DataFrame:
            subset = df[(df["start_ts"] >= start - 3600) & (df["start_ts"] <= end + 3600)]
            rows = []
            for _, row in subset.iterrows():
                t = row["start_ts"]
                durations = self._parse_raw_series(str(row.get("duration", "[]")))
                values = self._parse_raw_series(str(row.get("value", "[]")))
                for dur, val in zip(durations, values):
                    rows.append({"timestamp": t, "value": val})
                    t += dur
            return pd.DataFrame(rows)

        lats = parse_gps_file(lat_df)
        lons = parse_gps_file(lon_df)
        if lats.empty or lons.empty:
            return pd.DataFrame()

        lats = lats.rename(columns={"value": "lat"})
        lons = lons.rename(columns={"value": "lon"})
        gps = pd.merge_asof(
            lats.sort_values("timestamp"),
            lons.sort_values("timestamp"),
            on="timestamp", tolerance=5,
        )

        if alt_df is not None and not alt_df.empty:
            alts = parse_gps_file(alt_df).rename(columns={"value": "ele"})
            if not alts.empty:
                gps = pd.merge_asof(gps, alts.sort_values("timestamp"), on="timestamp", tolerance=5)

        return gps[(gps["timestamp"] >= start) & (gps["timestamp"] <= end)].reset_index(drop=True)

    def _load_hr(self, start: float, end: float, hr_df: pd.DataFrame | None) -> pd.DataFrame:
        if hr_df is None or hr_df.empty:
            return pd.DataFrame()
        subset = hr_df[(hr_df["start_ts"] >= start - 3600) & (hr_df["start_ts"] <= end + 3600)]
        rows = []
        for _, row in subset.iterrows():
            t = row["start_ts"]
            durations = self._parse_raw_series(str(row.get("duration", "[]")))
            values = self._parse_raw_series(str(row.get("value", "[]")))
            for dur, val in zip(durations, values):
                rows.append({"timestamp": t, "hr": val})
                t += dur
        if not rows:
            return pd.DataFrame()
        hr_parsed = pd.DataFrame(rows)
        return hr_parsed[(hr_parsed["timestamp"] >= start) & (hr_parsed["timestamp"] <= end)].reset_index(drop=True)

    def _build_trackpoints(
        self, gps: pd.DataFrame, hr: pd.DataFrame,
        sport_label: str, distance_m: float,
        start_ts: float, end_ts: float,
        ref_lat: float = 0.0, ref_lon: float = 0.0,
    ) -> list[TrackPoint]:
        """Build a list of TrackPoints, synthesizing GPS for indoor activities."""
        has_real_gps = not gps.empty
        is_indoor = sport_label in INDOOR_SPORTS

        # Detect stationary GPS (indoor with points at same location)
        use_synthetic = False
        if has_real_gps and is_indoor and distance_m > 0:
            lat_range = gps["lat"].max() - gps["lat"].min()
            lon_range = gps["lon"].max() - gps["lon"].min()
            if lat_range * _METERS_PER_DEG_LAT < 10 and lon_range * _METERS_PER_DEG_LAT < 10:
                use_synthetic = True

        if (not has_real_gps or use_synthetic) and distance_m > 0:
            gps = self._generate_synthetic_gps(start_ts, end_ts, distance_m, ref_lat, ref_lon)

        hr_ts = hr["timestamp"].values if not hr.empty else []
        hr_vals = hr["hr"].values if not hr.empty else []

        points: list[TrackPoint] = []
        for _, pt in gps.iterrows():
            hr_val = None
            if len(hr_ts) > 0:
                idx = (abs(hr_ts - pt["timestamp"])).argmin()
                if abs(hr_ts[idx] - pt["timestamp"]) < 30:
                    hr_val = int(hr_vals[idx])
            points.append(TrackPoint(
                timestamp=pt["timestamp"],
                lat=pt["lat"],
                lon=pt["lon"],
                ele=pt.get("ele"),
                hr=hr_val,
            ))

        # Fallback: minimal start/end points for duration tracking
        if not points:
            start_hr = None
            if len(hr_ts) > 0:
                idx = (abs(hr_ts - start_ts)).argmin()
                if abs(hr_ts[idx] - start_ts) < 60:
                    start_hr = int(hr_vals[idx])
            points.append(TrackPoint(timestamp=start_ts, lat=ref_lat, lon=ref_lon, hr=start_hr))

            if end_ts > start_ts:
                end_hr = None
                if len(hr_ts) > 0:
                    idx = (abs(hr_ts - end_ts)).argmin()
                    if abs(hr_ts[idx] - end_ts) < 60:
                        end_hr = int(hr_vals[idx])
                points.append(TrackPoint(timestamp=end_ts, lat=ref_lat, lon=ref_lon, hr=end_hr))

        return points

    @staticmethod
    def _generate_synthetic_gps(
        start_ts: float, end_ts: float, distance_m: float,
        ref_lat: float = 0.0, ref_lon: float = 0.0,
        interval_s: float = 10.0,
    ) -> pd.DataFrame:
        if distance_m <= 0 or end_ts <= start_ts:
            return pd.DataFrame()
        duration = end_ts - start_ts
        num_points = max(int(duration / interval_s), 2)
        dt = duration / (num_points - 1)
        dist_per_seg = distance_m / (num_points - 1)
        lat_step = dist_per_seg / _METERS_PER_DEG_LAT

        rows = []
        for i in range(num_points):
            rows.append({
                "timestamp": start_ts + i * dt,
                "lat": ref_lat + i * lat_step,
                "lon": ref_lon,
            })
        return pd.DataFrame(rows)
