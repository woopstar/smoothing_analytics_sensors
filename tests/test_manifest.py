"""Tests for the integration manifest."""

import json
from pathlib import Path

MANIFEST = Path(__file__).parent.parent / (
    "custom_components/smoothing_analytics_sensors/manifest.json"
)


def test_manifest_describes_a_calculated_helper() -> None:
    """SAS computes values from other entities and has no runtime dependencies."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["iot_class"] == "calculated"
    assert manifest["integration_type"] == "helper"
    assert "after_dependencies" not in manifest
    assert "dependencies" not in manifest
    assert "requirements" not in manifest
    assert manifest["documentation"].endswith("/wiki")


def test_manifest_lists_marketplace_categories() -> None:
    """One to three known categories, as the HACS action and Marketplace require."""
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    categories = manifest["categories"]
    assert 1 <= len(categories) <= 3
    assert len(set(categories)) == len(categories)
    assert "helpers.calculate_value" in categories


def test_brand_icon_ships_with_the_integration() -> None:
    """The Marketplace reads the icon from the integration's brand folder."""
    assert (MANIFEST.parent / "brand" / "icon.png").is_file()
