import client from './client'

export interface Job {
  id: number
  video_id: number
  owner_id: number
  owner_full_name?: string
  status: string
  run_id?: string | null
  parameters?: string
  tos_path?: string
  notes?: string
  is_public: boolean
  visible_to_user_ids?: string | null
  created_at: string
}

export interface JobVisibilityUpdate {
  is_public?: boolean
  visible_to_user_ids?: number[]
}

export async function fetchJobs() {
  const { data } = await client.get<Job[]>('/jobs/')
  return data
}

export async function createJob(video_id: number, parameters?: string, notes?: string) {
  const { data } = await client.post<Job>('/jobs/', { video_id, parameters, notes })
  return data
}

export async function updateJobNotes(id: number, notes: string) {
  const { data } = await client.patch<Job>(`/jobs/${id}`, { notes })
  return data
}

export async function deleteJob(id: number) {
  const { data } = await client.delete(`/jobs/${id}`)
  return data
}

export async function updateJobVisibility(id: number, updates: JobVisibilityUpdate) {
  const { data } = await client.patch<Job>(`/jobs/${id}/visibility`, updates)
  return data
}

export async function terminateJob(id: number) {
  const { data } = await client.post<Job>(`/jobs/${id}/terminate`, {})
  return data
}

export async function syncJobStatus(id: number) {
  const { data } = await client.post<Job>(`/jobs/${id}/sync-status`, {})
  return data
}
