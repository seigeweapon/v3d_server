import client from './client'

export interface User {
  id: number
  email: string
  full_name: string | null
  is_active: boolean
  is_superuser: boolean
  created_at: string
}

export interface UserCreate {
  email: string
  full_name?: string
  password: string
  is_superuser?: boolean
}

export interface UserUpdate {
  full_name?: string
  password?: string
  old_password?: string
  is_superuser?: boolean
}

export async function getCurrentUser() {
  const { data } = await client.get<User>('/users/me')
  return data
}

// 管理员专用的用户管理接口
export async function fetchUsers() {
  const { data } = await client.get<User[]>('/users/')
  return data
}

export async function createUser(user: UserCreate) {
  const { data } = await client.post<User>('/users/', user)
  return data
}

export async function getUser(id: number) {
  const { data } = await client.get<User>(`/users/${id}`)
  return data
}

export async function updateUser(id: number, updates: UserUpdate) {
  const { data } = await client.put<User>(`/users/${id}`, updates)
  return data
}

export async function deleteUser(id: number) {
  const { data } = await client.delete(`/users/${id}`)
  return data
}

