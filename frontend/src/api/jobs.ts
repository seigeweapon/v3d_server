import client from './client'

export interface Job {
  id: number
  video_id: number
  status: string
  parameters?: string
  tos_path?: string
  created_at: string
}

export async function fetchJobs() {
  const { data } = await client.get<Job[]>('/jobs/')
  return data
}

export async function createJob(video_id: number, parameters?: string) {
  const { data } = await client.post<Job>('/jobs/', { video_id, parameters })
  return data
}

export async function deleteJob(id: number) {
  const { data } = await client.delete(`/jobs/${id}`)
  return data
}
