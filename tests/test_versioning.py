from __future__ import annotations

import pytest

from services.versioning import EpochSemVer


def test_epoch_semver_parsing_and_ordering():
    version = EpochSemVer.parse("2.1.0.5")

    assert version.epoch == 2
    assert version.major == 1
    assert version.minor == 0
    assert version.patch == 5
    assert str(version) == "2.1.0.5"

    newer = EpochSemVer.parse("2.1.1.0")
    older = EpochSemVer.parse("1.9.9.9")

    assert newer > version
    assert version > older


def test_epoch_semver_rejects_invalid_values():
    with pytest.raises(ValueError):
        EpochSemVer.parse("")

    with pytest.raises(ValueError):
        EpochSemVer.parse("1.0.0")

    with pytest.raises(ValueError):
        EpochSemVer.parse("1.0.0.beta")

    with pytest.raises(ValueError):
        EpochSemVer.parse("-1.0.0.0")
