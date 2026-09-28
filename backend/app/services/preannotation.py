from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import torch
from monai.networks.nets import UNet

from backend.app.config import get_settings


def build_model() -> torch.nn.Module:
    """Default binary 2-D MONAI U-Net adapter."""
    return UNet(
        spatial_dims=2,
        in_channels=1,
        out_channels=1,
        channels=(16, 32, 64, 128, 256),
        strides=(2, 2, 2, 2),
        num_res_units=2,
        norm="INSTANCE",
    )


def _clean_state_dict(state):
    if isinstance(state, dict) and "state_dict" in state:
        state = state["state_dict"]

    if isinstance(state, dict):
        cleaned = {}
        for key, value in state.items():
            new_key = key
            for prefix in ("model.", "network.", "module."):
                if new_key.startswith(prefix):
                    new_key = new_key[len(prefix):]
            cleaned[new_key] = value
        return cleaned

    return state


def predict_checkpoint(image_bgr: np.ndarray, checkpoint: Path) -> np.ndarray:
    settings = get_settings()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = build_model().to(device)
    state = torch.load(checkpoint, map_location=device)
    model.load_state_dict(_clean_state_dict(state), strict=True)
    model.eval()

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    original_h, original_w = gray.shape

    size = settings.model_input_size
    resized = cv2.resize(gray, (size, size), interpolation=cv2.INTER_AREA)
    tensor = resized.astype(np.float32) / 255.0
    tensor = (tensor - tensor.mean()) / max(float(tensor.std()), 1e-6)
    tensor = torch.from_numpy(tensor).unsqueeze(0).unsqueeze(0).to(device)

    with torch.no_grad():
        logits = model(tensor)
        if isinstance(logits, (tuple, list)):
            logits = logits[0]
        if isinstance(logits, dict):
            logits = next(iter(logits.values()))
        probability = torch.sigmoid(logits)[0, 0].cpu().numpy()

    probability = cv2.resize(
        probability,
        (original_w, original_h),
        interpolation=cv2.INTER_LINEAR,
    )
    return (probability >= settings.threshold).astype(np.uint8)


def _largest_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(
        (mask > 0).astype(np.uint8),
        connectivity=8,
    )
    if count <= 1:
        return (mask > 0).astype(np.uint8)

    areas = stats[1:, cv2.CC_STAT_AREA]
    largest_label = 1 + int(np.argmax(areas))
    return (labels == largest_label).astype(np.uint8)


def predict_demo(image_bgr: np.ndarray) -> np.ndarray:
    """
    Deterministic region proposal for software demonstration only.
    It is not a trained medical prediction.
    """
    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 0)
    enhanced = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8),
    ).apply(blurred)

    normalized = enhanced.astype(np.float32) / 255.0
    darkness = 1.0 - normalized

    h, w = gray.shape
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w / 2.0, h / 2.0
    sx, sy = max(w * 0.42, 1), max(h * 0.42, 1)
    center_prior = np.exp(
        -0.5 * (((xx - cx) / sx) ** 2 + ((yy - cy) / sy) ** 2)
    ).astype(np.float32)

    score = 0.8 * darkness + 0.2 * center_prior
    score = cv2.GaussianBlur(score, (0, 0), sigmaX=3)

    threshold = float(np.percentile(score, 86))
    mask = (score >= threshold).astype(np.uint8)

    kernel = np.ones((5, 5), dtype=np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

    return _largest_component(mask)


def contour_to_polygon(mask: np.ndarray, max_points: int = 40) -> list[list[float]]:
    binary = (mask > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(
        binary,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return []

    contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(contour, True)
    epsilon = max(1.0, 0.01 * perimeter)
    approx = cv2.approxPolyDP(contour, epsilon, True)

    points = approx[:, 0, :].astype(float).tolist()
    if len(points) > max_points:
        indices = np.linspace(0, len(points) - 1, max_points, dtype=int)
        points = [points[i] for i in indices]

    return [[round(float(x), 2), round(float(y), 2)] for x, y in points]


def suggest_polygon(image_bgr: np.ndarray) -> tuple[list[list[float]], str]:
    settings = get_settings()

    if settings.model_path:
        checkpoint = Path(settings.model_path)
        if checkpoint.is_file():
            mask = predict_checkpoint(image_bgr, checkpoint)
            return contour_to_polygon(mask), "checkpoint"

    if not settings.allow_demo_mode:
        raise RuntimeError(
            "No model checkpoint is configured and demo mode is disabled."
        )

    mask = predict_demo(image_bgr)
    return contour_to_polygon(mask), "demo-heuristic"
