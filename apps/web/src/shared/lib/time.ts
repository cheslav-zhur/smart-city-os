/** Collapse threshold aligned with API cases.service COLLAPSE_MAX. */
export const COLLAPSE_MAX = 0.5

export function isCollapseSpeed(speed: number): boolean {
  return speed <= COLLAPSE_MAX
}

export function formatRelativeTime(
  iso: string,
  nowMs: number = Date.now(),
): string {
  const then = Date.parse(iso)
  if (Number.isNaN(then)) {
    return iso
  }
  const deltaSec = Math.round((nowMs - then) / 1000)
  if (deltaSec < 5) {
    return 'just now'
  }
  if (deltaSec < 60) {
    return `${deltaSec}s ago`
  }
  const deltaMin = Math.round(deltaSec / 60)
  if (deltaMin < 60) {
    return `${deltaMin}m ago`
  }
  const deltaHr = Math.round(deltaMin / 60)
  if (deltaHr < 48) {
    return `${deltaHr}h ago`
  }
  return new Date(then).toLocaleString()
}
