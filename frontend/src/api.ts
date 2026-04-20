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

export interface FirmwareFiles {
  files: Record<string, string>
}

export type BuildStatus = 'pending' | 'running' | 'succeeded' | 'failed'

export interface Build {
  id: string
  project_id: string
  status: BuildStatus
  logs: string
  exit_code: number | null
  started_at: string | null
  finished_at: string | null
}

export const api = {
  health: () => request<{ status: string }>('/api/health'),
  listProjects: () => request<Project[]>('/api/projects'),
  createProject: (body: ProjectCreate) =>
    request<Project>('/api/projects', { method: 'POST', body: JSON.stringify(body) }),
  deleteProject: (id: string) =>
    request<void>(`/api/projects/${id}`, { method: 'DELETE' }),
  getFirmware: (projectId: string) =>
    request<FirmwareFiles>(`/api/projects/${projectId}/firmware`),
  putFirmware: (projectId: string, files: Record<string, string>) =>
    request<FirmwareFiles>(`/api/projects/${projectId}/firmware`, {
      method: 'PUT',
      body: JSON.stringify({ files }),
    }),
  startBuild: (projectId: string) =>
    request<Build>(`/api/projects/${projectId}/builds`, { method: 'POST' }),
  getBuild: (projectId: string, buildId: string) =>
    request<Build>(`/api/projects/${projectId}/builds/${buildId}`),
  listBuilds: (projectId: string) =>
    request<Build[]>(`/api/projects/${projectId}/builds`),
}
