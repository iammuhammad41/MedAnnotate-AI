from __future__ import annotations

import io
import json
import zipfile

from sqlalchemy.orm import Session

from backend.app.models import Annotation, ImageAsset, Project
from backend.app.services.storage import image_path


def polygon_area(points: list[list[float]]) -> float:
    if len(points) < 3:
        return 0.0

    area = 0.0
    for idx, point in enumerate(points):
        x1, y1 = point
        x2, y2 = points[(idx + 1) % len(points)]
        area += x1 * y2 - x2 * y1

    return abs(area) / 2.0


def geometry_bbox(annotation: Annotation) -> tuple[float, float, float, float]:
    geometry = annotation.geometry

    if annotation.annotation_type == "bbox":
        return (
            float(geometry["x"]),
            float(geometry["y"]),
            float(geometry["width"]),
            float(geometry["height"]),
        )

    points = geometry["points"]
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    x1, x2 = min(xs), max(xs)
    y1, y2 = min(ys), max(ys)
    return x1, y1, x2 - x1, y2 - y1


def coco_export(db: Session, project: Project) -> dict:
    category_map = {
        label: idx + 1
        for idx, label in enumerate(project.classes)
    }

    images = (
        db.query(ImageAsset)
        .filter(ImageAsset.project_id == project.id)
        .order_by(ImageAsset.id)
        .all()
    )

    image_items = []
    annotation_items = []
    annotation_id = 1

    for image in images:
        image_items.append(
            {
                "id": image.id,
                "file_name": image.original_name,
                "width": image.width,
                "height": image.height,
            }
        )

        for annotation in image.annotations:
            if annotation.label not in category_map:
                continue

            x, y, w, h = geometry_bbox(annotation)

            if annotation.annotation_type == "polygon":
                points = annotation.geometry["points"]
                segmentation = [
                    [coord for point in points for coord in (float(point[0]), float(point[1]))]
                ]
                area = polygon_area(points)
            else:
                segmentation = []
                area = float(w * h)

            annotation_items.append(
                {
                    "id": annotation_id,
                    "image_id": image.id,
                    "category_id": category_map[annotation.label],
                    "bbox": [x, y, w, h],
                    "area": area,
                    "iscrowd": 0,
                    "segmentation": segmentation,
                    "source": annotation.source,
                }
            )
            annotation_id += 1

    return {
        "info": {
            "description": project.name,
            "generator": "MedAnnotate AI",
        },
        "images": image_items,
        "annotations": annotation_items,
        "categories": [
            {"id": category_map[label], "name": label}
            for label in project.classes
        ],
    }


def yolo_export_zip(db: Session, project: Project) -> bytes:
    class_map = {
        label: idx
        for idx, label in enumerate(project.classes)
    }

    images = (
        db.query(ImageAsset)
        .filter(ImageAsset.project_id == project.id)
        .order_by(ImageAsset.id)
        .all()
    )

    buffer = io.BytesIO()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(
            "classes.txt",
            "\n".join(project.classes) + "\n",
        )

        for image in images:
            rows = []

            # Include the source image so the YOLO export is immediately usable.
            source_path = image_path(image.stored_name)
            zf.write(
                source_path,
                arcname=f"images/{image.original_name}",
            )

            for annotation in image.annotations:
                if annotation.label not in class_map:
                    continue

                x, y, w, h = geometry_bbox(annotation)

                x_center = (x + w / 2.0) / image.width
                y_center = (y + h / 2.0) / image.height
                width = w / image.width
                height = h / image.height

                rows.append(
                    f"{class_map[annotation.label]} "
                    f"{x_center:.6f} {y_center:.6f} "
                    f"{width:.6f} {height:.6f}"
                )

            stem = image.original_name.rsplit(".", 1)[0]
            zf.writestr(
                f"labels/{stem}.txt",
                ("\n".join(rows) + "\n") if rows else "",
            )

        dataset_yaml = (
            f"path: .\n"
            f"train: images/train\n"
            f"val: images/val\n"
            f"names:\n"
            + "\n".join(
                f"  {idx}: {label}"
                for label, idx in class_map.items()
            )
            + "\n"
        )
        zf.writestr("dataset.yaml", dataset_yaml)

    return buffer.getvalue()
