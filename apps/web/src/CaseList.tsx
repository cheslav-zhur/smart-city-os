import type { CaseRow } from './types'

type CaseListProps = {
  cases: CaseRow[]
  selectedId: number | null
  onSelect: (id: number) => void
}

export function CaseList({ cases, selectedId, onSelect }: CaseListProps) {
  if (cases.length === 0) {
    return <p className="empty">No cases yet. Run the simulator.</p>
  }

  return (
    <div>
      <div className="case-head" aria-hidden="true">
        <span>id</span>
        <span>segment</span>
        <span>status</span>
        <span>drone_status</span>
      </div>
      <ul className="case-list">
        {cases.map((row) => (
          <li key={row.id}>
            <button
              type="button"
              className={row.id === selectedId ? 'case-row selected' : 'case-row'}
              onClick={() => onSelect(row.id)}
            >
              <span>{row.id}</span>
              <span>{row.segment}</span>
              <span>{row.status}</span>
              <span>{row.drone_status}</span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
