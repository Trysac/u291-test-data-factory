"""Behavior tests for the public API of test_data_factory."""

from __future__ import annotations

import pytest

import test_data_factory


def test_normalize_trims_and_lowercases() -> None:
    assert test_data_factory.normalize("  Hello World ") == "hello world"


@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_normalize_rejects_blank_input(value: str) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        test_data_factory.normalize(value)


def test_version_is_semver() -> None:
    parts = test_data_factory.__version__.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
