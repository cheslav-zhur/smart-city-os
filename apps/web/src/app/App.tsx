import { useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef, useState } from 'react'
import {
  getCasesCasesGet,
  getGetCaseAuditCasesCaseIdAuditGetQueryKey,
  getGetCasesCasesGetQueryKey,
  useGetCaseAuditCasesCaseIdAuditGet,
  useGetCasesCasesGet,
  usePostApproveCasesCaseIdApprovePost,
  usePostRejectCasesCaseIdRejectPost,
} from '../api/generated/cases/cases'
import { useGetEventsEventsGet } from '../api/generated/events/events'
import type { CaseDecisionOut } from '../api/generated/models/caseDecisionOut'
import type { CaseListItem } from '../api/generated/models/caseListItem'
import {
  CASE_OPEN,
  CaseCard,
  CaseList,
  type DecideKind,
} from '../features/cases'
import { ThemeToggle } from '../shared/theme'
import { Panel } from '../shared/ui'

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
  return cases.find((row) => row.status === CASE_OPEN)?.id ?? current
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
  const auditQuery = useGetCaseAuditCasesCaseIdAuditGet(selectedId ?? 0, {
    query: {
      enabled: selectedId != null,
      refetchInterval: POLL_MS,
    },
  })

  const cases = casesQuery.data?.data ?? []
  const speeds = (eventsQuery.data?.data ?? []).slice(0, LAST_SPEED_COUNT)
  const auditResponse = auditQuery.data
  const audit =
    auditResponse?.status === 200 ? auditResponse.data : []
  const auditError = selectedId != null && auditQuery.isError
  const loadError = casesQuery.isError || eventsQuery.isError
  const initialLoading =
    (casesQuery.isLoading && casesQuery.data == null) ||
    (eventsQuery.isLoading && eventsQuery.data == null)
  const liveUpdating =
    !initialLoading &&
    !loadError &&
    !auditError &&
    (casesQuery.isFetching ||
      eventsQuery.isFetching ||
      (selectedId != null && auditQuery.isFetching))

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
  const busyKind: DecideKind | null = approveMutation.isPending
    ? 'approve'
    : rejectMutation.isPending
      ? 'reject'
      : null

  function selectCase(id: number) {
    pinnedRef.current = true
    setSelectedId(id)
  }

  async function decide(kind: DecideKind) {
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
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: getGetCasesCasesGetQueryKey(),
        }),
        queryClient.invalidateQueries({
          queryKey: getGetCaseAuditCasesCaseIdAuditGetQueryKey(selectedId),
        }),
      ])
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
          <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
            {!loadError ? (
              <p
                className="m-0 flex items-center gap-2 text-slate-500 dark:text-slate-400"
                aria-live="polite"
              >
                <span
                  className={`inline-block h-1.5 w-1.5 rounded-full ${
                    liveUpdating
                      ? 'animate-pulse bg-teal-500'
                      : 'bg-teal-600/70 dark:bg-teal-400/70'
                  }`}
                />
                {initialLoading
                  ? 'Loading…'
                  : liveUpdating
                    ? 'Updating…'
                    : 'Live'}
              </p>
            ) : null}
            {loadError ? (
              <p className="m-0 text-rose-700 dark:text-rose-300">
                Could not load cases or events.
              </p>
            ) : null}
            {auditError ? (
              <p className="m-0 text-rose-700 dark:text-rose-300">
                Could not load audit.
              </p>
            ) : null}
            {decideError ? (
              <p className="m-0 text-rose-700 dark:text-rose-300">
                Could not apply approve or reject.
              </p>
            ) : null}
          </div>
        </div>
        <ThemeToggle />
      </header>
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(17rem,22rem)_minmax(0,1fr)] lg:gap-8">
        <Panel as="aside" padding="md">
          <h2 className="mb-4 text-sm font-medium tracking-wide text-slate-500 uppercase dark:text-slate-400">
            Cases
          </h2>
          <CaseList
            cases={cases}
            selectedId={selectedId}
            onSelect={selectCase}
            loading={casesQuery.isLoading && casesQuery.data == null}
          />
        </Panel>
        <CaseCard
          caseRow={selected}
          speeds={speeds}
          audit={audit}
          busy={busy}
          busyKind={busyKind}
          casesLoading={casesQuery.isLoading && casesQuery.data == null}
          speedsLoading={eventsQuery.isLoading && eventsQuery.data == null}
          auditLoading={
            selectedId != null &&
            auditQuery.isLoading &&
            auditQuery.data == null &&
            !auditError
          }
          auditError={auditError}
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
