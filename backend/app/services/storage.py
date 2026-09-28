from __future__ import annotations

import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import HTTPException, UploadFile

from backend.app.config import get_settings


ALLOWED_EXTENSIONS = (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff")


def valid_image_name(filename: str | None) -> bool:
    return bool(filename and filename.lower().endswith(ALLOWED_EXTENSIONS))


async def store_image(upload: UploadFile) -> tuple[str, int, int]:
    if not valid_image_name(upload.filename):
        raise HTTPException(
            status_code=400,
            detail="Supported formats: PNG, JPG, JPEG, BMP, TIF, TIFF.",
        )

    raw = await upload.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded image is empty.")

    array = np.frombuffer(raw, dtype=np.uint8)
    image = cv2.imdecode(array, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="Could not decode image.")

    suffix = Path(upload.filename).suffix.lower()
    stored_name = f"{uuid.uuid4().hex}{suffix}"
    path = get_settings().storage_path / stored_name
    path.write_bytes(raw)

    height, width = image.shape[:2]
    return stored_name, width, height


def image_path(stored_name: str) -> Path:
    path = get_settings().storage_path / stored_name
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file is missing.")
    return path


def read_image(stored_name: str) -> np.ndarray:
    path = image_path(stored_name)
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=500, detail="Stored image cannot be decoded.")
    return image
