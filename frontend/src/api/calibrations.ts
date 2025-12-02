import client from './client'

export interface Calibration {
  id: number
  owner_id: number
  camera_count: number
  tos_path: string
  notes?: string
  created_at: string
}

export async function fetchCalibrations() {
  const { data } = await client.get<Calibration[]>('/calibrations/')
  return data
}

export async function createCalibration(calibration: Omit<Calibration, 'id' | 'owner_id' | 'created_at'>) {
  const { data } = await client.post<Calibration>('/calibrations/', calibration)
  return data
}

export async function getCalibration(id: number) {
  const { data } = await client.get<Calibration>(`/calibrations/${id}`)
  return data
}

export async function deleteCalibration(id: number) {
  const { data } = await client.delete(`/calibrations/${id}`)
  return data
}

