import type { CaseListItem } from './api/generated/models/caseListItem'
import { StatusChip } from './StatusChip'

type CaseListProps = {
  cases: CaseListItem[]
  selectedId: number | null
  onSelect: (id: number) => void
  loading?: boolean
}

function CaseListSkeleton() {
  return (
    <ul className="m-0 flex list-none flex-col gap-2 p-0" aria-hidden="true">
      {[0, 1, 2].map((key) => (
        <li
          key={key}
          className="h-14 animate-pulse rounded-xl bg-slate-900/5 dark:bg-white/5"
        />
      ))}
    </ul>
  )
}

export function CaseList({
  cases,
  selectedId,
  onSelect,
  loading = false,
}: CaseListProps) {
  if (loading) {
    return <CaseListSkeleton />
  }

  if (cases.length === 0) {
    return (
      <div className="text-sm leading-relaxed text-slate-500 dark:text-slate-400">
        <p className="m-0 font-medium text-slate-700 dark:text-slate-200">
          No cases yet
        </p>
        <p className="mt-1.5 mb-0">
          Run <code className="font-mono text-[0.8rem]">make sim</code> to send
          the speed tape and open a collapse case.
        </p>
      </div>
    )
  }

  return (
    <ul className="m-0 flex list-none flex-col gap-1 p-0">
      {cases.map((row) => {
        const selected = row.id === selectedId
        return (
          <li key={row.id}>
            <button
              type="button"
              className={`w-full cursor-pointer rounded-xl px-3.5 py-3 text-left transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/50 ${
                selected
                  ? 'bg-teal-500/10 dark:bg-teal-400/10'
                  : 'hover:bg-slate-900/[0.04] dark:hover:bg-white/[0.04]'
              }`}
              onClick={() => onSelect(row.id)}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                  Case {row.id}
                </span>
                <StatusChip status={row.status} size="sm" />
              </div>
              <div className="mt-1.5 flex gap-3 text-xs text-slate-500 dark:text-slate-400">
                <span>segment {row.segment}</span>
                <span>{row.drone_status.replaceAll('_', ' ')}</span>
              </div>
            </button>
          </li>
        )
      })}
    </ul>
  )
}
