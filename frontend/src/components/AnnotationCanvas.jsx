import React, { useMemo, useRef, useState } from "react";
import { imageUrl } from "../api";

function scalePoint(event, imageElement, imageWidth, imageHeight) {
  const rect = imageElement.getBoundingClientRect();

  return {
    x: ((event.clientX - rect.left) / rect.width) * imageWidth,
    y: ((event.clientY - rect.top) / rect.height) * imageHeight
  };
}

function displayGeometry(annotation, displayWidth, displayHeight, imageWidth, imageHeight) {
  const sx = displayWidth / imageWidth;
  const sy = displayHeight / imageHeight;

  if (annotation.annotation_type === "bbox") {
    const g = annotation.geometry;
    return {
      type: "bbox",
      x: g.x * sx,
      y: g.y * sy,
      width: g.width * sx,
      height: g.height * sy
    };
  }

  return {
    type: "polygon",
    points: annotation.geometry.points.map(([x, y]) => [x * sx, y * sy])
  };
}

export default function AnnotationCanvas({
  image,
  annotations,
  draft,
  setDraft,
  mode
}) {
  const imageRef = useRef(null);
  const [displaySize, setDisplaySize] = useState({ width: 1, height: 1 });
  const [start, setStart] = useState(null);
  const [polygonPoints, setPolygonPoints] = useState([]);

  const allAnnotations = useMemo(() => {
    const items = [...annotations];
    if (draft) {
      items.push({
        ...draft,
        id: "draft"
      });
    }
    return items;
  }, [annotations, draft]);

  if (!image) {
    return (
      <div className="empty-stage">
        <div>
          <h2>Select an image</h2>
          <p>Choose a dataset image to begin annotation.</p>
        </div>
      </div>
    );
  }

  function syncDisplaySize() {
    if (!imageRef.current) return;
    const rect = imageRef.current.getBoundingClientRect();
    setDisplaySize({
      width: rect.width,
      height: rect.height
    });
  }

  function pointerDown(event) {
    if (mode !== "bbox" || !imageRef.current) return;

    const point = scalePoint(
      event,
      imageRef.current,
      image.width,
      image.height
    );

    setStart(point);
    setDraft({
      annotation_type: "bbox",
      geometry: {
        x: point.x,
        y: point.y,
        width: 1,
        height: 1
      },
      source: "manual"
    });
  }

  function pointerMove(event) {
    if (mode !== "bbox" || !start || !imageRef.current) return;

    const point = scalePoint(
      event,
      imageRef.current,
      image.width,
      image.height
    );

    setDraft({
      annotation_type: "bbox",
      geometry: {
        x: Math.min(start.x, point.x),
        y: Math.min(start.y, point.y),
        width: Math.abs(point.x - start.x),
        height: Math.abs(point.y - start.y)
      },
      source: "manual"
    });
  }

  function pointerUp() {
    setStart(null);
  }

  function polygonClick(event) {
    if (mode !== "polygon" || !imageRef.current) return;

    const point = scalePoint(
      event,
      imageRef.current,
      image.width,
      image.height
    );

    const next = [...polygonPoints, [point.x, point.y]];
    setPolygonPoints(next);

    setDraft({
      annotation_type: "polygon",
      geometry: { points: next },
      source: "manual"
    });
  }

  function finishPolygon(event) {
    if (mode !== "polygon") return;
    event.preventDefault();

    if (polygonPoints.length >= 3) {
      setDraft({
        annotation_type: "polygon",
        geometry: { points: polygonPoints },
        source: "manual"
      });
    }

    setPolygonPoints([]);
  }

  const sx = displaySize.width / image.width;
  const sy = displaySize.height / image.height;

  return (
    <div className="annotation-stage">
      <div
        className="image-wrapper"
        onPointerDown={pointerDown}
        onPointerMove={pointerMove}
        onPointerUp={pointerUp}
        onPointerLeave={pointerUp}
        onClick={polygonClick}
        onDoubleClick={finishPolygon}
      >
        <img
          ref={imageRef}
          src={imageUrl(image.id)}
          alt={image.original_name}
          draggable="false"
          onLoad={syncDisplaySize}
        />

        <svg
          className="annotation-layer"
          width={displaySize.width}
          height={displaySize.height}
          viewBox={`0 0 ${displaySize.width} ${displaySize.height}`}
        >
          {allAnnotations.map((annotation, idx) => {
            const geometry = displayGeometry(
              annotation,
              displaySize.width,
              displaySize.height,
              image.width,
              image.height
            );

            const isDraft = annotation.id === "draft";

            if (geometry.type === "bbox") {
              return (
                <g key={`${annotation.id}-${idx}`}>
                  <rect
                    x={geometry.x}
                    y={geometry.y}
                    width={geometry.width}
                    height={geometry.height}
                    className={isDraft ? "shape draft" : "shape"}
                  />
                  {!isDraft && (
                    <text
                      x={geometry.x + 6}
                      y={Math.max(geometry.y - 8, 16)}
                      className="shape-label"
                    >
                      {annotation.label}
                    </text>
                  )}
                </g>
              );
            }

            const points = geometry.points
              .map(([x, y]) => `${x},${y}`)
              .join(" ");

            return (
              <g key={`${annotation.id}-${idx}`}>
                <polygon
                  points={points}
                  className={isDraft ? "shape polygon draft" : "shape polygon"}
                />
                {!isDraft && geometry.points[0] && (
                  <text
                    x={geometry.points[0][0] + 6}
                    y={Math.max(geometry.points[0][1] - 8, 16)}
                    className="shape-label"
                  >
                    {annotation.label}
                  </text>
                )}
              </g>
            );
          })}

          {mode === "polygon" &&
            polygonPoints.map(([x, y], idx) => (
              <circle
                key={`${x}-${y}-${idx}`}
                cx={x * sx}
                cy={y * sy}
                r="4"
                className="polygon-point"
              />
            ))}
        </svg>
      </div>

      <div className="stage-help">
        {mode === "bbox" ? (
          <span>Drag on the image to draw a bounding box.</span>
        ) : (
          <span>Click polygon vertices; double-click to finish the polygon.</span>
        )}
      </div>
    </div>
  );
}
