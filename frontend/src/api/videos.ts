import client from './client'

export interface Video {
  id: number
  filename: string
  description?: string
  storage_path: string
  created_at: string
}

export async function fetchVideos() {
  const { data } = await client.get<Video[]>('/videos/')
  return data
}

export async function uploadVideo(file: File, description?: string) {
  const formData = new FormData()
  formData.append('file', file)
  if (description) {
    formData.append('description', description)
  }
  const { data } = await client.post<Video>('/videos/upload', formData)
  return data
}
