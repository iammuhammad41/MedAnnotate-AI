import React, { useEffect, useMemo, useState } from "react";
import {
  createAnnotation,
  createProject,
  deleteAnnotation,
  exportUrl,
  getStats,
  listAnnotations,
  listImages,
  listProjects,
  preannotate,
  uploadImage
} from "./api";

import AnnotationCanvas from "./components/AnnotationCanvas";
import ImagePanel from "./components/ImagePanel";
import ProjectPanel from "./components/ProjectPanel";

export default function App() {
  const [projects, setProjects] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);

  const [images, setImages] = useState([]);
  const [selectedImage, setSelectedImage] = useState(null);

  const [annotations, setAnnotations] = useState([]);
  const [stats, setStats] = useState(null);

  const [mode, setMode] = useState("bbox");
  const [label, setLabel] = useState("");
  const [draft, setDraft] = useState(null);

  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const classes = selectedProject?.classes || [];

  useEffect(() => {
    refreshProjects();
  }, []);

  useEffect(() => {
    if (selectedProject) {
      setLabel(selectedProject.classes[0] || "");
      refreshProjectData(selectedProject.id);
    } else {
      setImages([]);
      setSelectedImage(null);
      setStats(null);
    }
  }, [selectedProject]);

  useEffect(() => {
    if (selectedImage) {
      refreshAnnotations(selectedImage.id);
    } else {
      setAnnotations([]);
    }
    setDraft(null);
  }, [selectedImage]);

  async function run(action) {
    setBusy(true);
    setMessage("");
    try {
      await action();
    } catch (error) {
      setMessage(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function refreshProjects() {
    const data = await listProjects();
    setProjects(data);

    if (!selectedProject && data.length) {
      setSelectedProject(data[0]);
    }
  }

  async function refreshProjectData(projectId) {
    const [imageData, statsData] = await Promise.all([
      listImages(projectId),
      getStats(projectId)
    ]);

    setImages(imageData);
    setStats(statsData);

    if (selectedImage) {
      const stillExists = imageData.find((item) => item.id === selectedImage.id);
      setSelectedImage(stillExists || imageData[0] || null);
    } else {
      setSelectedImage(imageData[0] || null);
    }
  }

  async function refreshAnnotations(imageId) {
    const data = await listAnnotations(imageId);
    setAnnotations(data);
  }

  function handleCreateProject(payload) {
    return run(async () => {
      const project = await createProject(payload);
      await refreshProjects();
      setSelectedProject(project);
      setMessage("Project created.");
    });
  }

  function handleUpload(file) {
    if (!selectedProject) return;

    return run(async () => {
      const created = await uploadImage(selectedProject.id, file);
      await refreshProjectData(selectedProject.id);
      setSelectedImage(created);
      setMessage("Image uploaded.");
    });
  }

  function handleSaveDraft() {
    if (!selectedImage || !draft || !label) return;

    return run(async () => {
      const payload = {
        annotation_type: draft.annotation_type,
        label,
        geometry: draft.geometry,
        source: draft.source || "manual"
      };

      await createAnnotation(selectedImage.id, payload);
      setDraft(null);
      await refreshAnnotations(selectedImage.id);
      await refreshProjectData(selectedProject.id);
      setMessage("Annotation saved.");
    });
  }

  function handlePreannotate() {
    if (!selectedImage || !label) return;

    return run(async () => {
      const suggestion = await preannotate(selectedImage.id, label);
      setDraft({
        annotation_type: suggestion.annotation_type,
        geometry: suggestion.geometry,
        source: suggestion.source
      });
      setMode("polygon");
      setMessage(suggestion.message);
    });
  }

  function handleDelete(annotationId) {
    return run(async () => {
      await deleteAnnotation(annotationId);
      await refreshAnnotations(selectedImage.id);
      await refreshProjectData(selectedProject.id);
      setMessage("Annotation deleted.");
    });
  }

  const completion = useMemo(() => {
    if (!stats?.image_count) return 0;
    return Math.round(
      (stats.annotated_image_count / stats.image_count) * 100
    );
  }, [stats]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <span className="eyebrow">Medical AI research tooling</span>
          <h1>MedAnnotate AI</h1>
        </div>

        <div className="topbar-note">
          Research prototype · De-identified data only
        </div>
      </header>

      {message && (
        <div className={message.toLowerCase().includes("error") ? "toast error" : "toast"}>
          {message}
        </div>
      )}

      <main className="workspace-grid">
        <ProjectPanel
          projects={projects}
          selectedProject={selectedProject}
          onSelect={(project) => {
            setSelectedProject(project);
            setSelectedImage(null);
          }}
          onCreate={handleCreateProject}
        />

        <ImagePanel
          images={images}
          selectedImage={selectedImage}
          onSelect={setSelectedImage}
          onUpload={handleUpload}
          disabled={!selectedProject}
        />

        <section className="main-workspace">
          {selectedProject && (
            <div className="workspace-toolbar">
              <div className="tool-group">
                <button
                  type="button"
                  className={mode === "bbox" ? "tool active" : "tool"}
                  onClick={() => {
                    setMode("bbox");
                    setDraft(null);
                  }}
                >
                  Box
                </button>
                <button
                  type="button"
                  className={mode === "polygon" ? "tool active" : "tool"}
                  onClick={() => {
                    setMode("polygon");
                    setDraft(null);
                  }}
                >
                  Polygon
                </button>
              </div>

              <label className="inline-control">
                Class
                <select
                  value={label}
                  onChange={(event) => setLabel(event.target.value)}
                >
                  {classes.map((item) => (
                    <option value={item} key={item}>
                      {item}
                    </option>
                  ))}
                </select>
              </label>

              <button
                type="button"
                className="secondary-button"
                disabled={!selectedImage || busy}
                onClick={handlePreannotate}
              >
                AI pre-annotate
              </button>

              <button
                type="button"
                className="primary-button"
                disabled={!draft || busy}
                onClick={handleSaveDraft}
              >
                Save annotation
              </button>

              <button
                type="button"
                className="ghost-button"
                disabled={!draft}
                onClick={() => setDraft(null)}
              >
                Clear draft
              </button>
            </div>
          )}

          <AnnotationCanvas
            image={selectedImage}
            annotations={annotations}
            draft={draft}
            setDraft={setDraft}
            mode={mode}
          />

          {selectedProject && (
            <div className="bottom-grid">
              <section className="panel stats-panel">
                <div className="panel-title-row">
                  <div>
                    <span className="eyebrow">Dataset status</span>
                    <h2>Project statistics</h2>
                  </div>
                  <span className="completion-badge">{completion}% annotated</span>
                </div>

                <div className="stat-grid">
                  <article>
                    <strong>{stats?.image_count ?? 0}</strong>
                    <span>Images</span>
                  </article>
                  <article>
                    <strong>{stats?.annotation_count ?? 0}</strong>
                    <span>Annotations</span>
                  </article>
                  <article>
                    <strong>{stats?.annotated_image_count ?? 0}</strong>
                    <span>Annotated images</span>
                  </article>
                </div>

                <div className="class-counts">
                  {Object.entries(stats?.class_counts || {}).map(([key, value]) => (
                    <span key={key}>
                      {key}: <strong>{value}</strong>
                    </span>
                  ))}
                </div>

                <div className="export-row">
                  <a
                    className="secondary-button link-button"
                    href={exportUrl(selectedProject.id, "coco")}
                  >
                    Export COCO
                  </a>
                  <a
                    className="secondary-button link-button"
                    href={exportUrl(selectedProject.id, "yolo")}
                  >
                    Export YOLO
                  </a>
                </div>
              </section>

              <section className="panel annotation-list-panel">
                <div>
                  <span className="eyebrow">Current image</span>
                  <h2>Annotations</h2>
                </div>

                <div className="annotation-list">
                  {annotations.map((annotation) => (
                    <article key={annotation.id} className="annotation-row">
                      <div>
                        <strong>{annotation.label}</strong>
                        <span>
                          {annotation.annotation_type} · {annotation.source}
                        </span>
                      </div>
                      <button
                        type="button"
                        className="delete-button"
                        onClick={() => handleDelete(annotation.id)}
                      >
                        Delete
                      </button>
                    </article>
                  ))}

                  {!annotations.length && (
                    <p className="muted">No saved annotations on this image.</p>
                  )}
                </div>
              </section>
            </div>
          )}
        </section>
      </main>

      {busy && <div className="busy-indicator">Working…</div>}
    </div>
  );
}
