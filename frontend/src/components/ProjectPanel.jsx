import React, { useState } from "react";

export default function ProjectPanel({
  projects,
  selectedProject,
  onSelect,
  onCreate
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [classes, setClasses] = useState("lesion,tumour,organ");

  async function submit(event) {
    event.preventDefault();

    const parsed = classes
      .split(",")
      .map((item) => item.trim())
      .filter(Boolean);

    if (!name.trim() || !parsed.length) return;

    await onCreate({
      name: name.trim(),
      description: description.trim(),
      classes: parsed
    });

    setName("");
    setDescription("");
  }

  return (
    <aside className="panel project-panel">
      <div>
        <span className="eyebrow">Workspace</span>
        <h2>Projects</h2>
      </div>

      <div className="project-list">
        {projects.map((project) => (
          <button
            type="button"
            key={project.id}
            className={`project-card ${
              selectedProject?.id === project.id ? "active" : ""
            }`}
            onClick={() => onSelect(project)}
          >
            <strong>{project.name}</strong>
            <span>{project.classes.join(" · ")}</span>
          </button>
        ))}

        {!projects.length && (
          <p className="muted">Create your first annotation project.</p>
        )}
      </div>

      <form onSubmit={submit} className="stack create-project">
        <h3>New project</h3>

        <label>
          Name
          <input
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="Breast Ultrasound Lesions"
          />
        </label>

        <label>
          Classes
          <input
            value={classes}
            onChange={(event) => setClasses(event.target.value)}
            placeholder="lesion,tumour,organ"
          />
        </label>

        <label>
          Description
          <textarea
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Research dataset annotation project"
          />
        </label>

        <button className="primary-button" type="submit">
          Create project
        </button>
      </form>
    </aside>
  );
}
