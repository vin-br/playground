"""
GPX exporter — converts Workout objects to Strava-compatible GPX files.
"""

from __future__ import annotations

import re

import gpxpy
import gpxpy.gpx

from ..models import Workout
from .base import BaseExporter

# Garmin TrackPointExtension namespace for heart rate
_HR_NS = 'xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1"'


class GPXExporter(BaseExporter):
    """Export Workout objects to GPX files compatible with Strava."""

    format_name = "gpx"
    file_extension = ".gpx"

    def export_one(self, workout: Workout) -> str:
        """Build a GPX XML string from a Workout."""
        gpx = gpxpy.gpx.GPX()
        gpx.name = workout.sport_label
        gpx.description = f"{workout.source} export - {workout.sport_label}"

        track = gpxpy.gpx.GPXTrack()
        track.name = gpx.name
        track.type = workout.strava_type.value
        gpx.tracks.append(track)

        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)

        for pt in workout.trackpoints:
            trkpt = gpxpy.gpx.GPXTrackPoint(
                latitude=pt.lat,
                longitude=pt.lon,
                elevation=pt.ele,
                time=pt.datetime_utc,
            )
            if pt.hr is not None:
                trkpt.comment = f"__HR__{pt.hr}__"
            segment.points.append(trkpt)

        xml = gpx.to_xml()
        # Post-process: replace HR comment markers with Garmin extension XML
        xml = re.sub(r"<cmt>__HR__(\d+)__</cmt>", self._inject_hr, xml)
        return xml

    @staticmethod
    def _inject_hr(match: re.Match) -> str:
        bpm = match.group(1)
        return (
            f"<extensions>"
            f"<gpxtpx:TrackPointExtension {_HR_NS}>"
            f"<gpxtpx:hr>{bpm}</gpxtpx:hr>"
            f"</gpxtpx:TrackPointExtension>"
            f"</extensions>"
        )
