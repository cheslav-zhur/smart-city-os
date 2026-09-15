import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import {
  getCasesCasesGet,
  getGetCasesCasesGetQueryKey,
  useGetCasesCasesGet,
  usePostApproveCasesCaseIdApprovePost,
  usePostRejectCasesCaseIdRejectPost,
} from './api/generated/cases/cases'
import { useGetEventsEventsGet } from './api/generated/events/events'
import type { CaseDecisionOut } from './api/generated/models/caseDecisionOut'
import type { CaseListItem } from './api/generated/models/caseListItem'
import { CaseCard } from './CaseCard'
import { CaseList } from './CaseList'

const POLL_MS = 2000
const LAST_SPEED_COUNT = 8

function nextSelectedId(
  cases: CaseListItem[],
  current: number | null,
  pinned: boolean,
): number | null {
  if (pinned && current != null && cases.some((row) => row.id === current)) {
    return current
  }
  return cases.find((row) => row.status === 'open')?.id ?? current
}

function mergeDecision(
  cases: CaseListItem[],
  decision: CaseDecisionOut,
): CaseListItem[] {
  return cases.map((row) =>
    row.id === decision.id
      ? {
          ...row,
          status: decision.status,
          drone_status: decision.drone_status,
        }
      : row,
  )
}

export default function App() {
  const queryClient = useQueryClient()
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [decideError, setDecideError] = useState(false)
  const pinnedRef = useRef(false)

  const casesQuery = useGetCasesCasesGet({
    query: { refetchInterval: POLL_MS },
  })
  const eventsQuery = useGetEventsEventsGet({
    query: { refetchInterval: POLL_MS },
  })

  const cases = casesQuery.data?.data ?? []
  const speeds = (eventsQuery.data?.data ?? []).slice(0, LAST_SPEED_COUNT)
  const loadError = casesQuery.isError || eventsQuery.isError

  useEffect(() => {
    if (!casesQuery.isSuccess || !eventsQuery.isSuccess || casesQuery.data == null) {
      return
    }
    setDecideError(false)
    const nextCases = casesQuery.data.data
    setSelectedId((current) =>
      nextSelectedId(nextCases, current, pinnedRef.current),
    )
  }, [
    casesQuery.data,
    casesQuery.dataUpdatedAt,
    casesQuery.isSuccess,
    eventsQuery.dataUpdatedAt,
    eventsQuery.isSuccess,
  ])

  const approveMutation = usePostApproveCasesCaseIdApprovePost()
  const rejectMutation = usePostRejectCasesCaseIdRejectPost()
  const busy = approveMutation.isPending || rejectMutation.isPending

  function selectCase(id: number) {
    pinnedRef.current = true
    setSelectedId(id)
  }

  async function decide(kind: 'approve' | 'reject') {
    if (selectedId == null) {
      return
    }
    pinnedRef.current = true
    try {
      const result =
        kind === 'approve'
          ? await approveMutation.mutateAsync({ caseId: selectedId })
          : await rejectMutation.mutateAsync({ caseId: selectedId })
      if (result.status !== 200) {
        throw new Error(`decide ${result.status}`)
      }
      const decision = result.data
      setDecideError(false)
      queryClient.setQueryData(
        getGetCasesCasesGetQueryKey(),
        (current: Awaited<ReturnType<typeof getCasesCasesGet>> | undefined) => {
          if (current == null) {
            return current
          }
          return {
            ...current,
            data: mergeDecision(current.data, decision),
          }
        },
      )
      await queryClient.invalidateQueries({
        queryKey: getGetCasesCasesGetQueryKey(),
      })
    } catch {
      // Poll will refresh status; a repeat POST is 409 once decided.
      setDecideError(true)
    }
  }

  const selected = cases.find((row) => row.id === selectedId) ?? null

  return (
    <main className="desk">
      <header className="desk-header">
        <h1>Operations desk</h1>
        {loadError ? (
          <p className="error">Could not load cases or events.</p>
        ) : null}
        {decideError ? (
          <p className="error">Could not apply approve or reject.</p>
        ) : null}
      </header>
      <div className="desk-body">
        <aside className="list-pane">
          <h2>Cases</h2>
          <CaseList
            cases={cases}
            selectedId={selectedId}
            onSelect={selectCase}
          />
        </aside>
        <CaseCard
          caseRow={selected}
          speeds={speeds}
          busy={busy}
          onApprove={() => {
            void decide('approve')
          }}
          onReject={() => {
            void decide('reject')
          }}
        />
      </div>
    </main>
  )
}
