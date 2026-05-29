"""Abstract base class for health data importers."""

from abc import ABC, abstractmethod
from pathlib import Path

from ..models import Workout


class BaseImporter(ABC):
    """
    Base class for all importers.

    Subclasses implement load() to parse a source format and return
    a list of canonical Workout objects.
    """

    source_name: str = "unknown"

    @abstractmethod
    def load(self, source_path: Path) -> list[Workout]:
        """
        Parse the source data and return a list of Workout objects.

        Args:
            source_path: Path to the source directory or file.

        Returns:
            List of Workout objects with trackpoints and HR attached.
        """
        ...

    def inspect(self, source_path: Path) -> str:
        """
        Return a human-readable diagnostic string about the source data.
        Useful for debugging format changes before importing.
        """
        return f"No inspector implemented for {self.source_name}"
