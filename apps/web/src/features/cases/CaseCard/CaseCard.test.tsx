import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import {
  postApproveCasesCaseIdApprovePost,
  postRejectCasesCaseIdRejectPost,
} from '../../../api/generated/cases/cases'
import type { CaseListItem } from '../../../api/generated/models/caseListItem'
import {
  CASE_APPROVED,
  CASE_OPEN,
  CASE_OUTDATED,
  DRONE_IDLE,
  DRONE_ON_SITE,
  EMPTY_OPINIONS_COPY,
} from '../domain'
import { CaseCard } from './CaseCard'

const openCase: CaseListItem = {
  id: 7,
  segment: 'A',
  status: CASE_OPEN,
  drone_status: DRONE_IDLE,
  dispatcher_opinion: null,
  critic_opinion: null,
  trigger_kind: 'crash_drop',
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
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => {
        void postApproveCasesCaseIdApprovePost(openCase.id)
      }}
      onReject={() => {
        void postRejectCasesCaseIdRejectPost(openCase.id)
      }}
    />,
  )

  await user.click(screen.getByRole('button', { name: 'Send drone' }))

  expect(fetchMock).toHaveBeenCalledWith('/api/cases/7/approve', {
    method: 'POST',
  })
})

test('Dismiss posts reject', async () => {
  const user = userEvent.setup()
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => {
        void postApproveCasesCaseIdApprovePost(openCase.id)
      }}
      onReject={() => {
        void postRejectCasesCaseIdRejectPost(openCase.id)
      }}
    />,
  )

  await user.click(screen.getByRole('button', { name: 'Dismiss' }))

  expect(fetchMock).toHaveBeenCalledWith('/api/cases/7/reject', {
    method: 'POST',
  })
})

test('null opinions show rule fallback and keep buttons enabled', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByText(EMPTY_OPINIONS_COPY)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Send drone' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Dismiss' })).toBeEnabled()
})

test('filled opinions render both voice labels', () => {
  render(
    <CaseCard
      caseRow={{
        ...openCase,
        dispatcher_opinion: 'Look once.',
        critic_opinion: 'Agree, low risk.',
      }}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByText('Dispatcher')).toBeInTheDocument()
  expect(screen.getByText('Look once.')).toBeInTheDocument()
  expect(screen.getByText('Critic')).toBeInTheDocument()
  expect(screen.getByText('Agree, low risk.')).toBeInTheDocument()
  expect(screen.queryByText(EMPTY_OPINIONS_COPY)).not.toBeInTheDocument()
})

test('empty audit shows ledger empty state', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByText('No audit rows yet')).toBeInTheDocument()
})

test('audit loading shows skeleton not empty copy', () => {
  const { container } = render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      auditLoading
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.queryByText('No audit rows yet')).not.toBeInTheDocument()
  expect(container.querySelector('[aria-hidden="true"]')).toBeTruthy()
})

test('populated audit renders actor action and why', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[
        {
          id: 1,
          actor: 'demo-operator',
          action: 'approve',
          why: 'approved send drone',
          created_at: new Date().toISOString(),
        },
      ]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByText('demo-operator · approve')).toBeInTheDocument()
  expect(screen.getByText('approved send drone')).toBeInTheDocument()
  expect(screen.queryByText('No audit rows yet')).not.toBeInTheDocument()
})

test('audit error does not show empty ledger copy', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      auditError
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByText('Could not load audit')).toBeInTheDocument()
  expect(screen.queryByText('No audit rows yet')).not.toBeInTheDocument()
})

test('card shows trigger kind string for an open case', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(
    screen.getByText('Case 7 · segment A · crash_drop'),
  ).toBeInTheDocument()
})

test('outdated case disables Send and Dismiss', () => {
  render(
    <CaseCard
      caseRow={{ ...openCase, status: CASE_OUTDATED }}
      speeds={[]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  expect(screen.getByRole('button', { name: 'Send drone' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Dismiss' })).toBeDisabled()
})

test('Last speeds table has no kind column', () => {
  render(
    <CaseCard
      caseRow={openCase}
      speeds={[
        {
          event_id: 'sim-010',
          segment: 'A',
          kind: 'crash_drop',
          speed: 40,
          recorded_at: new Date().toISOString(),
        },
      ]}
      audit={[]}
      busy={false}
      busyKind={null}
      onApprove={() => undefined}
      onReject={() => undefined}
    />,
  )

  const headers = screen
    .getAllByRole('columnheader')
    .map((header) => header.textContent)
  expect(headers).toEqual(['event', 'segment', 'speed', 'recorded'])
})
