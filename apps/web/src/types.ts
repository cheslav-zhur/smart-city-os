export type CaseRow = {
  id: number
  segment: string
  status: string
  drone_status: string
  rationale: string | null
}

export type EventRow = {
  event_id: string
  segment: string
  speed: number
  recorded_at: string
}

export type CaseDecision = {
  id: number
  status: string
  drone_status: string
}
