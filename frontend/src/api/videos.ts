import client from './client'

export interface Video {
  id: number
  owner_id: number
  studio: string
  producer: string
  production: string
  action: string
  camera_count: number
  prime_camera_number: number
  background_id: number
  calibration_id: number
  frame_count: number
  frame_rate: number
  frame_width: number
  frame_height: number
  video_format: string
  tos_path: string
  created_at: string
}

export async function fetchVideos() {
  const { data } = await client.get<Video[]>('/videos/')
  return data
}

export async function createVideo(video: Omit<Video, 'id' | 'owner_id' | 'created_at'>) {
  const { data } = await client.post<Video>('/videos/', video)
  return data
}

export async function getVideo(id: number) {
  const { data } = await client.get<Video>(`/videos/${id}`)
  return data
}

export async function deleteVideo(id: number) {
  const { data } = await client.delete(`/videos/${id}`)
  return data
}
