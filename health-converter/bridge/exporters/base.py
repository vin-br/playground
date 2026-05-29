"""Abstract base class for health data exporters."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import Workout


class BaseExporter(ABC):
    """
    Base class for all exporters.

    Subclasses implement export_one() to convert a Workout to a file format,
    and export_all() for batch export.
    """

    format_name: str = "unknown"
    file_extension: str = ".dat"

    @abstractmethod
    def export_one(self, workout: Workout) -> str:
        """
        Convert a single Workout to the target format string.

        Returns:
            The file contents (e.g., GPX XML string).
        """
        ...

    def export_all(
        self, workouts: list[Workout], output_dir: Path, *, verbose: bool = False
    ) -> tuple[int, int]:
        """
        Export all workouts to files under output_dir/<year>/.

        Returns:
            (exported_count, failed_count)
        """
        exported = 0
        failed = 0
        total = len(workouts)
        for i, workout in enumerate(workouts, 1):
            year = workout.start_utc.strftime("%Y")
            out_dir = output_dir / year
            out_dir.mkdir(parents=True, exist_ok=True)
            fname = self.filename(workout)
            out_path = out_dir / fname
            try:
                content = self.export_one(workout)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(content)
                if verbose:
                    self._log_success(workout, out_path)
                exported += 1
            except Exception as e:
                print(f"[FAIL] {fname}: {e}")
                failed += 1
            if not verbose and i % 50 == 0:
                print(f"  [{i}/{total}]...")
        return exported, failed

    def filename(self, workout: Workout) -> str:
        """Generate a filename for the workout."""
        dt = workout.start_utc
        return f"{dt.strftime('%Y%m%d_%H%M%S')}_{workout.sport_label}{self.file_extension}"

    def _log_success(self, workout: Workout, path: Path) -> None:
        n_pts = len(workout.trackpoints)
        n_hr = sum(1 for p in workout.trackpoints if p.hr is not None)
        dist = f", {workout.distance_m / 1000:.1f}km" if workout.distance_m > 0 else ""
        print(f"[OK] {path.parent.name}/{path.name}  ({n_pts} pts, {n_hr} HR{dist})")
