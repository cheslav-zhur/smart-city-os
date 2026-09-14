import type { CaseDecision, CaseRow, EventRow } from './types'

async function readJson<T>(response: Response, label: string): Promise<T> {
  if (!response.ok) {
    throw new Error(`${label} ${response.status}`)
  }
  return (await response.json()) as T
}

export async function fetchCases(): Promise<CaseRow[]> {
  const response = await fetch('/api/cases')
  return readJson<CaseRow[]>(response, 'GET /api/cases')
}

export async function fetchEvents(): Promise<EventRow[]> {
  const response = await fetch('/api/events')
  return readJson<EventRow[]>(response, 'GET /api/events')
}

export async function approveCase(id: number): Promise<CaseDecision> {
  const response = await fetch(`/api/cases/${id}/approve`, { method: 'POST' })
  return readJson<CaseDecision>(response, `POST /api/cases/${id}/approve`)
}

export async function rejectCase(id: number): Promise<CaseDecision> {
  const response = await fetch(`/api/cases/${id}/reject`, { method: 'POST' })
  return readJson<CaseDecision>(response, `POST /api/cases/${id}/reject`)
}
