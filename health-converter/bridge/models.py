"""
Data models for the health_bridge framework.

These are the canonical internal representations — importers produce them,
exporters consume them.  Designed as Pydantic models so they work directly
with FastAPI when the web layer is added later.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class StravaActivityType(str, Enum):
    """Strava ActivityType enum — the values accepted by GPX <type>."""
    AlpineSki = "AlpineSki"
    BackcountrySki = "BackcountrySki"
    Canoeing = "Canoeing"
    Crossfit = "Crossfit"
    EBikeRide = "EBikeRide"
    Elliptical = "Elliptical"
    Golf = "Golf"
    Handcycle = "Handcycle"
    Hike = "Hike"
    IceSkate = "IceSkate"
    InlineSkate = "InlineSkate"
    Kayaking = "Kayaking"
    Kitesurf = "Kitesurf"
    NordicSki = "NordicSki"
    Ride = "Ride"
    RockClimbing = "RockClimbing"
    RollerSki = "RollerSki"
    Rowing = "Rowing"
    Run = "Run"
    Sail = "Sail"
    Skateboard = "Skateboard"
    Snowboard = "Snowboard"
    Snowshoe = "Snowshoe"
    Soccer = "Soccer"
    StairStepper = "StairStepper"
    StandUpPaddling = "StandUpPaddling"
    Surfing = "Surfing"
    Swim = "Swim"
    Velomobile = "Velomobile"
    VirtualRide = "VirtualRide"
    VirtualRun = "VirtualRun"
    Walk = "Walk"
    WeightTraining = "WeightTraining"
    Wheelchair = "Wheelchair"
    Windsurf = "Windsurf"
    Workout = "Workout"
    Yoga = "Yoga"


class TrackPoint(BaseModel):
    """A single time-stamped point with optional elevation and heart rate."""
    timestamp: float
    lat: float
    lon: float
    ele: float | None = None
    hr: int | None = None

    @property
    def datetime_utc(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


class Workout(BaseModel):
    """Canonical workout representation — the bridge between importers and exporters."""
    sport_label: str                         # normalized label e.g. "indoor_cycling"
    strava_type: StravaActivityType = StravaActivityType.Workout
    start: float                             # unix timestamp
    end: float                               # unix timestamp
    distance_m: float = 0.0
    calories: float = 0.0
    ref_lat: float = 0.0                     # fallback reference coordinate
    ref_lon: float = 0.0
    trackpoints: list[TrackPoint] = Field(default_factory=list)
    source: str = ""                         # e.g. "withings", "garmin"
    raw_metadata: dict = Field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        return self.end - self.start

    @property
    def start_utc(self) -> datetime:
        return datetime.fromtimestamp(self.start, tz=timezone.utc)

    @property
    def end_utc(self) -> datetime:
        return datetime.fromtimestamp(self.end, tz=timezone.utc)
