from types import SimpleNamespace

from backend.app.services.export import geometry_bbox, polygon_area


def test_polygon_area_square():
    points = [[0, 0], [10, 0], [10, 10], [0, 10]]
    assert polygon_area(points) == 100.0


def test_geometry_bbox_polygon():
    annotation = SimpleNamespace(
        annotation_type="polygon",
        geometry={
            "points": [[10, 20], [30, 20], [35, 50], [8, 45]]
        },
    )

    x, y, w, h = geometry_bbox(annotation)

    assert x == 8.0
    assert y == 20.0
    assert w == 27.0
    assert h == 30.0
