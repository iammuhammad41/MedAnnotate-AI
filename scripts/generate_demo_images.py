from pathlib import Path

import cv2
import numpy as np


def synthetic_ultrasound(index: int, size: int = 512) -> np.ndarray:
    rng = np.random.default_rng(100 + index)
    image = rng.normal(120, 27, size=(size, size)).astype(np.float32)

    y, x = np.mgrid[0:size, 0:size]
    image -= (y / size) * 20

    cx = 235 + index * 18
    cy = 250 - index * 12
    rx = 62 + index * 8
    ry = 48 + index * 5

    lesion = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
    image[lesion] -= 58
    image[lesion] += rng.normal(
        0,
        8,
        size=np.count_nonzero(lesion),
    )

    image = np.clip(image, 0, 255).astype(np.uint8)
    image = cv2.GaussianBlur(image, (3, 3), 0)

    color = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    cv2.putText(
        color,
        f"SYNTHETIC DEMO {index + 1}",
        (16, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.72,
        (240, 240, 240),
        2,
        cv2.LINE_AA,
    )
    return color


def main():
    output = Path("data/demo_images")
    output.mkdir(parents=True, exist_ok=True)

    for index in range(4):
        image = synthetic_ultrasound(index)
        cv2.imwrite(str(output / f"demo_ultrasound_{index + 1}.png"), image)

    print(f"Synthetic demo images written to: {output.resolve()}")


if __name__ == "__main__":
    main()
