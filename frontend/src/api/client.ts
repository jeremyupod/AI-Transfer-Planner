import { formatApiError } from './errors'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

export type HealthResponse = {
  status: string
}

export type Institution = {
  id: number
  name: string
  institution_type: string
}

export type Major = {
  id: number
  name: string
  institution_id: number
}

export type StudentProfile = {
  id: number
  current_college: Institution
  anticipated_transfer_term: string
  created_at: string
  targets: Array<{
    target_campus: Institution
    intended_major: Major
  }>
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })

  if (!response.ok) {
    const detail = await response.json().catch(() => null)
    throw new Error(formatApiError(detail, response.status))
  }

  return response.json() as Promise<T>
}

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>('/health')
}

export function getInstitutions(): Promise<Institution[]> {
  return request<Institution[]>('/api/v1/institutions')
}

export function getCampuses(): Promise<Institution[]> {
  return request<Institution[]>('/api/v1/campuses')
}

export function getMajors(institutionId: number, signal?: AbortSignal): Promise<Major[]> {
  return request<Major[]>(`/api/v1/majors?institution_id=${institutionId}`, { signal })
}

export function createStudentProfile(input: {
  current_college_id: number
  anticipated_transfer_term: string
  targets: Array<{ target_campus_id: number; intended_major_id: number }>
}): Promise<StudentProfile> {
  return request<StudentProfile>('/api/v1/student-profiles', {
    method: 'POST',
    body: JSON.stringify(input),
  })
}
