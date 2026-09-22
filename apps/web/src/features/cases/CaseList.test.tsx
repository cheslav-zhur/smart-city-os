import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import type { CaseListItem } from '../../api/generated/models/caseListItem'
import { CaseList } from './CaseList'
import { CASE_OPEN, DRONE_IDLE } from './domain'

const openCase: CaseListItem = {
  id: 3,
  segment: 'A',
  status: CASE_OPEN,
  drone_status: DRONE_IDLE,
  dispatcher_opinion: null,
  critic_opinion: null,
  trigger_kind: 'speeding',
}

test('list row shows trigger kind string', () => {
  render(
    <CaseList
      cases={[openCase]}
      selectedId={openCase.id}
      onSelect={() => undefined}
    />,
  )

  expect(screen.getByText('speeding')).toBeInTheDocument()
  expect(screen.getByText('Case 3')).toBeInTheDocument()
})
