import React from "react";

export default function ImagePanel({
  images,
  selectedImage,
  onSelect,
  onUpload,
  disabled
}) {
  async function handleUpload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    await onUpload(file);
    event.target.value = "";
  }

  return (
    <aside className="panel image-panel">
      <div className="panel-title-row">
        <div>
          <span className="eyebrow">Dataset</span>
          <h2>Images</h2>
        </div>

        <label className={`upload-button ${disabled ? "disabled" : ""}`}>
          + Upload
          <input
            type="file"
            accept=".png,.jpg,.jpeg,.bmp,.tif,.tiff"
            onChange={handleUpload}
            disabled={disabled}
            hidden
          />
        </label>
      </div>

      <div className="image-list">
        {images.map((image) => (
          <button
            type="button"
            key={image.id}
            className={`image-card ${
              selectedImage?.id === image.id ? "active" : ""
            }`}
            onClick={() => onSelect(image)}
          >
            <span className="image-index">#{image.id}</span>
            <div>
              <strong>{image.original_name}</strong>
              <span>
                {image.width} × {image.height} · {image.annotation_count} annotations
              </span>
            </div>
          </button>
        ))}

        {!images.length && (
          <p className="muted">
            {disabled
              ? "Select a project first."
              : "Upload PNG/JPG/TIFF research images."}
          </p>
        )}
      </div>
    </aside>
  );
}
