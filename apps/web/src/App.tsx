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
import { ThemeToggle } from './ThemeToggle'

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
    <main className="min-h-screen px-6 py-8 text-slate-800 md:px-10 dark:text-slate-100">
      <header className="mb-8 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-xl">
          <p className="mb-1 text-xs font-medium tracking-[0.14em] text-slate-500 uppercase dark:text-slate-400">
            Smart City OS
          </p>
          <h1 className="m-0 text-3xl font-semibold tracking-tight text-slate-900 dark:text-white">
            Operations desk
          </h1>
          {loadError ? (
            <p className="mt-3 mb-0 text-sm text-rose-700 dark:text-rose-300">
              Could not load cases or events.
            </p>
          ) : null}
          {decideError ? (
            <p className="mt-3 mb-0 text-sm text-rose-700 dark:text-rose-300">
              Could not apply approve or reject.
            </p>
          ) : null}
        </div>
        <ThemeToggle />
      </header>
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(17rem,22rem)_minmax(0,1fr)] lg:gap-8">
        <aside className="rounded-2xl bg-white/80 p-5 shadow-[0_1px_0_rgba(15,23,42,0.04)] dark:bg-white/[0.03] dark:shadow-none dark:ring-1 dark:ring-white/[0.06]">
          <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
            Cases
          </h2>
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
