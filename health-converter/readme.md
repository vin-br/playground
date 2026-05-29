# Health Converter

Modular health data import/export framework. Currently converts Withings CSV exports to Strava-compatible GPX files. Designed to be extended with additional importers (Garmin, Fitbit, Apple Health) and exporters (TCX, FIT, API).

## Architecture

```
health-converter/
  models.py              # Pydantic models: Workout, TrackPoint, StravaActivityType
  sport_mapping.py       # Withings codes -> normalized labels -> Strava types
  importers/
    base.py              # BaseImporter ABC
    withings.py          # WithingsImporter — reads Withings CSV export
  exporters/
    base.py              # BaseExporter ABC
    gpx.py               # GPXExporter — produces Strava-compatible GPX
cli.py                   # CLI entry point (also installable as `health-converter` command)
```

**Data flow:** `Source format -> Importer -> [Workout] -> Exporter -> Target format`

Adding a new source (e.g. Garmin): subclass `BaseImporter`, implement `load()` returning `list[Workout]`.
Adding a new target (e.g. TCX): subclass `BaseExporter`, implement `export_one()` consuming a `Workout`.

## Requirements

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (`pip install uv` or `brew install uv`)

## Setup

```bash
cd csv2gpx
uv sync
```

## Usage

### 1. Export your Withings data

Go to https://account.withings.com/export/user_select, request your archive, and unzip it.

### 2. Inspect the export (optional diagnostic)

```bash
uv run cli.py data/csv/ --inspect
```

Prints column names, sample rows, and detected sport labels to help debug format changes.

### 3. Convert to GPX

```bash
uv run cli.py data/csv/
# custom output dir:
uv run cli.py data/csv/ --output ~/Sports/gpx
# see per-file details:
uv run cli.py data/csv/ --verbose
```

If installed (`uv pip install .`), you can also use the `health-converter` command directly:

```bash
health-converter data/csv/ --output ~/Sports/gpx
```

### 4. Upload to Strava

Go to https://www.strava.com/upload/select and drag-and-drop the GPX files.

## Output structure

```
output/
  2022/
    20220314_073015_ride.gpx
    20220318_183200_run.gpx
  2023/
    20230101_090000_indoor_cycling.gpx
```

## Sport type mapping (Withings -> Strava)

| Withings label  | Strava `<type>`  | Notes                       |
|-----------------|------------------|-----------------------------|
| Walking         | `Walk`           |                             |
| Running         | `Run`            |                             |
| Hiking          | `Hike`           |                             |
| Cycling         | `Ride`           | Auto-reclassified if indoor |
| Indoor Cycling  | `VirtualRide`    | Synthetic GPS for distance  |
| Swimming        | `Swim`           |                             |
| Rowing          | `Rowing`         | Synthetic GPS for distance  |
| Tennis          | `Workout`        |                             |
| Weights         | `WeightTraining` |                             |
| Yoga            | `Yoga`           |                             |
| Other           | `Workout`        |                             |

Full mapping in `health-converter/sport_mapping.py`.

## How it works

1. `WithingsImporter` parses `activities.csv` for workout rows (string labels or numeric codes).
2. The `Data` JSON column provides distance; `GPS` JSON provides reference coordinates.
3. Activities labeled "Cycling" with no GPS movement are reclassified as indoor cycling.
4. GPS from `raw_location_*.csv` and HR from `raw_hr_hr.csv` are matched to each workout's time window.
5. Indoor activities with distance get synthetic trackpoints so Strava computes correct distance.
6. `GPXExporter` produces GPX with `<trk type="VirtualRide">` etc., and Garmin HR extensions.

## Extending for a web app

The Pydantic `Workout` model is FastAPI-ready:

```python
from fastapi import FastAPI, UploadFile
from health-converter.importers.withings import WithingsImporter
from health-converter.exporters.gpx import GPXExporter

app = FastAPI()

@app.post("/convert/withings")
async def convert_withings(file: UploadFile):
    # Extract zip, run importer, return GPX files
    ...
```

## Notes

- **No-GPS workouts** still export with start/end timestamps for duration tracking.
- **Indoor activities with distance** get synthetic GPS so Strava shows correct distance.
- **Apple Health imports** that mislabel indoor cycling are auto-detected and reclassified.
- HR data is injected as Garmin TrackPointExtension XML.
