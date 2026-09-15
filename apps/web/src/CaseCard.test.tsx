import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import {
  postApproveCasesCaseIdApprovePost,
  postRejectCasesCaseIdRejectPost,
} from './api/generated/cases/cases'
import { CaseCard } from './CaseCard'
import type { CaseListItem } from './api/generated/models/caseListItem'
import {
  CASE_APPROVED,
  CASE_OPEN,
  DRONE_IDLE,
  DRONE_ON_SITE,
} from './domain'

const openCase: CaseListItem = {
  id: 7,
  segment: 'A',
  status: CASE_OPEN,
  drone_status: DRONE_IDLE,
  rationale: null,
}

const fetchMock = vi.fn()

beforeEach(() => {
  fetchMock.mockResolvedValue({
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => ({
      id: 7,
      status: CASE_APPROVED,
      drone_status: DRONE_ON_SITE,
    }),
  })
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  fetchMock.mockReset()
  vi.unstubAllGlobals()
})

test('Send drone posts approve', async () => {
  const user = userEvent.setup()
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      busy={false}
      busyKind={null}
      onApprove={() => {
        void postApproveCasesCaseIdApprovePost(openCase.id)
      }}
      onReject={() => {
        void postRejectCasesCaseIdRejectPost(openCase.id)
      }}
    />
  )

  await user.click(screen.getByRole('button', { name: 'Send drone' }))

  expect(fetchMock).toHaveBeenCalledWith('/api/cases/7/approve', { method: 'POST' })
})

test('Dismiss posts reject', async () => {
  const user = userEvent.setup()
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      busy={false}
      busyKind={null}
      onApprove={() => {
        void postApproveCasesCaseIdApprovePost(openCase.id)
      }}
      onReject={() => {
        void postRejectCasesCaseIdRejectPost(openCase.id)
      }}
    />
  )

  await user.click(screen.getByRole('button', { name: 'Dismiss' }))

  expect(fetchMock).toHaveBeenCalledWith('/api/cases/7/reject', { method: 'POST' })
})
