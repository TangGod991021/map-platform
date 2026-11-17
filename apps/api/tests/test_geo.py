import pytest

from app.core.geo import is_in_guizhou
from app.services.map_service import validate_coordinate


def test_point_inside_guizhou():
    assert is_in_guizhou(106.63, 26.647) is True
    validate_coordinate(106.63, 26.647)


def test_point_outside_polygon_but_inside_bbox():
    """外接矩形内的省外点应被省界多边形拒绝。"""
    assert is_in_guizhou(104.5, 28.5) is False
    with pytest.raises(ValueError, match="贵州省"):
        validate_coordinate(104.5, 28.5)


def test_point_outside_bbox():
    assert is_in_guizhou(120.0, 31.0) is False
    with pytest.raises(ValueError, match="贵州省"):
        validate_coordinate(120.0, 31.0)
