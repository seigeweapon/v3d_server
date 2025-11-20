import client from './client'

export interface LoginResponse {
  access_token: string
  refresh_token: string
}

export async function login(email: string, password: string) {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  params.append('grant_type', 'password')

  const { data } = await client.post<LoginResponse>('/auth/login', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  })
  return data
}
