from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)
    classes: list[str] = Field(default_factory=lambda: ["lesion"])

    @field_validator("classes")
    @classmethod
    def validate_classes(cls, values: list[str]) -> list[str]:
        cleaned = []
        for value in values:
            item = value.strip()
            if item and item not in cleaned:
                cleaned.append(item)
        if not cleaned:
            raise ValueError("At least one annotation class is required.")
        return cleaned


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    classes: list[str]
    created_at: datetime


class ImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    original_name: str
    width: int
    height: int
    created_at: datetime
    annotation_count: int = 0


class AnnotationCreate(BaseModel):
    annotation_type: Literal["bbox", "polygon"]
    label: str = Field(min_length=1, max_length=100)
    geometry: dict
    source: Literal["manual", "ai-suggestion"] = "manual"

    @field_validator("geometry")
    @classmethod
    def validate_geometry(cls, geometry: dict, info):
        annotation_type = info.data.get("annotation_type")

        if annotation_type == "bbox":
            required = ("x", "y", "width", "height")
            if not all(key in geometry for key in required):
                raise ValueError("bbox requires x, y, width, and height.")
            if float(geometry["width"]) <= 0 or float(geometry["height"]) <= 0:
                raise ValueError("bbox width and height must be positive.")

        elif annotation_type == "polygon":
            points = geometry.get("points")
            if not isinstance(points, list) or len(points) < 3:
                raise ValueError("polygon requires at least three points.")

        return geometry


class AnnotationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    image_id: int
    annotation_type: str
    label: str
    geometry: dict
    source: str
    created_at: datetime


class PreAnnotationResponse(BaseModel):
    annotation_type: Literal["polygon"]
    label: str
    geometry: dict
    source: Literal["ai-suggestion"]
    inference_mode: str
    message: str


class ProjectStats(BaseModel):
    project_id: int
    image_count: int
    annotation_count: int
    annotated_image_count: int
    class_counts: dict[str, int]
