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
