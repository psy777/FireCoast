"""Epoch-based semantic version utilities for FireCoast."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, order=True)
class EpochSemVer:
    """Semantic version that includes an epoch segment.

    The format is ``epoch.major.minor.patch`` where each component is a
    non-negative integer. Ordering compares epoch first, then major, minor,
    and patch components.
    """

    epoch: int
    major: int
    minor: int
    patch: int

    @classmethod
    def parse(cls, value: str) -> "EpochSemVer":
        raw = value.strip()
        if not raw:
            raise ValueError("Version string is empty")

        parts = raw.split(".")
        if len(parts) != 4:
            raise ValueError(
                "Version must have four numeric components: epoch.major.minor.patch"
            )

        try:
            epoch, major, minor, patch = (int(part) for part in parts)
        except ValueError as exc:  # pragma: no cover - defensive
            raise ValueError("Version components must be integers") from exc

        for component_name, component_value in (
            ("epoch", epoch),
            ("major", major),
            ("minor", minor),
            ("patch", patch),
        ):
            if component_value < 0:
                raise ValueError(f"{component_name} component cannot be negative")

        return cls(epoch=epoch, major=major, minor=minor, patch=patch)

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.epoch}.{self.major}.{self.minor}.{self.patch}"


def read_version_file(path: Path) -> EpochSemVer:
    """Read an :class:`EpochSemVer` from a version file.

    Parameters
    ----------
    path:
        Path to the file containing the version string.

    Returns
    -------
    EpochSemVer
        Parsed version object.

    Raises
    ------
    FileNotFoundError
        If the version file does not exist.
    ValueError
        If the file contents cannot be parsed as an epoch semantic version.
    """

    if not path.exists():
        raise FileNotFoundError(path)

    return EpochSemVer.parse(path.read_text())
