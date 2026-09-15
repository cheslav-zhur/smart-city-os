import type { CaseListItem } from './api/generated/models/caseListItem'

type CaseListProps = {
  cases: CaseListItem[]
  selectedId: number | null
  onSelect: (id: number) => void
}

function statusTone(status: string): string {
  if (status === 'open') {
    return 'text-teal-700 dark:text-teal-300'
  }
  if (status === 'approved') {
    return 'text-slate-600 dark:text-slate-300'
  }
  return 'text-slate-500 dark:text-slate-400'
}

export function CaseList({ cases, selectedId, onSelect }: CaseListProps) {
  if (cases.length === 0) {
    return (
      <p className="m-0 text-sm leading-relaxed text-slate-500 dark:text-slate-400">
        No cases yet. Run the simulator.
      </p>
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
              className={`w-full cursor-pointer rounded-xl px-3.5 py-3 text-left transition ${
                selected
                  ? 'bg-teal-500/10 dark:bg-teal-400/10'
                  : 'hover:bg-slate-900/[0.04] dark:hover:bg-white/[0.04]'
              }`}
              onClick={() => onSelect(row.id)}
            >
              <div className="flex items-baseline justify-between gap-3">
                <span className="text-sm font-medium text-slate-900 dark:text-slate-50">
                  Case {row.id}
                </span>
                <span
                  className={`text-xs font-medium tracking-wide ${statusTone(row.status)}`}
                >
                  {row.status}
                </span>
              </div>
              <div className="mt-1 flex gap-3 text-xs text-slate-500 dark:text-slate-400">
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
