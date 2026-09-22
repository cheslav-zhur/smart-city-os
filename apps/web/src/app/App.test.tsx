import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import type { CaseListItem } from '../api/generated/models/caseListItem'
import {
  CASE_LIST_WINDOW,
  CASE_OPEN,
  CASE_OUTDATED,
  DRONE_IDLE,
} from '../features/cases'
import App from './App'

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

function jsonResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    headers: new Headers({ 'content-type': 'application/json' }),
    json: async () => data,
  }
}

const fetchMock = vi.fn()

function renderDesk() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  )
  return queryClient
}

function mockDesk(cases: CaseListItem[]) {
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url === '/api/cases') {
      return jsonResponse(cases)
    }
    if (url === '/api/events') {
      return jsonResponse([])
    }
    if (/\/api\/cases\/\d+\/audit$/.test(url)) {
      return jsonResponse([])
    }
    throw new Error(`unexpected fetch ${url}`)
  })
}

function caseList() {
  const heading = screen.getByRole('heading', { name: 'Cases' })
  const panel = heading.closest('aside')
  if (panel == null) {
    throw new Error('cases panel missing')
  }
  return panel
}

function listedCaseIds() {
  return within(caseList())
    .getAllByRole('button')
    .map((button) => button.textContent ?? '')
    .map((text) => /Case (\d+)/.exec(text)?.[1])
    .filter((id): id is string => id != null)
}

function caseRowButton(id: number) {
  return within(caseList()).getByRole('button', {
    name: new RegExp(
      `^Case ${id}(open|outdated|approved|rejected)\\b`,
    ),
  })
}

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
})

test('first open row is auto-selected until the operator clicks another', async () => {
  mockDesk([row(1, CASE_OPEN)])
  renderDesk()

  await waitFor(() => {
    expect(screen.getByText(/Case 1 · segment A/)).toBeInTheDocument()
  })
  expect(screen.getByRole('button', { name: 'Send drone' })).toBeEnabled()
})

test('new open does not steal the card; outdated disables Send and Dismiss', async () => {
  mockDesk([row(1, CASE_OPEN)])
  const queryClient = renderDesk()

  await waitFor(() => {
    expect(screen.getByText(/Case 1 · segment A/)).toBeInTheDocument()
  })

  mockDesk([row(2, CASE_OPEN, 'jam'), row(1, CASE_OUTDATED)])
  await queryClient.invalidateQueries()

  await waitFor(() => {
    expect(listedCaseIds()[0]).toBe('2')
  })
  expect(screen.getByText(/Case 1 · segment A/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Send drone' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Dismiss' })).toBeDisabled()
})

test('clicking a newer open case selects it and enables buttons', async () => {
  const user = userEvent.setup()
  mockDesk([row(1, CASE_OPEN)])
  const queryClient = renderDesk()

  await waitFor(() => {
    expect(screen.getByText(/Case 1 · segment A/)).toBeInTheDocument()
  })

  mockDesk([row(2, CASE_OPEN, 'jam'), row(1, CASE_OUTDATED)])
  await queryClient.invalidateQueries()
  await waitFor(() => {
    expect(listedCaseIds()[0]).toBe('2')
    expect(screen.getByRole('button', { name: 'Send drone' })).toBeDisabled()
  })

  await user.click(caseRowButton(2))
  await waitFor(() => {
    expect(screen.getByText(/Case 2 · segment A/)).toBeInTheDocument()
  })
  expect(screen.getByRole('button', { name: 'Send drone' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Dismiss' })).toBeEnabled()
})

test('decide 409 invalidates cases so Send disables on outdated', async () => {
  const user = userEvent.setup()
  let cases: CaseListItem[] = [row(1, CASE_OPEN)]
  fetchMock.mockImplementation(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url === '/api/cases/1/approve') {
      cases = [row(1, CASE_OUTDATED)]
      return {
        ok: false,
        status: 409,
        headers: new Headers({ 'content-type': 'application/json' }),
        json: async () => ({ detail: 'case already decided' }),
      }
    }
    if (url === '/api/cases') {
      return jsonResponse(cases)
    }
    if (url === '/api/events') {
      return jsonResponse([])
    }
    if (/\/api\/cases\/\d+\/audit$/.test(url)) {
      return jsonResponse([])
    }
    throw new Error(`unexpected fetch ${url}`)
  })
  renderDesk()

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Send drone' })).toBeEnabled()
  })

  await user.click(screen.getByRole('button', { name: 'Send drone' }))

  await waitFor(() => {
    expect(screen.getByRole('button', { name: 'Send drone' })).toBeDisabled()
  })
  expect(screen.getByRole('button', { name: 'Dismiss' })).toBeDisabled()
})

test('list keeps an aged-off selected row outside the newest ten', async () => {
  const store = Array.from({ length: 11 }, (_, index) => {
    const id = 11 - index
    return row(id, id === 1 ? CASE_OPEN : CASE_OUTDATED, 'speeding')
  })
  mockDesk(store)
  renderDesk()

  await waitFor(() => {
    expect(screen.getByText(/Case 1 · segment A/)).toBeInTheDocument()
  })
  expect(listedCaseIds()).toEqual([
    '11', '10', '9', '8', '7', '6', '5', '4', '3', '2', '1',
  ])
  expect(listedCaseIds()).toHaveLength(CASE_LIST_WINDOW + 1)
})
