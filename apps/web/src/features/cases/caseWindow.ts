import type { CaseListItem } from '../../api/generated/models/caseListItem'
import { CASE_OPEN } from './domain'

/** Newest rows shown in the case list. Tune after the first live shift. */
export const CASE_LIST_WINDOW = 10

/**
 * Keep the current card once chosen, including the first auto-select of an
 * open row. A later open must not steal the selection.
 */
export function nextSelectedId(
  cases: CaseListItem[],
  current: number | null,
): number | null {
  if (current != null && cases.some((row) => row.id === current)) {
    return current
  }
  return cases.find((row) => row.status === CASE_OPEN)?.id ?? current
}

/**
 * Console window only: newest N by id, plus the selected row if it aged off.
 * Does not slice the API store.
 */
export function visibleCases(
  cases: CaseListItem[],
  selectedId: number | null,
): CaseListItem[] {
  const newest = [...cases]
    .sort((left, right) => right.id - left.id)
    .slice(0, CASE_LIST_WINDOW)
  if (selectedId == null || newest.some((row) => row.id === selectedId)) {
    return newest
  }
  const selected = cases.find((row) => row.id === selectedId)
  if (selected == null) {
    return newest
  }
  return [...newest, selected].sort((left, right) => right.id - left.id)
}
