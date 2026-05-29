# Health Converter: CSV to GPX

Convert a Withings Health Mate CSV export into per-workout `.gpx` files compatible with Strava.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or `brew install uv`)

## Setup

```bash
cd health_converter
uv sync
```

## Workflow

### 1. Export your Withings data

Go to https://account.withings.com/export/user_select, request your archive, and unzip it into `data/csv/`.

### 2. Inspect the export (do this first)

```bash
uv run inspect_export.py data/csv
```

This prints column names from your `activities.csv` and sample GPS/HR rows.
Withings changes column names between export versions — always verify first.

### 3. Convert to GPX

```bash
uv run withings_to_gpx.py data/csv
# custom output dir:
uv run withings_to_gpx.py data/csv --output ~/Sports/withings_gpx
```

### 4. Upload to Strava

Go to https://www.strava.com/upload/select and drag-and-drop the GPX files.

---

## Directory structure

```
data/
  csv/                    # Your Withings export (gitignored)
    activities.csv
    raw_location_*.csv
    raw_hr_hr.csv
  gpx/                    # Generated GPX files (gitignored)
    2022/
      20220314_073015_ride.gpx
      20220318_183200_run.gpx
    2023/
      20230101_090000_hike.gpx
```

Filename: `YYYYMMDD_HHMMSS_<sport>.gpx` (UTC timestamps, sorts chronologically).

## Sport type mapping (Withings code → filename slug)

| Code | Withings sport  | Slug            |
|------|-----------------|-----------------|
| 1    | Walk            | `walk`          |
| 2    | Run             | `run`           |
| 3    | Hike            | `hike`          |
| 6    | Cycling         | `ride`          |
| 7    | Swimming        | `swim`          |
| 306  | Indoor cycling  | `indoor_cycling`|
| 307  | Indoor run      | `indoor_run`    |
| 309  | Rowing          | `rowing`        |
| 34   | Alpine ski      | `ski`           |

Full list in `SPORT_MAP` inside `withings_to_gpx.py`.

## How it works

1. `activities.csv` is parsed for rows with a numeric sport code (= workouts).
2. GPS points from `raw_location_latitude/longitude/altitude.csv` are extracted
   within each workout's `[start, end]` timestamp window.
3. Heart rate from `raw_hr_hr.csv` is joined to GPS points (nearest within 30s).
4. GPX is emitted with `<trk type="...">` set for Strava sport detection.

## Notes

- **No-GPS workouts** (indoor cycling, gym…) still export with start/end timestamps
  so Strava records duration and sport type correctly.
- HR data format: `Duration=[d1,d2,…]` + `Value=[v1,v2,…]` = HR v1 for d1 seconds, etc.
- If conversion fails, run `inspect_export.py` first — column names in `activities.csv`
  differ between Withings export versions.
