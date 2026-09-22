import { describe, expect, test } from 'vitest'
import type { CaseListItem } from '../../api/generated/models/caseListItem'
import { CASE_LIST_WINDOW, nextSelectedId, visibleCases } from './caseWindow'
import {
  CASE_OPEN,
  CASE_OUTDATED,
  CASE_REJECTED,
  DRONE_IDLE,
} from './domain'

function row(
  id: number,
  status: string,
  triggerKind = 'crash_drop',
): CaseListItem {
  return {
    id,
    segment: 'A',
    status,
    drone_status: DRONE_IDLE,
    dispatcher_opinion: null,
    critic_opinion: null,
    trigger_kind: triggerKind,
  }
}

describe('nextSelectedId', () => {
  test('unselected refresh picks an open row for the first selection only', () => {
    const firstOpen = row(1, CASE_OPEN)
    expect(nextSelectedId([firstOpen], null)).toBe(1)

    const afterDisplace = [
      row(2, CASE_OPEN, 'jam'),
      { ...firstOpen, status: CASE_OUTDATED },
    ]
    expect(nextSelectedId(afterDisplace, 1)).toBe(1)
  })

  test('keeps the selected case when a newer open appears', () => {
    const cases = [row(2, CASE_OPEN, 'jam'), row(1, CASE_OUTDATED)]
    expect(nextSelectedId(cases, 1)).toBe(1)
  })

  test('clicking another id is kept on the next refresh', () => {
    const cases = [row(2, CASE_OPEN, 'jam'), row(1, CASE_OUTDATED)]
    expect(nextSelectedId(cases, 2)).toBe(2)
  })

  test('does not follow a new open after the first auto-select', () => {
    const first = nextSelectedId([row(1, CASE_OPEN)], null)
    expect(first).toBe(1)
    expect(
      nextSelectedId([row(2, CASE_OPEN, 'speeding'), row(1, CASE_OPEN)], first),
    ).toBe(1)
  })
})

describe('visibleCases', () => {
  test('newer open is first in the window while selected stays listed', () => {
    const cases = [row(2, CASE_OPEN, 'jam'), row(1, CASE_OUTDATED)]
    const window = visibleCases(cases, 1)
    expect(window.map((item) => item.id)).toEqual([2, 1])
  })

  test('eleven stored cases show ten newest plus selected if it aged off', () => {
    const cases = Array.from({ length: 11 }, (_, index) =>
      row(11 - index, CASE_REJECTED),
    )
    const window = visibleCases(cases, 1)
    expect(window).toHaveLength(CASE_LIST_WINDOW + 1)
    expect(window.map((item) => item.id)).toEqual([
      11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1,
    ])
    expect(window.some((item) => item.id === 1)).toBe(true)
  })

  test('selected inside the newest ten is not duplicated', () => {
    const cases = Array.from({ length: 11 }, (_, index) =>
      row(11 - index, CASE_REJECTED),
    )
    const window = visibleCases(cases, 8)
    expect(window).toHaveLength(CASE_LIST_WINDOW)
    expect(window.filter((item) => item.id === 8)).toHaveLength(1)
    expect(window.map((item) => item.id)).toEqual([
      11, 10, 9, 8, 7, 6, 5, 4, 3, 2,
    ])
  })
})
