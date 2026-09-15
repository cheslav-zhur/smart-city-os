import { describe, expect, test } from 'vitest'
import { formatRelativeTime, isCollapseSpeed } from './time'

describe('formatRelativeTime', () => {
  test('formats recent seconds', () => {
    const now = Date.parse('2026-09-15T04:00:30.000Z')
    expect(
      formatRelativeTime('2026-09-15T04:00:10.000Z', now),
    ).toBe('20s ago')
  })

  test('falls back for invalid input', () => {
    expect(formatRelativeTime('not-a-date')).toBe('not-a-date')
  })
})

describe('isCollapseSpeed', () => {
  test('marks near-zero as collapse', () => {
    expect(isCollapseSpeed(0)).toBe(true)
    expect(isCollapseSpeed(0.5)).toBe(true)
    expect(isCollapseSpeed(0.51)).toBe(false)
  })
})
