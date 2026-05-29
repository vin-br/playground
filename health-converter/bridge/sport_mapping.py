"""
Sport mapping tables.

Central place for Withings sport codes → normalized labels → Strava GPX types.
"""

from .models import StravaActivityType

# ── Withings numeric sport codes → normalized slug ──────────────────────────
SPORT_MAP: dict[int, str] = {
    1: "walk",
    2: "run",
    3: "hike",
    4: "skate",
    5: "bmx",
    6: "ride",
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
    17: "workout",
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
    306: "indoor_cycling",
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

# ── Normalized label → Strava GPX <type> ────────────────────────────────────
# Keys include both CSV string labels (lowercased, spaces→underscores) and
# SPORT_MAP slug values so both code paths resolve correctly.
STRAVA_TYPE_MAP: dict[str, StravaActivityType] = {
    # CSV string labels
    "cycling": StravaActivityType.Ride,
    "indoor_cycling": StravaActivityType.VirtualRide,
    "walking": StravaActivityType.Walk,
    "running": StravaActivityType.Run,
    "swimming": StravaActivityType.Swim,
    "rowing": StravaActivityType.Rowing,
    "tennis": StravaActivityType.Workout,
    "weights": StravaActivityType.WeightTraining,
    "other": StravaActivityType.Workout,
    "hiking": StravaActivityType.Hike,
    "yoga": StravaActivityType.Yoga,
    # SPORT_MAP slugs
    "ride": StravaActivityType.Ride,
    "run": StravaActivityType.Run,
    "walk": StravaActivityType.Walk,
    "hike": StravaActivityType.Hike,
    "swim": StravaActivityType.Swim,
    "indoor_run": StravaActivityType.VirtualRun,
    "indoor_walk": StravaActivityType.Walk,
    "indoor_rowing": StravaActivityType.Rowing,
    "ski": StravaActivityType.AlpineSki,
    "alpine_ski": StravaActivityType.AlpineSki,
    "nordic_ski": StravaActivityType.NordicSki,
    "snowboard": StravaActivityType.Snowboard,
    "snowshoe": StravaActivityType.Snowshoe,
    "elliptical": StravaActivityType.Elliptical,
    "weight_training": StravaActivityType.WeightTraining,
    "crossfit": StravaActivityType.Crossfit,
    "surf": StravaActivityType.Surfing,
    "kitesurf": StravaActivityType.Kitesurf,
    "windsurf": StravaActivityType.Windsurf,
    "golf": StravaActivityType.Golf,
    "soccer": StravaActivityType.Soccer,
    "skateboard": StravaActivityType.Skateboard,
    "skate": StravaActivityType.IceSkate,
    "ice_skate": StravaActivityType.IceSkate,
    "workout": StravaActivityType.Workout,
    "hiit": StravaActivityType.Workout,
    "pilates": StravaActivityType.Yoga,
    "stretching": StravaActivityType.Yoga,
    "dance": StravaActivityType.Workout,
    "boxing": StravaActivityType.Workout,
    "martial_arts": StravaActivityType.Workout,
    "basketball": StravaActivityType.Workout,
    "volleyball": StravaActivityType.Workout,
    "rugby": StravaActivityType.Workout,
    "football": StravaActivityType.Workout,
    "table_tennis": StravaActivityType.Workout,
    "squash": StravaActivityType.Workout,
    "badminton": StravaActivityType.Workout,
    "water_polo": StravaActivityType.Swim,
    "bmx": StravaActivityType.Ride,
    "horse_riding": StravaActivityType.Ride,
    "fencing": StravaActivityType.Workout,
    "wrestling": StravaActivityType.Workout,
    "bodyboard": StravaActivityType.Surfing,
}

# Sports that are inherently indoor (no real GPS expected)
INDOOR_SPORTS: frozenset[str] = frozenset({
    "indoor_cycling", "indoor_run", "indoor_walk", "indoor_rowing",
    "weights", "weight_training", "elliptical", "yoga", "crossfit",
    "hiit", "pilates", "stretching", "swimming",
})


def resolve_strava_type(sport_label: str) -> StravaActivityType:
    """Resolve a normalized sport label to its Strava ActivityType."""
    return STRAVA_TYPE_MAP.get(sport_label, StravaActivityType.Workout)
