/** Case lifecycle on the console card/list. Matches API CASE_* constants. */
export type CaseStatus = 'open' | 'approved' | 'rejected' | 'outdated'

/** Drone stub status. Matches API DRONE_* constants. */
export type DroneStatus = 'idle' | 'in_flight' | 'on_site'

export const CASE_OPEN: CaseStatus = 'open'
export const CASE_APPROVED: CaseStatus = 'approved'
export const CASE_REJECTED: CaseStatus = 'rejected'
export const CASE_OUTDATED: CaseStatus = 'outdated'

export const DRONE_IDLE: DroneStatus = 'idle'
export const DRONE_IN_FLIGHT: DroneStatus = 'in_flight'
export const DRONE_ON_SITE: DroneStatus = 'on_site'

/** Card copy when both opinion columns are null (rule-only case). */
export const EMPTY_OPINIONS_COPY =
  'Rule opened the case. No model proposal.'

export function isCaseStatus(value: string): value is CaseStatus {
  return (
    value === CASE_OPEN ||
    value === CASE_APPROVED ||
    value === CASE_REJECTED ||
    value === CASE_OUTDATED
  )
}

export function isDroneStatus(value: string): value is DroneStatus {
  return (
    value === DRONE_IDLE ||
    value === DRONE_IN_FLIGHT ||
    value === DRONE_ON_SITE
  )
}

export function formatDroneStatus(status: string): string {
  return status.replaceAll('_', ' ')
}
