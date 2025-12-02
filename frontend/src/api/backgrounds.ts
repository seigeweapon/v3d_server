import client from './client'

export interface Background {
  id: number
  owner_id: number
  camera_count: number
  tos_path: string
  notes?: string
  created_at: string
}

export async function fetchBackgrounds() {
  const { data } = await client.get<Background[]>('/backgrounds/')
  return data
}

export async function createBackground(background: Omit<Background, 'id' | 'owner_id' | 'created_at'>) {
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

