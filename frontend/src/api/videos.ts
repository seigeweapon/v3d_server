import client from './client'

export interface Video {
  id: number
  owner_id: number
  owner_full_name?: string
  studio: string
  producer: string
  production: string
  action: string
  camera_count: number
  prime_camera_number: number
  frame_count: number
  frame_rate: number
  frame_width: number
  frame_height: number
  video_format: string
  tos_path: string
  status: string
  is_public: boolean
  visible_to_user_ids?: string | null
  created_at: string
  // 仅在创建时返回的 PostObject 表单数据
  post_form_data_list?: Array<{
    action: string
    fields: {
      key: string
      policy: string
      'x-tos-algorithm': string
      'x-tos-credential': string
      'x-tos-date': string
      'x-tos-signature': string
      'Content-Type'?: string
    }
  }>
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

export async function uploadVideo(
  video: {
    studio: string
    producer: string
    production: string
    action: string
    camera_count?: number
    prime_camera_number?: number
    frame_count?: number
    frame_rate?: number
    frame_width?: number
    frame_height?: number
    video_format?: string
    file_infos?: Array<{ name: string; type: string }>
  }
) {
  const { data } = await client.post<Video>('/videos/upload', video)
  return data
}

export async function markVideoReady(id: number) {
  const { data } = await client.post<Video>(`/videos/${id}/ready`)
  return data
}

export async function markVideoFailed(id: number) {
  const { data } = await client.post<Video>(`/videos/${id}/failed`)
  return data
}

export async function updateVideo(
  id: number,
  updates: {
    studio?: string
    producer?: string
    production?: string
    action?: string
  }
) {
  const { data } = await client.patch<Video>(`/videos/${id}`, updates)
  return data
}

export interface VideoMetadata {
  duration: number
  width: number
  height: number
  frame_rate: number
  frame_count: number
  format: string
}

export async function extractVideoMetadata(file: File): Promise<VideoMetadata> {
  const formData = new FormData()
  formData.append('file', file)
  // 不要手动设置 Content-Type，让 axios 自动设置正确的 multipart/form-data header（包含 boundary）
  const { data } = await client.post<VideoMetadata>('/videos/extract-metadata', formData)
  return data
}

export async function downloadVideoZip(
  id: number,
  fileTypes: string[]
): Promise<{ blob: Blob; filename: string }> {
  const response = await client.post(`/videos/${id}/download-zip`, {
    file_types: fileTypes,
  }, {
    responseType: 'blob',
  })

  // 从 Content-Disposition 提取文件名
  let filename = 'v3d_data.zip'
  const disposition = response.headers['content-disposition']
  if (disposition) {
    const match = /filename="?([^\";]+)"?/.exec(disposition)
    if (match && match[1]) {
      filename = match[1]
    }
  }

  return { blob: response.data, filename }
}

export interface VideoVisibilityUpdate {
  is_public?: boolean
  visible_to_user_ids?: number[]
}

export async function updateVideoVisibility(id: number, updates: VideoVisibilityUpdate) {
  const { data } = await client.patch<Video>(`/videos/${id}/visibility`, updates)
  return data
}
