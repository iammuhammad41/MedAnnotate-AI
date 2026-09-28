export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, options);

  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      // Keep default message.
    }
    throw new Error(detail);
  }

  return response;
}

export async function listProjects() {
  return (await request("/api/projects")).json();
}

export async function createProject(payload) {
  return (
    await request("/api/projects", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
  ).json();
}

export async function listImages(projectId) {
  return (await request(`/api/projects/${projectId}/images`)).json();
}

export async function uploadImage(projectId, file) {
  const body = new FormData();
  body.append("image", file);

  return (
    await request(`/api/projects/${projectId}/images`, {
      method: "POST",
      body
    })
  ).json();
}

export function imageUrl(imageId) {
  return `${API_URL}/api/images/${imageId}/file`;
}

export async function listAnnotations(imageId) {
  return (await request(`/api/images/${imageId}/annotations`)).json();
}

export async function createAnnotation(imageId, payload) {
  return (
    await request(`/api/images/${imageId}/annotations`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
  ).json();
}

export async function deleteAnnotation(annotationId) {
  return (
    await request(`/api/annotations/${annotationId}`, {
      method: "DELETE"
    })
  ).json();
}

export async function preannotate(imageId, label) {
  const body = new FormData();
  body.append("label", label);

  return (
    await request(`/api/images/${imageId}/preannotate`, {
      method: "POST",
      body
    })
  ).json();
}

export async function getStats(projectId) {
  return (await request(`/api/projects/${projectId}/stats`)).json();
}

export function exportUrl(projectId, format) {
  return `${API_URL}/api/projects/${projectId}/export/${format}`;
}
