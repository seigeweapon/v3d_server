import client from './client'

export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export async function getCurrentUser() {
  const { data } = await client.get<User>('/users/me')
  return data
}

