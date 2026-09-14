import { useEffect, useRef, useState } from 'react'
import { approveCase, fetchCases, fetchEvents, rejectCase } from './api'
import { CaseCard } from './CaseCard'
import { CaseList } from './CaseList'
import type { CaseDecision, CaseRow, EventRow } from './types'

const POLL_MS = 2000
const LAST_SPEED_COUNT = 8

function nextSelectedId(
  cases: CaseRow[],
  current: number | null,
  pinned: boolean,
): number | null {
  if (pinned && current != null && cases.some((row) => row.id === current)) {
    return current
  }
  return cases.find((row) => row.status === 'open')?.id ?? current
}

function mergeDecision(cases: CaseRow[], decision: CaseDecision): CaseRow[] {
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
  const [cases, setCases] = useState<CaseRow[]>([])
  const [speeds, setSpeeds] = useState<EventRow[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [busy, setBusy] = useState(false)
  const [loadError, setLoadError] = useState(false)
  const pinnedRef = useRef(false)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const [nextCases, nextEvents] = await Promise.all([
          fetchCases(),
          fetchEvents(),
        ])
        if (cancelled) {
          return
        }
        setLoadError(false)
        setCases(nextCases)
        setSpeeds(nextEvents.slice(0, LAST_SPEED_COUNT))
        setSelectedId((current) =>
          nextSelectedId(nextCases, current, pinnedRef.current),
        )
      } catch {
        if (!cancelled) {
          setLoadError(true)
        }
      }
    }

    void poll()
    const timer = window.setInterval(() => {
      void poll()
    }, POLL_MS)

    return () => {
      cancelled = true
      window.clearInterval(timer)
    }
  }, [])

  function selectCase(id: number) {
    pinnedRef.current = true
    setSelectedId(id)
  }

  async function decide(kind: 'approve' | 'reject') {
    if (selectedId == null) {
      return
    }
    pinnedRef.current = true
    setBusy(true)
    try {
      const decision =
        kind === 'approve'
          ? await approveCase(selectedId)
          : await rejectCase(selectedId)
      setCases((current) => mergeDecision(current, decision))
    } catch {
      // Poll will refresh status; a repeat POST is 409 once decided.
    } finally {
      setBusy(false)
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
