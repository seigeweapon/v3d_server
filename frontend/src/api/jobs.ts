import client from './client'

export interface Job {
  id: number
  video_id: number
  status: string
  parameters?: string
  result_path?: string
  created_at: string
  updated_at: string
}

export async function fetchJobs() {
  const { data } = await client.get<Job[]>('/jobs/')
  return data
}

export async function createJob(video_id: number, parameters?: string) {
  const { data } = await client.post<Job>('/jobs/', { video_id, parameters })
  return data
}
