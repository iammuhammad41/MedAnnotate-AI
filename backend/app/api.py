from __future__ import annotations

import io
import json
from collections import Counter
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import Annotation, ImageAsset, Project
from backend.app.schemas import (
    AnnotationCreate,
    AnnotationOut,
    ImageOut,
    PreAnnotationResponse,
    ProjectCreate,
    ProjectOut,
    ProjectStats,
)
from backend.app.services.export import coco_export, yolo_export_zip
from backend.app.services.preannotation import suggest_polygon
from backend.app.services.storage import image_path, read_image, store_image


router = APIRouter(prefix="/api")


def get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


def get_image_or_404(db: Session, image_id: int) -> ImageAsset:
    image = db.get(ImageAsset, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Image not found.")
    return image


@router.post("/projects", response_model=ProjectOut)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    project = Project(
        name=payload.name,
        description=payload.description,
        classes=payload.classes,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).order_by(Project.created_at.desc()).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return get_project_or_404(db, project_id)


@router.post("/projects/{project_id}/images", response_model=ImageOut)
async def upload_project_image(
    project_id: int,
    image: Annotated[UploadFile, File()],
    db: Session = Depends(get_db),
):
    get_project_or_404(db, project_id)

    stored_name, width, height = await store_image(image)

    asset = ImageAsset(
        project_id=project_id,
        original_name=image.filename or stored_name,
        stored_name=stored_name,
        width=width,
        height=height,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return ImageOut(
        id=asset.id,
        project_id=asset.project_id,
        original_name=asset.original_name,
        width=asset.width,
        height=asset.height,
        created_at=asset.created_at,
        annotation_count=0,
    )


@router.get("/projects/{project_id}/images", response_model=list[ImageOut])
def list_project_images(project_id: int, db: Session = Depends(get_db)):
    get_project_or_404(db, project_id)

    images = (
        db.query(ImageAsset)
        .filter(ImageAsset.project_id == project_id)
        .order_by(ImageAsset.created_at.desc())
        .all()
    )

    return [
        ImageOut(
            id=image.id,
            project_id=image.project_id,
            original_name=image.original_name,
            width=image.width,
            height=image.height,
            created_at=image.created_at,
            annotation_count=len(image.annotations),
        )
        for image in images
    ]


@router.get("/images/{image_id}/file")
def get_image_file(image_id: int, db: Session = Depends(get_db)):
    image = get_image_or_404(db, image_id)
    path = image_path(image.stored_name)
    return FileResponse(path=path)


@router.get(
    "/images/{image_id}/annotations",
    response_model=list[AnnotationOut],
)
def list_annotations(image_id: int, db: Session = Depends(get_db)):
    get_image_or_404(db, image_id)
    return (
        db.query(Annotation)
        .filter(Annotation.image_id == image_id)
        .order_by(Annotation.id)
        .all()
    )


@router.post(
    "/images/{image_id}/annotations",
    response_model=AnnotationOut,
)
def create_annotation(
    image_id: int,
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
):
    image = get_image_or_404(db, image_id)
    project = get_project_or_404(db, image.project_id)

    if payload.label not in project.classes:
        raise HTTPException(
            status_code=400,
            detail=f"Label must be one of {project.classes}.",
        )

    annotation = Annotation(
        image_id=image_id,
        annotation_type=payload.annotation_type,
        label=payload.label,
        geometry=payload.geometry,
        source=payload.source,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return annotation


@router.delete("/annotations/{annotation_id}")
def delete_annotation(annotation_id: int, db: Session = Depends(get_db)):
    annotation = db.get(Annotation, annotation_id)
    if annotation is None:
        raise HTTPException(status_code=404, detail="Annotation not found.")

    db.delete(annotation)
    db.commit()
    return {"deleted": annotation_id}


@router.post(
    "/images/{image_id}/preannotate",
    response_model=PreAnnotationResponse,
)
def preannotate_image(
    image_id: int,
    label: Annotated[str, Form()],
    db: Session = Depends(get_db),
):
    image = get_image_or_404(db, image_id)
    project = get_project_or_404(db, image.project_id)

    if label not in project.classes:
        raise HTTPException(
            status_code=400,
            detail=f"Label must be one of {project.classes}.",
        )

    image_bgr = read_image(image.stored_name)
    points, mode = suggest_polygon(image_bgr)

    if len(points) < 3:
        raise HTTPException(
            status_code=422,
            detail="No suitable pre-annotation region was found.",
        )

    return PreAnnotationResponse(
        annotation_type="polygon",
        label=label,
        geometry={"points": points},
        source="ai-suggestion",
        inference_mode=mode,
        message=(
            "AI suggestion generated from configured checkpoint."
            if mode == "checkpoint"
            else "Demo heuristic suggestion generated; review before saving."
        ),
    )


@router.get("/projects/{project_id}/stats", response_model=ProjectStats)
def project_stats(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)

    images = (
        db.query(ImageAsset)
        .filter(ImageAsset.project_id == project.id)
        .all()
    )

    annotation_count = 0
    annotated_image_count = 0
    class_counter = Counter()

    for image in images:
        if image.annotations:
            annotated_image_count += 1

        for annotation in image.annotations:
            annotation_count += 1
            class_counter[annotation.label] += 1

    return ProjectStats(
        project_id=project.id,
        image_count=len(images),
        annotation_count=annotation_count,
        annotated_image_count=annotated_image_count,
        class_counts=dict(class_counter),
    )


@router.get("/projects/{project_id}/export/coco")
def export_coco(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    payload = coco_export(db, project)

    content = json.dumps(payload, indent=2).encode("utf-8")
    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="project_{project.id}_coco.json"'
            )
        },
    )


@router.get("/projects/{project_id}/export/yolo")
def export_yolo(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(db, project_id)
    content = yolo_export_zip(db, project)

    return Response(
        content=content,
        media_type="application/zip",
        headers={
            "Content-Disposition": (
                f'attachment; filename="project_{project.id}_yolo.zip"'
            )
        },
    )
