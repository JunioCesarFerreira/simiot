export interface Project {
  id: string
  name: string
  description: string
}

export interface ProjectCreate {
  name: string
  description?: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (body: ProjectCreate) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(body) }),
  deleteProject: (id: string) =>
    request<void>(`/api/projects/${id}`, { method: 'DELETE' }),
}
