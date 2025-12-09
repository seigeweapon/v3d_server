import client from './client'

export interface Background {
  id: number
  owner_id: number
  camera_count: number
  tos_path: string
  notes?: string
  status: string
  created_at: string
  // 仅在创建时返回的预签名上传 URL（PUT 方式，已废弃）
  upload_url?: string
  // 仅在创建时返回的 PostObject 表单数据（用于浏览器表单上传，可绕过 CORS）
  // 如果上传多个文件，这是一个列表，每个元素对应一个文件的表单数据
  post_form_data_list?: Array<{
    action: string
    fields: {
      key: string
      policy: string
      'x-tos-algorithm': string
      'x-tos-credential': string
      'x-tos-date': string
      'x-tos-signature': string
    }
  }>
}

export async function fetchBackgrounds() {
  const { data } = await client.get<Background[]>('/backgrounds/')
  return data
}

export async function createBackground(
  background: Pick<Background, 'camera_count' | 'notes'> & { 
    file_infos?: Array<{ name: string; type: string }> 
  }
) {
  const { data } = await client.post<Background>('/backgrounds/', background)
  return data
}

export async function getBackground(id: number) {
  const { data } = await client.get<Background>(`/backgrounds/${id}`)
  return data
}

export async function deleteBackground(id: number) {
  const { data } = await client.delete(`/backgrounds/${id}`)
  return data
}

export async function markBackgroundReady(id: number) {
  const { data } = await client.post<Background>(`/backgrounds/${id}/ready`)
  return data
}
