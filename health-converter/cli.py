"""
Health Converter CLI -- Convert health data exports to Strava-compatible GPX files.

Usage:
    uv run cli.py <path_to_withings_export_folder> [--output <output_dir>]
    uv run cli.py <path_to_withings_export_folder> --inspect

Or if installed:
    health-converter <path_to_withings_export_folder>

The input folder should be the unzipped Withings data archive.
Output: output/<YYYY>/<YYYYMMDD_HHMMSS_sport>.gpx
"""

import argparse
import sys
from pathlib import Path

from bridge.exporters.gpx import GPXExporter
from bridge.importers.withings import WithingsImporter


def main():
    parser = argparse.ArgumentParser(
        description="Convert Withings CSV export to Strava-compatible GPX files.",
        epilog="Example: health-converter ~/Downloads/withings-export",
    )
    parser.add_argument("data_dir", type=Path, help="Path to unzipped Withings export folder")
    parser.add_argument("--output", "-o", type=Path, default=Path("data/gpx"), help="Output directory (default: ./data/gpx)")
    parser.add_argument("--inspect", action="store_true", help="Print diagnostic info about the export and exit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show per-file export details")
    args = parser.parse_args()

    data_dir: Path = args.data_dir.resolve()
    if not data_dir.is_dir():
        print(f"[ERROR] Not a directory: {data_dir}", file=sys.stderr)
        sys.exit(1)

    importer = WithingsImporter()

    if args.inspect:
        print(importer.inspect(data_dir))
        return

    workouts = importer.load(data_dir)
    if not workouts:
        print("[ERROR] No workouts found. Try --inspect to diagnose.", file=sys.stderr)
        sys.exit(1)

    out_root = args.output
    print(f"\nExporting {len(workouts)} workouts to {out_root} ...")
    exporter = GPXExporter()
    exported, failed = exporter.export_all(workouts, out_root, verbose=args.verbose)

    print(f"\nDone -- {exported} exported, {failed} failed -> {out_root}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
